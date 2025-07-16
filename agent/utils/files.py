"""
File utilities for agent operations.

Common file operations and utilities used across the agent.
"""

import subprocess
from pathlib import Path


def get_cli_version(command: str) -> str:
    """Get version of a CLI tool.
    
    Args:
        command: CLI command to check version for
        
    Returns:
        Version string or error message
    """
    try:
        result = subprocess.run(
            [command, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return f"Error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except FileNotFoundError:
        return "Error: Command not found"
    except Exception as e:
        return f"Error: {e!s}"


def ensure_directory_exists(path: Path) -> bool:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure exists
        
    Returns:
        True if directory exists or was created successfully
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def safe_file_read(file_path: Path, max_size: int = 50000) -> str | None:
    """Safely read file content with size limit.
    
    Args:
        file_path: Path to file to read
        max_size: Maximum file size to read in bytes
        
    Returns:
        File content or None if read failed
    """
    try:
        if not file_path.exists() or file_path.stat().st_size > max_size:
            return None

        with open(file_path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return None


def is_text_file(file_path: Path) -> bool:
    """Check if a file is likely a text file.
    
    Args:
        file_path: Path to file to check
        
    Returns:
        True if file appears to be text
    """
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            return b"\0" not in chunk
    except Exception:
        return False
