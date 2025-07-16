"""
Tasks API - Separate from runs for task monitoring workflow.

This API handles the task monitoring side of the architecture:
- List tasks for main page
- Get task details and progress 
- Read agent outputs from SQL

Enhanced to support frontend mock data structure replacement.
"""

import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.dependencies import CurrentUserAPIKey
from app.core.logging import get_logger
from app.models.task import Task, TaskOutput, TaskStatus
from app.schemas.tasks import TaskListItem, TaskListResponse, TaskCreate, TaskResponse, TaskOutputResponse

logger = get_logger(__name__)
router = APIRouter()


def parse_agent_output_content(content: str) -> dict[str, Any]:
    """Safely parse JSON content from agent outputs."""
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return {}


async def get_task_metrics(session: AsyncSession, task_id: int) -> dict[str, int]:
    """Get aggregated metrics across all variations for a task."""
    result = await session.execute(
        select(TaskOutput).where(
            TaskOutput.task_id == task_id,
            TaskOutput.output_type == "metrics"
        )
    )
    outputs = result.scalars().all()

    total_additions = 0
    total_deletions = 0

    for output in outputs:
        data = parse_agent_output_content(output.content)
        total_additions += data.get("additions", 0)
        total_deletions += data.get("deletions", 0)

    return {
        "additions": total_additions,
        "deletions": total_deletions
    }


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    current_user: CurrentUserAPIKey,
    limit: int = Query(default=10, le=50),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_session),
) -> TaskListResponse:
    """Get list of tasks for the main page (unified task model)."""

    # Query tasks for the current user, ordered by creation date (newest first)
    tasks_query = (
        select(Task)
        .where(Task.user_id == current_user.id)
        .order_by(desc(Task.created_at))
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(tasks_query)
    tasks_db = result.scalars().all()

    # Get total count for pagination
    count_query = select(func.count(Task.id)).where(Task.user_id == current_user.id)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Convert tasks to task list items
    tasks = []
    for task in tasks_db:
        # Generate title from prompt (truncate if needed)
        title = task.prompt or "Untitled Task"
        if len(title) > 50:
            title = title[:47] + "..."

        # Map TaskStatus to frontend status format
        status_mapping = {
            TaskStatus.PENDING: "Open",
            TaskStatus.RUNNING: "Open",
            TaskStatus.COMPLETED: "Completed",
            TaskStatus.FAILED: "Failed",
            TaskStatus.CANCELLED: "Failed"
        }
        frontend_status = status_mapping.get(task.status, "Open")

        # Generate details string with timestamp and repository info
        details = f"{task.created_at.strftime('%I:%M %p')} · "
        if task.github_url:
            # Extract repo name from URL for display
            repo_name = task.github_url.split("/")[-1] if "/" in task.github_url else task.github_url
            details += f"aideator/{repo_name}"
        else:
            details += "Chat Mode"

        # Get number of variations from the task
        versions = task.variations if task.variations else 1

        # Get aggregated metrics for completed tasks
        additions = None
        deletions = None
        if task.status == TaskStatus.COMPLETED:
            metrics = await get_task_metrics(db, task.id)
            additions = metrics["additions"]
            deletions = metrics["deletions"]

        task_item = TaskListItem(
            id=str(task.id),  # Convert to string for frontend compatibility
            title=title,
            details=details,
            status=frontend_status,
            versions=versions,
            additions=additions,
            deletions=deletions
        )
        tasks.append(task_item)

    return TaskListResponse(
        tasks=tasks,
        total=total,
        has_more=(offset + len(tasks)) < total
    )


@router.get("/{task_id}")
async def get_task_details(
    task_id: int,  # Now takes integer task_id
    current_user: CurrentUserAPIKey,
    db: AsyncSession = Depends(get_session),
):
    """
    Get detailed information about a specific task.
    Returns data in frontend-expected format with taskDetails structure.
    """
    # Get the task
    task_query = select(Task).where(Task.id == task_id).where(Task.user_id == current_user.id)
    task_result = await db.execute(task_query)
    task = task_result.scalar_one_or_none()
    
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    # Use unified Task data
    task_data = {
        'task_id': task.id,
        'github_url': task.github_url,
        'prompt': task.prompt,
        'variations': task.variations,
        'status': str(task.status),
        'task_status': str(task.status),
        'created_at': task.created_at,
        'updated_at': task.updated_at,
        'started_at': task.started_at,
        'completed_at': task.completed_at,
        'results': task.results,
        'error_message': task.error_message,
        'total_tokens_used': task.total_tokens_used,
        'total_cost_usd': task.total_cost_usd
    }

    # Get all outputs for this task
    outputs_result = await db.execute(
        select(TaskOutput).where(TaskOutput.task_id == task_id)
        .order_by(TaskOutput.variation_id, TaskOutput.timestamp)
    )
    outputs = outputs_result.scalars().all()

    # Group outputs by variation and type
    variations_data = {}
    for output in outputs:
        variation_id = output.variation_id
        if variation_id not in variations_data:
            variations_data[variation_id] = {
                "summary": "",
                "files": [],
                "logs": []
            }

        data = parse_agent_output_content(output.content)

        if output.output_type == "job_summary":
            variations_data[variation_id]["summary"] = data.get("summary", "")
        elif output.output_type == "diffs":
            variations_data[variation_id]["files"] = data.get("file_changes", [])
        elif output.output_type == "logging":
            variations_data[variation_id]["logs"].append({
                "level": data.get("level", "INFO"),
                "message": data.get("message", ""),
                "timestamp": output.timestamp.isoformat()
            })

    # Format for frontend taskDetails structure
    versions = []
    for variation_id in sorted(variations_data.keys()):
        version_data = variations_data[variation_id]
        versions.append({
            "id": variation_id,
            "summary": version_data["summary"],
            "files": version_data["files"]
        })

    # Generate details string
    details = f"{task_data['created_at'].strftime('%I:%M %p')} · "
    if task_data['github_url']:
        details += task_data['github_url'].replace("https://github.com/", "")
    else:
        details += "Chat Mode"

    # Map status
    status_mapping = {
        "pending": "Open",
        "running": "Open",
        "completed": "Completed",
        "failed": "Failed",
        "cancelled": "Failed"
    }
    frontend_status = status_mapping.get(task_data['task_status'], "Open")

    return {
        "id": task_data['task_id'],
        "title": task_data['prompt'],
        "details": details,
        "status": frontend_status,
        "versions": task_data['variations'],
        "taskDetails": {
            "versions": versions
        }
    }


@router.get("/{task_id}/outputs")
async def get_task_outputs(
    task_id: int,  # Now takes integer task_id
    current_user: CurrentUserAPIKey,
    since: datetime | None = Query(
        None, description="ISO timestamp to get outputs after"
    ),
    variation_id: int | None = Query(None, description="Filter by variation ID"),
    output_type: str | None = Query(None, description="Filter by output type"),
    limit: int = Query(100, le=1000, description="Maximum number of outputs to return"),
    db: AsyncSession = Depends(get_session),
) -> list[dict]:
    """
    Get agent outputs for a task.
    
    This is the main endpoint for task detail page to read agent progress.
    Frontend should poll this every 0.5 seconds with the last received timestamp.
    """
    # Verify task exists and user has access
    task_query = select(Task).where(Task.id == task_id)
    if current_user:
        task_query = task_query.where(Task.user_id == current_user.id)

    task_result = await db.execute(task_query)
    task = task_result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Query TaskOutput table
    outputs_query = select(TaskOutput).where(TaskOutput.task_id == task_id)
    
    # Apply filters
    if since:
        outputs_query = outputs_query.where(TaskOutput.timestamp > since)
    if variation_id is not None:
        outputs_query = outputs_query.where(TaskOutput.variation_id == variation_id)
    if output_type:
        outputs_query = outputs_query.where(TaskOutput.output_type == output_type)
    
    # Order by timestamp and limit
    outputs_query = outputs_query.order_by(TaskOutput.timestamp).limit(limit)
    
    # Execute query
    result = await db.execute(outputs_query)
    outputs = result.scalars().all()

    # Convert to response format
    return [
        {
            "id": output.id,
            "task_id": output.task_id,  # Changed from run_id to task_id
            "variation_id": output.variation_id,
            "content": output.content,
            "timestamp": output.timestamp.isoformat(),
            "output_type": output.output_type,
        }
        for output in outputs
    ]


@router.post("", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    current_user: CurrentUserAPIKey,
    db: AsyncSession = Depends(get_session),
) -> TaskResponse:
    """Create a new unified task."""
    
    # Extract model configurations from variants
    model_configs = [
        {
            "model_definition_id": variant.model_definition_id,
            "custom_params": variant.custom_params
        }
        for variant in task_data.model_variants
    ]
    
    # Create new task
    task = Task(
        github_url=task_data.github_url,
        prompt=task_data.prompt,
        agent_mode=task_data.agent_mode,
        variations=len(task_data.model_variants),
        model_configs=model_configs,
        status=TaskStatus.PENDING,
        user_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    return TaskResponse(
        id=task.id,
        github_url=task.github_url,
        prompt=task.prompt,
        agent_mode=task.agent_mode,
        status=task.status,
        variations=task.variations,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        results=task.results,
        task_metadata=task.task_metadata,
        total_tokens_used=task.total_tokens_used,
        total_cost_usd=task.total_cost_usd,
        error_message=task.error_message,
        polling_url=f"/api/v1/tasks/{task.id}/outputs",
        estimated_duration_seconds=300  # Default 5 minutes
    )


@router.get("/{task_id}/variations/{variation_id}/outputs")
async def get_variation_outputs(
    task_id: int,  # Now takes integer task_id
    variation_id: int,
    current_user: CurrentUserAPIKey,
    since: datetime | None = Query(
        None, description="ISO timestamp to get outputs after"
    ),
    limit: int = Query(100, le=1000, description="Maximum number of outputs to return"),
    db: AsyncSession = Depends(get_session),
) -> list[dict]:
    """
    Get agent outputs for a specific variation within a task.
    
    This endpoint allows filtering outputs by variation ID.
    """
    # Verify task exists and user has access
    task_query = select(Task).where(Task.id == task_id)
    if current_user:
        task_query = task_query.where(Task.user_id == current_user.id)

    task_result = await db.execute(task_query)
    task = task_result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    # Validate variation_id is within range
    if variation_id < 0 or variation_id >= task.variations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid variation ID. Must be between 0 and {task.variations - 1}",
        )

    # Query TaskOutput table
    outputs_query = select(TaskOutput).where(
        TaskOutput.task_id == task_id,
        TaskOutput.variation_id == variation_id
    )
    
    # Apply filters
    if since:
        outputs_query = outputs_query.where(TaskOutput.timestamp > since)
    if output_type:
        outputs_query = outputs_query.where(TaskOutput.output_type == output_type)
    
    # Order by timestamp and limit
    outputs_query = outputs_query.order_by(TaskOutput.timestamp).limit(limit)
    
    # Execute query
    result = await db.execute(outputs_query)
    outputs = result.scalars().all()

    # Convert to response format
    return [
        {
            "id": output.id,
            "task_id": output.task_id,
            "variation_id": output.variation_id,
            "content": output.content,
            "timestamp": output.timestamp.isoformat(),
            "output_type": output.output_type,
        }
        for output in outputs
    ]
