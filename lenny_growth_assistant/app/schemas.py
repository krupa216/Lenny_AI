from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any, Literal

class SessionCreate(BaseModel):
    title: str = Field(default="New chat", max_length=200)
    user_metadata: dict[str, Any] = Field(default_factory=dict)

class SessionOut(BaseModel):
    id: str
    title: str
    user_metadata: dict[str, Any]
    created_at: datetime

class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1, max_length=12000)

class SourceOut(BaseModel):
    source: str
    chunk_index: int
    excerpt: str

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[SourceOut]
    provider: str

class ArtifactRequest(BaseModel):
    session_id: str
    instruction: str = Field(min_length=1, max_length=8000)
    format: Literal["markdown", "html"] = "markdown"

class ArtifactResponse(BaseModel):
    format: str
    content: str
    provider: str
