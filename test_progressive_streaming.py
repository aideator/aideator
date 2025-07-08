#!/usr/bin/env python3
"""Test progressive streaming with Docker implementation"""

import asyncio
import json
import time
from datetime import datetime

import httpx


async def test_progressive_streaming():
    """Test that verifies true progressive streaming behavior."""
    print("\n🚀 PROGRESSIVE STREAMING TEST")
    print("=" * 80)
    
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=60.0) as client:
        # Create a run with a prompt that will output progressively
        print("\n📝 Creating run with progressive output prompt...")
        create_response = await client.post("/api/v1/runs", json={
            "github_url": "https://github.com/octocat/Hello-World",
            "prompt": "Count from 1 to 5, printing each number immediately with NO delay. Show timestamp for each.",
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
        print(f"\n⏱️  Streaming events (timestamps show when events arrive)...")
        print("-" * 80)
        
        events = []
        start_time = time.time()
        first_event_time = None
        last_event_time = start_time
        
        # Track event arrival pattern
        event_gaps = []
        
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
                        
                        if first_event_time is None:
                            first_event_time = current_time
                        
                        events.append({
                            "elapsed": elapsed,
                            "gap": gap,
                            "type": event_type,
                            "data": event_data
                        })
                        
                        if gap > 0.001:  # Only track meaningful gaps
                            event_gaps.append(gap)
                        
                        # Print event with timing info
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        if event_type == "agent_output":
                            content = event_data.get("content", "")
                            print(f"[{timestamp}] [{elapsed:6.2f}s] (+{gap:5.3f}s) 📤 {content}")
                        elif event_type == "agent_complete":
                            print(f"[{timestamp}] [{elapsed:6.2f}s] (+{gap:5.3f}s) ✅ Agent completed")
                        elif event_type == "run_complete":
                            print(f"[{timestamp}] [{elapsed:6.2f}s] (+{gap:5.3f}s) 🏁 Run complete")
                            break
                        elif event_type == "heartbeat":
                            print(f"[{timestamp}] [{elapsed:6.2f}s] (+{gap:5.3f}s) 💓 Heartbeat")
                            
                    except json.JSONDecodeError:
                        pass
        
        print("-" * 80)
        
        # Analyze streaming behavior
        print("\n📊 STREAMING ANALYSIS:")
        print(f"   Total events: {len(events)}")
        print(f"   Total duration: {events[-1]['elapsed'] if events else 0:.2f}s")
        
        if event_gaps:
            avg_gap = sum(event_gaps) / len(event_gaps)
            max_gap = max(event_gaps)
            min_gap = min(event_gaps)
            
            print(f"\n   Event timing:")
            print(f"   - Average gap between events: {avg_gap:.3f}s")
            print(f"   - Maximum gap: {max_gap:.3f}s")
            print(f"   - Minimum gap: {min_gap:.3f}s")
            
            # Count how many events came in "bursts" (gap < 0.1s)
            burst_events = sum(1 for gap in event_gaps if gap < 0.1)
            progressive_events = sum(1 for gap in event_gaps if gap >= 0.1)
            
            print(f"\n   Event distribution:")
            print(f"   - Progressive events (gap ≥ 0.1s): {progressive_events}")
            print(f"   - Burst events (gap < 0.1s): {burst_events}")
            
            # Determine streaming behavior
            print(f"\n   Streaming verdict:")
            if progressive_events > burst_events:
                print("   ✅ TRUE PROGRESSIVE STREAMING - Events arrive as they're generated")
                streaming_success = True
            elif max_gap > 1.0 and progressive_events > 0:
                print("   ⚠️  PARTIAL PROGRESSIVE STREAMING - Some events are progressive")
                streaming_success = True
            else:
                print("   ❌ BUFFERED STREAMING - Events arrive in bursts")
                streaming_success = False
        else:
            print("   ❌ No meaningful event gaps detected")
            streaming_success = False
        
        # Show event timeline visualization
        if events and len(events) > 2:
            print("\n   Event Timeline:")
            total_duration = events[-1]['elapsed']
            if total_duration > 0:
                for i, event in enumerate(events):
                    if event['type'] == 'agent_output':
                        # Create a visual timeline
                        position = int((event['elapsed'] / total_duration) * 50)
                        timeline = ['-'] * 50
                        timeline[position] = '●'
                        timeline_str = ''.join(timeline)
                        print(f"   {i:2d}: |{timeline_str}| {event['elapsed']:.2f}s")
        
        return streaming_success


async def main():
    """Run the progressive streaming test."""
    # Give server a moment to be ready
    await asyncio.sleep(1)
    
    success = await test_progressive_streaming()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 PROGRESSIVE STREAMING IS WORKING!")
    else:
        print("❌ PROGRESSIVE STREAMING NEEDS IMPROVEMENT")
    print("=" * 80)
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)