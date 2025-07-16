"""API endpoints for retrieving agent outputs from database."""


from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.dependencies import CurrentUserAPIKey
from app.core.logging import get_logger
from app.models.run import AgentOutput, Run
from app.schemas.common import PaginatedResponse

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/runs/{run_id}/outputs",
    response_model=PaginatedResponse[AgentOutput],
    summary="Get agent outputs for a run",
    description="Retrieve paginated agent outputs from database with optional filtering",
)
async def get_run_outputs(
    run_id: str,
    current_user: CurrentUserAPIKey,
    db: AsyncSession = Depends(get_session),
    variation_id: int | None = Query(None, description="Filter by variation ID"),
    output_type: str | None = Query(None, description="Filter by output type (stdout, stderr, status, etc.)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of outputs to return"),
    offset: int = Query(0, ge=0, description="Number of outputs to skip"),
) -> PaginatedResponse[AgentOutput]:
    """
    Retrieve agent outputs for a specific run.
    
    This endpoint provides access to all agent outputs stored in the database,
    supporting the real-time streaming architecture with historical data access.
    """

    # Verify run exists and user has access
    run_query = select(Run).where(Run.id == run_id)
    if current_user.user:
        run_query = run_query.where(Run.user_id == current_user.user.id)

    result = await db.execute(run_query)
    run = result.scalar_one_or_none()

    if not run:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found or access denied"
        )

    # Build outputs query with filters
    outputs_query = select(AgentOutput).where(AgentOutput.task_id == run.task_id)

    if variation_id is not None:
        outputs_query = outputs_query.where(AgentOutput.variation_id == variation_id)

    if output_type is not None:
        outputs_query = outputs_query.where(AgentOutput.output_type == output_type)

    # Order by timestamp (most recent first)
    outputs_query = outputs_query.order_by(AgentOutput.timestamp.desc())

    # Get total count for pagination
    count_query = select(AgentOutput).where(AgentOutput.task_id == run.task_id)
    if variation_id is not None:
        count_query = count_query.where(AgentOutput.variation_id == variation_id)
    if output_type is not None:
        count_query = count_query.where(AgentOutput.output_type == output_type)

    from sqlalchemy import func
    total_result = await db.execute(select(func.count()).select_from(count_query.subquery()))
    total = total_result.scalar() or 0

    # Apply pagination
    outputs_query = outputs_query.offset(offset).limit(limit)

    # Execute query
    result = await db.execute(outputs_query)
    outputs = result.scalars().all()

    logger.info(
        f"Retrieved {len(outputs)} agent outputs for run {run_id}",
        extra={
            "run_id": run_id,
            "variation_id": variation_id,
            "output_type": output_type,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    )

    return PaginatedResponse(
        items=outputs,
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + len(outputs) < total
    )


@router.get(
    "/runs/{run_id}/outputs/summary",
    summary="Get agent outputs summary",
    description="Get summary statistics for agent outputs",
)
async def get_run_outputs_summary(
    run_id: str,
    current_user: CurrentUserAPIKey,
    db: AsyncSession = Depends(get_session),
):
    """
    Get summary statistics for agent outputs.
    
    Provides overview of output types, variation counts, and timing information.
    """

    # Verify run exists and user has access
    run_query = select(Run).where(Run.id == run_id)
    if current_user.user:
        run_query = run_query.where(Run.user_id == current_user.user.id)

    result = await db.execute(run_query)
    run = result.scalar_one_or_none()

    if not run:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found or access denied"
        )

    # Get summary statistics
    from sqlalchemy import func

    summary_query = select(
        AgentOutput.output_type,
        AgentOutput.variation_id,
        func.count(AgentOutput.id).label("count"),
        func.min(AgentOutput.timestamp).label("first_output"),
        func.max(AgentOutput.timestamp).label("last_output")
    ).where(
        AgentOutput.task_id == run.task_id
    ).group_by(
        AgentOutput.output_type, AgentOutput.variation_id
    ).order_by(
        AgentOutput.variation_id, AgentOutput.output_type
    )

    result = await db.execute(summary_query)
    summary_data = result.all()

    # Total outputs count
    total_query = select(func.count(AgentOutput.id)).where(AgentOutput.task_id == run.task_id)
    total_result = await db.execute(total_query)
    total_outputs = total_result.scalar() or 0

    # Variation count
    variations_query = select(func.count(func.distinct(AgentOutput.variation_id))).where(AgentOutput.task_id == run.task_id)
    variations_result = await db.execute(variations_query)
    total_variations = variations_result.scalar() or 0

    return {
        "run_id": run_id,
        "total_outputs": total_outputs,
        "total_variations": total_variations,
        "output_breakdown": [
            {
                "output_type": row.output_type,
                "variation_id": row.variation_id,
                "count": row.count,
                "first_output": row.first_output,
                "last_output": row.last_output,
            }
            for row in summary_data
        ]
    }


@router.get(
    "/runs/{run_id}/outputs/latest",
    response_model=list[AgentOutput],
    summary="Get latest agent outputs",
    description="Get the most recent outputs for each variation",
)
async def get_latest_outputs(
    run_id: str,
    current_user: CurrentUserAPIKey,
    db: AsyncSession = Depends(get_session),
    per_variation: int = Query(5, ge=1, le=50, description="Number of latest outputs per variation"),
) -> list[AgentOutput]:
    """
    Get the latest outputs for each variation in a run.
    
    Useful for getting current status of all running agents.
    """

    # Verify run exists and user has access
    run_query = select(Run).where(Run.id == run_id)
    if current_user.user:
        run_query = run_query.where(Run.user_id == current_user.user.id)

    result = await db.execute(run_query)
    run = result.scalar_one_or_none()

    if not run:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found or access denied"
        )

    # Use window function to get latest outputs per variation
    from sqlalchemy.sql import text

    # Get latest outputs using row_number window function
    query = text("""
        SELECT id, run_id, variation_id, content, timestamp, output_type
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY variation_id ORDER BY timestamp DESC) as rn
            FROM agent_outputs
            WHERE task_id = :task_id
        ) ranked
        WHERE rn <= :per_variation
        ORDER BY variation_id, timestamp DESC
    """)

    result = await db.execute(query, {"task_id": run.task_id, "per_variation": per_variation})
    rows = result.fetchall()

    # Convert to AgentOutput objects
    outputs = []
    for row in rows:
        output = AgentOutput(
            id=row.id,
            run_id=row.run_id,
            variation_id=row.variation_id,
            content=row.content,
            timestamp=row.timestamp,
            output_type=row.output_type
        )
        outputs.append(output)

    return outputs
