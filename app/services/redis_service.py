"""Redis pub/sub service for streaming agent outputs."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, AsyncIterator, Dict, Optional

import redis.asyncio as redis
from redis.asyncio.client import PubSub

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Service for Redis pub/sub operations."""
    
    def __init__(self):
        """Initialize Redis service."""
        self.redis_url = settings.redis_url or "redis://localhost:6379/0"
        self._client: Optional[redis.Redis] = None
        self._pubsub: Optional[PubSub] = None
        
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self._client = redis.from_url(
                self.redis_url,
                decode_responses=settings.redis_decode_responses,
                password=settings.redis_password,
                db=settings.redis_db
            )
            await self._client.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
            
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._pubsub:
            await self._pubsub.close()
        if self._client:
            await self._client.close()
            
    @property
    def client(self) -> redis.Redis:
        """Get Redis client."""
        if not self._client:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._client
        
    async def publish_agent_output(
        self, 
        run_id: str, 
        variation_id: str, 
        content: str
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
        message = json.dumps({
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "variation_id": variation_id
        })
        return await self.client.publish(channel, message)
        
    async def publish_agent_log(
        self, 
        run_id: str, 
        variation_id: str, 
        log_entry: Dict[str, Any]
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
        self, 
        run_id: str, 
        status: str,
        metadata: Optional[Dict[str, Any]] = None
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
        message = json.dumps({
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        })
        return await self.client.publish(channel, message)
        
    async def subscribe_to_run(
        self, 
        run_id: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """Subscribe to all channels for a run.
        
        Args:
            run_id: The run ID to subscribe to
            
        Yields:
            Messages from the subscribed channels
        """
        if not self._pubsub:
            self._pubsub = self.client.pubsub()
            
        # Subscribe to all channels for this run
        pattern = f"run:{run_id}:*"
        await self._pubsub.psubscribe(pattern)
        
        try:
            async for message in self._pubsub.listen():
                if message["type"] == "pmessage":
                    # Parse channel to determine message type
                    channel = message["channel"]
                    parts = channel.split(":")
                    
                    if len(parts) >= 3:
                        message_type = parts[2]  # output, logs, or status
                        
                        # Parse the data
                        try:
                            data = json.loads(message["data"])
                        except json.JSONDecodeError:
                            # If not JSON, treat as plain text
                            data = {"content": message["data"]}
                            
                        yield {
                            "type": message_type,
                            "channel": channel,
                            "data": data
                        }
        finally:
            await self._pubsub.punsubscribe(pattern)
            
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