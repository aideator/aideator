from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session as SyncSession

from app.core.config import get_settings
from app.core.logging import get_logger

# Import models to ensure they're registered with SQLModel
from app.models import User, APIKey, Run, Session, Turn, Preference
from app.models.model_definition import ModelDefinitionDB, ModelSyncLog

settings = get_settings()
logger = get_logger(__name__)

# Create async engine
engine = create_async_engine(
    settings.database_url_async,
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    pool_recycle=settings.database_pool_recycle,
    pool_pre_ping=True,
    # PostgreSQL-specific optimizations
    pool_timeout=30,
    max_overflow=10,
)

# Create async session factory
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Alias for backward compatibility with migration scripts
AsyncSessionFactory = async_session_maker

# Create sync engine for background tasks
sync_engine = create_engine(
    settings.database_url.replace("postgresql+asyncpg://", "postgresql://"),
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    pool_recycle=settings.database_pool_recycle,
    pool_pre_ping=True,
)

# Create sync session factory
sync_session_maker = sessionmaker(
    sync_engine,
    class_=SyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def create_db_and_tables() -> None:
    """Create database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database tables created")


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


def get_sync_session():
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