"""Docker service for running containerized agents with real-time streaming."""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

import docker
from docker.errors import BuildError, ContainerError, ImageNotFound, APIError
from docker.models.containers import Container

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class DockerService:
    """Service for managing Docker containers with real-time output streaming."""
    
    def __init__(self):
        """Initialize Docker client."""
        try:
            self.client = docker.from_env()
            self.client.ping()
            logger.info("Docker service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise RuntimeError("Docker is not available. Please ensure Docker is installed and running.")
    
    async def build_agent_image(self, force_rebuild: bool = False) -> str:
        """Build the agent Docker image.
        
        Args:
            force_rebuild: Force rebuild even if image exists
            
        Returns:
            Image tag
        """
        image_tag = "aideator-agent:latest"
        
        # Check if image already exists
        if not force_rebuild:
            try:
                self.client.images.get(image_tag)
                logger.info(f"Using existing image: {image_tag}")
                return image_tag
            except ImageNotFound:
                pass
        
        logger.info("Building agent Docker image...")
        
        # Create Dockerfile content
        dockerfile_content = """
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    anthropic>=0.18.0 \
    aiofiles>=23.0.0 \
    gitpython>=3.1.0 \
    structlog>=23.0.0 \
    tenacity>=8.2.0

# Create app directory
WORKDIR /app

# Copy agent scripts
COPY dagger_module/src/aideator/agent.py /app/agent.py
COPY dagger_module/src/aideator/claude_code_agent.py /app/claude_code_agent.py
COPY dagger_module/src/aideator/slow_agent.py /app/slow_agent.py

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Default command
CMD ["python", "-u", "/app/agent.py"]
"""
        
        # Create temporary directory for build context
        with tempfile.TemporaryDirectory() as tmpdir:
            dockerfile_path = Path(tmpdir) / "Dockerfile"
            dockerfile_path.write_text(dockerfile_content)
            
            # Copy agent files to build context
            agent_src = Path("dagger_module/src/aideator")
            agent_dst = Path(tmpdir) / "dagger_module/src/aideator"
            agent_dst.mkdir(parents=True)
            
            for file in ["agent.py", "claude_code_agent.py", "slow_agent.py"]:
                src_file = agent_src / file
                if src_file.exists():
                    dst_file = agent_dst / file
                    dst_file.write_text(src_file.read_text())
            
            # Build image
            try:
                image, logs = self.client.images.build(
                    path=tmpdir,
                    tag=image_tag,
                    rm=True,
                    forcerm=True,
                )
                
                # Log build output
                for log in logs:
                    if 'stream' in log:
                        logger.debug(f"Build: {log['stream'].strip()}")
                
                logger.info(f"Successfully built image: {image_tag}")
                return image_tag
                
            except BuildError as e:
                logger.error(f"Failed to build Docker image: {e}")
                raise
    
    async def stream_agent_output(
        self,
        repo_url: str,
        prompt: str,
        variation_id: int = 0,
        agent_config: Optional[Dict[str, Any]] = None,
        use_claude_code: bool = False,
        image_tag: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream agent output in real-time using Docker.
        
        Args:
            repo_url: GitHub repository URL
            prompt: Agent prompt
            variation_id: Agent variation ID
            agent_config: Optional agent configuration
            use_claude_code: Whether to use Claude Code
            image_tag: Docker image to use (defaults to aideator-agent:latest)
            
        Yields:
            Lines of output from the agent
        """
        if not image_tag:
            image_tag = await self.build_agent_image()
        
        # Prepare environment variables
        environment = {
            "ANTHROPIC_API_KEY": settings.anthropic_api_key,
            "AGENT_VARIATION_ID": str(variation_id),
            "PYTHONUNBUFFERED": "1",
            "LOG_LEVEL": "INFO",
        }
        
        # Create container
        logger.info(f"Creating container for agent {variation_id}")
        container = None
        
        try:
            # Create working directory for repo
            working_dir = f"/workspace"
            
            # Create a script that will run the entire pipeline
            script_content = f"""#!/bin/sh
set -e

# Clone repository
echo "[Agent {variation_id}] Cloning repository..."
git clone --depth 1 "{repo_url}" {working_dir} || exit 1

cd {working_dir}

# Write prompt file
echo '{prompt}' > prompt.txt

# Write config file if provided
"""
            if agent_config:
                config_json = json.dumps(agent_config).replace("'", "'\"'\"'")
                script_content += f"echo '{config_json}' > config.json\n"
            
            # Add agent execution
            if "SLOW_AGENT_TEST" in prompt:
                # Special test mode - use slow agent
                script_content += "exec python -u /app/slow_agent.py"
            elif use_claude_code:
                script_content += "exec python -u /app/claude_code_agent.py"
            else:
                script_content += "exec python -u /app/agent.py"
            
            # Run container with the script as the main command
            container = self.client.containers.run(
                image_tag,
                command=["sh", "-c", script_content],
                environment=environment,
                working_dir="/",
                detach=True,
                auto_remove=False,  # Don't auto-remove so we can get logs
                mem_limit=settings.agent_memory_limit,
                cpu_quota=int(float(settings.agent_cpu_limit) * 100000),
                cpu_period=100000,
                labels={"aideator": "true", "variation_id": str(variation_id)},
            )
            
            logger.info(f"Started container {container.short_id} for agent {variation_id}")
            
            # Stream logs in real-time
            log_stream = container.logs(stream=True, follow=True, stdout=True, stderr=True)
            
            try:
                for log_line in log_stream:
                    if isinstance(log_line, bytes):
                        line = log_line.decode('utf-8').strip()
                    else:
                        line = str(log_line).strip()
                    
                    if line:
                        # Check if it's an error from git clone or other setup
                        if "fatal:" in line or "error:" in line.lower():
                            logger.error(f"Container error: {line}")
                            yield f"ERROR: {line}"
                        else:
                            yield line
                        
                        # Yield control to allow other tasks
                        await asyncio.sleep(0)
                
                # Wait for container to finish
                exit_code = container.wait()["StatusCode"]
                if exit_code != 0:
                    logger.error(f"Container exited with code {exit_code}")
                    yield f"ERROR: Container exited with code {exit_code}"
                    
            except Exception as e:
                logger.error(f"Error streaming logs: {e}")
                yield f"ERROR: Error streaming logs: {str(e)}"
                
        except ContainerError as e:
            logger.error(f"Container error: {e}")
            yield f"ERROR: Container error: {str(e)}"
        except APIError as e:
            logger.error(f"Docker API error: {e}")
            yield f"ERROR: Docker API error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            yield f"ERROR: {str(e)}"
        finally:
            # Ensure container is cleaned up
            if container:
                try:
                    container.remove(force=True)
                    logger.info(f"Cleaned up container for agent {variation_id}")
                except Exception as e:
                    logger.error(f"Failed to remove container: {e}")
    
    async def run_parallel_agents(
        self,
        repo_url: str,
        prompt: str,
        variations: int,
        agent_config: Optional[Dict[str, Any]] = None,
        use_claude_code: bool = False,
    ) -> List[AsyncGenerator[str, None]]:
        """Run multiple agents in parallel.
        
        Args:
            repo_url: GitHub repository URL
            prompt: Agent prompt
            variations: Number of variations
            agent_config: Optional agent configuration
            use_claude_code: Whether to use Claude Code
            
        Returns:
            List of async generators for each agent's output
        """
        # Build image once for all agents
        image_tag = await self.build_agent_image()
        
        # Create generators for each variation
        generators = []
        for i in range(variations):
            gen = self.stream_agent_output(
                repo_url=repo_url,
                prompt=prompt,
                variation_id=i,
                agent_config=agent_config,
                use_claude_code=use_claude_code,
                image_tag=image_tag,
            )
            generators.append(gen)
        
        return generators
    
    def cleanup(self):
        """Clean up Docker resources."""
        try:
            # Remove any lingering containers
            containers = self.client.containers.list(
                filters={"label": "aideator=true"}
            )
            for container in containers:
                try:
                    container.remove(force=True)
                except:
                    pass
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def is_available(self) -> bool:
        """Check if Docker is available."""
        try:
            self.client.ping()
            return True
        except:
            return False