"""SQLite schema and create-if-not-exists. Board JSON shape matches frontend BoardData."""

import hashlib
import os
import secrets
import sqlite3
from pathlib import Path
from typing import Generator, Optional

# Bump when the JSON structure stored in kanban_boards.board_json changes incompatibly.
BOARD_JSON_SCHEMA_VERSION = 1

DEMO_USERNAME = "user"
DEMO_PASSWORD = "password"

PBKDF2_ITERATIONS = 120_000
_SALT = b"pm-mvp-v1"

DEFAULT_RELATIVE = Path(__file__).resolve().parent.parent / "data" / "pm.db"

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

CREATE TABLE IF NOT EXISTS kanban_boards (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    board_json TEXT NOT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1
);
"""


def hash_password(password: str) -> str:
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), _SALT, PBKDF2_ITERATIONS
    )
    return dk.hex()


def verify_password(password: str, stored_hex: str) -> bool:
    try:
        expected = bytes.fromhex(stored_hex)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), _SALT, PBKDF2_ITERATIONS
    )
    return secrets.compare_digest(candidate, expected)


def get_database_path() -> Path:
    override = os.environ.get("PM_DATABASE_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return DEFAULT_RELATIVE.resolve()


def _seed_demo_user(conn: sqlite3.Connection) -> None:
    h = hash_password(DEMO_PASSWORD)
    conn.execute(
        """
        INSERT INTO users (username, password_hash)
        SELECT ?, ?
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = ?)
        """,
        (DEMO_USERNAME, h, DEMO_USERNAME),
    )
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (h, DEMO_USERNAME),
    )


def init_db() -> None:
    path = get_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(SCHEMA_SQL)
        _seed_demo_user(conn)
        conn.commit()
    finally:
        conn.close()


def get_db() -> Generator[sqlite3.Connection, None, None]:
    path = get_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Async route handlers may touch the connection on a different thread than the dependency.
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def verify_user_credentials(conn: sqlite3.Connection, username: str, password: str) -> bool:
    row = conn.execute(
        "SELECT password_hash FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if row is None:
        return False
    return verify_password(password, row["password_hash"])


def get_user_id(conn: sqlite3.Connection, username: str) -> Optional[int]:
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    return int(row["id"]) if row else None


def get_board_json(conn: sqlite3.Connection, user_id: int) -> Optional[str]:
    row = conn.execute(
        "SELECT board_json FROM kanban_boards WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    return str(row["board_json"]) if row else None


def save_board_json(conn: sqlite3.Connection, user_id: int, board_json: str) -> None:
    conn.execute(
        """
        INSERT INTO kanban_boards (user_id, board_json, schema_version)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            board_json = excluded.board_json,
            schema_version = excluded.schema_version
        """,
        (user_id, board_json, BOARD_JSON_SCHEMA_VERSION),
    )
