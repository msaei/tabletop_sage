"""
Capstone Backend Tests — Auth
===========================================
Tests user registration, login, and protected route token verification.
"""

import uuid

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_register_creates_user():
    unique_user = f"user_{uuid.uuid4().hex[:6]}"
    resp = client.post(
        "/auth/register",
        json={"username": unique_user, "password": "securepassword123", "role": "player"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == unique_user
    assert "id" in data
    assert data["role"] == "player"


def test_register_duplicate_username_fails():
    unique_user = f"user_{uuid.uuid4().hex[:6]}"
    client.post(
        "/auth/register",
        json={"username": unique_user, "password": "password123"},
    )
    dup_resp = client.post(
        "/auth/register",
        json={"username": unique_user, "password": "password456"},
    )
    assert dup_resp.status_code == 400
    assert "already registered" in dup_resp.json()["detail"]


def test_login_returns_token():
    unique_user = f"user_{uuid.uuid4().hex[:6]}"
    client.post(
        "/auth/register",
        json={"username": unique_user, "password": "mypassword123"},
    )
    login_resp = client.post(
        "/auth/token",
        data={"username": unique_user, "password": "mypassword123"},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_protected_route_requires_auth():
    # Without token
    resp_unauth = client.get("/auth/me")
    assert resp_unauth.status_code == 401

    # With valid token
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
    resp_auth = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_auth.status_code == 200
    assert resp_auth.json()["username"] == unique_user

