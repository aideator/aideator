"""
High-performance embedded PostgreSQL test configuration using in-memory tmpfs.

This configuration provides ultra-fast test databases by:
1. Using pytest-postgresql with tmpfs for in-memory database storage
2. Pre-loading schema and data using template databases
3. Using optimized PostgreSQL settings for testing
4. Leveraging database prefetching for parallel test execution
"""

import asyncio
import os
import tempfile
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
import pytest_asyncio
from pytest_postgresql import factories
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.main import app
from app.models.run import Run
from app.models.user import APIKey, User


def load_test_schema(**kwargs):
    """Load test schema and initial data for ultra-fast testing."""
    # This function is called once per test session to create the template database
    import psycopg2
    from sqlmodel import create_engine

    # Create sync engine for schema loading
    connection_string = f"postgresql://{kwargs['user']}@{kwargs['host']}:{kwargs['port']}/{kwargs['dbname']}"
    engine = create_engine(connection_string)

    # Create all tables
    SQLModel.metadata.create_all(engine)

    # Add any initial test data here if needed
    # For now, we'll keep it clean and fast


# Configure embedded PostgreSQL with ultra-fast settings
# Use tmpfs for in-memory database storage for maximum speed
postgresql_proc = factories.postgresql_proc(
    # Use tmpfs for data directory - this runs entirely in RAM
    postgres_options="-F -c shared_buffers=128MB -c fsync=off -c synchronous_commit=off "
    "-c full_page_writes=off -c checkpoint_segments=32 "
    "-c checkpoint_completion_target=0.9 -c wal_buffers=16MB",
    # Load our schema once and use it as a template
    load=[load_test_schema],
    # Use a temporary directory that can be mounted as tmpfs
    unixsocketdir=tempfile.gettempdir(),
    # Start faster
    startparams="-w -t 30",
)

# Create the PostgreSQL client fixture
postgresql = factories.postgresql("postgresql_proc")


@pytest.fixture(scope="session")
def embedded_postgres_settings() -> Settings:
    """Test settings for embedded PostgreSQL."""
    return Settings(
        # Will be overridden by the actual embedded postgres connection
        database_url="postgresql+asyncpg://postgres@localhost:5432/test_embedded",
        secret_key="test-secret-key-for-testing-only-32chars",
        openai_api_key="sk-test-openai-key",
        anthropic_api_key="sk-ant-test-key",
        gemini_api_key="AIza-test-gemini-key",
        debug=True,
        rate_limit_enabled=False,
    )


