import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import get_settings
from app.core.database import get_session
from app.core.dependencies import CurrentUserAPIKey
from app.core.deps import get_orchestrator
from app.core.logging import get_logger
from app.models.run import AgentOutput, Run, RunStatus
# Removed session imports - no longer using sessions
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.runs import (
    CreateRunRequest,
    CreateRunResponse,
    RunDetails,
    RunListItem,
)
from app.schemas.tasks import TaskListResponse, TaskListItem
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.model_catalog import model_catalog

settings = get_settings()
logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "",
    response_model=CreateRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a new agent run",
    response_description="Run accepted for processing",
)
async def create_run(
    request: CreateRunRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUserAPIKey,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    db: AsyncSession = Depends(get_session),
) -> CreateRunResponse:
    """
    Create a new agent run that will spawn N containerized LLM agents.

    The run is processed asynchronously in the background using Kubernetes Jobs.
    """
    # 1.  Generate legacy string id (used in job names & Redis streams)
    run_id = f"run-{uuid.uuid4().hex}"
    
    # Removed session/turn ID generation - runs are standalone now

    # 2.  Insert Run row – we *do not* provide task_id (auto-increment)
    run = Run(
        run_id=run_id,
        github_url=str(request.github_url),
        prompt=request.prompt,
        variations=len(request.model_variants),
        agent_config={
            "model_variants": [v.model_dump() for v in request.model_variants],
            "use_claude_code": request.use_claude_code,
            "agent_mode": request.agent_mode,
        },
        user_id=current_user.id,
        status=RunStatus.PENDING,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)  # populate task_id from DB

    # 3.  Kick off background orchestration
    background_tasks.add_task(
        orchestrator.execute_variations,
        task_id=run.task_id,
        run_id=run.run_id,
        repo_url=str(request.github_url),
        prompt=request.prompt,
        variations=len(request.model_variants),
        agent_config=None,  # already stored in DB
        agent_mode=request.agent_mode,
        db_session=db,
    )

    stream_url = f"ws://{settings.host}:{settings.port}/ws/runs/{run.run_id}"

    return CreateRunResponse(
        task_id=run.task_id,
        run_id=run.run_id,
        websocket_url=stream_url,
        stream_url=stream_url,
        polling_url=f"{settings.api_v1_prefix}/runs/{run.run_id}/outputs",
        status="accepted",
        estimated_duration_seconds=len(request.model_variants) * 40,
        # Removed session/turn parameters - runs are standalone
    )


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="List runs",
)
async def list_runs(
    current_user: CurrentUserAPIKey,
    db: AsyncSession = Depends(get_session),
    status: RunStatus | None = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse:
    """List runs with optional filtering."""
    # Build query
    # Build query
    query = select(Run).order_by(desc(Run.created_at))  # type: ignore[arg-type]

    # Apply filters
    query = query.where(Run.user_id == current_user.id)
    if status:
        query = query.where(Run.status == status)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    # Execute
    result = await db.execute(query)
    runs = result.scalars().all()

    # Convert to list items
    items = [RunListItem.model_validate(run) for run in runs]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )




@router.get(
    "/{task_id}",
    response_model=RunDetails,
    summary="Get run details",
)
async def get_run(
    task_id: int,
    current_user: CurrentUserAPIKey,
    db: AsyncSession = Depends(get_session),
) -> Run:
    """Get detailed information about a specific run."""
    query = select(Run).where(Run.task_id == task_id).where(Run.user_id == current_user.id)

    result = await db.execute(query)
    run = result.scalar_one_or_none()

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    return run


# Removed select_winner endpoint - no variation comparison needed


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel a run",
)
async def cancel_run(
    task_id: int,
    current_user: CurrentUserAPIKey,
    db: AsyncSession = Depends(get_session),
) -> None:
    """Cancel a pending or running run."""
    query = select(Run).where(Run.task_id == task_id).where(Run.user_id == current_user.id)

    result = await db.execute(query)
    run = result.scalar_one_or_none()

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    if run.status in [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel run with status: {run.status}",
        )

    # Update status
    run.status = RunStatus.CANCELLED
    run.updated_at = datetime.utcnow()
    await db.commit()

    logger.info("run_cancelled", run_id=run.run_id)


@router.get(
    "/{run_id}/outputs",
    response_model=list[dict],
    summary="Poll for agent outputs",
    description="""
    Get agent outputs since a given timestamp. This endpoint provides an alternative to WebSocket streaming for clients that prefer HTTP polling.

    **Usage Pattern:**
    1. Create a run via POST /runs
    2. Poll this endpoint every 500ms with the `since` parameter set to the timestamp of the last received output
    3. Process new outputs and update the `since` parameter for the next poll

    **Filtering:**
    - Use `variation_id` to get outputs from a specific model variant only
    - Use `output_type` to filter by message type ('llm', 'stdout', 'status')
    - Use `since` to get only outputs after a specific timestamp

    **Performance:**
    - Results are limited to 1000 outputs per request
    - Outputs are ordered by timestamp (oldest first)
    - Use pagination with `since` parameter for large result sets
    """,
)
async def get_agent_outputs(
    run_id: str,
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
    Poll for new agent outputs since a given timestamp.

    This endpoint replaces the SSE streaming with database polling.
    Frontend should call this every 0.5 seconds with the last received timestamp.
    """
    # Verify run exists and user has access
    query = select(Run).where(Run.id == run_id)
    if current_user:
        query = query.where(Run.user_id == current_user.id)

    result = await db.execute(query)
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    # Build query for outputs
    outputs_query = select(AgentOutput).where(AgentOutput.task_id == run.task_id)

    # Apply filters
    if since:
        outputs_query = outputs_query.where(AgentOutput.timestamp > since)
    if variation_id is not None:
        outputs_query = outputs_query.where(AgentOutput.variation_id == variation_id)
    if output_type:
        outputs_query = outputs_query.where(AgentOutput.output_type == output_type)

    # Order by timestamp and limit
    outputs_query = outputs_query.order_by(AgentOutput.timestamp).limit(limit)

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
