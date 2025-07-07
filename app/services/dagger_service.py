import json
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

import dagger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import DaggerEnvironment, get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class DaggerService:
    """Manages Dagger client lifecycle and container operations."""

    def __init__(self):
        self.client: Optional[dagger.Client] = None
        self._connected = False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def connect(self) -> None:
        """Connect to Dagger engine with retry logic."""
        try:
            self.client = dagger.Connection(
                dagger.Config(
                    log_output=settings.dagger_log_output,
                    execute_timeout=settings.dagger_engine_timeout,
                )
            )
            await self.client.connect()
            self._connected = True
            logger.info("Connected to Dagger engine")
        except Exception as e:
            logger.error(f"Failed to connect to Dagger engine: {e}")
            raise

    async def disconnect(self) -> None:
        """Cleanup Dagger connection."""
        if self.client and self._connected:
            try:
                await self.client.close()
                self._connected = False
                logger.info("Disconnected from Dagger engine")
            except Exception as e:
                logger.error(f"Error disconnecting from Dagger: {e}")

    @property
    def is_connected(self) -> bool:
        """Check if connected to Dagger engine."""
        return self._connected and self.client is not None

    async def create_agent_container(
        self,
        repo_url: str,
        prompt: str,
        variation_id: int,
        agent_config: Optional[dict[str, Any]] = None,
    ) -> dagger.Container:
        """Create an isolated agent container with proper configuration."""
        if not self.is_connected:
            raise RuntimeError("Not connected to Dagger engine")

        env_vars = DaggerEnvironment.get_agent_env(variation_id)

        # Base container with caching
        container = (
            self.client.container()
            .from_(settings.agent_container_image)
            # Cache apt packages
            .with_mounted_cache(
                "/var/cache/apt", self.client.cache_volume("apt-cache")
            )
            .with_mounted_cache("/var/lib/apt", self.client.cache_volume("apt-lib"))
            .with_exec(["apt-get", "update"])
            .with_exec(
                ["apt-get", "install", "-y", "git", "curl", "--no-install-recommends"]
            )
            # Cache pip packages
            .with_mounted_cache(
                "/root/.cache/pip", self.client.cache_volume("pip-cache")
            )
            .with_exec(
                [
                    "pip",
                    "install",
                    "--no-cache-dir",
                    "anthropic>=0.18.0",
                    "aiofiles>=23.0.0",
                    "gitpython>=3.1.0",
                    "structlog>=23.0.0",
                    "tenacity>=8.2.0",
                ]
            )
        )

        # Set up workspace and clone repo
        container = (
            container.with_workdir(settings.dagger_workdir)
            .with_exec(
                ["git", "clone", "--depth", "1", repo_url, "."],
                # Use timeout for clone operation
                experimental_exec_options=dagger.ExecOptions(
                    timeout=settings.clone_timeout
                ),
            )
        )

        # Apply environment variables
        for key, value in env_vars.items():
            container = container.with_env_variable(key, value)

        # Mount secrets securely
        for secret_name, secret_value in settings.get_dagger_secrets().items():
            secret = self.client.set_secret(secret_name, secret_value)
            container = container.with_secret_variable(
                secret_name.upper().replace("-", "_"), secret
            )

        # Apply resource limits
        container = container.with_env_variable(
            "MEMORY_LIMIT", settings.agent_memory_limit
        ).with_env_variable("CPU_LIMIT", str(settings.agent_cpu_limit))

        # Mount agent script
        agent_script_content = self._get_agent_script()
        container = container.with_new_file(
            "/app/agent.py", contents=agent_script_content, permissions=0o755
        )

        # Pass prompt via file to avoid command line length limits
        container = container.with_new_file("/app/prompt.txt", contents=prompt)

        # Agent configuration
        if agent_config:
            container = container.with_new_file(
                "/app/config.json", contents=json.dumps(agent_config)
            )

        return container

    async def execute_container(
        self, container: dagger.Container, command: list[str]
    ) -> AsyncGenerator[str, None]:
        """Execute container and stream output."""
        if not self.is_connected:
            raise RuntimeError("Not connected to Dagger engine")

        try:
            # Execute command
            exec_result = container.with_exec(command)

            # Stream stdout line by line
            stdout = await exec_result.stdout()
            for line in stdout.splitlines():
                if line.strip():
                    yield line.strip()

        except Exception as e:
            logger.error(f"Container execution failed: {e}")
            yield f"ERROR: {str(e)}"

    def _get_agent_script(self) -> str:
        """Get the agent script content."""
        return '''#!/usr/bin/env python3
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

        print(f"\\n[Agent {self.variation_id}] Sending request to Claude...")
        
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

            print(f"\\n[Agent {self.variation_id}] Response from Claude:")
            print(message.content[0].text)
            print(f"\\n[Agent {self.variation_id}] Analysis complete.")
            
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
'''

    @asynccontextmanager
    async def container_context(
        self,
        repo_url: str,
        prompt: str,
        variation_id: int,
        agent_config: Optional[dict[str, Any]] = None,
    ) -> AsyncGenerator[dagger.Container, None]:
        """Context manager for container lifecycle."""
        container = await self.create_agent_container(
            repo_url, prompt, variation_id, agent_config
        )
        try:
            yield container
        finally:
            # Cleanup is handled by Dagger
            pass