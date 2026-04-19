"""Smoke tests: public pages and status endpoints."""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_version(client):
    r = client.get("/version")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "build_sha" in data
    assert "build_id" in data


def test_player_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "NivPro" in r.text


def test_admin_page(client):
    r = client.get("/admin")
    assert r.status_code == 200
    assert "Admin" in r.text
