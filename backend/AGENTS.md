# Backend (FastAPI)

Python **FastAPI** app under **`app/`**, managed with **`uv`** (`pyproject.toml`, **`uv.lock`**).

## Layout

| Path | Role |
|------|------|
| `app/main.py` | FastAPI: **`/ping`**, **`/api/health`**, **`/api/hello`**, auth **`/api/auth/*`**, static **`/`** from **`site/`** (when present). |
| `app/auth.py` | Demo login **`user` / `password`**, in-memory sessions, **`pm_session`** HttpOnly cookie. |
| `site/` | **Generated**: copy of **`frontend/out/`** (run **`npm run build:site`** from **`frontend/`**). Gitignored. In Podman, the **`Containerfile`** fills this from the frontend build stage. |
| `tests/test_smoke.py` | Pytest smoke tests (TestClient). |

## Run locally (host)

After **`npm run build:site`** from **`frontend/`** (creates **`backend/site/`**):

```text
uv sync --all-groups
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

## Run in Podman

See **`docs/DEV_CONTAINER.md`**. Image build uses repo root **`Containerfile`** (multi-stage: Node build + Python); **`compose.yaml`** publishes the app on **host port 8001** (container internal port **8000**).

## Tests

```text
uv run pytest
```

Run **`npm run build:site`** first if you want the Kanban index test (not skipped).
