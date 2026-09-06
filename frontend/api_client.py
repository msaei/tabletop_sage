"""
Capstone Frontend — API Client
============================================
Wraps HTTP calls to the FastAPI backend (auth, game bank, library,
rulebooks, RAG questions, and system health).
"""

import os
from typing import Any

import requests

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")


def _get_headers(token: str | None = None) -> dict[str, str]:
    """Helper to generate request headers with optional JWT Bearer token."""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


# ─── Authentication API ───────────────────────────────────────────────────────

def register(username: str, password: str, role: str = "player") -> tuple[bool, Any]:
    """Register a new user account."""
    url = f"{BACKEND_URL}/auth/register"
    try:
        resp = requests.post(
            url,
            json={"username": username, "password": password, "role": role},
            timeout=10,
        )
        if resp.status_code == 201:
            return True, resp.json()
        error_msg = resp.json().get("detail", "Registration failed")
        return False, error_msg
    except requests.exceptions.RequestException as exc:
        return False, f"Server connection error: {exc!s}"


def login(username: str, password: str) -> tuple[bool, Any]:
    """Authenticate credentials and retrieve a JWT access token."""
    url = f"{BACKEND_URL}/auth/token"
    try:
        resp = requests.post(
            url,
            data={"username": username, "password": password},
            timeout=10,
        )
        if resp.status_code == 200:
            return True, resp.json()
        error_msg = resp.json().get("detail", "Invalid username or password")
        return False, error_msg
    except requests.exceptions.RequestException as exc:
        return False, f"Server connection error: {exc!s}"


def get_current_user(token: str) -> tuple[bool, Any]:
    """Fetch current user profile using JWT token."""
    url = f"{BACKEND_URL}/auth/me"
    try:
        resp = requests.get(url, headers=_get_headers(token), timeout=10)
        if resp.status_code == 200:
            return True, resp.json()
        return False, resp.json().get("detail", "Failed to fetch user")
    except requests.exceptions.RequestException as exc:
        return False, f"Server connection error: {exc!s}"


# ─── Game Bank API ────────────────────────────────────────────────────────────

def get_games(q: str | None = None, token: str | None = None) -> tuple[bool, Any]:
    """Search and browse board games in the shared bank."""
    url = f"{BACKEND_URL}/games"
    params = {}
    if q and q.strip():
        params["q"] = q.strip()
    try:
        resp = requests.get(url, params=params, headers=_get_headers(token), timeout=10)
        if resp.status_code == 200:
            return True, resp.json()
        return False, resp.json().get("detail", "Failed to load games")
    except requests.exceptions.RequestException as exc:
        return False, f"Server connection error: {exc!s}"


def get_game(game_id: int, token: str | None = None) -> tuple[bool, Any]:
    """Retrieve details for a single game."""
    url = f"{BACKEND_URL}/games/{game_id}"
    try:
        resp = requests.get(url, headers=_get_headers(token), timeout=10)
        if resp.status_code == 200:
            return True, resp.json()
        return False, resp.json().get("detail", "Game not found")
    except requests.exceptions.RequestException as exc:
        return False, f"Server connection error: {exc!s}"


def upload_game(
    name: str,
    description: str | None,
    file_bytes: bytes,
    filename: str,
    token: str,
) -> tuple[bool, Any]:
    """Upload a new board game and its rulebook file to the bank."""
    url = f"{BACKEND_URL}/games"
    data = {"name": name}
    if description:
        data["description"] = description
    files = {"file": (filename, file_bytes)}
    try:
        resp = requests.post(
            url,
            data=data,
            files=files,
            headers=_get_headers(token),
            timeout=60,
        )
        if resp.status_code == 201:
            return True, resp.json()
        return False, resp.json().get("detail", "Failed to upload game")
    except requests.exceptions.RequestException as exc:
        return False, f"Server connection error: {exc!s}"


def get_rulebook(game_id: int) -> tuple[bool, Any]:
    """Retrieve raw/markdown rulebook text for reading."""
    url = f"{BACKEND_URL}/games/{game_id}/rulebook"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return True, resp.json()
        return False, resp.json().get("detail", "Failed to retrieve rulebook")
    except requests.exceptions.RequestException as exc:
        return False, f"Server connection error: {exc!s}"


# ─── Personal Library API ─────────────────────────────────────────────────────

def get_library(token: str) -> tuple[bool, Any]:
    """Fetch the authenticated user's saved games library."""
    url = f"{BACKEND_URL}/library"
    try:
        resp = requests.get(url, headers=_get_headers(token), timeout=10)
        if resp.status_code == 200:
            return True, resp.json()
        return False, resp.json().get("detail", "Failed to fetch library")
    except requests.exceptions.RequestException as exc:
        return False, f"Server connection error: {exc!s}"


def add_to_library(game_id: int, token: str) -> tuple[bool, Any]:
    """Add a game from the bank to user's favorites/library."""
    url = f"{BACKEND_URL}/library/{game_id}"
    try:
        resp = requests.post(url, headers=_get_headers(token), timeout=10)
        if resp.status_code == 200:
            return True, resp.json()
        return False, resp.json().get("detail", "Failed to add game to library")
    except requests.exceptions.RequestException as exc:
        return False, f"Server connection error: {exc!s}"


def remove_from_library(game_id: int, token: str) -> tuple[bool, Any]:
    """Remove a game from user's library."""
    url = f"{BACKEND_URL}/library/{game_id}"
    try:
        resp = requests.delete(url, headers=_get_headers(token), timeout=10)
        if resp.status_code == 200:
            return True, resp.json()
        return False, resp.json().get("detail", "Failed to remove game from library")
    except requests.exceptions.RequestException as exc:
        return False, f"Server connection error: {exc!s}"


# ─── RAG Rules Assistant API ──────────────────────────────────────────────────

def ask_rules_question(
    game_id: int,
    question: str,
    session_id: str = "default-session",
    token: str | None = None,
) -> tuple[bool, Any]:
    """Ask a rules dispute question scoped to game_id."""
    url = f"{BACKEND_URL}/games/{game_id}/ask"
    payload = {"question": question, "session_id": session_id}
    try:
        resp = requests.post(
            url,
            json=payload,
            headers=_get_headers(token),
            timeout=60,
        )
        if resp.status_code == 200:
            return True, resp.json()
        return False, resp.json().get("detail", "Failed to get rules answer")
    except requests.exceptions.RequestException as exc:
        return False, f"Server connection error: {exc!s}"


# ─── System Health API ────────────────────────────────────────────────────────

def get_health() -> dict[str, Any]:
    """Retrieve backend database, vector store, and LLM health status."""
    url = f"{BACKEND_URL}/health"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return resp.json()
        return {"status": "degraded", "detail": f"Status code {resp.status_code}"}
    except Exception as exc:
        return {"status": "offline", "detail": str(exc)}

