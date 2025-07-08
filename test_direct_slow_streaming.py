#!/usr/bin/env python3
"""Test progressive streaming directly with the slow agent."""

import asyncio
import json
import time
from datetime import datetime

from app.services.docker_service import DockerService


async def test_direct_slow_streaming():
    """Test the slow agent directly through DockerService."""
    print("\n🐳 DIRECT SLOW AGENT STREAMING TEST")
    print("=" * 60)
    
    docker_service = DockerService()
    
    # Build the image first
    print("Building agent image...")
    await docker_service.build_agent_image()
    
    print("\nStreaming slow agent output...")
    print("-" * 60)
    
    start_time = time.time()
    last_time = start_time
    line_count = 0
    
    # Stream output using the SLOW_AGENT_TEST prompt
    async for line in docker_service.stream_agent_output(
        repo_url="https://github.com/octocat/Hello-World",
        prompt="SLOW_AGENT_TEST: Count to 5 with 1 second delays",
        variation_id=0,
    ):
        current_time = time.time()
        elapsed = current_time - start_time
        gap = current_time - last_time
        last_time = current_time
        line_count += 1
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Highlight count lines
        if "Count:" in line:
            print(f"[{timestamp}] [{elapsed:5.2f}s] (+{gap:4.2f}s) 🔢 {line}")
        elif "ERROR:" in line:
            print(f"[{timestamp}] [{elapsed:5.2f}s] (+{gap:4.2f}s) ❌ {line}")
        else:
            print(f"[{timestamp}] [{elapsed:5.2f}s] (+{gap:4.2f}s) 📤 {line}")
    
    print("-" * 60)
    print(f"✅ Received {line_count} lines of output")
    print(f"✅ Total time: {time.time() - start_time:.2f}s")
    
    # Verify timing
    if line_count >= 6:  # Start, 5 counts, finish
        expected_time = 5.0  # Should take about 5 seconds
        actual_time = time.time() - start_time
        if 4.5 <= actual_time <= 6.0:
            print("✅ Timing is correct - true progressive streaming!")
        else:
            print(f"⚠️  Timing off - expected ~5s, got {actual_time:.2f}s")


async def main():
    """Run the direct streaming test."""
    await test_direct_slow_streaming()


if __name__ == "__main__":
    asyncio.run(main())