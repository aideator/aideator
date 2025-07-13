"""Database service for agent dual-write functionality."""

import logging
import os
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

logger = logging.getLogger(__name__)


class AgentDatabaseService:
    """Database service for agent to write outputs to PostgreSQL."""

    def __init__(self):
        """Initialize the database service."""
        self.database_url = os.getenv("DATABASE_URL_ASYNC")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL_ASYNC environment variable not set")

        # Create async engine
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_pre_ping=True,
        )

        # Create session factory
        self.async_session_maker = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        self._session: AsyncSession | None = None

    async def connect(self) -> None:
        """Connect to database and create session."""
        try:
            self._session = self.async_session_maker()
            # Test connection
            await self._session.execute(select(1))
            logger.info("Connected to database successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise RuntimeError(f"Database connection failed: {e}")

    async def disconnect(self) -> None:
        """Disconnect from database."""
        if self._session:
            await self._session.close()
            self._session = None
        await self.engine.dispose()

    @property
    def session(self) -> AsyncSession:
        """Get database session."""
        if not self._session:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._session

    async def write_agent_output(
        self,
        run_id: str,
        variation_id: int,
        content: str,
        output_type: str = "llm",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Write agent output to database.

        Args:
            run_id: The run ID
            variation_id: The variation ID
            content: The output content
            output_type: Type of output (llm, stdout, status, etc.)
            metadata: Optional metadata
        """
        # Create a new session for this operation to avoid concurrency issues
        async with self.async_session_maker() as session:
            try:
                # Import here to avoid circular imports
                from app.models.run import AgentOutput

                output = AgentOutput(
                    run_id=run_id,
                    variation_id=variation_id,
                    content=content,
                    output_type=output_type,
                    timestamp=datetime.utcnow(),
                )

                session.add(output)
                await session.commit()

                logger.debug(
                    f"[DB-WRITE] Wrote {output_type} output to database: "
                    f"run_id={run_id}, variation_id={variation_id}, "
                    f"content_length={len(content)}"
                )

            except Exception as e:
                logger.error(
                    f"[DB-WRITE] Failed to write {output_type} output to database: {e}"
                )
                await session.rollback()
                # Don't raise - agent should continue even if DB write fails

    async def update_run_status(
        self,
        run_id: str,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update run status in database.

        Args:
            run_id: The run ID
            status: New status (running, completed, failed, etc.)
            metadata: Optional metadata
        """
        try:
            # Import here to avoid circular imports
            from app.models.run import Run, RunStatus

            # Get the run
            result = await self.session.execute(select(Run).where(Run.id == run_id))
            run = result.scalar_one_or_none()

            if run:
                # Update status
                if status == "running":
                    run.status = RunStatus.RUNNING
                    if not run.started_at:
                        run.started_at = datetime.utcnow()
                elif status == "completed":
                    run.status = RunStatus.COMPLETED
                    run.completed_at = datetime.utcnow()
                elif status == "failed":
                    run.status = RunStatus.FAILED
                    run.completed_at = datetime.utcnow()
                elif status == "cancelled":
                    run.status = RunStatus.CANCELLED
                    run.completed_at = datetime.utcnow()

                # Update metadata if provided
                if metadata:
                    if not run.results:
                        run.results = {}
                    run.results.update(metadata)

                await self.session.commit()

                logger.info(
                    f"[DB-WRITE] Updated run status: run_id={run_id}, status={status}"
                )
            else:
                logger.warning(
                    f"[DB-WRITE] Run not found for status update: run_id={run_id}"
                )

        except Exception as e:
            logger.error(f"[DB-WRITE] Failed to update run status: {e}")
            await self.session.rollback()
            # Don't raise - agent should continue even if DB write fails

    async def health_check(self) -> bool:
        """Check if database is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self._session:
                return False
            await self.session.execute(select(1))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def publish_log(
        self, message: str, level: str, **kwargs
    ) -> None:
        """Write log entry to database.

        Args:
            message: Log message
            level: Log level (INFO, DEBUG, WARNING, ERROR)
            **kwargs: Additional metadata
        """
        await self.write_agent_output(
            run_id=kwargs.get("run_id", ""),
            variation_id=kwargs.get("variation_id", 0),
            content=message,
            output_type="logging",
            metadata={"level": level, **kwargs}
        )

    async def update_run_stats(
        self,
        run_id: str,
        tokens_used: int | None = None,
        cost_usd: float | None = None,
        model: str | None = None,
        provider: str | None = None,
    ) -> None:
        """Update run statistics with LiteLLM usage data.

        Args:
            run_id: The run ID
            tokens_used: Number of tokens used
            cost_usd: Cost in USD
            model: Model name used
            provider: Provider name (openai, anthropic, etc.)
        """
        try:
            # Import here to avoid circular imports
            from app.models.run import Run

            # Get the run
            result = await self.session.execute(select(Run).where(Run.id == run_id))
            run = result.scalar_one_or_none()

            if run:
                # Update token usage
                if tokens_used is not None:
                    if run.total_tokens_used is None:
                        run.total_tokens_used = 0
                    run.total_tokens_used += tokens_used

                # Update cost
                if cost_usd is not None:
                    if run.total_cost_usd is None:
                        run.total_cost_usd = 0.0
                    run.total_cost_usd += cost_usd

                # Store model and provider info in results
                if model or provider:
                    if not run.results:
                        run.results = {}
                    if "llm_stats" not in run.results:
                        run.results["llm_stats"] = []

                    stat_entry = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "tokens_used": tokens_used,
                        "cost_usd": cost_usd,
                        "model": model,
                        "provider": provider
                    }
                    run.results["llm_stats"].append(stat_entry)

                await self.session.commit()

                logger.info(
                    f"[DB-WRITE] Updated run stats: run_id={run_id}, "
                    f"tokens={tokens_used}, cost={cost_usd}, model={model}"
                )
            else:
                logger.warning(
                    f"[DB-WRITE] Run not found for stats update: run_id={run_id}"
                )

        except Exception as e:
            logger.error(f"[DB-WRITE] Failed to update run stats: {e}")
            await self.session.rollback()
            # Don't raise - agent should continue even if DB write fails
