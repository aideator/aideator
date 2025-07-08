#!/usr/bin/env python3
"""Test script for Claude Code integration with Dagger."""

import asyncio
import os
import subprocess
import sys

async def test_claude_code():
    """Test the Claude Code Dagger module."""
    
    # Check if ANTHROPIC_API_KEY is set
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is not set")
        sys.exit(1)
    
    # Test repository and prompt
    repo_url = "https://github.com/fastapi/fastapi"
    prompt = "Add comprehensive docstrings to the main.py file explaining what each function does"
    
    print(f"Testing Claude Code integration...")
    print(f"Repository: {repo_url}")
    print(f"Prompt: {prompt}")
    print("-" * 80)
    
    # Build the Dagger command
    cmd = [
        "dagger", "call",
        "-m", "./dagger_module",
        "run-claude-code",
        "--repo-url", repo_url,
        "--prompt", prompt,
        "--anthropic-api-key", f"env:ANTHROPIC_API_KEY",
    ]
    
    # Execute the command
    try:
        print("Running Dagger command...")
        print(f"Command: {' '.join(cmd)}")
        print("-" * 80)
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Stream output
        for line in iter(process.stdout.readline, ''):
            if line:
                print(line.rstrip())
        
        # Wait for completion
        return_code = process.wait()
        
        if return_code == 0:
            print("-" * 80)
            print("✅ Test completed successfully!")
        else:
            print("-" * 80)
            print(f"❌ Test failed with exit code: {return_code}")
            sys.exit(return_code)
            
    except Exception as e:
        print(f"❌ Error running test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_claude_code())