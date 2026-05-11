import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.routes import auth, detection
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

# ── Aplicación Principal ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SentinelLab starting up")
    yield
    logger.info("SentinelLab shutting down")

# Crear instancia de FastAPI con configuración y rutas
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)
# Registrar rutas
app.include_router(auth.router, prefix="/api/v1")
app.include_router(detection.router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }