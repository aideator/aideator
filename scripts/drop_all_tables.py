#!/usr/bin/env python3
"""Drop all tables in the database."""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine


async def drop_all_tables():
    """Drop all tables in the database."""
    print(f"Connecting to database: {settings.DATABASE_URL}")

    async with engine.begin() as conn:
        # Get all table names
        result = await conn.execute(
            text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
        """)
        )

        tables = [row[0] for row in result]

        if not tables:
            print("No tables found in the database.")
            return

        print(f"\nFound {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")

        # Confirm before dropping
        confirm = input(
            "\nAre you sure you want to drop ALL tables? This cannot be undone! (yes/no): "
        )

        if confirm.lower() != "yes":
            print("Operation cancelled.")
            return

        # Drop all tables
        print("\nDropping tables...")

        # Disable foreign key checks temporarily
        await conn.execute(text("SET session_replication_role = 'replica';"))

        for table in tables:
            try:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"  ✓ Dropped table: {table}")
            except Exception as e:
                print(f"  ✗ Error dropping table {table}: {e}")

        # Re-enable foreign key checks
        await conn.execute(text("SET session_replication_role = 'origin';"))

        print("\nAll tables dropped successfully!")


if __name__ == "__main__":
    asyncio.run(drop_all_tables())
