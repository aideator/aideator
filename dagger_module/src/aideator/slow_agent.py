#!/usr/bin/env python3
"""Slow agent for testing progressive streaming."""

import asyncio
import os
import sys
import time


async def main():
    """Simulate a slow agent that outputs progressively."""
    variation_id = int(os.environ.get("AGENT_VARIATION_ID", "0"))
    
    print(f"[Agent {variation_id}] Starting slow count to 5...")
    sys.stdout.flush()
    
    for i in range(1, 6):
        print(f"[Agent {variation_id}] Count: {i} (timestamp: {time.time():.3f})")
        sys.stdout.flush()
        await asyncio.sleep(1)  # 1 second delay between numbers
    
    print(f"[Agent {variation_id}] Finished counting!")
    sys.stdout.flush()


if __name__ == "__main__":
    asyncio.run(main())