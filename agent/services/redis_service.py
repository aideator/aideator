"""Redis service for publishing agent output and status updates."""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisService:
    """Handles all Redis communication for the agent."""
    
    def __init__(self, redis_url: str, run_id: str, variation_id: str):
        self.redis_url = redis_url
        self.run_id = run_id
        self.variation_id = variation_id
        self.client: Optional[redis.Redis] = None
        
    async def connect(self) -> None:
        """Initialize Redis connection."""
        try:
            logger.info(f"[AGENT-REDIS] Connecting to Redis at: {self.redis_url}")
            self.client = redis.from_url(self.redis_url, decode_responses=True)
            await self.client.ping()
            logger.info(f"[AGENT-REDIS] Connected successfully")
            
            # Test publish permissions
            test_channel = f"run:{self.run_id}:test"
            await self.client.publish(test_channel, "test")
            logger.info(f"[AGENT-REDIS] Test publish successful to channel: {test_channel}")
        except Exception as e:
            logger.error(f"[AGENT-REDIS] Failed to connect: {e}")
            raise RuntimeError(f"Failed to connect to Redis: {e}")
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            self.client = None
    
    async def publish_output(self, content: str) -> None:
        """Publish agent output to Redis."""
        if not self.client:
            logger.warning("[AGENT-REDIS] Cannot publish output - no client connection")
            return
            
        channel = f"run:{self.run_id}:output:{self.variation_id}"
        message = json.dumps({
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "variation_id": self.variation_id
        })
        
        try:
            result = await self.client.publish(channel, message)
            logger.info(f"[AGENT-REDIS] Published output to {channel} - {result} subscribers, content_length: {len(content)}")
        except Exception as e:
            logger.error(f"[AGENT-REDIS] Failed to publish output: {e}")
            # Don't fail if publish fails
            pass
    
    async def publish_status(self, status: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Publish status update to Redis."""
        if not self.client:
            logger.warning("[AGENT-REDIS] Cannot publish status - no client connection")
            return
            
        channel = f"run:{self.run_id}:status"
        message = json.dumps({
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "variation_id": self.variation_id,
            "metadata": metadata or {}
        })
        
        try:
            result = await self.client.publish(channel, message)
            logger.info(f"[AGENT-REDIS] Published status '{status}' to {channel} - {result} subscribers")
        except Exception as e:
            logger.error(f"[AGENT-REDIS] Failed to publish status: {e}")
            # Don't fail if publish fails
            pass
    
    async def publish_log(self, message: str, level: str = "INFO", **kwargs) -> None:
        """Publish log entry to Redis."""
        if not self.client:
            logger.warning("[AGENT-REDIS] Cannot publish log - no client connection")
            return
            
        channel = f"run:{self.run_id}:logs:{self.variation_id}"
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "run_id": self.run_id,
            "variation_id": self.variation_id,
            "level": level,
            "message": message,
            **kwargs
        }
        
        try:
            result = await self.client.publish(channel, json.dumps(log_entry))
            logger.info(f"[AGENT-REDIS] Published log to {channel} - {result} subscribers")
        except Exception as e:
            logger.error(f"[AGENT-REDIS] Failed to publish log: {e}")
            # Don't fail if publish fails
            pass