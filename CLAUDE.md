# AIdeator - Instructions for Claude

## Project Overview

AIdeator is a Dagger-powered LLM orchestration platform that runs multiple AI agents in isolated containers, streaming their thought processes in real-time. By containerizing each agent variation, we ensure reproducibility, isolation, and scalability. As the primary coding assistant, I help build a sophisticated FastAPI + Dagger backend that orchestrates containerized Claude agents, captures their reasoning, and delivers insights through Server-Sent Events.

## 🎯 My Role & Capabilities

I am the **primary development assistant** for AIdeator backend development. I provide:

- **Production-Ready Code**: No mock data, proper async patterns, comprehensive error handling
- **FastAPI Expertise**: Async route handlers, SSE streaming, proper dependency injection
- **Dagger Integration**: Container orchestration, pipeline design, parallel execution
- **Real-time Streaming**: Server-Sent Events implementation for concurrent agent output
- **Security First**: Container isolation, secret management, SQL injection prevention

## 🏗️ Architecture Understanding

### Core Components

- **FastAPI Backend** - Async web framework running on the host machine
- **Dagger Module** - Container orchestration via CLI subprocess calls
- **Server-Sent Events (SSE)** - Real-time streaming of agent thought processes
- **SQLite + SQLModel** - Async database with Pydantic integration
- **Anthropic Claude API** - LLM agent for code generation tasks
- **Container Isolation** - Each agent runs in its own Dagger container

### Refactored Architecture

The architecture has been refactored to separate concerns:
- **Host Machine**: FastAPI server, database, SSE streaming
- **Dagger Containers**: Agent execution only (via module functions)
- **No Persistent Connection**: Server doesn't maintain Dagger connection

### Key Workflows

1. **Job Submission** → Create Dagger pipeline → Build containers → Execute agents
2. **Container Orchestration** → Parallel container execution → Resource isolation
3. **Real-time Streaming** → Capture container stdout → Stream via SSE
4. **Result Persistence** → Store winning variation → Cache for reuse

### Refactored Pipeline Architecture

```python
# Server runs on host, calls Dagger module via CLI
class DaggerModuleService:
    async def stream_agent_output(self, repo_url: str, prompt: str, variation_id: int):
        cmd = [
            "dagger", "call",
            "-m", ".",  # Module at project root
            "stream-agent",
            "--repo-url", repo_url,
            "--prompt", prompt,
            "--variation-id", str(variation_id),
            "--anthropic-api-key", f"env:{settings.anthropic_api_key_env_var}",
            "stdout"
        ]
        
        # Stream output line by line
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
        for line in process.stdout:
            yield line.strip()

# Dagger module defines container operations
@function
async def run_agent(
    self,
    repo_url: str,
    prompt: str,
    anthropic_api_key: dagger.Secret,
    variation_id: int = 0,
) -> str:
    # Container operations happen in Dagger module
    container = dag.container().from_("python:3.11-slim")
    # ... setup and execution
```

## 🚀 Development Commands

### Environment Setup with uv (Modern Python Package Manager)

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Dagger CLI
curl -L https://dl.dagger.io/dagger/install.sh | sh

# Create new project with uv
uv init

# Install dependencies
uv pip install -r requirements.txt

# Or install specific packages
uv pip install fastapi uvicorn[standard] sqlmodel aiosqlite httpx dagger-io

# Dagger engine starts automatically when needed
# No persistent connection required

# Run development server
uv run uvicorn app.main:app --reload --port 8000
```

### Testing & Quality with Modern Tools

```bash
# Run all tests with pytest
uv run pytest

# Run tests with coverage
uv run pytest --cov=app --cov-report=html --cov-report=term-missing

# Run async tests
uv run pytest -v --asyncio-mode=auto

# Run specific test file
uv run pytest tests/test_api.py -v

# Run tests matching pattern
uv run pytest -k "test_create" -v

# E2E tests with markers
uv run pytest -m "e2e" -v

# Linting with ruff (replaces flake8, black, isort, and more)
uv run ruff check .              # Check for issues
uv run ruff check --fix .        # Auto-fix issues
uv run ruff format .             # Format code (replaces black)

