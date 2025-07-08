"""
Kubernetes service for managing agent jobs and log streaming.
Replaces Dagger with native Kubernetes orchestration.
"""

import asyncio
import json
import os
import tempfile
from typing import Dict, Any, AsyncGenerator, Optional, List
from uuid import uuid4
import yaml
from pathlib import Path
import subprocess
from datetime import datetime

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class KubernetesService:
    """Service for managing Kubernetes jobs and log streaming."""
    
    def __init__(self, namespace: str = "aideator"):
        self.namespace = namespace
        self.helm_chart_path = Path(__file__).parent.parent.parent / "deploy" / "charts" / "aideator"
        self.job_templates_dir = Path(__file__).parent.parent.parent / "k8s" / "jobs"
        self.kubectl_timeout = 300  # 5 minutes
        
    async def create_agent_job(
        self,
        run_id: str,
        variation_id: int,
        repo_url: str,
        prompt: str,
        agent_config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a Kubernetes job for an agent variation."""
        job_name = f"agent-{run_id}-{variation_id}"
        
        # Load job template
        template_path = self.job_templates_dir / "agent-job-template.yaml"
        with open(template_path, "r") as f:
            job_yaml = f.read()
        
        # Replace placeholders
        job_yaml = job_yaml.format(
            run_id=run_id,
            variation_id=variation_id,
            repo_url=repo_url,
            prompt=prompt.replace('"', '\\"'),  # Escape quotes
        )
        
        # Create temporary file for job manifest
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(job_yaml)
            job_file = f.name
        
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
    
    async def create_batch_job(
        self,
        run_id: str,
        repo_url: str,
        prompt: str,
        variations: int,
        parallelism: Optional[int] = None,
    ) -> str:
        """Create a batch job for multiple agent variations."""
        job_name = f"batch-{run_id}"
        parallelism = parallelism or min(variations, 3)  # Default to 3 parallel
        
        # Load batch job template
        template_path = self.job_templates_dir / "batch-job-template.yaml"
        with open(template_path, "r") as f:
            job_yaml = f.read()
        
        # Replace placeholders
        job_yaml = job_yaml.format(
            run_id=run_id,
            repo_url=repo_url,
            prompt=prompt.replace('"', '\\"'),
            parallelism=parallelism,
            completions=variations,
        )
        
        # Create temporary file for job manifest
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(job_yaml)
            job_file = f.name
        
        try:
            # Apply the job
            cmd = [
                "kubectl", "apply", "-f", job_file, 
                "--namespace", self.namespace
            ]
            result = await self._run_kubectl_command(cmd)
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to create batch job: {result.stderr}")
            
            logger.info(f"Created batch job {job_name} for run {run_id} with {variations} variations")
            return job_name
            
        finally:
            # Clean up temporary file
            os.unlink(job_file)
    
    async def stream_job_logs(
        self,
        job_name: str,
        run_id: str,
        variation_id: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream logs from a Kubernetes job."""
        # First, wait for pods to be created
        await self._wait_for_job_pods(job_name)
        
        # Get pods for this job
        pods = await self._get_job_pods(job_name)
        
        if not pods:
            logger.warning(f"No pods found for job {job_name}")
            return
        
        # Stream logs from all pods
        for pod in pods:
            async for log_line in self._stream_pod_logs(pod, run_id, variation_id):
                yield log_line
    
    async def stream_batch_job_logs(
        self,
        job_name: str,
        run_id: str,
    ) -> AsyncGenerator[str, None]:
        """Stream logs from all pods in a batch job."""
        # Wait for pods to be created
        await self._wait_for_job_pods(job_name)
        
        # Get all pods for this batch job
        pods = await self._get_job_pods(job_name)
        
        if not pods:
            logger.warning(f"No pods found for batch job {job_name}")
            return
        
        # Stream logs from all pods concurrently
        tasks = []
        for pod in pods:
            # Extract variation ID from pod name or index
            variation_id = self._extract_variation_id(pod)
            task = asyncio.create_task(
                self._stream_pod_logs_to_list(pod, run_id, variation_id)
            )
            tasks.append(task)
        
        # Collect all log streams
        log_streams = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge and yield all logs chronologically
        all_logs = []
        for logs in log_streams:
            if isinstance(logs, list):
                all_logs.extend(logs)
        
        # Sort by timestamp and yield
        all_logs.sort(key=lambda x: x.get('timestamp', ''))
        for log_entry in all_logs:
            yield json.dumps(log_entry)
    
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
        else:
            logger.error(f"Failed to delete job {job_name}: {result.stderr}")
            return False
    
    async def get_job_status(self, job_name: str) -> Dict[str, Any]:
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
    
    async def _run_kubectl_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
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
        except asyncio.TimeoutError:
            logger.error(f"kubectl command timed out: {' '.join(cmd)}")
            raise RuntimeError(f"kubectl command timed out after {self.kubectl_timeout}s")
    
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
    
    async def _get_job_pods(self, job_name: str) -> List[str]:
        """Get pod names for a job."""
        cmd = [
            "kubectl", "get", "pods",
            "--namespace", self.namespace,
            "--selector", f"job-name={job_name}",
            "-o", "jsonpath={.items[*].metadata.name}"
        ]
        
        result = await self._run_kubectl_command(cmd)
        if result.returncode != 0:
            logger.error(f"Failed to get pods for job {job_name}: {result.stderr}")
            return []
        
        pods = result.stdout.strip().split()
        return [pod for pod in pods if pod]
    
    async def _stream_pod_logs(
        self,
        pod_name: str,
        run_id: str,
        variation_id: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream logs from a specific pod."""
        cmd = [
            "kubectl", "logs", "-f", pod_name,
            "--namespace", self.namespace
            # Removed --tail 0 to get all logs from the beginning
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                log_line = line.decode().rstrip('\n')
                if log_line:
                    # Just yield the raw log line - the agent_orchestrator will handle parsing
                    # Add newline back to preserve original formatting
                    yield log_line + '\n'
            
            # Wait for process to complete
            await process.wait()
            
        except Exception as e:
            logger.error(f"Error streaming logs from pod {pod_name}: {e}")
            error_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "run_id": run_id,
                "variation_id": variation_id,
                "pod_name": pod_name,
                "message": f"Error streaming logs: {str(e)}",
                "type": "error"
            }
            yield json.dumps(error_entry)
    
    async def _stream_pod_logs_to_list(
        self,
        pod_name: str,
        run_id: str,
        variation_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Stream logs from a pod and return as a list."""
        logs = []
        async for log_line in self._stream_pod_logs(pod_name, run_id, variation_id):
            try:
                log_entry = json.loads(log_line)
                logs.append(log_entry)
            except json.JSONDecodeError:
                # Handle malformed JSON
                logs.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "run_id": run_id,
                    "variation_id": variation_id,
                    "pod_name": pod_name,
                    "message": log_line,
                    "type": "raw_output"
                })
        return logs
    
    def _extract_variation_id(self, pod_name: str) -> Optional[int]:
        """Extract variation ID from pod name."""
        # Pod names follow pattern: agent-{run_id}-{variation_id}-{suffix}
        # or batch-{run_id}-{index}-{suffix}
        parts = pod_name.split('-')
        if len(parts) >= 3:
            try:
                # Try to parse the third part as variation ID
                return int(parts[2])
            except ValueError:
                pass
        return None
    
    def _determine_job_status(self, status: Dict[str, Any]) -> str:
        """Determine job status from Kubernetes status."""
        if status.get("succeeded", 0) > 0:
            return "completed"
        elif status.get("failed", 0) > 0:
            return "failed"
        elif status.get("active", 0) > 0:
            return "running"
        else:
            return "pending"