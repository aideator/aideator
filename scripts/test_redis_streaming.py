#!/usr/bin/env python3
"""Test script for Redis streaming implementation."""

import asyncio
import json
import redis
import httpx
from datetime import datetime

async def test_redis_streaming():
    """Test Redis pub/sub streaming."""
    print("🔍 Testing Redis Streaming Implementation\n")
    
    # 1. Test Redis connection
    print("1️⃣ Testing Redis connection...")
    try:
        r = redis.from_url("redis://localhost:6379", decode_responses=True)
        r.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return
    
    # 2. Test API health endpoint
    print("\n2️⃣ Testing API health endpoint...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/health")
            health_data = response.json()
            print(f"✅ API health: {health_data}")
            print(f"   Redis status: {health_data.get('redis', 'unknown')}")
        except Exception as e:
            print(f"❌ API health check failed: {e}")
    
    # 3. Create a test run
    print("\n3️⃣ Creating test run...")
    test_run_id = f"test-redis-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # 4. Publish test messages to Redis
    print(f"\n4️⃣ Publishing test messages to Redis (run_id: {test_run_id})...")
    
    # Publish status
    channel = f"run:{test_run_id}:status"
    message = json.dumps({
        "status": "starting",
        "timestamp": datetime.utcnow().isoformat()
    })
    subscribers = r.publish(channel, message)
    print(f"   Published to {channel}: {subscribers} subscribers")
    
    # Publish some output
    for i in range(3):
        variation_id = i
        channel = f"run:{test_run_id}:output:{variation_id}"
        message = json.dumps({
            "content": f"Test message {i+1} from variation {variation_id}",
            "timestamp": datetime.utcnow().isoformat(),
            "variation_id": str(variation_id)
        })
        subscribers = r.publish(channel, message)
        print(f"   Published to {channel}: {subscribers} subscribers")
        await asyncio.sleep(0.5)
    
    # Publish completion
    for i in range(3):
        channel = f"run:{test_run_id}:status"
        message = json.dumps({
            "status": "variation_completed",
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"variation_id": i}
        })
        r.publish(channel, message)
    
    # 5. Test SSE endpoints
    print(f"\n5️⃣ Testing SSE endpoints...")
    print("   To test SSE streaming, run these commands in separate terminals:")
    print(f"   kubectl: curl -N http://localhost:8000/api/v1/runs/{test_run_id}/stream")
    print(f"   Redis:   curl -N http://localhost:8000/api/v1/runs/{test_run_id}/stream/redis")
    
    # 6. Monitor Redis channels
    print(f"\n6️⃣ To monitor Redis channels in real-time:")
    print(f"   redis-cli psubscribe 'run:{test_run_id}:*'")
    
    print("\n✅ Redis streaming test complete!")

if __name__ == "__main__":
    asyncio.run(test_redis_streaming())