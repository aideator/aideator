#!/usr/bin/env python3
"""
Clear agent_outputs data from database.
"""

import asyncio
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def clear_agent_outputs():
    """Clear all agent_outputs data from database."""
    # Use the standard database URL from environment or default
    database_url = os.getenv("DATABASE_URL", "postgresql://aideator:aideator123@localhost:5432/aideator")

    # Convert to async format
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print(f"Connecting to database: {database_url}")

    try:
        engine = create_async_engine(database_url)

        async with engine.begin() as conn:
            # Clear agent_outputs table
            result = await conn.execute(text("DELETE FROM agent_outputs;"))
            print(f"Deleted {result.rowcount} records from agent_outputs table")

            # Reset auto-increment counter
            await conn.execute(text("ALTER SEQUENCE agent_outputs_id_seq RESTART WITH 1;"))
            print("Reset agent_outputs ID sequence")

        await engine.dispose()
        print("Database cleared successfully")

    except Exception as e:
        print(f"Error clearing database: {e}")
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(clear_agent_outputs())
    exit(0 if success else 1)
