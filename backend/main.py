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
except ImportError:
    from . import models
    from .database import Base, SessionLocal, engine
    from .rag_pipeline import ingest_rulebook
    from .routers import all_routers

# Configuration & Document Storage Directory
DOCS_STORAGE_PATH = Path(os.getenv("DOCS_STORAGE_PATH", "./docs"))
DOCS_STORAGE_PATH.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables, storage dirs, and sync existing rulebooks to ChromaDB."""
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

    # Sync rulebooks from database to ChromaDB on startup
    db = SessionLocal()
    try:
        games = db.query(models.BoardGame).filter(models.BoardGame.status == "active").all()
        for g in games:
            # Backfill sample game specifics if null
            if g.name.lower() == "catan" and not g.min_players:
                g.min_players, g.max_players, g.min_age, g.estimated_playtime = 3, 4, 10, 75
                g.complexity, g.category, g.publisher, g.year_published = "Medium", "Strategy", "KOSMOS", 1995
            elif g.name.lower() == "monopoly" and not g.min_players:
                g.min_players, g.max_players, g.min_age, g.estimated_playtime = 2, 8, 8, 90
                g.complexity, g.category, g.publisher, g.year_published = "Light / Casual", "Family", "Hasbro", 1935
            elif g.name.lower() == "chess" and not g.min_players:
                g.min_players, g.max_players, g.min_age, g.estimated_playtime = 2, 2, 6, 30
                g.complexity, g.category, g.publisher = "Medium", "Abstract Strategy", "Public Domain"
            elif g.name.lower() == "backgammon" and not g.min_players:
                g.min_players, g.max_players, g.min_age, g.estimated_playtime = 2, 2, 8, 30
                g.complexity, g.category, g.publisher = "Light / Casual", "Abstract Strategy", "Public Domain"

            rule_file = DOCS_STORAGE_PATH / g.filename
            if rule_file.exists():
                ingest_rulebook(rule_file, game_id=g.id, game_name=g.name)
        db.commit()
    except Exception as exc:
        logger.warning(f"Error syncing rulebooks on startup: {exc}")
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
