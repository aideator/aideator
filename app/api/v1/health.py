from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.core.dependencies import get_orchestrator
from app.core.logging import get_logger
from app.services.agent_orchestrator import AgentOrchestrator

settings = get_settings()
logger = get_logger(__name__)
router = APIRouter()


@router.get("/health", summary="Health check")
async def health_check() -> dict[str, Any]:
    """Check application health status."""
    return {
        "status": "healthy",
        "version": settings.version,
        "environment": "production" if not settings.debug else "development",
    }


@router.get("/health/detailed", summary="Detailed health check")
async def detailed_health_check(
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
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
        await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "OK"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = str(e)

    # Kubernetes service check would go here
    health_status["checks"]["kubernetes"] = "Not implemented"

    return health_status


@router.get("/system/status", summary="System status including concurrency")
async def system_status(
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
) -> dict[str, Any]:
    """Get system status including resource usage and limits."""
    active_runs = orchestrator.get_active_runs()

    # Count total active jobs
    total_jobs = sum(run.get("variations", 0) for run in active_runs.values())

    return {
        "status": "operational",
        "limits": {
            "max_concurrent_runs": settings.max_concurrent_runs,
            "max_concurrent_jobs": settings.max_concurrent_jobs,
            "max_variations_per_run": settings.max_variations,
        },
        "usage": {
            "active_runs": len(active_runs),
            "active_jobs": orchestrator._total_active_jobs,  # From the orchestrator's tracking
            "estimated_jobs": total_jobs,  # Calculated from run metadata
        },
        "capacity": {
            "runs_available": settings.max_concurrent_runs - len(active_runs),
            "jobs_available": settings.max_concurrent_jobs
            - orchestrator._total_active_jobs,
        },
        "active_run_ids": list(active_runs.keys()),
    }


# Redis endpoints removed - using PostgreSQL polling for task monitoring
