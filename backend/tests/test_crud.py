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


def test_upload_game_with_metadata_and_filter_search():
    token = _get_auth_token()
    unique_id = uuid.uuid4().hex[:4]
    game_title = f"Strategy Game {unique_id}"
    file_content = b"Setup: Deploy units.\nRules: Move 2 spaces."

    upload_resp = client.post(
        "/games",
        data={
            "name": game_title,
            "description": "An epic tactical board game",
            "min_players": 2,
            "max_players": 5,
            "min_age": 12,
            "estimated_playtime": 45,
            "complexity": "Medium",
            "category": "Strategy",
            "publisher": "Sage Studio",
            "year_published": 2024,
        },
        files={"file": (f"strat_game_{unique_id}.txt", io.BytesIO(file_content), "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload_resp.status_code == 201
    data = upload_resp.json()
    assert data["min_players"] == 2
    assert data["max_players"] == 5
    assert data["min_age"] == 12
    assert data["estimated_playtime"] == 45
    assert data["complexity"] == "Medium"
    assert data["category"] == "Strategy"
    assert data["publisher"] == "Sage Studio"
    assert data["year_published"] == 2024

    # 1. Filter by player count = 4 (should match 2-5)
    resp_player = client.get("/games", params={"players": 4})
    assert resp_player.status_code == 200
    names = [g["name"] for g in resp_player.json()]
    assert game_title in names

    # 2. Filter by player count = 10 (should not match 2-5)
    resp_player_out = client.get("/games", params={"players": 10})
    assert resp_player_out.status_code == 200
    names_out = [g["name"] for g in resp_player_out.json()]
    assert game_title not in names_out

    # 3. Filter by category
    resp_cat = client.get("/games", params={"category": "Strategy"})
    assert resp_cat.status_code == 200
    assert game_title in [g["name"] for g in resp_cat.json()]

    # 4. Filter by max playtime <= 60 mins
    resp_time = client.get("/games", params={"max_playtime": 60})
    assert resp_time.status_code == 200
    assert game_title in [g["name"] for g in resp_time.json()]

    # 5. Filter by min age <= 14 (game requires 12, so 14-year-old can play)
    resp_age = client.get("/games", params={"min_age": 14})
    assert resp_age.status_code == 200
    assert game_title in [g["name"] for g in resp_age.json()]


def test_upload_game_missing_file_returns_422():
    token = _get_auth_token()
    # Attempt upload with missing required file field
    resp = client.post(
        "/games",
        data={"name": "No File Game"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


def test_delete_game_from_bank():
    token = _get_auth_token()
    game_title = f"Delete Test Game {uuid.uuid4().hex[:4]}"
    file_content = b"Setup: Rules to be deleted.\nGoal: Test game deletion."

    # 1. Upload game
    upload_resp = client.post(
        "/games",
        data={"name": game_title, "description": "To be deleted"},
        files={"file": ("del_game.txt", io.BytesIO(file_content), "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload_resp.status_code == 201
    game_id = upload_resp.json()["id"]

    # Verify game exists
    get_resp = client.get(f"/games/{game_id}")
    assert get_resp.status_code == 200

    # 2. Delete game
    del_resp = client.delete(
        f"/games/{game_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["game_id"] == game_id

    # 3. Verify game no longer exists
    get_after = client.get(f"/games/{game_id}")
    assert get_after.status_code == 404
