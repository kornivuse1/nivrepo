"""Tests for /api/admin/users/* endpoints."""
import uuid


# ── list users ────────────────────────────────────────────────────────────────

def test_list_users_admin(client, admin_headers):
    r = client.get("/api/admin/users", headers=admin_headers)
    assert r.status_code == 200
    users = r.json()
    assert isinstance(users, list)
    assert len(users) >= 1  # at least admin exists
    # Verify shape
    for u in users:
        assert "id" in u
        assert "username" in u
        assert "role" in u
        assert "created_at" in u


def test_list_users_contains_admin(client, admin_headers):
    r = client.get("/api/admin/users", headers=admin_headers)
    usernames = [u["username"] for u in r.json()]
    assert "admin" in usernames


def test_list_users_viewer_forbidden(client, viewer_headers):
    r = client.get("/api/admin/users", headers=viewer_headers)
    assert r.status_code == 403


def test_list_users_unauthenticated(client):
    r = client.get("/api/admin/users")
    assert r.status_code == 401


# ── delete user ───────────────────────────────────────────────────────────────

def test_delete_user(client, admin_headers):
    # Register a throwaway user
    username = f"throwaway_{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "password_confirm": "password123"},
    )
    assert r.status_code == 200

    # Find their ID
    users_r = client.get("/api/admin/users", headers=admin_headers)
    user = next(u for u in users_r.json() if u["username"] == username)
    user_id = user["id"]

    # Delete them
    r = client.delete(f"/api/admin/users/{user_id}", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # Confirm gone
    users_r = client.get("/api/admin/users", headers=admin_headers)
    ids = [u["id"] for u in users_r.json()]
    assert user_id not in ids


def test_delete_self_forbidden(client, admin_headers):
    # Get admin's own ID
    users_r = client.get("/api/admin/users", headers=admin_headers)
    admin_user = next(u for u in users_r.json() if u["username"] == "admin")
    r = client.delete(f"/api/admin/users/{admin_user['id']}", headers=admin_headers)
    assert r.status_code == 400
    assert "yourself" in r.json()["detail"].lower()


def test_delete_nonexistent_user(client, admin_headers):
    r = client.delete("/api/admin/users/999999", headers=admin_headers)
    assert r.status_code == 404


def test_delete_user_viewer_forbidden(client, viewer_headers):
    r = client.delete("/api/admin/users/1", headers=viewer_headers)
    assert r.status_code == 403
