"""Simplified Admin Interface for Container Messaging Visualization."""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, text, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.logging import get_logger
from app.models.run import Run, RunStatus, AgentOutput

logger = get_logger(__name__)
router = APIRouter()


@router.get("/overview", summary="Simple container messaging overview")
async def get_overview(
    db: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Get a simple overview of container messaging activity."""
    # Count active runs
    active_runs = await db.scalar(
        select(func.count(Run.id))
        .where(Run.status.in_([RunStatus.PENDING, RunStatus.RUNNING]))
    )
    
    # Count total messages
    total_messages = await db.scalar(select(func.count(AgentOutput.id)))
    
    # Count messages in last hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_messages = await db.scalar(
        select(func.count(AgentOutput.id))
        .where(AgentOutput.timestamp > one_hour_ago)
    )
    
    # Get message types
    type_counts = await db.execute(
        select(AgentOutput.output_type, func.count(AgentOutput.id))
        .group_by(AgentOutput.output_type)
    )
    message_types = dict(type_counts)
    
    return {
        "active_runs": active_runs,
        "total_messages": total_messages,
        "recent_messages_1h": recent_messages,
        "message_types": message_types,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/runs", summary="Get current runs")
async def get_runs(
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_session),
) -> List[Dict[str, Any]]:
    """Get current runs with basic info."""
    # Get recent runs
    result = await db.execute(
        select(Run)
        .order_by(Run.created_at.desc())
        .limit(limit)
    )
    runs = result.scalars().all()
    
    # Get message counts for each run
    run_list = []
    for run in runs:
        # Count messages for this run
        message_count = await db.scalar(
            select(func.count(AgentOutput.id))
            .where(AgentOutput.run_id == run.id)
        )
        
        # Get latest message timestamp
        latest_message = await db.scalar(
            select(func.max(AgentOutput.timestamp))
            .where(AgentOutput.run_id == run.id)
        )
        
        run_list.append({
            "id": run.id,
            "status": run.status.value,
            "created_at": run.created_at.isoformat(),
            "variations": run.variations,
            "message_count": message_count,
            "latest_message": latest_message.isoformat() if latest_message else None,
            "github_url": run.github_url[:50] + "..." if len(run.github_url) > 50 else run.github_url,
        })
    
    return run_list


@router.get("/messages", summary="Get recent container messages")
async def get_messages(
    limit: int = Query(50, le=200),
    run_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_session),
) -> List[Dict[str, Any]]:
    """Get recent messages from containers."""
    # Build query
    query = select(AgentOutput)
    
    # Filter by run if specified
    if run_id:
        query = query.where(AgentOutput.run_id == run_id)
    
    # Order by timestamp (most recent first)
    query = query.order_by(AgentOutput.timestamp.desc()).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    messages = result.scalars().all()
    
    return [
        {
            "id": msg.id,
            "run_id": msg.run_id,
            "variation_id": msg.variation_id,
            "content": msg.content[:500] + "..." if len(msg.content) > 500 else msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "output_type": msg.output_type,
        }
        for msg in messages
    ]


@router.get("/live", summary="Live container activity")
async def get_live_activity(
    db: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Get live container activity - messages from last 5 minutes."""
    # Get messages from last 5 minutes
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    
    result = await db.execute(
        select(AgentOutput)
        .where(AgentOutput.timestamp > five_minutes_ago)
        .order_by(AgentOutput.timestamp.desc())
        .limit(100)
    )
    recent_messages = result.scalars().all()
    
    # Group by run_id and variation_id
    activity = {}
    for msg in recent_messages:
        key = f"{msg.run_id}:{msg.variation_id}"
        if key not in activity:
            activity[key] = {
                "run_id": msg.run_id,
                "variation_id": msg.variation_id,
                "message_count": 0,
                "latest_message": None,
                "latest_timestamp": None,
            }
        
        activity[key]["message_count"] += 1
        if not activity[key]["latest_timestamp"] or msg.timestamp > activity[key]["latest_timestamp"]:
            activity[key]["latest_message"] = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            activity[key]["latest_timestamp"] = msg.timestamp.isoformat()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "active_containers": len(activity),
        "total_messages_5min": len(recent_messages),
        "container_activity": list(activity.values()),
    }


@router.get("/health", summary="Simple health check")
async def health_check(
    db: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Simple database health check."""
    try:
        # Test database connection
        await db.execute(text("SELECT 1"))
        
        # Count messages
        message_count = await db.scalar(select(func.count(AgentOutput.id)))
        
        return {
            "status": "healthy",
            "database_connected": True,
            "total_messages": message_count,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database_connected": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }