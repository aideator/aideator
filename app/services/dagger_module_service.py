"""Service for interacting with Dagger modules."""

import json
import os
import subprocess
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class DaggerModuleService:
    """Service to interact with Dagger modules via the CLI."""
    
    def __init__(self):
        self.module_name = "aideator"
        self.module_path = "."  # Module is at project root
        
    async def run_agent(
        self,
        repo_url: str,
        prompt: str,
        variation_id: int = 0,
        agent_config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Run a single agent using the Dagger module."""
        cmd = [
            "dagger", "call",
            "-m", self.module_path,
            "run-agent",
            "--repo-url", repo_url,
            "--prompt", prompt,
            "--anthropic-api-key", f"env:{settings.anthropic_api_key_env_var}",
            "--variation-id", str(variation_id),
        ]
        
        # Add optional parameters
        if agent_config:
            cmd.extend(["--agent-config", json.dumps(agent_config)])
        
        cmd.extend([
            "--container-image", settings.agent_container_image,
            "--memory-limit", settings.agent_memory_limit,
            "--cpu-limit", str(settings.agent_cpu_limit),
            "--clone-timeout", str(settings.clone_timeout),
        ])
        
        try:
            # Create environment without SSH_AUTH_SOCK to avoid Dagger issues
            env = os.environ.copy()
            env.pop('SSH_AUTH_SOCK', None)
            env.pop('SSH_AGENT_PID', None)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                env=env,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Dagger module execution failed: {e.stderr}")
            raise RuntimeError(f"Agent execution failed: {e.stderr}")
    
    async def stream_agent_output(
        self,
        repo_url: str,
        prompt: str,
        variation_id: int = 0,
        agent_config: Optional[Dict[str, Any]] = None,
        use_claude_code: bool = False,
    ) -> AsyncGenerator[str, None]:
        """Stream agent output line by line using Dagger module."""
        cmd = [
            "dagger", "-q",  # Quiet mode - show only output
            "call",
            "-m", self.module_path,
            "stream-agent",
            "--repo-url", repo_url,
            "--prompt", prompt,
            "--anthropic-api-key", f"env:{settings.anthropic_api_key_env_var}",
            "--variation-id", str(variation_id),
        ]
        
        # Add optional parameters
        if agent_config:
            cmd.extend(["--agent-config", json.dumps(agent_config)])
        
        cmd.extend([
            "--container-image", settings.agent_container_image,
            "--memory-limit", settings.agent_memory_limit,
            "--cpu-limit", str(settings.agent_cpu_limit),
            "--clone-timeout", str(settings.clone_timeout),
        ])
        
        # Add Claude Code flag if requested
        if use_claude_code:
            cmd.append("--use-claude-code")
        
        cmd.append("stdout")  # Get stdout from the container
        
        try:
            # Create environment without SSH_AUTH_SOCK to avoid Dagger issues
            env = os.environ.copy()
            # Remove SSH_AUTH_SOCK completely to avoid socket not found errors
            env.pop('SSH_AUTH_SOCK', None)
            # Also remove SSH_AGENT_PID if present
            env.pop('SSH_AGENT_PID', None)
            
            # Use Popen for streaming output
            # Redirect stderr to devnull to suppress progress output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,  # Suppress all stderr output
                text=True,
                bufsize=1,  # Line buffered
                env=env,
            )
            
            # Stream stdout line by line
            logger.debug(f"Starting to stream output from Dagger process")
            line_count = 0
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if line:
                    # Yield all non-empty lines now that we're using --silent
                    logger.debug(f"Yielding line: {line[:100]}...")  # Log first 100 chars
                    line_count += 1
                    yield line
            
            logger.info(f"Streamed {line_count} lines from agent {variation_id}")
            
            # Wait for process to complete
            return_code = process.wait()
            
            if return_code != 0:
                stderr = process.stderr.read()
                logger.error(f"Dagger module execution failed: {stderr}")
                yield f"ERROR: Agent execution failed"
                
        except Exception as e:
            logger.error(f"Failed to stream agent output: {e}")
            yield f"ERROR: {str(e)}"
    
    async def run_parallel_agents(
        self,
        repo_url: str,
        prompt: str,
        variations: int,
        agent_config: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Run multiple agents in parallel using Dagger module."""
        cmd = [
            "dagger", "call",
            "-m", self.module_path,
            "run-parallel-agents",
            "--repo-url", repo_url,
            "--prompt", prompt,
            "--variations", str(variations),
            "--anthropic-api-key", f"env:{settings.anthropic_api_key_env_var}",
        ]
        
        # Add optional parameters
        if agent_config:
            cmd.extend(["--agent-config", json.dumps(agent_config)])
        
        cmd.extend([
            "--container-image", settings.agent_container_image,
            "--memory-limit", settings.agent_memory_limit,
            "--cpu-limit", str(settings.agent_cpu_limit),
            "--clone-timeout", str(settings.clone_timeout),
        ])
        
        try:
            # Create environment without SSH_AUTH_SOCK to avoid Dagger issues
            env = os.environ.copy()
            env.pop('SSH_AUTH_SOCK', None)
            env.pop('SSH_AGENT_PID', None)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                env=env,
            )
            # Parse JSON array output
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Dagger module execution failed: {e.stderr}")
            raise RuntimeError(f"Parallel agents execution failed: {e.stderr}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Dagger output: {e}")
            raise RuntimeError("Invalid output from Dagger module")
    
    def is_available(self) -> bool:
        """Check if Dagger CLI is available."""
        try:
            # Create environment without SSH_AUTH_SOCK
            env = os.environ.copy()
            env.pop('SSH_AUTH_SOCK', None)
            env.pop('SSH_AGENT_PID', None)
            
            subprocess.run(
                ["dagger", "version"],
                capture_output=True,
                check=True,
                env=env,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False