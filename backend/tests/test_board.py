import pytest
from fastapi.testclient import TestClient

from app.auth import reset_sessions
from app.main import app

MIN_BOARD = {
    "columns": [{"id": "c1", "title": "T", "cardIds": ["x"]}],
    "cards": {"x": {"id": "x", "title": "Card", "details": ""}},
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PM_DATABASE_PATH", str(tmp_path / "t.db"))
    reset_sessions()
    with TestClient(app) as c:
        yield c


def _login(c: TestClient) -> None:
    r = c.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert r.status_code == 200


def test_get_board_unauthorized(client: TestClient) -> None:
    assert client.get("/api/board").status_code == 401


def test_get_board_empty_after_login(client: TestClient) -> None:
    _login(client)
    r = client.get("/api/board")
    assert r.status_code == 200
    assert r.json() == {"columns": [], "cards": {}}


def test_put_get_roundtrip(client: TestClient) -> None:
    _login(client)
    assert client.put("/api/board", json=MIN_BOARD).status_code == 200
    g = client.get("/api/board")
    assert g.status_code == 200
    assert g.json() == MIN_BOARD


def test_put_invalid_card_reference(client: TestClient) -> None:
    _login(client)
    bad = {
        "columns": [{"id": "c1", "title": "T", "cardIds": ["missing"]}],
        "cards": {},
    }
    assert client.put("/api/board", json=bad).status_code == 422
