"""
Database service for agent containers.

This service provides database connectivity for agents to write outputs
to the same PostgreSQL database that the frontend reads from.
"""

import logging
import os

# Import the shared models from the main app
import sys
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

sys.path.append("/app")
from app.models.task import Task, TaskOutput, TaskStatus
from app.models.run import Run # Retaining Run import as removal was not explicitly instructed for the entire import block

logger = logging.getLogger(__name__)


class DatabaseService:
    """Database service for agent containers."""

    def __init__(self):
        """Initialize database service with connection from environment."""
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        # Convert postgres:// to postgresql+asyncpg:// for async operations
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        self.engine = create_async_engine(
            self.database_url,
            echo=False,  # Set to True for SQL debugging
            pool_size=5,
            max_overflow=10,
        )

        self.async_session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        logger.info("DatabaseService initialized")

    async def health_check(self) -> bool:
        """Check if database connection is healthy."""
        try:
            async with self.async_session_factory() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def get_run_by_run_id(self, run_id: str) -> Run | None:
        """Get run by run_id (Kubernetes job identifier)."""
        try:
            async with self.async_session_factory() as session:
                query = select(Run).where(Run.run_id == run_id)
                result = await session.execute(query)
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get run by run_id {run_id}: {e}")
            return None

    async def get_run_by_task_id(self, task_id: int) -> Run | None:
        """Get run by task_id (primary key)."""
        try:
            async with self.async_session_factory() as session:
                query = select(Run).where(Run.task_id == task_id)
                result = await session.execute(query)
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get run by task_id {task_id}: {e}")
            return None

    async def get_task_by_id(self, task_id: int) -> Task | None:
        """Get a task by its primary key ID."""
        try:
            async with self.async_session_factory() as session:
                query = select(Task).where(Task.id == task_id)
                result = await session.execute(query)
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get task by ID {task_id}: {e}")
            return None

    async def get_task_by_internal_run_id(self, internal_run_id: str) -> Task | None:
        """Get a task by its internal_run_id (Kubernetes job identifier).
        
        DUAL LOOKUP: Tries unified tasks table first, then legacy runs table for compatibility.
        """
        try:
            async with self.async_session_factory() as session:
                # Try unified tasks table first
                query = select(Task).where(Task.internal_run_id == internal_run_id)
                result = await session.execute(query)
                task = result.scalar_one_or_none()
                
                if task:
                    logger.debug(f"Found task {task.id} via unified table")
                    return task
                
                # DUAL LOOKUP: Also try legacy runs table
                legacy_query = select(Run).where(Run.run_id == internal_run_id)
                legacy_result = await session.execute(legacy_query)
                legacy_run = legacy_result.scalar_one_or_none()
                
                if legacy_run:
                    logger.debug(f"Found legacy run {legacy_run.task_id} via legacy table")
                    # Convert legacy Run to Task for compatibility
                    return Task(
                        id=legacy_run.task_id,
                        internal_run_id=legacy_run.run_id,
                        github_url=legacy_run.github_url,
                        prompt=legacy_run.prompt,
                        variations=legacy_run.variations,
                        status=TaskStatus(legacy_run.status.value),
                        created_at=legacy_run.created_at,
                        started_at=legacy_run.started_at,
                        completed_at=legacy_run.completed_at,
                        agent_config=legacy_run.agent_config,
                        metadata=legacy_run.run_metadata,
                        user_id=legacy_run.user_id,
                        results=legacy_run.results,
                        error_message=legacy_run.error_message
                    )
                
                logger.debug(f"No task found for internal_run_id {internal_run_id}")
                return None
                
        except Exception as e:
            logger.error(
                f"Failed to get task by internal_run_id {internal_run_id}: {e}"
            )
            return None

    # Legacy helper removed – unified schema is now authoritative

    async def write_task_output(
        self,
        task_id: int,
        variation_id: int,
        content: str,
        output_type: str = "stdout",
        timestamp: datetime | None = None
    ) -> bool:
        """
        Canonical writer for the unified task_outputs table.
        DUAL WRITE: Writes to both task_outputs and agent_outputs for safety during migration.
        """
        write_timestamp = timestamp or datetime.utcnow()
        
        try:
            async with self.async_session_factory() as session:
                # Write to unified task_outputs table
                task_output = TaskOutput(
                    task_id=task_id,
                    variation_id=variation_id,
                    content=content,
                    output_type=output_type,
                    timestamp=write_timestamp
                )
                session.add(task_output)
                
                await session.commit()
                logger.debug(
                    f"Wrote {output_type} output for task {task_id}, variation {variation_id}"
                )
                return True
        except Exception as e:
            logger.error(f"Failed to write task output (dual write): {e}")
            try:
                await session.rollback()
            except Exception:
                pass
            return False

    async def write_agent_output(
        self,
        task_id: int,
        variation_id: int,
        content: str,
        output_type: str = "stdout",
        timestamp: datetime | None = None
    ) -> bool:
        # Backwards-compat shim – now a thin alias
        return await self.write_task_output(
            task_id=task_id,
            variation_id=variation_id,
            content=content,
            output_type=output_type,
            timestamp=timestamp,
        )

    async def write_status_update(
        self,
        task_id: int,
        status: TaskStatus,
        error_message: str | None = None
    ) -> bool:
        """
        Update task status (unified schema).

        Args:
            task_id: Primary key of the Task
            status: New status (TaskStatus enum)
            error_message: Optional error detail

        Returns:
            True on success
        """
        try:
            async with self.async_session_factory() as session:
                result = await session.execute(select(Task).where(Task.id == task_id))
                task_row = result.scalar_one_or_none()

                if not task_row:
                    logger.error(f"Task {task_id} not found")
                    return False

                task_row.status = status
                if error_message:
                    task_row.error_message = error_message

                if status == TaskStatus.RUNNING and not task_row.started_at:
                    task_row.started_at = datetime.utcnow()
                elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    task_row.completed_at = datetime.utcnow()

                await session.commit()
                logger.info(f"Task {task_id} status updated → {status}")
                return True
        except Exception as e:
            logger.error(f"write_status_update failed: {e}")
            try:
                await session.rollback()
            except Exception:
                pass
            return False

    async def write_error(
        self,
        task_id: int,
        variation_id: int,
        error_message: str,
        error_type: str = "error"
    ) -> bool:
        """
        Write error message to database.
        
        Args:
            task_id: The task ID
            variation_id: The variation number
            error_message: Error message content
            error_type: Type of error (error, exception, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        return await self.write_task_output(
            task_id=task_id,
            variation_id=variation_id,
            content=error_message,
            output_type=error_type
        )

    async def write_log(
        self,
        task_id: int,
        variation_id: int,
        log_message: str,
        log_level: str = "INFO"
    ) -> bool:
        """
        Write log message to database.
        
        Args:
            task_id: The task ID
            variation_id: The variation number
            log_message: Log message content
            log_level: Log level (DEBUG, INFO, WARNING, ERROR)
            
        Returns:
            True if successful, False otherwise
        """
        log_data = {
            "level": log_level,
            "message": log_message,
            "timestamp": datetime.utcnow().isoformat()
        }

        return await self.write_task_output(
            task_id=task_id,
            variation_id=variation_id,
            content=str(log_data),
            output_type="logging"
        )

    async def write_assistant_response(
        self,
        task_id: int,
        variation_id: int,
        response: str,
        timestamp: datetime | None = None
    ) -> bool:
        """
        Write clean assistant response to database.
        
        Args:
            task_id: The task ID
            variation_id: The variation number
            response: Clean AI assistant response
            timestamp: Optional timestamp
            
        Returns:
            True if successful, False otherwise
        """
        return await self.write_agent_output(
            task_id=task_id,
            variation_id=variation_id,
            content=response,
            output_type="assistant_response",
            timestamp=timestamp
        )

    async def write_system_status(
        self,
        task_id: int,
        variation_id: int,
        status_message: str,
        timestamp: datetime | None = None
    ) -> bool:
        """
        Write system status update to database.
        
        Args:
            task_id: The task ID
            variation_id: The variation number
            status_message: System status message
            timestamp: Optional timestamp
            
        Returns:
            True if successful, False otherwise
        """
        return await self.write_agent_output(
            task_id=task_id,
            variation_id=variation_id,
            content=status_message,
            output_type="system_status",
            timestamp=timestamp
        )

    async def write_debug_info(
        self,
        task_id: int,
        variation_id: int,
        debug_message: str,
        timestamp: datetime | None = None
    ) -> bool:
        """
        Write debug information to database.
        
        Args:
            task_id: The task ID
            variation_id: The variation number
            debug_message: Debug information
            timestamp: Optional timestamp
            
        Returns:
            True if successful, False otherwise
        """
        return await self.write_agent_output(
            task_id=task_id,
            variation_id=variation_id,
            content=debug_message,
            output_type="debug_info",
            timestamp=timestamp
        )

    async def close(self):
        """Close database connections."""
        try:
            await self.engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Convenience functions for common operations
async def write_startup_message(task_id: int, variation_id: int, message: str) -> bool:
    """Write a startup message to the database."""
    db_service = DatabaseService()
    return await db_service.write_log(task_id, variation_id, f"[Variation {variation_id}] {message}")


async def write_error_message(task_id: int, variation_id: int, error: str) -> bool:
    """Write an error message to the database."""
    db_service = DatabaseService()
    return await db_service.write_error(task_id, variation_id, f"[Variation {variation_id}] ERROR: {error}")


async def write_completion_message(task_id: int, variation_id: int, message: str) -> bool:
    """Write a completion message to the database."""
    db_service = DatabaseService()
    return await db_service.write_log(task_id, variation_id, f"[Variation {variation_id}] COMPLETED: {message}")
