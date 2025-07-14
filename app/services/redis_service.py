"""Redis Streams service for streaming agent outputs.

This service provides Redis Streams-based streaming for:
- LLM output (run:{id}:llm)
- Debug logs (run:{id}:stdout)
- Status updates (run:{id}:status)

Replaces the old pub/sub architecture for better performance and reliability.
"""

import json
import logging
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


class RedisService:
    """Service for Redis Streams operations."""

    def __init__(self):
        """Initialize Redis service."""
        self.redis_url = settings.redis_url or "redis://localhost:6379/0"
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self._client = redis.from_url(
                self.redis_url,
                decode_responses=settings.redis_decode_responses,
                password=settings.redis_password,
                db=settings.redis_db,
            )
            await self._client.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()

    @property
    def client(self) -> redis.Redis:
        """Get Redis client."""
        if not self._client:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._client

    async def add_llm_output(
        self,
        run_id: str,
        variation_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Add LLM output to Redis Stream.

        Args:
            run_id: The run ID
            variation_id: The variation ID
            content: The LLM output content
            metadata: Optional metadata (e.g., token count, model info)

        Returns:
            Stream message ID
        """
        stream_name = f"run:{run_id}:llm"
        fields = {
            "variation_id": variation_id,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": json.dumps(metadata or {}),
        }

        logger.info(
            f"[REDIS-STREAMS] Adding LLM output to stream: {stream_name}, content_length: {len(content)}"
        )

        message_id = await self.client.xadd(stream_name, fields)
        logger.info(
            f"[REDIS-STREAMS] Added LLM message {message_id} to stream: {stream_name}"
        )
        return message_id

    async def add_stdout_log(
        self, run_id: str, variation_id: str, log_line: str, level: str = "INFO"
    ) -> str:
        """Add stdout log to Redis Stream.

        Args:
            run_id: The run ID
            variation_id: The variation ID
            log_line: The stdout log line
            level: Log level (DEBUG, INFO, WARNING, ERROR)

        Returns:
            Stream message ID
        """
        stream_name = f"run:{run_id}:stdout"
        fields = {
            "variation_id": variation_id,
            "content": log_line,
            "level": level,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.debug(
            f"[REDIS-STREAMS] Adding stdout log to stream: {stream_name}, level: {level}"
        )

        message_id = await self.client.xadd(stream_name, fields)
        logger.debug(
            f"[REDIS-STREAMS] Added stdout message {message_id} to stream: {stream_name}"
        )
        return message_id

    async def add_status_update(
        self, run_id: str, status: str, metadata: dict[str, Any] | None = None
    ) -> str:
        """Add status update to Redis Stream.

        Args:
            run_id: The run ID
            status: The status (running, completed, failed, cancelled)
            metadata: Optional metadata

        Returns:
            Stream message ID
        """
        stream_name = f"run:{run_id}:status"
        fields = {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": json.dumps(metadata or {}),
        }

        logger.info(
            f"[REDIS-STREAMS] Adding status update to stream: {stream_name}, status: {status}"
        )

        message_id = await self.client.xadd(stream_name, fields)
        logger.info(
            f"[REDIS-STREAMS] Added status message {message_id} to stream: {stream_name}"
        )
        return message_id

    async def read_run_streams(
        self, run_id: str, last_ids: dict[str, str] | None = None, block: int = 5000
    ) -> AsyncIterator[dict[str, Any]]:
        """Read from all streams for a run.

        Args:
            run_id: The run ID to read from
            last_ids: Last message IDs for each stream (for resuming)
            block: Block timeout in milliseconds

        Yields:
            Messages from the streams
        """
        logger.info(f"[REDIS-STREAMS] Starting stream read for run {run_id}")

        # Define streams to read from
        streams = {
            f"run:{run_id}:llm": last_ids.get("llm", "0-0") if last_ids else "0-0",
            f"run:{run_id}:stdout": last_ids.get("stdout", "0-0")
            if last_ids
            else "0-0",
            f"run:{run_id}:status": last_ids.get("status", "0-0")
            if last_ids
            else "0-0",
        }
        
        # Add debug stream if requested
        if last_ids and "debug" in last_ids:
            streams[f"run:{run_id}:debug"] = last_ids.get("debug", "0-0")

        logger.info(f"[REDIS-STREAMS] Reading from streams: {streams}")

        try:
            while True:
                # Read from all streams
                messages = await self.client.xread(streams, block=block)

                if not messages:
                    # Timeout reached, continue to next iteration
                    continue

                for stream_name, stream_messages in messages:
                    # Determine stream type
                    stream_type = stream_name.split(":")[-1]  # llm, stdout, or status

                    for message_id, fields in stream_messages:
                        # Update last_id for this stream
                        streams[stream_name] = message_id

                        # Parse fields
                        parsed_data = {}
                        for key, value in fields.items():
                            if key == "metadata":
                                try:
                                    parsed_data[key] = json.loads(value)
                                except json.JSONDecodeError:
                                    parsed_data[key] = value
                            else:
                                parsed_data[key] = value

                        logger.debug(
                            f"[REDIS-STREAMS] Received message: stream={stream_type}, id={message_id}"
                        )

                        yield {
                            "type": stream_type,
                            "message_id": message_id,
                            "data": parsed_data,
                        }

        except Exception as e:
            logger.error(f"[REDIS-STREAMS] Error reading streams: {e}")
            raise

    async def trim_streams(self, run_id: str, max_length: int = 1000) -> None:
        """Trim streams to prevent memory buildup.

        Args:
            run_id: The run ID
            max_length: Maximum number of messages to keep per stream
        """
        streams = [
            f"run:{run_id}:llm", 
            f"run:{run_id}:stdout", 
            f"run:{run_id}:status",
            f"run:{run_id}:debug"
        ]

        for stream_name in streams:
            try:
                await self.client.xtrim(stream_name, maxlen=max_length)
                logger.debug(
                    f"[REDIS-STREAMS] Trimmed stream {stream_name} to {max_length} messages"
                )
            except Exception as e:
                logger.warning(
                    f"[REDIS-STREAMS] Failed to trim stream {stream_name}: {e}"
                )

    async def delete_run_streams(self, run_id: str) -> None:
        """Delete all streams for a run.

        Args:
            run_id: The run ID
        """
        streams = [
            f"run:{run_id}:llm", 
            f"run:{run_id}:stdout", 
            f"run:{run_id}:status",
            f"run:{run_id}:debug"
        ]

        for stream_name in streams:
            try:
                await self.client.delete(stream_name)
                logger.info(f"[REDIS-STREAMS] Deleted stream {stream_name}")
            except Exception as e:
                logger.warning(
                    f"[REDIS-STREAMS] Failed to delete stream {stream_name}: {e}"
                )

    async def add_debug_log(
        self, 
        run_id: str, 
        log_line: str, 
        source: str = "kubectl",
        is_json: bool = False,
        metadata: dict[str, Any] | None = None
    ) -> str:
        """Add debug log to Redis Stream.

        Args:
            run_id: The run ID
            log_line: The log line content
            source: Source of the log (kubectl, stdout, stderr)
            is_json: Whether the log line is JSON formatted
            metadata: Optional metadata

        Returns:
            Stream message ID
        """
        stream_name = f"run:{run_id}:debug"
        fields = {
            "content": log_line,
            "source": source,
            "is_json": str(is_json),
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": json.dumps(metadata or {}),
        }

        logger.debug(
            f"[REDIS-STREAMS] Adding debug log to stream: {stream_name}, source: {source}"
        )

        message_id = await self.client.xadd(stream_name, fields)
        logger.debug(
            f"[REDIS-STREAMS] Added debug message {message_id} to stream: {stream_name}"
        )
        return message_id

    async def get_stream_info(self, run_id: str) -> dict[str, Any]:
        """Get information about streams for a run.

        Args:
            run_id: The run ID

        Returns:
            Dictionary with stream information
        """
        streams = [
            f"run:{run_id}:llm", 
            f"run:{run_id}:stdout", 
            f"run:{run_id}:status",
            f"run:{run_id}:debug"
        ]

        info = {}
        for stream_name in streams:
            try:
                stream_info = await self.client.xinfo_stream(stream_name)
                info[stream_name] = {
                    "length": stream_info.get("length", 0),
                    "first_entry": stream_info.get("first-entry"),
                    "last_entry": stream_info.get("last-entry"),
                }
            except Exception as e:
                logger.warning(
                    f"[REDIS-STREAMS] Failed to get info for stream {stream_name}: {e}"
                )
                info[stream_name] = {"length": 0, "error": str(e)}

        return info

    async def health_check(self) -> bool:
        """Check if Redis is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Global Redis service instance
redis_service = RedisService()
