"""Repository service for Git operations."""

import shutil
from pathlib import Path
import git


class RepositoryService:
    """Handles Git repository operations."""
    
    def __init__(self, work_dir: str):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(exist_ok=True)
        self.repo_dir = self.work_dir / "repo"
        
    async def clone(self, repo_url: str) -> Path:
        """Clone repository to work directory."""
        # Clean up existing repo if present
        if self.repo_dir.exists():
            shutil.rmtree(self.repo_dir)
        
        # Clone with minimal depth
        git.Repo.clone_from(
            repo_url,
            self.repo_dir,
            depth=1,
            single_branch=True
        )
        
        return self.repo_dir
    
    def get_size_mb(self) -> float:
        """Get repository size in MB."""
        if not self.repo_dir.exists():
            return 0.0
            
        total_size = sum(f.stat().st_size for f in self.repo_dir.rglob('*') if f.is_file())
        return round(total_size / (1024 * 1024), 2)
    
    def cleanup(self) -> None:
        """Clean up cloned repository."""
        if self.repo_dir.exists():
            shutil.rmtree(self.repo_dir)