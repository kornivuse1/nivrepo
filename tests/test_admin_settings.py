"""Tests for /api/admin/settings endpoints."""


# ── get settings ──────────────────────────────────────────────────────────────

def test_get_settings_admin(client, admin_headers):
    r = client.get("/api/admin/settings", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "auto_change_background" in data
    assert "allow_registration" in data
    assert isinstance(data["auto_change_background"], bool)
    assert isinstance(data["allow_registration"], bool)


def test_get_settings_viewer_forbidden(client, viewer_headers):
    r = client.get("/api/admin/settings", headers=viewer_headers)
    assert r.status_code == 403


def test_get_settings_unauthenticated(client):
    r = client.get("/api/admin/settings")
    assert r.status_code == 401


# ── update settings ───────────────────────────────────────────────────────────

def test_update_auto_change_bg_true(client, admin_headers):
    r = client.patch("/api/admin/settings", json={"auto_change_background": True}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["auto_change_background"] is True


def test_update_auto_change_bg_false(client, admin_headers):
    r = client.patch("/api/admin/settings", json={"auto_change_background": False}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["auto_change_background"] is False


def test_update_allow_registration_false(client, admin_headers):
    r = client.patch("/api/admin/settings", json={"allow_registration": False}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["allow_registration"] is False
    # Restore
    client.patch("/api/admin/settings", json={"allow_registration": True}, headers=admin_headers)


def test_update_allow_registration_true(client, admin_headers):
    r = client.patch("/api/admin/settings", json={"allow_registration": True}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["allow_registration"] is True


def test_update_both_settings(client, admin_headers):
    r = client.patch(
        "/api/admin/settings",
        json={"auto_change_background": True, "allow_registration": True},
        headers=admin_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["auto_change_background"] is True
    assert data["allow_registration"] is True


def test_update_settings_persists(client, admin_headers):
    client.patch("/api/admin/settings", json={"auto_change_background": True}, headers=admin_headers)
    r = client.get("/api/admin/settings", headers=admin_headers)
    assert r.json()["auto_change_background"] is True
    # Reset
    client.patch("/api/admin/settings", json={"auto_change_background": False}, headers=admin_headers)


def test_update_settings_viewer_forbidden(client, viewer_headers):
    r = client.patch("/api/admin/settings", json={"auto_change_background": True}, headers=viewer_headers)
    assert r.status_code == 403


def test_registration_toggle_reflected_in_public_endpoint(client, admin_headers):
    client.patch("/api/admin/settings", json={"allow_registration": False}, headers=admin_headers)
    r = client.get("/api/auth/registration-allowed")
    assert r.json()["allow_registration"] is False
    # Restore
    client.patch("/api/admin/settings", json={"allow_registration": True}, headers=admin_headers)