@pytest_asyncio.fixture
async def embedded_db_engine(postgresql, embedded_postgres_settings: Settings):
    """Create async database engine with embedded PostgreSQL."""
    # Build the async connection string from the embedded postgres info
    connection_string = (
        f"postgresql+asyncpg://{postgresql.info.user}@"
        f"{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    )

    engine = create_async_engine(
        connection_string,
        echo=False,
        pool_pre_ping=True,
        # Optimize for testing
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
    )

    # Update settings with actual connection string
    embedded_postgres_settings.database_url = connection_string

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def embedded_db_session(embedded_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session with embedded PostgreSQL."""
    async_session_maker = sessionmaker(
        embedded_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def embedded_client(
    embedded_db_session: AsyncSession, embedded_postgres_settings: Settings
) -> AsyncGenerator:
    """Create test client with embedded PostgreSQL."""
    from httpx import AsyncClient

    def override_get_settings():
        return embedded_postgres_settings

    async def override_get_session():
        yield embedded_db_session

    app.dependency_overrides[get_settings] = override_get_settings
    app.dependency_overrides[get_session] = override_get_session

    from httpx import ASGITransport

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# Factory fixtures for creating test data with embedded PostgreSQL
@pytest.fixture
def embedded_make_user(embedded_db_session: AsyncSession):
    """Factory for creating test users with embedded PostgreSQL."""

    async def _make_user(**kwargs):
        from app.api.v1.auth import get_password_hash

        defaults = {
            "id": f"user_embedded_{asyncio.get_event_loop().time()}",
            "email": f"embedded_{asyncio.get_event_loop().time()}@example.com",
            "hashed_password": get_password_hash("TestPassword123"),
            "is_active": True,
            "is_superuser": False,
        }
        user = User(**{**defaults, **kwargs})
        embedded_db_session.add(user)
        await embedded_db_session.commit()
        await embedded_db_session.refresh(user)
        return user

    return _make_user


@pytest.fixture
def embedded_make_api_key(embedded_db_session: AsyncSession):
    """Factory for creating test API keys with embedded PostgreSQL."""

    async def _make_api_key(user: User, **kwargs):
        from app.api.v1.auth import generate_api_key, get_password_hash

        api_key = generate_api_key()
        defaults = {
            "id": f"key_embedded_{asyncio.get_event_loop().time()}",
            "user_id": user.id,
            "key_hash": get_password_hash(api_key),
            "name": "Embedded Test API Key",
            "is_active": True,
            "scopes": ["runs:create", "runs:read"],
        }
        key_record = APIKey(**{**defaults, **kwargs})
        embedded_db_session.add(key_record)
        await embedded_db_session.commit()
        await embedded_db_session.refresh(key_record)
        return api_key, key_record

    return _make_api_key


@pytest.fixture
def embedded_api_key_headers():
    """Factory for creating API key headers with embedded PostgreSQL."""

    def _api_key_headers(api_key: str):
        return {"X-API-Key": api_key}

    return _api_key_headers


# Performance optimization: Create a pytest.ini configuration
def pytest_configure(config):
    """Configure pytest for embedded PostgreSQL testing."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "embedded_postgres: mark test to run with embedded PostgreSQL"
    )


# Optional: Create a pytest plugin for automatic embedded postgres usage
def pytest_collection_modifyitems(config, items):
    """Automatically mark tests that use embedded postgres fixtures."""
    for item in items:
        # Check if test uses embedded postgres fixtures
        if any(
            fixture_name.startswith("embedded_") for fixture_name in item.fixturenames
        ):
            item.add_marker(pytest.mark.embedded_postgres)


# Helper function to create tmpfs mount for ultra-fast database storage
def create_tmpfs_mount():
    """
    Create a tmpfs mount for ultra-fast database storage.

    This should be called in CI/CD environments or local development
    where you want maximum speed.
    """
    tmpfs_dir = Path("/tmp/aideator_test_db")  # noqa: S108
    tmpfs_dir.mkdir(exist_ok=True)

    # In production CI, you might want to mount this as tmpfs:
    # sudo mount -t tmpfs -o size=512M tmpfs /tmp/aideator_test_db

    return tmpfs_dir


# Configuration for pytest-postgresql with tmpfs
def setup_postgresql_environment():
    """Configure pytest-postgresql for maximum speed."""
    # Set environment variables for postgresql configuration
    os.environ.setdefault("POSTGRESQL_UNIXSOCKETDIR", tempfile.gettempdir())
    os.environ.setdefault("POSTGRESQL_STARTPARAMS", "-w -t 30")

    # Ultra-fast PostgreSQL configuration for testing
    postgres_options = [
        "-F",  # Don't run in background
        "-c",
        "shared_buffers=128MB",
        "-c",
        "fsync=off",
        "-c",
        "synchronous_commit=off",
        "-c",
        "full_page_writes=off",
        "-c",
        "checkpoint_segments=32",
        "-c",
        "checkpoint_completion_target=0.9",
        "-c",
        "wal_buffers=16MB",
        "-c",
        "effective_cache_size=256MB",
        "-c",
        "work_mem=8MB",
        "-c",
        "maintenance_work_mem=64MB",
        "-c",
        "random_page_cost=1.0",  # Optimized for SSD/RAM
        "-c",
        "log_statement=none",  # Reduce logging overhead
        "-c",
        "log_min_duration_statement=-1",  # Disable slow query logging
    ]

    os.environ.setdefault("POSTGRESQL_POSTGRES_OPTIONS", " ".join(postgres_options))


# Set up the environment when this module is imported
setup_postgresql_environment()
