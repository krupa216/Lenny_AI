# The Lenny Growth Assistant

A starter full-stack implementation for a grounded product/growth assistant. It includes FastAPI, PostgreSQL persistence, Ollama-first model configuration, transcript ingestion and retrieval, a Ship 30 for 30 writing skill, and a sandboxed artifact viewer.

## Quick start

1. Install Docker Desktop and ensure Ollama is installed locally.
2. Pull a small model that fits your machine, for example:
   ```bash
   ollama pull llama3.2:3b
   ```
3. Copy `.env.example` to `.env` and adjust values.
4. Put permitted Lenny's Podcast/newsletter transcript `.txt` or `.md` files in `data/transcripts/`.
5. Start the app:
   ```bash
   docker compose up --build
   ```
6. Open `http://localhost:8000` for the web UI and `http://localhost:8000/docs` for API docs.

> On Docker Desktop, the API reaches host Ollama using `host.docker.internal`. On Linux, you may need to add `extra_hosts` to the API service or run Ollama in Compose.

## What is implemented

- FastAPI API with health endpoint, input validation, structured error responses, and request IDs.
- PostgreSQL-backed sessions, messages, timestamps, and basic metadata.
- Ollama-first model adapter with optional Anthropic cloud adapter.
- Transcript ingestion into PostgreSQL-backed chunks and a simple local TF-IDF retriever. This keeps setup light; replace with pgvector/embeddings for larger corpora.
- Source references returned with grounded answers; the system says when retrieval finds no relevant evidence.
- Ship 30 for 30 essay tool prompt with approximate 1,250-word target and source-grounding instructions.
- Artifact generation endpoint and a UI viewer. HTML artifacts render in a sandboxed iframe with scripts disabled.
- Structured logs and graceful error handling for model/database/retrieval failures.

## Ingest transcripts

Place `.txt` or `.md` files under `data/transcripts/`, then run:
```bash
docker compose exec api python -m app.ingest
```
Each file is split into overlapping chunks and stored with its filename and chunk index. Re-run after adding or updating files. This starter does not automatically fetch copyrighted transcript repositories; provide files you have permission to use.

## Model configuration

- `LLM_PROVIDER=ollama` (default) or `anthropic`
- Ollama: `OLLAMA_BASE_URL=http://host.docker.internal:11434`, `OLLAMA_MODEL=llama3.2:3b`
- Anthropic: set `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL`. Never commit real keys.
- If the configured provider is unavailable, the API returns a structured 503 error rather than silently switching providers.

## Security notes

- The artifact viewer uses an iframe with a restrictive `sandbox` attribute and does not grant scripts, same-origin access, forms, popups, or top navigation.
- HTML is generated as untrusted text and rendered only in the isolated iframe. Do not remove the sandbox without a threat review.
- Transcript content is treated as reference material, not executable instructions.
- Never commit `.env`, API keys, private transcripts, or user data.
- For production, add authentication, per-user authorization, rate limiting, retention controls, stronger HTML sanitization, and database migrations.

## API overview

- `GET /health` - application and database health
- `POST /api/sessions` - create a chat session
- `GET /api/sessions` - list sessions
- `GET /api/sessions/{session_id}/messages` - fetch messages
- `POST /api/chat` - ask a grounded question
- `POST /api/skills/ship30` - generate an essay
- `POST /api/artifacts` - generate Markdown or HTML artifact

See `/docs` for request/response schemas.

## PRD / forward-deployment brief

### User and problem
Primary user: product managers, founders, growth practitioners, and product-minded builders. Their job is to make better product and growth decisions by extracting useful advice from a large collection of expert conversations. The assistant reduces transcript-search time and turns evidence into usable written or visual deliverables.

### Success metrics
- At least 90% of answer claims that are presented as transcript-grounded include a source reference in the evaluation set.
- Median response latency below 8 seconds on a local model for a short question on a modest transcript corpus (hardware dependent).
- A new evaluator can launch the stack and complete a question in under 10 minutes.

### Assumptions
- The evaluator can run Docker and Ollama locally.
- Transcript files are supplied by the evaluator or obtained from a source the evaluator is permitted to use.
- A local model is the demo default; cloud provider use is optional.
- Initial scope is single-user/local demo, not a production multi-tenant deployment.

### Scope choices
Included: chat sessions, persistence, retrieval, source attribution, provider configuration, essay skill, artifact generation/viewing, health endpoint, and reproducible startup. Excluded: automated transcript scraping, user authentication, multi-tenant authorization, background ingestion queue, and production-grade vector database. These are excluded to keep the take-home focused and runnable.

### Risks and trade-offs
- Hallucination: retrieval-grounded prompt, explicit abstention when evidence is weak, and source references; still requires evaluation.
- Latency: small local models reduce cost/privacy exposure but may be slower or lower quality depending on hardware.
- Cost: Ollama is local; cloud providers can incur API charges.
- Local-model quality: test several model sizes on the target machine before the demo.
- Data leakage: keep secrets in `.env`, avoid sending private transcripts to cloud models, and do not log full prompts or transcript text.
- Unsafe artifacts: render HTML only in a sandboxed iframe without scripts or same-origin privileges.
- Retrieval quality: TF-IDF is a lightweight baseline; pgvector + embedding model is a future improvement.
