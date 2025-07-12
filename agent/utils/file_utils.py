"""File and directory utilities."""

import subprocess
from pathlib import Path
from typing import Optional


def get_directory_size(path: Path) -> float:
    """Get directory size in MB."""
    if not path.exists():
        return 0.0
        
    total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
    return round(total_size / (1024 * 1024), 2)


def get_cli_version(command: str) -> str:
    """Get version of a CLI tool."""
    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except FileNotFoundError:
        return "Error: Command not found"
    except Exception as e:
        return f"Error: {str(e)}"