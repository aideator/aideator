from typing import Optional
from datetime import datetime
import asyncio
import json

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
        logger.info(f"[REDIS-STREAM] Starting event generator for run {run_id}")
        
        # Use asyncio.Queue to merge Redis messages and heartbeats
        event_queue = asyncio.Queue()
        
        async def redis_listener():
            """Listen to Redis messages and put them in the queue."""
            logger.info(f"[REDIS-STREAM] Starting Redis listener for run {run_id}")
            try:
                logger.info(f"[REDIS-STREAM] Subscribing to Redis channels for run {run_id}")
                message_count = 0
                async for message in redis_service.subscribe_to_run(run_id):
                    message_count += 1
                    logger.info(f"[REDIS-STREAM] Received message #{message_count} from Redis: type={message.get('type')}, channel={message.get('channel')}")
                    logger.debug(f"[REDIS-STREAM] Message content: {message}")
                    await event_queue.put(("message", message))
                logger.info(f"[REDIS-STREAM] Redis subscription ended for run {run_id}")
            except Exception as e:
                logger.error(f"[REDIS-STREAM] Redis listener error for run {run_id}: {e}", exc_info=True)
                await event_queue.put(("error", str(e)))
        
        async def heartbeat_sender():
            """Send periodic heartbeats."""
            logger.info(f"[REDIS-STREAM] Starting heartbeat sender for run {run_id}")
            heartbeat_count = 0
            while True:
                await asyncio.sleep(30)
                heartbeat_count += 1
                logger.debug(f"[REDIS-STREAM] Sending heartbeat #{heartbeat_count} for run {run_id}")
                await event_queue.put(("heartbeat", None))
        
        # Start background tasks
        logger.info(f"[REDIS-STREAM] Starting background tasks for run {run_id}")
        redis_task = asyncio.create_task(redis_listener())
        heartbeat_task = asyncio.create_task(heartbeat_sender())
        
        try:
            logger.info(f"[REDIS-STREAM] Starting main event loop for run {run_id}")
            event_count = 0
            while True:
                logger.debug(f"[REDIS-STREAM] Waiting for next event for run {run_id}")
                event_type, data = await event_queue.get()
                event_count += 1
                logger.info(f"[REDIS-STREAM] Processing event #{event_count} for run {run_id}: type={event_type}")
                
                if event_type == "heartbeat":
                    logger.debug(f"[REDIS-STREAM] Yielding heartbeat event for run {run_id}")
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps({"timestamp": datetime.utcnow().isoformat()})
                    }
                
                elif event_type == "error":
                    logger.error(f"[REDIS-STREAM] Yielding error event for run {run_id}: {data}")
                    yield {
                        "event": "error",
                        "data": json.dumps({"message": data})
                    }
                    break
                
                elif event_type == "message":
                    message = data
                    logger.info(f"[REDIS-STREAM] Processing Redis message for run {run_id}: type={message.get('type')}, channel={message.get('channel')}")
                    logger.debug(f"[REDIS-STREAM] Full message data: {message}")
                    
                    # Convert Redis message to SSE format
                    if message["type"] == "output":
                        # Extract variation_id from channel
                        parts = message["channel"].split(":")
                        logger.debug(f"[REDIS-STREAM] Channel parts: {parts}")
                        if len(parts) >= 4:
                            variation_id = parts[3]
                            logger.info(f"[REDIS-STREAM] Extracted variation_id {variation_id} from channel")
                            data = message["data"]
                            content = data.get("content", "") if isinstance(data, dict) else str(data)
                            logger.debug(f"[REDIS-STREAM] Output content length: {len(content)} chars")
                            
                            logger.info(f"[REDIS-STREAM] Yielding agent_output event for run {run_id}, variation {variation_id}")
                            yield {
                                "event": "agent_output",
                                "data": json.dumps({
                                    "variation_id": variation_id,
                                    "content": content,
                                    "timestamp": data.get("timestamp") if isinstance(data, dict) else None
                                })
                            }
                    
                    elif message["type"] == "log":
                        # Extract variation_id from channel
                        parts = message["channel"].split(":")
                        logger.debug(f"[REDIS-STREAM] Log channel parts: {parts}")
                        if len(parts) >= 4:
                            variation_id = parts[3]
                            logger.info(f"[REDIS-STREAM] Extracted variation_id {variation_id} from log channel")
                            data = message["data"]
                            
                            logger.info(f"[REDIS-STREAM] Yielding agent_log event for run {run_id}, variation {variation_id}")
                            logger.info(f"[REDIS-STREAM] Log data structure: {data}")
                            logger.info(f"[REDIS-STREAM] Log data type: {type(data)}")
                            
                            # Send the log entry directly like kubectl does
                            event_data = {
                                "variation_id": variation_id,
                                **data  # Spread the log entry fields directly
                            }
                            logger.info(f"[REDIS-STREAM] Final event data: {event_data}")
                            
                            yield {
                                "event": "agent_log", 
                                "data": json.dumps(event_data)
                            }
                    
                    elif message["type"] == "status":
                        data = message["data"]
                        status = data.get("status", "unknown")
                        
                        if status == "variation_completed":
                            variation_id = data.get("metadata", {}).get("variation_id", 0)
                            yield {
                                "event": "agent_complete",
                                "data": json.dumps({"variation_id": variation_id})
                            }
                        elif status in ["completed", "failed"]:
                            yield {
                                "event": "run_complete",
                                "data": json.dumps({"status": status})
                            }
                    
                    elif message["type"] == "logs":
                        # Log messages are not sent to frontend in current design
                        logger.debug(f"Received log message: {message}")
                    
        except Exception as e:
            logger.error(f"[REDIS-STREAM] Critical error in event generator for run {run_id}: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)})
            }
        finally:
            # Clean up background tasks
            logger.info(f"[REDIS-STREAM] Cleaning up background tasks for run {run_id}")
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