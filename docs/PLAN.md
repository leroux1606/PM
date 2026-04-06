# Project execution plan

This document expands the high-level phases into checklists, tests, and success criteria. Check items off as work completes. **User sign-off is required after Part 1 (this document) and after Part 5 (database design).**

## Locked decisions

| Topic | Decision |
|--------|-----------|
| Kanban persistence | Store board state **as JSON** in SQLite (per user), not a fully normalized relational model of every card field. |
| Session auth (MVP) | **HTTP-only session cookie** plus **server-side session** (memory or SQLite-backed). No JWT unless a later phase requires it. |
| HTTP port | **Any**; document the chosen port in scripts/README when fixed. |
| Frontend tooling | Match the **existing demo**: `package-lock.json` and **npm** scripts in `frontend/` (not pnpm unless migrated later). |
| AI | OpenRouter, model **`openai/gpt-oss-120b`**; `OPENROUTER_API_KEY` from environment at **runtime** (do not bake secrets into the container image). |
| Database product | **SQLite**; create DB file if missing. |
| Podman (local dev) | **`Containerfile`** and **`compose.yaml`** at repo root for **local containerized development** only (`podman build`, **`podman compose`**). Scripts should use compose—not undocumented one-off `podman run`. Not a production deployment mandate. |

## Test stack (project-wide)

Use this stack consistently; add tools only when a phase explicitly needs them.

| Layer | Tooling |
|--------|---------|
| Frontend unit / component | **Vitest**, **@testing-library/react**, **jsdom** (already in `frontend/`). |
| Frontend E2E | **Playwright** (already in `frontend/`). |
| Backend API | **pytest** with **httpx** `AsyncClient` (or Starlette/FastAPI `TestClient`) for route tests. |
| Backend AI / OpenRouter | pytest with **mocked HTTP** for unit tests; optional manual or integration check with real key behind a flag. |

Success criteria for "tests pass" in each phase: relevant automated tests green; no new linter errors in touched code.

---

## Part 1: Plan

**Goal:** Executable plan, frontend code map, and approval before scaffolding.

### Checklist

- [x] Enrich this `docs/PLAN.md` with phases, checklists, and success criteria (this file).
- [x] Add `frontend/AGENTS.md` describing the existing demo app.
- [ ] User reviews and **approves** this plan and the database direction (JSON in SQLite) at a high level.

### Tests

- N/A (documentation only).

### Success criteria

- Plan and `frontend/AGENTS.md` exist and match repo reality.
- User explicit approval recorded (comment, issue, or commit message as project prefers).

---

## Part 2: Scaffolding

**Goal:** Local Podman-based dev workflow (`Containerfile`, `compose.yaml`), `backend/` FastAPI app, `scripts/` start/stop for Mac/Windows/Linux, static hello page and a working API call path.

### Checklist

- [x] Add **`Containerfile`** at repo root (`podman build -f Containerfile .`). No Dockerfile-only path; **Containerfile** is required.
- [x] Add **`compose.yaml`** at repo root defining the app service (build context, ports, volumes for SQLite DB if persisted, `env_file` for `.env`). Document **`podman compose up`** / **`podman compose build`** in minimal README or `docs/`.
- [x] Create `backend/` with FastAPI app, single health or hello route and one JSON API route.
- [x] Serve **example static HTML** at `/` (or agreed path) from FastAPI until Part 3 replaces it with Next build output.
- [x] Add `scripts/` start and stop scripts for **Mac, Windows, Linux** (invoke **`podman compose`** using repo **`compose.yaml`**, or thin wrappers around the same).
- [x] **Runtime env** for secrets: document passing `--env-file` or `-e` for `OPENROUTER_API_KEY` later; no keys in image layers (see **`docs/DEV_CONTAINER.md`**, **`.env.example`**).

### Tests

- [x] Backend: pytest smoke test that hits hello/health and JSON route (in-process client).

### Success criteria

- On a dev machine with Podman: **`podman compose`** (using **`compose.yaml`**) brings up the local stack; **`Containerfile`** builds successfully; open `/` and see hello HTML.
- API returns expected JSON from host or documented URL.
- Start/stop scripts work on target OSes without manual Podman flags undocumented.

---

## Part 3: Add in Frontend

**Goal:** Production Next.js build output is served at `/` by FastAPI; Kanban demo visible; automated tests cover core behavior.

### Checklist

- [x] Wire static export or `out/` / `.next/static` serving strategy (align with Next version in `frontend/`).
- [x] FastAPI serves the built frontend at `/` (and forwards API under e.g. `/api` or `/api/v1`).
- [x] Confirm Kanban board UI matches current demo at `/` when run through the container.

### Tests

- [x] `frontend`: existing Vitest + Playwright suites still pass against built/served app (adjust base URL / webServer in Playwright as needed).
- [x] Add or update tests if routes or asset paths change.

### Success criteria

- Kanban board loads at `/` via the unified server (not only `next dev`).
- CI or local script can run unit + e2e against the integrated setup.

---

## Part 4: Fake user sign-in

