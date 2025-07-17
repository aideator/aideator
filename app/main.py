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


    # Kubernetes connections are handled via kubectl
    # No persistent connection needed at the server level

    # Redis removed - using PostgreSQL polling for task monitoring

    yield

    logger.info("Shutting down application")


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
        AIdeator is a Kubernetes-native AI orchestration platform that runs multiple AI agents in isolated containers,
        with real-time progress monitoring through HTTP polling.

        ## Features

        * **Container Isolation** - Each agent runs in its own Kubernetes Job
        * **Real-time Monitoring** - HTTP polling for live agent output and progress
        * **Parallel Execution** - Run multiple agent variations concurrently
        * **Task Management** - Create, monitor, and track coding tasks
        * **GitHub Integration** - Analyze any public repository

        ## Architecture

        The system uses a unified task-based architecture with PostgreSQL for data persistence
        and HTTP polling for real-time updates. Tasks are queued and executed in Kubernetes
        containers with outputs written directly to the database.

        ## Authentication

        Authentication is handled via GitHub OAuth in production, with development mode bypass available.
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
        return {
            "status": "healthy",
            "version": settings.version,
            "orchestration": "kubernetes",
            "database": "postgresql",
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
