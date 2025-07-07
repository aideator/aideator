# AIdeator

A Dagger-powered LLM orchestration platform that runs multiple AI agents in isolated containers, streaming their thought processes in real-time.

## Features

- **Container Isolation**: Each agent runs in its own Dagger container
- **Real-time Streaming**: Server-Sent Events (SSE) for live agent output
- **Parallel Execution**: Run N variations of agents concurrently
- **GitHub Integration**: Clone and analyze any public repository
- **OpenAPI Documentation**: Auto-generated API docs with Swagger UI
- **Async Architecture**: Built on FastAPI with SQLModel and async patterns

## Prerequisites

- Python 3.11+
- Docker (for Dagger)
- [uv](https://github.com/astral-sh/uv) package manager
- [Dagger CLI](https://docs.dagger.io/install) v0.18.12+

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/aideator.git
cd aideator

# Install dependencies with uv
uv pip install -e .

# Copy environment variables
cp .env.example .env

# Edit .env and add your ANTHROPIC_API_KEY
# Set DEBUG=true for development
```

### 2. Run Locally

```bash
# Start the FastAPI server with hot reload
uv run uvicorn app.main:app --reload

# Server runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### 3. Run with Dagger

```bash
# Ensure SSH_AUTH_SOCK is unset (known issue)
export SSH_AUTH_SOCK=""

# Run development server in container
dagger call dev --source=. up --ports 8001:8000

# Run tests
dagger call test --source=.

# Run linting
dagger call lint --source=.
```

## Project Structure

```
aideator/
├── app/                    # FastAPI application
│   ├── api/               # API endpoints
│   ├── core/              # Core configuration and database
│   ├── models/            # SQLModel database models
│   ├── schemas/           # Pydantic validation schemas
│   ├── services/          # Business logic and services
│   └── main.py            # Application entry point
├── src/                    # Dagger module
│   ├── main.py            # Dagger functions (dev, test, lint)
│   └── pyproject.toml     # Dagger module configuration
├── tests/                  # Test suite
├── pyproject.toml         # Project dependencies and config
└── dagger.json            # Dagger module configuration
```

## Development

### API Endpoints

Key endpoints available at http://localhost:8000/docs (or http://localhost:8001/docs when using Dagger):

- `POST /api/v1/runs` - Create a new agent run
- `GET /api/v1/runs` - List all runs
- `GET /api/v1/runs/{run_id}/stream` - Stream run output via SSE
- `GET /api/v1/health` - Health check endpoint
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_api.py -v
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type checking
uv run mypy app/

# Security scanning
uv run bandit -r app/
uv run semgrep --config=auto app/
```

### Database

The application uses SQLite with SQLModel (async via aiosqlite). Database is created automatically on startup.

```bash
# Database location
./aideator.db

# To reset the database, simply delete the file
rm aideator.db
```

### Environment Variables

Key configuration in `.env`:

```bash
# Enable debug mode and API docs
DEBUG=true

# API configuration
ANTHROPIC_API_KEY=sk-ant-api03-...
SECRET_KEY=your-secret-key-here

# Dagger settings
AGENT_CONTAINER_IMAGE=python:3.11-slim
MAX_VARIATIONS=5
AGENT_TIMEOUT=300

# Database
DATABASE_URL=sqlite+aiosqlite:///./aideator.db
```

## Architecture

### System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        UI[Web UI/CLI Client]
    end
    
    subgraph "API Layer"
        FastAPI[FastAPI Server]
        Auth[JWT/API Key Auth]
        SSE[SSE Streaming]
    end
    
    subgraph "Service Layer"
        AO[Agent Orchestrator]
        DS[Dagger Service]
        SSM[SSE Manager]
    end
    
    subgraph "Container Layer"
        DC[Dagger Client]
        subgraph "Isolated Containers"
            A1[Agent 1<br/>Container]
            A2[Agent 2<br/>Container]
            A3[Agent N<br/>Container]
        end
    end
    
    subgraph "External Services"
        Claude[Claude API]
        GitHub[GitHub Repos]
    end
    
    subgraph "Data Layer"
        SQLite[(SQLite DB)]
        Cache[Container Cache]
    end
    
    UI -->|HTTP/WSS| FastAPI
    FastAPI --> Auth
    Auth --> AO
    AO --> DS
    AO --> SSM
    DS --> DC
    DC --> A1
    DC --> A2
    DC --> A3
    A1 --> Claude
    A2 --> Claude
    A3 --> Claude
    A1 --> GitHub
    A2 --> GitHub
    A3 --> GitHub
    SSM --> SSE
    SSE -->|Real-time Events| UI
    AO --> SQLite
    DC --> Cache
    
    style FastAPI fill:#e1f5f0
    style AO fill:#e8f5e9
    style DS fill:#e8f5e9
    style DC fill:#fff3e0
    style A1 fill:#e3f2fd
    style A2 fill:#e3f2fd
    style A3 fill:#e3f2fd
    style Claude fill:#f3e5f5
    style GitHub fill:#f3e5f5
```

### Request Flow

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant Auth
    participant Orchestrator
    participant Dagger
    participant Container
    participant Claude
    participant SSE
    
    Client->>FastAPI: POST /api/v1/runs
    FastAPI->>Auth: Validate JWT/API Key
    Auth-->>FastAPI: Authorized
    FastAPI->>Orchestrator: Create Run
    Orchestrator->>Dagger: Build Containers
    
    loop For Each Variation
        Dagger->>Container: Spawn Agent
        Container->>Container: Clone Repo
        Container->>Claude: Generate Code
        Claude-->>Container: Response
        Container->>SSE: Stream Output
        SSE-->>Client: Real-time Events
    end
    
    Orchestrator->>FastAPI: Run Created
    FastAPI-->>Client: 202 Accepted + Stream URL
```

### Core Components

1. **FastAPI Application**: Async web framework with automatic OpenAPI generation
2. **Dagger Service**: Container orchestration for isolated agent execution
3. **Agent Orchestrator**: Manages parallel agent execution and result aggregation
4. **SSE Streaming**: Real-time output streaming using Server-Sent Events
5. **SQLModel**: Async ORM for database operations

### Security

- JWT-based authentication
- API key authentication via `X-API-Key` header
- Rate limiting middleware
- Input validation with Pydantic
- SQL injection protection via SQLModel

### Monitoring

- Structured logging with `structlog`
- Prometheus metrics at `/api/v1/metrics`
- Request ID tracking for debugging
- Performance timing on all requests

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Write tests for new features
- Maintain type hints throughout
- Follow existing code patterns
- Update API documentation
- Run the full test suite before submitting

## Troubleshooting

### Common Issues

1. **Dagger SSH Socket Error**: Unset SSH_AUTH_SOCK before running Dagger commands
   ```bash
   export SSH_AUTH_SOCK=""
   ```

2. **Module Import Errors**: Ensure you're using `uv` to manage dependencies
   ```bash
   uv pip install -e .
   ```

3. **Database Locked**: Stop all running instances before starting a new one

4. **Port Already in Use**: Kill the process using port 8000
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```

## License

MIT License - see LICENSE file for details