"""
Capstone Backend — Pydantic Schemas
=================================================
Defines request and response validation models for Tabletop Sage.
Compatible with both Pydantic v1 and v2 (orm_mode / from_attributes).
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


# ─── Auth Schemas ─────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")


class UserCreate(UserBase):
    password: str = Field(..., min_length=4, description="Raw password string")
    role: Optional[str] = Field(default="player", description="'player' or 'admin'")


class UserResponse(UserBase):
    id: int
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


# ─── Board Game Schemas ───────────────────────────────────────────────────────

class BoardGameBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Board game title")
    description: Optional[str] = Field(default=None, description="Brief summary or description")


class BoardGameCreate(BoardGameBase):
    pass


class BoardGameResponse(BoardGameBase):
    id: int
    filename: str
    uploaded_by_user_id: int
    status: str
    uploaded_at: datetime
    is_in_library: Optional[bool] = None

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
    game: Optional[BoardGameResponse] = None

    model_config = ConfigDict(from_attributes=True)


# ─── RAG & Chat Schemas ───────────────────────────────────────────────────────

class Citation(BaseModel):
    chunk_id: Optional[str] = None
    section: Optional[str] = None
    text: str
    score: Optional[float] = None


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=2, description="Rules dispute or gameplay question")
    session_id: Optional[str] = Field(default="default-session", description="Client session ID")


class QueryResponse(BaseModel):
    answer: str
    game_id: int
    game_name: str
    citations: List[Citation] = []
    confidence: Optional[float] = None
    session_id: Optional[str] = None


class ChatLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    game_id: int
    session_id: str
    question: str
    answer: str
    citations_json: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── System Health Schemas ────────────────────────────────────────────────────

class HealthStatus(BaseModel):
    status: str = "ok"
    database: str
    vector_store: str
    llm: str
    version: str = "1.0.0"

