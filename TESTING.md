# Testing Strategy for AIdeator

## Overview

AIdeator uses a comprehensive testing strategy with three distinct types of tests:

1. **Unit Tests** - Test individual functions/classes with mocked dependencies
2. **Integration Tests** - Test integration points with real services
3. **End-to-End Tests** - Test complete user workflows with all services

## Test Types

### Unit Tests (`-m unit`)
- **Purpose**: Test individual functions, classes, and modules in isolation
- **Dependencies**: All external dependencies are mocked (database, APIs, file system, etc.)
- **Execution**: Fast, no external services required
- **Coverage**: Should achieve 60%+ coverage for core business logic
- **Command**: `uv run pytest -m unit`

**Example**: Testing password hashing functions, schema validation, utility functions

### Integration Tests (`-m integration`)
- **Purpose**: Test integration points between components with real services
- **Dependencies**: Use real services (PostgreSQL, Redis, LiteLLM Gateway)
- **Execution**: Slower, requires service setup
- **Coverage**: Focus on integration patterns, not line coverage
- **Command**: `uv run pytest -m integration`

**Example**: Testing database operations, API client integrations, streaming functionality

### End-to-End Tests (`-m e2e`)
- **Purpose**: Test complete user workflows from UI to database
- **Dependencies**: Full application stack (API + Frontend + Services)
- **Execution**: Slowest, requires complete environment
- **Coverage**: User journey validation
- **Command**: `uv run pytest -m e2e`

**Example**: User registration → Login → Create run → Stream results → Select winner

## Service Requirements

### Unit Tests
- **Required**: None (all mocked)
- **Environment**: Any (CI, local, containers)

### Integration Tests
- **Required Services**:
  - PostgreSQL (test database)
  - Redis (caching)
  - LiteLLM Gateway (model routing)
- **Environment Variables**:
  ```bash
  DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aideator_test
  REDIS_URL=redis://localhost:6379
  LITELLM_GATEWAY_URL=http://localhost:4000
  ```

### End-to-End Tests
- **Required Services**:
  - All integration test services
  - Kubernetes cluster (k3d/minikube)
  - FastAPI application
  - Next.js frontend
- **Environment**: Tilt development environment

## Local Development

### Running Tests Locally

```bash
# Unit tests only (fast, no services required)
uv run pytest -m unit

# Integration tests (requires services)
docker-compose up -d postgres redis litellm
uv run pytest -m integration

# All tests with coverage
uv run pytest -m "unit or integration" --cov=app --cov-report=html

# Frontend tests
cd frontend/
npm run test:all
```

### Setting up Services for Integration Tests

#### Option 1: Docker Compose
```bash
# Start required services
docker-compose up -d postgres redis

# Set environment variables
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/aideator_test"
export REDIS_URL="redis://localhost:6379"

# Run integration tests
uv run pytest -m integration
```

#### Option 2: Manual Setup
```bash
# PostgreSQL
createdb aideator_test
export DATABASE_URL="postgresql://user:pass@localhost:5432/aideator_test"

# Redis
redis-server
export REDIS_URL="redis://localhost:6379"

# Run integration tests
uv run pytest -m integration
```

## CI/CD Strategy

### GitHub Actions Workflow

1. **Unit Tests** (`backend-unit-tests`)
   - Runs on every commit
   - No external services
   - Includes code quality checks (ruff, mypy, dead code analysis)
   - Coverage requirement: 60%

2. **Integration Tests** (`backend-integration-tests`)
   - Runs with GitHub Actions services (PostgreSQL, Redis)
   - Tests real database operations
   - Separate job to avoid service conflicts

3. **Frontend Tests** (`frontend-tests`)
   - Jest unit tests
   - TypeScript validation
   - Dead code analysis (Knip)

### Service Configuration in CI

```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_PASSWORD: postgres
      POSTGRES_USER: postgres
      POSTGRES_DB: aideator_test
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
    ports:
      - 5432:5432
  
  redis:
    image: redis:7-alpine
    options: >-
      --health-cmd "redis-cli ping"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
    ports:
      - 6379:6379
```

## Test Commands

### Backend Test Commands

```bash
# Single consolidated test command (unit + integration + quality)
uv run aideator-test-all

# Individual test types
uv run pytest -m unit                    # Unit tests only
uv run pytest -m integration             # Integration tests only
uv run pytest -m e2e                     # E2E tests only

# Quality checks
uv run ruff check .                       # Linting
uv run ruff format .                      # Formatting
uv run mypy app/                          # Type checking
uv run aideator-dead-code                 # Dead code detection

# Coverage
uv run pytest -m unit --cov=app --cov-report=html
```

### Frontend Test Commands

```bash
# Single consolidated test command
npm run test:all

# Individual test types
npm run test:unit                         # Jest unit tests
npm run test:integration                  # API integration tests
npm run test:e2e                          # Playwright E2E tests

# Quality checks
npm run type-check                        # TypeScript validation
npm run lint                              # ESLint
npm run knip                              # Dead code detection

# Coverage
npm run test:unit:coverage                # Jest with coverage
npm run test:all:coverage                 # All tests with coverage
```

## Best Practices

### Unit Tests
- Mock all external dependencies
- Test business logic, not implementation details
- Use descriptive test names
- Group related tests in classes
- Use pytest fixtures for common setup

### Integration Tests
- Test real integration points
- Use test databases, not production data
- Clean up after tests (database transactions)
- Test error conditions and edge cases
- Use realistic test data

### End-to-End Tests
- Test complete user workflows
- Use Page Object Model for UI tests
- Test critical paths first
- Handle timing issues (waits, retries)
- Test error scenarios and recovery

## Troubleshooting

### Common Issues

1. **Integration tests failing with connection errors**
   - Check that services are running
   - Verify connection strings
   - Check firewall/network settings

2. **Unit tests with import errors**
   - Ensure all dependencies are installed
   - Check PYTHONPATH if running outside virtual environment

3. **Coverage too low**
   - Add tests for uncovered code paths
   - Remove dead code
   - Check if tests are properly marked

### Debugging Tests

```bash
# Run specific test with verbose output
uv run pytest tests/unit/test_auth.py::test_password_hashing -v

# Run with pdb debugger
uv run pytest tests/unit/test_auth.py --pdb

# Run with coverage and show missing lines
uv run pytest -m unit --cov=app --cov-report=term-missing
```

## Integration Test Examples

### Database Integration
```python
@pytest.mark.integration
async def test_user_creation():
    """Test user creation with real database."""
    async with get_session() as session:
        user = User(email="test@example.com", ...)
        session.add(user)
        await session.commit()
        
        # Test user was created
        result = await session.get(User, user.id)
        assert result.email == "test@example.com"
```

### API Integration
```python
@pytest.mark.integration
async def test_litellm_gateway():
    """Test LiteLLM Gateway integration."""
    response = await litellm.acompletion(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}],
        api_base="http://localhost:4000"
    )
    assert response.choices[0].message.content
```

This testing strategy ensures comprehensive coverage while maintaining fast feedback loops and clear separation of concerns.