"""SQLite test configuration for local development and CI."""

import asyncio
import os
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.main import app


@pytest.fixture(scope="session")
def sqlite_test_settings() -> Settings:
    """Test settings for SQLite."""
    # Create a temporary SQLite database for testing
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db_file.name
    db_file.close()

    return Settings(
        database_url=f"sqlite:///{db_path}",
        secret_key="test-secret-key-for-testing-only-32chars",
        openai_api_key="sk-test-openai-key",
        anthropic_api_key="sk-ant-test-key",
        gemini_api_key="AIza-test-gemini-key",
        debug=True,
        rate_limit_enabled=False,
        encryption_key="test-encryption-key-32-chars-min",
    )


@pytest_asyncio.fixture
async def sqlite_db_engine(sqlite_test_settings: Settings):
    """Create test database engine for SQLite."""
    engine = create_async_engine(
        sqlite_test_settings.database_url_async,
        echo=False,
        connect_args={"check_same_thread": False},  # Required for SQLite
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    await engine.dispose()

    # Clean up the test database file
    db_path = Path(sqlite_test_settings.database_url.replace("sqlite:///", ""))
    if db_path.exists():
        db_path.unlink()


@pytest_asyncio.fixture
async def sqlite_db_session(sqlite_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session for SQLite."""
    async_session_maker = sessionmaker(
        sqlite_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


# Override the default fixtures to use SQLite
@pytest.fixture(scope="session")
def test_settings(sqlite_test_settings):
    """Override test_settings to use SQLite."""
    return sqlite_test_settings


@pytest_asyncio.fixture
async def db_engine(sqlite_db_engine):
    """Override db_engine to use SQLite."""
    return sqlite_db_engine


@pytest_asyncio.fixture
async def db_session(sqlite_db_session):
    """Override db_session to use SQLite."""
    return sqlite_db_session
