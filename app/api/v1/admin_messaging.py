"""Simplified Admin Interface for Container Messaging Visualization."""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, delete, desc, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import get_current_user_from_api_key
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.run import AgentOutput, Run, RunStatus
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter()


async def get_current_user_dev_bypass() -> User | None:
    """Development bypass for authentication."""
    settings = get_settings()
    logger.info(f"Dev bypass called: debug={settings.debug}")
    if settings.debug:  # Development mode when debug=True
        logger.info("Allowing anonymous access in development mode")
        return None  # Allow anonymous access in dev
    logger.info("Debug=False, requiring API key")
    raise HTTPException(status_code=401, detail="API key required")


@router.get("/overview", summary="Simple container messaging overview")
async def get_overview(
    db: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_current_user_dev_bypass),
) -> dict[str, Any]:
    """Get overall database statistics."""
    # Total runs
    total_runs = await db.scalar(select(func.count(Run.id)))

    # Runs by status
    status_counts = await db.execute(
        select(Run.status, func.count(Run.id)).group_by(Run.status)
    )
    runs_by_status = {status.value: count for status, count in status_counts}

    # Total messages
    total_messages = await db.scalar(select(func.count(AgentOutput.id)))

    # Messages by type
    type_counts = await db.execute(
        select(AgentOutput.output_type, func.count(AgentOutput.id)).group_by(
            AgentOutput.output_type
        )
    )
    messages_by_type = dict(type_counts)

    # Recent activity (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_runs = await db.scalar(
        select(func.count(Run.id)).where(Run.created_at > yesterday)
    )
    recent_messages = await db.scalar(
        select(func.count(AgentOutput.id)).where(AgentOutput.timestamp > yesterday)
    )

    # Database size (SQLite specific)
    try:
        result = await db.execute(
            text(
                "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"
            )
        )
        db_size = result.scalar() or 0
    except Exception:
        db_size = 0

    # Average messages per run
    avg_messages = total_messages / max(total_runs, 1)

    # Active runs count
    active_runs = await db.scalar(
        select(func.count(Run.id)).where(
            or_(
                Run.status == RunStatus.RUNNING,
                Run.status == RunStatus.PENDING,
            )
        )
    )

    return {
        "active_runs": active_runs or 0,
        "total_messages": total_messages or 0,
        "recent_messages_1h": recent_messages or 0,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/runs", summary="Get current runs")
async def get_runs(
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_current_user_dev_bypass),
) -> list[dict[str, Any]]:
    """Get active runs with message metrics."""
    # Build query
    query = select(Run).order_by(desc(Run.created_at)).limit(limit)

    # Get runs
    result = await db.execute(query)
    runs = result.scalars().all()

    # Get message counts for each run
    run_list = []
    for run in runs:
        # Get message counts by variation
        variation_counts = await db.execute(
            select(
                AgentOutput.variation_id,
                func.count(AgentOutput.id).label("count"),
                func.max(AgentOutput.timestamp).label("last_message"),
            )
            .where(AgentOutput.run_id == run.id)
            .group_by(AgentOutput.variation_id)
        )

        variation_data = {}
        total_messages = 0
        last_message_time = None

        for variation_id, count, last_msg in variation_counts:
            variation_data[variation_id] = {
                "message_count": count,
                "last_message": last_msg.isoformat() if last_msg else None,
            }
            total_messages += count
            if last_msg and (not last_message_time or last_msg > last_message_time):
                last_message_time = last_msg

        # Calculate message rate
        if run.started_at and last_message_time:
            duration = (last_message_time - run.started_at).total_seconds()
            message_rate = total_messages / max(duration, 1)
        else:
            message_rate = 0

        run_list.append(
            {
                "id": run.id,
                "status": run.status.value,
                "github_url": getattr(run, 'github_url', '') or '',
                "prompt": (run.prompt[:100] + "..." if len(run.prompt) > 100 else run.prompt) if run.prompt else '',
                "variations": getattr(run, 'variations', 1) or 1,
                "created_at": run.created_at.isoformat(),
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "message_count": total_messages,
                "message_rate_per_second": round(message_rate, 2),
                "variation_metrics": variation_data,
                "winning_variation_id": getattr(run, 'winning_variation_id', None),
            }
        )

    return run_list


