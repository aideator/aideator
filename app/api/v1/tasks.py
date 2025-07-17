"""
Tasks API - Separate from runs for task monitoring workflow.

This API handles the task monitoring side of the architecture:
- List tasks for main page
- Get task details and progress 
- Read agent outputs from SQL

Enhanced to support frontend mock data structure replacement.
"""

import asyncio # Added for create_task
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.dependencies import CurrentUser, OptionalCurrentUser, get_orchestrator # get_orchestrator added
from app.core.logging import get_logger
from app.models.task import Task, TaskOutput, TaskStatus
from app.schemas.tasks import ( # Modified import
    TaskListItem,
    TaskListResponse,
    CreateTaskRequest,
    CreateTaskResponse,
)
from app.services.agent_orchestrator import AgentOrchestrator # New import

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=CreateTaskResponse,
    summary="Create a new task",
    description="Submit a new repository-analysis task and enqueue agent variations.",
)
async def create_task(
    request: CreateTaskRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session),
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
) -> CreateTaskResponse:
    """Insert Task row ➜ trigger AgentOrchestrator ➜ return polling URLs."""
    # Derive variation count
    variations = request.variations or len(request.model_names)

    # Insert Task row
    new_task = Task(
        github_url=request.github_url,
        prompt=request.prompt,
        agent_mode=request.agent_mode or "claude-cli",
        variations=variations,
        model_configs=[{"model": m} for m in request.model_names],
        status=TaskStatus.PENDING,
        user_id=current_user.id if current_user else None,
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    # Build internal run_id to match Kubernetes job naming
    # This MUST match the job name pattern: task-{task_id}-{variation_id}
    # For now, store just the base pattern - agents will append variation_id
    run_id = f"task-{new_task.id}"
    new_task.internal_run_id = run_id
    await db.commit()

    # Fire-and-forget orchestration (no await to avoid blocking request)
    # NOTE: Do not pass HTTP request session to background tasks!
    asyncio.create_task(
        orchestrator.execute_variations(
            task_id=new_task.id,
            run_id=run_id,
            repo_url=request.github_url,
            prompt=request.prompt,
            variations=variations,
            agent_mode=request.agent_mode,
            db_session=None,  # Background task creates its own session
        )
    )

    base_url = "/api/v1/tasks"
    return CreateTaskResponse(
        task_id=new_task.id,
        # WebSocket streaming removed - using HTTP polling instead
        polling_url=f"{base_url}/{new_task.id}/outputs",
        status="pending",
    )


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
            TaskOutput.output_type == "metrics",
        )
    )
    metrics_outputs = result.scalars().all()

    total_additions = 0
    total_deletions = 0

    for output in metrics_outputs:
        data = parse_agent_output_content(output.content)
        total_additions += data.get("additions", 0)
        total_deletions += data.get("deletions", 0)

    return {
        "additions": total_additions,
        "deletions": total_deletions
    }


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    current_user: OptionalCurrentUser,
    limit: int = Query(default=10, le=50),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_session),
) -> TaskListResponse:
    """Get list of tasks for the main page (reads from tasks table)."""

    # In dev mode, always show all tasks. In production, filter by user.
    from app.core.config import get_settings
    settings = get_settings()
    
    # Show all tasks in development mode or if no user
    if not current_user or settings.debug or settings.environment == "development":
        tasks_query = (
            select(Task)
            .where(Task.archived == False)  # Filter out archived tasks
            .order_by(desc(Task.created_at))
            .offset(offset)
            .limit(limit)
        )
        use_user_filter = False
    else:
        # Production mode - filter by user
        tasks_query = (
            select(Task)
            .where(Task.user_id == current_user.id)
            .where(Task.archived == False)  # Filter out archived tasks
            .order_by(desc(Task.created_at))
            .offset(offset)
            .limit(limit)
        )
        use_user_filter = True

    result = await db.execute(tasks_query)
    tasks_rows = result.scalars().all()

    # Get total count for pagination
    if use_user_filter:
        count_query = select(func.count(Task.id)).where(Task.user_id == current_user.id).where(Task.archived == False)
    else:
        count_query = select(func.count(Task.id)).where(Task.archived == False)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Convert tasks to task list items
    tasks = []
    for task_row in tasks_rows:
        # Generate title from prompt (truncate if needed)
        title = task_row.prompt or "Untitled Task"
        if len(title) > 50:
            title = title[:47] + "..."

        # Map Task.status enum to frontend string
        status_mapping = {
            TaskStatus.PENDING: "Open",
            TaskStatus.RUNNING: "Open",
            TaskStatus.COMPLETED: "Completed",
            TaskStatus.FAILED: "Failed",
            TaskStatus.CANCELLED: "Failed",
        }
        frontend_status = status_mapping.get(task_row.status, "Open")

        # Generate details string with timestamp and repository info
        details = f"{task_row.created_at.strftime('%I:%M %p')} · "
        if task_row.github_url:
            # Extract repo name from URL for display
            repo_name = task_row.github_url.split("/")[-1] if "/" in task_row.github_url else task_row.github_url
            details += f"aideator/{repo_name}"
        else:
            details += "Chat Mode"

        # Get number of variations from the run
        versions = task_row.variations if task_row.variations else 1

        # Get aggregated metrics for completed tasks
        additions = None
        deletions = None
        if task_row.status == TaskStatus.COMPLETED:
            metrics = await get_task_metrics(db, task_row.id)
            additions = metrics["additions"]
            deletions = metrics["deletions"]

        task_item = TaskListItem(
            id=str(task_row.id),  # Convert to string for frontend compatibility
            title=title,
            details=details,
            status=frontend_status,
            versions=versions,
            additions=additions,
            deletions=deletions,
            archived=task_row.archived
        )
        tasks.append(task_item)

    return TaskListResponse(tasks=tasks, total=total, has_more=(offset + len(tasks)) < total)


@router.get("/archived", response_model=TaskListResponse)
async def list_archived_tasks(
    current_user: OptionalCurrentUser,
    limit: int = Query(default=10, le=50),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_session),
) -> TaskListResponse:
    """Get list of archived tasks."""

    # In dev mode, always show all tasks. In production, filter by user.
    from app.core.config import get_settings
    settings = get_settings()
    
    # Show all archived tasks in development mode or if no user
    if not current_user or settings.debug or settings.environment == "development":
        tasks_query = (
            select(Task)
            .where(Task.archived == True)  # Only archived tasks
            .order_by(desc(Task.created_at))
            .offset(offset)
            .limit(limit)
        )
        use_user_filter = False
    else:
        # Production mode - filter by user
        tasks_query = (
            select(Task)
            .where(Task.user_id == current_user.id)
            .where(Task.archived == True)  # Only archived tasks
            .order_by(desc(Task.created_at))
            .offset(offset)
            .limit(limit)
        )
        use_user_filter = True

    result = await db.execute(tasks_query)
    tasks_rows = result.scalars().all()

    # Get total count for pagination
    if use_user_filter:
        count_query = select(func.count(Task.id)).where(Task.user_id == current_user.id).where(Task.archived == True)
    else:
        count_query = select(func.count(Task.id)).where(Task.archived == True)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Convert tasks to task list items
    tasks = []
    for task_row in tasks_rows:
        # Generate title from prompt (truncate if needed)
        title = task_row.prompt or "Untitled Task"
        if len(title) > 50:
            title = title[:47] + "..."

        # Map Task.status enum to frontend string
        status_mapping = {
            TaskStatus.PENDING: "Open",
            TaskStatus.RUNNING: "Open",
            TaskStatus.COMPLETED: "Completed",
            TaskStatus.FAILED: "Failed",
            TaskStatus.CANCELLED: "Failed",
        }
        frontend_status = status_mapping.get(task_row.status, "Open")

        # Generate details string with timestamp and repository info
        details = f"{task_row.created_at.strftime('%I:%M %p')} · "
        if task_row.github_url:
            # Extract repo name from URL for display
            repo_name = task_row.github_url.split("/")[-1] if "/" in task_row.github_url else task_row.github_url
            details += f"aideator/{repo_name}"
        else:
            details += "Chat Mode"

        # Get number of variations from the run
        versions = task_row.variations if task_row.variations else 1

        # Get aggregated metrics for completed tasks
        additions = None
        deletions = None
        if task_row.status == TaskStatus.COMPLETED:
            metrics = await get_task_metrics(db, task_row.id)
            additions = metrics["additions"]
            deletions = metrics["deletions"]

        task_item = TaskListItem(
            id=str(task_row.id),  # Convert to string for frontend compatibility
            title=title,
            details=details,
            status=frontend_status,
            versions=versions,
            additions=additions,
            deletions=deletions,
            archived=task_row.archived
        )
        tasks.append(task_item)

    return TaskListResponse(tasks=tasks, total=total, has_more=(offset + len(tasks)) < total)


@router.get("/{task_id}")
async def get_task_details(
    task_id: int,  # Now takes integer task_id
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session),
):
    """
    Get detailed information about a specific task.
    Returns data in frontend-expected format with taskDetails structure.
    """
    # Get the task
    from app.core.config import get_settings
    settings = get_settings()
    
    query = select(Task).where(Task.id == task_id)
    # In dev mode, don't filter by user. In production, filter by user.
    if not (settings.debug or settings.environment == "development"):
        query = query.where(Task.user_id == current_user.id)
    
    result = await db.execute(query)
    task_row = result.scalar_one_or_none()

    if task_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

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
            "id": variation_id + 1,  # Convert 0-indexed to 1-indexed for display
            "summary": version_data["summary"],
            "files": version_data["files"]
        })

    # Generate details string
    details = f"{task_row.created_at.strftime('%I:%M %p')} · "
    if task_row.github_url:
        details += task_row.github_url.replace("https://github.com/", "")
    else:
        details += "Chat Mode"

    # Map status
    status_mapping = {
        TaskStatus.PENDING: "Open",
        TaskStatus.RUNNING: "Open",
        TaskStatus.COMPLETED: "Completed",
        TaskStatus.FAILED: "Failed",
        TaskStatus.CANCELLED: "Failed",
    }
    frontend_status = status_mapping.get(task_row.status, "Open")

    return {
        "id": task_row.id,
        "title": task_row.prompt,
        "details": details,
        "status": frontend_status,
        "versions": task_row.variations,
        "taskDetails": {
            "versions": versions
        }
    }


