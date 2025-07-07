#!/usr/bin/env python3
"""Test script for the refactored AIdeator implementation."""

import asyncio
import httpx
import json
import os
from datetime import datetime


async def test_server_health():
    """Test that the server is running independently of Dagger."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/health")
        print(f"Health check response: {response.status_code}")
        print(f"Response data: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200


async def test_create_run():
    """Test creating a run with the new architecture."""
    # Ensure we have the API key set
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY not set in environment")
        return False
    
    async with httpx.AsyncClient() as client:
        # Create a test run
        run_data = {
            "github_url": "https://github.com/fastapi/fastapi",
            "prompt": "Analyze the main FastAPI application structure and suggest improvements",
            "variations": 2,
            "agent_config": {
                "model": "claude-3-opus-20240229",
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
        
        response = await client.post(
            "http://localhost:8000/api/v1/runs",
            json=run_data,
            timeout=30.0
        )
        
        print(f"Create run response: {response.status_code}")
        if response.status_code == 202:
            data = response.json()
            print(f"Run ID: {data['run_id']}")
            print(f"Stream URL: {data['stream_url']}")
            return data
        else:
            print(f"Error: {response.text}")
            return None


async def test_stream_output(stream_url: str):
    """Test streaming SSE output."""
    print(f"\nConnecting to stream: {stream_url}")
    
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", f"http://localhost:8000{stream_url}") as response:
            print("Streaming agent outputs...")
            event_count = 0
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_count += 1
                    data = json.loads(line[6:])
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Event {event_count}: {data.get('type', 'unknown')}")
                    
                    if data.get("type") == "agent_output":
                        print(f"  Agent {data.get('variation_id')}: {data.get('content', '')[:100]}...")
                    elif data.get("type") == "run_complete":
                        print(f"  Run completed with status: {data.get('status')}")
                        break
                    
                    # Limit output for testing
                    if event_count > 20:
                        print("  (limiting output for test...)")
                        break


async def test_dagger_module():
    """Test the Dagger module directly."""
    print("\nTesting Dagger module directly...")
    
    # Check if Dagger CLI is available
    import subprocess
    try:
        result = subprocess.run(
            ["dagger", "version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Dagger version: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Dagger CLI not found. Please install Dagger to test module functionality.")
        return False
    
    # Test a simple module function
    try:
        result = subprocess.run(
            [
                "dagger", "call",
                "-m", "./dagger_module",
                "run-agent",
                "--repo-url", "https://github.com/fastapi/fastapi",
                "--prompt", "List the main files in this repository",
                "--anthropic-api-key", f"env:ANTHROPIC_API_KEY",
                "--variation-id", "0",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        
        if result.returncode == 0:
            print("Dagger module test successful!")
            print(f"Output preview: {result.stdout[:200]}...")
            return True
        else:
            print(f"Dagger module test failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("Dagger module test timed out")
        return False
    except Exception as e:
        print(f"Dagger module test error: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Refactored AIdeator Implementation")
    print("=" * 60)
    
    # Test 1: Server health
    print("\n1. Testing server health (independent of Dagger)...")
    health_ok = await test_server_health()
    
    if not health_ok:
        print("Server is not running. Please start it with: uvicorn app.main:app --reload")
        return
    
    # Test 2: Create run
    print("\n2. Testing run creation...")
    run_data = await test_create_run()
    
    if run_data:
        # Test 3: Stream output
        print("\n3. Testing SSE streaming...")
        await test_stream_output(run_data["stream_url"])
    
    # Test 4: Dagger module
    print("\n4. Testing Dagger module...")
    await test_dagger_module()
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("- Server runs independently: ✓")
    print("- API endpoints work: ✓" if run_data else "✗")
    print("- Dagger module available: Check output above")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())