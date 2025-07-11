"""Redis pub/sub service for streaming agent outputs."""

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
    """Service for Redis pub/sub operations."""

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

    async def publish_agent_output(
        self, run_id: str, variation_id: str, content: str
    ) -> int:
        """Publish agent output to Redis channel.

        Args:
            run_id: The run ID
            variation_id: The variation ID
            content: The output content

        Returns:
            Number of subscribers that received the message
        """
        channel = f"run:{run_id}:output:{variation_id}"
        message = json.dumps(
            {
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "variation_id": variation_id,
            }
        )
        logger.info(
            f"[REDIS-SERVICE] Publishing to channel: {channel}, content_length: {len(content)}"
        )
        result = await self.client.publish(channel, message)
        logger.info(
            f"[REDIS-SERVICE] Published to {result} subscribers on channel: {channel}"
        )
        return result

    async def publish_agent_log(
        self, run_id: str, variation_id: str, log_entry: dict[str, Any]
    ) -> int:
        """Publish agent log to Redis channel.

        Args:
            run_id: The run ID
            variation_id: The variation ID
            log_entry: The log entry dictionary

        Returns:
            Number of subscribers that received the message
        """
        channel = f"run:{run_id}:logs:{variation_id}"
        message = json.dumps(log_entry)
        return await self.client.publish(channel, message)

    async def publish_status(
        self, run_id: str, status: str, metadata: dict[str, Any] | None = None
    ) -> int:
        """Publish run status update.

        Args:
            run_id: The run ID
            status: The status (running, completed, failed)
            metadata: Optional metadata

        Returns:
            Number of subscribers that received the message
        """
        channel = f"run:{run_id}:status"
        message = json.dumps(
            {
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
            }
        )
        return await self.client.publish(channel, message)

    async def subscribe_to_run(self, run_id: str) -> AsyncIterator[dict[str, Any]]:
        """Subscribe to all channels for a run.

        Args:
            run_id: The run ID to subscribe to

        Yields:
            Messages from the subscribed channels
        """
        logger.info(f"[REDIS-SUB] Starting subscription for run {run_id}")

        # Create a new pubsub client for this subscription to avoid concurrent access
        logger.info("[REDIS-SUB] Creating new pubsub client for this subscription")
        pubsub = self.client.pubsub()

        # Subscribe to all channels for this run
        pattern = f"run:{run_id}:*"
        logger.info(f"[REDIS-SUB] Subscribing to pattern: {pattern}")
        await pubsub.psubscribe(pattern)
        logger.info(f"[REDIS-SUB] Successfully subscribed to pattern: {pattern}")

        message_count = 0
        try:
            logger.info(
                f"[REDIS-SUB] Starting to listen for messages on pattern: {pattern}"
            )
            async for message in pubsub.listen():
                message_count += 1
                logger.debug(
                    f"[REDIS-SUB] Raw message #{message_count}: type={message.get('type')}, channel={message.get('channel')}"
                )

                if message["type"] == "pmessage":
                    # Parse channel to determine message type
                    channel = message["channel"]
                    parts = channel.split(":")
                    logger.debug(f"[REDIS-SUB] Channel parts: {parts}")

                    if len(parts) >= 3:
                        message_type = parts[2]  # output, logs, or status
                        logger.info(
                            f"[REDIS-SUB] Processing {message_type} message from channel: {channel}"
                        )

                        # Special logging for log messages
                        if message_type == "logs":
                            logger.info(
                                f"[REDIS-SUB] LOG MESSAGE RECEIVED on channel: {channel}"
                            )
                            logger.info(
                                f"[REDIS-SUB] Raw log data: {message['data'][:200]}..."
                            )

                        # Parse the data
                        try:
                            data = json.loads(message["data"])
                            logger.debug(f"[REDIS-SUB] Parsed JSON data: {data}")
                            if message_type == "logs":
                                logger.info(f"[REDIS-SUB] Parsed log data: {data}")
                        except json.JSONDecodeError:
                            # If not JSON, treat as plain text
                            logger.warning(
                                f"[REDIS-SUB] Failed to parse JSON, treating as plain text: {message['data']}"
                            )
                            data = {"content": message["data"]}

                        logger.info(
                            f"[REDIS-SUB] Yielding message: type={message_type}, channel={channel}"
                        )
                        yield {"type": message_type, "channel": channel, "data": data}
                elif message["type"] == "psubscribe":
                    logger.info(
                        f"[REDIS-SUB] Subscription confirmed for pattern: {message.get('pattern')}"
                    )
                else:
                    logger.debug(
                        f"[REDIS-SUB] Ignoring message type: {message.get('type')}"
                    )
        finally:
            logger.info(f"[REDIS-SUB] Unsubscribing from pattern: {pattern}")
            await pubsub.punsubscribe(pattern)
            logger.info(f"[REDIS-SUB] Unsubscribed from pattern: {pattern}")
            # Close the pubsub client to free resources
            await pubsub.close()
            logger.info(f"[REDIS-SUB] Closed pubsub client for run {run_id}")

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
