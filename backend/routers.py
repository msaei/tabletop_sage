"""
Capstone Backend — API Routers
===================================================
Defines modular APIRouter endpoints for Tabletop Sage:
- auth_router: Authentication & user account management (/auth)
- games_router: Game Bank catalog and rulebook viewer (/games)
- library_router: User Personal Library management (/library)
- rag_router: RAG Assistant & rules referee (/games/{game_id}/ask)
- health_router: System health check (/health)
"""

import json
import logging
import os
import shutil
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_, text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

try:
    import models
    import schemas
    from auth import (
        create_access_token,
        get_current_user,
        get_current_user_optional,
        hash_password,
        verify_password,
    )
    from database import get_db
    from rag_pipeline import (
        check_rag_health,
        ingest_rulebook,
        query_rag_pipeline,
    )
except ImportError:
    from . import models, schemas
    from .auth import (
        create_access_token,
        get_current_user,
        get_current_user_optional,
        hash_password,
        verify_password,
    )
    from .database import get_db
    from .rag_pipeline import (
        check_rag_health,
        ingest_rulebook,
        query_rag_pipeline,
    )

# Configuration & Document Storage Directory
DOCS_STORAGE_PATH = Path(os.getenv("DOCS_STORAGE_PATH", "./docs"))
DOCS_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

# ── Router Definitions ────────────────────────────────────────────────────────
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
games_router = APIRouter(prefix="/games", tags=["Games Bank"])
library_router = APIRouter(prefix="/library", tags=["User Library"])
rag_router = APIRouter(tags=["RAG Assistant"])
health_router = APIRouter(tags=["System"])


# ─── Auth Endpoints ───────────────────────────────────────────────────────────

@auth_router.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register_user(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(models.User).filter(models.User.username == user_in.username).first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already registered",
        )

    new_user = models.User(
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
        role=user_in.role or "player",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@auth_router.post(
    "/token",
    response_model=schemas.Token,
    summary="Login with username and password to get a JWT access token",
)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User).filter(models.User.username == form_data.username).first()
    )
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.get(
    "/me",
    response_model=schemas.UserResponse,
    summary="Get current authenticated user profile",
)
def get_my_profile(
    current_user: models.User = Depends(get_current_user),
):
    return current_user


# ─── Board Game Catalog Endpoints ─────────────────────────────────────────────

@games_router.get(
    "",
    response_model=list[schemas.BoardGameResponse],
    summary="Search and browse board games in the shared bank",
)
def list_games(
    q: str | None = Query(None, description="Search term for title, description, category, or publisher"),
    players: int | None = Query(None, description="Filter for games supporting this exact number of players"),
    min_players: int | None = Query(None, description="Filter games with minimum player count >= this value"),
    max_players: int | None = Query(None, description="Filter games with maximum player count <= this value"),
    min_age: int | None = Query(None, description="Filter games suitable for this minimum age (game min_age <= value)"),
    max_playtime: int | None = Query(None, description="Filter games playable within this playtime (in minutes)"),
    complexity: str | None = Query(None, description="Filter by complexity (e.g. Light, Medium, Heavy)"),
    category: str | None = Query(None, description="Filter by category/genre"),
    skip: int = Query(0, ge=0, description="Offset pagination"),
    limit: int = Query(50, ge=1, le=100, description="Limit pagination"),
    db: Session = Depends(get_db),
    current_user: models.User | None = Depends(get_current_user_optional),
):
    query = db.query(models.BoardGame).filter(models.BoardGame.status == "active")

    if q:
        search_pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                models.BoardGame.name.ilike(search_pattern),
                models.BoardGame.description.ilike(search_pattern),
                models.BoardGame.category.ilike(search_pattern),
                models.BoardGame.publisher.ilike(search_pattern),
            )
        )

    if players is not None:
        query = query.filter(
            or_(
                models.BoardGame.min_players == None,
                models.BoardGame.min_players <= players,
            )
        ).filter(
            or_(
                models.BoardGame.max_players == None,
                models.BoardGame.max_players >= players,
            )
        )

    if min_players is not None:
        query = query.filter(
            or_(
                models.BoardGame.min_players == None,
                models.BoardGame.min_players >= min_players,
            )
        )

    if max_players is not None:
        query = query.filter(
            or_(
                models.BoardGame.max_players == None,
                models.BoardGame.max_players <= max_players,
            )
        )

    if min_age is not None:
        query = query.filter(
            or_(
                models.BoardGame.min_age == None,
                models.BoardGame.min_age <= min_age,
            )
        )

    if max_playtime is not None:
        query = query.filter(
            or_(
                models.BoardGame.estimated_playtime == None,
                models.BoardGame.estimated_playtime <= max_playtime,
            )
        )

    if complexity:
        query = query.filter(models.BoardGame.complexity.ilike(f"%{complexity.strip()}%"))

    if category:
        query = query.filter(models.BoardGame.category.ilike(f"%{category.strip()}%"))

    games = query.order_by(models.BoardGame.name.asc()).offset(skip).limit(limit).all()

    # Determine user's library items if logged in
    user_library_game_ids = set()
    if current_user:
        user_library_game_ids = {
            item.game_id
            for item in db.query(models.UserLibrary.game_id)
            .filter(models.UserLibrary.user_id == current_user.id)
            .all()
        }

    results = []
    for game in games:
        game_data = schemas.BoardGameResponse.model_validate(game)
        if current_user:
            game_data.is_in_library = game.id in user_library_game_ids
        results.append(game_data)

    return results


