"""Tests for /api/songs/* (player-facing) endpoints."""


# ── song list ─────────────────────────────────────────────────────────────────

def test_list_songs_unauthenticated(client):
    r = client.get("/api/songs")
    assert r.status_code == 401


def test_list_songs_returns_list(client, viewer_headers):
    r = client.get("/api/songs", headers=viewer_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_songs_shape(client, viewer_headers, uploaded_song):
    r = client.get("/api/songs", headers=viewer_headers)
    assert r.status_code == 200
    songs = r.json()
    assert len(songs) >= 1
    # Verify all required fields are present on every item
    for song in songs:
        assert "id" in song
        assert "title" in song
        assert "artist" in song
        assert "filename" in song
        assert "love_count" in song
        assert "is_loved" in song


def test_list_songs_search_match(client, viewer_headers, uploaded_song):
    # parse_tags falls back to the UUID stem as the title; use the actual title
    title = uploaded_song["title"]
    r = client.get(f"/api/songs?search={title}", headers=viewer_headers)
    assert r.status_code == 200
    ids = [s["id"] for s in r.json()]
    assert uploaded_song["id"] in ids


def test_list_songs_search_no_match(client, viewer_headers):
    r = client.get("/api/songs?search=zzz_this_title_does_not_exist_zzz", headers=viewer_headers)
    assert r.status_code == 200
    assert r.json() == []


# ── stream ────────────────────────────────────────────────────────────────────

def test_stream_unauthenticated(client, uploaded_song):
    r = client.get(f"/api/songs/{uploaded_song['id']}/stream")
    assert r.status_code == 401


def test_stream_not_found(client, viewer_headers):
    r = client.get("/api/songs/999999/stream", headers=viewer_headers)
    assert r.status_code == 404


def test_stream_returns_audio(client, viewer_headers, uploaded_song):
    r = client.get(f"/api/songs/{uploaded_song['id']}/stream", headers=viewer_headers)
    # File exists on disk (we uploaded it), so we expect 200
    assert r.status_code == 200
    assert len(r.content) > 0


# ── love / unlove ─────────────────────────────────────────────────────────────

def test_love_song(client, viewer_headers, uploaded_song):
    song_id = uploaded_song["id"]
    r = client.post(f"/api/songs/{song_id}/love", headers=viewer_headers)
    assert r.status_code == 200
    assert r.json()["loved"] is True


def test_love_song_idempotent(client, viewer_headers, uploaded_song):
    song_id = uploaded_song["id"]
    client.post(f"/api/songs/{song_id}/love", headers=viewer_headers)
    r = client.post(f"/api/songs/{song_id}/love", headers=viewer_headers)
    assert r.status_code == 200
    assert r.json()["loved"] is True
    assert "already" in r.json().get("message", "").lower()


def test_unlove_song(client, viewer_headers, uploaded_song):
    song_id = uploaded_song["id"]
    client.post(f"/api/songs/{song_id}/love", headers=viewer_headers)
    r = client.delete(f"/api/songs/{song_id}/love", headers=viewer_headers)
    assert r.status_code == 200
    assert r.json()["loved"] is False


def test_unlove_not_loved(client, viewer_headers, uploaded_song):
    song_id = uploaded_song["id"]
    # Ensure it's not loved first
    client.delete(f"/api/songs/{song_id}/love", headers=viewer_headers)
    r = client.delete(f"/api/songs/{song_id}/love", headers=viewer_headers)
    assert r.status_code == 200
    assert r.json()["loved"] is False


def test_love_nonexistent_song(client, viewer_headers):
    r = client.post("/api/songs/999999/love", headers=viewer_headers)
    assert r.status_code == 404


def test_love_count_reflects_loves(client, viewer_headers, admin_headers, uploaded_song):
    song_id = uploaded_song["id"]
    client.delete(f"/api/songs/{song_id}/love", headers=viewer_headers)  # start clean
    client.post(f"/api/songs/{song_id}/love", headers=viewer_headers)
    r = client.get("/api/songs", headers=viewer_headers)
    song = next(s for s in r.json() if s["id"] == song_id)
    assert song["love_count"] >= 1
    assert song["is_loved"] is True


# ── auto-change background setting ───────────────────────────────────────────

def test_auto_change_setting_unauthenticated(client):
    r = client.get("/api/songs/settings/auto-change-bg")
    assert r.status_code == 401


def test_auto_change_setting_authenticated(client, viewer_headers):
    r = client.get("/api/songs/settings/auto-change-bg", headers=viewer_headers)
    assert r.status_code == 200
    assert "auto_change_background" in r.json()
