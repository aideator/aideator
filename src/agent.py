#!/usr/bin/env python3
"""AI Agent Script for Code Analysis and Generation."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential


class AIAgent:
    """AI Agent for analyzing repositories and generating code."""

    def __init__(self, variation_id: int):
        self.variation_id = variation_id
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        self.config = self._load_config()
        self.prompt = self._load_prompt()

    def _load_config(self) -> Dict[str, Any]:
        """Load agent configuration."""
        config_path = Path("/app/config.json")
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {
            "model": os.environ.get("DEFAULT_AGENT_MODEL", "claude-3-opus-20240229"),
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
    async def analyze_repository(self) -> None:
        """Analyze the repository and generate response."""
        print(f"[Agent {self.variation_id}] Starting analysis...")
        print(f"[Agent {self.variation_id}] Repository contents:")
        
        # List repository files
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

        print(f"\n[Agent {self.variation_id}] Sending request to Claude...")
        
        try:
            # Create message with repository context
            message = self.client.messages.create(
                model=self.config["model"],
                max_tokens=self.config["max_tokens"],
                temperature=self.config.get("temperature", 0.7),
                messages=[
                    {
                        "role": "user",
                        "content": f"""You are Agent {self.variation_id} analyzing a repository.

Repository structure is shown above.

Task: {self.prompt}

Please provide your analysis and any code changes needed.
""",
                    }
                ],
            )

            print(f"\n[Agent {self.variation_id}] Response from Claude:")
            print(message.content[0].text)
            print(f"\n[Agent {self.variation_id}] Analysis complete.")
            
        except Exception as e:
            print(f"[Agent {self.variation_id}] Error: {str(e)}")
            raise


async def main():
    """Main entry point."""
    variation_id = int(os.environ.get("AGENT_VARIATION_ID", "0"))
    agent = AIAgent(variation_id)
    await agent.analyze_repository()


if __name__ == "__main__":
    asyncio.run(main())