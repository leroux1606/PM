import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth import reset_sessions
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PM_DATABASE_PATH", str(tmp_path / "ai.db"))
    reset_sessions()
    with TestClient(app) as c:
        yield c


def _login(c: TestClient) -> None:
    r = c.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert r.status_code == 200


def test_ai_smoke_requires_auth(client: TestClient) -> None:
    assert client.post("/api/ai/smoke", json={"message": "hi"}).status_code == 401


def test_ai_smoke_without_api_key_returns_503(client: TestClient, monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    _login(client)
    r = client.post("/api/ai/smoke", json={"message": "hi"})
    assert r.status_code == 503
    assert "OPENROUTER_API_KEY" in r.json()["detail"]


def test_ai_smoke_returns_mocked_reply(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    _login(client)
    with patch(
        "app.ai_client.chat_completion",
        new_callable=AsyncMock,
        return_value="4",
    ) as m:
        r = client.post("/api/ai/smoke", json={"message": "What is 2+2?"})
    assert r.status_code == 200
    assert r.json() == {"reply": "4"}
    m.assert_called_once_with("What is 2+2?")


@pytest.mark.integration
def test_ai_smoke_live_openrouter(client: TestClient, monkeypatch) -> None:
    if os.environ.get("RUN_OPENROUTER_INTEGRATION") != "1":
        pytest.skip("Set RUN_OPENROUTER_INTEGRATION=1 to run (uses real API).")
    if not os.environ.get("OPENROUTER_API_KEY", "").strip():
        pytest.skip("OPENROUTER_API_KEY not set.")
    _login(client)
    r = client.post(
        "/api/ai/smoke",
        json={"message": "Reply with exactly one word: pong"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "reply" in body
    assert len(body["reply"]) > 0
