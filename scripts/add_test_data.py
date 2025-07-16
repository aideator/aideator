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
from app.models.task import Task, TaskOutput, TaskStatus
from app.models.user import User


async def add_test_data():
    """Add test tasks and outputs to the database."""
    async with async_session_maker() as session:
        # Create test user if it doesn't exist
        test_user = User(
            id="test-user-001",
            email="test@example.com",
            hashed_password="$2b$12$dummy.hash",
            is_active=True,
            is_superuser=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            full_name="Test User",
            max_runs_per_day=50,
            max_variations_per_run=10
        )
        session.add(test_user)
        await session.commit()

        # Create test tasks
        test_tasks = []

        # Task 1: Completed task with lots of outputs
        task1 = Task(
            github_url="https://github.com/fastapi/fastapi",
            prompt="Analyze this FastAPI repository and suggest performance improvements",
            agent_mode="claude-cli",
            variations=3,
            model_configs=[
                {"model_definition_id": "gpt-4", "custom_params": {"temperature": 0.7}},
                {"model_definition_id": "gpt-4", "custom_params": {"temperature": 0.5}},
                {"model_definition_id": "gpt-4", "custom_params": {"temperature": 0.9}}
            ],
            status=TaskStatus.COMPLETED,
            created_at=datetime.utcnow() - timedelta(hours=2),
            updated_at=datetime.utcnow() - timedelta(hours=1, minutes=30),
            started_at=datetime.utcnow() - timedelta(hours=2),
            completed_at=datetime.utcnow() - timedelta(hours=1, minutes=30),
            user_id="test-user-001",
            total_tokens_used=45000,
            total_cost_usd=1.35,
            internal_run_id="test-run-001"
        )
        test_tasks.append(task1)

        # Task 2: Currently running
        task2 = Task(
            github_url="https://github.com/tiangolo/sqlmodel",
            prompt="Review the codebase and create comprehensive documentation",
            agent_mode="claude-cli",
            variations=2,
            model_configs=[
                {"model_definition_id": "claude-3-opus", "custom_params": {"temperature": 0.5}},
                {"model_definition_id": "claude-3-opus", "custom_params": {"temperature": 0.7}}
            ],
            status=TaskStatus.RUNNING,
            created_at=datetime.utcnow() - timedelta(minutes=30),
            updated_at=datetime.utcnow() - timedelta(minutes=5),
            started_at=datetime.utcnow() - timedelta(minutes=30),
            user_id="test-user-001",
            internal_run_id="test-run-002"
        )
        test_tasks.append(task2)

        # Task 3: Failed task
        task3 = Task(
            github_url="https://github.com/invalid/repo",
            prompt="This will fail",
            agent_mode="claude-cli",
            variations=1,
            model_configs=[
                {"model_definition_id": "gpt-3.5-turbo", "custom_params": {"temperature": 0.7}}
            ],
            status=TaskStatus.FAILED,
            created_at=datetime.utcnow() - timedelta(hours=5),
            updated_at=datetime.utcnow() - timedelta(hours=4, minutes=55),
            started_at=datetime.utcnow() - timedelta(hours=5),
            completed_at=datetime.utcnow() - timedelta(hours=4, minutes=55),
            error_message="Repository not found",
            user_id="test-user-001",
            internal_run_id="test-run-003"
        )
        test_tasks.append(task3)

        # Task 4: Pending task
        task4 = Task(
            github_url="https://github.com/pydantic/pydantic",
            prompt="Analyze type safety and suggest improvements",
            agent_mode="claude-cli",
            variations=4,
            model_configs=[
                {"model_definition_id": "gpt-4", "custom_params": {"temperature": 0.6}},
                {"model_definition_id": "gpt-4", "custom_params": {"temperature": 0.4}},
                {"model_definition_id": "gpt-4", "custom_params": {"temperature": 0.8}},
                {"model_definition_id": "gpt-4", "custom_params": {"temperature": 0.5}}
            ],
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow() - timedelta(minutes=5),
            updated_at=datetime.utcnow() - timedelta(minutes=5),
            user_id="test-user-001",
            internal_run_id="test-run-004"
        )
        test_tasks.append(task4)

        # Add tasks to session
        for task in test_tasks:
            session.add(task)
        
        await session.commit()
        
        # Get the task IDs for creating outputs
        await session.refresh(task1)
        await session.refresh(task2)
        await session.refresh(task3)
        await session.refresh(task4)

        # Create task outputs 
        outputs = []

        # Messages for task1 (completed)
        base_time = datetime.utcnow() - timedelta(hours=2)
        for variation in range(3):
            # Initial status
            outputs.append(
                TaskOutput(
                    task_id=task1.id,
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
                    TaskOutput(
                        task_id=task1.id,
                        variation_id=variation,
                        content=msg,
                        output_type="stdout",
                        timestamp=base_time + timedelta(minutes=variation * 20 + i * 2),
                    )
                )

            # Add some logging
            outputs.append(
                TaskOutput(
                    task_id=task1.id,
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
                TaskOutput(
                    task_id=task1.id,
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
                TaskOutput(
                    task_id=task1.id,
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

        # Messages for task2 (currently running)
        base_time2 = datetime.utcnow() - timedelta(minutes=30)
        for variation in range(2):
            outputs.append(
                TaskOutput(
                    task_id=task2.id,
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
                    TaskOutput(
                        task_id=task2.id,
                        variation_id=variation,
                        content=msg,
                        output_type="stdout",
                        timestamp=base_time2
                        + timedelta(minutes=variation * 10 + i * 2),
                    )
                )

        # Error messages for task3 (failed)
        base_time3 = datetime.utcnow() - timedelta(hours=5)
        outputs.append(
            TaskOutput(
                task_id=task3.id,
                variation_id=0,
                content="🚀 Starting repository analysis...",
                output_type="stdout",
                timestamp=base_time3,
            )
        )

        outputs.append(
            TaskOutput(
                task_id=task3.id,
                variation_id=0,
                content="ERROR: Failed to clone repository: Repository not found",
                output_type="stderr",
                timestamp=base_time3 + timedelta(minutes=1),
            )
        )

        outputs.append(
            TaskOutput(
                task_id=task3.id,
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

        # No messages for task4 (pending)

        # Add all outputs to session
        for output in outputs:
            session.add(output)

        # Commit all data
        await session.commit()

        print(f"✅ Added {len(test_tasks)} test tasks")
        print(f"✅ Added {len(outputs)} task outputs")
        print("\nTest tasks created:")
        for task in test_tasks:
            print(f"  - {task.id}: {task.status.value} ({task.github_url})")


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
