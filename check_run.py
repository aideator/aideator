#!/usr/bin/env python3
"""Check the status of a run and diagnose issues."""

import asyncio
import sys
import httpx
from datetime import datetime


async def check_run(run_id: str):
    """Check detailed status of a run."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # Get run details
        print(f"\n🔍 Checking run: {run_id}")
        print("=" * 60)
        
        response = await client.get(f"{base_url}/api/v1/runs/{run_id}")
        if response.status_code != 200:
            print(f"❌ Failed to get run details: {response.status_code}")
            print(response.text)
            return
        
        run_data = response.json()
        
        # Display run info
        print(f"📋 Run Details:")
        print(f"   Status: {run_data.get('status', 'unknown')}")
        print(f"   Created: {run_data.get('created_at', 'unknown')}")
        print(f"   Prompt: {run_data.get('prompt', 'unknown')}")
        print(f"   Variations: {run_data.get('variations', 'unknown')}")
        print(f"   GitHub URL: {run_data.get('github_url', 'unknown')}")
        
        # Check for errors
        if 'error' in run_data:
            print(f"\n❌ Error: {run_data['error']}")
        
        # Check results
        results = run_data.get('results', {})
        if results:
            print(f"\n📊 Results:")
            for variation_id, result in results.items():
                print(f"   Variation {variation_id}: {result}")
        else:
            print(f"\n⚠️  No results found")
        
        # List all runs to see patterns
        print(f"\n📜 Recent runs:")
        runs_response = await client.get(f"{base_url}/api/v1/runs?limit=5")
        if runs_response.status_code == 200:
            runs = runs_response.json()
            for run in runs[:5]:
                created = run.get('created_at', 'unknown')
                print(f"   {run['id']}: {run['status']} (created: {created[:19]})")


async def check_docker():
    """Check Docker status and containers."""
    print("\n🐳 Docker Status:")
    print("=" * 60)
    
    import subprocess
    
    # Check for aideator containers
    result = subprocess.run(
        ["docker", "ps", "-a", "--filter", "label=aideator=true", "--format", "table {{.ID}}\t{{.Status}}\t{{.Names}}"],
        capture_output=True,
        text=True
    )
    
    if result.stdout.strip():
        print("AIdeator containers:")
        print(result.stdout)
    else:
        print("No AIdeator containers found")
    
    # Check if agent image exists
    result = subprocess.run(
        ["docker", "images", "aideator-agent:latest", "--format", "{{.Repository}}:{{.Tag}} - {{.CreatedSince}}"],
        capture_output=True,
        text=True
    )
    
    if result.stdout.strip():
        print(f"\n✅ Agent image: {result.stdout.strip()}")
    else:
        print("\n❌ Agent image not found")


async def test_slow_agent():
    """Test the slow agent directly."""
    print("\n🧪 Testing slow agent directly:")
    print("=" * 60)
    
    from app.services.docker_service import DockerService
    
    try:
        docker_service = DockerService()
        
        print("Running slow agent...")
        line_count = 0
        async for line in docker_service.stream_agent_output(
            repo_url="https://github.com/octocat/Hello-World",
            prompt="SLOW_AGENT_TEST: Count to 5 with 1 second delays",
            variation_id=0,
        ):
            print(f"   {line}")
            line_count += 1
            
        print(f"\n✅ Received {line_count} lines of output")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run diagnostics."""
    if len(sys.argv) > 1:
        run_id = sys.argv[1]
        await check_run(run_id)
    else:
        print("Usage: python check_run.py <run_id>")
        print("\nRunning general diagnostics...")
    
    await check_docker()
    
    # Test slow agent if requested
    if len(sys.argv) > 2 and sys.argv[2] == "--test":
        await test_slow_agent()


if __name__ == "__main__":
    asyncio.run(main())