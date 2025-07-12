#!/usr/bin/env python3
"""Add test data to the database for testing the admin page."""

import asyncio
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import async_session_maker
from app.models.run import AgentOutput, Run, RunStatus


async def add_test_data():
    """Add test runs and messages to the database."""
    async with async_session_maker() as session:
        # Create test runs
        test_runs = []

        # Run 1: Completed run with lots of messages
        run1 = Run(
            id="test-run-001",
            github_url="https://github.com/fastapi/fastapi",
            prompt="Analyze this FastAPI repository and suggest performance improvements",
            variations=3,
            status=RunStatus.COMPLETED,
            created_at=datetime.utcnow() - timedelta(hours=2),
            started_at=datetime.utcnow() - timedelta(hours=2),
            completed_at=datetime.utcnow() - timedelta(hours=1, minutes=30),
            winning_variation_id=1,
            agent_config={"model": "gpt-4", "temperature": 0.7},
            total_tokens_used=45000,
            total_cost_usd=1.35,
        )
        test_runs.append(run1)

        # Run 2: Currently running
        run2 = Run(
            id="test-run-002",
            github_url="https://github.com/tiangolo/sqlmodel",
            prompt="Review the codebase and create comprehensive documentation",
            variations=2,
            status=RunStatus.RUNNING,
            created_at=datetime.utcnow() - timedelta(minutes=30),
            started_at=datetime.utcnow() - timedelta(minutes=30),
            agent_config={"model": "claude-3-opus", "temperature": 0.5},
        )
        test_runs.append(run2)

        # Run 3: Failed run
        run3 = Run(
            id="test-run-003",
            github_url="https://github.com/invalid/repo",
            prompt="This will fail",
            variations=1,
            status=RunStatus.FAILED,
            created_at=datetime.utcnow() - timedelta(hours=5),
            started_at=datetime.utcnow() - timedelta(hours=5),
            completed_at=datetime.utcnow() - timedelta(hours=4, minutes=55),
            error_message="Repository not found",
            agent_config={"model": "gpt-3.5-turbo", "temperature": 0.7},
        )
        test_runs.append(run3)

        # Run 4: Pending run
        run4 = Run(
            id="test-run-004",
            github_url="https://github.com/pydantic/pydantic",
            prompt="Analyze type safety and suggest improvements",
            variations=4,
            status=RunStatus.PENDING,
            created_at=datetime.utcnow() - timedelta(minutes=5),
            agent_config={"model": "gpt-4", "temperature": 0.6},
        )
        test_runs.append(run4)

        # Add runs to session
        for run in test_runs:
            session.add(run)

        # Create agent outputs for the runs
        outputs = []

        # Messages for run1 (completed)
        base_time = datetime.utcnow() - timedelta(hours=2)
        for variation in range(3):
            # Initial status
            outputs.append(
                AgentOutput(
                    run_id="test-run-001",
                    variation_id=variation,
                    content=json.dumps(
                        {
                            "status": "variation_started",
                            "variation_id": variation,
                            "metadata": {"model": "gpt-4", "temperature": 0.7},
                        }
                    ),
                    output_type="status",
                    timestamp=base_time + timedelta(seconds=variation * 2),
                )
            )

            # Analysis messages
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
                outputs.append(
                    AgentOutput(
                        run_id="test-run-001",
                        variation_id=variation,
                        content=msg,
                        output_type="stdout",
                        timestamp=base_time + timedelta(minutes=variation * 20 + i * 2),
                    )
                )

            # Add some logging
            outputs.append(
                AgentOutput(
                    run_id="test-run-001",
                    variation_id=variation,
                    content=json.dumps(
                        {
                            "level": "INFO",
                            "message": f"Completed analysis for variation {variation}",
                            "files_analyzed": 127,
                            "issues_found": 8,
                            "suggestions_made": 12,
                        }
                    ),
                    output_type="logging",
                    timestamp=base_time + timedelta(minutes=variation * 20 + 25),
                )
            )

            # Summary
            outputs.append(
                AgentOutput(
                    run_id="test-run-001",
                    variation_id=variation,
                    content=f"## Summary for Variation {variation}\n\n"
                    + "### Key Findings:\n"
                    + "1. Database connection pooling can improve performance by 40%\n"
                    + "2. Implementing Redis caching for user sessions\n"
                    + "3. Async operations for all I/O bound tasks\n\n"
                    + "### Recommendations:\n"
                    + "- Upgrade to latest FastAPI version\n"
                    + "- Implement proper logging middleware\n"
                    + "- Add comprehensive API documentation",
                    output_type="summary",
                    timestamp=base_time + timedelta(minutes=variation * 20 + 28),
                )
            )

            # Completion status
            outputs.append(
                AgentOutput(
                    run_id="test-run-001",
                    variation_id=variation,
                    content=json.dumps(
                        {
                            "status": "variation_completed",
                            "variation_id": variation,
                            "metadata": {"success": True, "duration_seconds": 1680},
                        }
                    ),
                    output_type="status",
                    timestamp=base_time + timedelta(minutes=variation * 20 + 30),
                )
            )

        # Messages for run2 (currently running)
        base_time2 = datetime.utcnow() - timedelta(minutes=30)
        for variation in range(2):
            outputs.append(
                AgentOutput(
                    run_id="test-run-002",
                    variation_id=variation,
                    content=json.dumps(
                        {
                            "status": "variation_started",
                            "variation_id": variation,
                            "metadata": {"model": "claude-3-opus"},
                        }
                    ),
                    output_type="status",
                    timestamp=base_time2 + timedelta(seconds=variation * 2),
                )
            )

            # Ongoing analysis
            ongoing_messages = [
                "📚 Starting documentation analysis...",
                "📖 Reading existing documentation structure",
                "🔍 Analyzing code patterns and conventions",
                "📝 Generating documentation outline...",
                "✍️ Writing API documentation for core modules",
                "🏗️ Creating architecture overview diagrams",
                "📊 Documenting data models and relationships",
            ]

            for i, msg in enumerate(ongoing_messages[: random.randint(4, 7)]):  # noqa: S311
                outputs.append(
                    AgentOutput(
                        run_id="test-run-002",
                        variation_id=variation,
                        content=msg,
                        output_type="stdout",
                        timestamp=base_time2
                        + timedelta(minutes=variation * 10 + i * 2),
                    )
                )

        # Error messages for run3 (failed)
        base_time3 = datetime.utcnow() - timedelta(hours=5)
        outputs.append(
            AgentOutput(
                run_id="test-run-003",
                variation_id=0,
                content="🚀 Starting repository analysis...",
                output_type="stdout",
                timestamp=base_time3,
            )
        )

        outputs.append(
            AgentOutput(
                run_id="test-run-003",
                variation_id=0,
                content="ERROR: Failed to clone repository: Repository not found",
                output_type="stderr",
                timestamp=base_time3 + timedelta(minutes=1),
            )
        )

        outputs.append(
            AgentOutput(
                run_id="test-run-003",
                variation_id=0,
                content=json.dumps(
                    {
                        "status": "variation_failed",
                        "variation_id": 0,
                        "metadata": {
                            "error": "Repository not found",
                            "error_code": "REPO_404",
                        },
                    }
                ),
                output_type="status",
                timestamp=base_time3 + timedelta(minutes=2),
            )
        )

        # No messages for run4 (pending)

        # Add all outputs to session
        for output in outputs:
            session.add(output)

        # Commit all data
        await session.commit()

        print(f"✅ Added {len(test_runs)} test runs")
        print(f"✅ Added {len(outputs)} agent outputs")
        print("\nTest runs created:")
        for run in test_runs:
            print(f"  - {run.id}: {run.status.value} ({run.github_url})")


async def main():
    """Main function."""
    print("🚀 Adding test data to database...")
    try:
        await add_test_data()
        print("\n✅ Test data added successfully!")
        print("\nYou can now visit http://localhost:3000/admin to see the data")
    except Exception as e:
        print(f"\n❌ Error adding test data: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
