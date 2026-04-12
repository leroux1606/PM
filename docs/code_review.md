# Code Review

**Date:** 2026-04-12
**Scope:** Full repository — backend, frontend, tests, infrastructure.
**Basis:** All source files read and analysed; test suite confirmed green (25 backend + 12 unit + 8 E2E passing).

Findings are grouped by area and ordered from most to least severe within each group. Each entry notes the relevant file and line.

---/

## 1. Security

### 1.1 Real API key committed in `.env.example` — CRITICAL

**File:** `.env.example:4`

```
OPENROUTER_API_KEY=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
```

`.env.example` is committed to source control. This key is now in git history and should be treated as compromised. The example file should only ever contain a placeholder.

**Action:** Revoke this key in the OpenRouter dashboard immediately. Replace the value with a placeholder such as `sk-or-v1-your-key-here`.

---

### 1.2 Corrupted `.env.example`

**File:** `.env.example:12`

The file ends with the literal text `run all test`, which appears to have been typed into the wrong window. This would cause any tool that validates the env file to fail, and it is confusing for anyone reading the file.

**Action:** Remove that line.

---

### 1.3 Static, shared PBKDF2 salt

**File:** `backend/app/db.py:17`

```python
_SALT = b"pm-mvp-v1"
```

All users share the same salt. If the password database were leaked, a single rainbow table built against this salt would crack every user's password at once. The standard practice is to generate a random, per-user salt and store it alongside the hash (e.g. as a hex prefix: `salt_hex:hash_hex`).

**Action:** This is MVP scope but must be addressed before any real users are added. Add a TODO comment at the constant so it is not forgotten.

---

### 1.4 `secure=False` on session cookie

**File:** `backend/app/auth.py:66`

```python
response.set_cookie(..., secure=False)
```

The cookie is transmitted over plain HTTP. This is documented as intentional for local dev, but there is no guard to prevent deploying with `secure=False` in a real environment.

**Action:** Add a `COOKIE_SECURE` environment variable (default `False` for dev, `True` for prod) and wire it to `set_cookie(secure=...)`. Add a note in `.env.example`.

---

### 1.5 Container runs as root

**File:** `Containerfile`

No `USER` instruction is present, so the process runs as root inside the container. If there is a path-traversal or code-execution vulnerability in any dependency, the attacker has root in the container.

**Action:** Add before `CMD`:
```dockerfile
RUN adduser --disabled-password --gecos "" appuser
USER appuser
```

---

## 2. Backend

### 2.1 `pydantic` not listed as an explicit dependency

**File:** `backend/pyproject.toml`

Pydantic is used directly in `board.py`, `ai_routes.py`, and `ai_schemas.py` but only arrives as a transitive dependency of FastAPI. If FastAPI ever adjusts its own pinning, the pydantic version in use could silently change.

**Action:** Add `pydantic>=2.0` to `[project] dependencies`.

---

### 2.2 History window inconsistency in AI chat

**File:** `backend/app/ai_routes.py:47` and `:87`

```python
class ChatBody(BaseModel):
    history: list[ChatTurn] = Field(default_factory=list, max_length=24)
...
for turn in body.history[-12:]:
```

The Pydantic model accepts up to 24 turns, but only the last 12 are forwarded to the model. The frontend sends the full accumulated history, so turns 13–24 are silently dropped. The limit should be consistent — either accept 12, or use all 24.

**Action:** Align the Pydantic `max_length` with the slice: change `max_length=24` to `max_length=12`, or change `[-12:]` to `[:]`.

---

### 2.3 Exception cause chain dropped in `ai_chat`

**File:** `backend/app/ai_routes.py:100–105`

```python
except httpx.HTTPError:
    logger.exception("OpenRouter request failed")
    raise HTTPException(status_code=502, detail="OpenRouter request failed.")
```

Compare with the smoke endpoint (`:63–68`) which uses `raise HTTPException(...) from e`. Losing the cause chain makes debugging harder when the 502 surfaces.

**Action:** Add `from e` to the `raise` statement.

---

### 2.4 Duplicate HTTP client logic

**File:** `backend/app/ai_client.py`

