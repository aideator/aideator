#!/usr/bin/env python3
"""Drop all tables in the database - force version."""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


async def drop_all_tables():
    """Drop all tables in the database."""
    # Get database URL from environment or use default
    database_url = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://aideator:aideator@localhost:5432/aideator"
    )
    
    print(f"Connecting to database: {database_url}")
    
    # Create engine
    engine = create_async_engine(database_url, echo=False)
    
    async with engine.begin() as conn:
        # Get all table names
        result = await conn.execute(text("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
        """))
        
        tables = [row[0] for row in result]
        
        if not tables:
            print("No tables found in the database.")
            await engine.dispose()
            return
        
        print(f"\nFound {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")
        
        # Drop all tables
        print("\nDropping tables...")
        
        # Disable foreign key checks temporarily
        await conn.execute(text("SET session_replication_role = 'replica';"))
        
        for table in tables:
            try:
                await conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                print(f"  ✓ Dropped table: {table}")
            except Exception as e:
                print(f"  ✗ Error dropping table {table}: {e}")
        
        # Re-enable foreign key checks
        await conn.execute(text("SET session_replication_role = 'origin';"))
        
        print("\nAll tables dropped successfully!")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(drop_all_tables())