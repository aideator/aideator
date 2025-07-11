#!/usr/bin/env python3
"""Unit test runner script."""

import subprocess
import sys


def main():
    """Run unit tests with coverage."""
    cmd = ["pytest", "tests/unit/", "-v", "--cov=app", "--cov-report=html"]

    result = subprocess.run(cmd, check=False)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