@router.get("/{task_id}/outputs")
async def get_task_outputs(
    task_id: int,  # Now takes integer task_id
    current_user: CurrentUser,
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
    from app.core.config import get_settings
    settings = get_settings()
    
    query = select(Task).where(Task.id == task_id)
    # In dev mode, don't filter by user. In production, filter by user.
    if not (settings.debug or settings.environment == "development"):
        query = query.where(Task.user_id == current_user.id)

    result = await db.execute(query)
    task_row = result.scalar_one_or_none()

    if not task_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Build query for outputs
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


@router.get("/{task_id}/variations/{variation_id}/outputs")
async def get_variation_outputs(
    task_id: int,  # Now takes integer task_id
    variation_id: int,
    current_user: CurrentUser,
    since: datetime | None = Query(
        None, description="ISO timestamp to get outputs after"
    ),
    output_type: str | None = Query(None, description="Filter by output type"),
    limit: int = Query(100, le=1000, description="Maximum number of outputs to return"),
    db: AsyncSession = Depends(get_session),
) -> list[dict]:
    """
    Get agent outputs for a specific variation of a task.

    Useful for variation comparison in the task detail page.
    """
    # Verify task exists and user has access
    from app.core.config import get_settings
    settings = get_settings()
    
    query = select(Task).where(Task.id == task_id)
    # In dev mode, don't filter by user. In production, filter by user.
    if not (settings.debug or settings.environment == "development"):
        query = query.where(Task.user_id == current_user.id)

    result = await db.execute(query)
    task_row = result.scalar_one_or_none()

    if not task_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Verify variation_id is valid
    if variation_id < 0 or variation_id >= task_row.variations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid variation ID. Must be between 0 and {task_row.variations - 1}",
        )

    # Build query for outputs
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
            "task_id": output.task_id,  # Changed from run_id to task_id
            "variation_id": output.variation_id,
            "content": output.content,
            "timestamp": output.timestamp.isoformat(),
            "output_type": output.output_type,
        }
        for output in outputs
    ]


@router.patch("/{task_id}/archive")
async def archive_task(
    task_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Archive a task."""
    # Get the task
    from app.core.config import get_settings
    settings = get_settings()
    
    query = select(Task).where(Task.id == task_id)
    # In dev mode, don't filter by user. In production, filter by user.
    if not (settings.debug or settings.environment == "development"):
        query = query.where(Task.user_id == current_user.id)
    
    result = await db.execute(query)
    task_row = result.scalar_one_or_none()
    
    if not task_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    # Archive the task
    task_row.archived = True
    task_row.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Task archived successfully"}


@router.patch("/{task_id}/unarchive")
async def unarchive_task(
    task_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Unarchive a task."""
    # Get the task
    from app.core.config import get_settings
    settings = get_settings()
    
    query = select(Task).where(Task.id == task_id)
    # In dev mode, don't filter by user. In production, filter by user.
    if not (settings.debug or settings.environment == "development"):
        query = query.where(Task.user_id == current_user.id)
    
    result = await db.execute(query)
    task_row = result.scalar_one_or_none()
    
    if not task_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    # Unarchive the task
    task_row.archived = False
    task_row.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Task unarchived successfully"}


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Delete a task permanently."""
    try:
        # Get the task
        from app.core.config import get_settings
        settings = get_settings()
        
        query = select(Task).where(Task.id == task_id)
        # In dev mode, don't filter by user. In production, filter by user.
        if current_user and not (settings.debug or settings.environment == "development"):
            query = query.where(Task.user_id == current_user.id)
        
        result = await db.execute(query)
        task_row = result.scalar_one_or_none()
        
        if not task_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        
        logger.info(f"Deleting task {task_id} and its outputs")
        
        # Delete all task outputs first (more efficient bulk delete)
        from sqlalchemy import delete as sql_delete
        
        # Delete all outputs for this task in one query
        await db.execute(
            sql_delete(TaskOutput).where(TaskOutput.task_id == task_id)
        )
        
        # Delete the task
        await db.delete(task_row)
        
        # Commit all changes in a single transaction
        await db.commit()
        
        logger.info(f"Successfully deleted task {task_id}")
        return {"message": "Task deleted successfully"}
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        await db.rollback()
        raise
    except Exception as e:
        # Rollback on any other error
        await db.rollback()
        logger.error(f"Failed to delete task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )