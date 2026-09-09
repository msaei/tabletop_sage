"""
Capstone Backend — SQLAlchemy Models
==================================================
Database models for Tabletop Sage:
- User: Authentication & role management
- BoardGame: Game catalog details & rulebook metadata
- UserLibrary: Association model for user favorites / personal libraries
- ChatLog: Q&A session history and citation audit logs
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

try:
    from database import Base
except ImportError:
    from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="player", nullable=False)  # "player" | "admin"
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    uploaded_games = relationship("BoardGame", back_populates="uploader")
    library_entries = relationship(
        "UserLibrary", back_populates="user", cascade="all, delete-orphan"
    )
    chats = relationship(
        "ChatLog", back_populates="user", cascade="all, delete-orphan"
    )


class BoardGame(Base):
    __tablename__ = "board_games"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    filename = Column(String(255), unique=True, nullable=False)
    uploaded_by_user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    # Specifics & Discovery Metadata
    min_players = Column(Integer, nullable=True)
    max_players = Column(Integer, nullable=True)
    min_age = Column(Integer, nullable=True)  # Recommended minimum age, e.g. 10 for 10+
    estimated_playtime = Column(Integer, nullable=True)  # Estimated duration in minutes
    complexity = Column(String(50), nullable=True)  # e.g. "Light", "Medium", "Heavy"
    category = Column(String(100), nullable=True)  # e.g. "Strategy", "Family", "Party", etc.
    publisher = Column(String(100), nullable=True)
    year_published = Column(Integer, nullable=True)

    status = Column(String(20), default="active", nullable=False)  # "active" | "flagged"
    uploaded_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    uploader = relationship("User", back_populates="uploaded_games")
    library_entries = relationship(
        "UserLibrary", back_populates="game", cascade="all, delete-orphan"
    )
    chats = relationship(
        "ChatLog", back_populates="game", cascade="all, delete-orphan"
    )


class UserLibrary(Base):
    """
    Association model tracking which board games a user has added
    to their personal favorites/library.
    """
    __tablename__ = "user_library"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    game_id = Column(Integer, ForeignKey("board_games.id"), nullable=False, index=True)
    added_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "game_id", name="uq_user_game"),
    )

    # Relationships
    user = relationship("User", back_populates="library_entries")
    game = relationship("BoardGame", back_populates="library_entries")


class ChatLog(Base):
    """
    Stores conversational query and answer history along with source citations
    scoped to a specific game.
    """
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    game_id = Column(Integer, ForeignKey("board_games.id"), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    citations_json = Column(Text, nullable=True)  # JSON string of source citations
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="chats")
    game = relationship("BoardGame", back_populates="chats")

