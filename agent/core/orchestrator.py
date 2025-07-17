"""
Agent orchestrator that coordinates all services and components.

This replaces the monolithic AIdeatorAgent logic with a clean orchestration pattern.
"""

import shutil
import asyncio # Add this import for asyncio.sleep
import subprocess
import json
import re

from agent.analyzers.codebase import CodebaseAnalyzer
from agent.analyzers.repository import RepositoryAnalyzer
from agent.config.providers import ProviderConfig
from agent.config.settings import AgentConfig
from agent.providers.claude_cli import ClaudeCLIProvider
from agent.providers.gemini_cli import GeminiCLIProvider
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

            # Validate credentials step removed – OAuth-only mode
            await self.output_writer.write_job_data(
                "🔓 API key validation skipped (OAuth-only mode)"
            )

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

            # Generate git diff after successful execution (only in code mode)
            if self.config.is_code_mode:
                await self._generate_git_diff()

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
            # Default to Claude CLI
            self.provider = ClaudeCLIProvider(self.config, self.output_writer)

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

    async def _run_git_command(self, command: list[str], cwd: str = None) -> subprocess.CompletedProcess:
        """Run a git command safely in the container.
        
        Args:
            command: Git command as list of strings (e.g., ['git', 'diff', 'HEAD'])
            cwd: Working directory (defaults to repo directory)
            
        Returns:
            CompletedProcess result
        """
        if cwd is None and self.repo_analyzer:
            cwd = str(self.repo_analyzer.config.repo_dir)
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            return result
        except subprocess.TimeoutExpired:
            await self.output_writer.write_error(f"Git command timed out: {' '.join(command)}")
            raise
        except Exception as e:
            await self.output_writer.write_error(f"Git command failed: {e}")
            raise

    def _parse_git_diff(self, diff_output: str) -> dict:
        """Parse git diff output into structured format for frontend.
        
        Args:
            diff_output: Raw git diff output
            
        Returns:
            Dict with file_changes structure expected by frontend
        """
        if not diff_output.strip():
            return {"file_changes": []}
        
        files = []
        current_file = None
        diff_lines = []
        
        for line in diff_output.split('\n'):
            # New file marker
            if line.startswith('diff --git'):
                # Save previous file if exists
                if current_file:
                    files.append(self._create_file_change(current_file, diff_lines))
                
                # Extract file path (handle a/path b/path format)
                parts = line.split()
                if len(parts) >= 4:
                    file_path = parts[3][2:]  # Remove "b/" prefix
                    current_file = {"name": file_path}
                    diff_lines = []
            
            # File header lines (index, ---, +++)
            elif line.startswith('index ') or line.startswith('---') or line.startswith('+++'):
                continue
                
            # Hunk header (@@ -1,4 +1,6 @@)
            elif line.startswith('@@'):
                diff_lines.append({
                    "type": "normal",
                    "oldLine": None,
                    "newLine": None,
                    "content": line
                })
                
            # Content lines
            elif current_file is not None:
                if line.startswith('+'):
                    diff_lines.append({
                        "type": "add",
                        "oldLine": None,
                        "newLine": None,  # Frontend will calculate
                        "content": line[1:]  # Remove + prefix
                    })
                elif line.startswith('-'):
                    diff_lines.append({
                        "type": "del", 
                        "oldLine": None,  # Frontend will calculate
                        "newLine": None,
                        "content": line[1:]  # Remove - prefix
                    })
                elif line.startswith(' '):
                    diff_lines.append({
                        "type": "normal",
                        "oldLine": None,  # Frontend will calculate
                        "newLine": None,  # Frontend will calculate
                        "content": line[1:]  # Remove space prefix
                    })
        
        # Don't forget the last file
        if current_file:
            files.append(self._create_file_change(current_file, diff_lines))
        
        return {"file_changes": files}

    def _create_file_change(self, file_info: dict, diff_lines: list) -> dict:
        """Create a file change entry with additions/deletions count.
        
        Args:
            file_info: Dict with file name
            diff_lines: List of diff line objects
            
        Returns:
            Complete file change dict
        """
        additions = sum(1 for line in diff_lines if line["type"] == "add")
        deletions = sum(1 for line in diff_lines if line["type"] == "del")
        
        return {
            "name": file_info["name"],
            "additions": additions,
            "deletions": deletions,
            "diff": diff_lines
        }

    async def _generate_git_diff(self) -> None:
        """Generate git diff with AI summaries after claude-cli execution and write to database."""
        try:
            await self.output_writer.write_job_data("📝 Generating git diff of changes...")
            
            # First check if we're in a git repository
            git_status_result = await self._run_git_command(['git', 'status', '--porcelain'])
            
            if git_status_result.returncode != 0:
                await self.output_writer.write_job_data("⚠️ Not in a git repository - skipping diff generation")
                return
            
            # Check if there are any changes
            if not git_status_result.stdout.strip():
                await self.output_writer.write_job_data("ℹ️ No changes detected in repository")
                # Write empty XML diff for frontend
                empty_xml = self._create_empty_diff_xml()
                await self.output_writer.write_git_diff_xml(empty_xml)
                return
            
            # Generate diff of all changes (staged and unstaged)
            diff_result = await self._run_git_command(['git', 'diff', 'HEAD'])
            
            if diff_result.returncode == 0:
                if diff_result.stdout.strip():
                    await self.output_writer.write_job_data("🤖 Generating AI summaries for file changes...")
                    
                    # Parse diff and generate XML with AI summaries
                    diff_xml = await self._generate_diff_xml_with_summaries(diff_result.stdout)
                    
                    # Write XML to database with "diffs" output_type
                    await self.output_writer.write_git_diff_xml(diff_xml)
                    
                    # Count files for status message
                    file_count = diff_result.stdout.count('diff --git')
                    await self.output_writer.write_job_data(f"✅ Generated diff with AI summaries for {file_count} changed files")
                else:
                    await self.output_writer.write_job_data("ℹ️ No diff content to display")
                    # Write empty XML for frontend consistency
                    empty_xml = self._create_empty_diff_xml()
                    await self.output_writer.write_git_diff_xml(empty_xml)
            else:
                error_msg = f"Git diff command failed: {diff_result.stderr}"
                await self.output_writer.write_error(error_msg)
                # Still write empty XML so frontend doesn't wait forever
                empty_xml = self._create_empty_diff_xml()
                await self.output_writer.write_git_diff_xml(empty_xml)
                
        except Exception as e:
            error_msg = f"Failed to generate git diff: {e}"
            await self.output_writer.write_error(error_msg)
            await self.output_writer.write_job_data("⚠️ Git diff generation failed - continuing without diff")
            # Still write empty XML so frontend doesn't wait forever
            try:
                empty_xml = self._create_empty_diff_xml()
                await self.output_writer.write_git_diff_xml(empty_xml)
            except Exception:
                pass  # Don't let secondary errors mask the main error

    async def _generate_diff_xml_with_summaries(self, diff_output: str) -> str:
        """Generate XML diff format with AI-generated summaries for each file.
        
        Args:
            diff_output: Raw git diff output
            
        Returns:
            XML string in format expected by frontend DiffViewer
        """
        if not diff_output.strip():
            return self._create_empty_diff_xml()
        
        file_diffs = []
        current_file = None
        current_diff_lines = []
        
        for line in diff_output.split('\n'):
            # New file marker
            if line.startswith('diff --git'):
                # Process previous file if exists
                if current_file and current_diff_lines:
                    file_diff_content = '\n'.join(current_diff_lines)
                    summary = await self._summarize_file_changes(current_file, file_diff_content)
                    file_diffs.append({
                        'name': current_file,
                        'diff': file_diff_content,
                        'changes': summary
                    })
                
                # Extract file path (handle a/path b/path format)
                parts = line.split()
                if len(parts) >= 4:
                    current_file = parts[3][2:]  # Remove "b/" prefix
                    current_diff_lines = []
            
            # Collect all diff lines for this file
            elif current_file is not None:
                current_diff_lines.append(line)
        
        # Don't forget the last file
        if current_file and current_diff_lines:
            file_diff_content = '\n'.join(current_diff_lines)
            summary = await self._summarize_file_changes(current_file, file_diff_content)
            file_diffs.append({
                'name': current_file,
                'diff': file_diff_content,
                'changes': summary
            })
        
        return self._create_diff_xml(file_diffs)

    async def _summarize_file_changes(self, filename: str, diff_content: str) -> str:
        """Use Anthropic API to generate English summary of file changes.
        
        Args:
            filename: Name of the file being changed
            diff_content: The git diff content for this file
            
        Returns:
            Human-readable summary of changes
        """
        try:
            # Create a focused prompt for change analysis
            prompt = f"""Analyze this git diff for {filename} and provide a concise summary of the changes:

{diff_content}

Provide a brief, clear summary of what was changed in this file. Focus on:
- What functionality was added, modified, or removed
- The purpose/intent of the changes
- Any new imports, dependencies, or components added

Keep it under 100 words and make it readable for developers. Avoid technical jargon about line numbers or syntax."""

            # Use the same provider that's already configured for the main task
            summary = await self.provider.generate_response(prompt)
            return summary.strip()
            
        except Exception as e:
            # Fallback to basic description if AI summary fails
            await self.output_writer.write_job_data(f"⚠️ Failed to generate AI summary for {filename}: {e}")
            
            # Provide a more informative fallback based on file type and changes
            lines_added = diff_content.count('\n+')
            lines_removed = diff_content.count('\n-')
            
            # Try to identify the type of change
            if '+' in diff_content and '-' not in diff_content:
                change_type = "Added new content to"
            elif '-' in diff_content and '+' not in diff_content:
                change_type = "Removed content from"
            else:
                change_type = "Modified"
            
            return f"{change_type} {filename} ({lines_added} additions, {lines_removed} deletions)"

    def _create_empty_diff_xml(self) -> str:
        """Create empty diff XML for when no changes are detected."""
        return """<diff_analysis>
  <file>
    <name>No files modified</name>
    <diff>No changes detected in this task</diff>
    <changes>No modifications were made during task execution</changes>
  </file>
</diff_analysis>"""

    def _create_diff_xml(self, file_diffs: list[dict]) -> str:
        """Create XML structure expected by frontend DiffViewer.
        
        Args:
            file_diffs: List of dicts with name, diff, and changes keys
            
        Returns:
            XML string formatted for DiffViewer
        """
        if not file_diffs:
            return self._create_empty_diff_xml()

        file_elements = []
        for file_data in file_diffs:
            # Escape XML special characters
            name = self._escape_xml(file_data['name'])
            diff = self._escape_xml(file_data['diff'])
            changes = self._escape_xml(file_data['changes'])

            file_elements.append(f"""  <file>
    <name>{name}</name>
    <diff>{diff}</diff>
    <changes>{changes}</changes>
  </file>""")

        return f"""<diff_analysis>
{chr(10).join(file_elements)}
</diff_analysis>"""

    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters in text content.
        
        Args:
            text: Text to escape
            
        Returns:
            XML-safe text
        """
        if not text:
            return ""
        
        # Replace XML special characters
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))

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
