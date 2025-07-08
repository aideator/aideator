#!/usr/bin/env python3
"""Test Docker streaming with real-time output"""

import asyncio
import json
from datetime import datetime

import httpx


async def test_docker_streaming():
    """Test creating a run and streaming output via Docker."""
    print(f"[{datetime.now()}] Starting Docker streaming test...")
    
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Create a run
        print(f"\n[{datetime.now()}] Creating run...")
        response = await client.post("/api/v1/runs", json={
            "github_url": "https://github.com/octocat/Hello-World",
            "prompt": "Test Docker streaming - analyze the README",
            "variations": 2,
        })
        
        if response.status_code != 202:
            print(f"Failed to create run: {response.status_code} - {response.text}")
            return
            
        data = response.json()
        run_id = data["run_id"]
        stream_url = data["stream_url"]
        
        print(f"[{datetime.now()}] Run created: {run_id}")
        print(f"[{datetime.now()}] Connecting to stream: {stream_url}")
        
        # Connect to SSE stream
        print(f"\n[{datetime.now()}] Streaming events:")
        print("-" * 80)
        
        async with client.stream("GET", stream_url, timeout=60.0) as stream:
            event_count = 0
            async for line in stream.aiter_lines():
                if line.startswith("event:"):
                    event_type = line[6:].strip()
                elif line.startswith("data:"):
                    event_data = json.loads(line[5:].strip())
                    timestamp = datetime.now()
                    
                    if event_type == "agent_output":
                        variation_id = event_data.get("variation_id", "?")
                        content = event_data.get("content", "")
                        print(f"[{timestamp}] [Agent {variation_id}] {content}")
                    elif event_type == "agent_complete":
                        variation_id = event_data.get("variation_id", "?")
                        print(f"[{timestamp}] [Agent {variation_id}] ✅ Complete")
                    elif event_type == "error":
                        print(f"[{timestamp}] ❌ Error: {event_data}")
                    elif event_type == "run_complete":
                        print(f"[{timestamp}] 🏁 Run complete: {event_data}")
                        break
                    elif event_type == "heartbeat":
                        print(f"[{timestamp}] 💓 Heartbeat")
                    
                    event_count += 1
        
        print("-" * 80)
        print(f"\n[{datetime.now()}] Stream ended. Total events: {event_count}")


if __name__ == "__main__":
    asyncio.run(test_docker_streaming())