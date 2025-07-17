import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Load environment variables from .env if it exists (for local development)
# In CI, these will already be set by GitHub Actions
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Set required environment variables for tests if not already set
if not os.getenv("ENCRYPTION_KEY"):
    os.environ["ENCRYPTION_KEY"] = "test-encryption-key-32-chars-min"


# Global fixture to set REDIS_URL for all agent tests
@pytest.fixture(scope="session", autouse=True)
def redis_url_env():
    """Set Redis URL environment variable for all tests."""
    if not os.getenv("REDIS_URL"):
        os.environ["REDIS_URL"] = "redis://localhost:6379/1"


from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.main import app
from app.models.task import Task
from app.models.user import APIKey, User


# Override settings for testing
@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Test-specific settings."""
    return Settings(
        database_url="sqlite:///test_aideator.db",
        secret_key="test-secret-key-for-testing-only-32chars",
        openai_api_key="sk-test-openai-key",
        anthropic_api_key="sk-ant-test-key",
        gemini_api_key="AIza-test-gemini-key",
        debug=True,
        rate_limit_enabled=False,
    )


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_engine(test_settings: Settings):
    """Create test database engine."""
    engine = create_async_engine(
        test_settings.database_url_async,
        echo=False,
        pool_pre_ping=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session_maker = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession, test_settings: Settings
) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""

    def override_get_settings():
        return test_settings

    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_settings] = override_get_settings
    app.dependency_overrides[get_session] = override_get_session

    # Mock Kubernetes service
    app.state.kubernetes = MockKubernetesService()

    from httpx import ASGITransport

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def mock_kubernetes_service():
    """Mock Kubernetes service for testing."""
    return MockKubernetesService()


# Mock implementations
class MockKubernetesService:
    """Mock Kubernetes service for testing."""

    def __init__(self):
        self._connected = True

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def create_agent_job(self, *args, **kwargs):
        """Mock job creation."""
        return f"agent-{kwargs.get('run_id', 'test')}-{kwargs.get('variation_id', 0)}"

    async def stream_job_logs(self, job_name, run_id, variation_id=None):
        """Mock job log streaming."""
        for i in range(5):
            yield f"[Agent] Mock output line {i}"
            await asyncio.sleep(0.1)


# Factory fixtures
@pytest.fixture
def make_user(db_session: AsyncSession):
    """Factory for creating test users."""

    async def _make_user(**kwargs):
        defaults = {
            "id": f"user_test_{asyncio.get_event_loop().time()}",
            "email": f"test_{asyncio.get_event_loop().time()}@example.com",
            "name": "Test User",
            "is_active": True,
            "is_superuser": False,
        }
        user = User(**{**defaults, **kwargs})
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _make_user


@pytest.fixture
def make_api_key(db_session: AsyncSession):
    """Factory for creating test API keys."""

    async def _make_api_key(user: User, **kwargs):
        # API key authentication removed - using GitHub OAuth only
        # This fixture is kept for backward compatibility but creates dummy data
        from datetime import datetime
        
        dummy_key = {
            "id": f"key_test_{asyncio.get_event_loop().time()}",
            "user_id": user.id,
            "name": "Test API Key",
            "is_active": True,
            "scopes": ["runs:create", "runs:read"],
            "created_at": datetime.utcnow()
        }
        
        return "dummy_api_key", dummy_key

    return _make_api_key


@pytest.fixture
def make_task(db_session: AsyncSession):
    """Factory for creating test tasks."""

    async def _make_task(**kwargs):
        defaults = {
            "id": f"task_test_{int(asyncio.get_event_loop().time())}",
            "github_url": "https://github.com/test/repo",
            "prompt": "Test prompt for the agent",
            "variations": 3,
            "status": "pending",
        }
        task = Task(**{**defaults, **kwargs})
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)
        return task

    return _make_task


# Test data
@pytest.fixture
def sample_task_request():
    """Sample task request data."""
    return {
        "github_url": "https://github.com/fastapi/fastapi",
        "prompt": "Add comprehensive error handling to all API endpoints",
        "variations": 3,
        "agent_config": {
            "model": "claude-3-opus-20240229",
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    }


@pytest.fixture
def auth_headers():
    """Factory for creating auth headers."""

    def _auth_headers(token: str):
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers


@pytest.fixture
def api_key_headers():
    """Factory for creating API key headers."""

    def _api_key_headers(api_key: str):
        return {"X-API-Key": api_key}

    return _api_key_headers


# Import SQLite fixtures for testing
# This imports all the fixtures from conftest_sqlite.py
pytest_plugins = ["tests.conftest_sqlite"]
