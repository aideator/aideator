"""
Standardized output writing service.

Handles all database writes with consistent output types.
"""

from typing import Optional
from datetime import datetime

from agent.services.database_service import DatabaseService


class OutputWriter:
    """Standardized output writer for all agent outputs."""
    
    def __init__(self, config, db_service: DatabaseService):
        """Initialize output writer.
        
        Args:
            config: AgentConfig instance
            db_service: DatabaseService instance
        """
        self.config = config
        self.db_service = db_service
        self.task_id = None
        self.variation_id = int(config.variation_id)
    
    async def initialize(self) -> bool:
        """Initialize the output writer by getting task_id from run_id.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            run = await self.db_service.get_run_by_run_id(self.config.run_id)
            if run:
                self.task_id = run.task_id
                return True
            else:
                print(f"⚠️ Could not find run with run_id={self.config.run_id}")
                return False
        except Exception as e:
            print(f"❌ Failed to initialize OutputWriter: {e}")
            return False
    
    async def write_output(
        self, 
        content: str, 
        output_type: str = "job_data",
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Write output to database.
        
        Args:
            content: Output content
            output_type: Type of output (job_data, diff, summary, error)
            timestamp: Optional timestamp (defaults to current time)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.task_id:
            print("❌ OutputWriter not initialized - no task_id")
            return False
            
        try:
            success = await self.db_service.write_agent_output(
                task_id=self.task_id,
                variation_id=self.variation_id,
                content=content,
                output_type=output_type,
                timestamp=timestamp
            )
            
            if success:
                print(f"✅ Wrote {output_type} output ({len(content)} chars)")
            else:
                print(f"❌ Failed to write {output_type} output")
                
            return success
            
        except Exception as e:
            print(f"❌ Error writing {output_type} output: {e}")
            return False
    
    async def write_job_data(self, content: str) -> bool:
        """Write main job data output (what shows in Logs tab).
        
        Args:
            content: Job output content
            
        Returns:
            True if successful
        """
        return await self.write_output(content, "job_data")
    
    async def write_error(self, error_message: str) -> bool:
        """Write error output (what shows in Errors tab).
        
        Args:
            error_message: Error message
            
        Returns:
            True if successful
        """
        return await self.write_output(error_message, "error")
    
    async def write_diff(self, diff_content: str) -> bool:
        """Write diff output (what shows in Diffs tab).
        
        Args:
            diff_content: Diff content
            
        Returns:
            True if successful
        """
        return await self.write_output(diff_content, "diff")
    
    async def write_summary(self, summary_content: str) -> bool:
        """Write summary output (what shows in Summary tab).
        
        Args:
            summary_content: Summary content
            
        Returns:
            True if successful
        """
        return await self.write_output(summary_content, "summary")
    
    async def write_startup_message(self) -> bool:
        """Write agent startup message."""
        message = f"🚀 Agent {self.variation_id} starting for run {self.config.run_id}"
        return await self.write_job_data(message)
    
    async def write_completion_message(self, success: bool, response_length: int = 0) -> bool:
        """Write agent completion message.
        
        Args:
            success: Whether the agent completed successfully
            response_length: Length of generated response
            
        Returns:
            True if successful
        """
        if success:
            message = f"✅ Agent {self.variation_id} completed successfully. Generated {response_length} characters."
        else:
            message = f"❌ Agent {self.variation_id} failed to complete."
            
        return await self.write_job_data(message)