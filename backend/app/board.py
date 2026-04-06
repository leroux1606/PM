"""Kanban board JSON API (matches frontend BoardData)."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, model_validator
from sqlite3 import Connection

from app.auth import SESSION_COOKIE, get_session_user
from app.db import get_board_json, get_db, get_user_id, save_board_json

router = APIRouter(prefix="/api/board", tags=["board"])


class Card(BaseModel):
    id: str
    title: str
    details: str


class Column(BaseModel):
    id: str
    title: str
    cardIds: list[str]


class BoardData(BaseModel):
    columns: list[Column]
    cards: dict[str, Card]

    @model_validator(mode="after")
    def card_ids_match(self) -> "BoardData":
        for col in self.columns:
            for cid in col.cardIds:
                if cid not in self.cards:
                    raise ValueError(f"card id {cid!r} referenced in columns but missing in cards")
        return self


def _empty_board() -> BoardData:
    return BoardData(columns=[], cards={})


def load_board_data(conn: Connection, user_id: int) -> BoardData:
    """Current board for persistence / AI context; empty shape if missing or invalid."""
    raw = get_board_json(conn, user_id)
    if raw is None:
        return _empty_board()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return _empty_board()
    try:
        return BoardData.model_validate(data)
    except Exception:
        return _empty_board()


def require_username(request: Request) -> str:
    token = request.cookies.get(SESSION_COOKIE)
    user = get_session_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.get("")
def get_board(
    conn: Annotated[Connection, Depends(get_db)],
    username: str = Depends(require_username),
) -> BoardData:
    user_id = get_user_id(conn, username)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return load_board_data(conn, user_id)


@router.put("")
def put_board(
    body: BoardData,
    conn: Annotated[Connection, Depends(get_db)],
    username: str = Depends(require_username),
) -> BoardData:
    user_id = get_user_id(conn, username)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = body.model_dump(mode="json")
    save_board_json(
        conn,
        user_id,
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False),
    )
    return body