# Type checking with mypy
uv run mypy app/                 # Type check app directory
uv run mypy app/ --strict        # Strict mode
uv run mypy app/ --show-error-codes  # Show error codes for ignores
```

## 📋 Quality Standards

### Code Requirements

- **No Mock Data**: All endpoints return real functionality
- **Async Patterns**: Use `async def` for all route handlers
- **Proper Error Handling**: HTTPException for API errors, try/except blocks
- **Type Hints**: Full type annotations with mypy strict mode compliance
- **Runtime Validation**: Pydantic models for all inputs/outputs
- **Security**: Parameterized queries, input validation, secure defaults
- **Code Style**: Enforced by ruff with line length 88, Python 3.11+ features

### Modern Python Standards

- **Type Annotations**: All functions must have type hints (enforced by mypy)
- **Pydantic Everywhere**: Use Pydantic for all data validation
- **Docstrings**: Google-style docstrings for all public functions
- **Import Order**: Automatically handled by ruff (stdlib → third-party → local)
- **Async/Await**: Consistent async patterns, no blocking I/O in async functions
- **Error Messages**: Descriptive errors with proper exception hierarchy

### Pydantic Validation Patterns

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime

# Use descriptive Field definitions
class CreateRunRequest(BaseModel):
    github_url: HttpUrl = Field(
        ...,
        description="Public GitHub repository URL",
        examples=["https://github.com/fastapi/fastapi"]
    )
    prompt: constr(min_length=10, max_length=2000) = Field(
        ...,
        description="Prompt for the LLM agents"
    )
    
    # Custom validators for complex logic
    @field_validator('github_url')
    @classmethod
    def validate_github_url(cls, v: HttpUrl) -> HttpUrl:
        if not str(v).startswith('https://github.com/'):
            raise ValueError('Must be a GitHub URL')
        return v
    
    # Model-level validation
    @model_validator(mode='after')
    def validate_request(self) -> 'CreateRunRequest':
        # Complex validation across fields
        return self

# Use Pydantic Settings for config
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # All config validated at startup
    anthropic_api_key: str
    max_variations: int = Field(default=5, ge=1, le=10)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )
```

### API Design Principles

- **RESTful Conventions**: Proper HTTP methods and status codes
- **Response Models**: Pydantic models for request/response validation
- **Error Responses**: Consistent error format with helpful messages
- **Documentation**: OpenAPI/Swagger auto-generated from Pydantic models
- **Versioning**: API versioning through URL path (/api/v1/)
- **Validation Errors**: Automatic 422 responses with field-level details

## 🔧 Implementation Patterns

### Dagger Module Service (Refactored)

```python
# app/services/dagger_module_service.py
class DaggerModuleService:
    """Service to interact with Dagger modules via CLI - no persistent connection"""
    
    def __init__(self):
        self.module_name = "aideator"
        self.module_path = "."  # Module at project root
        
    async def stream_agent_output(
        self,
        repo_url: str,
        prompt: str,
        variation_id: int = 0,
        agent_config: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream agent output via Dagger module call"""
        cmd = [
            "dagger", "call",
            "-m", self.module_path,
            "stream-agent",
            "--repo-url", repo_url,
            "--prompt", prompt,
            "--variation-id", str(variation_id),
            "--anthropic-api-key", f"env:{settings.anthropic_api_key_env_var}",
            "stdout"
        ]
        
        if agent_config:
            cmd.extend(["--agent-config", json.dumps(agent_config)])
        
        # Stream output line by line
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )
        
        for line in process.stdout:
            if line.strip():
                yield line.strip()
    
    def is_available(self) -> bool:
        """Check if Dagger CLI is available"""
        try:
            subprocess.run(["dagger", "version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

# No Dagger in FastAPI lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - only database initialization
    await create_db_and_tables()
    logger.info("Database initialized")
    
    # Dagger connections handled on-demand via module calls
    yield
    
    # Shutdown
    logger.info("Shutting down application")
```

### Agent Execution Pipeline

