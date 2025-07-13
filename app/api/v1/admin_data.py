from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.run import AgentOutput, Run
from sqlmodel import select

router = APIRouter()


@router.get("/runs")
async def get_runs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_session),
):
    """Get runs with filtering and pagination."""
    
    # Build query
    query = select(Run)
    
    # Apply filters
    if status:
        query = query.where(Run.status == status)
    
    if start_date:
        query = query.where(Run.created_at >= start_date)
    
    if end_date:
        query = query.where(Run.created_at <= end_date)
    
    # Add order and pagination
    query = query.order_by(desc(Run.created_at))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination and execute
    paginated_query = query.offset(offset).limit(limit)
    result = await db.execute(paginated_query)
    runs = result.scalars().all()
    
    # Get message counts for each run
    run_ids = [run.id for run in runs]
    message_count_dict = {}
    if run_ids:
        count_query = select(AgentOutput.run_id, func.count(AgentOutput.id).label('count')).where(
            AgentOutput.run_id.in_(run_ids)
        ).group_by(AgentOutput.run_id)
        count_result = await db.execute(count_query)
        for row in count_result.fetchall():
            message_count_dict[row.run_id] = row.count
    
    # Format response
    runs_data = []
    for run in runs:
        run_data = {
            "id": run.id,
            "status": run.status,
            "created_at": run.created_at,
            "updated_at": getattr(run, 'updated_at', run.created_at),
            "github_url": run.github_url,
            "prompt": run.prompt,
            "model_variants": run.variations,
            "agent_mode": getattr(run, 'agent_mode', 'unknown'),
            "message_count": message_count_dict.get(run.id, 0)
        }
        runs_data.append(run_data)
    
    return {
        "runs": runs_data,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/agent-outputs")
async def get_agent_outputs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    output_type: Optional[str] = Query(None),
    run_id: Optional[str] = Query(None),
    variation_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_session),
):
    """Get agent outputs with filtering and pagination."""
    
    # Build query
    query = select(AgentOutput)
    
    # Apply filters
    if output_type:
        query = query.where(AgentOutput.output_type == output_type)
    
    if run_id:
        query = query.where(AgentOutput.run_id == run_id)
    
    if variation_id is not None:
        query = query.where(AgentOutput.variation_id == variation_id)
    
    if start_date:
        query = query.where(AgentOutput.timestamp >= start_date)
    
    if end_date:
        query = query.where(AgentOutput.timestamp <= end_date)
    
    # Add order and pagination
    query = query.order_by(desc(AgentOutput.timestamp))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination and execute
    paginated_query = query.offset(offset).limit(limit)
    result = await db.execute(paginated_query)
    outputs = result.scalars().all()
    
    # Format response
    outputs_data = []
    for output in outputs:
        output_data = {
            "id": output.id,
            "run_id": output.run_id,
            "variation_id": output.variation_id,
            "output_type": output.output_type,
            "content": output.content,
            "timestamp": output.timestamp
        }
        outputs_data.append(output_data)
    
    return {
        "outputs": outputs_data,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/variations/{run_id}")
async def get_variations_for_run(
    run_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Get all variation IDs for a specific run."""
    
    query = select(AgentOutput.variation_id).where(
        AgentOutput.run_id == run_id
    ).distinct().order_by(AgentOutput.variation_id)
    
    result = await db.execute(query)
    variations = result.scalars().all()
    
    return {"variations": variations}


@router.get("/output-types")
async def get_output_types(db: AsyncSession = Depends(get_session)):
    """Get all distinct output types."""
    
    query = select(AgentOutput.output_type).distinct().order_by(AgentOutput.output_type)
    
    result = await db.execute(query)
    output_types = result.scalars().all()
    
    return {"output_types": output_types}


@router.get("/run-ids")
async def get_run_ids(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_session),
):
    """Get all run IDs for dropdown selection."""
    
    query = select(AgentOutput.run_id).distinct().order_by(desc(AgentOutput.run_id)).limit(limit)
    
    result = await db.execute(query)
    run_ids = result.scalars().all()
    
    return {"run_ids": run_ids}