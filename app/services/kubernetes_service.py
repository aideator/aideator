"""
Kubernetes service for managing agent jobs.
"""

import asyncio
import asyncio.subprocess
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class KubernetesService:
    """Service for managing Kubernetes jobs."""

    def __init__(self, namespace: str = "aideator"):
        self.namespace = namespace
        self.helm_chart_path = (
            Path(__file__).parent.parent.parent / "deploy" / "charts" / "aideator"
        )
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
            cmd = ["kubectl", "apply", "-f", job_file, "--namespace", self.namespace]
            result = await self._run_kubectl_command(cmd)

            if result.returncode != 0:
                stderr_str = (
                    result.stderr.decode("utf-8")
                    if isinstance(result.stderr, bytes)
                    else result.stderr
                )
                raise RuntimeError(f"Failed to create job: {stderr_str}")

            logger.info(
                f"Created job {job_name} for run {run_id}, variation {variation_id}"
            )
            return job_name

        finally:
            # Clean up temporary file
            os.unlink(job_file)

    async def delete_job(self, job_name: str) -> bool:
        """Delete a Kubernetes job."""
        cmd = [
            "kubectl",
            "delete",
            "job",
            job_name,
            "--namespace",
            self.namespace,
            "--ignore-not-found=true",
        ]

        result = await self._run_kubectl_command(cmd)
        if result.returncode == 0:
            logger.info(f"Deleted job {job_name}")
            return True
        stderr_str = (
            result.stderr.decode("utf-8")
            if isinstance(result.stderr, bytes)
            else result.stderr
        )
        logger.error(f"Failed to delete job {job_name}: {stderr_str}")
        return False

    async def cancel_run(self, run_id: str) -> bool:
        """Cancel all agent jobs for a run."""
        logger.info(f"Cancelling run {run_id}")

        # Get all jobs for this run
        cmd = [
            "kubectl",
            "get",
            "jobs",
            "--namespace",
            self.namespace,
            "-l",
            f"run-id={run_id}",
            "-o",
            "json",
        ]
        result = await self._run_kubectl_command(cmd)

        if result.returncode != 0:
            logger.error(f"Failed to get jobs for run {run_id}")
            return False

        try:
            jobs_data = json.loads(result.stdout)
            job_names = [job["metadata"]["name"] for job in jobs_data["items"]]

            if not job_names:
                logger.info(f"No jobs found for run {run_id}")
                return True

            # Delete all jobs for this run
            success = True
            for job_name in job_names:
                if not await self.delete_job(job_name):
                    success = False

            if success:
                logger.info(f"Successfully cancelled run {run_id}")
            else:
                logger.error(f"Failed to cancel some jobs for run {run_id}")

            return success

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse kubectl output for run {run_id}: {e}")
            return False

    async def get_job_status(self, job_name: str) -> dict[str, Any]:
        """Get the status of a Kubernetes job."""
        cmd = [
            "kubectl",
            "get",
            "job",
            job_name,
            "--namespace",
            self.namespace,
            "-o",
            "json",
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

    async def _run_kubectl_command(
        self, cmd: list[str]
    ) -> subprocess.CompletedProcess[bytes]:
        """Run a kubectl command asynchronously."""
        try:
            process = await asyncio.create_subprocess_exec(
                cmd[0],
                *cmd[1:],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self.kubectl_timeout
            )

            return subprocess.CompletedProcess(
                args=cmd,
                returncode=process.returncode or 0,
                stdout=stdout or b"",
                stderr=stderr or b"",
            )
        except TimeoutError:
            logger.error(f"kubectl command timed out: {' '.join(cmd)}")
            raise RuntimeError(
                f"kubectl command timed out after {self.kubectl_timeout}s"
            )

    async def _wait_for_job_pods(self, job_name: str, timeout: int = 60) -> None:
        """Wait for job pods to be created."""
        start_time = asyncio.get_event_loop().time()

        while True:
            pods = await self._get_job_pods(job_name)
            if pods:
                logger.info(f"Found {len(pods)} pods for job {job_name}")
                return

            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise RuntimeError(f"Timeout waiting for pods for job {job_name}")

            await asyncio.sleep(2)

    async def _get_job_pods(self, job_name: str) -> list[str]:
        """Get pod names for a job."""
        cmd = [
            "kubectl",
            "get",
            "pods",
            "--namespace",
            self.namespace,
            "--selector",
            f"job-name={job_name}",
            "-o",
            "jsonpath={.items[*].metadata.name}",
        ]

        result = await self._run_kubectl_command(cmd)
        if result.returncode != 0:
            stderr_str = (
                result.stderr.decode("utf-8")
                if isinstance(result.stderr, bytes)
                else result.stderr
            )
            logger.error(f"Failed to get pods for job {job_name}: {stderr_str}")
            return []

        stdout_str = (
            result.stdout.decode("utf-8")
            if isinstance(result.stdout, bytes)
            else result.stdout
        )
        pods = stdout_str.strip().split()
        return [pod for pod in pods if pod]

    def _extract_variation_id(self, pod_name: str) -> int | None:
        """Extract variation ID from pod name."""
        # Pod names follow pattern: agent-{run_id}-{variation_id}-{suffix}
        # or batch-{run_id}-{index}-{suffix}
        parts = pod_name.split("-")
        if len(parts) >= 3:
            try:
                # Try to parse the third part as variation ID
                return int(parts[2])
            except ValueError:
                pass
        return None

    def _determine_job_status(self, status: dict[str, Any]) -> str:
        """Determine job status from Kubernetes status."""
        if status.get("succeeded", 0) > 0:
            return "completed"
        if status.get("failed", 0) > 0:
            return "failed"
        if status.get("active", 0) > 0:
            return "running"
        return "pending"