```python
# app/services/agent_orchestrator.py
import asyncio
from typing import AsyncIterator
import json

class AgentOrchestrator:
    def __init__(self, dagger_service: DaggerService, sse_manager: SSEManager):
        self.dagger = dagger_service
        self.sse = sse_manager
    
    async def execute_variations(
        self, 
        run_id: str,
        repo_url: str, 
        prompt: str, 
        variations: int
    ):
        """Execute N agent variations in parallel containers"""
        tasks = []
        
        for i in range(variations):
            container = await self.dagger.create_agent_container(
                repo_url, prompt, i
            )
            task = asyncio.create_task(
                self.stream_container_output(container, run_id, i)
            )
            tasks.append(task)
        
        # Execute all containers in parallel
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stream_container_output(
        self, 
        container: dagger.Container, 
        run_id: str, 
        variation_id: int
    ):
        """Stream container stdout to SSE"""
        # Execute the agent script with validated config
        exec_result = container.with_exec([
            "python", "-u", "/app/agent.py", 
            "--variation", str(variation_id)
        ])
        
        # Stream stdout line by line
        async for line in exec_result.stdout().lines():
            if line.strip():
                await self.sse.send_event(run_id, {
                    "variation_id": variation_id,
                    "type": "agent_output",
                    "content": line.strip()
                })
```

