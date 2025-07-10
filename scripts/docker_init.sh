#!/bin/bash
"""
Docker initialization script for AIdeator.
This script runs database migrations and seeding when the container starts.
"""

set -e

echo "🚀 AIdeator Container Initialization"
echo "====================================="

# Check if we're in development mode
if [ "$DEBUG" = "true" ]; then
    echo "📍 Running in development mode"
    
    # Check database connection
    echo "🔍 Checking database connection..."
    python -c "
import asyncio
from app.core.database import engine
async def test_db():
    async with engine.connect() as conn:
        result = await conn.execute('SELECT 1')
        print('✅ Database connection successful')
asyncio.run(test_db())
" || {
    echo "❌ Database connection failed"
    exit 1
}
    
    # Run seed script to create test user
    echo "🌱 Seeding development data..."
    python /app/seed_database.py || {
        echo "⚠️  Seeding failed, but continuing..."
    }
fi

echo "✅ Initialization complete"
echo "========================="