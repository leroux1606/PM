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


# Demo board seeded for a brand-new user. Mirrors initialData in frontend/src/lib/kanban.ts.
def _seed_board() -> BoardData:
    return BoardData(
        columns=[
            Column(id="col-backlog", title="Backlog", cardIds=["card-1", "card-2"]),
            Column(id="col-discovery", title="Discovery", cardIds=["card-3"]),
            Column(id="col-progress", title="In Progress", cardIds=["card-4", "card-5"]),
            Column(id="col-review", title="Review", cardIds=["card-6"]),
            Column(id="col-done", title="Done", cardIds=["card-7", "card-8"]),
        ],
        cards={
            "card-1": Card(id="card-1", title="Align roadmap themes", details="Draft quarterly themes with impact statements and metrics."),
            "card-2": Card(id="card-2", title="Gather customer signals", details="Review support tags, sales notes, and churn feedback."),
            "card-3": Card(id="card-3", title="Prototype analytics view", details="Sketch initial dashboard layout and key drill-downs."),
            "card-4": Card(id="card-4", title="Refine status language", details="Standardize column labels and tone across the board."),
            "card-5": Card(id="card-5", title="Design card layout", details="Add hierarchy and spacing for scanning dense lists."),
            "card-6": Card(id="card-6", title="QA micro-interactions", details="Verify hover, focus, and loading states."),
            "card-7": Card(id="card-7", title="Ship marketing page", details="Final copy approved and asset pack delivered."),
            "card-8": Card(id="card-8", title="Close onboarding sprint", details="Document release notes and share internally."),
        },
    )


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
    raw = get_board_json(conn, user_id)
    if raw is None:
        # First visit: seed default columns and persist so subsequent GETs are consistent.
        board = _seed_board()
        save_board_json(
            conn,
            user_id,
            json.dumps(board.model_dump(mode="json"), separators=(",", ":"), ensure_ascii=False),
        )
        return board
    try:
        return BoardData.model_validate(json.loads(raw))
    except Exception:
        return _empty_board()


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