`chat_completion` (lines 22–55) and `chat_json_completion` (lines 58–93) are nearly identical — they share the same `_read_config()` call, the same `httpx.AsyncClient` block, the same error handling, and the same response-parsing logic. The only differences are the payload and the presence of `response_format`.

**Action:** Extract a private `_post_completion(payload: dict) -> str` helper and call it from both public functions, eliminating ~25 lines of duplication.

---

### 2.5 `_seed_demo_user` uses two queries where one suffices

**File:** `backend/app/db.py:71–84`

```python
conn.execute("INSERT INTO users ... WHERE NOT EXISTS ...")
conn.execute("UPDATE users SET password_hash = ? WHERE username = ?")
```

The INSERT guards against creating a duplicate; the UPDATE then overwrites the hash unconditionally. A single upsert achieves the same result:

```python
conn.execute(
    "INSERT INTO users (username, password_hash) VALUES (?, ?) "
    "ON CONFLICT(username) DO UPDATE SET password_hash = excluded.password_hash",
    (DEMO_USERNAME, h),
)
```

**Action:** Replace the two-statement pattern with the upsert above.

---

### 2.6 `typing.Optional` vs `X | None` style inconsistency

**File:** `backend/app/db.py:8` and `backend/app/ai_schemas.py:9`

`db.py` imports `from typing import Optional` and uses `Optional[int]`, while `ai_schemas.py` uses the modern `BoardData | None` syntax (Python 3.10+). Both work on Python 3.12, but the codebase should be consistent.

**Action:** Replace `Optional[X]` with `X | None` in `db.py` and remove the `Optional` import.

---

### 2.7 `test_db.py` uses `pytest.MonkeyPatch()` directly

**File:** `backend/tests/test_db.py:11`

```python
monkeypatch = pytest.MonkeyPatch()
```

The other test files receive `monkeypatch` as a fixture parameter, which pytest manages (including automatic cleanup). The manual instantiation here requires explicit `delenv` in a `finally` block to avoid leaking state.

**Action:** Accept `monkeypatch` as a fixture parameter and remove the manual cleanup.

---

### 2.8 No test for session expiry

**File:** `backend/tests/test_auth.py`

The 7-day TTL logic in `auth.py:get_session_user` is untested. An expired session must be rejected, and the stale entry must be cleaned up.

**Action:** Add a test that monkeypatches `time.time` to return a value past the expiry and asserts that `GET /api/auth/me` returns 401.

---

### 2.9 No test for `load_board_data` with corrupt JSON

**File:** `backend/app/board.py:45–57`

The silent fallback to an empty board when stored JSON is invalid is important defensive logic, but it has no test coverage.

**Action:** Add a test that writes corrupt JSON directly to the DB (bypassing the API) and asserts that `GET /api/board` returns the empty board shape.

---

## 3. Frontend

### 3.1 `board.cards[cardId]` has no undefined guard

**File:** `frontend/src/components/KanbanBoard.tsx:250`

```tsx
cards={column.cardIds.map((cardId) => board.cards[cardId])}
```

If a column's `cardIds` contains a reference to a card that does not exist in `board.cards`, this passes `undefined` to `KanbanCard`, which would cause a runtime error. The backend's `model_validator` prevents this at the API boundary, and the AI response is validated too, but the frontend has no runtime guard.

**Action:** Filter out undefined references:
```tsx
cards={column.cardIds.flatMap((id) => board.cards[id] ? [board.cards[id]] : [])}
```

---

### 3.2 Deliberately empty board reverts to demo data on reload

**File:** `frontend/src/components/KanbanBoard.tsx:49`

```tsx
setBoard(isBoardEmpty(data) ? initialData : data);
```

If a user removes all cards and columns, the server stores an empty board. On next load, `isBoardEmpty(data)` is true and the demo data is displayed instead — overwriting whatever the user did. This also does not trigger a save, so the demo data is not persisted; but the visual state is surprising.

**Action:** Show the empty board as-is, or prompt the user to add columns. If the intent is to always seed a fresh user with demo data, do it server-side (on first `GET /api/board` for a user who has never saved a board).

---

### 3.3 AI-updated board is not re-saved via the debounced save path

**File:** `frontend/src/components/KanbanBoard.tsx:61–64`

```tsx
const applyBoardFromAssistant = useCallback((data: BoardData) => {
  lastSavedJson.current = JSON.stringify(data);
  setBoard(data);
}, []);
```