### FastAPI Implementation with OpenAPI

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.api.v1 import runs, streams, health
from app.services.dagger_service import DaggerService

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle including Dagger engine."""
    # Startup
    app.state.dagger = DaggerService()
    await app.state.dagger.connect()
    
    yield
    
    # Shutdown
    await app.state.dagger.disconnect()

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["System"])
app.include_router(
    runs.router,
    prefix=settings.api_v1_prefix,
    tags=["Runs"]
)
app.include_router(
    streams.router,
    prefix=settings.api_v1_prefix,
    tags=["Streaming"]
)

# Route implementation matching OpenAPI spec
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.schemas.runs import CreateRunRequest, CreateRunResponse
from app.services.agent_orchestrator import AgentOrchestrator

router = APIRouter(prefix="/runs")

@router.post(
    "",
    response_model=CreateRunResponse,
    status_code=202,
    summary="Create a new agent run",
    response_description="Run accepted for processing"
)
async def create_run(
    request: CreateRunRequest,
    background_tasks: BackgroundTasks,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    db: AsyncSession = Depends(get_db),
) -> CreateRunResponse:
    """
    Create a new agent run that will spawn N containerized LLM agents.
    
    The run is processed asynchronously in the background using Dagger containers.
    Connect to the returned stream_url to receive real-time agent outputs.
    """
    # Validate GitHub URL
    if not request.github_url.startswith("https://github.com/"):
        raise HTTPException(
            status_code=400,
            detail="Only public GitHub repositories are supported"
        )
    
    # Create run in database
    run = await create_run_record(db, request)
    
    # Schedule background orchestration
    background_tasks.add_task(
        orchestrator.execute_variations,
        run_id=run.id,
        repo_url=request.github_url,
        prompt=request.prompt,
        variations=request.variations,
        agent_config=request.agent_config
    )
    
    return CreateRunResponse(
        run_id=run.id,
        stream_url=f"{settings.api_v1_prefix}/runs/{run.id}/stream",
        status="accepted",
        estimated_duration_seconds=request.variations * 40  # Rough estimate
    )
```

### Pydantic Validation Flow Example

```python
# app/api/v1/runs.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import ValidationError

from app.schemas import (
    CreateRunRequest, 
    CreateRunResponse,
    RunDetails,
    ErrorResponse
)
from app.services.agent_orchestrator import AgentOrchestrator
from app.core.deps import get_db, get_orchestrator

router = APIRouter(prefix="/runs")

@router.post(
    "",
    response_model=CreateRunResponse,  # Pydantic validates response
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ValidationErrorResponse}
    }
)
async def create_run(
    request: CreateRunRequest,  # Pydantic validates request automatically
    background_tasks: BackgroundTasks,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    db: AsyncSession = Depends(get_db),
) -> CreateRunResponse:
    """
    Create a new agent run with automatic validation.
    
    Pydantic ensures:
    - GitHub URL is valid and starts with https://github.com/
    - Prompt is 10-2000 characters
    - Variations is between 1-5
    - Agent config has valid model, temperature, etc.
    """
    try:
        # Create execution context with validated data
        context = AgentExecutionContext(
            run_id=uuid4(),
            variation_id=0,
            repo_url=request.github_url,
            prompt=request.prompt,
            config=request.agent_config or AgentConfig(),
            container_config=DaggerContainerConfig(
                memory_limit=settings.agent_memory_limit,
                cpu_limit=settings.agent_cpu_limit
            )
        )
        
        # Context is fully validated by Pydantic
        run = await create_run_in_db(db, context)
        
        # Schedule background task
        background_tasks.add_task(
            orchestrator.execute_with_context,
            context
        )
        
        # Response is validated before returning
        return CreateRunResponse(
            run_id=run.id,
            stream_url=f"{settings.api_v1_prefix}/runs/{run.id}/stream",
            status="accepted",
            estimated_duration_seconds=request.variations * 40
        )
        
    except ValidationError as e:
        # Pydantic validation errors are automatically 422
        raise
    except Exception as e:
        # Other errors become 500
        logger.error(f"Failed to create run: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

# Streaming with validated events
async def stream_events(run_id: UUID) -> AsyncIterator[str]:
    """Stream validated SSE events"""
    async for event in orchestrator.get_events(run_id):
        # Each event is a Pydantic model
        if isinstance(event, AgentOutputEvent):
            yield f"event: {event.event_type.value}\n"
            yield f"data: {event.model_dump_json()}\n\n"
        elif isinstance(event, ErrorEvent):
            yield f"event: error\n"
            yield f"data: {event.model_dump_json()}\n\n"
```

### SSE Streaming Pattern

```python
from fastapi import Response
from fastapi.responses import StreamingResponse
import asyncio
import json

async def event_generator(run_id: str):
    """Generate SSE events for agent outputs."""
    async for event in agent_stream:
        yield f"event: message\ndata: {json.dumps(event)}\n\n"
    
    yield f"event: complete\ndata: {json.dumps({'status': 'completed'})}\n\n"

@router.get("/{run_id}/stream")
async def stream_run(run_id: str) -> StreamingResponse:
    """Stream agent outputs via Server-Sent Events."""
    return StreamingResponse(
        event_generator(run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
```

### Database Pattern (SQLite with SQLModel)

```python
from sqlmodel import Field, SQLModel, Session, select
from datetime import datetime
from typing import Optional

class Run(SQLModel, table=True):
    """Database model for agent runs."""
    id: str = Field(primary_key=True)
    github_url: str
    prompt: str
    variations: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    winning_variation: Optional[int] = None

async def get_run(db: AsyncSession, run_id: str) -> Optional[Run]:
    """Retrieve a run by ID."""
    result = await db.execute(select(Run).where(Run.id == run_id))
    return result.scalar_one_or_none()
```

## 🔐 Security Practices

### SQL Injection Prevention

```python
# ❌ NEVER do this
query = f"SELECT * FROM runs WHERE id = '{run_id}'"

# ✅ Always use parameterized queries
result = await db.execute(
    select(Run).where(Run.id == run_id)
)
```

### Environment Configuration for Dagger

```python
# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with validation and Dagger support."""
    # API Configuration
    api_v1_prefix: str = "/api/v1"
    project_name: str = "AIdeator"
    version: str = "1.0.0"
    debug: bool = False
    
    # Security
    anthropic_api_key: str
    api_key_header: str = "X-API-Key"
    allowed_origins: list[str] = ["*"]
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./aideator.db"
    database_echo: bool = False
    
    # Dagger Configuration
    dagger_log_output: bool = True
    dagger_engine_timeout: int = 600  # 10 minutes
    dagger_cache_volume: str = "aideator-cache"
    dagger_workdir: str = "/workspace"
    
    # Agent Configuration
    max_variations: int = 5
    max_prompt_length: int = 2000
    agent_container_image: str = "python:3.11-slim"
    agent_memory_limit: str = "512m"
    agent_cpu_limit: float = 0.5
    
    # Repository Configuration
    clone_timeout: int = 300  # 5 minutes
    max_repo_size_mb: int = 100
    
    # SSE Configuration
    sse_ping_interval: int = 30
    sse_retry_timeout: int = 3000
    
    # Redis (optional, for production)
    redis_url: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    def get_dagger_secrets(self) -> dict[str, str]:
        """Get secrets to mount in Dagger containers."""
        return {
            "anthropic-api-key": self.anthropic_api_key,
        }

