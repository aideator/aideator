#!/usr/bin/env python3
"""End-to-end test for Docker-based streaming"""

import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict

import httpx


async def test_e2e_docker_streaming():
    """Complete end-to-end test of Docker streaming functionality."""
    print("=" * 80)
    print("🧪 E2E TEST: Docker-based Real-time Streaming")
    print("=" * 80)
    
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=30.0) as client:
        # Step 1: Health check
        print("\n1️⃣  Checking API health...")
        health_response = await client.get("/api/v1/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        print(f"   ✅ API is {health_data['status']} (version {health_data['version']})")
        
        # Step 2: Create a run
        print("\n2️⃣  Creating agent run...")
        create_payload = {
            "github_url": "https://github.com/octocat/Hello-World",
            "prompt": "Analyze this repository and describe what you find. List all files.",
            "variations": 2,
            "agent_config": {
                "model": "claude-3-5-sonnet-20241022",  # Use non-deprecated model
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
        
        create_response = await client.post("/api/v1/runs", json=create_payload)
        assert create_response.status_code == 202
        run_data = create_response.json()
        run_id = run_data["run_id"]
        stream_url = run_data["stream_url"]
        
        print(f"   ✅ Run created: {run_id}")
        print(f"   📡 Stream URL: {stream_url}")
        
        # Step 3: Connect to SSE stream immediately
        print("\n3️⃣  Connecting to real-time stream...")
        print("-" * 80)
        
        events_received: List[Dict] = []
        agent_outputs: Dict[int, List[str]] = {0: [], 1: []}
        start_time = time.time()
        
        try:
            async with client.stream("GET", stream_url) as stream:
                async for line in stream.aiter_lines():
                    if line.startswith("event:"):
                        event_type = line[6:].strip()
                    elif line.startswith("data:"):
                        try:
                            event_data = json.loads(line[5:].strip())
                            elapsed = time.time() - start_time
                            
                            if event_type == "agent_output":
                                variation_id = event_data.get("variation_id", -1)
                                content = event_data.get("content", "")
                                agent_outputs[variation_id].append(content)
                                print(f"[{elapsed:5.1f}s] 🤖 Agent {variation_id}: {content}")
                                
                            elif event_type == "agent_complete":
                                variation_id = event_data.get("variation_id", -1)
                                print(f"[{elapsed:5.1f}s] ✅ Agent {variation_id} completed")
                                
                            elif event_type == "agent_error":
                                variation_id = event_data.get("variation_id", -1)
                                error = event_data.get("error", "Unknown error")
                                print(f"[{elapsed:5.1f}s] ❌ Agent {variation_id} error: {error}")
                                
                            elif event_type == "run_complete":
                                status = event_data.get("status", "unknown")
                                print(f"[{elapsed:5.1f}s] 🏁 Run completed with status: {status}")
                                break
                                
                            elif event_type == "heartbeat":
                                print(f"[{elapsed:5.1f}s] 💓 Heartbeat")
                            
                            events_received.append({
                                "time": elapsed,
                                "type": event_type,
                                "data": event_data
                            })
                            
                        except json.JSONDecodeError as e:
                            print(f"Failed to parse event data: {e}")
                            
        except asyncio.TimeoutError:
            print("\n⏱️  Stream timeout (this is normal for the test)")
        
        print("-" * 80)
        
        # Step 4: Analyze results
        print("\n4️⃣  Test Results:")
        print(f"   📊 Total events received: {len(events_received)}")
        print(f"   ⏱️  Total time: {time.time() - start_time:.1f}s")
        print(f"   🤖 Agent 0 output lines: {len(agent_outputs[0])}")
        print(f"   🤖 Agent 1 output lines: {len(agent_outputs[1])}")
        
        # Step 5: Verify real-time streaming
        print("\n5️⃣  Real-time Streaming Verification:")
        
        # Check if we got events
        if len(events_received) > 0:
            print("   ✅ Events were received")
        else:
            print("   ❌ No events received")
            
        # Check if we got agent outputs
        total_outputs = len(agent_outputs[0]) + len(agent_outputs[1])
        if total_outputs > 0:
            print(f"   ✅ Agent outputs received ({total_outputs} total lines)")
        else:
            print("   ❌ No agent outputs received")
            
        # Check event timing (events should be spread over time, not all at once)
        if len(events_received) > 2:
            time_spread = events_received[-1]["time"] - events_received[0]["time"]
            if time_spread > 1.0:  # At least 1 second spread
                print(f"   ✅ Events spread over {time_spread:.1f}s (real-time streaming)")
            else:
                print(f"   ⚠️  Events arrived within {time_spread:.1f}s (might be buffered)")
        
        # Step 6: Get run details
        print("\n6️⃣  Fetching run details...")
        run_response = await client.get(f"/api/v1/runs/{run_id}")
        if run_response.status_code == 200:
            run_details = run_response.json()
            print(f"   ✅ Run status: {run_details['status']}")
            print(f"   📅 Created at: {run_details['created_at']}")
        
        # Summary
        print("\n" + "=" * 80)
        print("📋 E2E TEST SUMMARY:")
        print("=" * 80)
        
        success_count = 0
        total_checks = 5
        
        # Check 1: API health
        if health_response.status_code == 200:
            print("✅ API health check passed")
            success_count += 1
        else:
            print("❌ API health check failed")
            
        # Check 2: Run creation
        if create_response.status_code == 202:
            print("✅ Run creation passed")
            success_count += 1
        else:
            print("❌ Run creation failed")
            
        # Check 3: Event streaming
        if len(events_received) > 0:
            print("✅ Event streaming passed")
            success_count += 1
        else:
            print("❌ Event streaming failed")
            
        # Check 4: Agent outputs
        if total_outputs > 0:
            print("✅ Agent execution passed")
            success_count += 1
        else:
            print("❌ Agent execution failed")
            
        # Check 5: Real-time behavior
        if len(events_received) > 2 and (events_received[-1]["time"] - events_received[0]["time"]) > 1.0:
            print("✅ Real-time streaming passed")
            success_count += 1
        else:
            print("❌ Real-time streaming failed")
        
        print(f"\n🎯 Overall: {success_count}/{total_checks} checks passed")
        
        if success_count == total_checks:
            print("🎉 All tests passed! Docker streaming is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
        
        return success_count == total_checks


if __name__ == "__main__":
    success = asyncio.run(test_e2e_docker_streaming())
    exit(0 if success else 1)