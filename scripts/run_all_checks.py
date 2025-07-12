#!/usr/bin/env python3
"""Run all checks: linting, type checking, unit tests, integration tests, and coverage."""

import subprocess
import sys
import time
from pathlib import Path


def run_command_sequential(
    cmd: list[str], description: str, timeout_seconds: int = 300
) -> bool:
    """Run a command and stream output in real-time."""
    print(f"\n{'=' * 80}")
    print(f"🚀 Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"Timeout: {timeout_seconds}s")
    print("=" * 80)

    start_time = time.time()

    try:
        # Run with real-time output
        result = subprocess.run(cmd, timeout=timeout_seconds, check=False)

        elapsed = time.time() - start_time

        if result.returncode != 0:
            print(f"\n❌ {description} failed! (took {elapsed:.1f}s)")
            return False
        print(f"\n✅ {description} passed! (took {elapsed:.1f}s)")
        return True

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(
            f"\n❌ {description} timed out after {timeout_seconds}s! (ran for {elapsed:.1f}s)"
        )
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ {description} crashed! (took {elapsed:.1f}s)")
        print(f"Error: {e}")
        return False


def main() -> int:
    """Run all checks sequentially with real-time output."""
    # Change to project root
    _project_root = Path(__file__).parent.parent

    # Auto-fix any ruff issues first
    print("🔧 Auto-fixing code issues...")
    print("=" * 80)

    # Run ruff fix
    fix_result = subprocess.run(
        ["uv", "run", "ruff", "check", ".", "--fix"],
        check=False,
        capture_output=True,
        text=True,
    )
    if fix_result.stdout:
        print("Ruff fixes applied:")
        print(fix_result.stdout)

    # Run ruff format
    format_result = subprocess.run(
        ["uv", "run", "ruff", "format", "."],
        check=False,
        capture_output=True,
        text=True,
    )
    if format_result.stdout:
        print("Ruff format applied:")
        print(format_result.stdout)

    print("=" * 80)

    checks = [
        # Linting with ruff (very fast, 5s timeout) - should pass after auto-fix
        (["uv", "run", "ruff", "check", "."], "Ruff Linting", 5),
        (["uv", "run", "ruff", "format", "--check", "."], "Ruff Format Check", 5),
        # Type checking with ty (fast, 10s timeout)
        (["uv", "run", "ty", "check", "app/"], "Type Checking (ty)", 10),
        # Unit tests with coverage (medium, 60s timeout)
        (
            [
                "uv",
                "run",
                "pytest",
                "tests/unit/",
                "-v",
                "--cov=app",
                "--cov-report=term-missing",
                "--cov-report=html",
            ],
            "Unit Tests with Coverage",
            60,
        ),
        # Integration tests (long, 300s/5min timeout) - no coverage
        # Check if integration tests exist first
        *(
            [
                (
                    ["uv", "run", "pytest", "tests/integration/", "-v"],
                    "Integration Tests",
                    300,
                )
            ]
            if Path("tests/integration").exists()
            and any(Path("tests/integration").glob("test_*.py"))
            else []
        ),
    ]

    print("🚀 AIdeator Test Suite")
    print(f"Running {len(checks)} checks: {', '.join(desc for _, desc, _ in checks)}")
    print("=" * 80)

    start_time = time.time()
    all_passed = True
    passed_count = 0
    failed_count = 0

    # Run all checks sequentially
    for cmd, desc, timeout in checks:
        success = run_command_sequential(cmd, desc, timeout)
        if success:
            passed_count += 1
        else:
            failed_count += 1
            all_passed = False

    total_time = time.time() - start_time

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    print(f"✅ Passed: {passed_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"⏱️  Total time: {total_time:.1f}s")

    if all_passed:
        print("\n🎉 All checks passed!")
        exit_code = 0
    else:
        print(f"\n❌ {failed_count} check(s) failed. Please fix the issues above.")
        exit_code = 1

    # Force exit to handle any hanging threads/processes
    print("\nForcing exit...")
    import os

    os._exit(exit_code)


if __name__ == "__main__":
    sys.exit(main())
