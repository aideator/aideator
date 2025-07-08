#!/usr/bin/env python3
"""Test streaming by pre-connecting before agents start."""

import asyncio
import json
import httpx
from datetime import datetime


async def test_streaming_with_preconnect():
    """Create run and connect to stream in parallel."""
    print("🚀 Real-Time Streaming Test (Pre-connect)")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        # Step 1: Create the run
        print("Creating run...")
        response = await client.post(
            "http://localhost:8000/api/v1/runs",
            json={
                "github_url": "https://github.com/octocat/Hello-World",
                "prompt": "Analyze each file in detail and suggest improvements",
                "variations": 2,
            }
        )
        
        data = response.json()
        run_id = data["run_id"]
        stream_url = f"http://localhost:8000{data['stream_url']}"
        
        print(f"✓ Run created: {run_id}")
        print(f"⚡ Connecting to stream IMMEDIATELY...")
        print("-" * 50)
        
        # Step 2: Connect to stream WITHOUT DELAY
        # This ensures we catch all output from the beginning
        async with client.stream("GET", stream_url) as stream:
            event_count = 0
            start_time = datetime.now()
            
            async for line in stream.aiter_lines():
                current_time = datetime.now()
                elapsed = (current_time - start_time).total_seconds()
                
                if line.startswith("event:"):
                    event_type = line[7:].strip()
                    if event_type != "heartbeat":
                        print(f"\n[{elapsed:.1f}s] 📨 {line}")
                        
                elif line.startswith("data:"):
                    try:
                        data = json.loads(line[6:])
                        
                        if "content" in data:
                            # Real-time agent output
                            variation_id = data.get('variation_id', 0)
                            content = data['content']
                            print(f"[{elapsed:.1f}s] Agent {variation_id}: {content}")
                            
                        elif "error" in data:
                            print(f"[{elapsed:.1f}s] ❌ Error: {data['error']}")
                            
                    except json.JSONDecodeError:
                        pass
                
                event_count += 1
                
                # Check for completion
                if "event: run_complete" in line:
                    print(f"\n[{elapsed:.1f}s] ✅ Run completed!")
                    break
                    
                # Safety limit
                if event_count > 500:
                    print(f"\n[{elapsed:.1f}s] Reached event limit")
                    break
        
        print("-" * 50)
        print(f"Total time: {elapsed:.1f} seconds")
        print(f"Total events: {event_count}")


if __name__ == "__main__":
    try:
        asyncio.run(test_streaming_with_preconnect())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")