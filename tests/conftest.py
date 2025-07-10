import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.main import app
from app.models.run import Run
from app.models.user import APIKey, User
from app.services.kubernetes_service import KubernetesService
from app.services.sse_manager import SSEManager


# Override settings for testing
@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Test-specific settings."""
    return Settings(
        database_url="postgresql+asyncpg://test:test@localhost:5432/test_aideator",
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
async def client(db_session: AsyncSession, test_settings: Settings) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""
    
    def override_get_settings():
        return test_settings
    
    async def override_get_session():
        yield db_session
    
    app.dependency_overrides[get_settings] = override_get_settings
    app.dependency_overrides[get_session] = override_get_session
    
    # Mock Kubernetes service
    app.state.kubernetes = MockKubernetesService()
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_kubernetes_service():
    """Mock Kubernetes service for testing."""
    return MockKubernetesService()


@pytest.fixture
def sse_manager():
    """SSE manager instance for testing."""
    return SSEManager()


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
        from app.api.v1.auth import get_password_hash
        
        defaults = {
            "id": f"user_test_{asyncio.get_event_loop().time()}",
            "email": f"test_{asyncio.get_event_loop().time()}@example.com",
            "hashed_password": get_password_hash("TestPassword123"),
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
        from app.api.v1.auth import generate_api_key, get_password_hash
        
        api_key = generate_api_key()
        defaults = {
            "id": f"key_test_{asyncio.get_event_loop().time()}",
            "user_id": user.id,
            "key_hash": get_password_hash(api_key),
            "name": "Test API Key",
            "is_active": True,
            "scopes": ["runs:create", "runs:read"],
        }
        key_record = APIKey(**{**defaults, **kwargs})
        db_session.add(key_record)
        await db_session.commit()
        await db_session.refresh(key_record)
        return api_key, key_record
    
    return _make_api_key


@pytest.fixture
def make_run(db_session: AsyncSession):
    """Factory for creating test runs."""
    async def _make_run(**kwargs):
        defaults = {
            "id": f"run_test_{asyncio.get_event_loop().time()}",
            "github_url": "https://github.com/test/repo",
            "prompt": "Test prompt for the agent",
            "variations": 3,
            "status": "pending",
        }
        run = Run(**{**defaults, **kwargs})
        db_session.add(run)
        await db_session.commit()
        await db_session.refresh(run)
        return run
    
    return _make_run


# Test data
@pytest.fixture
def sample_run_request():
    """Sample run request data."""
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