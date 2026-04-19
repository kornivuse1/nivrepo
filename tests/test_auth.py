"""Tests for /api/auth/* endpoints."""
import uuid


# ── login ─────────────────────────────────────────────────────────────────────

def test_login_success(client):
    r = client.post("/api/auth/login", data={"username": "admin", "password": "admin"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    r = client.post("/api/auth/login", data={"username": "admin", "password": "wrongpassword"})
    assert r.status_code == 401


def test_login_wrong_username(client):
    r = client.post("/api/auth/login", data={"username": "nobody", "password": "admin"})
    assert r.status_code == 401


def test_login_missing_fields(client):
    r = client.post("/api/auth/login", data={})
    assert r.status_code == 422


# ── registration-allowed (public) ─────────────────────────────────────────────

def test_registration_allowed_is_public(client):
    r = client.get("/api/auth/registration-allowed")
    assert r.status_code == 200
    assert "allow_registration" in r.json()


# ── register ─────────────────────────────────────────────────────────────────

def test_register_success(client, admin_headers):
    username = f"user_{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/auth/register",
        json={"username": username, "password": "validpass", "password_confirm": "validpass"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    # Clean up: delete the user we just created
    users_r = client.get("/api/admin/users", headers=admin_headers)
    for user in users_r.json():
        if user["username"] == username:
            client.delete(f"/api/admin/users/{user['id']}", headers=admin_headers)
            break


def test_register_duplicate_username(client):
    # "testviewer" was created by the session fixture
    r = client.post(
        "/api/auth/register",
        json={"username": "testviewer", "password": "password123", "password_confirm": "password123"},
    )
    assert r.status_code == 400
    assert "taken" in r.json()["detail"].lower()


def test_register_password_mismatch(client):
    r = client.post(
        "/api/auth/register",
        json={"username": "whoever", "password": "abc123", "password_confirm": "abc456"},
    )
    assert r.status_code == 400
    assert "match" in r.json()["detail"].lower()


def test_register_password_too_short(client):
    r = client.post(
        "/api/auth/register",
        json={"username": "whoever", "password": "abc", "password_confirm": "abc"},
    )
    assert r.status_code == 400
    assert "6" in r.json()["detail"]


def test_register_disabled(client, admin_headers):
    # Disable registration, try to register, then re-enable
    client.patch("/api/admin/settings", json={"allow_registration": False}, headers=admin_headers)
    try:
        r = client.post(
            "/api/auth/register",
            json={"username": "blocked_user", "password": "password123", "password_confirm": "password123"},
        )
        assert r.status_code == 403
        assert "disabled" in r.json()["detail"].lower()
    finally:
        client.patch("/api/admin/settings", json={"allow_registration": True}, headers=admin_headers)


# ── /me ───────────────────────────────────────────────────────────────────────

def test_me_as_admin(client, admin_headers):
    r = client.get("/api/auth/me", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"


def test_me_as_viewer(client, viewer_headers):
    r = client.get("/api/auth/me", headers=viewer_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "testviewer"
    assert data["role"] == "viewer"


def test_me_unauthenticated(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_me_invalid_token(client):
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer this.is.invalid"})
    assert r.status_code == 401
