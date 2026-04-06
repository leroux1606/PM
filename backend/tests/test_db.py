import sqlite3
from pathlib import Path

import pytest

from app import db as db_module


def test_init_db_creates_tables(tmp_path: Path) -> None:
    path = tmp_path / "test.db"
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("PM_DATABASE_PATH", str(path))
    try:
        db_module.init_db()
        conn = sqlite3.connect(str(path))
        try:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            names = [row[0] for row in cur.fetchall()]
            assert "kanban_boards" in names
            assert "sessions" in names
            assert "users" in names
        finally:
            conn.close()
    finally:
        monkeypatch.delenv("PM_DATABASE_PATH", raising=False)


def test_get_database_path_respects_env(tmp_path: Path) -> None:
    p = tmp_path / "custom.db"
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("PM_DATABASE_PATH", str(p))
    try:
        assert db_module.get_database_path() == p.resolve()
    finally:
        monkeypatch.delenv("PM_DATABASE_PATH", raising=False)
