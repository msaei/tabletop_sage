"""
Capstone Backend — FastAPI Application
===================================================
Main application entrypoint for Tabletop Sage.
Initializes database, CORS, lifespan startup hooks, and mounts API routers.

Run locally:
    uvicorn main:app --reload --port 8000
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

logger = logging.getLogger(__name__)

try:
    import models
    from database import Base, SessionLocal, engine
    from rag_pipeline import ingest_rulebook
    from routers import all_routers
    from seed_data import seed_all_games
except ImportError:
    from . import models
    from .database import Base, SessionLocal, engine
    from .rag_pipeline import ingest_rulebook
    from .routers import all_routers
    from .seed_data import seed_all_games

# Configuration & Document Storage Directory
BASE_DIR = Path(__file__).resolve().parent
DOCS_STORAGE_PATH = Path(os.getenv("DOCS_STORAGE_PATH", str(BASE_DIR / "docs")))
DOCS_STORAGE_PATH.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables, storage dirs, auto-seed games, and sync existing rulebooks to ChromaDB."""
    Base.metadata.create_all(bind=engine)
    DOCS_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

    # Auto-migrate SQLite schema if new columns are missing
    try:
        with engine.connect() as conn:
            existing_cols = [
                row[1] for row in conn.execute(text("PRAGMA table_info(board_games)")).fetchall()
            ]
            new_columns = [
                ("min_players", "INTEGER"),
                ("max_players", "INTEGER"),
                ("min_age", "INTEGER"),
                ("estimated_playtime", "INTEGER"),
                ("complexity", "VARCHAR(50)"),
                ("category", "VARCHAR(100)"),
                ("publisher", "VARCHAR(100)"),
                ("year_published", "INTEGER"),
            ]
            for col_name, col_type in new_columns:
                if col_name not in existing_cols:
                    conn.execute(text(f"ALTER TABLE board_games ADD COLUMN {col_name} {col_type}"))
            conn.commit()
    except Exception as exc:
        logger.warning(f"Database column check/migration notice: {exc}")

    # Check and auto-seed all 22 popular and classic games
    db = SessionLocal()
    try:
        active_count = db.query(models.BoardGame).filter(models.BoardGame.status == "active").count()
        if active_count < 22:
            logger.info(f"Database currently has {active_count} games. Auto-seeding 22 demo games...")
            seed_all_games()
        else:
            # Sync rulebooks from database to ChromaDB on startup
            games = db.query(models.BoardGame).filter(models.BoardGame.status == "active").all()
            for g in games:
                rule_file = DOCS_STORAGE_PATH / g.filename
                if rule_file.exists():
                    ingest_rulebook(rule_file, game_id=g.id, game_name=g.name)
    except Exception as exc:
        logger.warning(f"Error during startup game sync/seed: {exc}")
    finally:
        db.close()

    yield


app = FastAPI(
    title="Tabletop Sage API",
    description="Backend API for Tabletop Sage: RAG-powered board game assistant, catalog, and library.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production environments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all endpoint routers
for router in all_routers:
    app.include_router(router)
