#!/usr/bin/env python3
"""
Comprehensive test runner for the IRIS API Integration System.

This script provides an advanced test runner with multiple execution modes,
comprehensive reporting, and integration with external services.
"""

import argparse
import asyncio
import os
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import tempfile

# Rich for beautiful terminal output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.tree import Tree
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


@dataclass
class TestResult:
    """Container for test execution results."""
    command: str
    returncode: int
    stdout: str
    stderr: str
    duration: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def success(self) -> bool:
        return self.returncode == 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration": self.duration,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success
        }


@dataclass
class TestSuite:
    """Test suite configuration."""
    name: str
    description: str
    command: str
    markers: List[str] = field(default_factory=list)
    requires_services: bool = False
    timeout: Optional[int] = None
    parallel: bool = False
    
    def build_command(self, base_args: List[str] = None) -> str:
        """Build the full pytest command."""
        cmd_parts = ["pytest"]
        
        if base_args:
            cmd_parts.extend(base_args)
        
        if self.markers:
            marker_expr = " and ".join(self.markers)
            cmd_parts.extend(["-m", f'"{marker_expr}"'])
        
        if self.parallel:
            cmd_parts.extend(["-n", "auto"])
        
        if self.timeout:
            cmd_parts.extend(["--timeout", str(self.timeout)])
        
        cmd_parts.extend(self.command.split() if isinstance(self.command, str) else self.command)
        
        return " ".join(cmd_parts)