@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()

# Dagger-specific environment setup
class DaggerEnvironment:
    """Manages environment variables for Dagger containers."""
    
    @staticmethod
    def get_agent_env(variation_id: int) -> dict[str, str]:
        """Get environment variables for agent container."""
        return {
            "PYTHONUNBUFFERED": "1",
            "AGENT_VARIATION_ID": str(variation_id),
            "LOG_LEVEL": "INFO",
        }
    
    @staticmethod
    def get_build_args() -> dict[str, str]:
        """Get build args for container construction."""
        settings = get_settings()
        return {
            "PYTHON_VERSION": "3.11",
            "WORKDIR": settings.dagger_workdir,
        }
```

### Environment File Example

```bash
# .env.example
# API Configuration
API_V1_PREFIX=/api/v1
PROJECT_NAME=AIdeator
VERSION=1.0.0
DEBUG=false

# Security
ANTHROPIC_API_KEY=sk-ant-api03-...
API_KEY_HEADER=X-API-Key
ALLOWED_ORIGINS=["http://localhost:3000","https://app.aideator.com"]

# Database
DATABASE_URL=sqlite+aiosqlite:///./aideator.db
DATABASE_ECHO=false

# Dagger Configuration
DAGGER_LOG_OUTPUT=true
DAGGER_ENGINE_TIMEOUT=600
DAGGER_CACHE_VOLUME=aideator-cache
DAGGER_WORKDIR=/workspace

# Agent Configuration
MAX_VARIATIONS=5
MAX_PROMPT_LENGTH=2000
AGENT_CONTAINER_IMAGE=python:3.11-slim
AGENT_MEMORY_LIMIT=512m
AGENT_CPU_LIMIT=0.5

# Repository Configuration
CLONE_TIMEOUT=300
MAX_REPO_SIZE_MB=100

# SSE Configuration
SSE_PING_INTERVAL=30
SSE_RETRY_TIMEOUT=3000

# Redis (optional)
# REDIS_URL=redis://localhost:6379/0
```

## 🧪 Testing Approach

### Modern Test Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = [
    "--strict-markers",
    "--tb=short",
    "--cov=app",
    "--cov-branch",
    "--cov-report=term-missing:skip-covered",
    "--cov-fail-under=80",
]
markers = [
    "unit: Unit tests (fast)",
    "integration: Integration tests (slower)",
    "e2e: End-to-end tests (slowest)",
]

[tool.coverage.run]
source = ["app"]
omit = ["*/tests/*", "*/migrations/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if __name__ == .__main__.:",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
```

### Unit Test Pattern with Fixtures

```python
import pytest
from httpx import AsyncClient
from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from app.main import app
from app.models import Run
from app.database import get_session

# Fixtures
@pytest.fixture
async def async_client():
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def db_session():
    """Create a test database session with rollback."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()

# Override dependency
@pytest.fixture(autouse=True)
def override_get_session(db_session):
    """Override the database session dependency."""
    app.dependency_overrides[get_session] = lambda: db_session

# Unit test example
@pytest.mark.unit
async def test_create_run(async_client: AsyncClient, db_session: AsyncSession):
    """Test creating a new run."""
    response = await async_client.post("/api/v1/runs", json={
        "github_url": "https://github.com/user/repo",
        "prompt": "Refactor the main function",
        "variations": 3
    })
    
    assert response.status_code == 202
    data = response.json()
    assert "run_id" in data
    assert "stream_url" in data
    
    # Verify database
    run = await db_session.get(Run, data["run_id"])
    assert run is not None
    assert run.github_url == "https://github.com/user/repo"

# Parametrized test example
@pytest.mark.parametrize("variations,expected_status", [
    (1, 202),
    (5, 202),
    (0, 422),  # Invalid: too few
    (6, 422),  # Invalid: too many
])
async def test_create_run_variations(
    async_client: AsyncClient, 
    variations: int, 
    expected_status: int
):
    """Test run creation with different variation counts."""
    response = await async_client.post("/api/v1/runs", json={
        "github_url": "https://github.com/user/repo",
        "prompt": "Test prompt",
        "variations": variations
    })
    assert response.status_code == expected_status
```

