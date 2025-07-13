"""
Background task for syncing models from LiteLLM proxy.
"""

import asyncio
import contextlib
import logging
from datetime import timedelta

from app.core.database import get_sync_session
from app.services.model_sync_service import model_sync_service

logger = logging.getLogger(__name__)


class ModelSyncTask:
    """Background task that periodically syncs models from LiteLLM proxy."""

    def __init__(self, sync_interval_minutes: int = 60):
        self.sync_interval = timedelta(minutes=sync_interval_minutes)
        self.is_running = False
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start the background sync task."""
        if self.is_running:
            logger.warning("Model sync task is already running")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._run_sync_loop())
        logger.info("Model sync task started")

    async def stop(self) -> None:
        """Stop the background sync task."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        logger.info("Model sync task stopped")

    async def _run_sync_loop(self) -> None:
        """Main sync loop."""
        # Run initial sync
        await self._sync_once()

        while self.is_running:
            try:
                # Wait for next sync interval
                await asyncio.sleep(self.sync_interval.total_seconds())

                if self.is_running:
                    await self._sync_once()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in model sync loop: {e!s}")
                # Continue running even if sync fails

    async def _sync_once(self) -> None:
        """Run a single sync operation."""
        logger.info("Starting model sync from LiteLLM proxy")

        try:
            for session in get_sync_session():
                sync_log = await model_sync_service.sync_models(session)

                logger.info(
                    f"Model sync completed: "
                    f"discovered={sync_log.models_discovered}, "
                    f"added={sync_log.models_added}, "
                    f"updated={sync_log.models_updated}, "
                    f"deactivated={sync_log.models_deactivated}"
                )

        except Exception as e:
            logger.error(f"Model sync failed: {e!s}")

    async def sync_now(self) -> None:
        """Trigger an immediate sync (useful for manual triggers)."""
        await self._sync_once()


# Global instance
model_sync_task = ModelSyncTask()
