# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Kanban-based project management MVP. Next.js 16 frontend (static export) served by a FastAPI backend over SQLite. AI chat powered by OpenRouter. Containerized with Podman.

## Commands

### Container (primary dev workflow)

```bash
scripts/start.sh          # Build and start Podman stack (auto-copies .env.example → .env if missing)
scripts/stop.sh           # Stop and remove containers
podman compose up -d --build  # Manual equivalent
```

App runs at `http://127.0.0.1:8001/`.

### Backend

```bash
cd backend
uv sync --all-groups              # Install all dependencies including dev
uv run uvicorn app.main:app --host 127.0.0.1 --port 8001  # Run directly
uv run pytest                     # All tests
uv run pytest tests/test_auth.py  # Single file
uv run pytest tests/test_auth.py::test_login_success_sets_http_only_cookie  # Single test
RUN_OPENROUTER_INTEGRATION=1 uv run pytest -m integration  # Live OpenRouter tests (needs OPENROUTER_API_KEY)
```

### Frontend

```bash
cd frontend
npm install
npm run dev               # Dev server on :3000 with proxy to backend :8001
npm run build:site        # Static export → copies output to backend/site/
npm run test:unit         # Vitest
npm run test:e2e          # Playwright (builds first, or set PW_USE_NEXT_DEV=1 for dev server)
npm run test:all          # Both
npm run lint              # ESLint
```

## Architecture

### Request Flow

1. Static frontend (`frontend/out/`) is copied to `backend/site/` at build time.
2. FastAPI serves the static site at `/` and all API routes under `/api/*`.
3. In container: uvicorn on port 8000, mapped to host port 8001.
4. In dev: Next.js dev server on :3000 proxies `/api/*` to backend on :8001.

### Backend (`backend/app/`)

- **`main.py`** — FastAPI app with lifespan (DB init + user seed), mounts static files, registers routers.
- **`db.py`** — SQLite via stdlib `sqlite3`. Tables: `users`, `sessions`, `kanban_boards`. Demo user `user`/`password` seeded on startup. Board stored as a single JSON blob per user.
- **`auth.py`** — HTTP-only `pm_session` cookie; in-memory session dict (SQLite session table exists but is not used yet). 7-day TTL.
- **`board.py`** — GET/PUT board JSON validated by Pydantic `BoardData`. Cross-field validator ensures all card IDs referenced in columns exist in the cards map. Schema version: `BOARD_JSON_SCHEMA_VERSION = 1`.
- **`ai_client.py`** — OpenRouter HTTP wrapper. `chat_completion()` and `chat_json_completion()`. Model: `openai/gpt-oss-120b`. No key → 503; request failure → 502.
- **`ai_routes.py`** — `/api/ai/smoke` (simple text reply) and `/api/ai/chat` (structured `AiKanbanResponse`: `assistant_message` + optional `board` update).

### Frontend (`frontend/src/`)

- **`app/page.tsx`** — Kanban board root page, wrapped in `AuthGate`.
- **`app/login/page.tsx`** — Login form.
- **`components/`** — `KanbanBoard`, `KanbanColumn`, `KanbanCard`, `ChatSidebar`. Drag-and-drop via `@dnd-kit`.
- **`lib/boardApi.ts`** — Fetch/save board state. Auto-save is debounced 450ms on board changes.
- **`lib/aiChatApi.ts`** — Sends chat messages; response may include a full board replacement.

### Board JSON Shape

```json
{
  "columns": [{ "id": "col-1", "title": "To Do", "cardIds": ["card-1"] }],
  "cards": { "card-1": { "id": "card-1", "title": "Task", "details": "" } }
}
```

### Environment Variables

See `.env.example`. Key vars:
- `OPENROUTER_API_KEY` — required for AI features; without it `/api/ai/*` returns 503.
- `PM_DATABASE_PATH` — overrides default `backend/data/pm.db` (Podman uses `/data/pm.db`).

## Coding Standards

From `AGENTS.md`:
- Use latest library versions; idiomatic approaches.
- Keep it simple — no over-engineering, no unnecessary defensive programming.
- Be concise; no emojis ever.
- Root cause analysis before fixing; prove with evidence.
