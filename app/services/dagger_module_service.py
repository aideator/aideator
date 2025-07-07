"""Service for interacting with Dagger modules."""

import json
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
            "--variation-id", str(variation_id),
            "--anthropic-api-key", f"env:{settings.anthropic_api_key_env_var}",
        ]
        
        # Add optional parameters
        if agent_config:
            cmd.extend(["--agent-config", json.dumps(agent_config)])
        
        cmd.extend([
            "--container-image", settings.agent_container_image,
            "--memory-limit", settings.agent_memory_limit,
            "--cpu-limit", str(settings.agent_cpu_limit),
            "--workdir", settings.dagger_workdir,
            "--clone-timeout", str(settings.clone_timeout),
        ])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
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
    ) -> AsyncGenerator[str, None]:
        """Stream agent output line by line using Dagger module."""
        cmd = [
            "dagger", "call",
            "-m", self.module_path,
            "stream-agent",
            "--repo-url", repo_url,
            "--prompt", prompt,
            "--variation-id", str(variation_id),
            "--anthropic-api-key", f"env:{settings.anthropic_api_key_env_var}",
        ]
        
        # Add optional parameters
        if agent_config:
            cmd.extend(["--agent-config", json.dumps(agent_config)])
        
        cmd.extend([
            "--container-image", settings.agent_container_image,
            "--memory-limit", settings.agent_memory_limit,
            "--cpu-limit", str(settings.agent_cpu_limit),
            "--workdir", settings.dagger_workdir,
            "--clone-timeout", str(settings.clone_timeout),
            "stdout",  # Get stdout from the container
        ])
        
        try:
            # Use Popen for streaming output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
            )
            
            # Stream stdout line by line
            for line in process.stdout:
                if line.strip():
                    yield line.strip()
            
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
            "--workdir", settings.dagger_workdir,
            "--clone-timeout", str(settings.clone_timeout),
        ])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
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
            subprocess.run(
                ["dagger", "version"],
                capture_output=True,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False