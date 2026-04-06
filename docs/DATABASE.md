# Database (SQLite)

Kanban state is stored **as JSON** per user (see locked decision in `docs/PLAN.md`). Sessions and users use normal relational tables so the MVP can move off the in-memory session store from Part 4 without another redesign.

## File location (create if missing)

| Environment | Typical `PM_DATABASE_PATH` | Notes |
|-------------|----------------------------|--------|
| Local `uv run` from `backend/` | *(unset)* | Defaults to `backend/data/pm.db` next to the package. Parent dirs are created on first run. |
| Podman Compose | `/data/pm.db` | `compose.yaml` mounts volume `pm_data` at `/data`; set `PM_DATABASE_PATH` accordingly (see `.env.example`). |

If the database file does not exist, the app creates the file and tables on startup (`app.db.init_db`).

## Tables

| Table | Purpose |
|-------|---------|
| `users` | One row per account. `password_hash` is PBKDF2-HMAC-SHA256 (hex), see `app/db.py`. The demo user `user` is seeded on startup; the hash is refreshed on each `init_db` for that username (MVP local dev only). |
| `sessions` | Server-side sessions: opaque `id` (cookie value), `user_id`, `expires_at` (Unix timestamp, seconds). Table exists for future use; Part 6 still uses the in-memory session store from Part 4 for cookie validation. |
| `kanban_boards` | One row per user: `board_json` is the full `BoardData` object serialized to JSON; `schema_version` tracks incompatible JSON shape changes (`BOARD_JSON_SCHEMA_VERSION` in `app/db.py`). |

### ER diagram

```mermaid
erDiagram
    users ||--o| kanban_boards : owns
    users ||--o{ sessions : has

    users {
        int id PK
        text username UK
        text password_hash
    }

    sessions {
        text id PK
        int user_id FK
        real expires_at
    }

    kanban_boards {
        int user_id PK_FK
        text board_json
        int schema_version
    }
```

## Board JSON shape (`board_json`)

Matches **`BoardData`** in `frontend/src/lib/kanban.ts`:

- `columns`: array of `{ id, title, cardIds }`
- `cards`: object map of card id to `{ id, title, details }`

Example (minimal valid payload):

```json
{
  "columns": [
    { "id": "col-backlog", "title": "Backlog", "cardIds": ["card-1"] }
  ],
  "cards": {
    "card-1": {
      "id": "card-1",
      "title": "Sample task",
      "details": "Optional description."
    }
  }
}
```

Validation on write (Part 6+) should enforce this shape before persisting.

## Migrations (MVP)

No migration framework yet. If `board_json` shape changes incompatibly, increment `BOARD_JSON_SCHEMA_VERSION` and handle reads in code (default empty board for unknown versions if needed).
