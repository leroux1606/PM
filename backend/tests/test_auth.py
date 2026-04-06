import pytest
from fastapi.testclient import TestClient

from app.auth import reset_sessions
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("PM_DATABASE_PATH", str(tmp_path / "auth.db"))
    reset_sessions()
    with TestClient(app) as c:
        yield c


def test_login_success_sets_http_only_cookie(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
    set_cookie = response.headers.get("set-cookie", "")
    assert "HttpOnly" in set_cookie or "httponly" in set_cookie.lower()
    assert "pm_session=" in set_cookie


def test_login_wrong_password(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PM_DATABASE_PATH", str(tmp_path / "auth.db"))
    reset_sessions()
    with TestClient(app) as c:
        response = c.post(
            "/api/auth/login",
            json={"username": "user", "password": "wrong"},
        )
        assert response.status_code == 401
        assert c.get("/api/auth/me").status_code == 401


def test_me_after_login(client: TestClient) -> None:
    client.post("/api/auth/login", json={"username": "user", "password": "password"})
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "user"


def test_me_without_cookie(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PM_DATABASE_PATH", str(tmp_path / "auth.db"))
    reset_sessions()
    with TestClient(app) as c:
        assert c.get("/api/auth/me").status_code == 401


def test_logout_clears_session(client: TestClient) -> None:
    client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert client.get("/api/auth/me").status_code == 200
    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401