@router.get("/messages", summary="Get recent messages across all runs")
async def get_message_stream(
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    run_id: str | None = Query(None),
    variation_id: int | None = Query(None),
    output_type: str | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_current_user_dev_bypass),
) -> dict[str, Any]:
    """Get recent messages with filtering."""
    # Build query
    query = select(AgentOutput)

    # Apply filters
    conditions = []
    if run_id:
        conditions.append(AgentOutput.run_id == run_id)
    if variation_id is not None:
        conditions.append(AgentOutput.variation_id == variation_id)
    if output_type:
        conditions.append(AgentOutput.output_type == output_type)
    if search:
        conditions.append(
            func.lower(AgentOutput.content).like(func.lower(f"%{search}%"))
        )

    if conditions:
        if len(conditions) == 1:
            query = query.where(conditions[0])
        elif len(conditions) > 1:
            query = query.where(and_(*conditions))  # type: ignore[missing-argument]

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_count = await db.scalar(count_query)

    # Apply pagination and ordering
    query = query.order_by(desc(AgentOutput.timestamp)).offset(offset).limit(limit)

    # Execute query
    result = await db.execute(query)
    messages = result.scalars().all()

    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "messages": [
            {
                "id": msg.id,
                "run_id": msg.run_id,
                "variation_id": msg.variation_id,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "output_type": msg.output_type,
            }
            for msg in messages
        ],
    }


@router.get("/messages/search", summary="Search messages")
async def search_messages(
    query: str = Query(..., min_length=1),
    limit: int = Query(50, le=200),
    run_id: str | None = Query(None),
    output_type: str | None = Query(None),
    db: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_current_user_dev_bypass),
) -> list[dict[str, Any]]:
    """Search message content."""
    # Build search query
    search_query = select(AgentOutput).where(
        func.lower(AgentOutput.content).like(func.lower(f"%{query}%"))
    )

    if run_id:
        search_query = search_query.where(AgentOutput.run_id == run_id)
    if output_type:
        search_query = search_query.where(AgentOutput.output_type == output_type)

    search_query = search_query.order_by(desc(AgentOutput.timestamp)).limit(limit)

    # Execute search
    result = await db.execute(search_query)
    messages = result.scalars().all()

    return [
        {
            "id": msg.id,
            "run_id": msg.run_id,
            "variation_id": msg.variation_id,
            "content": msg.content[:500] + "..." if len(msg.content) > 500 else msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "output_type": msg.output_type,
            "match_preview": msg.content[:200] + "..."
            if len(msg.content) > 200
            else msg.content,
        }
        for msg in messages
    ]


@router.get("/live", summary="Live container activity")
async def get_live_activity(
    db: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_current_user_dev_bypass),
) -> dict[str, Any]:
    """Get live container activity in the last 5 minutes."""
    # Get activity from last 5 minutes
    since = datetime.utcnow() - timedelta(minutes=5)
    
    # Get active containers (runs with recent messages)
    active_containers_query = select(
        AgentOutput.run_id,
        AgentOutput.variation_id,
        func.count(AgentOutput.id).label("message_count"),
        func.max(AgentOutput.timestamp).label("latest_timestamp"),
        func.max(AgentOutput.content).label("latest_message")
    ).where(
        AgentOutput.timestamp > since
    ).group_by(
        AgentOutput.run_id, AgentOutput.variation_id
    ).order_by(
        desc("latest_timestamp")
    ).limit(10)
    
    result = await db.execute(active_containers_query)
    container_activity = []
    
    for row in result:
        container_activity.append({
            "run_id": row.run_id,
            "variation_id": row.variation_id,
            "message_count": row.message_count,
            "latest_timestamp": row.latest_timestamp.isoformat(),
            "latest_message": (row.latest_message[:100] + "..." if len(row.latest_message) > 100 else row.latest_message) if row.latest_message else ""
        })
    
    return {
        "active_containers": len(container_activity),
        "container_activity": container_activity,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health", summary="Simple health check")
async def health_check(
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Check database health and performance."""
    health_checks = {
        "database_connection": False,
        "write_test": False,
        "read_test": False,
        "response_time_ms": 0,
    }

    start_time = datetime.utcnow()

    try:
        # Test database connection
        await db.execute(text("SELECT 1"))
        health_checks["database_connection"] = True

        # Test read
        await db.scalar(select(func.count(Run.id)))
        health_checks["read_test"] = True

        # Test write (create and delete a test record)
        test_output = AgentOutput(
            run_id="health-check-test",
            variation_id=0,
            content="Health check test",
            output_type="system",
        )
        db.add(test_output)
        await db.flush()

        # Delete test record
        await db.delete(test_output)
        await db.flush()

        health_checks["write_test"] = True

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_checks["error"] = str(e)

    # Calculate response time
    response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    health_checks["response_time_ms"] = round(response_time, 2)

    # Overall health status
    health_checks["healthy"] = all(
        [
            health_checks["database_connection"],
            health_checks["read_test"],
            health_checks["write_test"],
        ]
    )

    return health_checks
