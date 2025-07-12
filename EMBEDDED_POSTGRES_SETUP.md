# Ultra-Fast Embedded PostgreSQL Testing Setup

This document describes the embedded PostgreSQL testing solution implemented for AIdeator, providing ultra-fast in-memory database testing using tmpfs.

## Overview

The embedded PostgreSQL solution provides:

- **Ultra-fast testing**: Database runs entirely in RAM using tmpfs
- **Isolated testing**: Each test gets a fresh database instance
- **Production-like**: Uses real PostgreSQL, not SQLite
- **Zero dependencies**: No external PostgreSQL server needed
- **CI/CD ready**: Works in containerized environments

## Installation

The embedded PostgreSQL testing requires:

1. **PostgreSQL binaries** (for pg_ctl, initdb, etc.)
2. **pytest-postgresql** Python package
3. **psycopg-binary** for PostgreSQL connectivity

### Installing PostgreSQL

```bash
# macOS
brew install postgresql@15

# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# Add to PATH (macOS)
echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Installing Python Dependencies

```bash
# Already added to pyproject.toml
uv add --dev pytest-postgresql psycopg-binary
```

## Files Created

### 1. `tests/conftest_embedded_postgres.py`
- **Embedded PostgreSQL fixtures**: `embedded_db_session`, `embedded_db_engine`, `embedded_client`
- **Factory fixtures**: `embedded_make_user`, `embedded_make_api_key`, `embedded_api_key_headers`
- **Ultra-fast PostgreSQL settings**: Optimized for testing performance
- **Tmpfs support**: Environment setup for RAM-based storage

### 2. `tests/unit/test_embedded_postgres.py`
- **Test basic functionality**: Raw SQL queries, database connectivity
- **Test user creation**: User model creation and persistence
- **Test API key creation**: API key model creation and relationships
- **Test performance**: Bulk operations timing

### 3. `pytest.ini`
- **Embedded PostgreSQL configuration**: Ultra-fast PostgreSQL options
- **Test markers**: `embedded_postgres` marker for embedded tests
- **Timeout settings**: 5-minute timeout for database operations

### 4. `scripts/setup_tmpfs_testing.sh`
- **Tmpfs setup**: Creates RAM-based filesystem for ultra-fast storage
- **Cross-platform**: Supports Linux (tmpfs) and macOS (RAM disk)
- **Automated**: One-command setup

### 5. `scripts/cleanup_tmpfs_testing.sh`
- **Cleanup**: Unmounts tmpfs and cleans up directories
- **Cross-platform**: Handles both Linux and macOS cleanup
- **Safe**: Checks if mounted before attempting cleanup

## Usage

### Running Embedded PostgreSQL Tests

```bash
# Run all embedded PostgreSQL tests
uv run pytest -m embedded_postgres

# Run specific embedded test
uv run pytest tests/unit/test_embedded_postgres.py::test_embedded_postgres_basic

# Run with verbose output
uv run pytest -m embedded_postgres -v -s

# Run without coverage (faster)
uv run pytest -m embedded_postgres --no-cov
```

### Using in Your Tests

```python
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.embedded_postgres
async def test_my_feature(embedded_db_session: AsyncSession, embedded_make_user):
    \"\"\"Test using embedded PostgreSQL.\"\"\"
    # Create test user
    user = await embedded_make_user(email="test@example.com")
    
    # Test database operations
    result = await embedded_db_session.execute(
        text("SELECT email FROM users WHERE id = :id"), {"id": user.id}
    )
    row = result.fetchone()
    assert row.email == "test@example.com"
```

## Performance Optimization

### Tmpfs Setup (Optional)

For maximum performance, set up tmpfs for database storage:

```bash
# Setup tmpfs (run once)
./scripts/setup_tmpfs_testing.sh

# Run tests with tmpfs
uv run pytest -m embedded_postgres

