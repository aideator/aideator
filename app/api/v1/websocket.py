"""WebSocket endpoints for streaming agent outputs."""

import json
from typing import Any

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, WebSocketException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import get_current_user_from_websocket
from app.core.logging import get_logger
from app.models.run import Run
from app.models.user import User
from app.services.kubernetes_service import KubernetesService
from app.services.redis_service import redis_service

logger = get_logger(__name__)
router = APIRouter()


def format_stream_message(message: dict[str, Any]) -> dict[str, Any]:
    """Format a Redis Stream message for WebSocket transmission."""
    message_type = message["type"]
    message_id = message["message_id"]
    data = message["data"].copy()

    # Add message_id to data
    data["message_id"] = message_id

    # Parse metadata if it's a JSON string
    if "metadata" in data and isinstance(data["metadata"], str):
        try:
            data["metadata"] = json.loads(data["metadata"])
        except json.JSONDecodeError:
            # Keep as string if not valid JSON
            pass

    # Map stream types to WebSocket message types
    type_mapping = {
        "llm": "llm_output",
        "stdout": "stdout_log",
        "status": "status_update",
    }

    websocket_type = type_mapping.get(message_type, message_type)

    return {"type": websocket_type, "data": data}


async def get_websocket_user(
    websocket: WebSocket,
    api_key: str | None = Query(None),
    db: AsyncSession = Depends(get_session),
):
    """Get user from WebSocket query parameters."""
    logger.info(f"🔌 WebSocket authentication attempt with API key: {api_key[:10] + '...' if api_key else 'None'}")
    
    if not api_key:
        logger.warning("🔌 WebSocket authentication failed: No API key provided")
        raise WebSocketException(code=1008, reason="API key required")
    
    from app.core.auth import get_user_from_api_key
    try:
        user = await get_user_from_api_key(api_key, db)
        if not user or not user.is_active:
            logger.warning(f"🔌 WebSocket authentication failed: Invalid API key {api_key[:10] + '...'}")
            raise WebSocketException(code=1008, reason="Invalid API key")
        
        logger.info(f"🔌 WebSocket authentication successful for user: {user.email}")
        return user
    except Exception as e:
        logger.error(f"🔌 WebSocket authentication error: {e}")
        raise WebSocketException(code=1008, reason="Authentication failed")


