"""
Capstone Backend Tests — CRUD
===========================================
Tests Game Bank listing, uploading, rulebook viewing, and User Library CRUD.
"""

import io
import uuid

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def _get_auth_token():
    unique_user = f"user_{uuid.uuid4().hex[:6]}"
    client.post(
        "/auth/register",
        json={"username": unique_user, "password": "mypassword123"},
    )
    token_resp = client.post(
        "/auth/token",
        data={"username": unique_user, "password": "mypassword123"},
    )
    return token_resp.json()["access_token"]


def test_list_games_returns_list():
    resp = client.get("/games")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_upload_game_and_fetch_rulebook():
    token = _get_auth_token()
    game_title = f"Test Game {uuid.uuid4().hex[:4]}"
    file_content = b"Setup: Place the board.\nGoal: Reach 100 points."

    upload_resp = client.post(
        "/games",
        data={"name": game_title, "description": "A fun test game"},
        files={"file": ("test_game.txt", io.BytesIO(file_content), "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload_resp.status_code == 201
    game_data = upload_resp.json()
    assert game_data["name"] == game_title
    assert game_data["is_in_library"] is True
    game_id = game_data["id"]

    # Fetch rulebook text
    rulebook_resp = client.get(f"/games/{game_id}/rulebook")
    assert rulebook_resp.status_code == 200
    assert "Reach 100 points" in rulebook_resp.json()["content"]


def test_user_library_add_and_remove():
    token = _get_auth_token()
    game_title = f"Lib Test Game {uuid.uuid4().hex[:4]}"
    file_content = b"Rules: Standard testing rules."

    upload_resp = client.post(
        "/games",
        data={"name": game_title},
        files={"file": ("lib_game.txt", io.BytesIO(file_content), "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    game_id = upload_resp.json()["id"]

    # Check library contains the uploaded game
    lib_resp = client.get("/library", headers={"Authorization": f"Bearer {token}"})
    assert lib_resp.status_code == 200
    lib_ids = [g["id"] for g in lib_resp.json()]
    assert game_id in lib_ids

    # Remove from library
    rm_resp = client.delete(f"/library/{game_id}", headers={"Authorization": f"Bearer {token}"})
    assert rm_resp.status_code == 200
    assert rm_resp.json()["in_library"] is False

    # Check library no longer contains game
    lib_after = client.get("/library", headers={"Authorization": f"Bearer {token}"})
    assert game_id not in [g["id"] for g in lib_after.json()]


def test_health_endpoint_returns_200():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "database" in data
    assert "version" in data


def test_upload_game_missing_file_returns_422():
    token = _get_auth_token()
    # Attempt upload with missing required file field
    resp = client.post(
        "/games",
        data={"name": "No File Game"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


