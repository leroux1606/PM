from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.auth import router as auth_router

SITE_DIR = Path(__file__).resolve().parent.parent / "site"

app = FastAPI(title="PM MVP")

app.include_router(auth_router)


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
