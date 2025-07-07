"""
AIdeator Dagger Module

Simple containerized development pipeline for AIdeator.
"""

from typing import Optional
import dagger
from dagger import dag, function, object_type, Directory


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