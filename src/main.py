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
        anthropic_api_key: dagger.Secret,
        variation_id: int = 0,
        agent_config: Optional[str] = None,  # JSON string
        container_image: str = "python:3.11-slim",
        memory_limit: str = "512m",
        cpu_limit: str = "0.5",
        work_dir: str = "/workspace",
        clone_timeout: int = 300,
        use_claude_code: bool = False,
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
            work_dir: Working directory in container
            clone_timeout: Git clone timeout in seconds
            use_claude_code: Use Claude Code CLI instead of basic agent
            
        Returns:
            Agent output as a string
        """
        # Create base container with dependencies
        container = await self._create_base_container(
            container_image,
            work_dir,
            clone_timeout,
        )
        
        # Clone repository
        container = await self._clone_repository(container, repo_url, work_dir)
        
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
        if use_claude_code:
            return await container.with_exec([
                "python3", "-u", "/app/claude_code_agent.py"
            ]).stdout()
        else:
            return await container.with_exec([
                "python3", "-u", "/app/agent.py"
            ]).stdout()
    
    @function
    async def run_parallel_agents(
        self,
        repo_url: str,
        prompt: str,
        variations: int,
        anthropic_api_key: dagger.Secret,
        agent_config: Optional[str] = None,  # JSON string
        container_image: str = "python:3.11-slim",
        memory_limit: str = "512m",
        cpu_limit: str = "0.5",
        work_dir: str = "/workspace",
        clone_timeout: int = 300,
        use_claude_code: bool = False,
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
            work_dir: Working directory in container
            clone_timeout: Git clone timeout in seconds
            
        Returns:
            List of agent outputs
        """
        outputs = []
        
        for i in range(variations):
            output = await self.run_agent(
                repo_url=repo_url,
                prompt=prompt,
                anthropic_api_key=anthropic_api_key,
                variation_id=i,
                agent_config=agent_config,
                container_image=container_image,
                memory_limit=memory_limit,
                cpu_limit=cpu_limit,
                workdir=work_dir,
                clone_timeout=clone_timeout,
                use_claude_code=use_claude_code,
            )
            outputs.append(output)
        
        return outputs
    
    @function
    async def stream_agent(
        self,
        repo_url: str,
        prompt: str,
        anthropic_api_key: dagger.Secret,
        variation_id: int = 0,
        agent_config: Optional[str] = None,  # JSON string
        container_image: str = "python:3.11-slim",
        memory_limit: str = "512m",
        cpu_limit: str = "0.5",
        work_dir: str = "/workspace",
        clone_timeout: int = 300,
        use_claude_code: bool = False,
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
            work_dir: Working directory in container
            clone_timeout: Git clone timeout in seconds
            
        Returns:
            Container ready for execution
        """
        # Create base container with dependencies
        container = await self._create_base_container(
            container_image,
            work_dir,
            clone_timeout,
        )
        
        # Clone repository
        container = await self._clone_repository(container, repo_url, work_dir)
        
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
        if use_claude_code:
            return container.with_exec([
                "python3", "-u", "/app/claude_code_agent.py"
            ])
        else:
            return container.with_exec([
                "python3", "-u", "/app/agent.py"
            ])
    
    @function
    async def run_claude_code(
        self,
        repo_url: str,
        prompt: str,
        anthropic_api_key: dagger.Secret,
        container_image: str = "python:3.11-slim",
        memory_limit: str = "2g",  # More memory for Claude Code
        cpu_limit: str = "2.0",    # More CPU for Claude Code
    ) -> str:
        """
        Run Claude Code CLI directly on a repository.
        
        This is a dedicated function for running Claude Code with optimal settings.
        
        Args:
            repo_url: GitHub repository URL to analyze
            prompt: Task prompt for Claude Code
            anthropic_api_key: Anthropic API key secret
            container_image: Base container image
            memory_limit: Container memory limit (default 2g for Claude Code)
            cpu_limit: Container CPU limit (default 2.0 for Claude Code)
            
        Returns:
            Claude Code output as a string
        """
        # Use the existing run_agent with Claude Code enabled
        return await self.run_agent(
            repo_url=repo_url,
            prompt=prompt,
            anthropic_api_key=anthropic_api_key,
            variation_id=0,
            agent_config=None,
            container_image=container_image,
            memory_limit=memory_limit,
            cpu_limit=cpu_limit,
            work_dir="/workspace",
            clone_timeout=300,
            use_claude_code=True,
        )
    
    async def _create_base_container(
        self,
        container_image: str,
        work_dir: str,
        clone_timeout: int,
    ) -> dagger.Container:
        """Create base container with all dependencies."""
        # Get agent scripts from module
        agent_script = dag.current_module().source().file("aideator/agent.py")
        claude_code_agent_script = dag.current_module().source().file("aideator/claude_code_agent.py")
        
        # Use node:20-slim for Claude Code support
        if "python" in container_image:
            container_image = "node:20-slim"
        
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
                "git", "curl", "ca-certificates", "python3", "python3-pip", "ripgrep",
                "--no-install-recommends"
            ])
            # Cache npm packages
            .with_mounted_cache(
                "/root/.npm",
                dag.cache_volume("npm-cache")
            )
            # Install Claude Code CLI via npm
            .with_exec([
                "npm", "install", "-g", "@anthropic-ai/claude-code"
            ])
            # Cache pip packages
            .with_mounted_cache(
                "/root/.cache/pip",
                dag.cache_volume("pip-cache")
            )
            .with_exec([
                "pip3", "install", "--no-cache-dir", "--break-system-packages",
                "anthropic>=0.18.0",
                "aiofiles>=23.0.0",
                "gitpython>=3.1.0",
                "structlog>=23.0.0",
                "tenacity>=8.2.0",
            ])
            # Mount agent scripts
            .with_file("/app/agent.py", agent_script)
            .with_file("/app/claude_code_agent.py", claude_code_agent_script)
            .with_workdir(work_dir)
        )
        
        return container
    
    async def _clone_repository(
        self,
        container: dagger.Container,
        repo_url: str,
        work_dir: str,
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
