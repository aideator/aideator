"""
Agent orchestrator that coordinates all services and components.

This replaces the monolithic AIdeatorAgent logic with a clean orchestration pattern.
"""

import shutil

from agent.analyzers.codebase import CodebaseAnalyzer
from agent.analyzers.repository import RepositoryAnalyzer
from agent.config.providers import ProviderConfig
from agent.config.settings import AgentConfig
# Providers imported conditionally to avoid dependency issues
from agent.services.database_service import DatabaseService
from agent.services.output_writer import OutputWriter
from agent.utils.errors import (
    ConfigurationError,
    ProviderError,
    format_configuration_error,
)


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

        # Initialize LLM provider based on agent mode (dynamic imports)
        if self.config.agent_mode == "claude-cli":
            from agent.providers.claude_cli import ClaudeCLIProvider
            self.provider = ClaudeCLIProvider(self.config, self.output_writer)
        elif self.config.agent_mode == "gemini-cli":
            from agent.providers.gemini_cli import GeminiCLIProvider
            self.provider = GeminiCLIProvider(self.config, self.output_writer)
        else:
            # Default to Claude CLI
            from agent.providers.claude_cli import ClaudeCLIProvider
            self.provider = ClaudeCLIProvider(self.config, self.output_writer)

        # Initialize analyzers (only needed for code mode)
        self.repo_analyzer = RepositoryAnalyzer(self.config, self.output_writer)
        self.codebase_analyzer = CodebaseAnalyzer(self.config, self.output_writer)

        await self.output_writer.write_job_data(
            f"🔧 Initialized components: {self.provider.get_provider_name()} provider, {self.config.agent_mode} mode"
        )

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
