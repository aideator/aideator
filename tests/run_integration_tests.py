#!/usr/bin/env python3
"""
Integration test runner for AIdeator Charlie track.

This script runs all integration tests and provides comprehensive reporting
for Gateway connectivity, streaming, and API functionality.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


class IntegrationTestRunner:
    """Comprehensive integration test runner."""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.test_results = {}
        self.gateway_url = os.getenv("LITELLM_GATEWAY_URL", "http://localhost:4000")
        self.api_url = os.getenv("API_BASE_URL", "http://localhost:8000")

    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        console.print("\n[bold blue]Checking Prerequisites...[/bold blue]")

        checks = [
            ("Python pytest", self._check_pytest),
            ("Backend API", self._check_backend_api),
            ("LiteLLM Gateway", self._check_gateway),
            ("Environment Variables", self._check_env_vars),
            ("Test Dependencies", self._check_test_deps),
        ]

        all_good = True
        for check_name, check_func in checks:
            try:
                result = check_func()
                status = "✅" if result else "❌"
                console.print(f"  {status} {check_name}")
                if not result:
                    all_good = False
            except Exception as e:
                console.print(f"  ❌ {check_name}: {e}")
                all_good = False

        return all_good

    def _check_pytest(self) -> bool:
        """Check if pytest is available."""
        try:
            subprocess.run(["pytest", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _check_backend_api(self) -> bool:
        """Check if backend API is running."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def _check_gateway(self) -> bool:
        """Check if LiteLLM Gateway is running."""
        try:
            response = requests.get(f"{self.gateway_url}/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def _check_env_vars(self) -> bool:
        """Check required environment variables."""
        required_vars = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
        ]

        for var in required_vars:
            if not os.getenv(var):
                console.print(f"    Missing: {var}")
                return False

        return True

    def _check_test_deps(self) -> bool:
        """Check if test dependencies are installed."""
        try:
            import aiohttp
            import httpx
            import openai
            import rich

            return True
        except ImportError as e:
            console.print(f"    Missing dependency: {e}")
            return False

    def run_test_suite(self, test_file: str, test_name: str) -> dict:
        """Run a specific test suite."""
        console.print(f"\n[bold yellow]Running {test_name}...[/bold yellow]")

        start_time = time.time()

        # Run pytest with detailed output
        cmd = [
            "pytest",
            test_file,
            "-v",
            "--tb=short",
            "--capture=no",
            "--durations=10",
            f"--junit-xml=test_results_{test_name.lower().replace(' ', '_')}.xml",
        ]

        try:
            result = subprocess.run(
                cmd,
                check=False,
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            duration = time.time() - start_time

            # Parse results
            passed = result.returncode == 0
            output = result.stdout + result.stderr

            return {
                "passed": passed,
                "duration": duration,
                "output": output,
                "return_code": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "duration": 300,
                "output": "Test timed out after 5 minutes",
                "return_code": -1,
            }
        except Exception as e:
            return {
                "passed": False,
                "duration": time.time() - start_time,
                "output": f"Test failed with exception: {e}",
                "return_code": -1,
            }

    def run_all_tests(self) -> dict:
        """Run all integration tests."""
        console.print(
            "\n[bold green]🚀 Starting AIdeator Integration Tests[/bold green]"
        )

        # Check prerequisites first
        if not self.check_prerequisites():
            console.print(
                "\n[bold red]❌ Prerequisites not met. Please fix the issues above.[/bold red]"
            )
            return {"overall_passed": False, "results": {}}

        # Define test suites
        test_suites = [
            {
                "file": "tests/integration/test_litellm_gateway.py",
                "name": "LiteLLM Gateway Integration",
                "description": "Tests Gateway connectivity, model routing, and error handling",
            },
            {
                "file": "tests/integration/test_streaming_integration.py",
                "name": "Streaming Integration",
                "description": "Tests multi-model streaming, SSE, and real-time functionality",
            },
        ]

        results = {}
        overall_passed = True

        # Run each test suite
        for suite in test_suites:
            console.print(f"\n[dim]{suite['description']}[/dim]")

            result = self.run_test_suite(suite["file"], suite["name"])
            results[suite["name"]] = result

            if not result["passed"]:
                overall_passed = False

            # Show immediate feedback
            status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            console.print(f"  {status} ({result['duration']:.2f}s)")

            # Show failures immediately
            if not result["passed"]:
                console.print("[red]Test Output:[/red]")
                console.print(result["output"][-1000:])  # Last 1000 chars

        return {"overall_passed": overall_passed, "results": results}

    def generate_report(self, test_results: dict) -> None:
        """Generate a comprehensive test report."""
        console.print("\n" + "=" * 80)
        console.print("[bold blue]🔍 TEST REPORT[/bold blue]")
        console.print("=" * 80)

        # Overall status
        if test_results["overall_passed"]:
            console.print("[bold green]✅ ALL TESTS PASSED[/bold green]")
        else:
            console.print("[bold red]❌ SOME TESTS FAILED[/bold red]")

        # Create results table
        table = Table(title="Test Suite Results")
        table.add_column("Test Suite", style="bold")
        table.add_column("Status", justify="center")
        table.add_column("Duration", justify="right")
        table.add_column("Details")

        for suite_name, result in test_results["results"].items():
            status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            duration = f"{result['duration']:.2f}s"

            if result["passed"]:
                details = "All tests passed successfully"
            else:
                details = f"Return code: {result['return_code']}"

            table.add_row(suite_name, status, duration, details)

        console.print(table)

        # Show detailed failures
        for suite_name, result in test_results["results"].items():
            if not result["passed"]:
                console.print(f"\n[bold red]❌ {suite_name} Failures:[/bold red]")
                console.print(
                    Panel(
                        result["output"][-2000:],  # Last 2000 chars
                        title=f"Error Output - {suite_name}",
                        border_style="red",
                    )
                )

        # Summary statistics
        total_suites = len(test_results["results"])
        passed_suites = sum(1 for r in test_results["results"].values() if r["passed"])
        failed_suites = total_suites - passed_suites
        total_time = sum(r["duration"] for r in test_results["results"].values())

        console.print("\n[bold]Summary:[/bold]")
        console.print(f"  Total test suites: {total_suites}")
        console.print(f"  Passed: {passed_suites}")
        console.print(f"  Failed: {failed_suites}")
        console.print(f"  Total time: {total_time:.2f}s")

        # Recommendations
        if not test_results["overall_passed"]:
            console.print("\n[bold yellow]🔧 Recommendations:[/bold yellow]")
            console.print(
                "  1. Check that LiteLLM Gateway is running with correct configuration"
            )
            console.print("  2. Verify all required environment variables are set")
            console.print("  3. Ensure backend API is running and accessible")
            console.print("  4. Review test output above for specific error details")

    def run_specific_tests(self, test_patterns: list[str]) -> dict:
        """Run specific tests matching patterns."""
        console.print(
            f"\n[bold yellow]Running specific tests: {', '.join(test_patterns)}[/bold yellow]"
        )

        cmd = ["pytest", "-v", "--tb=short", "--capture=no", *test_patterns]

        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                check=False,
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=300,
            )

            duration = time.time() - start_time
            passed = result.returncode == 0

            return {
                "overall_passed": passed,
                "results": {
                    "Specific Tests": {
                        "passed": passed,
                        "duration": duration,
                        "output": result.stdout + result.stderr,
                        "return_code": result.returncode,
                    }
                },
            }

        except Exception as e:
            return {
                "overall_passed": False,
                "results": {
                    "Specific Tests": {
                        "passed": False,
                        "duration": time.time() - start_time,
                        "output": f"Failed to run tests: {e}",
                        "return_code": -1,
                    }
                },
            }


def main():
    """Main entry point."""
    runner = IntegrationTestRunner()

    # Parse command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--specific":
        # Run specific tests
        patterns = sys.argv[2:] if len(sys.argv) > 2 else ["tests/integration/"]
        results = runner.run_specific_tests(patterns)
    else:
        # Run all tests
        results = runner.run_all_tests()

    # Generate report
    runner.generate_report(results)

    # Exit with appropriate code
    sys.exit(0 if results["overall_passed"] else 1)


if __name__ == "__main__":
    main()
