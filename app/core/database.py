from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session as SyncSession
from sqlmodel import SQLModel

from app.core.config import get_settings
from app.core.logging import get_logger

# Import models to ensure they're registered with SQLModel
from app.models.model_definition import ModelDefinitionDB, ModelSyncLog  # noqa: F401
from app.models.provider import (  # noqa: F401
    ModelDefinition,
    ModelVariant,
    ProviderCredential,
)
from app.models.provider_key import (  # noqa: F401
    ProviderAPIKeyAuditLog,
    ProviderAPIKeyDB,
)
from app.models.run import AgentOutput, Run  # noqa: F401
from app.models.session import Preference, Session, Turn  # noqa: F401
from app.models.user import APIKey, User  # noqa: F401

settings = get_settings()
logger = get_logger(__name__)

# Create async engine with database-specific parameters
engine_kwargs: dict[str, Any] = {
    "echo": settings.database_echo,
    "pool_pre_ping": True,
}

# Add PostgreSQL-specific parameters only for PostgreSQL
if "postgresql" in settings.database_url_async:
    engine_kwargs.update(
        {
            "pool_size": settings.database_pool_size,
            "pool_recycle": settings.database_pool_recycle,
            "pool_timeout": 30,
            "max_overflow": 10,
        }
    )

engine = create_async_engine(settings.database_url_async, **engine_kwargs)

# Create async session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# Create sync engine for background tasks with database-specific parameters
sync_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
sync_engine_kwargs: dict[str, Any] = {
    "echo": settings.database_echo,
    "pool_pre_ping": True,
}

# Add PostgreSQL-specific parameters only for PostgreSQL
if "postgresql" in sync_url:
    sync_engine_kwargs.update(
        {
            "pool_size": settings.database_pool_size,
            "pool_recycle": settings.database_pool_recycle,
        }
    )

sync_engine = create_engine(sync_url, **sync_engine_kwargs)

# Create sync session factory
sync_session_maker = sessionmaker(
    bind=sync_engine,
    class_=SyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def create_db_and_tables() -> None:
    """Create database tables."""
    try:
        async with engine.begin() as conn:
            # Try to create tables and indexes
            await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("Database tables created successfully")
            
            # Verify our key tables were created
            result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('model_sync_logs', 'model_definitions')"))
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"Verified tables created: {tables}")
            
    except Exception as e:
        error_msg = str(e).lower()
        # Handle specific duplicate index/table errors
        if (
            "ix_model_definitions_model_name" in error_msg
            and "already exists" in error_msg
        ):
            logger.info(
                "Database index already exists, continuing with existing schema"
            )
        elif "already exists" in error_msg or "duplicate" in error_msg:
            logger.info("Database objects already exist, skipping creation")
        else:
            logger.error(f"Failed to create database tables: {e}")
            raise


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session (alias for get_session)."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session() -> Any:
    """Get synchronous database session for background tasks."""
    with sync_session_maker() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
