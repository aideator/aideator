import uuid
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.core.dependencies import CurrentUserAPIKey
from app.core.deps import get_orchestrator
from app.core.logging import get_logger
from app.models.run import Run, RunStatus
from app.models.user import User
from app.models.session import Session, Turn
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.runs import (
    CreateRunRequest,
    CreateRunResponse,
    RunDetails,
    RunListItem,
    SelectWinnerRequest,
)

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
    orchestrator = Depends(get_orchestrator),
    db: AsyncSession = Depends(get_session),
) -> CreateRunResponse:
    """
    Create a new agent run that will spawn N containerized LLM agents.
    
    The run is processed asynchronously in the background using Kubernetes Jobs.
    Connect to the returned stream_url to receive real-time agent outputs.
    """
    # Generate run ID (use hyphens for Kubernetes compatibility)
    run_id = f"run-{uuid.uuid4().hex}"
    
    # Handle session and turn creation
    session_id = request.session_id
    turn_id = request.turn_id
    
    if not session_id:
        # Create a new session if none provided
        session_id = str(uuid.uuid4())
        session = Session(
            id=session_id,
            user_id=current_user.id,
            title=f"Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            description="Multi-model comparison session",
            models_used=[variant.model_definition_id for variant in request.model_variants],
        )
        db.add(session)
        logger.info(f"Created new session: {session_id}")
    else:
        # Verify session exists and belongs to user
        session_query = select(Session).where(
            Session.id == session_id,
            Session.user_id == current_user.id
        )
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or not accessible"
            )
    
    if not turn_id:
        # Create a new turn if none provided
        turn_id = str(uuid.uuid4())
        
        # Get next turn number
        turn_count_query = select(func.count(Turn.id)).where(Turn.session_id == session_id)
        turn_count_result = await db.execute(turn_count_query)
        turn_number = turn_count_result.scalar() + 1
        
        turn = Turn(
            id=turn_id,
            session_id=session_id,
            turn_number=turn_number,
            prompt=request.prompt,
            models_requested=[variant.model_definition_id for variant in request.model_variants],
            status="pending",
        )
        db.add(turn)
        logger.info(f"Created new turn: {turn_id} (turn #{turn_number})")
    else:
        # Verify turn exists and belongs to the session
        turn_query = select(Turn).where(
            Turn.id == turn_id,
            Turn.session_id == session_id
        )
        turn_result = await db.execute(turn_query)
        turn = turn_result.scalar_one_or_none()
        
        if not turn:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Turn not found or not accessible"
            )
    
    # Create run record
    run = Run(
        id=run_id,
        github_url=str(request.github_url),
        prompt=request.prompt,
        variations=len(request.model_variants),  # Number of model variants
        agent_config={
            "model_variants": [variant.model_dump() for variant in request.model_variants],
            "use_claude_code": request.use_claude_code,
            "agent_mode": request.agent_mode,
            "session_id": session_id,
            "turn_id": turn_id,
        },
        user_id=current_user.id,
        status=RunStatus.PENDING,
    )
    
    db.add(run)
    await db.commit()
    
    logger.info(
        "run_created",
        run_id=run_id,
        user_id=current_user.id,
        variations=len(request.model_variants),
    )
    
    # Schedule background orchestration
    background_tasks.add_task(
        orchestrator.execute_variations,
        run_id=run_id,
        repo_url=str(request.github_url),
        prompt=request.prompt,
        variations=len(request.model_variants),
        agent_config=None,  # agent_config is stored in the run record
        agent_mode=request.agent_mode,
        db_session=db,
        use_batch_job=False,  # Use individual jobs for now
    )
    
    return CreateRunResponse(
        run_id=run_id,
        stream_url=f"{settings.api_v1_prefix}/runs/{run_id}/stream",
        status="accepted",
        estimated_duration_seconds=len(request.model_variants) * 40,  # Rough estimate
        session_id=session_id,
        turn_id=turn_id,
    )


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="List runs",
)
async def list_runs(
    current_user: CurrentUserAPIKey,
    db: AsyncSession = Depends(get_session),
    status: Optional[RunStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse:
    """List runs with optional filtering."""
    # Build query
    query = select(Run).order_by(Run.created_at.desc())
    
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
    "/{run_id}",
    response_model=RunDetails,
    summary="Get run details",
)
async def get_run(
    run_id: str,
    current_user: CurrentUserAPIKey,
    db: AsyncSession = Depends(get_session),
) -> Run:
    """Get detailed information about a specific run."""
    query = select(Run).where(Run.id == run_id)
    
    # Filter by user
    query = query.where(Run.user_id == current_user.id)
    
    result = await db.execute(query)
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    
    return run


@router.post(
    "/{run_id}/select",
    response_model=RunDetails,
    summary="Select winning variation",
)
async def select_winner(
    run_id: str,
    request: SelectWinnerRequest,
    current_user: CurrentUserAPIKey,
    db: AsyncSession = Depends(get_session),
) -> Run:
    """Select the winning variation for a completed run."""
    query = select(Run).where(Run.id == run_id)
    
    # Filter by user
    query = query.where(Run.user_id == current_user.id)
    
    result = await db.execute(query)
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    
    if run.status != RunStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only select winner for completed runs",
        )
    
    if request.winning_variation_id >= run.variations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid variation ID. Must be between 0 and {run.variations - 1}",
        )
    
    # Update winning variation
    run.winning_variation_id = request.winning_variation_id
    await db.commit()
    await db.refresh(run)
    
    logger.info(
        "winner_selected",
        run_id=run_id,
        variation_id=request.winning_variation_id,
    )
    
    return run


@router.delete(
    "/{run_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel a run",
)
async def cancel_run(
    run_id: str,
    current_user: CurrentUserAPIKey,
    db: AsyncSession = Depends(get_session),
) -> None:
    """Cancel a pending or running run."""
    query = select(Run).where(Run.id == run_id)
    
    # Filter by user
    query = query.where(Run.user_id == current_user.id)
    
    result = await db.execute(query)
    run = result.scalar_one_or_none()
    
    if not run:
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
    await db.commit()
    
    logger.info("run_cancelled", run_id=run_id)