@games_router.post(
    "",
    response_model=schemas.BoardGameResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new board game and its rulebook to the bank",
)
async def upload_game(
    name: str = Form(..., min_length=1, max_length=100),
    description: str | None = Form(None),
    min_players: int | None = Form(None),
    max_players: int | None = Form(None),
    min_age: int | None = Form(None),
    estimated_playtime: int | None = Form(None),
    complexity: str | None = Form(None),
    category: str | None = Form(None),
    publisher: str | None = Form(None),
    year_published: int | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Validate file format
    allowed_extensions = {".txt", ".md"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{file_ext}'. Allowed formats: {', '.join(allowed_extensions)}",
        )

    # Check for duplicate game name
    existing_game = (
        db.query(models.BoardGame).filter(models.BoardGame.name.ilike(name.strip())).first()
    )
    if existing_game:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A game titled '{name}' already exists in the bank.",
        )

    # Sanitize and create unique filename
    safe_name = "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")
    unique_filename = f"{safe_name}_{os.urandom(4).hex()}{file_ext}"
    destination_path = DOCS_STORAGE_PATH / unique_filename

    # Save rulebook to storage
    try:
        with destination_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save rulebook file: {exc!s}",
        )

    # Create BoardGame record
    new_game = models.BoardGame(
        name=name.strip(),
        description=description.strip() if description else None,
        min_players=min_players,
        max_players=max_players,
        min_age=min_age,
        estimated_playtime=estimated_playtime,
        complexity=complexity.strip() if complexity else None,
        category=category.strip() if category else None,
        publisher=publisher.strip() if publisher else None,
        year_published=year_published,
        filename=unique_filename,
        uploaded_by_user_id=current_user.id,
        status="active",
    )
    db.add(new_game)
    db.commit()
    db.refresh(new_game)

    # Automatically add to the uploader's library
    uploader_entry = models.UserLibrary(user_id=current_user.id, game_id=new_game.id)
    db.add(uploader_entry)
    db.commit()

    # Automatically chunk and index rulebook into ChromaDB
    try:
        indexed_chunks = ingest_rulebook(
            file_path=destination_path,
            game_id=new_game.id,
            game_name=new_game.name,
        )
        logger.info(f"Indexed {indexed_chunks} chunks for '{new_game.name}' (game_id={new_game.id})")
    except Exception as exc:
        logger.error(f"Vector indexing failed for '{new_game.name}': {exc}")

    game_resp = schemas.BoardGameResponse.model_validate(new_game)
    game_resp.is_in_library = True
    return game_resp


@games_router.get(
    "/{game_id}",
    response_model=schemas.BoardGameResponse,
    summary="Get details of a single board game",
)
def get_game(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: models.User | None = Depends(get_current_user_optional),
):
    game = db.query(models.BoardGame).filter(models.BoardGame.id == game_id).first()
    if not game or game.status != "active":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board game not found",
        )

    game_data = schemas.BoardGameResponse.model_validate(game)
    if current_user:
        is_saved = (
            db.query(models.UserLibrary)
            .filter(
                models.UserLibrary.user_id == current_user.id,
                models.UserLibrary.game_id == game.id,
            )
            .first()
            is not None
        )
        game_data.is_in_library = is_saved
    return game_data


@games_router.get(
    "/{game_id}/rulebook",
    response_model=schemas.RulebookContentResponse,
    summary="Retrieve the raw rulebook content for reading",
)
def get_game_rulebook(
    game_id: int,
    db: Session = Depends(get_db),
):
    game = db.query(models.BoardGame).filter(models.BoardGame.id == game_id).first()
    if not game or game.status != "active":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board game not found",
        )

    file_path = DOCS_STORAGE_PATH / game.filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rulebook file not found on server",
        )

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not read rulebook file: {exc!s}",
        )

    return {
        "game_id": game.id,
        "game_name": game.name,
        "filename": game.filename,
        "content": content,
    }


