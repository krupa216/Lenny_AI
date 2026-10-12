import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from app.config import settings
from app.db import Base, engine, get_db
from app.models import ChatSession, Message
from app.schemas import SessionCreate, SessionOut, ChatRequest, ChatResponse, SourceOut, ArtifactRequest, ArtifactResponse
from app.retrieval import retrieve
from app.llm import generate
from app.skills import SHIP30_SYSTEM, ARTIFACT_SYSTEM

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO),
                    format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("lenny_assistant")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("database_initialized")
    except Exception:
        logger.exception("database_initialization_failed")
    yield

app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = str(uuid.uuid4())
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info("request_complete request_id=%s method=%s path=%s status=%s",
                    request_id, request.method, request.url.path, response.status_code)
        return response
    except Exception:
        logger.exception("request_failed request_id=%s path=%s", request_id, request.url.path)
        return JSONResponse(status_code=500, content={"error": {"code": "internal_error", "message": "Unexpected server error.", "request_id": request_id}})

@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    return JSONResponse(status_code=503, content={"error": {"code": "service_unavailable", "message": str(exc)}})

@app.get("/health")
def health(db: Session = Depends(get_db)):
    database = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database = "unavailable"
    return {"status": "ok" if database == "ok" else "degraded", "database": database, "provider": settings.llm_provider}

@app.post("/api/sessions", response_model=SessionOut)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    session = ChatSession(id=str(uuid.uuid4()), title=payload.title, user_metadata=payload.user_metadata)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@app.get("/api/sessions", response_model=list[SessionOut])
def list_sessions(db: Session = Depends(get_db)):
    return list(db.scalars(select(ChatSession).order_by(ChatSession.created_at.desc()).limit(100)))

@app.get("/api/sessions/{session_id}/messages")
def get_messages(session_id: str, db: Session = Depends(get_db)):
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail={"code": "session_not_found", "message": "Chat session was not found."})
    messages = db.scalars(select(Message).where(Message.session_id == session_id).order_by(Message.created_at))
    return [{"role": m.role, "content": m.content, "sources": m.sources, "created_at": m.created_at} for m in messages]

async def answer_question(session_id: str, message: str, db: Session, system_override: str | None = None):
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail={"code": "session_not_found", "message": "Create a session first."})
    history = list(db.scalars(select(Message).where(Message.session_id == session_id).order_by(Message.created_at.desc()).limit(8)))
    history.reverse()
    hits = retrieve(db, message)
    db.add(Message(session_id=session_id, role="user", content=message, sources=[]))
    evidence = "\n\n".join(
        f"[Source: {h['source']} | chunk {h['chunk_index']} | score {h['score']}]\n{h['content']}"
        for h in hits
    )
    if not hits:
        evidence = "No relevant transcript excerpts were found."
    history_text = "\n".join(f"{m.role}: {m.content}" for m in history)
    system = system_override or (
        "You are The Lenny Growth Assistant. Answer product management and growth questions using ONLY "
        "the transcript evidence provided. If the evidence does not support an answer, explicitly say so. "
        "Do not invent quotes, facts, or sources. Cite source filename and chunk number for key claims. "
        "Use prior conversation only to interpret follow-up questions, not as factual evidence."
    )
    prompt = f"Recent conversation:\n{history_text}\n\nUser question:\n{message}\n\nTranscript evidence:\n{evidence}\n\nAnswer:"
    try:
        result = await generate(prompt, system)
    except RuntimeError:
        db.rollback()
        raise
    source_payload = [{"source": h["source"], "chunk_index": h["chunk_index"], "excerpt": h["content"][:260]} for h in hits]
    db.add(Message(session_id=session_id, role="assistant", content=result, sources=source_payload))
    db.commit()
    return result, source_payload

@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    answer, sources = await answer_question(payload.session_id, payload.message, db)
    return ChatResponse(session_id=payload.session_id, answer=answer, sources=sources, provider=settings.llm_provider)

@app.post("/api/skills/ship30", response_model=ChatResponse)
async def ship30(payload: ChatRequest, db: Session = Depends(get_db)):
    instruction = "Turn the following request into a Ship 30 for 30-style essay: " + payload.message
    answer, sources = await answer_question(payload.session_id, instruction, db, SHIP30_SYSTEM + "\nGround every factual claim in the supplied transcript evidence.")
    return ChatResponse(session_id=payload.session_id, answer=answer, sources=sources, provider=settings.llm_provider)

@app.post("/api/artifacts", response_model=ArtifactResponse)
async def create_artifact(payload: ArtifactRequest, db: Session = Depends(get_db)):
    session = db.get(ChatSession, payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail={"code": "session_not_found", "message": "Create a session first."})
    messages = list(db.scalars(select(Message).where(Message.session_id == payload.session_id).order_by(Message.created_at.desc()).limit(10)))
    context = "\n\n".join(f"{m.role}: {m.content}" for m in reversed(messages))
    hits = retrieve(db, payload.instruction)
    evidence = "\n\n".join(f"[{h['source']} chunk {h['chunk_index']}] {h['content']}" for h in hits)
    prompt = f"Conversation:\n{context}\n\nRelevant transcript evidence:\n{evidence}\n\nArtifact request: {payload.instruction}\nFormat: {payload.format}"
    content = await generate(prompt, ARTIFACT_SYSTEM)
    if payload.format == "html":
        # Defensive cleanup: scripts and external resource tags are stripped; iframe sandbox is the main boundary.
        import re
        content = re.sub(r"<script\b[^>]*>[\s\S]*?</script\s*>", "", content, flags=re.I)
        content = re.sub(r"<(iframe|object|embed|form)\b[^>]*>[\s\S]*?</\1\s*>", "", content, flags=re.I)
        content = re.sub(r"\son\w+\s*=\s*(['\"]).*?\1", "", content, flags=re.I)
    return ArtifactResponse(format=payload.format, content=content, provider=settings.llm_provider)

@app.get("/", response_class=HTMLResponse)
def home():
    path = Path(__file__).resolve().parent.parent / "frontend" / "index.html"
    return path.read_text(encoding="utf-8")
