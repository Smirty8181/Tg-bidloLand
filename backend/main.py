from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api.internal import router as internal_router
from backend.api.routes import router as api_router
from backend.database.base import Base
from backend.database.session import engine
from backend.models import User, UserRole, Admin  # noqa: F401
from config.settings import settings
from utils.logging import setup_logging

logger = logging.getLogger(__name__)
MINIAPP_DIST = Path("miniapp/dist")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    Path("data").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Backend started for %s", settings.server_name)
    yield
    await engine.dispose()


app = FastAPI(title="БыдлоЛенд API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if detail == "minecraft_unavailable":
        detail = "🔴 Не удалось связаться с Minecraft-сервером.\n\nПопробуйте повторить действие через несколько секунд."
    return JSONResponse(status_code=exc.status_code, content={"detail": detail, "ok": False})


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={"ok": False, "detail": "Сервис временно недоступен. Попробуйте позже."},
    )


app.include_router(api_router, prefix="/api")
app.include_router(internal_router)


@app.get("/api/config/public")
async def public_config() -> dict:
    base = (settings.hosting_panel_url or "").rstrip("/")
    panel_url = f"{base}/server/{settings.hosting_server_id}" if base and settings.hosting_server_id else None
    return {
        "server_name": settings.server_name,
        "server_version": settings.server_version,
        "map_url": settings.map_url,
        "webapp_url": settings.webapp_url,
        "panel_url": panel_url,
    }


if MINIAPP_DIST.exists():
    app.mount("/assets", StaticFiles(directory=MINIAPP_DIST / "assets"), name="assets")

    @app.get("/BydloBridge-1.0.0.jar")
    async def plugin_jar():
        jar = MINIAPP_DIST / "BydloBridge-1.0.0.jar"
        if jar.exists():
            return FileResponse(jar, media_type="application/java-archive", filename="BydloBridge-1.0.0.jar")
        raise HTTPException(404, "plugin jar not built")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        candidate = MINIAPP_DIST / full_path
        if full_path and candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
        index = MINIAPP_DIST / "index.html"
        if index.exists():
            return FileResponse(index)
        return JSONResponse({"status": "miniapp not built"}, status_code=404)
