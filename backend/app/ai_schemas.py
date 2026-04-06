"""Structured AI responses (Part 9)."""

from pydantic import BaseModel, Field

from app.board import BoardData


class AiKanbanResponse(BaseModel):
    assistant_message: str = Field(..., max_length=64000)
    board: BoardData | None = None
