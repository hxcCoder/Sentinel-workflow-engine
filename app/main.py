import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.routes import (
    auth,
    detection,
    alerts,
)

from app.core.config import settings
from app.core.logging import setup_logging
from app.scheduler.scheduler import (
    get_scheduler_status,
    shutdown_scheduler,
    start_scheduler,
)

setup_logging()

logger = logging.getLogger(__name__)


# ── Lifespan ───────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SentinelLab starting up")
    start_scheduler()

    yield

    shutdown_scheduler()
    logger.info("SentinelLab shutting down")


# ── FastAPI App ───────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)


# ── API Routes ────────────────────────────────────────

app.include_router(
    auth.router,
    prefix="/api/v1",
)

app.include_router(
    detection.router,
    prefix="/api/v1",
)

app.include_router(
    alerts.router,
    prefix="/api/v1",
)


# ── Health Check ──────────────────────────────────────

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "scheduler": get_scheduler_status(),
    }
