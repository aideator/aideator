"""
Admin endpoints for system management.
"""


from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.v1.deps import require_admin
from app.core.database import get_session
from app.models.model_definition import ModelSyncLog
from app.tasks.model_sync_task import model_sync_task

router = APIRouter()


@router.post("/models/sync", dependencies=[Depends(require_admin)])
async def trigger_model_sync():
    """Manually trigger a model sync from LiteLLM proxy.
    
    This endpoint allows admins to force an immediate sync rather than
    waiting for the next scheduled sync.
    """
    try:
        await model_sync_task.sync_now()
        return {"status": "success", "message": "Model sync triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {e!s}")


@router.get("/models/sync/history", response_model=list[ModelSyncLog], dependencies=[Depends(require_admin)])
async def get_sync_history(
    session: Session = Depends(get_session),
    limit: int = 10
):
    """Get the history of model sync operations.
    
    Returns the most recent sync logs showing when syncs ran and their results.
    """
    sync_logs = session.exec(
        select(ModelSyncLog)
        .order_by(ModelSyncLog.started_at.desc())
        .limit(limit)
    ).all()

    return sync_logs


@router.get("/models/sync/status", dependencies=[Depends(require_admin)])
async def get_sync_status(session: Session = Depends(get_session)):
    """Get the current sync status and last sync information."""
    # Get the most recent sync log
    last_sync = session.exec(
        select(ModelSyncLog)
        .order_by(ModelSyncLog.started_at.desc())
        .limit(1)
    ).first()

    # Check if sync is currently running
    is_running = model_sync_task.is_running

    # Get total active models
    from app.models.model_definition import ModelDefinitionDB
    active_models_count = session.exec(
        select(ModelDefinitionDB).where(ModelDefinitionDB.is_active == True)
    ).count()

    return {
        "sync_task_running": is_running,
        "last_sync": last_sync,
        "active_models_count": active_models_count,
        "sync_interval_minutes": model_sync_task.sync_interval.total_seconds() / 60
    }
