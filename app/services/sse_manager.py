"""
SSE Manager for streaming agent outputs to frontend clients.
"""

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import datetime

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class SSEManager:
    """Manages Server-Sent Events for streaming agent outputs."""

    def __init__(self):
        self._connections: dict[str, set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, run_id: str) -> AsyncGenerator[str, None]:
        """Connect a client to receive SSE events for a specific run."""
        queue = asyncio.Queue()

        async with self._lock:
            if run_id not in self._connections:
                self._connections[run_id] = set()
            self._connections[run_id].add(queue)

        logger.info(f"SSE client connected for run {run_id}")

        try:
            # Send initial connection event
            yield f"event: connected\ndata: {json.dumps({'run_id': run_id, 'timestamp': datetime.utcnow().isoformat()})}\n\n"

            # Send periodic heartbeats and handle events
            heartbeat_task = asyncio.create_task(self._heartbeat_sender(queue))

            while True:
                try:
                    # Wait for events with timeout for heartbeat
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event
                    queue.task_done()
                except TimeoutError:
                    # Heartbeat handled by heartbeat_task
                    continue
                except asyncio.CancelledError:
                    break

        except Exception as e:
            logger.error(f"SSE connection error for run {run_id}: {e}")
        finally:
            # Clean up connection
            heartbeat_task.cancel()
            async with self._lock:
                if run_id in self._connections:
                    self._connections[run_id].discard(queue)
                    if not self._connections[run_id]:
                        del self._connections[run_id]

            logger.info(f"SSE client disconnected for run {run_id}")

    async def _heartbeat_sender(self, queue: asyncio.Queue) -> None:
        """Send periodic heartbeat events."""
        try:
            while True:
                await asyncio.sleep(settings.sse_ping_interval)
                heartbeat_event = f"event: heartbeat\ndata: {json.dumps({'timestamp': datetime.utcnow().isoformat()})}\n\n"
                try:
                    queue.put_nowait(heartbeat_event)
                except asyncio.QueueFull:
                    # Queue is full, client may be slow
                    logger.warning("SSE queue full, skipping heartbeat")
        except asyncio.CancelledError:
            pass

    async def send_agent_output(
        self, run_id: str, variation_id: int, content: str
    ) -> None:
        """Send agent output to connected clients."""
        event_data = {
            "variation_id": variation_id,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }

        event = f"event: agent_output\ndata: {json.dumps(event_data)}\n\n"
        await self._broadcast_to_run(run_id, event)

    async def send_agent_error(
        self, run_id: str, variation_id: int, error: str
    ) -> None:
        """Send agent error to connected clients."""
        event_data = {
            "variation_id": variation_id,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        }

        event = f"event: agent_error\ndata: {json.dumps(event_data)}\n\n"
        await self._broadcast_to_run(run_id, event)

    async def send_agent_complete(self, run_id: str, variation_id: int) -> None:
        """Send agent completion event to connected clients."""
        event_data = {
            "variation_id": variation_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        event = f"event: agent_complete\ndata: {json.dumps(event_data)}\n\n"
        await self._broadcast_to_run(run_id, event)

    async def send_run_complete(self, run_id: str, status: str) -> None:
        """Send run completion event to connected clients."""
        event_data = {"status": status, "timestamp": datetime.utcnow().isoformat()}

        event = f"event: run_complete\ndata: {json.dumps(event_data)}\n\n"
        await self._broadcast_to_run(run_id, event)

    async def _broadcast_to_run(self, run_id: str, event: str) -> None:
        """Broadcast an event to all clients connected to a specific run."""
        async with self._lock:
            if run_id not in self._connections:
                return

            # Send to all connected clients for this run
            disconnected_queues = set()
            for queue in self._connections[run_id]:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    logger.warning(
                        f"SSE queue full for run {run_id}, client may be slow"
                    )
                    disconnected_queues.add(queue)
                except Exception as e:
                    logger.error(f"Error sending SSE event to client: {e}")
                    disconnected_queues.add(queue)

            # Clean up disconnected clients
            for queue in disconnected_queues:
                self._connections[run_id].discard(queue)

            if not self._connections[run_id]:
                del self._connections[run_id]

    def get_connection_count(self, run_id: str) -> int:
        """Get the number of connected clients for a run."""
        return len(self._connections.get(run_id, set()))

    def get_total_connections(self) -> int:
        """Get the total number of connected clients."""
        return sum(len(queues) for queues in self._connections.values())


# Global SSE manager instance
sse_manager = SSEManager()
