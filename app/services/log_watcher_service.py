"""Kubernetes log watcher service for capturing job stdout/stderr."""

import asyncio
import json
from typing import Any

from app.core.logging import get_logger
from app.services.redis_service import redis_service

logger = get_logger(__name__)


class LogWatcherService:
    """Service for watching and streaming Kubernetes job logs to Redis."""

    def __init__(self, namespace: str = "aideator"):
        self.namespace = namespace
        self.active_watchers: dict[str, asyncio.Task] = {}

    async def start_log_watcher(self, run_id: str, job_name: str) -> None:
        """Start watching logs for a Kubernetes job.
        
        Args:
            run_id: The run ID
            job_name: The Kubernetes job name
        """
        # Stop any existing watcher for this run
        await self.stop_log_watcher(run_id)
        
        # Create new watcher task
        watcher_task = asyncio.create_task(
            self._watch_logs(run_id, job_name),
            name=f"log_watcher_{run_id}"
        )
        self.active_watchers[run_id] = watcher_task
        
        logger.info(f"Started log watcher for run {run_id}, job {job_name}")

    async def stop_log_watcher(self, run_id: str) -> None:
        """Stop watching logs for a run.
        
        Args:
            run_id: The run ID
        """
        if run_id in self.active_watchers:
            watcher_task = self.active_watchers[run_id]
            watcher_task.cancel()
            try:
                await watcher_task
            except asyncio.CancelledError:
                pass
            del self.active_watchers[run_id]
            logger.info(f"Stopped log watcher for run {run_id}")

    async def _watch_logs(self, run_id: str, job_name: str) -> None:
        """Watch logs from a Kubernetes job and stream to Redis.
        
        Args:
            run_id: The run ID
            job_name: The Kubernetes job name
        """
        cmd = [
            "kubectl", "logs", "-f",
            f"job/{job_name}",
            "--namespace", self.namespace,
            "--timestamps=false",
            "--all-containers=true",
            "--max-log-requests=10",
        ]

        logger.info(f"Starting kubectl logs for job {job_name}: {' '.join(cmd)}")

        try:
            # Start kubectl logs process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Stream stdout
            async def stream_output(stream, stream_type: str):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    
                    # Decode the line
                    line_str = line.decode('utf-8').rstrip()
                    if not line_str:
                        continue
                    
                    # Publish to Redis debug stream
                    try:
                        # Check if it's JSON log from agent
                        is_json = False
                        if line_str.startswith('{') and line_str.endswith('}'):
                            try:
                                json.loads(line_str)
                                is_json = True
                            except json.JSONDecodeError:
                                pass
                        
                        # Add to debug stream
                        await redis_service.add_debug_log(
                            run_id=run_id,
                            log_line=line_str,
                            source=stream_type,
                            is_json=is_json,
                            metadata={"job_name": job_name}
                        )
                        
                    except Exception as e:
                        logger.error(f"Error publishing log to Redis: {e}")

            # Create tasks for both stdout and stderr
            stdout_task = asyncio.create_task(stream_output(process.stdout, "stdout"))
            stderr_task = asyncio.create_task(stream_output(process.stderr, "stderr"))

            # Wait for process to complete or be cancelled
            await asyncio.gather(stdout_task, stderr_task)
            await process.wait()

            exit_code = process.returncode
            if exit_code != 0:
                logger.warning(f"kubectl logs exited with code {exit_code} for job {job_name}")
            else:
                logger.info(f"kubectl logs completed successfully for job {job_name}")

        except asyncio.CancelledError:
            # Clean shutdown
            if process and process.returncode is None:
                process.terminate()
                await process.wait()
            raise
        except Exception as e:
            logger.error(f"Error watching logs for job {job_name}: {e}")
            raise

    async def cleanup(self) -> None:
        """Stop all active log watchers."""
        logger.info(f"Cleaning up {len(self.active_watchers)} active log watchers")
        
        # Cancel all watchers
        tasks = list(self.active_watchers.values())
        for task in tasks:
            task.cancel()
        
        # Wait for all to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.active_watchers.clear()


# Global log watcher service instance
log_watcher_service = LogWatcherService()