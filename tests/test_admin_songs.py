"""Tests for /api/admin/songs/* endpoints."""
from tests.conftest import FAKE_MP3


# ── upload ────────────────────────────────────────────────────────────────────

def test_upload_song_valid(client, admin_headers):
    r = client.post(
        "/api/admin/songs",
        files={"file": ("upload_test.mp3", FAKE_MP3, "audio/mpeg")},
        headers=admin_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert data["title"]      # falls back to filename stem
    assert data["artist"]
    assert data["filename"].endswith(".mp3")
    # Cleanup
    client.delete(f"/api/admin/songs/{data['id']}", headers=admin_headers)


def test_upload_song_invalid_extension(client, admin_headers):
    r = client.post(
        "/api/admin/songs",
        files={"file": ("song.exe", b"binary", "application/octet-stream")},
        headers=admin_headers,
    )
    assert r.status_code == 400


def test_upload_song_empty_file(client, admin_headers):
    r = client.post(
        "/api/admin/songs",
        files={"file": ("empty.mp3", b"", "audio/mpeg")},
        headers=admin_headers,
    )
    assert r.status_code == 400


def test_upload_song_viewer_forbidden(client, viewer_headers):
    r = client.post(
        "/api/admin/songs",
        files={"file": ("song.mp3", FAKE_MP3, "audio/mpeg")},
        headers=viewer_headers,
    )
    assert r.status_code == 403


def test_upload_song_unauthenticated(client):
    r = client.post(
        "/api/admin/songs",
        files={"file": ("song.mp3", FAKE_MP3, "audio/mpeg")},
    )
    assert r.status_code == 401


# ── list ──────────────────────────────────────────────────────────────────────

def test_admin_list_songs(client, admin_headers, uploaded_song):
    r = client.get("/api/admin/songs", headers=admin_headers)
    assert r.status_code == 200
    songs = r.json()
    assert isinstance(songs, list)
    ids = [s["id"] for s in songs]
    assert uploaded_song["id"] in ids


def test_admin_list_songs_has_love_count(client, admin_headers, uploaded_song):
    r = client.get("/api/admin/songs", headers=admin_headers)
    assert r.status_code == 200
    song = next(s for s in r.json() if s["id"] == uploaded_song["id"])
    assert "love_count" in song


def test_admin_list_songs_viewer_forbidden(client, viewer_headers):
    r = client.get("/api/admin/songs", headers=viewer_headers)
    assert r.status_code == 403


def test_admin_list_songs_unauthenticated(client):
    r = client.get("/api/admin/songs")
    assert r.status_code == 401


def test_admin_search_songs(client, admin_headers, uploaded_song):
    # parse_tags falls back to the UUID stem as title; use the actual stored title
    title = uploaded_song["title"]
    r = client.get(f"/api/admin/songs?search={title}", headers=admin_headers)
    assert r.status_code == 200
    ids = [s["id"] for s in r.json()]
    assert uploaded_song["id"] in ids


# ── update ────────────────────────────────────────────────────────────────────

def test_update_song_title_and_artist(client, admin_headers, uploaded_song):
    song_id = uploaded_song["id"]
    r = client.patch(
        f"/api/admin/songs/{song_id}",
        json={"title": "New Title", "artist": "New Artist"},
        headers=admin_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "New Title"
    assert data["artist"] == "New Artist"


def test_update_song_partial(client, admin_headers, uploaded_song):
    song_id = uploaded_song["id"]
    r = client.patch(
        f"/api/admin/songs/{song_id}",
        json={"title": "Only Title Changed"},
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Only Title Changed"


def test_update_song_not_found(client, admin_headers):
    r = client.patch(
        "/api/admin/songs/999999",
        json={"title": "Ghost"},
        headers=admin_headers,
    )
    assert r.status_code == 404


def test_update_song_viewer_forbidden(client, viewer_headers, uploaded_song):
    r = client.patch(
        f"/api/admin/songs/{uploaded_song['id']}",
        json={"title": "Hacked"},
        headers=viewer_headers,
    )
    assert r.status_code == 403


# ── delete ────────────────────────────────────────────────────────────────────

def test_delete_song(client, admin_headers):
    # Create a song specifically to delete it
    r = client.post(
        "/api/admin/songs",
        files={"file": ("to_delete.mp3", FAKE_MP3, "audio/mpeg")},
        headers=admin_headers,
    )
    assert r.status_code == 200
    song_id = r.json()["id"]

    r = client.delete(f"/api/admin/songs/{song_id}", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # Confirm it's gone
    r = client.get("/api/admin/songs", headers=admin_headers)
    ids = [s["id"] for s in r.json()]
    assert song_id not in ids


def test_delete_song_not_found(client, admin_headers):
    r = client.delete("/api/admin/songs/999999", headers=admin_headers)
    assert r.status_code == 404


def test_delete_song_viewer_forbidden(client, viewer_headers, uploaded_song):
    r = client.delete(f"/api/admin/songs/{uploaded_song['id']}", headers=viewer_headers)
    assert r.status_code == 403
