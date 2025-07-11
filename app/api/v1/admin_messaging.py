"""Admin API endpoints for database monitoring."""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, delete, desc, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import get_current_user_from_api_key
from app.core.logging import get_logger
from app.models.run import AgentOutput, Run, RunStatus
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter()


@router.get("/stats", summary="Get database statistics")
async def get_database_stats(
    db: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_current_user_from_api_key),
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

    return {
        "total_runs": total_runs,
        "runs_by_status": runs_by_status,
        "total_messages": total_messages,
        "messages_by_type": messages_by_type,
        "recent_runs_24h": recent_runs,
        "recent_messages_24h": recent_messages,
        "database_size_bytes": db_size,
        "average_messages_per_run": round(avg_messages, 2),
    }


@router.get("/runs/active", summary="Get active runs with metrics")
async def get_active_runs(
    limit: int = Query(20, le=100),
    include_completed: bool = Query(False),
    db: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_current_user_from_api_key),
) -> list[dict[str, Any]]:
    """Get active runs with message metrics."""
    # Build query
    query = select(Run)
    if not include_completed:
        query = query.where(Run.status.in_([RunStatus.PENDING, RunStatus.RUNNING]))
    query = query.order_by(Run.created_at.desc()).limit(limit)

    # Get runs
    result = await db.execute(query)
    runs = result.scalars().all()

    # Get message counts for each run
    run_metrics = []
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

        run_metrics.append(
            {
                "id": run.id,
                "status": run.status.value,
                "github_url": run.github_url,
                "prompt": run.prompt[:100] + "..."
                if len(run.prompt) > 100
                else run.prompt,
                "variations": run.variations,
                "created_at": run.created_at.isoformat(),
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "total_messages": total_messages,
                "message_rate_per_second": round(message_rate, 2),
                "variation_metrics": variation_data,
                "winning_variation_id": run.winning_variation_id,
            }
        )

    return run_metrics


@router.get("/messages/stream", summary="Get recent messages across all runs")
async def get_message_stream(
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    run_id: str | None = Query(None),
    variation_id: int | None = Query(None),
    output_type: str | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_current_user_from_api_key),
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
        conditions.append(AgentOutput.content.ilike(f"%{search}%"))

    if conditions:
        if len(conditions) == 1:
            query = query.where(conditions[0])
        else:
            query = query.where(and_(*conditions))

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
    current_user: User | None = Depends(get_current_user_from_api_key),
) -> list[dict[str, Any]]:
    """Search message content."""
    # Build search query
    search_query = select(AgentOutput).where(AgentOutput.content.ilike(f"%{query}%"))

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
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "output_type": msg.output_type,
            "match_preview": msg.content[:200] + "..."
            if len(msg.content) > 200
            else msg.content,
        }
        for msg in messages
    ]


@router.post("/cleanup", summary="Cleanup old data")
async def cleanup_database(
    older_than_days: int = Query(7, ge=1, le=90),
    dry_run: bool = Query(True),
    db: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_current_user_from_api_key),
) -> dict[str, Any]:
    """Delete old runs and their messages."""
    cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

    # Find old runs
    old_runs_query = select(Run.id).where(
        and_(
            Run.created_at < cutoff_date,
            Run.status.in_(
                [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED]
            ),
        )
    )
    result = await db.execute(old_runs_query)
    old_run_ids = [row[0] for row in result]

    if not old_run_ids:
        return {
            "message": "No old runs found to clean up",
            "runs_affected": 0,
            "messages_affected": 0,
            "dry_run": dry_run,
        }

    # Count messages that would be deleted
    messages_count = await db.scalar(
        select(func.count(AgentOutput.id)).where(AgentOutput.run_id.in_(old_run_ids))
    )

    if not dry_run:
        # Delete messages first (foreign key constraint)
        await db.execute(delete(AgentOutput).where(AgentOutput.run_id.in_(old_run_ids)))

        # Delete runs
        await db.execute(delete(Run).where(Run.id.in_(old_run_ids)))

        await db.commit()

        logger.info(
            "database_cleanup_completed",
            runs_deleted=len(old_run_ids),
            messages_deleted=messages_count,
            older_than_days=older_than_days,
        )

    return {
        "message": "Cleanup completed" if not dry_run else "Dry run - no data deleted",
        "runs_affected": len(old_run_ids),
        "messages_affected": messages_count,
        "dry_run": dry_run,
        "cutoff_date": cutoff_date.isoformat(),
    }


@router.get("/health", summary="Database health check")
async def database_health(
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
        # Test connection
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
