#!/usr/bin/env python3
"""Test streaming functionality with proper termination."""

import asyncio
import json
import sys
import httpx
import signal


async def test_streaming():
    """Test creating a run and streaming its output."""
    print("Creating test run...")
    
    async with httpx.AsyncClient() as client:
        # Create a run with a simple prompt
        response = await client.post(
            "http://localhost:8000/api/v1/runs",
            json={
                "github_url": "https://github.com/octocat/Hello-World",
                "prompt": "List all files in the repository",
                "variations": 1,
                "use_claude_code": False,
            }
        )
        
        if response.status_code != 202:
            print(f"Failed to create run: {response.status_code}")
            print(response.text)
            return
            
        data = response.json()
        run_id = data["run_id"]
        stream_url = data["stream_url"]
        print(f"Run created: {run_id}")
        print(f"Stream URL: {stream_url}")
        
        # Connect to SSE stream with timeout
        print("\nConnecting to stream...")
        timeout = 10  # 10 second timeout for faster testing
        
        async with client.stream(
            "GET", 
            f"http://localhost:8000{stream_url}",
            timeout=httpx.Timeout(timeout=timeout, connect=5.0)
        ) as stream:
            try:
                event_count = 0
                async for line in stream.aiter_lines():
                    if line.startswith("event:"):
                        event_type = line[7:].strip()
                        print(f"\nEvent: {event_type}")
                    elif line.startswith("data:"):
                        try:
                            data = json.loads(line[6:])
                            if "content" in data:
                                print(f"[Variation {data.get('variation_id', 0)}] {data['content']}")
                            else:
                                print(f"Data: {json.dumps(data, indent=2)}")
                        except json.JSONDecodeError:
                            print(f"Raw data: {line[6:]}")
                    
                    event_count += 1
                    
                    # Check for completion events
                    if line.startswith("event: run_complete"):
                        print("\nRun completed!")
                        break
                        
                    # Safety limit to prevent infinite streaming
                    if event_count > 200:
                        print("\nReached event limit, stopping...")
                        break
                        
            except asyncio.TimeoutError:
                print(f"\nStream timeout after {timeout} seconds")
            except Exception as e:
                print(f"\nStream error: {e}")
        
        print("\nStreaming test completed")


def signal_handler(signum, frame):
    print("\nInterrupted, exiting...")
    sys.exit(0)


if __name__ == "__main__":
    # Set up signal handler for clean exit
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        asyncio.run(test_streaming())
    except KeyboardInterrupt:
        print("\nTest interrupted")