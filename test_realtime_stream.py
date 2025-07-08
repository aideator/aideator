#!/usr/bin/env python3
"""Test real-time streaming with visible output."""

import asyncio
import json
import httpx
import sys
from datetime import datetime


async def test_realtime_streaming():
    """Test real-time streaming with a verbose agent."""
    print("🚀 Starting real-time streaming test...")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 50)
    
    async with httpx.AsyncClient() as client:
        # Create a run with a prompt that will generate output
        response = await client.post(
            "http://localhost:8000/api/v1/runs",
            json={
                "github_url": "https://github.com/octocat/Hello-World",
                "prompt": "Analyze this repository and list all files with their purposes. Be verbose and show your thinking process.",
                "variations": 2,  # Run 2 agents to see parallel output
                "use_claude_code": False,
            }
        )
        
        if response.status_code != 202:
            print(f"❌ Failed to create run: {response.status_code}")
            print(response.text)
            return
            
        data = response.json()
        run_id = data["run_id"]
        print(f"✅ Run created: {run_id}")
        print(f"📡 Connecting to stream: {data['stream_url']}")
        print("-" * 50)
        
        # Connect to SSE stream
        async with client.stream(
            "GET", 
            f"http://localhost:8000{data['stream_url']}",
            timeout=httpx.Timeout(timeout=120.0, connect=5.0)
        ) as stream:
            print("🔌 Connected! Waiting for agent output...\n")
            
            async for line in stream.aiter_lines():
                if line.startswith("event:"):
                    event_type = line[7:].strip()
                    if event_type != "heartbeat":  # Skip heartbeat events
                        print(f"\n📨 Event: {event_type}")
                        
                elif line.startswith("data:"):
                    try:
                        data = json.loads(line[6:])
                        
                        # Format output based on event type
                        if "content" in data:
                            # Agent output - show in real-time
                            variation_id = data.get('variation_id', 0)
                            content = data['content']
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            print(f"[{timestamp}] Agent {variation_id}: {content}")
                            
                        elif "error" in data:
                            # Error output
                            variation_id = data.get('variation_id', 0)
                            print(f"❌ Agent {variation_id} Error: {data['error']}")
                            
                        elif "status" in data:
                            # Completion status
                            print(f"\n✅ Run Status: {data['status']}")
                            
                    except json.JSONDecodeError:
                        pass  # Skip non-JSON data
                
                # Check for completion
                if line.startswith("event: run_complete"):
                    print("\n🎉 All agents completed!")
                    break
        
        print("\n" + "-" * 50)
        print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        print("📊 Streaming test completed")


if __name__ == "__main__":
    print("AIdeator Real-Time Streaming Demo")
    print("=" * 50)
    
    try:
        asyncio.run(test_realtime_streaming())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")