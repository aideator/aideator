from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.agent_outputs import AgentOutput
from app.models.run import Run

router = APIRouter()


@router.get("/runs")
async def get_runs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get runs with filtering and pagination."""
    
    query = db.query(Run)
    
    # Apply filters
    filters = []
    
    if status:
        filters.append(Run.status == status)
    
    if start_date:
        filters.append(Run.created_at >= start_date)
    
    if end_date:
        filters.append(Run.created_at <= end_date)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Add order and pagination
    query = query.order_by(desc(Run.created_at))
    
    # Get total count
    total = await query.count()
    
    # Apply pagination
    runs = await query.offset(offset).limit(limit).all()
    
    # Get message counts for each run
    run_ids = [run.id for run in runs]
    if run_ids:
        message_counts = await db.execute(
            "SELECT run_id, COUNT(*) as count FROM agent_outputs WHERE run_id = ANY(:run_ids) GROUP BY run_id",
            {"run_ids": run_ids}
        )
        message_count_dict = {row.run_id: row.count for row in message_counts}
    else:
        message_count_dict = {}
    
    # Format response
    runs_data = []
    for run in runs:
        run_data = {
            "id": run.id,
            "status": run.status,
            "created_at": run.created_at,
            "updated_at": run.updated_at,
            "github_url": run.github_url,
            "prompt": run.prompt,
            "model_variants": run.model_variants,
            "agent_mode": run.agent_mode,
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
    db: AsyncSession = Depends(get_db),
):
    """Get agent outputs with filtering and pagination."""
    
    query = db.query(AgentOutput)
    
    # Apply filters
    filters = []
    
    if output_type:
        filters.append(AgentOutput.output_type == output_type)
    
    if run_id:
        filters.append(AgentOutput.run_id == run_id)
    
    if variation_id is not None:
        filters.append(AgentOutput.variation_id == variation_id)
    
    if start_date:
        filters.append(AgentOutput.timestamp >= start_date)
    
    if end_date:
        filters.append(AgentOutput.timestamp <= end_date)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Add order and pagination
    query = query.order_by(desc(AgentOutput.timestamp))
    
    # Get total count
    total = await query.count()
    
    # Apply pagination
    outputs = await query.offset(offset).limit(limit).all()
    
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
    db: AsyncSession = Depends(get_db),
):
    """Get all variation IDs for a specific run."""
    
    result = await db.execute(
        "SELECT DISTINCT variation_id FROM agent_outputs WHERE run_id = :run_id ORDER BY variation_id",
        {"run_id": run_id}
    )
    
    variations = [row.variation_id for row in result]
    
    return {"variations": variations}


@router.get("/output-types")
async def get_output_types(db: AsyncSession = Depends(get_db)):
    """Get all distinct output types."""
    
    result = await db.execute(
        "SELECT DISTINCT output_type FROM agent_outputs ORDER BY output_type"
    )
    
    output_types = [row.output_type for row in result]
    
    return {"output_types": output_types}


@router.get("/run-ids")
async def get_run_ids(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Get all run IDs for dropdown selection."""
    
    result = await db.execute(
        "SELECT DISTINCT run_id FROM agent_outputs ORDER BY run_id DESC LIMIT :limit",
        {"limit": limit}
    )
    
    run_ids = [row.run_id for row in result]
    
    return {"run_ids": run_ids}