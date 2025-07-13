import secrets
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_client import make_asgi_app
from sqlmodel import select

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.database import create_db_and_tables, get_session
from app.core.encryption import encrypt_token
from app.core.logging import setup_logging
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.models.provider_key import ProviderAPIKeyDB
from app.models.user import User
from app.services.redis_service import redis_service
from app.tasks.model_sync_task import model_sync_task

# Using Kubernetes service for container orchestration
from app.utils.openapi import custom_openapi

settings = get_settings()
logger = setup_logging()


async def _init_dev_user() -> None:
    """Initialize development user and provider keys from environment."""
    try:
        # Get database session
        async for db in get_session():
            user_id = f"user_{settings.github_test_username.replace('-', '_')}"

            # Check if user already exists
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                # Create development user
                user = User(
                    id=user_id,
                    email=f"{settings.github_test_username}@github.dev",
                    full_name="Development User",
                    github_id="dev_github_id_12345",
                    github_username=settings.github_test_username,
                    github_avatar_url=f"https://github.com/{settings.github_test_username}.png",
                    auth_provider="github",
                    is_active=True,
                    is_superuser=True,
                    created_at=datetime.utcnow(),
                    hashed_password="dev_hashed_password",
                    github_access_token_encrypted=encrypt_token("dev_github_token"),
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                logger.info(f"Created development user: {user.email}")
            else:
                logger.info(f"Development user exists: {user.email}")

            # Setup provider keys
            for provider, api_key_attr in [
                ("openai", "openai_api_key"),
                ("anthropic", "anthropic_api_key"),
            ]:
                api_key = getattr(settings, api_key_attr, None)
                if not api_key or api_key.startswith("sk-placeholder"):
                    continue

                # Check if provider key already exists
                result = await db.execute(
                    select(ProviderAPIKeyDB).where(
                        ProviderAPIKeyDB.user_id == user.id,
                        ProviderAPIKeyDB.provider == provider,
                        ProviderAPIKeyDB.is_active,
                    )
                )
                if not result.scalar_one_or_none():
                    # Create provider key
                    provider_key = ProviderAPIKeyDB(
                        id=f"provkey_{secrets.token_urlsafe(12)}",
                        user_id=user.id,
                        provider=provider,
                        encrypted_key=encrypt_token(api_key),
                        key_hint=f"...{api_key[-4:]}",
                        name=f"Dev {provider.upper()} Key",
                        description=f"Auto-configured {provider} key for development",
                        is_active=True,
                        is_valid=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    db.add(provider_key)
                    await db.commit()
                    logger.info(f"Created {provider} provider key")
                else:
                    logger.info(f"{provider} provider key exists")

            break  # Exit the async generator loop

    except Exception as e:
        logger.error(f"Failed to initialize development user: {e}")


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

    # Initialize Redis (required)
    try:
        await redis_service.connect()
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise RuntimeError(
            "Redis connection is required for streaming. Please ensure Redis is available."
        )

    # Initialize development user and provider keys
    if settings.debug and settings.github_test_username:
        await _init_dev_user()
        logger.info("Development user initialized")

    yield

    # Shutdown
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

    if settings.rate_limit_enabled:
        app.add_middleware(RateLimitMiddleware)

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
        redis_healthy = await redis_service.health_check()

        return {
            "status": "healthy" if redis_healthy else "degraded",
            "version": settings.version,
            "orchestration": "kubernetes",
            "redis": "healthy" if redis_healthy else "unhealthy",
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
