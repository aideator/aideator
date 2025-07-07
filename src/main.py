"""
AIdeator Dagger Module

Simple containerized development pipeline for AIdeator.
"""

from typing import Optional, List, Any, Dict
import dagger
from dagger import dag, function, object_type, Directory
import json


@object_type
class Aideator:
    """AIdeator development pipeline."""

    @function
    async def dev(
        self,
        source: Directory,
        port: Optional[int] = 8000
    ) -> dagger.Service:
        """Run the FastAPI development server.
        
        Args:
            source: The project source directory
            port: Port to expose (default: 8000)
        
        Example:
            dagger call dev --source=. up --ports 8001:8000
        """
        return (
            dag.container()
            .from_("python:3.11-slim")
            .with_exec(["apt-get", "update"])
            .with_exec(["apt-get", "install", "-y", "git", "curl", "--no-install-recommends"])
            .with_exec(["pip", "install", "--upgrade", "pip", "uv"])
            .with_workdir("/app")
            .with_directory("/app", source)
            .with_exec(["uv", "pip", "install", "--system", "-e", "."])
            .with_env_variable("PYTHONUNBUFFERED", "1")
            .with_exposed_port(port)
            .with_exec([
                "uvicorn", "app.main:app",
                "--host", "0.0.0.0",
                "--port", str(port),
                "--reload"
            ])
            .as_service()
        )

    @function
    async def test(self, source: Directory) -> str:
        """Run tests with pytest.
        
        Args:
            source: The project source directory
            
        Example:
            dagger call test --source=.
        """
        result = await (
            dag.container()
            .from_("python:3.11-slim")
            .with_exec(["pip", "install", "--upgrade", "pip", "uv"])
            .with_workdir("/app")
            .with_directory("/app", source)
            .with_exec(["uv", "pip", "install", "--system", "-e", ".[dev]"])
            .with_env_variable("PYTHONPATH", "/app")
            .with_exec(["pytest", "-v"])
            .stdout()
        )
        return result

    @function
    async def lint(self, source: Directory) -> str:
        """Run linting with ruff.
        
        Args:
            source: The project source directory
            
        Example:
            dagger call lint --source=.
        """
        result = await (
            dag.container()
            .from_("python:3.11-slim")
            .with_exec(["pip", "install", "--upgrade", "pip", "uv"])
            .with_workdir("/app")
            .with_directory("/app", source)
            .with_exec(["uv", "pip", "install", "--system", "ruff"])
            .with_exec(["ruff", "check", "app/"])
            .stdout()
        )
        return result
    
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
    ) -> str:
        """
        Run a single AI agent in an isolated container.
        
        Example:
            dagger call run-agent --repo-url https://github.com/user/repo \
                --prompt "Analyze code" --anthropic-api-key env:ANTHROPIC_API_KEY
        """
        # Create container with dependencies
        container = (
            dag.container()
            .from_(container_image)
            .with_exec(["apt-get", "update"])
            .with_exec(["apt-get", "install", "-y", "git", "curl", "--no-install-recommends"])
            .with_exec([
                "pip", "install", "--no-cache-dir",
                "anthropic>=0.18.0",
                "aiofiles>=23.0.0", 
                "gitpython>=3.1.0",
                "structlog>=23.0.0",
                "tenacity>=8.2.0",
            ])
            .with_workdir("/workspace")
        )
        
        # Clone repository
        container = container.with_exec([
            "git", "clone", "--depth", "1", 
            repo_url, "."
        ])
        
        # Set up environment
        container = (
            container
            .with_env_variable("PYTHONUNBUFFERED", "1")
            .with_env_variable("AGENT_VARIATION_ID", str(variation_id))
            .with_env_variable("LOG_LEVEL", "INFO")
            .with_secret_variable("ANTHROPIC_API_KEY", anthropic_api_key)
        )
        
        # Copy agent script
        agent_script = dag.current_module().source().file("dagger_module/src/aideator/agent.py")
        container = container.with_file("/app/agent.py", agent_script)
        
        # Add prompt and config
        container = container.with_new_file("/app/prompt.txt", contents=prompt)
        if agent_config:
            container = container.with_new_file("/app/config.json", contents=agent_config)
        
        # Execute agent
        return await container.with_exec([
            "python", "-u", "/app/agent.py"
        ]).stdout()
    
    @function
    async def stream_agent(
        self,
        repo_url: str,
        prompt: str,
        anthropic_api_key: dagger.Secret,
        variation_id: int = 0,
        agent_config: Optional[str] = None,
        container_image: str = "python:3.11-slim",
    ) -> dagger.Container:
        """
        Create a container ready to stream agent output.
        
        Example:
            dagger call stream-agent --repo-url https://github.com/user/repo \
                --prompt "Analyze code" --anthropic-api-key env:ANTHROPIC_API_KEY stdout
        """
        # Create container with dependencies
        container = (
            dag.container()
            .from_(container_image)
            .with_exec(["apt-get", "update"])
            .with_exec(["apt-get", "install", "-y", "git", "curl", "--no-install-recommends"])
            .with_exec([
                "pip", "install", "--no-cache-dir",
                "anthropic>=0.18.0",
                "aiofiles>=23.0.0",
                "tenacity>=8.2.0",
            ])
            .with_workdir("/workspace")
        )
        
        # Clone repository
        container = container.with_exec([
            "git", "clone", "--depth", "1", repo_url, "."
        ])
        
        # Set up environment
        container = (
            container
            .with_env_variable("PYTHONUNBUFFERED", "1")
            .with_env_variable("AGENT_VARIATION_ID", str(variation_id))
            .with_secret_variable("ANTHROPIC_API_KEY", anthropic_api_key)
        )
        
        # Copy agent script
        agent_script = dag.current_module().source().file("dagger_module/src/aideator/agent.py")
        container = container.with_file("/app/agent.py", agent_script)
        
        # Add prompt and config
        container = container.with_new_file("/app/prompt.txt", contents=prompt)
        if agent_config:
            container = container.with_new_file("/app/config.json", contents=agent_config)
        
        # Return container ready for execution
        return container.with_exec(["python", "-u", "/app/agent.py"])