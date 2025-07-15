#!/usr/bin/env python
"""
AIdeator Agent - Refactored modular version.

Slim orchestrator that maintains external interface compatibility.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, UTC

# Import the orchestrator that contains the main logic
from agent.core.orchestrator import AgentOrchestrator

# Import the database service for early testing
try:
    from agent.services.database_service import DatabaseService
    DATABASE_SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"Failed to import DatabaseService: {e}")
    DATABASE_SERVICE_AVAILABLE = False
    DatabaseService = None


class AIdeatorAgent:
    """
    AIdeator Agent - maintains external interface compatibility.
    
    This class preserves the exact interface that Kubernetes and tests expect,
    while delegating all actual work to the modular orchestrator.
    """
    
    def __init__(self):
        """Initialize agent - maintains original interface."""
        self.run_id = os.getenv("RUN_ID", "local-test")
        self.variation_id = os.getenv("VARIATION_ID", "0")
        
        # Initialize the orchestrator that does the real work
        self._orchestrator = AgentOrchestrator()
        
        # Set up basic logging for interface compatibility
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up basic logging for interface compatibility."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(f"agent_{self.run_id}_{self.variation_id}")
    
    async def run(self) -> None:
        """Main agent execution - delegates to orchestrator."""
        self.log("🚀 Starting AIdeator Agent (modular version)", "INFO")
        
        try:
            # Delegate all the real work to the orchestrator
            await self._orchestrator.execute()
            
            # Sleep for 600 seconds (10 minutes) before exit on success
            self.log("⏱️ Sleeping for 600 seconds before exit", "INFO")
            await asyncio.sleep(600)
            
        except Exception as e:
            self.log(f"💥 Fatal error: {e!s}", "ERROR")
            raise
    
    def log(self, message: str, level: str = "INFO", **kwargs):
        """
        Structured logging - maintains interface compatibility.
        """
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "run_id": self.run_id,
            "variation_id": self.variation_id,
            "level": level,
            "message": message,
            **kwargs,
        }
        
        # Print to stdout for debugging (maintains original behavior)
        if os.getenv("DEBUG") == "true":
            import json
            print(json.dumps(log_entry), flush=True)
        
        # Log with standard logger
        self.logger.log(
            getattr(logging, level, logging.INFO),
            f"{message} | {kwargs if kwargs else ''}",
        )


async def main():
    """Main entry point - maintains exact signature."""
    
    # Test database connection early (maintains original behavior)
    if DATABASE_SERVICE_AVAILABLE:
        try:
            db_service = DatabaseService()
            if await db_service.health_check():
                print("✅ Database connection successful")
                
                # Try to write a startup message if we have environment variables
                run_id = os.getenv("RUN_ID", "unknown")
                variation_id = int(os.getenv("VARIATION_ID", "0"))
                
                # Get task_id from run_id
                run = await db_service.get_run_by_run_id(run_id)
                if run:
                    task_id = run.task_id
                    await db_service.write_log(
                        task_id=task_id,
                        variation_id=variation_id,
                        log_message=f"Agent starting up for run_id={run_id}, task_id={task_id} (MODULAR VERSION)",
                        log_level="INFO"
                    )
                    print(f"✅ Wrote startup message to database for task_id={task_id}")
                else:
                    print(f"⚠️ Could not find run with run_id={run_id}")
                    
            else:
                print("❌ Database health check failed")
            await db_service.close()
        except Exception as e:
            print(f"❌ Database test failed: {e}")
            # Write to stdout so orchestrator can see
            print(f"DATABASE_ERROR: {e}")
    else:
        print("❌ DatabaseService not available due to import error")
    
    # Create and run the agent (maintains original interface)
    agent = AIdeatorAgent()
    try:
        # Run the agent
        await agent.run()
        
        # Clean exit
        sys.exit(0)
    except Exception as e:
        # Ensure error is visible in logs and database
        error_msg = f"💥 Fatal error: {e!s}"
        print(error_msg, flush=True)  # Ensure it's in container logs
        agent.log(error_msg, "ERROR")
        agent.log("❌ Agent failed", "INFO", status="failed")
        agent.log("🏁 Exiting agent container", "INFO")
        
        # Try to write to database if we have a task_id
        try:
            if DATABASE_SERVICE_AVAILABLE:
                db_service = DatabaseService()
                run_id = os.getenv("RUN_ID", "unknown")
                run = await db_service.get_run_by_run_id(run_id)
                if run:
                    await db_service.write_error(run.task_id, 0, error_msg)
                await db_service.close()
        except:
            pass  # Best effort
            
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