# Cleanup tmpfs (when done)
./scripts/cleanup_tmpfs_testing.sh
```

### PostgreSQL Settings

The embedded PostgreSQL uses ultra-fast settings:

```ini
# From pytest.ini
postgresql_postgres_options = -F -c shared_buffers=128MB -c fsync=off -c synchronous_commit=off -c full_page_writes=off -c checkpoint_segments=32 -c checkpoint_completion_target=0.9 -c wal_buffers=16MB -c effective_cache_size=256MB -c work_mem=8MB -c maintenance_work_mem=64MB -c random_page_cost=1.0 -c log_statement=none -c log_min_duration_statement=-1
```

### Key Optimizations

1. **fsync=off**: Disables disk synchronization for speed
2. **synchronous_commit=off**: Asynchronous commits
3. **full_page_writes=off**: Reduces write overhead
4. **shared_buffers=128MB**: Large buffer pool
5. **random_page_cost=1.0**: Optimized for SSD/RAM
6. **log_statement=none**: Reduces logging overhead

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests with Embedded PostgreSQL

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Install PostgreSQL
      run: |
        sudo apt-get update
        sudo apt-get install -y postgresql postgresql-contrib
        
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        pip install uv
        uv sync --dev
        
    - name: Setup tmpfs (optional)
      run: |
        sudo mkdir -p /tmp/aideator_test_db
        sudo mount -t tmpfs -o size=512M tmpfs /tmp/aideator_test_db
        
    - name: Run embedded PostgreSQL tests
      run: uv run pytest -m embedded_postgres
```

## Benefits

### Ultra-Fast Testing
- **RAM-based storage**: Database runs entirely in memory
- **Optimized settings**: PostgreSQL tuned for maximum speed
- **Parallel execution**: Multiple test databases simultaneously
- **No I/O bottlenecks**: Eliminates disk write delays

### Production-Like Testing
- **Real PostgreSQL**: Not SQLite or other substitutes
- **Full feature support**: All PostgreSQL features available
- **Accurate testing**: Same database engine as production
- **SQL compatibility**: Tests real SQL queries and constraints

### Developer Experience
- **Zero setup**: No external PostgreSQL server needed
- **Isolated tests**: Each test gets fresh database
- **Fast feedback**: Tests complete in seconds, not minutes
- **CI/CD ready**: Works in any containerized environment

## Troubleshooting

### Common Issues

1. **pg_config not found**
   ```bash
   # Install PostgreSQL development tools
   brew install postgresql@15  # macOS
   sudo apt-get install postgresql postgresql-contrib  # Ubuntu
   ```

2. **Permission denied**
   ```bash
   # Fix PostgreSQL permissions
   sudo chown -R $(whoami) /usr/local/var/postgres
   ```

3. **Port conflicts**
   ```bash
   # pytest-postgresql automatically assigns free ports
   # No manual configuration needed
   ```

4. **Slow tests**
   ```bash
   # Enable tmpfs for maximum speed
   ./scripts/setup_tmpfs_testing.sh
   ```

### Debugging

```bash
# Run with verbose output
uv run pytest -m embedded_postgres -v -s

# Check PostgreSQL logs
# Logs are in temporary directories shown in test output

# Test connectivity
uv run pytest tests/unit/test_embedded_postgres.py::test_embedded_postgres_basic -v
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Test Process                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   Test Case     │    │   Test Case     │                │
│  │                 │    │                 │                │
│  │ embedded_db_    │    │ embedded_db_    │                │
│  │ session         │    │ session         │                │
│  └─────────────────┘    └─────────────────┘                │
│           │                       │                         │
│           └───────────┬───────────┘                         │
│                       │                                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │            embedded_db_engine                           │ │
│  │        (AsyncSession + Connection Pool)                 │ │
│  └─────────────────────────────────────────────────────────┘ │
│                       │                                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              postgresql fixture                         │ │
│  │           (pytest-postgresql client)                    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                       │                                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │            postgresql_proc fixture                      │ │
│  │         (Embedded PostgreSQL Process)                   │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────────────────┐
│                 Operating System                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                  tmpfs (RAM)                            │ │
│  │                                                         │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │          PostgreSQL Data Directory                  │ │ │
│  │  │                                                     │ │ │
│  │  │  • WAL files in RAM                                 │ │ │
│  │  │  • Data files in RAM                                │ │ │
│  │  │  • Lock files in RAM                                │ │ │
│  │  │  • Log files in RAM                                 │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Future Enhancements

1. **Connection pooling**: Reuse connections across tests
2. **Snapshot testing**: Save/restore database states
3. **Parallel databases**: Multiple isolated databases per test
4. **Memory monitoring**: Track RAM usage and optimize
5. **Benchmark suite**: Performance regression testing