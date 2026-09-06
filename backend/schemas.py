"""
Capstone Backend — Pydantic Schemas
=================================================
Defines request and response validation models for Tabletop Sage.
Compatible with both Pydantic v1 and v2 (orm_mode / from_attributes).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# ─── Auth Schemas ─────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")


class UserCreate(UserBase):
    password: str = Field(..., min_length=4, description="Raw password string")
    role: str | None = Field(default="player", description="'player' or 'admin'")


class UserResponse(UserBase):
    id: int
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None
    role: str | None = None


# ─── Board Game Schemas ───────────────────────────────────────────────────────

class BoardGameBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Board game title")
    description: str | None = Field(default=None, description="Brief summary or description")


class BoardGameCreate(BoardGameBase):
    pass


class BoardGameResponse(BoardGameBase):
    id: int
    filename: str
    uploaded_by_user_id: int
    status: str
    uploaded_at: datetime
    is_in_library: bool | None = None

    model_config = ConfigDict(from_attributes=True)


class RulebookContentResponse(BaseModel):
    game_id: int
    game_name: str
    filename: str
    content: str


# ─── Library Schemas ──────────────────────────────────────────────────────────

class LibraryActionResponse(BaseModel):
    message: str
    game_id: int
    user_id: int
    in_library: bool


class UserLibraryResponse(BaseModel):
    id: int
    user_id: int
    game_id: int
    added_at: datetime
    game: BoardGameResponse | None = None

    model_config = ConfigDict(from_attributes=True)


# ─── RAG & Chat Schemas ───────────────────────────────────────────────────────

class Citation(BaseModel):
    chunk_id: str | None = None
    section: str | None = None
    text: str
    score: float | None = None


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=2, description="Rules dispute or gameplay question")
    session_id: str | None = Field(default="default-session", description="Client session ID")


class QueryResponse(BaseModel):
    answer: str
    game_id: int
    game_name: str
    citations: list[Citation] = []
    confidence: float | None = None
    session_id: str | None = None


class ChatLogResponse(BaseModel):
    id: int
    user_id: int | None = None
    game_id: int
    session_id: str
    question: str
    answer: str
    citations_json: str | None = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── System Health Schemas ────────────────────────────────────────────────────

class HealthStatus(BaseModel):
    status: str = "ok"
    database: str
    vector_store: str
    llm: str
    version: str = "1.0.0"

