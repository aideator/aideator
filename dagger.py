"""
AIdeator Dagger CI/CD Pipeline

This module provides a complete containerized development and deployment pipeline
using Dagger's Python SDK. All components run in isolated containers.

Usage:
    dagger call test
    dagger call dev --port=8000
    dagger call build-production-image --tag="aideator:latest"
    dagger call ci-pipeline
"""

from typing import Optional

import dagger
from dagger import dag, function, object_type


@object_type
class Aideator:
    """AIdeator Dagger pipeline for development, testing, and deployment."""

    @function
    async def build_base(self) -> dagger.Container:
        """Build the base Python container with all dependencies."""
        return (
            dag.container()
            .from_("python:3.11-slim")
            .with_exec(["apt-get", "update"])
            .with_exec([
                "apt-get", "install", "-y",
                "git", "curl", "build-essential", "--no-install-recommends"
            ])
            .with_exec(["pip", "install", "--upgrade", "pip", "uv"])
            .with_workdir("/app")
            .with_file("pyproject.toml", dag.host().file("pyproject.toml"))
            .with_exec(["uv", "pip", "install", "-e", ".[dev]"])
        )

    @function
    async def test(
        self,
        coverage: bool = True,
        markers: Optional[str] = None,
    ) -> str:
        """Run tests in a container with optional coverage and markers."""
        base = await self.build_base()
        
        # Copy source code
        test_container = (
            base
            .with_directory("/app/app", dag.host().directory("app"))
            .with_directory("/app/tests", dag.host().directory("tests"))
            .with_env_variable("PYTHONPATH", "/app")
        )
        
        # Build test command
        cmd = ["pytest", "-v"]
        if coverage:
            cmd.extend(["--cov=app", "--cov-report=term-missing"])
        if markers:
            cmd.extend(["-m", markers])
        
        # Run tests
        result = await test_container.with_exec(cmd).stdout()
        return result

    @function
    async def lint(self) -> str:
        """Run linting with ruff."""
        base = await self.build_base()
        
        lint_container = (
            base
            .with_directory("/app/app", dag.host().directory("app"))
            .with_directory("/app/tests", dag.host().directory("tests"))
        )
        
        # Run ruff check
        check_result = await lint_container.with_exec([
            "ruff", "check", "app/", "tests/"
        ]).stdout()
        
        # Run ruff format check
        format_result = await lint_container.with_exec([
            "ruff", "format", "--check", "app/", "tests/"
        ]).stdout()
        
        return f"Ruff Check:\n{check_result}\n\nFormat Check:\n{format_result}"

    @function
    async def type_check(self) -> str:
        """Run type checking with mypy."""
        base = await self.build_base()
        
        mypy_container = (
            base
            .with_directory("/app/app", dag.host().directory("app"))
            .with_exec(["mypy", "app/", "--strict"])
        )
        
        result = await mypy_container.stdout()
        return result

    @function
    async def security_scan(self) -> str:
        """Run security scans with bandit and safety."""
        base = await self.build_base()
        
        security_container = (
            base
            .with_directory("/app/app", dag.host().directory("app"))
            .with_file(".bandit", dag.host().file(".bandit"))
        )
        
        # Run bandit
        bandit_result = await security_container.with_exec([
            "bandit", "-r", "app/", "-f", "json"
        ]).stdout()
        
        # Run safety check
        safety_result = await security_container.with_exec([
            "safety", "check", "--json"
        ]).stdout()
        
        return f"Bandit Results:\n{bandit_result}\n\nSafety Results:\n{safety_result}"

    @function
    async def dev(self, port: int = 8000) -> dagger.Service:
        """Run the FastAPI development server as a service.
        
        Example:
            dagger call dev up --ports 8000:8000
        """
        base = await self.build_base()
        
        # Create dev container with source mounted
        dev_container = (
            base
            .with_directory("/app/app", dag.host().directory("app"))
            .with_file(".env", dag.host().file(".env.example"))
            .with_env_variable("PYTHONPATH", "/app")
            .with_exposed_port(port)
            .with_exec([
                "uvicorn", "app.main:app",
                "--host", "0.0.0.0",
                "--port", str(port),
                "--reload"
            ])
        )
        
        return dev_container.as_service()

    @function
    async def prod(
        self,
        port: int = 8000,
        workers: int = 4,
    ) -> dagger.Service:
        """Run the production FastAPI server with gunicorn.
        
        Example:
            dagger call prod up --ports 8000:8000
        """
        base = await self.build_base()
        
        # Build production image
        prod_container = (
            base
            .with_directory("/app/app", dag.host().directory("app"))
            .with_env_variable("PYTHONPATH", "/app")
            .with_exposed_port(port)
            .with_exec([
                "gunicorn", "app.main:app",
                "-w", str(workers),
                "-k", "uvicorn.workers.UvicornWorker",
                "--bind", f"0.0.0.0:{port}",
                "--access-logfile", "-",
                "--error-logfile", "-"
            ])
        )
        
        return prod_container.as_service()

    @function
    async def full_stack(self, port: int = 8000) -> dagger.Service:
        """Run the full stack including Dagger engine and Redis.
        
        Example:
            dagger call full-stack up --ports 8000:8000
        """
        # Start Dagger engine as a service
        dagger_engine = (
            dag.container()
            .from_("docker:24-dind")
            .with_privileged()
            .with_exec(["dockerd"])
            .with_exposed_port(2375)
            .as_service()
        )
        
        # Start Redis service for production
        redis = (
            dag.container()
            .from_("redis:7-alpine")
            .with_exposed_port(6379)
            .as_service()
        )
        
        # Start the API server with services
        api_container = (
            await self.build_base()
            .with_directory("/app/app", dag.host().directory("app"))
            .with_env_variable("PYTHONPATH", "/app")
            .with_env_variable("DAGGER_ENGINE_URL", "tcp://dagger-engine:2375")
            .with_env_variable("REDIS_URL", "redis://redis:6379/0")
            .with_service_binding("dagger-engine", dagger_engine)
            .with_service_binding("redis", redis)
            .with_exposed_port(port)
            .with_exec([
                "uvicorn", "app.main:app",
                "--host", "0.0.0.0",
                "--port", str(port),
                "--log-level", "info"
            ])
        )
        
        return api_container.as_service()

    @function
    async def e2e_test(self) -> str:
        """Run end-to-end tests with all services."""
        # Start required services
        dagger_engine = (
            dag.container()
            .from_("docker:24-dind")
            .with_privileged()
            .with_exec(["dockerd"])
            .with_exposed_port(2375)
            .as_service()
        )
        
        # Start API service
        api_service = await self.prod(port=8000)
        
        # Build test container
        test_container = (
            await self.build_base()
            .with_directory("/app/app", dag.host().directory("app"))
            .with_directory("/app/tests", dag.host().directory("tests"))
            .with_env_variable("PYTHONPATH", "/app")
            .with_env_variable("API_BASE_URL", "http://api:8000")
            .with_service_binding("dagger-engine", dagger_engine)
            .with_service_binding("api", api_service)
        )
        
        # Run E2E tests
        result = await test_container.with_exec([
            "pytest", "-v", "-m", "e2e",
            "--tb=short"
        ]).stdout()
        
        return result

    @function
    async def build_production_image(self, tag: str = "aideator:latest") -> str:
        """Build production Docker image."""
        # Multi-stage build
        builder = (
            dag.container()
            .from_("python:3.11-slim")
            .with_exec(["pip", "install", "--upgrade", "pip", "uv"])
            .with_workdir("/app")
            .with_file("pyproject.toml", dag.host().file("pyproject.toml"))
            .with_exec(["uv", "pip", "install", "-e", "."])
        )
        
        # Production image
        prod_image = (
            dag.container()
            .from_("python:3.11-slim")
            .with_exec(["apt-get", "update"])
            .with_exec([
                "apt-get", "install", "-y",
                "git", "curl", "--no-install-recommends"
            ])
            .with_exec(["rm", "-rf", "/var/lib/apt/lists/*"])
            .with_workdir("/app")
            # Copy installed packages from builder
            .with_directory(
                "/usr/local/lib/python3.11/site-packages",
                builder.directory("/usr/local/lib/python3.11/site-packages")
            )
            .with_directory("/app/app", dag.host().directory("app"))
            .with_env_variable("PYTHONPATH", "/app")
            .with_exposed_port(8000)
            .with_entrypoint([
                "gunicorn", "app.main:app",
                "-w", "4",
                "-k", "uvicorn.workers.UvicornWorker",
                "--bind", "0.0.0.0:8000"
            ])
        )
        
        # Export to local Docker
        await prod_image.export(tag)
        
        return f"Production image built and tagged as: {tag}"

    @function
    async def migrate_database(self) -> str:
        """Run database migrations."""
        base = await self.build_base()
        
        migrate_container = (
            base
            .with_directory("/app/app", dag.host().directory("app"))
            .with_file(".env", dag.host().file(".env.example"))
            .with_exec(["python", "-c", """
import asyncio
from app.core.database import create_db_and_tables
asyncio.run(create_db_and_tables())
print("Database migrations completed successfully!")
"""])
        )
        
        result = await migrate_container.stdout()
        return result

    @function
    async def generate_openapi_spec(self) -> dagger.File:
        """Generate OpenAPI specification file."""
        base = await self.build_base()
        
        generator = (
            base
            .with_directory("/app/app", dag.host().directory("app"))
            .with_env_variable("PYTHONPATH", "/app")
            .with_exec(["python", "-c", """
import json
from app.main import app

# Generate OpenAPI schema
openapi_schema = app.openapi()

# Write to file
with open("/tmp/openapi.json", "w") as f:
    json.dump(openapi_schema, f, indent=2)

print("OpenAPI spec generated successfully!")
"""])
        )
        
        await generator.sync()
        
        return generator.file("/tmp/openapi.json")

    @function
    async def ci_pipeline(self) -> str:
        """Run complete CI pipeline."""
        results = []
        
        # Run all checks sequentially to capture output
        try:
            lint_result = await self.lint()
            results.append(f"✅ Lint: PASSED\n{lint_result}\n")
        except Exception as e:
            results.append(f"❌ Lint: FAILED\n{str(e)}\n")
        
        try:
            type_result = await self.type_check()
            results.append(f"✅ Type Check: PASSED\n{type_result}\n")
        except Exception as e:
            results.append(f"❌ Type Check: FAILED\n{str(e)}\n")
        
        try:
            security_result = await self.security_scan()
            results.append(f"✅ Security Scan: PASSED\n{security_result}\n")
        except Exception as e:
            results.append(f"❌ Security Scan: FAILED\n{str(e)}\n")
        
        try:
            unit_result = await self.test(markers="unit")
            results.append(f"✅ Unit Tests: PASSED\n{unit_result}\n")
        except Exception as e:
            results.append(f"❌ Unit Tests: FAILED\n{str(e)}\n")
        
        try:
            integration_result = await self.test(markers="integration")
            results.append(f"✅ Integration Tests: PASSED\n{integration_result}\n")
        except Exception as e:
            results.append(f"❌ Integration Tests: FAILED\n{str(e)}\n")
        
        return "\n".join(results)