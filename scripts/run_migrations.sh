#!/bin/bash
"""
Run database migrations in Kubernetes container.
"""

set -e

echo "=== AIdeator Database Migration ==="
echo "Database URL: $DATABASE_URL"
echo

# Check if we're in a container or local environment
if [ -f "/app/alembic.ini" ]; then
    # Running in container
    cd /app
    echo "Running migrations in container..."
    python -m alembic upgrade head
else
    # Running locally
    echo "Running migrations locally..."
    python scripts/migrate.py up
fi

echo
echo "Migration completed successfully!"
echo "=================================="