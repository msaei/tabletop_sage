"""
Capstone Backend Tests — RAG
==========================================
Tests the scoped RAG pipeline, document chunking, and Q&A endpoint.
"""

import io
import uuid

from fastapi.testclient import TestClient
from main import app
from rag_pipeline import chunk_document

client = TestClient(app)


def test_chunk_document_splits_properly():
    sample_text = (
        "# Setup\nPlace the board in the middle.\n\n"
        "# How to Play\nRoll the dice to move your pawn.\n\n"
        "# Winning\nThe first player to score 10 points wins the game."
    )
    chunks = chunk_document(sample_text, chunk_size=200, chunk_overlap=20)
    assert len(chunks) >= 3
    sections = [c[0] for c in chunks]
    assert "Setup" in sections
    assert "How to Play" in sections


def test_rag_ask_returns_citations():
    # Register and upload a game
    unique_user = f"user_{uuid.uuid4().hex[:6]}"
    client.post(
        "/auth/register",
        json={"username": unique_user, "password": "mypassword123"},
    )
    token_resp = client.post(
        "/auth/token",
        data={"username": unique_user, "password": "mypassword123"},
    )
    token = token_resp.json()["access_token"]

    game_title = f"RAG Test Game {uuid.uuid4().hex[:4]}"
    rulebook_text = (
        "Goal of the Game\nCollect all 4 ancient relics to open the mystic portal and win.\n\n"
        "Turn Sequence\nDraw 2 cards, move 3 tiles, and resolve any encounter tokens."
    )

    upload_resp = client.post(
        "/games",
        data={"name": game_title},
        files={"file": ("rag_rules.txt", io.BytesIO(rulebook_text.encode("utf-8")), "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload_resp.status_code == 201
    game_id = upload_resp.json()["id"]

    # Query the RAG endpoint
    ask_resp = client.post(
        f"/games/{game_id}/ask",
        json={"question": "How do I win the game?", "session_id": "test-session"},
    )
    assert ask_resp.status_code == 200
    data = ask_resp.json()
    assert "answer" in data
    assert "citations" in data
    assert len(data["citations"]) > 0
    assert data["game_id"] == game_id
    assert any(
        "relics" in c["text"].lower() or "win" in c["text"].lower() or "portal" in c["text"].lower()
        for c in data["citations"]
    )

