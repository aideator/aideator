#!/usr/bin/env python3
"""Test progressive streaming with a slow agent that counts with delays."""

import asyncio
import json
import time
from datetime import datetime

import httpx

from app.services.docker_service import DockerService


async def test_slow_agent_directly():
    """Test the slow agent directly through Docker to verify timing."""
    print("\n🐳 DIRECT DOCKER TEST - Slow Agent")
    print("=" * 60)
    
    docker_service = DockerService()
    
    # Build the image first
    print("Building agent image...")
    await docker_service.build_agent_image(force_rebuild=True)
    
    print("\nRunning slow agent with 1-second delays between outputs...")
    print("-" * 60)
    
    start_time = time.time()
    last_time = start_time
    
    # Create a simple script that runs the slow agent
    script_content = """#!/bin/sh
cd /app
exec python -u slow_agent.py
"""
    
    container = docker_service.client.containers.run(
        "aideator-agent:latest",
        command=["sh", "-c", script_content],
        environment={
            "PYTHONUNBUFFERED": "1",
            "AGENT_VARIATION_ID": "0",
        },
        detach=True,
        auto_remove=False,
    )
    
    # Stream logs
    log_stream = container.logs(stream=True, follow=True, stdout=True, stderr=True)
    
    try:
        for log_line in log_stream:
            current_time = time.time()
            elapsed = current_time - start_time
            gap = current_time - last_time
            last_time = current_time
            
            if isinstance(log_line, bytes):
                line = log_line.decode('utf-8').strip()
            else:
                line = str(log_line).strip()
            
            if line:
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[{timestamp}] [{elapsed:5.2f}s] (+{gap:4.2f}s) {line}")
        
        # Wait for container to finish
        exit_code = container.wait()["StatusCode"]
        print(f"\nContainer exited with code: {exit_code}")
        
    finally:
        container.remove(force=True)
    
    print("-" * 60)
    print("✅ Direct Docker test completed\n")


async def test_slow_streaming_api():
    """Test progressive streaming through the API with slow output."""
    print("\n🌐 API TEST - Progressive Streaming with Slow Agent")
    print("=" * 60)
    
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=60.0) as client:
        # Create a special run that uses the slow agent
        print("\n📝 Creating run with slow agent test...")
        
        # We'll use a special prompt that triggers slow behavior
        create_response = await client.post("/api/v1/runs", json={
            "github_url": "https://github.com/octocat/Hello-World",
            "prompt": "SLOW_AGENT_TEST: Count to 5 with 1 second delays",
            "variations": 1,
            "agent_config": {
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.7,
                "max_tokens": 500
            }
        })
        
        if create_response.status_code != 202:
            print(f"❌ Failed to create run: {create_response.status_code}")
            print(create_response.text)
            return False
        
        run_data = create_response.json()
        run_id = run_data["run_id"]
        stream_url = run_data["stream_url"]
        
        print(f"✅ Run created: {run_id}")
        print(f"\n⏱️  Streaming events (expect ~1 second gaps)...")
        print("-" * 60)
        
        events = []
        start_time = time.time()
        last_event_time = start_time
        
        async with client.stream("GET", stream_url) as stream:
            async for line in stream.aiter_lines():
                current_time = time.time()
                
                if line.startswith("event:"):
                    event_type = line[6:].strip()
                elif line.startswith("data:"):
                    try:
                        event_data = json.loads(line[5:].strip())
                        elapsed = current_time - start_time
                        gap = current_time - last_event_time
                        last_event_time = current_time
                        
                        events.append({
                            "elapsed": elapsed,
                            "gap": gap,
                            "type": event_type,
                            "data": event_data
                        })
                        
                        # Print event with timing info
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        if event_type == "agent_output":
                            content = event_data.get("content", "")
                            # Highlight count lines
                            if "Count:" in content:
                                print(f"[{timestamp}] [{elapsed:5.2f}s] (+{gap:4.2f}s) 🔢 {content}")
                            else:
                                print(f"[{timestamp}] [{elapsed:5.2f}s] (+{gap:4.2f}s) 📤 {content}")
                        elif event_type == "run_complete":
                            print(f"[{timestamp}] [{elapsed:5.2f}s] (+{gap:4.2f}s) 🏁 Run complete")
                            break
                            
                    except json.JSONDecodeError:
                        pass
        
        print("-" * 60)
        
        # Analyze timing of count events
        count_events = [e for e in events if e['type'] == 'agent_output' and 'Count:' in e['data'].get('content', '')]
        
        if len(count_events) >= 2:
            print("\n📊 COUNT EVENT TIMING ANALYSIS:")
            print(f"   Found {len(count_events)} count events")
            
            # Calculate gaps between count events
            count_gaps = []
            for i in range(1, len(count_events)):
                gap = count_events[i]['elapsed'] - count_events[i-1]['elapsed']
                count_gaps.append(gap)
                print(f"   Gap between count {i} and {i+1}: {gap:.2f}s")
            
            if count_gaps:
                avg_gap = sum(count_gaps) / len(count_gaps)
                print(f"\n   Average gap between counts: {avg_gap:.2f}s")
                
                # Check if gaps are close to 1 second
                if all(0.8 <= gap <= 1.2 for gap in count_gaps):
                    print("   ✅ Perfect 1-second delays between counts!")
                elif all(0.5 <= gap <= 1.5 for gap in count_gaps):
                    print("   ✅ Good timing - approximately 1 second between counts")
                else:
                    print("   ⚠️  Timing varies more than expected")
        
        return True


async def main():
    """Run all progressive streaming tests."""
    print("\n🧪 PROGRESSIVE STREAMING TEST SUITE")
    print("=" * 80)
    
    # Test 1: Direct Docker test
    await test_slow_agent_directly()
    
    # Give a moment between tests
    await asyncio.sleep(2)
    
    # Test 2: API streaming test
    await test_slow_streaming_api()
    
    print("\n" + "=" * 80)
    print("✅ All progressive streaming tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())