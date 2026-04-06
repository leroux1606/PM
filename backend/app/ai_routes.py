"""Authenticated AI smoke / chat endpoints."""

import json
import logging
from typing import Annotated, Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ValidationError
from sqlite3 import Connection

import app.ai_client as ai_client
from app.ai_schemas import AiKanbanResponse
from app.board import load_board_data, require_username
from app.db import get_db, get_user_id, save_board_json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])

CHAT_SYSTEM_PREFIX = """You are a helpful assistant for a single-user Kanban board. Reply ONLY with a JSON object (no markdown code fences) matching this shape:
{"assistant_message": "<string>", "board": null OR <full board object>}

The board has "columns": [{"id","title","cardIds":[]}, ...] and "cards": {"<id>": {"id","title","details"}, ...}.
Every card id in cardIds must exist in "cards". Use "board": null if you are not changing the board; otherwise return the complete replacement board.

Current board (JSON):
"""


class SmokeBody(BaseModel):
    message: str = Field(
        default="What is 2+2? Reply with a single number only.",
        min_length=1,
        max_length=8000,
    )


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=16000)


class ChatBody(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=24)


@router.post("/smoke")
async def ai_smoke(
    body: SmokeBody,
    _username: str = Depends(require_username),
) -> dict[str, str]:
    try:
        reply = await ai_client.chat_completion(body.message)
    except ValueError as e:
        if "OPENROUTER_API_KEY" in str(e):
            raise HTTPException(
                status_code=503,
                detail="AI is not configured (set OPENROUTER_API_KEY).",
            ) from e
        raise HTTPException(status_code=502, detail=str(e)) from e
    except httpx.HTTPError as e:
        logger.exception("OpenRouter request failed")
        raise HTTPException(
            status_code=502,
            detail="OpenRouter request failed.",
        ) from e
    return {"reply": reply}


@router.post("/chat")
async def ai_chat(
    body: ChatBody,
    conn: Annotated[Connection, Depends(get_db)],
    username: str = Depends(require_username),
) -> dict[str, object]:
    user_id = get_user_id(conn, username)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    current = load_board_data(conn, user_id)
    board_json = json.dumps(current.model_dump(mode="json"), ensure_ascii=False)
    system_content = CHAT_SYSTEM_PREFIX + board_json

    messages: list[dict[str, str]] = [{"role": "system", "content": system_content}]
    for turn in body.history[-12:]:
        messages.append({"role": turn.role, "content": turn.content})
    messages.append({"role": "user", "content": body.message})

    try:
        raw = await ai_client.chat_json_completion(messages)
    except ValueError as e:
        if "OPENROUTER_API_KEY" in str(e):
            raise HTTPException(
                status_code=503,
                detail="AI is not configured (set OPENROUTER_API_KEY).",
            ) from e
        raise HTTPException(status_code=502, detail=str(e)) from e
    except httpx.HTTPError:
        logger.exception("OpenRouter request failed")
        raise HTTPException(
            status_code=502,
            detail="OpenRouter request failed.",
        )

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("AI non-JSON content: %s", raw[:500])
        raise HTTPException(
            status_code=502,
            detail="AI did not return valid JSON.",
        )

    try:
        parsed = AiKanbanResponse.model_validate(data)
    except ValidationError:
        logger.warning("AI validation failed; raw=%s", raw[:1000])
        raise HTTPException(
            status_code=502,
            detail="AI response failed validation.",
        )

    if parsed.board is not None:
        payload = parsed.board.model_dump(mode="json")
        save_board_json(
            conn,
            user_id,
            json.dumps(payload, separators=(",", ":"), ensure_ascii=False),
        )

    return {
        "assistant_message": parsed.assistant_message,
        "board_updated": parsed.board is not None,
        "board": parsed.board.model_dump(mode="json") if parsed.board else None,
    }
