import time
from fastapi import APIRouter
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()

START_TIME = time.time()


# ------------------------------------------------------------------------------
# Basic Liveness Probe (Is the process alive?)
# ------------------------------------------------------------------------------
@router.get("/health/live", tags=["Health"])
async def liveness_probe():
    return {
        "status": "alive",
        "service": settings.SERVICE_NAME,
        "timestamp": int(time.time()),
    }


# ------------------------------------------------------------------------------
# Readiness Probe (Is the service ready to accept traffic?)
# ------------------------------------------------------------------------------
@router.get("/health/ready", tags=["Health"])
async def readiness_probe():
    # Example: check DB, cache, AI service, etc.
    dependencies = {
        "database": "ok",
        "cache": "ok",
        "ai_service": "ok",
    }

    all_ok = all(v == "ok" for v in dependencies.values())

    return {
        "status": "ready" if all_ok else "degraded",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "environment": settings.ENVIRONMENT,
        "dependencies": dependencies,
        "timestamp": int(time.time()),
    }


# ------------------------------------------------------------------------------
# Full Health (Human-friendly)
# ------------------------------------------------------------------------------
@router.get("/health", tags=["Health"])
async def health_check():
    uptime_seconds = int(time.time() - START_TIME)

    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": uptime_seconds,
        "timestamp": int(time.time()),
    }
