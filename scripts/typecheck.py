#!/usr/bin/env python3
"""Script to run type checking with ty."""

import subprocess
import sys


def main():
    """Run ty check."""
    try:
        result = subprocess.run(["ty", "check", "app/"], check=False)
        sys.exit(result.returncode)
    except FileNotFoundError:
        print("ty not found. Please install ty.")
        sys.exit(1)


if __name__ == "__main__":
    main()
