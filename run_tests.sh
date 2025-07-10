#!/bin/bash

# Run tests for model sync functionality

echo "Running model sync service tests..."
docker run --rm \
  -v $(pwd):/app \
  -w /app \
  -e PYTHONPATH=/app \
  -e DATABASE_URL="postgresql://test:test@localhost:5432/test" \
  -e SECRET_KEY="test-secret-key-32-chars-minimum" \
  -e LITELLM_PROXY_URL="http://localhost:4000" \
  python:3.11-slim \
  bash -c "pip install -q pytest pytest-asyncio sqlmodel httpx && python -m pytest tests/unit/test_model_sync_service.py tests/unit/test_model_sync_task.py tests/unit/test_admin_endpoints.py -v"