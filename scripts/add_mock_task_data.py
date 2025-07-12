#!/usr/bin/env python3
"""
Generate mock task data in database to replace frontend static data.
This script creates realistic agent_outputs entries that match the original mock data structure.
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
from app.models.run import Run, RunStatus, AgentOutput
from app.models.user import User


async def get_or_create_test_user() -> str:
    """Get or create a test user for the mock data - uses same user as development middleware"""
    async for db in get_session():
        # Check if test user exists (same email as development middleware)
        result = await db.execute(select(User).where(User.email == "test@aideator.local"))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"Using existing dev user: {existing_user.email} (ID: {existing_user.id})")
            return existing_user.id
        else:
            # This should not happen if development middleware is working
            print("WARNING: Development user not found, creating one...")
            import secrets
            from app.core.auth import get_password_hash
            user = User(
                id=f"user_test_{secrets.token_urlsafe(12)}",
                email="test@aideator.local",
                hashed_password=get_password_hash("testpass123"),
                full_name="Test User",
                company="AIdeator Development",
                is_active=True,
                is_superuser=True,
                created_at=datetime.utcnow()
            )
            db.add(user)
            await db.commit()
            print(f"Created test user: {user.email} (ID: {user.id})")
            return user.id


async def insert_agent_output(
    run_id: str, 
    variation_id: int, 
    output_type: str, 
    content_data: dict
) -> None:
    """Insert a structured agent output entry."""
    async for db in get_session():
        output = AgentOutput(
            run_id=run_id,
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
    run_id = "1"
    user_id = await get_or_create_test_user()
    
    # Create run entry
    async for db in get_session():
        # Check if run already exists
        result = await db.execute(select(Run).where(Run.id == run_id))
        existing_run = result.scalar_one_or_none()
        
        if not existing_run:
            run = Run(
                id=run_id,
                user_id=user_id,
                github_url="https://github.com/aideator/helloworld",
                prompt="Make hello world label ominous",
                variations=3,
                status=RunStatus.COMPLETED,
                task_status="completed",
                created_at=datetime.utcnow() - timedelta(hours=8, minutes=15),
                completed_at=datetime.utcnow() - timedelta(hours=8, minutes=10)
            )
            db.add(run)
            await db.commit()
            print(f"Created run: {run_id}")
        else:
            print(f"Run {run_id} already exists, updating outputs only")
        break

    # Create agent outputs for each variation
    variations_data = [
        {
            "id": 1,
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
            "id": 2,
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
            "id": 3,
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
        await insert_agent_output(run_id, variation_id, "job_summary", {
            "summary": variation["summary"],
            "success": True,
            "variation_id": variation_id
        })
        
        # Diffs
        await insert_agent_output(run_id, variation_id, "diffs", {
            "file_changes": variation["files"],
            "variation_id": variation_id
        })
        
        # Metrics  
        total_additions = sum(f["additions"] for f in variation["files"])
        total_deletions = sum(f["deletions"] for f in variation["files"])
        await insert_agent_output(run_id, variation_id, "metrics", {
            "additions": total_additions,
            "deletions": total_deletions,
            "files_changed": len(variation["files"]),
            "variation_id": variation_id
        })
        
        # Sample logs
        await insert_agent_output(run_id, variation_id, "logging", {
            "level": "INFO",
            "message": f"[Variation {variation_id}] Analyzing task: 'make hello world label ominous'",
            "variation_id": variation_id
        })
        
        await insert_agent_output(run_id, variation_id, "logging", {
            "level": "INFO", 
            "message": f"[Variation {variation_id}] Changes applied successfully to README.md",
            "variation_id": variation_id
        })

    print(f"Created outputs for task 1 with 3 variations")


async def create_task_2_data():
    """Create data for task 2: Make hello world message cheerier"""
    run_id = "2"
    user_id = await get_or_create_test_user()
    
    # Create run entry
    async for db in get_session():
        # Check if run already exists
        result = await db.execute(select(Run).where(Run.id == run_id))
        existing_run = result.scalar_one_or_none()
        
        if not existing_run:
            run = Run(
                id=run_id,
                user_id=user_id,
                github_url="https://github.com/aideator/helloworld",
                prompt="Make hello world message cheerier",
                variations=3,
                status=RunStatus.COMPLETED,
                task_status="completed",
                created_at=datetime.utcnow() - timedelta(hours=7, minutes=29),
                completed_at=datetime.utcnow() - timedelta(hours=7, minutes=25)
            )
            db.add(run)
            await db.commit()
            print(f"Created run: {run_id}")
        else:
            print(f"Run {run_id} already exists, updating outputs only")
        break

    # Create agent outputs for each variation - matches updated mock data
    variations_data = [
        {
            "id": 1,
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
            "id": 2,
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
            "id": 3,
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
        await insert_agent_output(run_id, variation_id, "job_summary", {
            "summary": variation["summary"],
            "success": True,
            "variation_id": variation_id
        })
        
        # Diffs
        await insert_agent_output(run_id, variation_id, "diffs", {
            "file_changes": variation["files"],
            "variation_id": variation_id
        })
        
        # Metrics  
        total_additions = sum(f["additions"] for f in variation["files"])
        total_deletions = sum(f["deletions"] for f in variation["files"])
        await insert_agent_output(run_id, variation_id, "metrics", {
            "additions": total_additions,
            "deletions": total_deletions,
            "files_changed": len(variation["files"]),
            "variation_id": variation_id
        })
        
        # Sample logs
        await insert_agent_output(run_id, variation_id, "logging", {
            "level": "INFO",
            "message": f"[Variation {variation_id}] Analyzing task: 'make hello world message cheerier'",
            "variation_id": variation_id
        })
        
        await insert_agent_output(run_id, variation_id, "logging", {
            "level": "INFO",
            "message": f"[Variation {variation_id}] Applied cheerful changes to README.md",
            "variation_id": variation_id
        })

    print(f"Created outputs for task 2 with 3 variations")


async def create_other_tasks_data():
    """Create data for other tasks from the original mock data"""
    user_id = await get_or_create_test_user()
    
    other_tasks = [
        {
            "id": "3",
            "title": "Update hello world message", 
            "github_url": "https://github.com/aideator/helloworld",
            "status": RunStatus.PENDING,
            "task_status": "open",
            "variations": 1,
            "created_at": datetime.utcnow() - timedelta(days=3)
        },
        {
            "id": "4",
            "title": "Update hello world message",
            "github_url": "https://github.com/aideator/helloworld", 
            "status": RunStatus.FAILED,
            "task_status": "failed",
            "variations": 1,
            "created_at": datetime.utcnow() - timedelta(days=4)
        },
        {
            "id": "5",
            "title": "Complete v2 UI functionality",
            "github_url": "https://github.com/heyalchang/dev-runner",
            "status": RunStatus.COMPLETED,
            "task_status": "completed", 
            "variations": 3,
            "created_at": datetime.utcnow() - timedelta(days=5)
        }
    ]
    
    async for db in get_session():
        for task_data in other_tasks:
            # Check if run already exists
            result = await db.execute(select(Run).where(Run.id == task_data["id"]))
            existing_run = result.scalar_one_or_none()
            
            if not existing_run:
                run = Run(
                    id=task_data["id"],
                    user_id=user_id,
                    github_url=task_data["github_url"],
                    prompt=task_data["title"],
                    variations=task_data["variations"],
                    status=task_data["status"],
                    task_status=task_data["task_status"],
                    created_at=task_data["created_at"]
                )
                db.add(run)
                print(f"Created run: {task_data['id']}")
            else:
                print(f"Run {task_data['id']} already exists")
        await db.commit()
        break


async def main():
    """Main function to create all mock task data"""
    print("🗄️ Creating mock task data in database...")
    
    try:
        await create_task_1_data()
        await create_task_2_data() 
        await create_other_tasks_data()
        
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