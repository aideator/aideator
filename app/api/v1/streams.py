from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user_from_api_key
from app.core.logging import get_logger
from app.models.run import Run
from app.models.user import User
from app.services.sse_manager import sse_manager

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/{run_id}/stream",
    summary="Stream agent outputs",
    response_class=StreamingResponse,
)
async def stream_run(
    run_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_from_api_key),
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
    
    # Filter by user if authenticated
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