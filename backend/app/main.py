from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# uvicorn does not load `.env` by default; load before importing `app.*` packages.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_REPO_ROOT / ".env")
load_dotenv(_BACKEND_ROOT / ".env")

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.ai_routes import router as ai_router
from app.auth import router as auth_router
from app.board import router as board_router
from app.db import init_db

SITE_DIR = Path(__file__).resolve().parent.parent / "site"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="PM MVP", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(board_router)
app.include_router(ai_router)


@app.get("/ping")
def ping() -> dict[str, str]:
    """Always try this first: if this 404s, traffic is not reaching this app."""
    return {"service": "pm-mvp-backend", "ok": "true"}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/hello")
def hello() -> dict[str, str]:
    return {"message": "Hello from the API"}


@app.get("/login")
def login_page() -> FileResponse:
    """Next `output: export` emits `login.html` at the site root; StaticFiles does not map `/login` to it."""
    path = SITE_DIR / "login.html"
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="login.html missing; run npm run build:site from frontend/",
        )
    return FileResponse(path)


def _site_ready() -> bool:
    return SITE_DIR.is_dir() and (SITE_DIR / "index.html").is_file()


if _site_ready():
    app.mount(
        "/",
        StaticFiles(directory=str(SITE_DIR), html=True),
        name="site",
    )
else:

    @app.get("/")
    def site_missing() -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Frontend not built into backend/site. "
                "From frontend/: npm run build && node scripts/copy-site.mjs"
            },
        )
