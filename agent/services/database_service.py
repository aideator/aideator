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
from app.models.run import AgentOutput, Run, RunStatus

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

    async def write_agent_output(
        self,
        task_id: int,
        variation_id: int,
        content: str,
        output_type: str = "stdout",
        timestamp: datetime | None = None
    ) -> bool:
        """
        Write agent output to the database.
        
        Args:
            task_id: The task ID (primary key of runs table)
            variation_id: The variation/agent number (0, 1, 2, etc.)
            content: The output content
            output_type: Type of output (stdout, stderr, status, summary, diffs, logging, addinfo)
            timestamp: Optional timestamp (defaults to current time)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with self.async_session_factory() as session:
                output = AgentOutput(
                    task_id=task_id,
                    variation_id=variation_id,
                    content=content,
                    output_type=output_type,
                    timestamp=timestamp or datetime.utcnow()
                )

                session.add(output)
                await session.commit()

                logger.debug(f"Wrote {output_type} output for task {task_id}, variation {variation_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to write agent output: {e}")
            try:
                await session.rollback()
            except:
                pass
            return False

    async def write_status_update(
        self,
        task_id: int,
        status: RunStatus,
        error_message: str | None = None
    ) -> bool:
        """
        Update run status in the database.
        
        Args:
            task_id: The task ID (primary key)
            status: New status
            error_message: Optional error message
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with self.async_session_factory() as session:
                query = select(Run).where(Run.task_id == task_id)
                result = await session.execute(query)
                run = result.scalar_one_or_none()

                if not run:
                    logger.error(f"Run with task_id {task_id} not found")
                    return False

                run.status = status
                if error_message:
                    run.error_message = error_message

                if status == RunStatus.RUNNING and not run.started_at:
                    run.started_at = datetime.utcnow()
                elif status in [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED]:
                    run.completed_at = datetime.utcnow()

                await session.commit()

                logger.info(f"Updated run {task_id} status to {status}")
                return True

        except Exception as e:
            logger.error(f"Failed to update run status: {e}")
            try:
                await session.rollback()
            except:
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
        return await self.write_agent_output(
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

        return await self.write_agent_output(
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
