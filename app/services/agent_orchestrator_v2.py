"""Agent orchestrator using Dagger modules."""

import asyncio
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.run import Run, RunStatus
from app.schemas.runs import AgentConfig
from app.services.dagger_module_service import DaggerModuleService
from app.services.sse_manager import sse_manager

settings = get_settings()
logger = get_logger(__name__)


class AgentOrchestratorV2:
    """Orchestrates the execution of multiple agent variations using Dagger modules."""

    def __init__(self):
        self.dagger = DaggerModuleService()
        self.sse = sse_manager

    async def execute_variations(
        self,
        run_id: str,
        repo_url: str,
        prompt: str,
        variations: int,
        agent_config: Optional[AgentConfig] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> None:
        """Execute N agent variations in parallel containers."""
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

        # Check if Dagger is available
        if not self.dagger.is_available():
            error_msg = "Dagger CLI is not available"
            logger.error(error_msg)
            if db_session:
                await self._update_run_status(db_session, run_id, RunStatus.FAILED)
            await self.sse.send_run_error(run_id, error_msg)
            return

        tasks = []
        for i in range(variations):
            task = asyncio.create_task(
                self._execute_single_agent(
                    run_id=run_id,
                    repo_url=repo_url,
                    prompt=prompt,
                    variation_id=i,
                    agent_config=agent_config.model_dump() if agent_config else None,
                )
            )
            tasks.append(task)

        # Execute all agents in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check results
        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = sum(1 for r in results if isinstance(r, Exception))

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
    ) -> None:
        """Execute a single agent variation using Dagger module."""
        logger.info(
            "starting_agent_execution",
            run_id=run_id,
            variation_id=variation_id,
        )

        try:
            # Stream output from Dagger module
            async for line in self.dagger.stream_agent_output(
                repo_url=repo_url,
                prompt=prompt,
                variation_id=variation_id,
                agent_config=agent_config,
            ):
                # Send output to SSE
                await self.sse.send_agent_output(run_id, variation_id, line)

            # Mark agent as complete
            await self.sse.send_agent_complete(run_id, variation_id)

            logger.info(
                "agent_execution_complete",
                run_id=run_id,
                variation_id=variation_id,
            )

        except Exception as e:
            logger.error(
                "agent_execution_failed",
                run_id=run_id,
                variation_id=variation_id,
                error=str(e),
            )
            await self.sse.send_agent_error(run_id, variation_id, str(e))
            raise

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
agent_orchestrator_v2 = AgentOrchestratorV2()