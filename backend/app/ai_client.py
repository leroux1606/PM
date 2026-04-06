"""OpenRouter chat completions (OpenAI-compatible API)."""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-oss-120b"


def _read_config() -> tuple[str, str, str]:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    base = os.environ.get("OPENROUTER_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    model = os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL)
    return key, base, model


async def chat_completion(user_message: str) -> str:
    key, base, model = _read_config()
    if not key:
        raise ValueError("OPENROUTER_API_KEY is not set")

    url = f"{base}/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": user_message}],
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            logger.exception(
                "OpenRouter HTTP error status=%s body=%s",
                response.status_code,
                response.text[:2000],
            )
            raise

    data = response.json()
    try:
        text = data["choices"][0]["message"]["content"]
        return str(text).strip()
    except (KeyError, IndexError, TypeError):
        logger.error("Unexpected OpenRouter JSON shape: %s", data)
        raise ValueError("Invalid response from OpenRouter") from None


async def chat_json_completion(messages: list[dict[str, Any]]) -> str:
    """Chat completion with JSON object output (OpenAI-compatible ``response_format``)."""
    key, base, model = _read_config()
    if not key:
        raise ValueError("OPENROUTER_API_KEY is not set")

    url = f"{base}/chat/completions"
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            logger.exception(
                "OpenRouter HTTP error status=%s body=%s",
                response.status_code,
                response.text[:2000],
            )
            raise

    data = response.json()
    try:
        text = data["choices"][0]["message"]["content"]
        return str(text).strip()
    except (KeyError, IndexError, TypeError):
        logger.error("Unexpected OpenRouter JSON shape: %s", data)
        raise ValueError("Invalid response from OpenRouter") from None
