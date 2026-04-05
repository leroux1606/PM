import secrets
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

SESSION_TTL_SEC = 7 * 24 * 3600
SESSION_COOKIE = "pm_session"

VALID_USERNAME = "user"
VALID_PASSWORD = "password"

_sessions: dict[str, tuple[str, float]] = {}


def create_session(username: str) -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = (username, time.time() + SESSION_TTL_SEC)
    return token


def get_session_user(token: Optional[str]) -> Optional[str]:
    if not token or token not in _sessions:
        return None
    username, exp = _sessions[token]
    if time.time() > exp:
        del _sessions[token]
        return None
    return username


def delete_session(token: Optional[str]) -> None:
    if token and token in _sessions:
        del _sessions[token]


def reset_sessions() -> None:
    _sessions.clear()


router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginBody(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(body: LoginBody, response: Response) -> dict[str, str | bool]:
    if body.username != VALID_USERNAME or body.password != VALID_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_session(body.username)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_TTL_SEC,
        path="/",
        secure=False,
    )
    return {"ok": True, "username": VALID_USERNAME}


@router.post("/logout")
def logout(request: Request, response: Response) -> dict[str, bool]:
    token = request.cookies.get(SESSION_COOKIE)
    delete_session(token)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@router.get("/me")
def me(request: Request) -> dict[str, str]:
    token = request.cookies.get(SESSION_COOKIE)
    user = get_session_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"username": user}
