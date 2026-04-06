# Local development (Podman)

The stack is defined by **`Containerfile`** (image build) and **`compose.yaml`** (local dev run). This is for **local containerized development** only.

## Prerequisites

- [Podman](https://podman.io/) with Compose support (`podman compose`).

## First run

1. From the repository root, ensure `.env` exists. The start scripts copy **`.env.example`** to **`.env`** if missing.
2. Set `OPENROUTER_API_KEY` in `.env` when you add AI features (Part 8+). Do not commit real keys; do not bake keys into images.
3. Start: **`scripts/start.sh`** (macOS/Linux) or **`scripts/start.ps1`** (Windows), or manually:

```text
podman compose up -d --build
```

4. Open **`http://127.0.0.1:8001/`** for the **Kanban** UI (Next static export). API: **`http://127.0.0.1:8001/api/hello`**, **`http://127.0.0.1:8001/api/health`**, **`http://127.0.0.1:8001/ping`**. (Compose maps **host port 8001** to **container port 8000** so this app does not fight other tools that use **8000** on your machine.)

The **`Containerfile`** builds the frontend (`npm run build`) and copies **`out/`** into the image as **`/app/site`** for FastAPI to serve.

## Stop

- **`scripts/stop.sh`** or **`scripts/stop.ps1`**, or: `podman compose down`.

## Ports and data

- **On your PC:** use **`http://127.0.0.1:8001`** (see `compose.yaml`: **`8001:8000`**). **Inside** the container, uvicorn still listens on **8000**; only the published host port is **8001**. Change the left side of the mapping in `compose.yaml` if you need another host port.
- Volume **`pm_data`** is mounted at **`/data`** in the container. **`compose.yaml`** sets **`PM_DATABASE_PATH=/data/pm.db`** so SQLite lives on the volume (see **`docs/DATABASE.md`**). Local runs without Compose default to **`backend/data/pm.db`** when **`PM_DATABASE_PATH`** is unset.

## Backend tests (host, not container)

From **`frontend/`**, produce **`backend/site/`** once:

```text
npm run build:site
```

From **`backend/`**:

```text
uv sync --all-groups
uv run pytest
```

The index HTML test is skipped if **`backend/site/`** is missing.

## Runtime secrets

Pass or edit `.env` at compose time. Prefer **env file on the host** over embedding secrets in the **`Containerfile`**.

## OpenRouter / AI smoke (Part 8)

- Configure **`OPENROUTER_API_KEY`** in **`.env`** (see **`.env.example`**). Optional: **`OPENROUTER_BASE_URL`** (default `https://openrouter.ai/api/v1`), **`OPENROUTER_MODEL`** (default `openai/gpt-oss-120b`).
- After signing in, **`POST /api/ai/smoke`** with JSON body `{"message":"..."}` returns `{"reply":"..."}`. **`POST /api/ai/chat`** accepts `{"message":"...","history":[]}` (optional chat turns) and returns `assistant_message`, `board_updated`, and optional `board`; the model is asked for JSON (`response_format` **json_object**) matching **`AiKanbanResponse`** (see **`app/ai_schemas.py`**). Valid `board` updates are saved like **`PUT /api/board`**. Without a key, AI endpoints respond with **503** and a clear message.
- **Tests:** normal **`uv run pytest`** mocks OpenRouter and does not call the network. To run the optional live call (uses your key and quota), set **`RUN_OPENROUTER_INTEGRATION=1`**, ensure **`OPENROUTER_API_KEY`** is in the environment, then: **`uv run pytest -m integration`**.

## Session cookie (Part 4)

The **`pm_session`** cookie is **HttpOnly**, **SameSite=Lax**, and **`Secure` is off** for local HTTP. Behind HTTPS in production, set **`Secure`** on the cookie (code change in `app/auth.py`) so it is only sent over TLS.

## If you see `{"detail":"Not Found"}`

That response is only from **this** FastAPI app. Use it to see whether your browser is really talking to **`pm-mvp`** on **host port 8001** (not 8000).

1. Open **`http://127.0.0.1:8001/ping`** first. You should get JSON with `"service":"pm-mvp-backend"`.  
   - If **`/ping` is 404** too, the request is **not** reaching this code (wrong port, different process, or an old image still running).  
   - If **`/ping` works** but **`/api/health` does not**, say so; that should not happen on current code.

2. **Rebuild** so the container cannot use a cached old layer:

```text
podman compose down
podman compose build --no-cache
podman compose up -d
```

3. Prefer **`http://127.0.0.1:8001/...`** for Podman (see `compose.yaml`). Use **`localhost`** only if you know it resolves the same as **`127.0.0.1`** on your system.

4. Run **`podman ps`** and confirm the container maps **`0.0.0.0:8001`** (or similar) to **`8000/tcp`** inside the container.

5. Quick check **without Podman**: from **`frontend/`**, `npm run build:site`, then from **`backend/`**, `uv run uvicorn app.main:app --host 127.0.0.1 --port 8001`, then open **`http://127.0.0.1:8001/ping`** and **`http://127.0.0.1:8001/`** (Kanban). Stop the server with Ctrl+C when done. Use any free host port if **8001** is taken (and match it in the browser).
