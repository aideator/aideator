#!/usr/bin/env python3
"""Validate that streaming is truly real-time"""

import asyncio
import json
import time
from datetime import datetime

import httpx


async def validate_realtime_streaming():
    """Test that demonstrates real-time streaming with time measurements."""
    print("\n🔬 REAL-TIME STREAMING VALIDATION TEST")
    print("=" * 60)
    
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=30.0) as client:
        # Create a run
        print("\n📝 Creating run with slow agent prompt...")
        create_response = await client.post("/api/v1/runs", json={
            "github_url": "https://github.com/octocat/Hello-World",
            "prompt": "Count to 5 slowly, pausing 1 second between each number",
            "variations": 1,
            "agent_config": {
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.7,
                "max_tokens": 500
            }
        })
        
        run_data = create_response.json()
        run_id = run_data["run_id"]
        stream_url = run_data["stream_url"]
        
        print(f"✅ Run created: {run_id}")
        print(f"\n⏱️  Monitoring event timing...")
        print("-" * 60)
        
        events = []
        start_time = time.time()
        first_event_time = None
        
        async with client.stream("GET", stream_url) as stream:
            async for line in stream.aiter_lines():
                if line.startswith("event:"):
                    event_type = line[6:].strip()
                elif line.startswith("data:"):
                    event_data = json.loads(line[5:].strip())
                    current_time = time.time()
                    elapsed = current_time - start_time
                    
                    if first_event_time is None:
                        first_event_time = current_time
                    
                    events.append({
                        "elapsed": elapsed,
                        "type": event_type,
                        "data": event_data
                    })
                    
                    # Print timing info
                    if event_type == "agent_output":
                        content = event_data.get("content", "")
                        print(f"[{elapsed:6.2f}s] 📤 {content[:60]}...")
                    elif event_type == "run_complete":
                        print(f"[{elapsed:6.2f}s] 🏁 Run complete")
                        break
        
        print("-" * 60)
        
        # Analyze timing
        print("\n📊 TIMING ANALYSIS:")
        print(f"   Total events: {len(events)}")
        print(f"   Total duration: {events[-1]['elapsed']:.2f}s")
        
        if len(events) > 2:
            # Calculate time between events
            gaps = []
            for i in range(1, len(events)):
                gap = events[i]['elapsed'] - events[i-1]['elapsed']
                gaps.append(gap)
            
            avg_gap = sum(gaps) / len(gaps)
            max_gap = max(gaps)
            
            print(f"   Average time between events: {avg_gap:.3f}s")
            print(f"   Max time between events: {max_gap:.3f}s")
            
            # Check if events are spread out
            if max_gap > 0.5:
                print("   ✅ Events are spread over time (REAL-TIME)")
            else:
                print("   ❌ Events arrived too quickly (BUFFERED)")
        
        return len(events) > 0


if __name__ == "__main__":
    asyncio.run(validate_realtime_streaming())