#!/usr/bin/env python3
"""Claude Code Agent Script for Code Analysis and Generation."""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from tenacity import retry, stop_after_attempt, wait_exponential


class ClaudeCodeAgent:
    """Claude Code Agent for analyzing repositories and generating code."""

    def __init__(self, variation_id: int):
        self.variation_id = variation_id
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.prompt = self._load_prompt()
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load agent configuration."""
        config_path = Path("/app/config.json")
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {
            "model": os.environ.get("DEFAULT_AGENT_MODEL", "claude-3-5-sonnet-20241022"),
            "max_tokens": 4096,
            "temperature": 0.7,
        }

    def _load_prompt(self) -> str:
        """Load prompt from file."""
        with open("/app/prompt.txt") as f:
            return f.read().strip()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def run_claude_code(self) -> None:
        """Run Claude Code on the repository with the given prompt."""
        print(f"[Agent {self.variation_id}] Starting Claude Code analysis...")
        print(f"[Agent {self.variation_id}] Working directory: {os.getcwd()}")
        
        # List repository files for context
        print(f"[Agent {self.variation_id}] Repository contents:")
        for root, dirs, files in os.walk("."):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            level = root.replace(".", "", 1).count(os.sep)
            indent = " " * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = " " * 2 * (level + 1)
            for file in files:
                if not file.startswith("."):
                    print(f"{subindent}{file}")

        print(f"\n[Agent {self.variation_id}] Launching Claude Code with prompt...")
        
        try:
            # Build Claude Code command - use headless mode with -p flag
            cmd = [
                "claude",
                "-p",  # Headless mode with prompt
                self.prompt
            ]
            
            # Set environment variables
            env = os.environ.copy()
            env["CLAUDE_OUTPUT_WIDTH"] = "120"  # Set reasonable width for container
            # API key is already in environment from Dagger secret
            
            print(f"[Agent {self.variation_id}] Command: claude -p '{self.prompt[:50]}...'")
            
            # Run Claude Code and stream output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env
            )
            
            # Stream output line by line
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(f"[Agent {self.variation_id}] {line.rstrip()}")
            
            # Wait for process to complete
            return_code = process.wait()
            
            if return_code != 0:
                raise Exception(f"Claude Code exited with code {return_code}")
                
            print(f"\n[Agent {self.variation_id}] Claude Code analysis complete.")
            
        except Exception as e:
            print(f"[Agent {self.variation_id}] Error: {str(e)}")
            raise


async def main():
    """Main entry point."""
    variation_id = int(os.environ.get("AGENT_VARIATION_ID", "0"))
    agent = ClaudeCodeAgent(variation_id)
    await agent.run_claude_code()


if __name__ == "__main__":
    asyncio.run(main())