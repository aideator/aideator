import json
from typing import Any, Dict, List, Optional

import dagger
from dagger import dag, function, object_type


@object_type
class Aideator:
    """AIdeator Dagger module for orchestrating LLM agents in containers."""
    
    @function
    async def run_agent(
        self,
        repo_url: str,
        prompt: str,
        variation_id: int = 0,
        agent_config: Optional[str] = None,  # JSON string
        anthropic_api_key: dagger.Secret,
        container_image: str = "python:3.11-slim",
        memory_limit: str = "512m",
        cpu_limit: str = "0.5",
        workdir: str = "/workspace",
        clone_timeout: int = 300,
    ) -> str:
        """
        Run a single AI agent in an isolated container.
        
        Args:
            repo_url: GitHub repository URL to analyze
            prompt: Task prompt for the agent
            variation_id: Unique ID for this agent variation
            agent_config: JSON string with agent configuration
            anthropic_api_key: Anthropic API key secret
            container_image: Base container image
            memory_limit: Container memory limit
            cpu_limit: Container CPU limit
            workdir: Working directory in container
            clone_timeout: Git clone timeout in seconds
            
        Returns:
            Agent output as a string
        """
        # Create base container with dependencies
        container = await self._create_base_container(
            container_image,
            workdir,
            clone_timeout,
        )
        
        # Clone repository
        container = await self._clone_repository(container, repo_url, workdir)
        
        # Set up agent environment
        container = await self._setup_agent_environment(
            container,
            variation_id,
            prompt,
            agent_config,
            anthropic_api_key,
            memory_limit,
            cpu_limit,
        )
        
        # Execute agent and return output
        return await container.with_exec([
            "python", "-u", "/app/agent.py"
        ]).stdout()
    
    @function
    async def run_parallel_agents(
        self,
        repo_url: str,
        prompt: str,
        variations: int,
        agent_config: Optional[str] = None,  # JSON string
        anthropic_api_key: dagger.Secret,
        container_image: str = "python:3.11-slim",
        memory_limit: str = "512m",
        cpu_limit: str = "0.5",
        workdir: str = "/workspace",
        clone_timeout: int = 300,
    ) -> List[str]:
        """
        Run multiple AI agents in parallel containers.
        
        Args:
            repo_url: GitHub repository URL to analyze
            prompt: Task prompt for the agents
            variations: Number of agent variations to run
            agent_config: JSON string with agent configuration
            anthropic_api_key: Anthropic API key secret
            container_image: Base container image
            memory_limit: Container memory limit per agent
            cpu_limit: Container CPU limit per agent
            workdir: Working directory in container
            clone_timeout: Git clone timeout in seconds
            
        Returns:
            List of agent outputs
        """
        outputs = []
        
        for i in range(variations):
            output = await self.run_agent(
                repo_url=repo_url,
                prompt=prompt,
                variation_id=i,
                agent_config=agent_config,
                anthropic_api_key=anthropic_api_key,
                container_image=container_image,
                memory_limit=memory_limit,
                cpu_limit=cpu_limit,
                workdir=workdir,
                clone_timeout=clone_timeout,
            )
            outputs.append(output)
        
        return outputs
    
    @function
    async def stream_agent(
        self,
        repo_url: str,
        prompt: str,
        variation_id: int = 0,
        agent_config: Optional[str] = None,  # JSON string
        anthropic_api_key: dagger.Secret,
        container_image: str = "python:3.11-slim",
        memory_limit: str = "512m",
        cpu_limit: str = "0.5",
        workdir: str = "/workspace",
        clone_timeout: int = 300,
    ) -> dagger.Container:
        """
        Create and return a container ready to stream agent output.
        
        This function returns the container itself, allowing the caller
        to stream output line-by-line or handle execution differently.
        
        Args:
            repo_url: GitHub repository URL to analyze
            prompt: Task prompt for the agent
            variation_id: Unique ID for this agent variation
            agent_config: JSON string with agent configuration
            anthropic_api_key: Anthropic API key secret
            container_image: Base container image
            memory_limit: Container memory limit
            cpu_limit: Container CPU limit
            workdir: Working directory in container
            clone_timeout: Git clone timeout in seconds
            
        Returns:
            Container ready for execution
        """
        # Create base container with dependencies
        container = await self._create_base_container(
            container_image,
            workdir,
            clone_timeout,
        )
        
        # Clone repository
        container = await self._clone_repository(container, repo_url, workdir)
        
        # Set up agent environment
        container = await self._setup_agent_environment(
            container,
            variation_id,
            prompt,
            agent_config,
            anthropic_api_key,
            memory_limit,
            cpu_limit,
        )
        
        # Return container ready for execution
        return container.with_exec([
            "python", "-u", "/app/agent.py"
        ])
    
    async def _create_base_container(
        self,
        container_image: str,
        workdir: str,
        clone_timeout: int,
    ) -> dagger.Container:
        """Create base container with all dependencies."""
        # Get agent script from module
        agent_script = dag.current_module().source().file("agent.py")
        
        container = (
            dag.container()
            .from_(container_image)
            # Cache apt packages
            .with_mounted_cache(
                "/var/cache/apt", 
                dag.cache_volume("apt-cache")
            )
            .with_mounted_cache(
                "/var/lib/apt", 
                dag.cache_volume("apt-lib")
            )
            .with_exec(["apt-get", "update"])
            .with_exec([
                "apt-get", "install", "-y",
                "git", "curl",
                "--no-install-recommends"
            ])
            # Cache pip packages
            .with_mounted_cache(
                "/root/.cache/pip",
                dag.cache_volume("pip-cache")
            )
            .with_exec([
                "pip", "install", "--no-cache-dir",
                "anthropic>=0.18.0",
                "aiofiles>=23.0.0",
                "gitpython>=3.1.0",
                "structlog>=23.0.0",
                "tenacity>=8.2.0",
            ])
            # Mount agent script
            .with_file("/app/agent.py", agent_script)
            .with_workdir(workdir)
        )
        
        return container
    
    async def _clone_repository(
        self,
        container: dagger.Container,
        repo_url: str,
        workdir: str,
    ) -> dagger.Container:
        """Clone repository into container."""
        return container.with_exec([
            "git", "clone", "--depth", "1", 
            repo_url, "."
        ])
    
    async def _setup_agent_environment(
        self,
        container: dagger.Container,
        variation_id: int,
        prompt: str,
        agent_config: Optional[str],
        anthropic_api_key: dagger.Secret,
        memory_limit: str,
        cpu_limit: str,
    ) -> dagger.Container:
        """Set up agent environment variables and files."""
        # Base environment
        container = (
            container
            .with_env_variable("PYTHONUNBUFFERED", "1")
            .with_env_variable("AGENT_VARIATION_ID", str(variation_id))
            .with_env_variable("LOG_LEVEL", "INFO")
            .with_env_variable("MEMORY_LIMIT", memory_limit)
            .with_env_variable("CPU_LIMIT", cpu_limit)
            .with_secret_variable("ANTHROPIC_API_KEY", anthropic_api_key)
        )
        
        # Add prompt file
        container = container.with_new_file(
            "/app/prompt.txt",
            contents=prompt
        )
        
        # Add config file if provided
        if agent_config:
            container = container.with_new_file(
                "/app/config.json",
                contents=agent_config
            )
        
        return container
