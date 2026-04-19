"""Tests for /api/admin/backgrounds/* endpoints."""
from tests.conftest import FAKE_IMG


# ── upload ────────────────────────────────────────────────────────────────────

def test_upload_background_valid(client, admin_headers):
    r = client.post(
        "/api/admin/backgrounds",
        files={"file": ("upload_test.jpg", FAKE_IMG, "image/jpeg")},
        headers=admin_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert data["filename"].endswith(".jpg")
    assert isinstance(data["is_active"], bool)
    # Cleanup
    client.delete(f"/api/admin/backgrounds/{data['id']}", headers=admin_headers)


def test_upload_background_invalid_extension(client, admin_headers):
    r = client.post(
        "/api/admin/backgrounds",
        files={"file": ("image.bmp", b"data", "image/bmp")},
        headers=admin_headers,
    )
    assert r.status_code == 400


def test_upload_background_empty_file(client, admin_headers):
    r = client.post(
        "/api/admin/backgrounds",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
        headers=admin_headers,
    )
    assert r.status_code == 400


def test_upload_background_viewer_forbidden(client, viewer_headers):
    r = client.post(
        "/api/admin/backgrounds",
        files={"file": ("image.jpg", FAKE_IMG, "image/jpeg")},
        headers=viewer_headers,
    )
    assert r.status_code == 403


def test_upload_background_unauthenticated(client):
    r = client.post(
        "/api/admin/backgrounds",
        files={"file": ("image.jpg", FAKE_IMG, "image/jpeg")},
    )
    assert r.status_code == 401


# ── list ──────────────────────────────────────────────────────────────────────

def test_list_backgrounds_admin(client, admin_headers, uploaded_bg):
    r = client.get("/api/admin/backgrounds", headers=admin_headers)
    assert r.status_code == 200
    images = r.json()
    assert isinstance(images, list)
    ids = [img["id"] for img in images]
    assert uploaded_bg["id"] in ids


def test_list_backgrounds_shape(client, admin_headers, uploaded_bg):
    r = client.get("/api/admin/backgrounds", headers=admin_headers)
    for img in r.json():
        assert "id" in img
        assert "filename" in img
        assert "is_active" in img


def test_list_backgrounds_viewer_forbidden(client, viewer_headers):
    r = client.get("/api/admin/backgrounds", headers=viewer_headers)
    assert r.status_code == 403


# ── activate ──────────────────────────────────────────────────────────────────

def test_activate_background(client, admin_headers, uploaded_bg):
    bg_id = uploaded_bg["id"]
    r = client.post(f"/api/admin/backgrounds/{bg_id}/activate", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # Confirm it is the only active one
    r = client.get("/api/admin/backgrounds", headers=admin_headers)
    active = [img for img in r.json() if img["is_active"]]
    assert len(active) == 1
    assert active[0]["id"] == bg_id


def test_activate_background_not_found(client, admin_headers):
    r = client.post("/api/admin/backgrounds/999999/activate", headers=admin_headers)
    assert r.status_code == 404


def test_activate_background_viewer_forbidden(client, viewer_headers, uploaded_bg):
    r = client.post(f"/api/admin/backgrounds/{uploaded_bg['id']}/activate", headers=viewer_headers)
    assert r.status_code == 403


# ── delete ────────────────────────────────────────────────────────────────────

def test_delete_background(client, admin_headers):
    # Upload specifically to delete
    r = client.post(
        "/api/admin/backgrounds",
        files={"file": ("to_delete.png", FAKE_IMG, "image/png")},
        headers=admin_headers,
    )
    assert r.status_code == 200
    bg_id = r.json()["id"]

    r = client.delete(f"/api/admin/backgrounds/{bg_id}", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # Confirm gone
    r = client.get("/api/admin/backgrounds", headers=admin_headers)
    ids = [img["id"] for img in r.json()]
    assert bg_id not in ids


def test_delete_background_not_found(client, admin_headers):
    r = client.delete("/api/admin/backgrounds/999999", headers=admin_headers)
    assert r.status_code == 404


def test_delete_background_viewer_forbidden(client, viewer_headers, uploaded_bg):
    r = client.delete(f"/api/admin/backgrounds/{uploaded_bg['id']}", headers=viewer_headers)
    assert r.status_code == 403