class TestRunner:
    """Advanced test runner with comprehensive reporting."""
    
    def __init__(self, console=None):
        self.console = console or (Console() if RICH_AVAILABLE else None)
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None
        
        # Define test suites
        self.test_suites = {
            "unit": TestSuite(
                name="Unit Tests",
                description="Fast, isolated unit tests",
                command="",
                markers=["unit", "not slow"],
            ),
            "integration": TestSuite(
                name="Integration Tests",
                description="Integration tests with external dependencies",
                command="",
                markers=["integration"],
                requires_services=True,
                timeout=300,
            ),
            "security": TestSuite(
                name="Security Tests",
                description="Security and authentication tests",
                command="",
                markers=["security"],
                timeout=120,
            ),
            "performance": TestSuite(
                name="Performance Tests",
                description="Performance and benchmark tests",
                command="--benchmark-only",
                markers=["performance"],
                timeout=600,
            ),
            "api": TestSuite(
                name="API Tests",
                description="API endpoint tests",
                command="",
                markers=["api"],
                requires_services=True,
            ),
            "database": TestSuite(
                name="Database Tests",
                description="Database-related tests",
                command="",
                markers=["database"],
                requires_services=True,
            ),
            "event_bus": TestSuite(
                name="Event Bus Tests",
                description="Event bus and messaging tests",
                command="",
                markers=["event_bus"],
            ),
            "smoke": TestSuite(
                name="Smoke Tests",
                description="Basic functionality smoke tests",
                command="--tb=short",
                markers=["smoke"],
                timeout=60,
            ),
            "regression": TestSuite(
                name="Regression Tests",
                description="Regression tests for known issues",
                command="",
                markers=["regression"],
            ),
            "e2e": TestSuite(
                name="End-to-End Tests",
                description="Complete workflow tests",
                command="--tb=short",
                markers=["e2e"],
                requires_services=True,
                timeout=900,
            ),
            "containers": TestSuite(
                name="Container Tests",
                description="Tests using real containers",
                command="",
                markers=["requires_containers"],
                requires_services=True,
                timeout=600,
            ),
        }
    
    def print(self, *args, **kwargs):
        """Print with rich console if available."""
        if self.console:
            self.console.print(*args, **kwargs)
        else:
            print(*args, **kwargs)
    
    async def run_command(self, command: str, timeout: Optional[int] = None) -> TestResult:
        """Run a command asynchronously and capture results."""
        start_time = time.time()
        
        try:
            # Run command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                stderr = b"Command timed out"
                stdout = b""
            
            duration = time.time() - start_time
            
            result = TestResult(
                command=command,
                returncode=process.returncode or -1,
                stdout=stdout.decode('utf-8', errors='replace'),
                stderr=stderr.decode('utf-8', errors='replace'),
                duration=duration
            )
            
            self.results.append(result)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult(
                command=command,
                returncode=-1,
                stdout="",
                stderr=str(e),
                duration=duration
            )
            self.results.append(result)
            return result
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        missing = []
        
        # Check pytest
        try:
            subprocess.run(["pytest", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append("pytest")
        
        # Check if in correct directory
        if not Path("app").exists() or not Path("app/tests").exists():
            missing.append("app/tests directory")
        
        if missing:
            self.print(f"[red]Missing prerequisites: {', '.join(missing)}[/red]")
            return False
        
        return True
    
    def check_services(self, required: bool = False) -> bool:
        """Check if test services are running."""
        if not required:
            return True
        
        # Check if docker-compose is available
        try:
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.test.yml", "ps"],
                capture_output=True,
                check=False
            )
            if result.returncode != 0:
                self.print("[yellow]Test services not running. Start with: make start-services[/yellow]")
                return False
        except FileNotFoundError:
            self.print("[yellow]docker-compose not available for service checks[/yellow]")
        
        return True
    
    async def run_test_suite(self, suite_name: str, base_args: List[str] = None) -> TestResult:
        """Run a specific test suite."""
        if suite_name not in self.test_suites:
            raise ValueError(f"Unknown test suite: {suite_name}")
        
        suite = self.test_suites[suite_name]
        
        # Check services if required
        if not self.check_services(suite.requires_services):
            return TestResult(
                command="service_check",
                returncode=1,
                stdout="",
                stderr="Required services not available",
                duration=0
            )
        
        # Build command
        command = suite.build_command(base_args)
        
        # Run the test suite
        self.print(f"[blue]Running {suite.name}...[/blue]")
        if self.console:
            self.print(f"[dim]{suite.description}[/dim]")
            self.print(f"[dim]Command: {command}[/dim]")
        
        result = await self.run_command(command, suite.timeout)
        
        # Report results
        if result.success:
            self.print(f"[green]✓ {suite.name} completed successfully ({result.duration:.2f}s)[/green]")
        else:
            self.print(f"[red]✗ {suite.name} failed ({result.duration:.2f}s)[/red]")
            if result.stderr:
                self.print(f"[red]Error: {result.stderr[:200]}...[/red]")
        
        return result
    
    async def run_suites(self, suite_names: List[str], base_args: List[str] = None) -> List[TestResult]:
        """Run multiple test suites."""
        results = []
        
        for suite_name in suite_names:
            result = await self.run_test_suite(suite_name, base_args)
            results.append(result)
            
            # Stop on first failure if requested
            if not result.success and "--fail-fast" in (base_args or []):
                break
        
        return results
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate comprehensive test report."""
        if not self.results:
            return "No test results available."
        
        total_duration = sum(r.duration for r in self.results)
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        
        report_lines = [
            "=" * 80,
            "IRIS API Integration System - Test Report",
            "=" * 80,
            f"Generated: {datetime.now().isoformat()}",
            f"Total Suites: {len(self.results)}",
            f"Successful: {len(successful)}",
            f"Failed: {len(failed)}",
            f"Total Duration: {total_duration:.2f}s",
            "",
        ]
        
        # Add detailed results
        for result in self.results:
            status = "PASS" if result.success else "FAIL"
            report_lines.extend([
                f"[{status}] {result.command}",
                f"  Duration: {result.duration:.2f}s",
                f"  Return Code: {result.returncode}",
                ""
            ])
            
            if not result.success and result.stderr:
                report_lines.extend([
                    "  Error Output:",
                    "  " + "\n  ".join(result.stderr.split("\n")[:10]),
                    ""
                ])
        
        report = "\n".join(report_lines)
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            self.print(f"[green]Report saved to {output_file}[/green]")
        
        return report
    
    def generate_json_report(self, output_file: str = "test-report.json"):
        """Generate JSON report for CI/CD integration."""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "total_suites": len(self.results),
            "successful": len([r for r in self.results if r.success]),
            "failed": len([r for r in self.results if not r.success]),
            "total_duration": sum(r.duration for r in self.results),
            "results": [r.to_dict() for r in self.results]
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        self.print(f"[green]JSON report saved to {output_file}[/green]")
    
    def print_summary(self):
        """Print test execution summary."""
        if not self.results:
            return
        
        if self.console and RICH_AVAILABLE:
            # Rich table summary
            table = Table(title="Test Execution Summary")
            table.add_column("Suite", style="cyan")
            table.add_column("Status", style="bold")
            table.add_column("Duration", justify="right")
            table.add_column("Details")
            
            for result in self.results:
                status = "[green]PASS[/green]" if result.success else "[red]FAIL[/red]"
                duration = f"{result.duration:.2f}s"
                details = "Success" if result.success else "Error"
                
                table.add_row(result.command.split()[1] if len(result.command.split()) > 1 else result.command, 
                             status, duration, details)
            
            self.console.print(table)
        else:
            # Simple text summary
            self.print("\nTest Execution Summary:")
            self.print("-" * 40)
            for result in self.results:
                status = "PASS" if result.success else "FAIL"
                self.print(f"{status:4} {result.command} ({result.duration:.2f}s)")


async def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(
        description="Advanced test runner for IRIS API Integration System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py unit                    # Run unit tests
  python run_tests.py integration --coverage  # Run integration tests with coverage
  python run_tests.py --all --report          # Run all tests and generate report
  python run_tests.py smoke e2e --parallel    # Run smoke and e2e tests in parallel
        """
    )
    
    # Test suite selection
    parser.add_argument(
        "suites",
        nargs="*",
        help="Test suites to run (unit, integration, security, performance, etc.)"
    )
    
    parser.add_argument("--all", action="store_true", help="Run all test suites")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only (unit + smoke)")
    parser.add_argument("--ci", action="store_true", help="Run CI test suite")
    
    # Test execution options
    parser.add_argument("--coverage", action="store_true", help="Run with coverage")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first failure")
    parser.add_argument("--timeout", type=int, help="Global timeout for all tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # Service management
    parser.add_argument("--start-services", action="store_true", help="Start test services before running")
    parser.add_argument("--stop-services", action="store_true", help="Stop test services after running")
    
    # Reporting
    parser.add_argument("--report", action="store_true", help="Generate test report")
    parser.add_argument("--json-report", action="store_true", help="Generate JSON report")
    parser.add_argument("--output", help="Output file for reports")
    
    # Development options
    parser.add_argument("--watch", action="store_true", help="Watch mode (requires pytest-watch)")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = TestRunner()
    
    # Check prerequisites
    if not runner.check_prerequisites():
        return 1
    
    # Determine which suites to run
    suites_to_run = []
    
    if args.all:
        suites_to_run = list(runner.test_suites.keys())
    elif args.quick:
        suites_to_run = ["unit", "smoke"]
    elif args.ci:
        suites_to_run = ["unit", "integration", "security", "api"]
    elif args.suites:
        suites_to_run = args.suites
    else:
        suites_to_run = ["unit"]  # Default
    
    # Validate suite names
    invalid_suites = [s for s in suites_to_run if s not in runner.test_suites]
    if invalid_suites:
        runner.print(f"[red]Invalid test suites: {', '.join(invalid_suites)}[/red]")
        runner.print(f"Available suites: {', '.join(runner.test_suites.keys())}")
        return 1
    
    # Build base pytest arguments
    base_args = []
    
    if args.verbose:
        base_args.append("-v")
    
    if args.coverage:
        base_args.extend(["--cov=app", "--cov-report=html", "--cov-report=term-missing"])
    
    if args.fail_fast:
        base_args.append("--fail-fast")
    
    if args.timeout:
        base_args.extend(["--timeout", str(args.timeout)])
    
    if args.debug:
        base_args.extend(["--pdb", "--tb=long"])
    
    # Start services if requested
    if args.start_services:
        runner.print("[blue]Starting test services...[/blue]")
        await runner.run_command("make start-services")
    
    try:
        # Run test suites
        runner.start_time = datetime.now()
        
        if args.watch:
            # Watch mode
            runner.print("[blue]Starting watch mode...[/blue]")
            await runner.run_command("pytest-watch -- " + " ".join(base_args))
        else:
            # Normal execution
            await runner.run_suites(suites_to_run, base_args)
        
        runner.end_time = datetime.now()
        
        # Print summary
        runner.print_summary()
        
        # Generate reports
        if args.report or args.json_report:
            if args.report:
                report = runner.generate_report(args.output)
                if not args.output:
                    runner.print("\n" + report)
            
            if args.json_report:
                json_output = args.output.replace('.txt', '.json') if args.output else 'test-report.json'
                runner.generate_json_report(json_output)
        
        # Determine exit code
        failed_suites = [r for r in runner.results if not r.success]
        exit_code = len(failed_suites)
        
        if exit_code == 0:
            runner.print("[green]All test suites passed! 🎉[/green]")
        else:
            runner.print(f"[red]{exit_code} test suite(s) failed[/red]")
        
        return min(exit_code, 1)  # Cap at 1 for shell compatibility
    
    finally:
        # Stop services if requested
        if args.stop_services:
            runner.print("[blue]Stopping test services...[/blue]")
            await runner.run_command("make stop-services")


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)