from typing import Optional
from datetime import datetime
import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.core.dependencies import CurrentUserAPIKey, get_current_user_from_api_key
from app.core.logging import get_logger
from app.core.config import get_settings
from app.models.run import Run
from app.models.user import User
from app.services.redis_service import redis_service

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()


@router.get(
    "/{run_id}/stream",
    summary="Stream agent outputs via Redis (currently disabled)",
    response_class=StreamingResponse,
    deprecated=True,
)
async def stream_run(
    run_id: str,
    current_user: CurrentUserAPIKey,
    db: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """
    Stream agent outputs via Redis pub/sub.
    
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
        "redis_stream_connection_started",
        run_id=run_id,
        variation_id=variation_id,
        user_id=current_user.id if current_user else None,
    )
    
    async def event_generator():
        """Generate SSE events from Redis pub/sub."""
        logger.info(f"[REDIS-STREAM] Starting event generator for run {run_id}")
        
        # Use asyncio.Queue to merge Redis messages and heartbeats
        event_queue = asyncio.Queue()
        
        async def redis_listener():
            """Listen to Redis messages and put them in the queue."""
            # Currently unused - using database polling instead
            logger.info(f"[REDIS-STREAM] Redis streaming disabled, using database polling")
            await event_queue.put(("error", "SSE streaming is deprecated. Please use the polling endpoint /api/v1/runs/{run_id}/outputs instead."))
            # logger.info(f"[REDIS-STREAM] Starting Redis listener for run {run_id}")
            # try:
            #     logger.info(f"[REDIS-STREAM] Subscribing to Redis channels for run {run_id}")
            #     message_count = 0
            #     async for message in redis_service.subscribe_to_run(run_id):
            #         message_count += 1
            #         logger.info(f"[REDIS-STREAM] Received message #{message_count} from Redis: type={message.get('type')}, channel={message.get('channel')}")
            #         await event_queue.put(("message", message))
            # except Exception as e:
            #     logger.error(f"[REDIS-STREAM] Redis listener error: {e}")
            #     await event_queue.put(("error", str(e)))
            # finally:
            #     logger.info(f"[REDIS-STREAM] Redis listener completed for run {run_id}")
            #     await event_queue.put(("complete", None))
        
        async def heartbeat_sender():
            """Send periodic heartbeats to keep connection alive."""
            try:
                while True:
                    await asyncio.sleep(30)
                    await event_queue.put(("heartbeat", None))
            except asyncio.CancelledError:
                logger.info(f"[REDIS-STREAM] Heartbeat sender cancelled for run {run_id}")
        
        # Start background tasks
        redis_task = asyncio.create_task(redis_listener())
        heartbeat_task = asyncio.create_task(heartbeat_sender())
        
        try:
            while True:
                # Wait for events from the queue
                event_type, data = await event_queue.get()
                
                if event_type == "complete":
                    logger.info(f"[REDIS-STREAM] Stream complete for run {run_id}")
                    break
                elif event_type == "error":
                    logger.error(f"[REDIS-STREAM] Stream error for run {run_id}: {data}")
                    yield f"event: error\ndata: {json.dumps({'error': data})}\n\n"
                    break
                elif event_type == "heartbeat":
                    yield f"event: heartbeat\ndata: {json.dumps({'timestamp': datetime.utcnow().isoformat()})}\n\n"
                elif event_type == "message":
                    message = data
                    logger.info(f"[REDIS-STREAM] Processing message type: {message['type']}")
                    
                    # Convert Redis message to SSE event
                    if message["type"] == "output":
                        # Extract variation_id from channel name
                        parts = message["channel"].split(":")
                        variation_id = parts[3] if len(parts) > 3 else "0"
                        
                        event_data = {
                            "variation_id": int(variation_id),
                            "content": message["data"]["content"],
                            "timestamp": message["data"].get("timestamp", datetime.utcnow().isoformat())
                        }
                        yield f"event: agent_output\ndata: {json.dumps(event_data)}\n\n"
                        
                    elif message["type"] == "logs":
                        # Extract variation_id from channel name
                        parts = message["channel"].split(":")
                        variation_id = parts[3] if len(parts) > 3 else "0"
                        
                        event_data = {
                            "variation_id": int(variation_id),
                            "log_entry": message["data"]
                        }
                        yield f"event: agent_log\ndata: {json.dumps(event_data)}\n\n"
                        
                    elif message["type"] == "status":
                        status_data = message["data"]
                        status = status_data.get("status", "")
                        
                        if status == "variation_completed":
                            variation_id = status_data.get("metadata", {}).get("variation_id", 0)
                            yield f"event: agent_complete\ndata: {json.dumps({'variation_id': variation_id})}\n\n"
                        elif status == "completed":
                            yield f"event: run_complete\ndata: {json.dumps({'status': 'completed'})}\n\n"
                        elif status == "failed":
                            yield f"event: run_complete\ndata: {json.dumps({'status': 'failed', 'error': status_data.get('metadata', {}).get('error', 'Unknown error')})}\n\n"
                    
        except asyncio.CancelledError:
            logger.info(f"[REDIS-STREAM] Event generator cancelled for run {run_id}")
        except Exception as e:
            logger.error(f"[REDIS-STREAM] Event generator error: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        finally:
            # Clean up tasks
            redis_task.cancel()
            heartbeat_task.cancel()
            await asyncio.gather(redis_task, heartbeat_task, return_exceptions=True)
            logger.info(f"[REDIS-STREAM] Event generator cleanup complete for run {run_id}")
    
    # Create SSE response
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*",  # CORS for SSE
        },
    )