import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ping() -> None:
    response = client.get("/ping")
    assert response.status_code == 200
    body = response.json()
    assert body.get("service") == "pm-mvp-backend"
    assert body.get("ok") == "true"


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_hello() -> None:
    response = client.get("/api/hello")
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Hello from the API"


def test_login_page_serves_html() -> None:
    response = client.get("/login")
    if response.status_code == 404:
        pytest.skip(
            "backend/site/login.html missing; from frontend/: npm run build && node scripts/copy-site.mjs"
        )
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Sign in" in response.text


def test_index_serves_app_html() -> None:
    response = client.get("/")
    if response.status_code == 503:
        pytest.skip(
            "backend/site missing; from frontend/: npm run build && node scripts/copy-site.mjs"
        )
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    text = response.text
    assert "Kanban Studio" in text or "Loading" in text or "login" in text.lower()
