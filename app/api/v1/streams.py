from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
import asyncio
import json

from app.core.config import get_settings
from app.core.database import get_session
from app.core.dependencies import CurrentUserAPIKey, get_current_user_from_api_key
from app.core.logging import get_logger
from app.models.run import Run
from app.models.user import User
from app.services.sse_manager import sse_manager

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()


@router.get(
    "/{run_id}/stream",
    summary="Stream agent outputs via Server-Sent Events",
    response_class=StreamingResponse,
)
async def stream_run(
    run_id: str,
    current_user: CurrentUserAPIKey,
    db: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """
    Stream agent outputs via Server-Sent Events.

    This endpoint establishes a long-lived connection to receive real-time
    updates from all agent variations as they process the repository.

    Event Types:
    - `agent_output`: Output from an agent variation
    - `agent_error`: Error from an agent variation  
    - `agent_complete`: Agent variation finished
    - `run_complete`: All agents finished
    - `heartbeat`: Keep-alive signal
    """
    # Verify run exists and user has access
    query = select(Run).where(Run.id == run_id)
    query = query.where(Run.user_id == current_user.id)

    result = await db.execute(query)
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    logger.info(
        "stream_connection_started",
        run_id=run_id,
        user_id=current_user.id if current_user else None,
    )

    # Create SSE response
    return StreamingResponse(
        sse_manager.connect(run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*",  # CORS for SSE
        },
    )


@router.get(
    "/{run_id}/debug-logs",
    summary="Stream debug logs from agent containers",
    response_class=StreamingResponse,
)
async def stream_debug_logs(
    run_id: str,
    variation_id: int = 0,
    db: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_current_user_from_api_key),
) -> StreamingResponse:
    """
    Stream raw Kubernetes logs from agent containers for debugging.

    This endpoint provides access to the raw kubectl logs output from agent
    containers, including structured logs, debug messages, and system output.
    Only available when DEBUG_AGENT_CONTAINER is enabled.

    Args:
        run_id: The run ID to debug
        variation_id: The agent variation ID to debug (default: 0)

    Returns:
        StreamingResponse with raw log lines
    """
    settings = get_settings()

    # Check if debug mode is enabled
    if not settings.debug_agent_container:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debug mode is not enabled. Set DEBUG_AGENT_CONTAINER=true to enable.",
        )

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

    logger.info(
        "debug_stream_connection_started",
        run_id=run_id,
        variation_id=variation_id,
        user_id=current_user.id if current_user else None,
    )
    
    # Import here to avoid circular imports
    from app.services.kubernetes_service import KubernetesService
    kubernetes_service = KubernetesService()
    
    async def debug_event_generator():
        """Generate debug events from raw kubectl logs."""
        logger.info(f"[DEBUG-STREAM] Starting debug stream for run {run_id}")
        
        try:
            # Get the job name
            job_name = f"agent-{run_id}-{variation_id}"
            
            # Stream raw logs
            async for log_line in kubernetes_service.stream_raw_debug_logs(job_name):
                yield f"data: {log_line}\n\n"
                
        except Exception as e:
            logger.error(f"[DEBUG-STREAM] Error streaming debug logs: {e}")
            yield f"data: [ERROR] {e}\n\n"
        finally:
            logger.info(f"[DEBUG-STREAM] Debug stream completed for run {run_id}")
    
    # Create SSE response
    return StreamingResponse(
        debug_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*",  # CORS for SSE
        },
    )