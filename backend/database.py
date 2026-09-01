"""
Capstone Backend — Database Setup
===============================================
Creates SQLAlchemy engine, session maker, declarative Base, and
the get_db dependency for FastAPI routes.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Resolve database path relative to the backend directory if not provided in environment
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "tabletop_sage.db"

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# SQLite requires check_same_thread=False for multi-threaded FastAPI access
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency yielding a SQLAlchemy database session,
    ensuring cleanup and closure when the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