`lastSavedJson.current` is set to the serialized new board before `setBoard`, so the debounced save effect's equality check (`serialized === lastSavedJson.current`) immediately passes and no save is triggered. This is correct because the backend already persists the board in `ai_routes.py` before responding. However, the logic is subtle enough to mislead future maintainers.

**Action:** Add a comment explaining why `lastSavedJson` is pre-set here (to prevent a redundant PUT, since the backend already saved during the AI response).

---

### 3.4 Hardcoded "Five columns" copy

**File:** `frontend/src/components/KanbanBoard.tsx:215`

```tsx
<p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
  One board. Five columns. Zero clutter.
</p>
```

The AI assistant can replace the board with any number of columns. After a board update with three columns, this copy is inaccurate.

**Action:** Replace with a dynamic string such as `One board. {board.columns.length} {board.columns.length === 1 ? "column" : "columns"}. Zero clutter.` or remove the column count from the copy.

---

### 3.5 `fetchBoard` response is cast, not validated at runtime

**File:** `frontend/src/lib/boardApi.ts:8`

```ts
return res.json() as Promise<BoardData>;
```

If the server returns an unexpected shape, TypeScript does not catch it at runtime — the cast is purely a compile-time assertion. Downstream code (notably `board.cards[cardId]`) could crash unexpectedly.

**Action:** For MVP this is acceptable, but note that adding a Zod schema parse here would make the data boundary explicit and the error messages actionable.

---

### 3.6 `kanban.spec.ts` drag test relies on initial server state

**File:** `frontend/tests/kanban.spec.ts:48–70`

The "moves a card between columns" test drags `card-card-1` from its assumed position in `col-backlog` to `col-review`. If a prior test mutated and persisted the board (e.g., card-1 was deleted), this test fails with a confusing missing-element error.

`chat.spec.ts` restores the board in `afterEach`, but `kanban.spec.ts` does not reset the board before or after its tests. Test order determines whether this is safe.

