"""
Codebase analyzer for analyzing repository structure and content.

Handles file discovery, content analysis, and summary generation.
"""

import glob
import os
from pathlib import Path

import aiofiles

from agent.utils.errors import RepositoryError


class CodebaseAnalyzer:
    """Analyzes codebase structure and content."""

    def __init__(self, config, output_writer):
        """Initialize codebase analyzer.
        
        Args:
            config: AgentConfig instance
            output_writer: OutputWriter instance
        """
        self.config = config
        self.output_writer = output_writer

        # Analysis constants
        self.max_key_file_size = 50000
        self.max_key_files_to_read = 10
        self.max_file_preview_chars = 2000

    async def analyze_codebase(self) -> str:
        """Analyze the codebase structure and content.
        
        Returns:
            Formatted codebase analysis summary
            
        Raises:
            RepositoryError: If analysis fails
        """
        await self.output_writer.write_job_data("🔍 Analyzing codebase structure...")

        analysis = {
            "files": [],
            "total_files": 0,
            "total_size_mb": 0,
            "languages": {},
            "key_files": [],
        }

        try:
            # Walk through repository
            for root, dirs, files in os.walk(self.config.repo_dir):
                # Skip hidden and vendor directories
                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".")
                    and d not in ["node_modules", "vendor", "__pycache__"]
                ]

                for file in files:
                    if file.startswith("."):
                        continue

                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(self.config.repo_dir)

                    # Track file extension
                    ext = file_path.suffix.lower()
                    if ext:
                        analysis["languages"][ext] = (
                            analysis["languages"].get(ext, 0) + 1
                        )

                    analysis["total_files"] += 1

                    # Add file info
                    file_info = {
                        "path": str(relative_path),
                        "size": file_path.stat().st_size,
                    }
                    analysis["files"].append(file_info)

            # Calculate total size
            analysis["total_size_mb"] = self._get_directory_size(self.config.repo_dir)

            # Identify key files
            analysis["key_files"] = self._identify_key_files()

            await self.output_writer.write_job_data(
                f"📊 Analysis complete: {analysis['total_files']} files, {analysis['total_size_mb']} MB"
            )

            # Generate summary
            summary = await self._generate_summary(analysis)

            await self.output_writer.write_job_data("✅ Codebase analysis summary generated")

            return summary

        except Exception as e:
            error_msg = f"❌ Codebase analysis failed: {e}"
            await self.output_writer.write_error(error_msg)
            raise RepositoryError(f"Failed to analyze codebase: {e}") from e

    async def _generate_summary(self, analysis: dict) -> str:
        """Generate formatted codebase summary.
        
        Args:
            analysis: Analysis results dictionary
            
        Returns:
            Formatted summary string
        """
        # Build summary parts
        summary_parts = [
            f"Repository: {self.config.repo_url}",
            f"Total files: {analysis['total_files']}",
            f"Total size: {analysis['total_size_mb']} MB",
            f"Languages: {', '.join(f'{k}({v})' for k, v in sorted(analysis['languages'].items(), key=lambda x: x[1], reverse=True)[:5])}",
            "",
            "Key files:",
        ]

        # Read contents of key files
        for key_file in analysis["key_files"][:self.max_key_files_to_read]:
            file_path = self.config.repo_dir / key_file
            if (
                file_path.exists()
                and file_path.stat().st_size < self.max_key_file_size
            ):
                try:
                    async with aiofiles.open(
                        file_path, encoding="utf-8", errors="ignore"
                    ) as f:
                        content = await f.read()
                        summary_parts.extend([
                            f"\n--- {key_file} ---",
                            content[:self.max_file_preview_chars],
                            "..." if len(content) > self.max_file_preview_chars else "",
                            "",
                        ])

                        await self.output_writer.write_job_data(f"📄 Read key file: {key_file}")

                except Exception as e:
                    await self.output_writer.write_job_data(f"⚠️ Failed to read {key_file}: {e}")

        return "\n".join(summary_parts)

    def _identify_key_files(self) -> list[str]:
        """Identify important files in the repository.
        
        Returns:
            List of relative paths to key files
        """
        key_patterns = [
            "README*",
            "readme*",
            "package.json",
            "requirements.txt",
            "setup.py",
            "Cargo.toml",
            "go.mod",
            "Dockerfile",
            "docker-compose*",
            ".github/workflows/*",
            "main.*",
            "app.*",
            "index.*",
            "config.*",
            "settings.*",
        ]

        key_files = []
        for pattern in key_patterns:
            if "*" in pattern:
                # Handle wildcards
                matches = glob.glob(str(self.config.repo_dir / pattern), recursive=True)
                for match in matches:
                    try:
                        rel_path = Path(match).relative_to(self.config.repo_dir)
                        key_files.append(str(rel_path))
                    except:
                        pass
            else:
                # Direct file check
                file_path = self.config.repo_dir / pattern
                if file_path.exists():
                    key_files.append(pattern)

        return key_files

    def _get_directory_size(self, path: Path) -> float:
        """Get directory size in MB.
        
        Args:
            path: Directory path to measure
            
        Returns:
            Size in MB rounded to 2 decimal places
        """
        total_size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        return round(total_size / (1024 * 1024), 2)
