import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth import reset_sessions
from app.main import app

MIN_BOARD = {
    "columns": [{"id": "c1", "title": "T", "cardIds": ["x"]}],
    "cards": {"x": {"id": "x", "title": "Card", "details": ""}},
}

AI_UPDATE_JSON = json.dumps(
    {
        "assistant_message": "Added.",
        "board": {
            "columns": [{"id": "c1", "title": "T", "cardIds": ["n1"]}],
            "cards": {"n1": {"id": "n1", "title": "New", "details": "d"}},
        },
    }
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PM_DATABASE_PATH", str(tmp_path / "chat.db"))
    reset_sessions()
    with TestClient(app) as c:
        yield c


def _login(c: TestClient) -> None:
    assert (
        c.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        ).status_code
        == 200
    )


def test_chat_requires_auth(client: TestClient) -> None:
    assert client.post("/api/ai/chat", json={"message": "hi"}).status_code == 401


def test_chat_updates_board_when_valid(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    _login(client)
    with patch(
        "app.ai_client.chat_json_completion",
        new_callable=AsyncMock,
        return_value=AI_UPDATE_JSON,
    ):
        r = client.post("/api/ai/chat", json={"message": "Please update"})
    assert r.status_code == 200
    body = r.json()
    assert body["assistant_message"] == "Added."
    assert body["board_updated"] is True
    assert body["board"]["cards"]["n1"]["title"] == "New"

    g = client.get("/api/board")
    assert g.status_code == 200
    assert g.json()["cards"]["n1"]["title"] == "New"


def test_chat_null_board_does_not_change_db(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    _login(client)
    client.put("/api/board", json=MIN_BOARD)
    payload = json.dumps(
        {"assistant_message": "No change.", "board": None},
    )
    with patch(
        "app.ai_client.chat_json_completion",
        new_callable=AsyncMock,
        return_value=payload,
    ):
        r = client.post("/api/ai/chat", json={"message": "Hi"})
    assert r.status_code == 200
    assert r.json()["board_updated"] is False
    assert client.get("/api/board").json() == MIN_BOARD


def test_chat_invalid_json_does_not_corrupt_db(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    _login(client)
    client.put("/api/board", json=MIN_BOARD)
    with patch(
        "app.ai_client.chat_json_completion",
        new_callable=AsyncMock,
        return_value="NOT JSON",
    ):
        r = client.post("/api/ai/chat", json={"message": "Hi"})
    assert r.status_code == 502
    assert client.get("/api/board").json() == MIN_BOARD


def test_chat_invalid_board_schema_does_not_corrupt_db(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    _login(client)
    client.put("/api/board", json=MIN_BOARD)
    bad = json.dumps(
        {
            "assistant_message": "bad",
            "board": {
                "columns": [{"id": "c1", "title": "T", "cardIds": ["missing"]}],
                "cards": {},
            },
        }
    )
    with patch(
        "app.ai_client.chat_json_completion",
        new_callable=AsyncMock,
        return_value=bad,
    ):
        r = client.post("/api/ai/chat", json={"message": "Hi"})
    assert r.status_code == 502
    assert client.get("/api/board").json() == MIN_BOARD


def test_chat_without_key_returns_503(client: TestClient, monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    _login(client)
    r = client.post("/api/ai/chat", json={"message": "Hi"})
    assert r.status_code == 503
