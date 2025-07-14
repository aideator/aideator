#!/usr/bin/env python3
"""Simple test to understand stdout behavior in async context."""

import asyncio
import sys
import json
from datetime import datetime

async def test_async_stdout():
    """Test stdout in async context."""
    print("=== STDOUT TEST START ===", flush=True)
    
    # Test regular print
    print("Regular print works", flush=True)
    
    # Test sys.stdout.write
    sys.stdout.write("sys.stdout.write works\n")
    sys.stdout.flush()
    
    # Test in async loop
    for i in range(3):
        print(f"Async loop iteration {i}", flush=True)
        sys.stdout.write(f"sys.stdout.write in loop {i}\n")
        sys.stdout.flush()
        await asyncio.sleep(0.1)
    
    # Test JSON output like agent does
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": "DEBUG",
        "message": "JSON test message"
    }
    print(json.dumps(log_entry), flush=True)
    
    print("=== STDOUT TEST END ===", flush=True)

if __name__ == "__main__":
    asyncio.run(test_async_stdout())