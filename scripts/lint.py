#!/usr/bin/env python3
"""Script to run linting with ruff."""

import subprocess
import sys


def main():
    """Run ruff check."""
    try:
        result = subprocess.run(["ruff", "check", "."], check=False)
        sys.exit(result.returncode)
    except FileNotFoundError:
        print("ruff not found. Please install ruff.")
        sys.exit(1)


if __name__ == "__main__":
    main()
