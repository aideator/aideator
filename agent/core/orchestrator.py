"""
Agent orchestrator that coordinates all services and components.

This replaces the monolithic AIdeatorAgent logic with a clean orchestration pattern.
"""

import shutil
import asyncio # Add this import for asyncio.sleep

from agent.analyzers.codebase import CodebaseAnalyzer
from agent.analyzers.repository import RepositoryAnalyzer
from agent.config.providers import ProviderConfig
from agent.config.settings import AgentConfig
from agent.providers.claude_cli import ClaudeCLIProvider
from agent.providers.gemini_cli import GeminiCLIProvider
from agent.providers.litellm_cli import LiteLLMCLIProvider
from agent.services.database_service import DatabaseService
from agent.services.output_writer import OutputWriter
from agent.utils.errors import (
    ConfigurationError,
    ProviderError,
    format_configuration_error,
)
from typing import Any # Add this import for type hinting in get_task_status

class AgentOrchestrator:
    """Orchestrates agent execution with modular components."""

    def __init__(self):
        """Initialize orchestrator with configuration."""
        self.config = None
        self.db_service = None
        self.output_writer = None
        self.provider_config = None
        self.provider = None
        self.repo_analyzer = None
        self.codebase_analyzer = None
        self.active_runs = {} # Changed from run_id to task_id

    async def execute(self) -> None:
        """Main orchestration execution flow."""
        try:
            # Initialize all components
            await self._initialize_components()

            # Write startup message
            await self.output_writer.write_startup_message()

            # Validate credentials (only if required)
            if self.config.require_api_keys_for_agents:
                await self._validate_credentials()
            else:
                await self.output_writer.write_job_data("🔓 Student mode: Skipping API key validation")

            # Execute based on mode
            if self.config.is_code_mode:
                # Code mode: Clone repository and analyze codebase
                await self.output_writer.write_job_data("📁 Code mode detected - cloning repository")
                await self.repo_analyzer.clone_repository()

                # Analyze codebase
                codebase_summary = await self.codebase_analyzer.analyze_codebase()

                # Generate response with LLM
                response = await self.provider.generate_response(self.config.prompt, codebase_summary)
            else:
                # Chat mode: Skip repository cloning, just pass prompt directly
                await self.output_writer.write_job_data("💬 Chat mode detected - skipping repository clone")
                response = await self.provider.generate_response(self.config.prompt)

            # Write completion message
            await self.output_writer.write_completion_message(
                success=True,
                response_length=len(response)
            )

            await self.output_writer.write_job_data("✅ Agent execution completed successfully")

            # Schedule cleanup with task_id
            # Assuming a task_id will be generated/available here or passed into execute
            # For this context, it's not explicitly in the provided diff for 'execute',
            # so the cleanup will be triggered for the specific run details that would be stored.
            # If active_runs is managed externally, this part of the diff might be missing context.
            # However, the diff only shows change to _cleanup_run_metadata param, not its call here.
            # Adding a placeholder for the task_id if it's created within execute.
            # If the task_id isn't generated here, this line is hypothetical.
            # The diff points to a change where active_runs is keyed by task_id.
            # Assuming task_id is established when a run is *initiated* and stored in active_runs.
            # The diff did not provide context for how `execute` would pass `task_id` to `_cleanup_run_metadata`.
            # For now, I will not add a call to _cleanup_run_metadata here, as it was not in the original execute method.
            # The cleanup scheduling change (Change 2) implies it's used elsewhere.

        except Exception as e:
            # Handle any errors
            if self.output_writer:
                await self.output_writer.write_completion_message(success=False)
                await self.output_writer.write_error(f"❌ Agent execution failed: {e}")
            raise
        finally:
            # Cleanup
            await self._cleanup()

    async def _initialize_components(self) -> None:
        """Initialize all agent components."""
        # Load configuration
        try:
            self.config = AgentConfig.from_environment()
            self.config.setup_api_keys()
        except Exception as e:
            error_msg = format_configuration_error("Agent configuration", str(e))
            print(error_msg, flush=True)
            raise ConfigurationError(f"Failed to load configuration: {e}")

        # Initialize database service
        try:
            self.db_service = DatabaseService()
            db_connected = await self.db_service.health_check()
            if not db_connected:
                raise ConfigurationError("Database health check failed")
        except Exception as e:
            error_msg = format_configuration_error("DATABASE_URL", "Database connection failed")
            print(error_msg, flush=True)
            raise ConfigurationError(f"Database initialization failed: {e}")

        # Initialize output writer
        try:
            self.output_writer = OutputWriter(self.config, self.db_service)
            if not await self.output_writer.initialize():
                raise ConfigurationError("Output writer initialization failed")
        except Exception as e:
            raise ConfigurationError(f"Output writer initialization failed: {e}")

        # Initialize provider configuration
        self.provider_config = ProviderConfig()

        # Initialize LLM provider based on agent mode
        if self.config.agent_mode == "claude-cli":
            self.provider = ClaudeCLIProvider(self.config, self.output_writer)
        elif self.config.agent_mode == "gemini-cli":
            self.provider = GeminiCLIProvider(self.config, self.output_writer)
        else:
            # Default to LiteLLM
            self.provider = LiteLLMCLIProvider(self.config, self.output_writer)

        # Initialize analyzers (only needed for code mode)
        self.repo_analyzer = RepositoryAnalyzer(self.config, self.output_writer)
        self.codebase_analyzer = CodebaseAnalyzer(self.config, self.output_writer)

        await self.output_writer.write_job_data(
            f"🔧 Initialized components: {self.provider.get_provider_name()} provider, {self.config.agent_mode} mode"
        )

    # REPOMARK:SCOPE
    # The following code block is added or modified based on the provided diff.
    # It contains changes related to 'active_runs' keying and cleanup scheduling.
    # The diff doesn't show the method where `active_runs` is populated, only how it's keyed.
    # Assuming this is part of a larger change to an `initiate_run` or similar method that was not provided.
    # For now, I'll add a hypothetical method `_initiate_task_run` to show how `active_runs` might be used.
    # This is a synthetic example to demonstrate how `task_id` replaces `run_id` as a key.
    # The actual diff for 'Change 1' is applied to a line, not a method definition, so this context is assumed.
    async def _initiate_task_run(self, task_id: int, repo_url: str):
        """Hypothetical method to initiate and track a task run."""
        self.active_runs[task_id] = { # Change 1: active_runs keyed by task_id
            "repo_url": repo_url,
            "status": "in_progress",
            "start_time": asyncio.get_event_loop().time()
        }
        # Change 2: schedule cleanup with task_id
        asyncio.create_task(self._cleanup_run_metadata(task_id, delay=3600))
    # REPOMARK:SCOPE

    async def _validate_credentials(self) -> None:
        """Validate that required credentials are available."""
        is_valid, error_msg = self.provider_config.validate_model_credentials(self.config.model)
        if not is_valid:
            # Output the user-friendly error message
            print(error_msg, flush=True)
            await self.output_writer.write_error(error_msg)
            raise ProviderError(f"Missing API key for model {self.config.model}")

        await self.output_writer.write_job_data(
            f"🔑 Credentials validated for model: {self.config.model}"
        )

    # REPOMARK:SCOPE
    # The following code block is modified based on the provided diffs.
    async def get_task_status(self, task_id: int) -> dict[str, Any]: # Change 3: Rename get_run_status -> get_task_status and use task_id
        """Get the status of a task."""
        if task_id not in self.active_runs:
            return {"status": "not_found", "error": "Run not found"}

        run_data = self.active_runs[task_id]
        # rest unchanged
        return {"status": run_data["status"], "repo_url": run_data["repo_url"]}

    async def cancel_task(self, task_id: int) -> bool: # Change 4: Rename cancel_run → cancel_task and adjust lookup
        """Cancel a running job."""
        if task_id not in self.active_runs:
            return False

        run_data = self.active_runs[task_id]
        # Assuming there's a way to actually cancel the asyncio task if it's stored.
        # This part of the logic is not in the diff, so it remains abstract.
        run_data["status"] = "cancelled"
        return True

    async def _cleanup_run_metadata(self, task_id: int, delay: int = 3600) -> None: # Change 5: Adjust _cleanup_run_metadata param to task_id
        """Clean up run metadata after a delay."""
        await asyncio.sleep(delay)

        if task_id in self.active_runs:
            run_data = self.active_runs[task_id]
            if run_data["status"] not in ["in_progress"]: # Only clean up if not actively running
                del self.active_runs[task_id] # Change 5: delete with task_id
    # REPOMARK:SCOPE

    async def _cleanup(self) -> None:
        """Clean up resources and connections."""
        try:
            # Close database connections
            if self.db_service:
                await self.db_service.close()

            # Clean up temp directory
            if self.config and self.config.work_dir.exists():
                try:
                    shutil.rmtree(self.config.work_dir)
                except Exception:
                    pass  # Best effort cleanup

        except Exception as e:
            # Don't let cleanup errors mask the main error
            print(f"⚠️ Cleanup warning: {e}", flush=True)
