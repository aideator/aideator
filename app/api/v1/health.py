from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.core.deps import get_orchestrator
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


@router.get("/redis/test", summary="Test Redis connectivity and pub/sub")
async def test_redis() -> dict[str, Any]:
    """Test Redis connection and pub/sub functionality."""
    import asyncio

    from app.services.redis_service import redis_service

    result = {
        "connected": False,
        "redis_url": settings.redis_url,
        "health_check": False,
        "publish_test": False,
        "subscribe_test": False,
        "error": None,
    }

    try:
        # Test 1: Health check
        result["health_check"] = await redis_service.health_check()
        result["connected"] = result["health_check"]

        # Test 2: Publish test
        test_run_id = "test-run-123"
        test_content = "This is a test message"
        subscribers = await redis_service.publish_agent_output(
            test_run_id, "0", test_content
        )
        result["publish_test"] = True
        result["publish_subscribers"] = subscribers

        # Test 3: Subscribe test (with timeout)
        messages_received = []

        async def subscribe_test():
            async for message in redis_service.subscribe_to_run(test_run_id):
                messages_received.append(message)
                if len(messages_received) >= 1:
                    break

        # Publish after subscribing
        async def publish_after_delay():
            await asyncio.sleep(0.5)
            await redis_service.publish_agent_output(
                test_run_id, "1", "Test message for subscriber"
            )

        # Run subscribe and publish concurrently with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(subscribe_test(), publish_after_delay()), timeout=2.0
            )
            result["subscribe_test"] = len(messages_received) > 0
            result["messages_received"] = len(messages_received)
        except TimeoutError:
            result["subscribe_test"] = False
            result["messages_received"] = 0

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Redis test failed: {e}", exc_info=True)

    return result
