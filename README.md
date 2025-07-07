# AIdeator

A Dagger-powered LLM orchestration platform that runs multiple AI agents in isolated containers, streaming their thought processes in real-time.

## Quick Start

### Prerequisites

- Python 3.11+
- [Dagger CLI](https://docs.dagger.io/cli/465058/install)
- Docker (for Dagger engine)

### Installation

```bash
# Install Dagger CLI
curl -L https://dl.dagger.io/dagger/install.sh | sh

# Install Python dependencies (optional for local development)
pip install uv
uv pip install -e ".[dev]"
```

## Development with Dagger

All development tasks are containerized using Dagger. No local Python environment needed!

### Start Development Server

```bash
# Start FastAPI with hot reload
dagger call dev up --ports 8000:8000

# With custom port
dagger call dev --port=8080 up --ports 8080:8080
```

### Run Tests

```bash
# Run all tests with coverage
dagger call test

# Run specific test markers
dagger call test --markers="unit"
dagger call test --markers="integration"
dagger call test --markers="e2e"

# Run without coverage
dagger call test --coverage=false
```

### Code Quality

```bash
# Run linting
dagger call lint

# Run type checking
dagger call type-check

# Run security scans
dagger call security-scan

# Run complete CI pipeline
dagger call ci-pipeline
```

### Production Deployment

```bash
# Start production server
dagger call prod up --ports 8000:8000

# Start full stack with Dagger engine and Redis
dagger call full-stack up --ports 8000:8000

# Build production Docker image
dagger call build-production-image --tag="aideator:v1.0.0"
```

### Database Operations

```bash
# Run database migrations
dagger call migrate-database

# Generate OpenAPI specification
dagger call generate-openapi-spec export > openapi.json
```

### Development Tools

```bash
# Open interactive shell in container
dagger call build-base terminal

# Run E2E tests with full stack
dagger call e2e-test
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/api/v1/openapi.json

## Architecture

- **FastAPI**: Modern async web framework
- **Dagger**: Container orchestration for both development and agent execution
- **SQLite + SQLModel**: Lightweight async database
- **Server-Sent Events**: Real-time streaming of agent outputs
- **Anthropic Claude**: LLM for code generation tasks

## Project Structure

```
aideator/
├── app/                    # FastAPI application
│   ├── api/               # API routes
│   ├── core/              # Core configuration
│   ├── models/            # Database models
│   ├── schemas/           # Pydantic schemas
│   └── services/          # Business logic
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── e2e/               # End-to-end tests
├── dagger.py              # Dagger pipeline definitions
└── pyproject.toml         # Project configuration
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key variables:
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `SECRET_KEY`: JWT secret key (generate with `openssl rand -hex 32`)
- `DATABASE_URL`: SQLite database path
- `DAGGER_LOG_OUTPUT`: Enable Dagger logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `dagger call test`
4. Run CI pipeline: `dagger call ci-pipeline`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.