### E2E Test Pattern

```python
import asyncio
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from playwright.async_api import async_playwright, Page

@pytest.fixture
async def api_server():
    """Start the API server for E2E tests."""
    # In practice, you might use a subprocess or docker container
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.fixture
async def browser_page() -> AsyncGenerator[Page, None]:
    """Create a browser page for E2E tests."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        yield page
        await browser.close()

@pytest.mark.e2e
async def test_full_flow(api_server: AsyncClient, browser_page: Page):
    """Test the complete user flow from submission to selection."""
    # Create a run via API
    response = await api_server.post("/api/v1/runs", json={
        "github_url": "https://github.com/fastapi/fastapi",
        "prompt": "Add type hints to main.py",
        "variations": 3
    })
    assert response.status_code == 202
    run_id = response.json()["run_id"]
    
    # Connect to SSE stream
    stream_url = f"/api/v1/runs/{run_id}/stream"
    events = []
    
    async with api_server.stream("GET", stream_url) as stream:
        async for line in stream.aiter_lines():
            if line.startswith("data: "):
                events.append(line[6:])
            if len(events) >= 10:  # Collect some events
                break
    
    # Verify we got events
    assert len(events) > 0
    
    # Select a winning variation
    response = await api_server.post(f"/api/v1/runs/{run_id}/select", json={
        "winning_variation_id": 1
    })
    assert response.status_code == 200
```

### Test Utilities

```python
# tests/conftest.py
import pytest
from typing import AsyncGenerator
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.main import app

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh test database for each test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session

# Factory fixtures
@pytest.fixture
def make_run():
    """Factory for creating test runs."""
    def _make_run(**kwargs):
        defaults = {
            "github_url": "https://github.com/test/repo",
            "prompt": "Test prompt",
            "variations": 3,
        }
        return Run(**{**defaults, **kwargs})
    return _make_run
```

## 🚨 Common Pitfalls to Avoid

### What I Never Do

- ❌ Use synchronous I/O in async functions (open, requests, time.sleep)
- ❌ Return static/mock data in production endpoints
- ❌ Use string formatting for SQL queries
- ❌ Forget to handle exceptions in async operations
- ❌ Mix sync and async database operations

### What I Always Do

- ✅ Use `async def` for all route handlers
- ✅ Implement proper error handling with HTTPException
- ✅ Add response_model to endpoints for validation
- ✅ Use dependency injection for database sessions
- ✅ Set appropriate status codes (201 for POST, 202 for async operations)
- ✅ Validate all user inputs with Pydantic models

## 🔄 Development Workflow

### Modern Tool Configuration

```toml
# pyproject.toml - Complete configuration
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "aideator"
version = "0.1.0"
description = "Dagger-powered LLM orchestration platform"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.0.0",
    "sqlmodel>=0.0.14",
    "aiosqlite>=0.19.0",
    "httpx>=0.25.0",
    "dagger-io>=0.9.0",
    "anthropic>=0.18.0",
    "python-multipart>=0.0.6",
    "sse-starlette>=2.0.0",
    "structlog>=23.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "mypy>=1.7.0",
    "ruff>=0.1.0",
    "httpx>=0.25.0",  # For testing
    "hypothesis>=6.90.0",  # Property testing
]

[tool.ruff]
# Enable pycodestyle, pyflakes, bugbear, and more
select = ["E", "F", "B", "W", "I", "N", "UP", "S", "A", "C4", "RET", "SIM", "TCH"]
ignore = ["E501", "B008"]  # Line length handled by formatter, B008 for FastAPI Depends
line-length = 88
target-version = "py311"

[tool.ruff.per-file-ignores]
"tests/*" = ["S101", "S106"]  # Allow assert and hardcoded passwords in tests

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

# Per-module options
[[tool.mypy.overrides]]
module = "tests.*"
ignore_errors = true

[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
asyncio_mode = "auto"
```

