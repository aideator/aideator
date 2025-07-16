#!/usr/bin/env python
"""
AIdeator Agent - Refactored modular version.

Slim orchestrator that maintains external interface compatibility.
"""

import asyncio
import logging
import os
import sys
from datetime import UTC, datetime

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
        # Use TASK_ID as the primary identifier
        self.task_id = os.getenv("TASK_ID")
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
        self.logger = logging.getLogger(
            f"agent_task-{self.task_id or 'local'}_{self.variation_id}"
        )

    async def run(self) -> None:
        """Main agent execution - delegates to orchestrator."""
        self.log("🚀 Starting AIdeator Agent (modular version)", "INFO")

        try:
            # Delegate all the real work to the orchestrator
            await self._orchestrator.execute()

            # Sleep for 600 seconds (10 minutes) before exit on success
            self.log("⏱️ Sleeping for 600 seconds before exit", "INFO")

        except Exception as e:
            self.log(f"💥 Fatal error: {e!s}", "ERROR")
            raise

    def log(self, message: str, level: str = "INFO", **kwargs):
        """
        Structured logging - maintains interface compatibility.
        """
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "task_id": self.task_id,
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
                variation_id = int(os.getenv("VARIATION_ID", "0"))
                task_id_env = os.getenv("TASK_ID")

                if task_id_env:
                    # Use task_id directly from environment (unified tasks)
                    task_id = int(task_id_env)
                    await db_service.write_log(
                        task_id=task_id,
                        variation_id=variation_id,
                        log_message=f"Agent starting up for task_id={task_id}, variation_id={variation_id}",
                        log_level="INFO"
                    )
                    print(f"✅ Wrote startup message to database for task_id={task_id}")
                else:
                    print(f"❌ TASK_ID environment variable not set - cannot continue")

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
                task_id_env = os.getenv("TASK_ID")
                
                if task_id_env:
                    # Use task_id directly (unified tasks)
                    task_id = int(task_id_env)
                    variation_id = int(os.getenv("VARIATION_ID", "0"))
                    await db_service.write_error(task_id, variation_id, error_msg)
                else:
                    print("❌ Cannot write error - TASK_ID not set")
                await db_service.close()
        except:
            pass  # Best effort

        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
# Test change