**Goal:** Unauthenticated users cannot see the board; login `user` / `password`; logout clears session.

### Checklist

- [x] Login page or modal; POST credentials to backend; set **HTTP-only** session cookie.
- [x] Server-side session store keyed by session id; reject invalid/expired sessions.
- [x] Protected route or layout: redirect to login if not authenticated.
- [x] Logout endpoint and UI control.

### Tests

- [x] Backend pytest: login success/failure, cookie attributes, protected route 401/redirect behavior.
- [x] Playwright: cannot see board without login; can after login; logout hides board.

### Success criteria

- Wrong password never issues a valid session.
- Session cookie is HTTP-only; MVP secure flags documented for local vs production.

---

## Part 5: Database modeling

**Goal:** Schema and docs for SQLite + JSON Kanban; user sign-off before heavy API work.

### Checklist

- [x] Define tables: at minimum **users** (or single-user placeholder with future multi-user columns), **session** storage if not only in-memory, and **kanban JSON** per user (column name and migration/versioning approach).
- [x] Save an example JSON shape matching `BoardData` in `frontend/src/lib/kanban.ts` (or documented delta) in `docs/`.
- [x] Document create-if-not-exists path for DB file location in container/volume.

### Tests

- [x] N/A or light migration smoke test once ORM/raw SQL layer exists.

### Success criteria

- `docs/` contains accurate ERD or table list + example JSON payload.
- **User sign-off** on schema before Part 6 implementation proceeds.

---

## Part 6: Backend (Kanban API)

**Goal:** CRUD/read-write API for the signed-in user’s Kanban JSON; DB auto-created.

### Checklist

- [x] GET board for current user (default empty board shape if none).
- [x] PATCH or PUT to replace/update board JSON with validation.
- [x] All routes require authenticated session from Part 4.
- [x] SQLite file created on first run if missing.

### Tests

- [x] pytest: full API coverage for happy paths and auth failures; concurrent requests optional for MVP.

### Success criteria

- API alone can drive board lifecycle without the frontend (manual or automated).

---

## Part 7: Frontend + Backend integration

**Goal:** UI uses real API; persistence across refresh; thorough automated tests.

### Checklist

- [x] Replace local-only `useState` seed with load from API after login.
- [x] Debounce or explicit save for column rename, drag, add, delete (choose simplest consistent strategy).
- [x] Error handling for network/API errors (minimal, per project standards).

### Tests

- [x] Playwright: login, mutate board, reload, assert persistence.
- [x] Vitest for any extracted client logic.

### Success criteria

- Refresh after changes shows the same board.
- Tests run against backend + DB in test harness or container.

---

## Part 8: AI connectivity

**Goal:** Backend calls OpenRouter; smoke test e.g. "2+2".

### Checklist

- [x] Config: `OPENROUTER_API_KEY`, base URL, model `openai/gpt-oss-120b` from env.
- [x] Single endpoint or internal function that performs one chat completion.
- [x] Document how to run integration test with real key vs mocked tests in CI.

### Tests

- [x] pytest with mocked OpenRouter HTTP; optional marked integration test with real API.

### Success criteria

- With valid key, smoke request returns a sensible answer; failures surface clearly in logs.

---

## Part 9: AI + Kanban structured outputs

**Goal:** Request includes Kanban JSON + user message + history; response schema includes assistant text and optional board update.

### Checklist

- [x] Define JSON schema / structured output format agreed with the model (OpenRouter structured outputs).
- [x] Apply board updates only after validation; reject malformed AI payloads safely.
- [x] Persist updated board when applied.

### Tests

- [x] pytest: fixture AI responses (mocked) update board correctly; invalid payloads do not corrupt DB.

### Success criteria

- End-to-end path: user message in, structured response out, board updates when present.

---

## Part 10: AI chat sidebar UI

**Goal:** Sidebar chat UX; LLM-driven board updates; UI refreshes when board changes.

### Checklist

- [x] Sidebar component(s) under `frontend/src/components/` (and `ui` subfolder if shared primitives are added) per project conventions.
- [x] Chat history display; send message; loading/error states.
- [x] On successful structured board update from API, refetch or merge state and re-render Kanban.

### Tests

- [x] Playwright: send message (mock backend or stub) and assert UI refresh hook fires when board changes.
- [x] Component tests for sidebar if logic warrants.

### Success criteria

- Polished UI aligned with existing color tokens and typography.
- User sees assistant reply and board changes without manual refresh.

---

## Original high-level phases (reference)

1. Plan (this document + `frontend/AGENTS.md` + approval).
2. Scaffolding (`Containerfile`, `compose.yaml`, FastAPI, scripts, hello + API).
3. Static Next at `/`, Kanban visible, tests.
4. Fake login/logout, tests.
5. DB model (JSON in SQLite), docs, sign-off.
6. Backend Kanban API, pytest.
7. Frontend wired to API, persistence, tests.
8. OpenRouter connectivity smoke test.
9. Structured outputs + Kanban in payload, tests.
10. Sidebar chat + auto-refresh on board updates.
