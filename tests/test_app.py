from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_player_page():
    r = client.get("/")
    assert r.status_code == 200
    assert "NivPro" in r.text


def test_admin_page():
    r = client.get("/admin")
    assert r.status_code == 200
    assert "Admin" in r.text
