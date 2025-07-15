#!/usr/bin/env python3
"""
LiteLLM subprocess wrapper for consistent CLI interface.

This script provides a CLI interface to LiteLLM that matches the 
subprocess pattern used by other providers.
"""

import sys
import asyncio
import json
import os
from typing import List, Dict, Any

# Import litellm only in this wrapper script
try:
    from litellm import acompletion
except ImportError:
    print("ERROR: litellm library not available", file=sys.stderr)
    sys.exit(1)


def parse_args() -> Dict[str, Any]:
    """Parse command line arguments."""
    if len(sys.argv) < 3:
        print("Usage: litellm_wrapper.py <model> <prompt> [temperature] [max_tokens] [api_base] [api_key]", file=sys.stderr)
        sys.exit(1)
    
    config = {
        "model": sys.argv[1],
        "prompt": sys.argv[2],
        "temperature": float(sys.argv[3]) if len(sys.argv) > 3 else 0.7,
        "max_tokens": int(sys.argv[4]) if len(sys.argv) > 4 else 4000,
        "api_base": sys.argv[5] if len(sys.argv) > 5 else None,
        "api_key": sys.argv[6] if len(sys.argv) > 6 else None,
    }
    
    return config


async def stream_completion(config: Dict[str, Any]) -> None:
    """Stream completion results to stdout."""
    try:
        # Prepare messages
        messages = [{"role": "user", "content": config["prompt"]}]
        
        # Call LiteLLM with streaming
        response = await acompletion(
            model=config["model"],
            messages=messages,
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
            stream=True,
            api_base=config["api_base"],
            api_key=config["api_key"]
        )
        
        # Stream output in JSON format (similar to Claude CLI)
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                # Create a streaming JSON object
                stream_obj = {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {
                                "type": "text",
                                "text": chunk.choices[0].delta.content
                            }
                        ]
                    }
                }
                print(json.dumps(stream_obj), flush=True)
        
    except Exception as e:
        error_obj = {
            "type": "error",
            "error": str(e)
        }
        print(json.dumps(error_obj), file=sys.stderr, flush=True)
        sys.exit(1)


async def main():
    """Main entry point."""
    config = parse_args()
    await stream_completion(config)


if __name__ == "__main__":
    asyncio.run(main())