# ─── Personal Library Endpoints ───────────────────────────────────────────────

@library_router.get(
    "",
    response_model=list[schemas.BoardGameResponse],
    summary="List all board games in the authenticated user's library",
)
def get_user_library(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    entries = (
        db.query(models.BoardGame)
        .join(models.UserLibrary, models.BoardGame.id == models.UserLibrary.game_id)
        .filter(
            models.UserLibrary.user_id == current_user.id,
            models.BoardGame.status == "active",
        )
        .order_by(models.UserLibrary.added_at.desc())
        .all()
    )

    results = []
    for game in entries:
        game_data = schemas.BoardGameResponse.model_validate(game)
        game_data.is_in_library = True
        results.append(game_data)
    return results


@library_router.post(
    "/{game_id}",
    response_model=schemas.LibraryActionResponse,
    summary="Add a board game from the bank into the user's library",
)
def add_to_library(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    game = db.query(models.BoardGame).filter(models.BoardGame.id == game_id).first()
    if not game or game.status != "active":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board game not found",
        )

    existing_entry = (
        db.query(models.UserLibrary)
        .filter(
            models.UserLibrary.user_id == current_user.id,
            models.UserLibrary.game_id == game_id,
        )
        .first()
    )
    if existing_entry:
        return {
            "message": f"'{game.name}' is already in your library.",
            "game_id": game_id,
            "user_id": current_user.id,
            "in_library": True,
        }

    new_entry = models.UserLibrary(user_id=current_user.id, game_id=game_id)
    db.add(new_entry)
    db.commit()

    return {
        "message": f"Added '{game.name}' to your library.",
        "game_id": game_id,
        "user_id": current_user.id,
        "in_library": True,
    }


@library_router.delete(
    "/{game_id}",
    response_model=schemas.LibraryActionResponse,
    summary="Remove a board game from the user's library",
)
def remove_from_library(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    entry = (
        db.query(models.UserLibrary)
        .filter(
            models.UserLibrary.user_id == current_user.id,
            models.UserLibrary.game_id == game_id,
        )
        .first()
    )
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game is not in your library",
        )

    db.delete(entry)
    db.commit()

    return {
        "message": "Game removed from library.",
        "game_id": game_id,
        "user_id": current_user.id,
        "in_library": False,
    }


# ─── RAG Assistant Endpoints ──────────────────────────────────────────────────

@rag_router.post(
    "/games/{game_id}/ask",
    response_model=schemas.QueryResponse,
    tags=["RAG Assistant"],
    summary="Ask a rules question strictly scoped to a specific board game's rulebook",
)
def ask_game_rulebook(
    game_id: int,
    query_in: schemas.QueryRequest,
    db: Session = Depends(get_db),
    current_user: models.User | None = Depends(get_current_user_optional),
):
    game = db.query(models.BoardGame).filter(models.BoardGame.id == game_id).first()
    if not game or game.status != "active":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board game not found",
        )

    # Execute scoped RAG query (vector search + LLM generation)
    rag_result = query_rag_pipeline(
        question=query_in.question,
        game_id=game.id,
        game_name=game.name,
    )

    # Audit log Q&A interaction to SQLite chat_history
    try:
        chat_log = models.ChatLog(
            user_id=current_user.id if current_user else None,
            game_id=game.id,
            session_id=query_in.session_id or "default-session",
            question=query_in.question,
            answer=rag_result["answer"],
            citations_json=json.dumps(rag_result.get("citations", [])),
        )
        db.add(chat_log)
        db.commit()
    except Exception as exc:
        logger.warning(f"Failed to record chat history audit log: {exc}")

    return {
        "answer": rag_result["answer"],
        "game_id": game.id,
        "game_name": game.name,
        "citations": rag_result.get("citations", []),
        "confidence": rag_result.get("confidence", 0.0),
        "session_id": query_in.session_id,
    }


# ─── System Health Endpoint ───────────────────────────────────────────────────

@health_router.get(
    "/health",
    response_model=schemas.HealthStatus,
    tags=["System"],
    summary="Check database, vector store, and server health",
)
def health_check(
    db: Session = Depends(get_db),
):
    # Check Database connectivity
    db_status = "unhealthy"
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as exc:
        db_status = f"unhealthy: {exc!s}"

    # Check Vector Store and LLM connectivity
    rag_health = check_rag_health()

    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "database": db_status,
        "vector_store": rag_health.get("vector_store", "unknown"),
        "llm": rag_health.get("llm", "unknown"),
        "version": "1.0.0",
    }


# Convenience list for registering all routers with FastAPI app
all_routers = [
    auth_router,
    games_router,
    library_router,
    rag_router,
    health_router,
]
