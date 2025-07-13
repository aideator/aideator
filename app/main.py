from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_client import make_asgi_app

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.database import create_db_and_tables
from app.core.logging import setup_logging
from app.middleware.development import DevelopmentAuthMiddleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.services.redis_service import redis_service
from app.tasks.model_sync_task import model_sync_task

# Using Kubernetes service for container orchestration
from app.utils.openapi import custom_openapi

settings = get_settings()
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage app lifecycle - database initialization and background tasks."""
    # Startup
    logger.info(f"Starting {settings.project_name} v{settings.version}")

    # Initialize database
    await create_db_and_tables()
    logger.info("Database initialized")

    # Start model sync task
    await model_sync_task.start()
    logger.info("Model sync task started")

    # Kubernetes connections are handled via kubectl
    # No persistent connection needed at the server level

    # Initialize Redis (conditionally - off by default)
    if settings.enable_redis:
        try:
            await redis_service.connect()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            if settings.require_redis:
                raise RuntimeError("Redis connection is required for streaming.")
            else:
                logger.warning("Redis connection failed - continuing without streaming features")
    else:
        logger.info("Redis disabled by configuration (enable_redis=False)")

    yield

    # Shutdown Redis if it was enabled
    if settings.enable_redis:
        await redis_service.disconnect()
        logger.info("Redis disconnected")

    logger.info("Shutting down application")

    # Stop model sync task
    await model_sync_task.stop()
    logger.info("Model sync task stopped")


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.project_name,
        version=settings.version,
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
        debug=settings.debug,
        servers=[
            {"url": "http://localhost:8000", "description": "Local development"},
            {"url": "https://api.aideator.com", "description": "Production"},
        ],
        description="""
        AIdeator is a Kubernetes-native LLM orchestration platform that runs multiple AI agents in isolated containers,
        streaming their thought processes in real-time.

        ## Features

        * **Container Isolation** - Each agent runs in its own Kubernetes Job
        * **Real-time Streaming** - Server-Sent Events for live agent output
        * **Parallel Execution** - Run N variations concurrently
        * **Result Persistence** - Save and retrieve winning variations
        * **GitHub Integration** - Clone and analyze any public repository

        ## Authentication

        Most endpoints require an API key passed in the `X-API-Key` header.
        """,
        contact={
            "name": "AIdeator Team",
            "email": "support@aideator.com",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    # Set custom OpenAPI schema
    app.openapi = custom_openapi(app)  # type: ignore[method-assign]

    # Add middleware in reverse order (last added = first executed)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    if settings.allowed_hosts != ["*"]:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

    if getattr(settings, 'enable_rate_limiting', True):
        app.add_middleware(RateLimitMiddleware)

    # Add development middleware for simplified auth (must be before LoggingMiddleware)
    if settings.simple_dev_mode or settings.auto_create_test_user:
        app.add_middleware(DevelopmentAuthMiddleware)

    app.add_middleware(LoggingMiddleware)

    # Include API router
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    # Mount metrics endpoint
    if settings.enable_metrics:
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)

    @app.get("/", tags=["Root"])
    async def root() -> dict[str, Any]:
        """Root endpoint with API information."""
        return {
            "name": settings.project_name,
            "version": settings.version,
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": f"{settings.api_v1_prefix}/openapi.json",
            "health": "/health",
            "description": "AIdeator - Kubernetes-native LLM orchestration platform",
        }

    @app.get("/health", tags=["System"])
    async def health_check() -> dict[str, Any]:
        """Health check endpoint."""
        redis_healthy = True  # Default to healthy when disabled
        if settings.enable_redis:
            redis_healthy = await redis_service.health_check()

        return {
            "status": "healthy" if redis_healthy else "degraded",
            "version": settings.version,
            "orchestration": "kubernetes",
            "redis": "healthy" if redis_healthy else "disabled",
        }

    return app


# Create app instance
app = create_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level,
        access_log=True,
    )
