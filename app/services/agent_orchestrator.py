"""
Agent orchestrator using Kubernetes jobs and kubectl log streaming.
"""

import asyncio
import json
from typing import Dict, Any, AsyncGenerator, Optional, List
from uuid import uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.run import Run, RunStatus
from app.schemas.runs import AgentConfig
from app.services.kubernetes_service import KubernetesService
from app.services.sse_manager import sse_manager, SSEManager

logger = get_logger(__name__)
settings = get_settings()


class AgentOrchestrator:
    """Orchestrates LLM agents using Kubernetes jobs."""
    
    def __init__(self, kubernetes_service: KubernetesService, sse_manager_instance: SSEManager = None):
        self.kubernetes = kubernetes_service
        self.sse = sse_manager_instance or sse_manager
        self.active_runs: Dict[str, Dict[str, Any]] = {}

    async def execute_variations(
        self,
        run_id: str,
        repo_url: str,
        prompt: str,
        variations: int,
        agent_config: Optional[AgentConfig] = None,
        db_session: Optional[AsyncSession] = None,
        use_batch_job: bool = True,
    ) -> None:
        """Execute N agent variations using Kubernetes jobs."""
        logger.info(
            "starting_agent_orchestration",
            run_id=run_id,
            variations=variations,
            repo_url=repo_url,
        )
        
        # Update run status
        if db_session:
            await self._update_run_status(
                db_session, run_id, RunStatus.RUNNING
            )
        
        # Store run metadata
        self.active_runs[run_id] = {
            "repo_url": repo_url,
            "prompt": prompt,
            "variations": variations,
            "agent_config": agent_config.model_dump() if agent_config else None,
            "status": "starting",
            "start_time": datetime.utcnow().isoformat(),
            "jobs": []
        }
        
        try:
            if use_batch_job:
                await self._execute_batch_job(run_id, repo_url, prompt, variations, db_session)
            else:
                await self._execute_individual_jobs(run_id, repo_url, prompt, variations, db_session)
            
        except Exception as e:
            logger.error(f"Error executing variations for run {run_id}: {e}")
            await self._send_error_event(run_id, str(e))
            self.active_runs[run_id]["status"] = "failed"
            
            # Update database status
            if db_session:
                await self._update_run_status(db_session, run_id, RunStatus.FAILED)
        
        finally:
            # Clean up run metadata after some time
            asyncio.create_task(self._cleanup_run_metadata(run_id, delay=3600))

    async def _execute_batch_job(
        self,
        run_id: str,
        repo_url: str,
        prompt: str,
        variations: int,
        db_session: Optional[AsyncSession] = None,
    ) -> None:
        """Execute agents using a single batch job."""
        # Create batch job
        job_name = await self.kubernetes.create_batch_job(
            run_id=run_id,
            repo_url=repo_url,
            prompt=prompt,
            variations=variations,
            parallelism=min(variations, 3)  # Max 3 parallel
        )
        
        self.active_runs[run_id]["jobs"].append(job_name)
        self.active_runs[run_id]["status"] = "running"
        
        # Send start event
        await self._send_status_event(run_id, "started", f"Batch job {job_name} created")
        
        # Stream logs from batch job
        await self._stream_batch_job_logs(run_id, job_name, db_session)
    
    async def _execute_individual_jobs(
        self,
        run_id: str,
        repo_url: str,
        prompt: str,
        variations: int,
        db_session: Optional[AsyncSession] = None,
    ) -> None:
        """Execute agents using individual jobs."""
        # Create individual jobs
        jobs = []
        for i in range(variations):
            job_name = await self.kubernetes.create_agent_job(
                run_id=run_id,
                variation_id=i,
                repo_url=repo_url,
                prompt=prompt,
            )
            jobs.append((job_name, i))
        
        self.active_runs[run_id]["jobs"] = [job[0] for job in jobs]
        self.active_runs[run_id]["status"] = "running"
        
        # Send start event
        await self._send_status_event(run_id, "started", f"Created {len(jobs)} agent jobs")
        
        # Stream logs from all jobs concurrently
        tasks = []
        for job_name, variation_id in jobs:
            task = asyncio.create_task(
                self._stream_job_logs(run_id, job_name, variation_id)
            )
            tasks.append(task)
        
        # Wait for all streaming tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update database status
        if db_session:
            await self._update_run_status(db_session, run_id, RunStatus.COMPLETED)
    
    async def _stream_batch_job_logs(
        self, 
        run_id: str, 
        job_name: str, 
        db_session: Optional[AsyncSession] = None
    ) -> None:
        """Stream logs from a batch job."""
        try:
            async for log_line in self.kubernetes.stream_batch_job_logs(job_name, run_id):
                try:
                    log_entry = json.loads(log_line)
                    if 'variation_id' in log_entry:
                        await self.sse.send_agent_output(run_id, log_entry['variation_id'], log_entry['message'])
                    else:
                        await self.sse.send_agent_output(run_id, 0, log_entry['message'])
                except json.JSONDecodeError:
                    # Handle raw text logs
                    await self.sse.send_agent_output(run_id, 0, log_line)
            
            # Send completion event
            await self._send_status_event(run_id, "completed", f"Batch job {job_name} completed")
            self.active_runs[run_id]["status"] = "completed"
            
            # Update database status
            if db_session:
                await self._update_run_status(db_session, run_id, RunStatus.COMPLETED)
            
        except Exception as e:
            logger.error(f"Error streaming batch job logs for run {run_id}: {e}")
            await self._send_error_event(run_id, f"Log streaming error: {str(e)}")
            self.active_runs[run_id]["status"] = "failed"
            
            # Update database status
            if db_session:
                await self._update_run_status(db_session, run_id, RunStatus.FAILED)
    
    async def _stream_job_logs(self, run_id: str, job_name: str, variation_id: int) -> None:
        """Stream logs from an individual job."""
        try:
            async for log_line in self.kubernetes.stream_job_logs(job_name, run_id, variation_id):
                try:
                    log_entry = json.loads(log_line)
                    if 'variation_id' in log_entry:
                        await self.sse.send_agent_output(run_id, log_entry['variation_id'], log_entry['message'])
                    else:
                        await self.sse.send_agent_output(run_id, 0, log_entry['message'])
                except json.JSONDecodeError:
                    # Handle raw text logs
                    await self.sse.send_agent_output(run_id, variation_id, log_line)
            
            # Send job completion event
            await self._send_status_event(
                run_id, 
                "job_completed", 
                f"Job {job_name} (variation {variation_id}) completed"
            )
            
        except Exception as e:
            logger.error(f"Error streaming job logs for {job_name}: {e}")
            await self._send_error_event(run_id, f"Job {job_name} error: {str(e)}")
    
    async def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """Get the status of a run."""
        if run_id not in self.active_runs:
            return {"status": "not_found", "error": "Run not found"}
        
        run_data = self.active_runs[run_id]
        
        # Get job statuses
        job_statuses = []
        for job_name in run_data["jobs"]:
            job_status = await self.kubernetes.get_job_status(job_name)
            job_statuses.append({
                "job_name": job_name,
                "status": job_status
            })
        
        return {
            "run_id": run_id,
            "status": run_data["status"],
            "start_time": run_data["start_time"],
            "variations": run_data["variations"],
            "jobs": job_statuses,
            "repo_url": run_data["repo_url"],
            "prompt": run_data["prompt"]
        }
    
    async def cancel_run(self, run_id: str) -> bool:
        """Cancel a running job."""
        if run_id not in self.active_runs:
            return False
        
        run_data = self.active_runs[run_id]
        
        # Delete all jobs for this run
        success = True
        for job_name in run_data["jobs"]:
            deleted = await self.kubernetes.delete_job(job_name)
            if not deleted:
                success = False
        
        # Update run status
        run_data["status"] = "cancelled"
        await self._send_status_event(run_id, "cancelled", "Run cancelled by user")
        
        return success
    
    async def _send_status_event(self, run_id: str, status: str, message: str) -> None:
        """Send a status event via SSE."""
        await self.sse.send_agent_output(run_id, 0, f"STATUS: {status} - {message}")
    
    async def _send_error_event(self, run_id: str, error: str) -> None:
        """Send an error event via SSE."""
        await self.sse.send_agent_error(run_id, 0, error)
    
    async def _cleanup_run_metadata(self, run_id: str, delay: int = 3600) -> None:
        """Clean up run metadata after a delay."""
        await asyncio.sleep(delay)
        
        if run_id in self.active_runs:
            run_data = self.active_runs[run_id]
            
            # Only cleanup if the run is completed/failed/cancelled
            if run_data["status"] in ["completed", "failed", "cancelled"]:
                # Delete associated jobs
                for job_name in run_data["jobs"]:
                    await self.kubernetes.delete_job(job_name)
                
                # Remove from active runs
                del self.active_runs[run_id]
                logger.info(f"Cleaned up run metadata for {run_id}")
    
    def get_active_runs(self) -> Dict[str, Dict[str, Any]]:
        """Get all active runs."""
        return dict(self.active_runs)

    async def _update_run_status(
        self, db_session: AsyncSession, run_id: str, status: RunStatus
    ) -> None:
        """Update run status in database."""
        try:
            run = await db_session.get(Run, run_id)
            if run:
                run.status = status
                await db_session.commit()
        except Exception as e:
            logger.error(f"Failed to update run status: {e}")
            await db_session.rollback()