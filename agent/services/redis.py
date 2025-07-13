"""
Redis service - isolated for easy removal.

This service contains all Redis-related functionality and can be 
easily removed when transitioning to database-first architecture.
"""

import json
from datetime import datetime, UTC
from typing import Optional, Any, Dict

from agent.utils.errors import format_configuration_error, ConfigurationError


class RedisService:
    """Redis service for streaming - isolated for removal."""
    
    def __init__(self, config):
        """Initialize Redis service.
        
        Args:
            config: AgentConfig instance
        """
        self.config = config
        self.redis_client = None
        self.redis_url = config.redis_url
        
        if not self.redis_url:
            error_msg = format_configuration_error(
                "REDIS_URL", 
                "Redis URL is required for streaming functionality"
            )
            raise ConfigurationError(error_msg)
    
    async def connect(self) -> bool:
        """Connect to Redis.
        
        Returns:
            True if connection successful
        """
        try:
            import redis.asyncio as redis

            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            
            # Test stream access
            test_stream = f"run:{self.config.run_id}:test"
            test_id = await self.redis_client.xadd(test_stream, {"test": "connection"})
            
            # Clean up test stream
            await self.redis_client.delete(test_stream)
            
            return True
            
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            return False
    
    async def publish_output(self, content: str, variation_id: str) -> bool:
        """Publish agent output to Redis streams.
        
        Args:
            content: Output content
            variation_id: Agent variation ID
            
        Returns:
            True if successful
        """
        if not self.redis_client:
            return False
            
        try:
            stream_name = f"run:{self.config.run_id}:llm"
            fields = {
                "variation_id": variation_id,
                "content": content,
                "timestamp": datetime.now(UTC).isoformat(),
                "metadata": json.dumps({"content_length": len(content)}),
            }

            message_id = await self.redis_client.xadd(stream_name, fields)
            return True
            
        except Exception as e:
            print(f"❌ Failed to publish to Redis: {e}")
            return False
    
    async def publish_status(self, status: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Publish status update to Redis streams.
        
        Args:
            status: Status message
            metadata: Optional metadata dictionary
            
        Returns:
            True if successful
        """
        if not self.redis_client:
            return False
            
        try:
            stream_name = f"run:{self.config.run_id}:status"
            fields = {
                "status": status,
                "timestamp": datetime.now(UTC).isoformat(),
                "metadata": json.dumps(metadata or {}),
            }
            
            message_id = await self.redis_client.xadd(stream_name, fields)
            return True
            
        except Exception as e:
            print(f"❌ Failed to publish status to Redis: {e}")
            return False
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            try:
                await self.redis_client.close()
            except Exception as e:
                print(f"⚠️ Error closing Redis connection: {e}")


# NOTE: This entire service will be removed in the next pass
# when transitioning to database-first architecture.
# All functionality here is optional and duplicated in the database layer.