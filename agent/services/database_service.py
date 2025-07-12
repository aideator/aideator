"""Database service for agent output persistence."""

import asyncio
import os
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel

import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for writing agent outputs to database."""
    
    def __init__(self, run_id: str, variation_id: int):
        """Initialize database service."""
        self.run_id = run_id
        self.variation_id = variation_id
        self.engine = None
        self.session_maker = None
        self._connected = False
        
    def _sync_connect(self) -> bool:
        """Synchronous database connection (called from async context)."""
        try:
            database_url = os.environ.get("DATABASE_URL")
            if not database_url:
                logger.warning("DATABASE_URL not set, database writes disabled")
                return False
                
            # Create synchronous engine for agent use
            self.engine = create_engine(database_url)
            self.session_maker = sessionmaker(self.engine, class_=Session, expire_on_commit=False)
            
            # Test connection
            with self.session_maker() as session:
                session.exec(text("SELECT 1"))
                
            self._connected = True
            logger.info(f"Connected to database for run {self.run_id}, variation {self.variation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    async def connect(self) -> bool:
        """Connect to database (async wrapper)."""
        return await asyncio.to_thread(self._sync_connect)
            
    def _sync_write_output(
        self, 
        content: str, 
        output_type: str = "stdout",
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Synchronous database write (called from async context)."""
        if not self._connected:
            return False
            
        try:
            # Import here to avoid circular imports
            from app.models.run import AgentOutput
            
            with self.session_maker() as session:
                output = AgentOutput(
                    run_id=self.run_id,
                    variation_id=self.variation_id,
                    content=content,
                    output_type=output_type,
                    timestamp=timestamp or datetime.utcnow()
                )
                session.add(output)
                session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to write to database: {e}")
            return False
    
    async def write_output(
        self, 
        content: str, 
        output_type: str = "stdout",
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Write output to database (async wrapper)."""
        return await asyncio.to_thread(self._sync_write_output, content, output_type, timestamp)
            
    async def publish_output(self, content: str) -> bool:
        """Write standard output to database."""
        return await self.write_output(content, output_type="stdout")
        
    async def publish_status(self, status: str, metadata: Optional[dict] = None) -> bool:
        """Write status update to database."""
        import json
        status_content = {
            "status": status,
            "variation_id": self.variation_id,
            "metadata": metadata or {}
        }
        return await self.write_output(
            json.dumps(status_content), 
            output_type="status"
        )
        
    async def publish_log(self, message: str, level: str = "INFO", **kwargs) -> bool:
        """Write log entry to database."""
        import json
        log_content = {
            "level": level,
            "message": message,
            "variation_id": self.variation_id,
            **kwargs
        }
        return await self.write_output(
            json.dumps(log_content),
            output_type="logging"
        )
    
    async def publish_job_summary(self, summary: str, success: bool = True, **metadata) -> bool:
        """Write job completion summary to database."""
        import json
        summary_content = {
            "summary": summary,
            "success": success,
            "variation_id": self.variation_id,
            "metadata": metadata
        }
        return await self.write_output(
            json.dumps(summary_content),
            output_type="job_summary"
        )
    
    async def publish_metrics(self, additions: int = 0, deletions: int = 0, files_changed: int = 0, **other_metrics) -> bool:
        """Write code change metrics to database."""
        import json
        metrics_content = {
            "additions": additions,
            "deletions": deletions, 
            "files_changed": files_changed,
            "variation_id": self.variation_id,
            **other_metrics
        }
        return await self.write_output(
            json.dumps(metrics_content),
            output_type="metrics"
        )
    
    async def publish_diffs(self, file_changes: list, **metadata) -> bool:
        """Write file diff information to database."""
        import json
        diffs_content = {
            "file_changes": file_changes,
            "variation_id": self.variation_id,
            "metadata": metadata
        }
        return await self.write_output(
            json.dumps(diffs_content),
            output_type="diffs"
        )
        
    def _sync_disconnect(self) -> None:
        """Synchronous database disconnect (called from async context)."""
        if self.engine:
            self.engine.dispose()
        self._connected = False
    
    async def disconnect(self) -> None:
        """Disconnect from database (async wrapper)."""
        await asyncio.to_thread(self._sync_disconnect)