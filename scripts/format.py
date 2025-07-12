#!/usr/bin/env python3
"""Script to run formatting with ruff."""

import subprocess
import sys


def main():
    """Run ruff format."""
    try:
        result = subprocess.run(["ruff", "format", "."], check=False)
        sys.exit(result.returncode)
    except FileNotFoundError:
        print("ruff not found. Please install ruff.")
        sys.exit(1)


if __name__ == "__main__":
    main()
