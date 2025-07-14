"""Database service for agent dual-write functionality."""

import asyncio
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

        # Create async engine with proper pool configuration
        # Agent should use minimal connections since it's a single process
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=1,  # Single connection for agent
            max_overflow=0,  # No overflow connections
            pool_timeout=30,  # Match backend timeout
            pool_recycle=3600,  # Recycle connections after 1 hour
        )

        # Create session factory
        self.async_session_maker = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        
        # Batching configuration
        self._write_queue: list[dict[str, Any]] = []
        self._write_lock = asyncio.Lock()
        self._batch_task: asyncio.Task | None = None
        self._batch_size = 50  # Write in batches of 50
        self._batch_interval = 1.0  # Write every 1 second
        self._shutdown = False

    async def connect(self) -> None:
        """Connect to database and test connection."""
        # Test connection using a temporary session
        async with self.async_session_maker() as session:
            try:
                await session.execute(select(1))
                logger.info("Connected to database successfully")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise RuntimeError(f"Database connection failed: {e}")

    async def disconnect(self) -> None:
        """Disconnect from database and flush pending writes."""
        # Stop accepting new writes
        self._shutdown = True
        
        # Flush any remaining items
        async with self._write_lock:
            if self._write_queue:
                logger.info(f"[DB-FLUSH] Flushing {len(self._write_queue)} pending writes")
                await self._write_batch(self._write_queue)
                self._write_queue = []
        
        # Cancel batch task
        if self._batch_task and not self._batch_task.done():
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass
        
        await self.engine.dispose()

    async def write_agent_output(
        self,
        run_id: str,
        variation_id: int,
        content: str,
        output_type: str = "llm",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Queue agent output for batched writing to database.

        Args:
            run_id: The run ID
            variation_id: The variation ID
            content: The output content
            output_type: Type of output (llm, stdout, status, etc.)
            metadata: Optional metadata
        """
        # Add to queue
        async with self._write_lock:
            self._write_queue.append({
                "run_id": run_id,
                "variation_id": variation_id,
                "content": content,
                "output_type": output_type,
                "timestamp": datetime.utcnow(),
                "metadata": metadata
            })
            
            # Start batch writer if not running
            if self._batch_task is None or self._batch_task.done():
                self._batch_task = asyncio.create_task(self._batch_writer())
    
    async def _batch_writer(self):
        """Background task that writes batched outputs to database."""
        while not self._shutdown:
            try:
                # Wait for batch interval or until we have enough items
                await asyncio.sleep(self._batch_interval)
                
                # Get items to write
                async with self._write_lock:
                    if not self._write_queue:
                        continue
                        
                    # Take up to batch_size items
                    items_to_write = self._write_queue[:self._batch_size]
                    self._write_queue = self._write_queue[self._batch_size:]
                
                # Write batch to database
                await self._write_batch(items_to_write)
                
            except Exception as e:
                logger.error(f"[BATCH-WRITER] Error in batch writer: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def _write_batch(self, items: list[dict[str, Any]]) -> None:
        """Write a batch of outputs to the database."""
        if not items:
            return
            
        async with self.async_session_maker() as session:
            try:
                # Import here to avoid circular imports
                from app.models.run import AgentOutput
                
                # Create all output objects
                outputs = [
                    AgentOutput(
                        run_id=item["run_id"],
                        variation_id=item["variation_id"],
                        content=item["content"],
                        output_type=item["output_type"],
                        timestamp=item["timestamp"],
                    )
                    for item in items
                ]
                
                # Add all at once
                session.add_all(outputs)
                await session.commit()
                
                logger.debug(
                    f"[DB-BATCH] Wrote batch of {len(items)} outputs to database"
                )
                
            except Exception as e:
                logger.error(
                    f"[DB-BATCH] Failed to write batch of {len(items)} outputs: {e}"
                )
                await session.rollback()

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
        # Create a new session for this operation to avoid concurrency issues
        async with self.async_session_maker() as session:
            try:
                # Import here to avoid circular imports
                from app.models.run import Run, RunStatus

                # Get the run
                result = await session.execute(select(Run).where(Run.id == run_id))
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

                    await session.commit()

                    logger.info(
                        f"[DB-WRITE] Updated run status: run_id={run_id}, status={status}"
                    )
                else:
                    logger.warning(
                        f"[DB-WRITE] Run not found for status update: run_id={run_id}"
                    )

            except Exception as e:
                logger.error(f"[DB-WRITE] Failed to update run status: {e}")
                await session.rollback()
                # Don't raise - agent should continue even if DB write fails

    async def health_check(self) -> bool:
        """Check if database is healthy.

        Returns:
            True if healthy, False otherwise
        """
        # Create a new session for health check to avoid interfering with other operations
        async with self.async_session_maker() as session:
            try:
                await session.execute(select(1))
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
        # Create a new session for this operation to avoid concurrency issues
        async with self.async_session_maker() as session:
            try:
                # Import here to avoid circular imports
                from app.models.run import Run

                # Get the run
                result = await session.execute(select(Run).where(Run.id == run_id))
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

                    await session.commit()

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
                await session.rollback()
                # Don't raise - agent should continue even if DB write fails

    async def write_litellm_analytics(
        self,
        run_id: str,
        variation_id: int,
        analytics_data: dict[str, Any],
    ) -> None:
        """Write LiteLLM analytics data to database.

        Args:
            run_id: The run ID
            variation_id: The variation ID
            analytics_data: Dictionary containing LiteLLM analytics data
        """
        async with self.async_session_maker() as session:
            try:
                # Import here to avoid circular imports
                from app.models.run import LiteLLMAnalytics

                # Create analytics record
                analytics_record = LiteLLMAnalytics(
                    run_id=run_id,
                    variation_id=variation_id,
                    request_id=analytics_data.get("request_id"),
                    model=analytics_data.get("model", "unknown"),
                    provider=analytics_data.get("provider", "unknown"),
                    prompt_tokens=analytics_data.get("prompt_tokens"),
                    completion_tokens=analytics_data.get("completion_tokens"),
                    total_tokens=analytics_data.get("total_tokens"),
                    cost_usd=analytics_data.get("cost_usd"),
                    input_cost_per_token=analytics_data.get("input_cost_per_token"),
                    output_cost_per_token=analytics_data.get("output_cost_per_token"),
                    response_time_ms=analytics_data.get("response_time_ms"),
                    time_to_first_token_ms=analytics_data.get("time_to_first_token_ms"),
                    tokens_per_second=analytics_data.get("tokens_per_second"),
                    temperature=analytics_data.get("temperature"),
                    max_tokens=analytics_data.get("max_tokens"),
                    stream=analytics_data.get("stream", False),
                    status=analytics_data.get("status", "success"),
                    error_type=analytics_data.get("error_type"),
                    error_message=analytics_data.get("error_message"),
                    request_start_time=analytics_data.get("request_start_time"),
                    request_end_time=analytics_data.get("request_end_time"),
                    litellm_metadata=analytics_data.get("metadata", {}),
                )

                session.add(analytics_record)
                await session.commit()

                logger.info(
                    f"[DB-WRITE] Wrote LiteLLM analytics: run_id={run_id}, "
                    f"variation_id={variation_id}, model={analytics_data.get('model')}"
                )

            except Exception as e:
                logger.error(f"[DB-WRITE] Failed to write LiteLLM analytics: {e}")
                await session.rollback()
                # Don't raise - agent should continue even if DB write fails