@router.websocket("/ws/runs/{run_id}")
async def websocket_stream_run(
    websocket: WebSocket,
    run_id: str,
    current_user: User = Depends(get_websocket_user),
    db: AsyncSession = Depends(get_session),
):
    """
    WebSocket endpoint for streaming agent outputs.

    Streams both LLM output and stdout logs from Redis Streams.
    Supports bidirectional communication for control commands.
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for run {run_id} by user {current_user.id}")

    # Verify run exists and user has access
    query = select(Run).where(Run.id == run_id, Run.user_id == current_user.id)
    result = await db.execute(query)
    run = result.scalar_one_or_none()

    if not run:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Run not found"
        )
        return

    # Send initial connection confirmation
    await websocket.send_json(
        {
            "type": "connected",
            "data": {"run_id": run_id, "timestamp": "2024-01-01T00:00:00Z"},
        }
    )

    # Initialize Redis connection
    if not await redis_service.health_check():
        await websocket.close(
            code=status.WS_1011_INTERNAL_ERROR, reason="Redis unavailable"
        )
        return

    # Track last message IDs for resumption
    last_ids = {}

    try:
        # Start streaming task
        stream_task = None

        async def stream_messages():
            """Stream messages from Redis Streams to WebSocket."""
            try:
                async for message in redis_service.read_run_streams(run_id, last_ids):
                    # Update last_ids
                    stream_type = message["type"]
                    last_ids[stream_type] = message["message_id"]

                    # Send to WebSocket
                    await websocket.send_json(
                        {
                            "type": stream_type,
                            "message_id": message["message_id"],
                            "data": message["data"],
                        }
                    )

                    logger.debug(
                        f"Sent {stream_type} message to WebSocket: {message['message_id']}"
                    )

            except Exception as e:
                logger.error(f"Error streaming messages: {e}")
                await websocket.close(
                    code=status.WS_1011_INTERNAL_ERROR, reason="Stream error"
                )

        # Start streaming in background
        import asyncio

        stream_task = asyncio.create_task(stream_messages())

        # Handle incoming messages (control commands)
        while True:
            try:
                message = await websocket.receive_json()
                await handle_control_message(websocket, run_id, message)

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for run {run_id}")
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                break

    except Exception as e:
        logger.error(f"WebSocket error for run {run_id}: {e}")
    finally:
        # Clean up
        if stream_task:
            stream_task.cancel()
            try:
                await stream_task
            except asyncio.CancelledError:
                pass

        logger.info(f"WebSocket connection closed for run {run_id}")


async def handle_control_message(
    websocket: WebSocket, run_id: str, message: dict[str, Any]
) -> None:
    """Handle control messages from the client."""
    control_type = message.get("control")

    if control_type == "cancel":
        logger.info(f"Received cancel request for run {run_id}")

        try:
            # Cancel the Kubernetes job
            kubernetes_service = KubernetesService()
            await kubernetes_service.cancel_run(run_id)

            # Update status in Redis
            await redis_service.add_status_update(
                run_id, "cancelled", {"reason": "user_requested"}
            )

            # Send acknowledgment
            await websocket.send_json(
                {
                    "type": "control_ack",
                    "data": {
                        "control": "cancel",
                        "status": "success",
                        "run_id": run_id,
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error cancelling run {run_id}: {e}")
            await websocket.send_json(
                {
                    "type": "control_ack",
                    "data": {
                        "control": "cancel",
                        "status": "error",
                        "error": str(e),
                        "run_id": run_id,
                    },
                }
            )

    elif control_type == "ping":
        # Simple ping/pong for keepalive
        await websocket.send_json(
            {"type": "pong", "data": {"timestamp": "2024-01-01T00:00:00Z"}}
        )

    else:
        logger.warning(f"Unknown control message: {control_type}")
        await websocket.send_json(
            {
                "type": "error",
                "data": {"message": f"Unknown control type: {control_type}"},
            }
        )


@router.websocket("/ws/runs/{run_id}/debug")
async def websocket_debug_stream(
    websocket: WebSocket,
    run_id: str,
    variation_id: int = 0,
    current_user: User = Depends(get_websocket_user),
    db: AsyncSession = Depends(get_session),
):
    """
    WebSocket endpoint for debugging - streams only stdout logs.
    """
    await websocket.accept()
    logger.info(f"Debug WebSocket connected for run {run_id}, variation {variation_id} by user {current_user.id}")

    # Verify run exists and user has access
    query = select(Run).where(Run.id == run_id, Run.user_id == current_user.id)
    result = await db.execute(query)
    run = result.scalar_one_or_none()

    if not run:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Run not found"
        )
        return

    # Initialize Redis connection
    if not await redis_service.health_check():
        await websocket.close(
            code=status.WS_1011_INTERNAL_ERROR, reason="Redis unavailable"
        )
        return

    try:
        # Stream only stdout logs for this variation
        async for message in redis_service.read_run_streams(run_id, {"stdout": "0-0"}):
            if message["type"] == "stdout":
                # Filter by variation_id if specified
                if message["data"].get("variation_id") == str(variation_id):
                    await websocket.send_json(
                        {
                            "type": "stdout",
                            "message_id": message["message_id"],
                            "data": message["data"],
                        }
                    )

    except WebSocketDisconnect:
        logger.info(f"Debug WebSocket disconnected for run {run_id}")
    except Exception as e:
        logger.error(f"Debug WebSocket error for run {run_id}: {e}")
    finally:
        logger.info(f"Debug WebSocket connection closed for run {run_id}")
