import asyncio
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Dict, Optional, Set

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class EventType(str, Enum):
    """SSE event types."""

    AGENT_OUTPUT = "agent_output"
    AGENT_ERROR = "agent_error"
    AGENT_COMPLETE = "agent_complete"
    RUN_COMPLETE = "run_complete"
    HEARTBEAT = "heartbeat"
    AGENT_LOG = "agent_log"


@dataclass
class SSEEvent:
    """Server-Sent Event data structure."""

    event_type: EventType
    data: Dict[str, Any]
    id: Optional[str] = None
    retry: Optional[int] = None

    def format(self) -> str:
        """Format event for SSE protocol."""
        lines = []

        if self.id:
            lines.append(f"id: {self.id}")

        lines.append(f"event: {self.event_type.value}")

        if self.retry:
            lines.append(f"retry: {self.retry}")

        lines.append(f"data: {json.dumps(self.data)}")
        lines.append("")  # Empty line to signal end of event

        return "\n".join(lines) + "\n"


class SSEManager:
    """Manages Server-Sent Events connections and broadcasting."""

    def __init__(self):
        self._connections: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        self._event_counter = 0
        self._lock = asyncio.Lock()

    async def connect(self, run_id: str) -> AsyncIterator[str]:
        """Connect a client to receive events for a run."""
        queue: asyncio.Queue[Optional[SSEEvent]] = asyncio.Queue(maxsize=100)

        async with self._lock:
            self._connections[run_id].add(queue)
            connection_count = len(self._connections[run_id])

        logger.info(
            "sse_client_connected",
            run_id=run_id,
            total_connections=connection_count,
        )

        try:
            # Send initial connection event
            await queue.put(
                SSEEvent(
                    event_type=EventType.HEARTBEAT,
                    data={
                        "message": "Connected to event stream",
                        "run_id": run_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    retry=settings.sse_retry_timeout,
                )
            )

            # Start heartbeat task
            heartbeat_task = asyncio.create_task(self._heartbeat(queue))

            # Yield events
            while True:
                try:
                    event = await asyncio.wait_for(
                        queue.get(), timeout=settings.sse_ping_interval * 2
                    )

                    if event is None:  # Disconnect signal
                        break

                    yield event.format()

                except asyncio.TimeoutError:
                    # Connection might be stale
                    logger.warning("sse_connection_timeout", run_id=run_id)
                    break

        finally:
            heartbeat_task.cancel()
            async with self._lock:
                self._connections[run_id].discard(queue)
                if not self._connections[run_id]:
                    del self._connections[run_id]

            logger.info("sse_client_disconnected", run_id=run_id)

    async def broadcast(self, run_id: str, event: SSEEvent) -> None:
        """Broadcast an event to all connected clients for a run."""
        async with self._lock:
            connections = list(self._connections.get(run_id, []))
            self._event_counter += 1
            event.id = str(self._event_counter)

        if not connections:
            logger.debug("no_sse_connections", run_id=run_id)
            return

        # Send to all connected clients
        disconnected = []
        for queue in connections:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("sse_queue_full", run_id=run_id)
                disconnected.append(queue)

        # Clean up disconnected clients
        if disconnected:
            async with self._lock:
                for queue in disconnected:
                    self._connections[run_id].discard(queue)

    async def send_agent_output(
        self, run_id: str, variation_id: int, content: str
    ) -> None:
        """Send agent output event."""
        event = SSEEvent(
            event_type=EventType.AGENT_OUTPUT,
            data={
                "variation_id": variation_id,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        await self.broadcast(run_id, event)

    async def send_agent_error(
        self, run_id: str, variation_id: int, error: str
    ) -> None:
        """Send agent error event."""
        event = SSEEvent(
            event_type=EventType.AGENT_ERROR,
            data={
                "variation_id": variation_id,
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        await self.broadcast(run_id, event)

    async def send_agent_log(self, run_id: str, variation_id: int, log_entry: dict) -> None:
        """Send agent log event."""
        event = SSEEvent(
            event_type=EventType.AGENT_LOG,
            data={
                "variation_id": variation_id,
                "log": log_entry,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        await self.broadcast(run_id, event)

    async def send_agent_complete(self, run_id: str, variation_id: int) -> None:
        """Send agent completion event."""
        event = SSEEvent(
            event_type=EventType.AGENT_COMPLETE,
            data={
                "variation_id": variation_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        await self.broadcast(run_id, event)

    async def send_run_complete(self, run_id: str, status: str) -> None:
        """Send run completion event."""
        event = SSEEvent(
            event_type=EventType.RUN_COMPLETE,
            data={
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        await self.broadcast(run_id, event)

        # Disconnect all clients after a delay
        await asyncio.sleep(5)
        await self.disconnect_all(run_id)

    async def disconnect_all(self, run_id: str) -> None:
        """Disconnect all clients for a run."""
        async with self._lock:
            connections = list(self._connections.get(run_id, []))

        for queue in connections:
            try:
                await queue.put(None)  # Disconnect signal
            except asyncio.QueueFull:
                pass

    async def _heartbeat(self, queue: asyncio.Queue) -> None:
        """Send periodic heartbeat events."""
        while True:
            try:
                await asyncio.sleep(settings.sse_ping_interval)
                event = SSEEvent(
                    event_type=EventType.HEARTBEAT,
                    data={
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
                queue.put_nowait(event)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break


# Global SSE manager instance
sse_manager = SSEManager()