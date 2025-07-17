#!/usr/bin/env python3
"""
Simplified mock task data generator for the new unified architecture.
Creates realistic task data without user management complexity.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List

# Add the project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select

from app.core.database import engine


async def create_mock_task(
    task_id: int,
    github_url: str,
    prompt: str,
    status: str = "completed",
    variations: int = 3,
    hours_ago: int = 1
) -> None:
    """Create a mock task with outputs in the simplified schema."""
    
    with Session(engine) as session:
        # Create task entry (simplified - no user_id)
        task = {
            "id": task_id,
            "github_url": github_url,
            "prompt": prompt,
            "status": status,
            "variations": variations,
            "created_at": datetime.utcnow() - timedelta(hours=hours_ago),
            "completed_at": datetime.utcnow() - timedelta(hours=hours_ago - 0.5) if status == "completed" else None,
            "outputs": []  # Will store all outputs as JSON
        }
        
        # Add to tasks table (when simplified schema is ready)
        # session.add(Task(**task))
        # session.commit()
        
        print(f"Created mock task {task_id}: {prompt[:50]}...")


async def add_mock_outputs(task_id: int, outputs: List[Dict[str, Any]]) -> None:
    """Add mock outputs to a task."""
    
    with Session(engine) as session:
        # In simplified architecture, outputs might be JSON in tasks table
        # or a separate simplified outputs table
        for output in outputs:
            output_data = {
                "task_id": task_id,
                "variation_id": output.get("variation_id", 0),
                "content": output.get("content", ""),
                "output_type": output.get("output_type", "job_data"),
                "timestamp": datetime.utcnow()
            }
            # session.add(TaskOutput(**output_data))
            print(f"  Added {output_data['output_type']} output for variation {output_data['variation_id']}")
        
        # session.commit()


async def create_sample_data():
    """Create sample tasks with realistic outputs."""
    
    # Task 1: Simple refactoring
    await create_mock_task(
        task_id=1,
        github_url="https://github.com/fastapi/fastapi",
        prompt="Refactor authentication middleware for clarity",
        status="completed",
        variations=3,
        hours_ago=2
    )
    
    outputs_task_1 = [
        # Variation 0 - Claude
        {
            "variation_id": 0,
            "output_type": "job_data",
            "content": "🔧 Starting refactoring analysis..."
        },
        {
            "variation_id": 0,
            "output_type": "job_data", 
            "content": "📊 Found 5 files with authentication logic"
        },
        {
            "variation_id": 0,
            "output_type": "summary",
            "content": json.dumps({
                "summary": "Refactored auth middleware into separate concerns",
                "files_changed": 5,
                "additions": 120,
                "deletions": 85
            })
        },
        
        # Variation 1 - GPT-4
        {
            "variation_id": 1,
            "output_type": "job_data",
            "content": "🤖 Analyzing authentication patterns..."
        },
        {
            "variation_id": 1,
            "output_type": "job_data",
            "content": "✅ Identified 3 improvement areas"
        },
        {
            "variation_id": 1,
            "output_type": "summary",
            "content": json.dumps({
                "summary": "Consolidated auth logic into single module",
                "files_changed": 3,
                "additions": 95,
                "deletions": 110
            })
        },
        
        # Variation 2 - Gemini
        {
            "variation_id": 2,
            "output_type": "error",
            "content": "Rate limit exceeded"
        }
    ]
    
    await add_mock_outputs(1, outputs_task_1)
    
    # Task 2: Feature implementation
    await create_mock_task(
        task_id=2,
        github_url="https://github.com/user/myapp",
        prompt="Add rate limiting to API endpoints",
        status="running",
        variations=2,
        hours_ago=0.5
    )
    
    outputs_task_2 = [
        {
            "variation_id": 0,
            "output_type": "job_data",
            "content": "🚀 Implementing rate limiting middleware..."
        },
        {
            "variation_id": 0,
            "output_type": "job_data",
            "content": "📝 Creating configuration for rate limits"
        },
        {
            "variation_id": 1,
            "output_type": "job_data",
            "content": "🔍 Analyzing existing middleware stack..."
        }
    ]
    
    await add_mock_outputs(2, outputs_task_2)
    
    # Task 3: Code review
    await create_mock_task(
        task_id=3,
        github_url="https://github.com/django/django",
        prompt="Review and improve error handling in views",
        status="pending",
        variations=1,
        hours_ago=0.1
    )
    
    print("\n✅ Mock data creation complete!")
    print("\nCreated tasks:")
    print("  1. Refactor authentication (completed) - 3 variations")
    print("  2. Add rate limiting (running) - 2 variations")
    print("  3. Review error handling (pending) - 1 variation")


async def main():
    """Main entry point."""
    print("🗄️ Creating simplified mock task data...")
    print("⚠️  Note: This script is for the simplified architecture")
    print("    Update table names and schemas as needed\n")
    
    try:
        await create_sample_data()
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())