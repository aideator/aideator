"""Claude CLI provider implementation."""

import os
import json
import asyncio
from typing import AsyncGenerator, Dict, Any
from pathlib import Path

from .base import LLMProvider


class ClaudeCLIProvider(LLMProvider):
    """Claude CLI-based provider."""
    
    def __init__(self):
        self.name = "claude-cli"
    
    async def generate(
        self,
        prompt: str,
        config: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """Generate response using Claude CLI."""
        repo_dir = config.get("repo_dir")
        if not repo_dir:
            raise ValueError("repo_dir is required for Claude CLI provider")
        
        # Save current directory
        original_dir = os.getcwd()
        
        try:
            # Change to repository directory for context
            os.chdir(repo_dir)
            
            # Execute Claude CLI
            process = await asyncio.create_subprocess_exec(
                "claude",
                "-p",
                prompt,
                "--output-format",
                "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ  # Includes ANTHROPIC_API_KEY
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                process.terminate()
                await process.wait()
                raise RuntimeError("Claude CLI execution timed out after 30 seconds")
            
            if process.returncode == 0:
                # Parse JSON output
                try:
                    response_data = json.loads(stdout.decode())
                    # Extract content from JSON structure
                    if isinstance(response_data, dict):
                        content = response_data.get("content", response_data.get("text", str(response_data)))
                    else:
                        content = str(response_data)
                    
                    # Yield the entire response at once (Claude CLI doesn't stream)
                    yield content
                    
                except json.JSONDecodeError:
                    # Fall back to raw output if JSON parsing fails
                    yield stdout.decode()
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise RuntimeError(f"Claude CLI failed with exit code {process.returncode}: {error_msg}")
                
        finally:
            # Always restore original directory
            os.chdir(original_dir)
    
    def get_name(self) -> str:
        """Get provider name."""
        return self.name