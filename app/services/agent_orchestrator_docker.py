"""Agent orchestrator using Docker for real-time streaming."""

import asyncio
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.run import Run, RunStatus
from app.schemas.runs import AgentConfig
from app.services.docker_service import DockerService
from app.services.sse_manager import sse_manager

settings = get_settings()
logger = get_logger(__name__)


class AgentOrchestratorDocker:
    """Orchestrates agent execution using Docker with real-time streaming."""
    
    def __init__(self):
        """Initialize orchestrator with Docker service."""
        self.docker = DockerService()
        self.sse = sse_manager
    
    async def execute_variations(
        self,
        run_id: str,
        repo_url: str,
        prompt: str,
        variations: int,
        agent_config: Optional[AgentConfig] = None,
        db_session: Optional[AsyncSession] = None,
        use_claude_code: bool = False,
    ) -> None:
        """Execute N agent variations in parallel Docker containers.
        
        Args:
            run_id: Unique run identifier
            repo_url: GitHub repository URL
            prompt: Agent prompt
            variations: Number of agent variations to run
            agent_config: Optional agent configuration
            db_session: Optional database session
            use_claude_code: Whether to use Claude Code
        """
        logger.info(
            "starting_agent_orchestration",
            run_id=run_id,
            variations=variations,
            repo_url=repo_url,
            orchestrator="docker",
        )
        
        # Update run status
        if db_session:
            await self._update_run_status(db_session, run_id, RunStatus.RUNNING)
        
        # Check if Docker is available
        if not self.docker.is_available():
            error_msg = "Docker is not available"
            logger.error(error_msg)
            if db_session:
                await self._update_run_status(db_session, run_id, RunStatus.FAILED)
            await self.sse.send_agent_error(run_id, 0, error_msg)
            await self.sse.send_run_complete(run_id, "failed")
            return
        
        # Build agent image once
        try:
            await self.docker.build_agent_image()
        except Exception as e:
            error_msg = f"Failed to build agent image: {str(e)}"
            logger.error(error_msg)
            if db_session:
                await self._update_run_status(db_session, run_id, RunStatus.FAILED)
            await self.sse.send_agent_error(run_id, 0, error_msg)
            await self.sse.send_run_complete(run_id, "failed")
            return
        
        # Create tasks for parallel execution
        tasks = []
        for i in range(variations):
            task = asyncio.create_task(
                self._execute_single_agent(
                    run_id=run_id,
                    repo_url=repo_url,
                    prompt=prompt,
                    variation_id=i,
                    agent_config=agent_config.model_dump() if agent_config else None,
                    use_claude_code=use_claude_code,
                )
            )
            tasks.append(task)
        
        # Execute all agents in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check results
        successful = sum(1 for r in results if not isinstance(r, Exception) and r)
        failed = sum(1 for r in results if isinstance(r, Exception) or not r)
        
        logger.info(
            "agent_orchestration_complete",
            run_id=run_id,
            successful=successful,
            failed=failed,
        )
        
        # Update run status
        if db_session:
            status = RunStatus.COMPLETED if successful > 0 else RunStatus.FAILED
            await self._update_run_status(db_session, run_id, status)
        
        # Send completion event
        await self.sse.send_run_complete(
            run_id, "completed" if successful > 0 else "failed"
        )
    
    async def _execute_single_agent(
        self,
        run_id: str,
        repo_url: str,
        prompt: str,
        variation_id: int,
        agent_config: Optional[Dict[str, Any]] = None,
        use_claude_code: bool = False,
    ) -> bool:
        """Execute a single agent variation using Docker.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(
            "starting_agent_execution",
            run_id=run_id,
            variation_id=variation_id,
        )
        
        try:
            line_count = 0
            
            # Stream output from Docker container
            async for line in self.docker.stream_agent_output(
                repo_url=repo_url,
                prompt=prompt,
                variation_id=variation_id,
                agent_config=agent_config,
                use_claude_code=use_claude_code,
            ):
                # Check for errors
                if line.startswith("ERROR:"):
                    await self.sse.send_agent_error(run_id, variation_id, line[6:].strip())
                    return False
                else:
                    # Send output to SSE
                    await self.sse.send_agent_output(run_id, variation_id, line)
                    line_count += 1
            
            # Mark agent as complete
            await self.sse.send_agent_complete(run_id, variation_id)
            
            logger.info(
                "agent_execution_complete",
                run_id=run_id,
                variation_id=variation_id,
                lines_streamed=line_count,
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "agent_execution_failed",
                run_id=run_id,
                variation_id=variation_id,
                error=str(e),
            )
            await self.sse.send_agent_error(run_id, variation_id, str(e))
            return False
    
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


# Singleton instance
agent_orchestrator_docker = AgentOrchestratorDocker()