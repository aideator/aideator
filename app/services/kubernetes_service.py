"""
Kubernetes service for managing agent jobs.
"""

import asyncio
import json
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class KubernetesService:
    """Service for managing Kubernetes jobs."""

    def __init__(self, namespace: str = "aideator"):
        self.namespace = namespace
        self.helm_chart_path = Path(__file__).parent.parent.parent / "deploy" / "charts" / "aideator"
        self.job_templates_dir = Path(__file__).parent.parent.parent / "k8s" / "jobs"
        self.kubectl_timeout = 300  # 5 minutes

    def _escape_yaml_string(self, value: str) -> str:
        """Properly escape a string for YAML to prevent injection attacks.
        
        Uses JSON encoding which is valid YAML and handles all special cases.
        """
        # JSON strings are valid YAML and handle all escaping properly
        return json.dumps(value)

    async def create_agent_job(
        self,
        run_id: str,
        variation_id: int,
        repo_url: str,
        prompt: str,
        agent_config: dict[str, Any] | None = None,
        agent_mode: str | None = None,
    ) -> str:
        """Create a Kubernetes job for an agent variation."""
        job_name = f"agent-{run_id}-{variation_id}"

        # Load job template
        template_path = self.job_templates_dir / "agent-job-template.yaml"
        with open(template_path) as f:
            job_yaml = f.read()

        # Replace placeholders
        job_yaml = job_yaml.format(
            run_id=run_id,
            variation_id=variation_id,
            repo_url=repo_url,
            prompt=self._escape_yaml_string(prompt),  # Proper YAML escaping
            agent_mode=agent_mode or "litellm",  # Default to litellm
        )

        # Create temporary file for job manifest
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(job_yaml)
            job_file = f.name
        
        # Debug: Log the YAML content
        logger.debug(f"Generated YAML for job {job_name}:\n{job_yaml}")

        try:
            # Apply the job
            cmd = [
                "kubectl", "apply", "-f", job_file,
                "--namespace", self.namespace
            ]
            result = await self._run_kubectl_command(cmd)

            if result.returncode != 0:
                raise RuntimeError(f"Failed to create job: {result.stderr}")

            logger.info(f"Created job {job_name} for run {run_id}, variation {variation_id}")
            return job_name

        finally:
            # Clean up temporary file
            os.unlink(job_file)

    async def delete_job(self, job_name: str) -> bool:
        """Delete a Kubernetes job."""
        cmd = [
            "kubectl", "delete", "job", job_name,
            "--namespace", self.namespace,
            "--ignore-not-found=true"
        ]

        result = await self._run_kubectl_command(cmd)
        if result.returncode == 0:
            logger.info(f"Deleted job {job_name}")
            return True
        logger.error(f"Failed to delete job {job_name}: {result.stderr}")
        return False

    async def get_job_status(self, job_name: str) -> dict[str, Any]:
        """Get the status of a Kubernetes job."""
        cmd = [
            "kubectl", "get", "job", job_name,
            "--namespace", self.namespace,
            "-o", "json"
        ]

        result = await self._run_kubectl_command(cmd)
        if result.returncode != 0:
            return {"status": "not_found", "error": result.stderr}

        try:
            job_data = json.loads(result.stdout)
            status = job_data.get("status", {})

            return {
                "status": self._determine_job_status(status),
                "conditions": status.get("conditions", []),
                "active": status.get("active", 0),
                "succeeded": status.get("succeeded", 0),
                "failed": status.get("failed", 0),
                "start_time": status.get("startTime"),
                "completion_time": status.get("completionTime"),
            }
        except json.JSONDecodeError:
            return {"status": "error", "error": "Invalid JSON response"}

    async def _run_kubectl_command(self, cmd: list[str]) -> subprocess.CompletedProcess:
        """Run a kubectl command asynchronously."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.kubectl_timeout
            )

            return subprocess.CompletedProcess(
                args=cmd,
                returncode=process.returncode,
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else "",
            )
        except TimeoutError:
            logger.error(f"kubectl command timed out: {' '.join(cmd)}")
            raise RuntimeError(f"kubectl command timed out after {self.kubectl_timeout}s")

    def _determine_job_status(self, status: dict) -> str:
        """Determine the simplified status of a job."""
        if status.get("succeeded", 0) > 0:
            return "completed"
        if status.get("failed", 0) > 0:
            return "failed"
        if status.get("active", 0) > 0:
            return "running"
        return "pending"
