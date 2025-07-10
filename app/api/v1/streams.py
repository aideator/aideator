from typing import Optional
from datetime import datetime
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import get_current_user_from_api_key
from app.core.logging import get_logger
from app.core.config import get_settings
from app.models.run import Run
from app.models.user import User
from app.services.sse_manager import sse_manager
from app.services.redis_service import redis_service

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()


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


@router.get(
    "/{run_id}/stream/redis",
    summary="Stream agent outputs via Redis pub/sub",
    response_class=StreamingResponse,
)
async def stream_run_redis(
    run_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_from_api_key),
) -> StreamingResponse:
    """
    Stream agent outputs via Redis pub/sub (experimental).
    
    This endpoint uses Redis pub/sub for improved reliability and performance
    compared to the kubectl logs-based streaming.
    
    Event Types:
    - `agent_output`: Output from an agent variation
    - `agent_error`: Error from an agent variation  
    - `agent_complete`: Agent variation finished
    - `run_complete`: All agents finished
    - `heartbeat`: Keep-alive signal
    """
    # Check if Redis is configured
    if not settings.redis_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis streaming not available",
        )
    
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
        "redis_stream_connection_started",
        run_id=run_id,
        user_id=current_user.id if current_user else None,
    )
    
    async def event_generator():
        """Generate SSE events from Redis pub/sub."""
        # Use asyncio.Queue to merge Redis messages and heartbeats
        event_queue = asyncio.Queue()
        
        async def redis_listener():
            """Listen to Redis messages and put them in the queue."""
            try:
                async for message in redis_service.subscribe_to_run(run_id):
                    await event_queue.put(("message", message))
            except Exception as e:
                await event_queue.put(("error", str(e)))
        
        async def heartbeat_sender():
            """Send periodic heartbeats."""
            while True:
                await asyncio.sleep(30)
                await event_queue.put(("heartbeat", None))
        
        # Start background tasks
        redis_task = asyncio.create_task(redis_listener())
        heartbeat_task = asyncio.create_task(heartbeat_sender())
        
        try:
            while True:
                event_type, data = await event_queue.get()
                
                if event_type == "heartbeat":
                    yield {
                        "event": "heartbeat",
                        "data": {"timestamp": datetime.utcnow().isoformat()}
                    }
                
                elif event_type == "error":
                    yield {
                        "event": "error",
                        "data": {"message": data}
                    }
                    break
                
                elif event_type == "message":
                    message = data
                    # Convert Redis message to SSE format
                    if message["type"] == "output":
                        # Extract variation_id from channel
                        parts = message["channel"].split(":")
                        if len(parts) >= 4:
                            variation_id = parts[3]
                            data = message["data"]
                            content = data.get("content", "") if isinstance(data, dict) else str(data)
                            
                            yield {
                                "event": "agent_output",
                                "data": {
                                    "variation_id": variation_id,
                                    "content": content,
                                    "timestamp": data.get("timestamp") if isinstance(data, dict) else None
                                }
                            }
                    
                    elif message["type"] == "status":
                        data = message["data"]
                        status = data.get("status", "unknown")
                        
                        if status == "variation_completed":
                            variation_id = data.get("metadata", {}).get("variation_id", 0)
                            yield {
                                "event": "agent_complete",
                                "data": {"variation_id": variation_id}
                            }
                        elif status in ["completed", "failed"]:
                            yield {
                                "event": "run_complete",
                                "data": {"status": status}
                            }
                    
                    elif message["type"] == "logs":
                        # Log messages are not sent to frontend in current design
                        logger.debug(f"Received log message: {message}")
                    
        except Exception as e:
            logger.error(f"Error in Redis stream: {e}")
            yield {
                "event": "error",
                "data": {"message": str(e)}
            }
        finally:
            # Clean up background tasks
            redis_task.cancel()
            heartbeat_task.cancel()
            try:
                await redis_task
            except asyncio.CancelledError:
                pass
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
    
    # Import here to avoid circular import
    from sse_starlette.sse import EventSourceResponse
    
    return EventSourceResponse(event_generator())