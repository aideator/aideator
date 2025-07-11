#!/usr/bin/env python3
"""Add test data directly to SQLite database."""

import sqlite3
import json
from datetime import datetime, timedelta
import random

# Database path - same as what the app uses
DB_PATH = "./aideator.db"

def add_test_data():
    """Add test runs and messages to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            github_url TEXT,
            prompt TEXT,
            variations INTEGER,
            status TEXT,
            winning_variation_id INTEGER,
            created_at TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            agent_config TEXT,
            user_id TEXT,
            api_key_id TEXT,
            results TEXT,
            error_message TEXT,
            total_tokens_used INTEGER,
            total_cost_usd REAL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_outputs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
            variation_id INTEGER,
            content TEXT,
            timestamp TIMESTAMP,
            output_type TEXT,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        )
    """)
    
    # Clear existing test data
    cursor.execute("DELETE FROM agent_outputs WHERE run_id LIKE 'test-run-%'")
    cursor.execute("DELETE FROM runs WHERE id LIKE 'test-run-%'")
    
    # Create test runs
    now = datetime.utcnow()
    
    # Run 1: Completed run
    cursor.execute("""
        INSERT INTO runs (id, github_url, prompt, variations, status, winning_variation_id,
                         created_at, started_at, completed_at, agent_config, total_tokens_used, total_cost_usd)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "test-run-001",
        "https://github.com/fastapi/fastapi",
        "Analyze this FastAPI repository and suggest performance improvements",
        3,
        "completed",
        1,
        (now - timedelta(hours=2)).isoformat(),
        (now - timedelta(hours=2)).isoformat(),
        (now - timedelta(hours=1, minutes=30)).isoformat(),
        json.dumps({"model": "gpt-4", "temperature": 0.7}),
        45000,
        1.35
    ))
    
    # Run 2: Currently running
    cursor.execute("""
        INSERT INTO runs (id, github_url, prompt, variations, status,
                         created_at, started_at, agent_config)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "test-run-002",
        "https://github.com/tiangolo/sqlmodel",
        "Review the codebase and create comprehensive documentation",
        2,
        "running",
        (now - timedelta(minutes=30)).isoformat(),
        (now - timedelta(minutes=30)).isoformat(),
        json.dumps({"model": "claude-3-opus", "temperature": 0.5})
    ))
    
    # Run 3: Failed run
    cursor.execute("""
        INSERT INTO runs (id, github_url, prompt, variations, status,
                         created_at, started_at, completed_at, error_message, agent_config)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "test-run-003",
        "https://github.com/invalid/repo",
        "This will fail",
        1,
        "failed",
        (now - timedelta(hours=5)).isoformat(),
        (now - timedelta(hours=5)).isoformat(),
        (now - timedelta(hours=4, minutes=55)).isoformat(),
        "Repository not found",
        json.dumps({"model": "gpt-3.5-turbo", "temperature": 0.7})
    ))
    
    # Run 4: Pending run
    cursor.execute("""
        INSERT INTO runs (id, github_url, prompt, variations, status,
                         created_at, agent_config)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "test-run-004",
        "https://github.com/pydantic/pydantic",
        "Analyze type safety and suggest improvements",
        4,
        "pending",
        (now - timedelta(minutes=5)).isoformat(),
        json.dumps({"model": "gpt-4", "temperature": 0.6})
    ))
    
    # Create agent outputs
    base_time = now - timedelta(hours=2)
    
    # Messages for run1 (completed)
    for variation in range(3):
        # Status message
        cursor.execute("""
            INSERT INTO agent_outputs (run_id, variation_id, content, timestamp, output_type)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "test-run-001",
            variation,
            json.dumps({
                "status": "variation_started",
                "variation_id": variation,
                "metadata": {"model": "gpt-4", "temperature": 0.7}
            }),
            (base_time + timedelta(seconds=variation * 2)).isoformat(),
            "status"
        ))
        
        # Regular messages
        messages = [
            "🔍 Analyzing repository structure...",
            "📊 Found 127 Python files to analyze",
            "🏗️ Repository structure:\n- app/\n  - main.py\n  - routers/\n  - models/\n  - dependencies/",
            "🔎 Scanning for performance patterns...",
            "⚡ Found potential optimization: Database connection pooling",
            "💡 Suggestion: Implement async database operations",
            "🚀 Performance tip: Use Redis for caching frequently accessed data",
            "📈 Analyzing API endpoint performance...",
            "⚠️ Warning: N+1 query pattern detected in /api/users endpoint",
            "✅ Good practice found: Proper use of FastAPI dependencies",
        ]
        
        for i, msg in enumerate(messages):
            cursor.execute("""
                INSERT INTO agent_outputs (run_id, variation_id, content, timestamp, output_type)
                VALUES (?, ?, ?, ?, ?)
            """, (
                "test-run-001",
                variation,
                msg,
                (base_time + timedelta(minutes=variation * 20 + i * 2)).isoformat(),
                "stdout"
            ))
        
        # Logging message
        cursor.execute("""
            INSERT INTO agent_outputs (run_id, variation_id, content, timestamp, output_type)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "test-run-001",
            variation,
            json.dumps({
                "level": "INFO",
                "message": f"Completed analysis for variation {variation}",
                "files_analyzed": 127,
                "issues_found": 8,
                "suggestions_made": 12
            }),
            (base_time + timedelta(minutes=variation * 20 + 25)).isoformat(),
            "logging"
        ))
        
        # Summary
        cursor.execute("""
            INSERT INTO agent_outputs (run_id, variation_id, content, timestamp, output_type)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "test-run-001",
            variation,
            f"## Summary for Variation {variation}\n\n" +
            "### Key Findings:\n" +
            "1. Database connection pooling can improve performance by 40%\n" +
            "2. Implementing Redis caching for user sessions\n" +
            "3. Async operations for all I/O bound tasks\n\n" +
            "### Recommendations:\n" +
            "- Upgrade to latest FastAPI version\n" +
            "- Implement proper logging middleware\n" +
            "- Add comprehensive API documentation",
            (base_time + timedelta(minutes=variation * 20 + 28)).isoformat(),
            "summary"
        ))
        
        # Completion status
        cursor.execute("""
            INSERT INTO agent_outputs (run_id, variation_id, content, timestamp, output_type)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "test-run-001",
            variation,
            json.dumps({
                "status": "variation_completed",
                "variation_id": variation,
                "metadata": {"success": True, "duration_seconds": 1680}
            }),
            (base_time + timedelta(minutes=variation * 20 + 30)).isoformat(),
            "status"
        ))
    
    # Messages for run2 (currently running)
    base_time2 = now - timedelta(minutes=30)
    for variation in range(2):
        messages = [
            "📚 Starting documentation analysis...",
            "📖 Reading existing documentation structure",
            "🔍 Analyzing code patterns and conventions",
            "📝 Generating documentation outline...",
            "✍️ Writing API documentation for core modules",
        ]
        
        for i, msg in enumerate(messages[:random.randint(3, 5)]):
            cursor.execute("""
                INSERT INTO agent_outputs (run_id, variation_id, content, timestamp, output_type)
                VALUES (?, ?, ?, ?, ?)
            """, (
                "test-run-002",
                variation,
                msg,
                (base_time2 + timedelta(minutes=variation * 10 + i * 2)).isoformat(),
                "stdout"
            ))
    
    # Error messages for run3 (failed)
    base_time3 = now - timedelta(hours=5)
    cursor.execute("""
        INSERT INTO agent_outputs (run_id, variation_id, content, timestamp, output_type)
        VALUES (?, ?, ?, ?, ?)
    """, (
        "test-run-003",
        0,
        "ERROR: Failed to clone repository: Repository not found",
        (base_time3 + timedelta(minutes=1)).isoformat(),
        "stderr"
    ))
    
    # Commit changes
    conn.commit()
    
    # Get counts
    cursor.execute("SELECT COUNT(*) FROM runs WHERE id LIKE 'test-run-%'")
    run_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM agent_outputs WHERE run_id LIKE 'test-run-%'")
    output_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"✅ Added {run_count} test runs")
    print(f"✅ Added {output_count} agent outputs")
    print("\nTest runs created:")
    print("  - test-run-001: completed (fastapi)")
    print("  - test-run-002: running (sqlmodel)")
    print("  - test-run-003: failed (invalid repo)")
    print("  - test-run-004: pending (pydantic)")


if __name__ == "__main__":
    print("🚀 Adding test data to database...")
    try:
        add_test_data()
        print("\n✅ Test data added successfully!")
        print("\nYou can now visit http://localhost:3000/admin to see the data")
    except Exception as e:
        print(f"\n❌ Error adding test data: {e}")
        import traceback
        traceback.print_exc()