"""Codebase analysis module."""

import os
from pathlib import Path
from typing import Dict, List, Tuple
import aiofiles


class CodebaseAnalyzer:
    """Analyzes repository structure and content."""
    
    def __init__(self, repo_dir: Path):
        self.repo_dir = repo_dir
        
    async def analyze(self) -> str:
        """Analyze the codebase and return a summary."""
        analysis = {
            "files": [],
            "total_files": 0,
            "total_size_mb": 0,
            "languages": {},
            "key_files": []
        }
        
        # Walk through repository
        for root, dirs, files in os.walk(self.repo_dir):
            # Skip hidden and vendor directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and 
                      d not in ['node_modules', 'vendor', '__pycache__', 'venv', '.git']]
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.repo_dir)
                
                # Track file extension
                ext = file_path.suffix.lower()
                if ext:
                    analysis["languages"][ext] = analysis["languages"].get(ext, 0) + 1
                
                analysis["total_files"] += 1
                
                # Add file info
                file_info = {
                    "path": str(relative_path),
                    "size": file_path.stat().st_size
                }
                analysis["files"].append(file_info)
        
        # Calculate total size
        analysis["total_size_mb"] = self._get_directory_size_mb()
        
        # Identify key files
        analysis["key_files"] = self._identify_key_files()
        
        # Build summary
        summary = await self._build_summary(analysis)
        return summary
    
    def _get_directory_size_mb(self) -> float:
        """Get directory size in MB."""
        total_size = sum(f.stat().st_size for f in self.repo_dir.rglob('*') if f.is_file())
        return round(total_size / (1024 * 1024), 2)
    
    def _identify_key_files(self) -> List[str]:
        """Identify important files in the repository."""
        key_patterns = [
            "README*", "readme*",
            "package.json", "requirements.txt", "setup.py", "Cargo.toml", "go.mod",
            "Dockerfile", "docker-compose*",
            ".github/workflows/*",
            "main.*", "app.*", "index.*",
            "config.*", "settings.*"
        ]
        
        key_files = []
        for pattern in key_patterns:
            if '*' in pattern:
                # Handle wildcards
                import glob
                matches = glob.glob(str(self.repo_dir / pattern), recursive=True)
                for match in matches:
                    try:
                        rel_path = Path(match).relative_to(self.repo_dir)
                        key_files.append(str(rel_path))
                    except:
                        pass
            else:
                # Direct file check
                file_path = self.repo_dir / pattern
                if file_path.exists():
                    key_files.append(pattern)
        
        return key_files
    
    async def _build_summary(self, analysis: Dict) -> str:
        """Build a text summary of the analysis."""
        repo_url = os.getenv("REPO_URL", "Unknown")
        
        summary_parts = [
            f"Repository: {repo_url}",
            f"Total files: {analysis['total_files']}",
            f"Total size: {analysis['total_size_mb']} MB",
            f"Languages: {', '.join(f'{k}({v})' for k, v in sorted(analysis['languages'].items(), key=lambda x: x[1], reverse=True)[:5])}",
            "",
            "Key files:",
        ]
        
        # Read contents of key files
        for key_file in analysis["key_files"][:10]:  # Limit to top 10 files
            file_path = self.repo_dir / key_file
            if file_path.exists() and file_path.stat().st_size < 50000:  # Skip large files
                try:
                    async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = await f.read()
                        summary_parts.extend([
                            f"\n--- {key_file} ---",
                            content[:2000],  # First 2000 chars
                            "..." if len(content) > 2000 else "",
                            ""
                        ])
                except Exception:
                    pass
        
        return "\n".join(summary_parts)