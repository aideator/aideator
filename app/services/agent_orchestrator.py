"""
Agent orchestrator using Kubernetes jobs with Redis-based streaming.
"""

import asyncio
import json
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.run import Run, RunStatus
from app.schemas.runs import AgentConfig
from app.services.kubernetes_service import KubernetesService
from app.services.redis_service import redis_service

logger = get_logger(__name__)
settings = get_settings()


class AgentOrchestrator:
    """Orchestrates LLM agents using Kubernetes jobs."""

    def __init__(self, kubernetes_service: KubernetesService):
        self.kubernetes = kubernetes_service
        self.active_runs: dict[str, dict[str, Any]] = {}
        self._job_count_lock = asyncio.Lock()
        self._total_active_jobs = 0

    async def _check_concurrency_limits(self, requested_jobs: int) -> bool:
        """Check if we can create the requested number of jobs.
        
        Returns True if within limits, False otherwise.
        """
        async with self._job_count_lock:
            # Check run limit
            if len(self.active_runs) >= settings.max_concurrent_runs:
                logger.warning(f"Max concurrent runs limit reached: {settings.max_concurrent_runs}")
                return False

            # Check job limit
            if self._total_active_jobs + requested_jobs > settings.max_concurrent_jobs:
                logger.warning(
                    f"Would exceed max concurrent jobs: {self._total_active_jobs} + {requested_jobs} > {settings.max_concurrent_jobs}"
                )
                return False

            return True

    async def _increment_job_count(self, count: int) -> None:
        """Increment the active job count."""
        async with self._job_count_lock:
            self._total_active_jobs += count
            logger.info(f"Active jobs: {self._total_active_jobs}")

    async def _decrement_job_count(self, count: int) -> None:
        """Decrement the active job count."""
        async with self._job_count_lock:
            self._total_active_jobs -= count
            self._total_active_jobs = max(0, self._total_active_jobs)  # Ensure non-negative
            logger.info(f"Active jobs: {self._total_active_jobs}")

    async def execute_variations(
        self,
        run_id: str,
        repo_url: str,
        prompt: str,
        variations: int,
        agent_config: AgentConfig | None = None,
        agent_mode: str | None = None,
        db_session: AsyncSession | None = None,
    ) -> None:
        """Execute N agent variations using Kubernetes jobs."""
        logger.info(
            "starting_agent_orchestration",
            run_id=run_id,
            variations=variations,
            repo_url=repo_url,
        )

        # Check concurrency limits before starting
        if not await self._check_concurrency_limits(variations):
            raise RuntimeError(
                f"Cannot start run: would exceed concurrency limits. "
                f"Active runs: {len(self.active_runs)}/{settings.max_concurrent_runs}, "
                f"Active jobs: {self._total_active_jobs}/{settings.max_concurrent_jobs}"
            )

        # Update run status
        if db_session:
            await self._update_run_status(
                db_session, run_id, RunStatus.RUNNING
            )

        # Store run metadata and increment job count
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
            # Increment job count
            await self._increment_job_count(variations)

            await self._execute_individual_jobs(run_id, repo_url, prompt, variations, agent_mode, db_session)

        except Exception as e:
            logger.error(f"Error executing variations for run {run_id}: {e}")
            self.active_runs[run_id]["status"] = "failed"
            
            # Publish error to Redis
            await redis_service.publish_status(
                run_id,
                "failed",
                {"error": str(e)}
            )

            # Decrement job count on failure
            await self._decrement_job_count(variations)

            # Update database status
            if db_session:
                await self._update_run_status(db_session, run_id, RunStatus.FAILED)

        finally:
            # Clean up run metadata after some time
            asyncio.create_task(self._cleanup_run_metadata(run_id, delay=3600))


    async def _execute_individual_jobs(
        self,
        run_id: str,
        repo_url: str,
        prompt: str,
        variations: int,
        agent_mode: str | None = None,
        db_session: AsyncSession | None = None,
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
                agent_mode=agent_mode,
            )
            jobs.append((job_name, i))

        self.active_runs[run_id]["jobs"] = [job[0] for job in jobs]
        self.active_runs[run_id]["status"] = "running"

        # Publish start event to Redis
        await redis_service.publish_status(
            run_id,
            "started",
            {"message": f"Created {len(jobs)} agent jobs", "jobs": [job[0] for job in jobs]}
        )
        
        # Monitor job statuses
        completed_variations = set()
        failed_variations = set()
        
        # Wait for all jobs to complete
        while len(completed_variations) + len(failed_variations) < variations:
            await asyncio.sleep(5)  # Check every 5 seconds
            
            for job_name, variation_id in jobs:
                if variation_id in completed_variations or variation_id in failed_variations:
                    continue
                    
                status = await self.kubernetes.get_job_status(job_name)
                
                if status["status"] == "completed":
                    completed_variations.add(variation_id)
                    await redis_service.publish_status(
                        run_id,
                        "variation_completed",
                        {"variation_id": variation_id, "job_name": job_name}
                    )
                elif status["status"] == "failed":
                    failed_variations.add(variation_id)
                    await redis_service.publish_status(
                        run_id,
                        "variation_failed",
                        {"variation_id": variation_id, "job_name": job_name, "error": "Job failed"}
                    )

        # Publish run completion
        await redis_service.publish_status(
            run_id,
            "completed",
            {
                "completed_variations": list(completed_variations),
                "failed_variations": list(failed_variations),
                "total_variations": variations
            }
        )

        # Update database status
        if db_session:
            await self._update_run_status(db_session, run_id, RunStatus.COMPLETED)

    async def get_run_status(self, run_id: str) -> dict[str, Any]:
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
        
        # Publish cancellation to Redis
        await redis_service.publish_status(
            run_id,
            "cancelled",
            {"message": "Run cancelled by user"}
        )

        return success

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

                # Decrement job count
                variations = run_data.get("variations", 0)
                if variations > 0:
                    await self._decrement_job_count(variations)

                # Remove from active runs
                del self.active_runs[run_id]
                logger.info(f"Cleaned up run metadata for {run_id}")

    def get_active_runs(self) -> dict[str, dict[str, Any]]:
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