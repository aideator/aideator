"""
Repository analyzer for cloning and basic repository operations.

Handles Git cloning and repository setup.
"""

import shutil
from pathlib import Path

import git

from agent.utils.errors import RepositoryError, format_repository_error


class RepositoryAnalyzer:
    """Handles repository cloning and basic operations."""

    def __init__(self, config, output_writer):
        """Initialize repository analyzer.
        
        Args:
            config: AgentConfig instance
            output_writer: OutputWriter instance
        """
        self.config = config
        self.output_writer = output_writer

    async def clone_repository(self) -> None:
        """Clone the repository to analyze.
        
        Raises:
            RepositoryError: If cloning fails
        """
        await self.output_writer.write_job_data(f"📁 Cloning repository: {self.config.repo_url}")

        try:
            if self.config.repo_dir.exists():
                shutil.rmtree(self.config.repo_dir)

            # Clone with minimal depth
            git.Repo.clone_from(
                self.config.repo_url,
                self.config.repo_dir,
                depth=1,
                single_branch=True
            )

            # Calculate repository size
            repo_size = self._get_directory_size(self.config.repo_dir)

            await self.output_writer.write_job_data(
                f"✅ Repository cloned successfully. Size: {repo_size} MB"
            )

        except Exception as e:
            error_message = format_repository_error(e, self.config.repo_url)
            await self.output_writer.write_error(error_message)
            raise RepositoryError(f"Repository clone failed: {e}") from e

    def _get_directory_size(self, path: Path) -> float:
        """Get directory size in MB.
        
        Args:
            path: Directory path to measure
            
        Returns:
            Size in MB rounded to 2 decimal places
        """
        total_size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        return round(total_size / (1024 * 1024), 2)

    def get_repository_info(self) -> dict:
        """Get basic repository information.
        
        Returns:
            Dictionary with repository metadata
        """
        if not self.config.repo_dir.exists():
            return {"error": "Repository not cloned"}

        return {
            "url": self.config.repo_url,
            "local_path": str(self.config.repo_dir),
            "size_mb": self._get_directory_size(self.config.repo_dir),
            "exists": True
        }