**Action:** Add a `beforeEach` in `kanban.spec.ts` that restores the initial board via `PUT /api/board` (mirroring `chat.spec.ts`'s `afterEach` pattern).

---

### 3.7 Chat message key uses array index

**File:** `frontend/src/components/chat/ChatSidebar.tsx:89`

```tsx
key={`${i}-${t.role}`}
```

Using the array index in a React key is discouraged when list items can be reordered or removed, because it causes stale renders. Messages are append-only here so it is harmless in practice, but it sets a bad precedent.

**Action:** Assign a stable ID when each turn is created (e.g., `crypto.randomUUID()`) and use that as the key.

---

### 3.8 `LogoutButton` has no loading state

**File:** `frontend/src/components/LogoutButton.tsx`

The logout is `async` but the button stays enabled throughout. Double-clicking would fire two simultaneous logout requests. The second request succeeds (the cookie is already cleared), but it creates unnecessary requests.

**Action:** Track a `loggingOut` state and disable the button while the request is in flight. Low priority given the MVP context.

---

## 4. Infrastructure

### 4.1 `uv:latest` tag in Containerfile

**File:** `Containerfile:15`

```dockerfile
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
```

Using `latest` means the uv version changes silently on each build. If uv introduces a breaking change, the build breaks with no indication of what changed.

**Action:** Pin to a specific version: `ghcr.io/astral-sh/uv:0.6.14` (or current stable). Update it deliberately when uv releases are reviewed.

---

### 4.2 No `HEALTHCHECK` in Containerfile or compose

**File:** `Containerfile`, `compose.yaml`

Podman Compose does not know when the app is actually ready to serve traffic. The `/ping` endpoint already exists and is ideal for a healthcheck.

**Action:** Add to `Containerfile`:
```dockerfile
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')"
```
Or in `compose.yaml`:
```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')"]
  interval: 15s
  timeout: 5s
  retries: 3
  start_period: 10s
```

---

### 4.3 `next.config.ts` `rewrites()` produces a build warning

**File:** `frontend/next.config.ts:12–19`

During `npm run build` (static export), Next.js emits three warnings about rewrites being incompatible with `output: export`. These are visible in the Playwright test output. The rewrites are guarded with `if (process.env.NODE_ENV !== 'development') return []`, which is correct logic, but Next.js still calls and warns on the function during build.

**Action:** The cleanest fix is to return an empty object from `rewrites()` when `output: 'export'` is active. However, this requires detecting the export mode. Alternatively, suppress the warning in CI by noting it as expected. Low priority.

---

## 5. Summary Table

| # | Area | Severity | File | Title |
|---|------|----------|------|-------|
| 1.1 | Security | Critical | `.env.example:4` | Real API key committed |
| 1.2 | Security | High | `.env.example:12` | Corrupted file content |
| 1.3 | Security | High | `backend/app/db.py:17` | Static shared PBKDF2 salt |
| 1.4 | Security | Medium | `backend/app/auth.py:66` | `secure=False` cookie |
| 1.5 | Security | Low | `Containerfile` | Container runs as root |
| 2.1 | Backend | Medium | `pyproject.toml` | Pydantic not an explicit dep |
| 2.2 | Backend | Medium | `ai_routes.py:47,87` | History window inconsistency |
| 2.3 | Backend | Low | `ai_routes.py:100` | Exception cause chain dropped |
| 2.4 | Backend | Low | `ai_client.py` | Duplicate HTTP client logic |
| 2.5 | Backend | Low | `db.py:71` | Two-query seed where one suffices |
| 2.6 | Backend | Low | `db.py:8` | `Optional` vs `X \| None` style |
| 2.7 | Backend | Low | `tests/test_db.py:11` | Manual MonkeyPatch instantiation |
| 2.8 | Backend | Low | `tests/test_auth.py` | No session expiry test |
| 2.9 | Backend | Low | `tests/test_board.py` | No corrupt JSON fallback test |
| 3.1 | Frontend | Medium | `KanbanBoard.tsx:250` | No undefined guard on card lookup |
| 3.2 | Frontend | Medium | `KanbanBoard.tsx:49` | Empty board reverts to demo data |
| 3.3 | Frontend | Low | `KanbanBoard.tsx:61` | Subtle `lastSavedJson` pre-set logic |
| 3.4 | Frontend | Low | `KanbanBoard.tsx:215` | Hardcoded "Five columns" copy |
| 3.5 | Frontend | Low | `boardApi.ts:8` | No runtime board shape validation |
| 3.6 | Frontend | Low | `kanban.spec.ts:48` | Drag test relies on initial state |
| 3.7 | Frontend | Low | `ChatSidebar.tsx:89` | Array index in React key |
| 3.8 | Frontend | Low | `LogoutButton.tsx` | No loading state on logout |
| 4.1 | Infra | Medium | `Containerfile:15` | `uv:latest` non-reproducible |
| 4.2 | Infra | Low | `Containerfile`, `compose.yaml` | No HEALTHCHECK |
| 4.3 | Infra | Info | `next.config.ts:12` | Build warning from rewrites |

---

## 6. Prioritised action list

**Do immediately:**
1. Revoke and rotate the OpenRouter API key (finding 1.1).
2. Fix `.env.example`: replace key with placeholder, remove trailing `run all test` line (1.1, 1.2).

**Before any real users or production deployment:**
3. Per-user random salt for password hashing (1.3).
4. `COOKIE_SECURE` environment variable wired to `set_cookie` (1.4).
5. Non-root user in Containerfile (1.5).
6. Add `pydantic>=2.0` to `pyproject.toml` (2.1).

**Recommended improvements (no urgency):**
7. Align history `max_length` with the `[-12:]` slice (2.2).
8. Fix exception cause chain in `ai_chat` (2.3).
9. Extract `_post_completion` helper in `ai_client.py` (2.4).
10. Replace two-query seed with upsert (2.5).
11. Add undefined guard on `board.cards[cardId]` lookup (3.1).
12. Fix empty-board-revert-to-demo-data behaviour (3.2).
13. Add comment explaining `lastSavedJson` pre-set in `applyBoardFromAssistant` (3.3).
14. Make "columns" count dynamic in the header copy (3.4).
15. Add board-reset `beforeEach` to `kanban.spec.ts` (3.6).
16. Add session expiry test (2.8) and corrupt-JSON board test (2.9).
17. Pin `uv` to a specific version in Containerfile (4.1).
18. Add a HEALTHCHECK (4.2).
