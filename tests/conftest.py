"""
Shared fixtures for NivPro tests.

All fixtures use session scope for performance (single TestClient, single DB).
Function-scoped fixtures (uploaded_song, uploaded_bg) create resources and
clean them up after each test that requests them.
"""
import os
import shutil

# ── env vars must be set before any app module is imported ──────────────────
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_nivpro.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-tests-only"
os.environ["CREATE_DEFAULT_ADMIN"] = "true"
os.environ["ALLOW_REGISTRATION"] = "true"
os.environ["UPLOAD_DIR"] = "./test_uploads"
os.environ["IMAGES_DIR"] = "./test_uploads/images"

import pytest
from fastapi.testclient import TestClient
from app.main import app

# ── minimal fake binary payloads ─────────────────────────────────────────────
# mutagen will fail to parse these, but parse_tags() catches all exceptions
# and falls back to the filename, so the upload still succeeds.
FAKE_MP3 = b"\xff\xfb\x90\x00" + b"\x00" * 128  # fake MP3 frame header
FAKE_IMG = b"\xff\xd8\xff\xe0" + b"\x00" * 128  # fake JPEG SOI marker


# ── session-scoped client ─────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    """Single TestClient for the whole test session."""
    with TestClient(app) as c:
        yield c
    # Dispose async engine so aiosqlite releases the file handle (needed on Windows).
    import asyncio
    from app.database import get_engine
    engine = get_engine()
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(engine.dispose())
    finally:
        loop.close()
    # Cleanup test artifacts
    try:
        os.remove("./test_nivpro.db")
    except (FileNotFoundError, PermissionError):
        pass
    shutil.rmtree("./test_uploads", ignore_errors=True)


# ── auth fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def admin_headers(client):
    """Auth headers for the default admin user (created by CREATE_DEFAULT_ADMIN)."""
    r = client.post("/api/auth/login", data={"username": "admin", "password": "admin"})
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def viewer_headers(client):
    """Auth headers for a viewer registered once per session.

    Falls back to login if the user already exists (e.g. from a previous run
    that left the test DB behind).
    """
    r = client.post(
        "/api/auth/register",
        json={"username": "testviewer", "password": "password123", "password_confirm": "password123"},
    )
    if r.status_code == 400 and "taken" in r.json().get("detail", "").lower():
        r = client.post("/api/auth/login", data={"username": "testviewer", "password": "password123"})
    assert r.status_code == 200, f"Viewer setup failed: {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ── resource fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def uploaded_song(client, admin_headers):
    """Upload a fake song; delete it after the test."""
    r = client.post(
        "/api/admin/songs",
        files={"file": ("pytest_song.mp3", FAKE_MP3, "audio/mpeg")},
        headers=admin_headers,
    )
    assert r.status_code == 200, f"Song upload failed: {r.text}"
    song = r.json()
    yield song
    client.delete(f"/api/admin/songs/{song['id']}", headers=admin_headers)


@pytest.fixture
def uploaded_bg(client, admin_headers):
    """Upload a fake background image; delete it after the test."""
    r = client.post(
        "/api/admin/backgrounds",
        files={"file": ("pytest_bg.jpg", FAKE_IMG, "image/jpeg")},
        headers=admin_headers,
    )
    assert r.status_code == 200, f"Background upload failed: {r.text}"
    bg = r.json()
    yield bg
    client.delete(f"/api/admin/backgrounds/{bg['id']}", headers=admin_headers)