### Ruff Configuration (Alternative)

```toml
# ruff.toml - If you prefer separate config
[lint]
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "I",   # isort
    "B",   # bugbear
    "C4",  # comprehensions
    "UP",  # pyupgrade
    "ARG", # unused arguments
    "SIM", # simplify
    "TCH", # type checking
]

[format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
```

### Before Committing

```bash
# Run all checks with uv
uv run ruff check --fix .        # Fix linting issues
uv run ruff format .             # Format code
uv run mypy app/                 # Type check
uv run pytest                    # Run tests
uv run pytest --cov=app --cov-fail-under=80  # Ensure coverage

# Or create a Makefile
# Makefile
.PHONY: check
check:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy app/
	uv run pytest --cov=app --cov-fail-under=80
```

### API Development Flow

1. Define Pydantic models with strict validation
2. Implement async route handler with type hints
3. Add comprehensive error handling
4. Write unit and integration tests
5. Run full quality check suite
6. Update OpenAPI documentation

## 🪝 CNS Hooks Integration

The project uses CNS hooks for quality enforcement:

### Active Hooks for Python/FastAPI

- **secret-scanner.py** - Prevents API key exposure
- **pre-commit-validator.py** - Runs ruff, mypy, and tests automatically
- **no-mock-code.py** - Ensures production-ready implementations
- **env-sync-validator.py** - Keeps .env files synchronized
- **fastapi-async-validator.py** - Enforces async best practices
- **python-type-hints-validator.py** - Encourages type annotations
- **mypy-strict-mode.py** - Ensures mypy strict compliance
- **python-testing-standards.py** - Enforces pytest best practices
- **sqlite-security-validator.py** - Prevents SQL injection

### Hook Benefits

- **Automatic Quality Gates**: Validates code before commits
- **Modern Tool Integration**: Works with uv, ruff, mypy
- **FastAPI-Specific**: Detects async/await issues, route patterns
- **Security First**: SQL injection prevention, secret scanning
- **Test Quality**: Ensures proper test structure and coverage

## 📚 Key Technologies

### Core Stack

- **FastAPI** - Modern async web framework with automatic OpenAPI
- **SQLite + SQLModel** - Lightweight database with async ORM
- **Pydantic** - Data validation and serialization
- **HTTPX** - Async HTTP client for Claude API integration
- **asyncio** - Concurrent task orchestration for N agents
- **Server-Sent Events** - Real-time streaming protocol

### Development Tools

- **uv** - Fast Python package manager (10-100x faster than pip)
- **pytest** - Testing framework with async support
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- **ruff** - All-in-one Python linter and formatter (replaces black, flake8, isort)
- **mypy** - Static type checker with strict mode
- **hypothesis** - Property-based testing for edge cases

### Testing Stack

- **Unit Tests**: pytest with fixtures and parametrization
- **Integration Tests**: httpx AsyncClient for API testing
- **E2E Tests**: playwright for full flow testing
- **Coverage**: 80% minimum enforced by hooks
- **Mocking**: pytest-mock for external dependencies

## 🎯 MVP Success Criteria

The backend successfully:

1. Accepts job submissions with repo URL and prompt
2. Clones repositories to temporary locations
3. Orchestrates N concurrent Claude API calls
4. Streams real-time agent outputs via SSE
5. Persists user's winning variation selection

______________________________________________________________________

**I am your primary coding assistant for AIdeator. I build production-ready FastAPI backends with real-time streaming, ensuring robust async patterns and comprehensive error handling.**