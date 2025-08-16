#!/usr/bin/env python3
"""
Clinical Workflows Test Runner

Enterprise-grade test execution script with comprehensive reporting.
Supports different test categories, parallel execution, and detailed reporting.
"""

import os
import sys
import argparse
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class ClinicalWorkflowTestRunner:
    """Comprehensive test runner for clinical workflows module."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).parent
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def run_test_category(self, category: str, parallel: bool = False, verbose: bool = True) -> Dict[str, Any]:
        """Run tests for a specific category."""
        print(f"\\n{'='*60}")
        print(f"Running {category.upper()} Tests")
        print(f"{'='*60}")
        
        # Define test categories and their configurations
        test_categories = {
            "unit": {
                "markers": "unit and not slow",
                "description": "Unit Tests - Isolated component testing",
                "timeout": 120,
                "coverage": True
            },
            "integration": {
                "markers": "integration and not slow", 
                "description": "Integration Tests - Component interaction testing",
                "timeout": 300,
                "coverage": True
            },
            "security": {
                "markers": "security",
                "description": "Security Tests - PHI protection and compliance",
                "timeout": 180,
                "coverage": True
            },
            "performance": {
                "markers": "performance",
                "description": "Performance Tests - Speed and scalability",
                "timeout": 600,
                "coverage": False
            },
            "e2e": {
                "markers": "e2e",
                "description": "End-to-End Tests - Complete workflow scenarios", 
                "timeout": 900,
                "coverage": False
            },
            "fast": {
                "markers": "fast or (unit and not slow)",
                "description": "Fast Tests - Quick validation",
                "timeout": 60,
                "coverage": True
            },
            "all": {
                "markers": "",
                "description": "All Tests - Complete test suite",
                "timeout": 1800,
                "coverage": True
            }
        }
        
        if category not in test_categories:
            raise ValueError(f"Unknown test category: {category}")
        
        config = test_categories[category]
        print(f"Description: {config['description']}")
        print(f"Timeout: {config['timeout']} seconds")
        print(f"Parallel: {parallel}")
        print(f"Coverage: {config['coverage']}")
        
        # Build pytest command
        cmd = ["python", "-m", "pytest"]
        
        # Add test directory
        cmd.append(str(self.base_dir))
        
        # Add markers
        if config["markers"]:
            cmd.extend(["-m", config["markers"]])
        
        # Add verbosity
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
        
        # Add parallel execution
        if parallel:
            cmd.extend(["-n", "auto"])
        
        # Add timeout
        cmd.extend(["--timeout", str(config["timeout"])])
        
        # Add coverage
        if config["coverage"]:
            cmd.extend([
                "--cov=app/modules/clinical_workflows",
                "--cov-report=term-missing",
                f"--cov-report=html:htmlcov/clinical_workflows_{category}",
                f"--cov-report=xml:coverage-{category}.xml"
            ])
        
        # Add output files
        cmd.extend([
            f"--junitxml=test-results-{category}.xml",
            "--tb=short"
        ])
        
        # Execute tests
        start_time = time.time()
        print(f"\\nExecuting: {' '.join(cmd)}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=config["timeout"])
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse results
            success = result.returncode == 0
            
            test_result = {
                "category": category,
                "success": success,
                "duration": duration,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd),
                "start_time": start_time,
                "end_time": end_time
            }
            
            # Print summary
            print(f"\\n{'-'*60}")
            print(f"Test Category: {category.upper()}")
            print(f"Result: {'PASSED' if success else 'FAILED'}")
            print(f"Duration: {duration:.2f} seconds")
            print(f"Return Code: {result.returncode}")
            
            if verbose and result.stdout:
                print(f"\\nSTDOUT:")
                print(result.stdout[-2000:])  # Last 2000 chars
            
            if result.stderr:
                print(f"\\nSTDERR:")
                print(result.stderr[-1000:])  # Last 1000 chars
            
            return test_result
            
        except subprocess.TimeoutExpired:
            print(f"\\n❌ Tests timed out after {config['timeout']} seconds")
            return {
                "category": category,
                "success": False,
                "duration": config["timeout"],
                "return_code": -1,
                "error": "Timeout",
                "command": " ".join(cmd)
            }
        
        except Exception as e:
            print(f"\\n❌ Error running tests: {e}")
            return {
                "category": category,
                "success": False,
                "duration": 0,
                "return_code": -1,
                "error": str(e),
                "command": " ".join(cmd)
            }
    
    def run_role_based_tests(self, role: str, parallel: bool = False) -> Dict[str, Any]:
        """Run tests for a specific user role."""
        print(f"\\n{'='*60}")
        print(f"Running {role.upper()} Role Tests")
        print(f"{'='*60}")
        
        valid_roles = [
            "physician", "nurse", "admin", "clinical_admin", 
            "ai_researcher", "patient", "unauthorized"
        ]
        
        if role not in valid_roles:
            raise ValueError(f"Unknown role: {role}. Valid roles: {valid_roles}")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.base_dir),
            "-m", role,
            "-v",
            "--tb=short",
            f"--junitxml=test-results-role-{role}.xml"
        ]
        
        if parallel:
            cmd.extend(["-n", "auto"])
        
        return self._execute_command(cmd, f"role-{role}")
    
    def run_compliance_tests(self, standard: str) -> Dict[str, Any]:
        """Run compliance tests for specific standards."""
        print(f"\\n{'='*60}")
        print(f"Running {standard.upper()} Compliance Tests")
        print(f"{'='*60}")
        
        valid_standards = ["hipaa", "soc2", "fhir"]
        
        if standard not in valid_standards:
            raise ValueError(f"Unknown standard: {standard}. Valid: {valid_standards}")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.base_dir),
            "-m", standard,
            "-v",
            "--tb=long",  # Detailed output for compliance
            f"--junitxml=test-results-compliance-{standard}.xml",
            "--cov=app/modules/clinical_workflows",
            f"--cov-report=html:htmlcov/compliance_{standard}",
            f"--cov-report=xml:coverage-compliance-{standard}.xml"
        ]
        
        return self._execute_command(cmd, f"compliance-{standard}")
    
    def run_security_audit(self) -> Dict[str, Any]:
        """Run comprehensive security audit tests."""
        print(f"\\n{'='*60}")
        print("Running Security Audit Tests")
        print(f"{'='*60}")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.base_dir / "security"),
            "-v",
            "--tb=long",
            "--junitxml=test-results-security-audit.xml",
            "--cov=app/modules/clinical_workflows",
            "--cov-report=html:htmlcov/security_audit",
            "--cov-report=xml:coverage-security-audit.xml",
            "-m", "security"
        ]
        
        return self._execute_command(cmd, "security-audit")
    
    def run_performance_benchmark(self) -> Dict[str, Any]:
        """Run performance benchmark tests."""
        print(f"\\n{'='*60}")
        print("Running Performance Benchmark Tests")
        print(f"{'='*60}")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.base_dir / "performance"),
            "-v",
            "--tb=short",
            "--benchmark-only",
            "--benchmark-json=benchmark-results.json",
            "--junitxml=test-results-performance.xml",
            "-m", "performance"
        ]
        
        return self._execute_command(cmd, "performance-benchmark")
    
    def _execute_command(self, cmd: List[str], test_type: str) -> Dict[str, Any]:
        """Execute a test command and return results."""
        start_time = time.time()
        print(f"\\nExecuting: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            end_time = time.time()
            duration = end_time - start_time
            
            success = result.returncode == 0
            
            print(f"\\n{'-'*40}")
            print(f"Test Type: {test_type}")
            print(f"Result: {'PASSED' if success else 'FAILED'}")
            print(f"Duration: {duration:.2f} seconds")
            
            return {
                "test_type": test_type,
                "success": success,
                "duration": duration,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except Exception as e:
            print(f"❌ Error running {test_type}: {e}")
            return {
                "test_type": test_type,
                "success": False,
                "duration": 0,
                "error": str(e)
            }
    
    def generate_summary_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate comprehensive test summary report."""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.get("success", False))
        failed_tests = total_tests - passed_tests
        total_duration = sum(r.get("duration", 0) for r in results)
        
        report = f"""
Clinical Workflows Test Execution Summary
{'='*60}

Execution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Test Categories: {total_tests}
Passed: {passed_tests}
Failed: {failed_tests}
Success Rate: {(passed_tests/total_tests*100):.1f}%
Total Duration: {total_duration:.2f} seconds

Test Category Results:
{'-'*60}
"""
        
        for result in results:
            status = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
            category = result.get("category", result.get("test_type", "Unknown"))
            duration = result.get("duration", 0)
            
            report += f"{status:<12} {category:<20} ({duration:.2f}s)\\n"
        
        report += f"""
{'-'*60}

Detailed Results Available In:
- JUnit XML: test-results-*.xml
- Coverage Reports: htmlcov/
- Benchmark Results: benchmark-results.json

Enterprise Quality Gates:
{'✅' if passed_tests == total_tests else '❌'} All tests passing
{'✅' if total_duration < 1800 else '❌'} Total duration < 30 minutes
{'✅' if (passed_tests/total_tests) >= 0.95 else '❌'} Success rate >= 95%

"""
        return report
    
    def run_full_test_suite(self, parallel: bool = True, include_slow: bool = False) -> None:
        """Run the complete test suite with comprehensive reporting."""
        print("\\n" + "="*80)
        print("Clinical Workflows - Enterprise Test Suite Execution")
        print("="*80)
        
        self.start_time = time.time()
        
        # Define test execution plan
        test_plan = [
            ("fast", "Fast validation tests"),
            ("unit", "Unit tests"),
            ("integration", "Integration tests"),
            ("security", "Security tests")
        ]
        
        if include_slow:
            test_plan.extend([
                ("performance", "Performance tests"),
                ("e2e", "End-to-end tests")
            ])
        
        results = []
        
        # Execute test categories
        for category, description in test_plan:
            print(f"\\n\\n🔄 Starting: {description}")
            result = self.run_test_category(category, parallel=parallel)
            results.append(result)
            
            if not result.get("success", False):
                print(f"\\n⚠️  {category} tests failed - continuing with remaining tests")
        
        # Run compliance tests
        compliance_standards = ["hipaa", "soc2", "fhir"]
        for standard in compliance_standards:
            print(f"\\n\\n🔄 Starting: {standard.upper()} compliance tests")
            result = self.run_compliance_tests(standard)
            results.append(result)
        
        # Run security audit
        print(f"\\n\\n🔄 Starting: Security audit")
        security_result = self.run_security_audit()
        results.append(security_result)
        
        self.end_time = time.time()
        
        # Generate and print summary report
        summary_report = self.generate_summary_report(results)
        print(summary_report)
        
        # Save report to file
        report_file = f"test-execution-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(summary_report)
        
        print(f"📄 Full report saved to: {report_file}")
        
        # Exit with appropriate code
        all_passed = all(r.get("success", False) for r in results)
        exit_code = 0 if all_passed else 1
        
        print(f"\\n{'🎉 All tests passed!' if all_passed else '❌ Some tests failed.'}")
        print(f"Total execution time: {self.end_time - self.start_time:.2f} seconds")
        
        sys.exit(exit_code)


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="Clinical Workflows Enterprise Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --category unit              # Run unit tests
  python run_tests.py --category security          # Run security tests
  python run_tests.py --role physician             # Run physician role tests
  python run_tests.py --compliance hipaa           # Run HIPAA compliance tests
  python run_tests.py --full-suite                 # Run complete test suite
  python run_tests.py --full-suite --include-slow  # Include performance tests
        """
    )
    
    parser.add_argument(
        "--category", 
        choices=["unit", "integration", "security", "performance", "e2e", "fast", "all"],
        help="Run specific test category"
    )
    
    parser.add_argument(
        "--role",
        choices=["physician", "nurse", "admin", "clinical_admin", "ai_researcher", "patient", "unauthorized"],
        help="Run tests for specific user role"
    )
    
    parser.add_argument(
        "--compliance",
        choices=["hipaa", "soc2", "fhir"],
        help="Run compliance tests for specific standard"
    )
    
    parser.add_argument(
        "--security-audit",
        action="store_true",
        help="Run comprehensive security audit"
    )
    
    parser.add_argument(
        "--performance-benchmark",
        action="store_true", 
        help="Run performance benchmark tests"
    )
    
    parser.add_argument(
        "--full-suite",
        action="store_true",
        help="Run complete test suite"
    )
    
    parser.add_argument(
        "--include-slow",
        action="store_true",
        help="Include slow tests (performance, e2e)"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        default=True,
        help="Run tests in parallel (default: True)"
    )
    
    parser.add_argument(
        "--no-parallel",
        action="store_true",
        help="Disable parallel test execution"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Verbose output (default: True)"
    )
    
    args = parser.parse_args()
    
    # Determine parallel execution
    parallel = args.parallel and not args.no_parallel
    
    # Initialize test runner
    runner = ClinicalWorkflowTestRunner()
    
    try:
        if args.full_suite:
            runner.run_full_test_suite(parallel=parallel, include_slow=args.include_slow)
        
        elif args.category:
            result = runner.run_test_category(args.category, parallel=parallel, verbose=args.verbose)
            exit_code = 0 if result.get("success", False) else 1
            sys.exit(exit_code)
        
        elif args.role:
            result = runner.run_role_based_tests(args.role, parallel=parallel)
            exit_code = 0 if result.get("success", False) else 1
            sys.exit(exit_code)
        
        elif args.compliance:
            result = runner.run_compliance_tests(args.compliance)
            exit_code = 0 if result.get("success", False) else 1
            sys.exit(exit_code)
        
        elif args.security_audit:
            result = runner.run_security_audit()
            exit_code = 0 if result.get("success", False) else 1
            sys.exit(exit_code)
        
        elif args.performance_benchmark:
            result = runner.run_performance_benchmark()
            exit_code = 0 if result.get("success", False) else 1
            sys.exit(exit_code)
        
        else:
            parser.print_help()
            print("\\n❌ No test option specified. Use --help for available options.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\\n\\n⚠️  Test execution interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"\\n\\n❌ Error running tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()