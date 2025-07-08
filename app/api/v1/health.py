from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session

settings = get_settings()
router = APIRouter()


@router.get("/health", summary="Health check")
async def health_check() -> Dict[str, Any]:
    """Check application health status."""
    return {
        "status": "healthy",
        "version": settings.version,
        "environment": "production" if not settings.debug else "development",
    }


@router.get("/health/detailed", summary="Detailed health check")
async def detailed_health_check(
    db: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Detailed health check including dependencies."""
    health_status = {
        "status": "healthy",
        "version": settings.version,
        "checks": {
            "database": False,
            "kubernetes": False,
        },
    }

    # Check database
    try:
        await db.execute("SELECT 1")
        health_status["checks"]["database"] = True
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = str(e)

    # Kubernetes service check would go here
    health_status["checks"]["kubernetes"] = "Not implemented"

    return health_status