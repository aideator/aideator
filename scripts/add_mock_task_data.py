#!/usr/bin/env python3
"""
Generate mock task data in database to replace frontend static data.
This script creates realistic TaskOutput entries that match the original mock data structure.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta

# Add the project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import select

from app.core.database import get_session
from app.models.task import Task, TaskOutput, TaskStatus
from app.models.user import User
from app.utils.dev_user import ensure_dev_user_exists


async def get_or_create_test_user() -> str:
    """Get or create a test user for the mock data - uses standardized dev user utility"""
    async for db in get_session():
        # Use the standardized dev user utility
        user_id = await ensure_dev_user_exists(db)
        
        # Get user info for logging
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user:
            print(f"Using existing dev user: {user.email} (ID: {user.id})")
        else:
            print(f"Created dev user with ID: {user_id}")
            
        return user_id


async def insert_agent_output(
    task_id: int,
    variation_id: int,
    output_type: str,
    content_data: dict
) -> None:
    """Insert a structured agent output entry."""
    async for db in get_session():
        output = TaskOutput(
            task_id=task_id,
            variation_id=variation_id,
            content=json.dumps(content_data),
            output_type=output_type,
            timestamp=datetime.utcnow()
        )
        db.add(output)
        await db.commit()
        break


async def create_task_1_data():
    """Create data for task 1: Make hello world label ominous"""
    user_id = await get_or_create_test_user()

    # Create task entry
    task_id = None
    async for db in get_session():
        # Check if task already exists
        result = await db.execute(select(Task).where(Task.id == 1))
        existing_task = result.scalar_one_or_none()

        if not existing_task:
            task = Task(
                id=1,
                github_url="https://github.com/aideator/helloworld",
                prompt="Make hello world label ominous",
                agent_mode="claude-cli",
                variations=3,
                status=TaskStatus.COMPLETED,
                user_id=user_id,
                created_at=datetime.utcnow() - timedelta(hours=8, minutes=15),
                completed_at=datetime.utcnow() - timedelta(hours=8, minutes=10),
                internal_run_id="task-1-mock"
            )
            db.add(task)
            await db.commit()
            await db.refresh(task)
            task_id = task.id
            print(f"Created task: {task_id}")
        else:
            task_id = existing_task.id
            print(f"Task {task_id} already exists, updating outputs only")
        break

    # Create agent outputs for each variation
    variations_data = [
        {
            "id": 0,
            "summary": "Updated the project description to read 'An ominous Hello World for Python,' making the greeting label more foreboding.",
            "files": [
                {
                    "name": "README.md",
                    "additions": 1,
                    "deletions": 1,
                    "diff": [
                        {"type": "normal", "oldLine": 1, "newLine": 1, "content": "# helloworld"},
                        {"type": "del", "oldLine": 2, "newLine": None, "content": "- Hello World for Python"},
                        {"type": "add", "oldLine": None, "newLine": 2, "content": "+ An ominous Hello World for Python"}
                    ]
                }
            ]
        },
        {
            "id": 1,
            "summary": "A slightly different take, using 'Greetings, mortal' for a more dramatic flair.",
            "files": [
                {
                    "name": "README.md",
                    "additions": 1,
                    "deletions": 1,
                    "diff": [
                        {"type": "normal", "oldLine": 1, "newLine": 1, "content": "# helloworld"},
                        {"type": "del", "oldLine": 2, "newLine": None, "content": "- Hello World for Python"},
                        {"type": "add", "oldLine": None, "newLine": 2, "content": "+ Greetings, mortal. Welcome to the Python world."}
                    ]
                }
            ]
        },
        {
            "id": 2,
            "summary": "A more subtle change, adding an ellipsis to create a sense of suspense.",
            "files": [
                {
                    "name": "README.md",
                    "additions": 1,
                    "deletions": 1,
                    "diff": [
                        {"type": "normal", "oldLine": 1, "newLine": 1, "content": "# helloworld"},
                        {"type": "del", "oldLine": 2, "newLine": None, "content": "- Hello World for Python"},
                        {"type": "add", "oldLine": None, "newLine": 2, "content": "+ Hello World for Python..."}
                    ]
                }
            ]
        }
    ]

    for variation in variations_data:
        variation_id = variation["id"]

        # Job summary
        await insert_agent_output(task_id, variation_id, "job_summary", {
            "summary": variation["summary"],
            "success": True,
            "variation_id": variation_id
        })

        # Diffs
        await insert_agent_output(task_id, variation_id, "diffs", {
            "file_changes": variation["files"],
            "variation_id": variation_id
        })

        # Metrics
        total_additions = sum(f["additions"] for f in variation["files"])
        total_deletions = sum(f["deletions"] for f in variation["files"])
        await insert_agent_output(task_id, variation_id, "metrics", {
            "additions": total_additions,
            "deletions": total_deletions,
            "files_changed": len(variation["files"]),
            "variation_id": variation_id
        })

        # Sample logs
        await insert_agent_output(task_id, variation_id, "logging", {
            "level": "INFO",
            "message": f"[Variation {variation_id}] Analyzing task: 'make hello world label ominous'",
            "variation_id": variation_id
        })

        await insert_agent_output(task_id, variation_id, "logging", {
            "level": "INFO",
            "message": f"[Variation {variation_id}] Changes applied successfully to README.md",
            "variation_id": variation_id
        })

    print("Created outputs for task 1 with 3 variations")


async def create_task_2_data():
    """Create data for task 2: Make hello world message cheerier"""
    user_id = await get_or_create_test_user()

    # Create task entry
    task_id = None
    async for db in get_session():
        # Check if task already exists
        result = await db.execute(select(Task).where(Task.id == 2))
        existing_task = result.scalar_one_or_none()

        if not existing_task:
            task = Task(
                id=2,
                github_url="https://github.com/aideator/helloworld",
                prompt="Make hello world message cheerier",
                agent_mode="claude-cli",
                variations=3,
                status=TaskStatus.COMPLETED,
                user_id=user_id,
                created_at=datetime.utcnow() - timedelta(hours=7, minutes=29),
                completed_at=datetime.utcnow() - timedelta(hours=7, minutes=25),
                internal_run_id="task-2-mock"
            )
            db.add(task)
            await db.commit()
            await db.refresh(task)
            task_id = task.id
            print(f"Created task: {task_id}")
        else:
            task_id = existing_task.id
            print(f"Task {task_id} already exists, updating outputs only")
        break

    # Create agent outputs for each variation - matches updated mock data
    variations_data = [
        {
            "id": 0,
            "summary": "Added a cheerful greeting with exclamation marks and emojis.",
            "files": [
                {
                    "name": "README.md",
                    "additions": 3,
                    "deletions": 3,
                    "diff": [
                        {"type": "normal", "oldLine": 1, "newLine": 1, "content": "# helloworld"},
                        {"type": "del", "oldLine": 2, "newLine": None, "content": "- Hello World for Python"},
                        {"type": "add", "oldLine": None, "newLine": 2, "content": "+ Hello World for Python! 🎉✨"},
                        {"type": "normal", "oldLine": 3, "newLine": 3, "content": ""},
                        {"type": "add", "oldLine": None, "newLine": 4, "content": "+ Welcome to the most cheerful Python project!"}
                    ]
                }
            ]
        },
        {
            "id": 1,
            "summary": "Made it even more cheerful with rainbow colors and celebration.",
            "files": [
                {
                    "name": "README.md",
                    "additions": 4,
                    "deletions": 2,
                    "diff": [
                        {"type": "normal", "oldLine": 1, "newLine": 1, "content": "# helloworld"},
                        {"type": "del", "oldLine": 2, "newLine": None, "content": "- Hello World for Python"},
                        {"type": "add", "oldLine": None, "newLine": 2, "content": "+ 🌈 SUPER HAPPY Hello World for Python! 🌈"},
                        {"type": "normal", "oldLine": 3, "newLine": 3, "content": ""},
                        {"type": "add", "oldLine": None, "newLine": 4, "content": "+ 🎊 The most joyful Python experience ever! 🎊"},
                        {"type": "add", "oldLine": None, "newLine": 5, "content": "+ Let's code with happiness! 😊💖"}
                    ]
                }
            ]
        },
        {
            "id": 2,
            "summary": "Toned it down to a warm, friendly welcome message.",
            "files": [
                {
                    "name": "README.md",
                    "additions": 2,
                    "deletions": 3,
                    "diff": [
                        {"type": "normal", "oldLine": 1, "newLine": 1, "content": "# helloworld"},
                        {"type": "del", "oldLine": 2, "newLine": None, "content": "- Hello World for Python"},
                        {"type": "add", "oldLine": None, "newLine": 2, "content": "+ A warm Hello World for Python 😊"},
                        {"type": "normal", "oldLine": 3, "newLine": 3, "content": ""},
                        {"type": "add", "oldLine": None, "newLine": 4, "content": "+ Hope you enjoy your Python journey!"}
                    ]
                }
            ]
        }
    ]

    for variation in variations_data:
        variation_id = variation["id"]

        # Job summary
        await insert_agent_output(task_id, variation_id, "job_summary", {
            "summary": variation["summary"],
            "success": True,
            "variation_id": variation_id
        })

        # Diffs
        await insert_agent_output(task_id, variation_id, "diffs", {
            "file_changes": variation["files"],
            "variation_id": variation_id
        })

        # Metrics
        total_additions = sum(f["additions"] for f in variation["files"])
        total_deletions = sum(f["deletions"] for f in variation["files"])
        await insert_agent_output(task_id, variation_id, "metrics", {
            "additions": total_additions,
            "deletions": total_deletions,
            "files_changed": len(variation["files"]),
            "variation_id": variation_id
        })

        # Sample logs
        await insert_agent_output(task_id, variation_id, "logging", {
            "level": "INFO",
            "message": f"[Variation {variation_id}] Analyzing task: 'make hello world message cheerier'",
            "variation_id": variation_id
        })

        await insert_agent_output(task_id, variation_id, "logging", {
            "level": "INFO",
            "message": f"[Variation {variation_id}] Applied cheerful changes to README.md",
            "variation_id": variation_id
        })

    print("Created outputs for task 2 with 3 variations")


async def create_other_tasks_data():
    """Create data for other tasks from the original mock data"""
    user_id = await get_or_create_test_user()

    other_tasks = [
        {
            "id": "3",
            "title": "Update hello world message",
            "github_url": "https://github.com/aideator/helloworld",
            "status": TaskStatus.PENDING,
            "variations": 1,
            "created_at": datetime.utcnow() - timedelta(days=3)
        },
        {
            "id": "4",
            "title": "Update hello world message",
            "github_url": "https://github.com/aideator/helloworld",
            "status": TaskStatus.FAILED,
            "variations": 1,
            "created_at": datetime.utcnow() - timedelta(days=4)
        },
        {
            "id": "5",
            "title": "Complete v2 UI functionality",
            "github_url": "https://github.com/heyalchang/dev-runner",
            "status": TaskStatus.COMPLETED,
            "variations": 3,
            "created_at": datetime.utcnow() - timedelta(days=5)
        }
    ]

    async for db in get_session():
        for task_data in other_tasks:
            # Check if task already exists
            result = await db.execute(select(Task).where(Task.id == int(task_data["id"])))
            existing_task = result.scalar_one_or_none()

            if not existing_task:
                task = Task(
                    id=int(task_data["id"]),
                    user_id=user_id,
                    github_url=task_data["github_url"],
                    prompt=task_data["title"],
                    variations=task_data["variations"],
                    status=task_data["status"],
                    created_at=task_data["created_at"],
                    internal_run_id=f"task-{task_data['id']}-mock"
                )
                db.add(task)
                print(f"Created task: {task_data['id']}")
            else:
                print(f"Task {task_data['id']} already exists")
        await db.commit()
        break


async def fix_task_sequence():
    """Fix the task ID sequence after inserting mock data with explicit IDs"""
    async for db in get_session():
        try:
            # Get the max task ID and set the sequence to start from the next value
            result = await db.execute(select(Task.id).order_by(Task.id.desc()).limit(1))
            max_id = result.scalar_one_or_none()
            
            if max_id:
                # Set the sequence to start from the next value using raw SQL
                from sqlalchemy import text
                await db.execute(text(f"SELECT setval('tasks_id_seq', {max_id})"))
                await db.commit()
                print(f"✅ Fixed task sequence: next ID will be {max_id + 1}")
            else:
                print("⚠️ No tasks found, sequence unchanged")
        except Exception as e:
            print(f"❌ Error fixing sequence: {e}")
            raise
        break


async def main():
    """Main function to create all mock task data"""
    print("🗄️ Creating mock task data in database...")

    try:
        await create_task_1_data()
        await create_task_2_data()
        await create_other_tasks_data()
        
        # Fix the sequence after creating tasks with explicit IDs
        await fix_task_sequence()

        print("✅ Successfully created all mock task data!")
        print("\n📋 Created tasks:")
        print("  - task-1: Make hello world label ominous (3 variations)")
        print("  - task-2: Make hello world message cheerier (3 variations)")
        print("  - task-3: Update hello world message (open)")
        print("  - task-4: Update hello world message (failed)")
        print("  - task-5: Complete v2 UI functionality (completed)")

    except Exception as e:
        print(f"❌ Error creating mock data: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
