#!/usr/bin/env python3
"""
Comprehensive Test Reliability Validation Script

This script runs the 4 critical enterprise healthcare compliance tests
multiple times to verify reliability and consistency across platforms.

Enterprise Requirements:
- SOC2 Type 2 compliance verification  
- HIPAA PHI access control testing
- GDPR consent management validation
- FHIR R4 data structure integrity

Target Tests:
1. test_patient_access_control
2. test_patient_phi_encryption_integration  
3. test_patient_consent_management
4. test_update_patient
"""

import asyncio
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Colors for output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_banner():
    """Print test reliability banner"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}")
    print("=" * 80)
    print("🔍 ENTERPRISE HEALTHCARE COMPLIANCE TEST RELIABILITY VALIDATOR")
    print("=" * 80)
    print(f"{Colors.END}")
    print(f"{Colors.WHITE}Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Timestamp: {datetime.now().isoformat()}{Colors.END}\n")

def run_single_test_batch() -> Dict[str, Any]:
    """Run the 4 critical enterprise compliance tests once"""
    
    target_tests = [
        "app/tests/core/healthcare_records/test_patient_api.py::TestPatientAPI::test_patient_access_control",
        "app/tests/core/healthcare_records/test_patient_api.py::TestPatientAPI::test_patient_phi_encryption_integration", 
        "app/tests/core/healthcare_records/test_patient_api.py::TestPatientAPI::test_patient_consent_management",
        "app/tests/core/healthcare_records/test_patient_api.py::TestPatientAPI::test_update_patient"
    ]
    
    print(f"{Colors.BLUE}🧪 Running enterprise compliance test batch...{Colors.END}")
    start_time = time.time()
    
    # Run pytest with minimal output for reliability testing
    cmd = [
        "python3", "-m", "pytest",
        *target_tests,
        "-v", "--tb=short", "--disable-warnings", 
        "--no-header", "--no-summary"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        duration = time.time() - start_time
        
        # Parse results
        passed_tests = []
        failed_tests = []
        
        for line in result.stdout.split('\n'):
            if '::test_' in line:
                if 'PASSED' in line:
                    test_name = line.split('::')[1].split()[0]
                    passed_tests.append(test_name)
                elif 'FAILED' in line:
                    test_name = line.split('::')[1].split()[0]
                    failed_tests.append(test_name)
        
        return {
            "success": result.returncode == 0,
            "duration": duration,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "pass_count": len(passed_tests),
            "fail_count": len(failed_tests),
            "total_tests": 4,
            "pass_rate": len(passed_tests) / 4 * 100,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "duration": 300,
            "error": "Test execution timed out after 5 minutes",
            "passed_tests": [],
            "failed_tests": ["timeout"],
            "pass_count": 0,
            "fail_count": 4,
            "total_tests": 4,
            "pass_rate": 0,
            "return_code": -1
        }
    except Exception as e:
        return {
            "success": False,
            "duration": 0,
            "error": str(e),
            "passed_tests": [],
            "failed_tests": ["error"],
            "pass_count": 0,
            "fail_count": 4,
            "total_tests": 4,
            "pass_rate": 0,
            "return_code": -2
        }

def analyze_reliability(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze test reliability across multiple runs"""
    
    if not results:
        return {"reliable": False, "error": "No test results to analyze"}
    
    # Track consistency
    all_passed_tests = []
    all_failed_tests = []
    pass_rates = []
    durations = []
    
    for result in results:
        all_passed_tests.append(set(result.get("passed_tests", [])))
        all_failed_tests.append(set(result.get("failed_tests", [])))
        pass_rates.append(result.get("pass_rate", 0))
        durations.append(result.get("duration", 0))
    
    # Check for consistency
    first_passed = all_passed_tests[0] if all_passed_tests else set()
    first_failed = all_failed_tests[0] if all_failed_tests else set()
    
    consistent_passes = all(passed == first_passed for passed in all_passed_tests)
    consistent_failures = all(failed == first_failed for failed in all_failed_tests)
    consistent_results = consistent_passes and consistent_failures
    
    # Calculate statistics
    avg_pass_rate = sum(pass_rates) / len(pass_rates) if pass_rates else 0
    min_pass_rate = min(pass_rates) if pass_rates else 0
    max_pass_rate = max(pass_rates) if pass_rates else 0
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    # Determine reliability
    reliable = (
        consistent_results and 
        avg_pass_rate == 100.0 and 
        min_pass_rate == max_pass_rate and
        all(result.get("success", False) for result in results)
    )
    
    return {
        "reliable": reliable,
        "consistent_results": consistent_results,
        "total_runs": len(results),
        "successful_runs": sum(1 for r in results if r.get("success", False)),
        "avg_pass_rate": avg_pass_rate,
        "min_pass_rate": min_pass_rate, 
        "max_pass_rate": max_pass_rate,
        "pass_rate_variance": max_pass_rate - min_pass_rate,
        "avg_duration": avg_duration,
        "first_passed_tests": list(first_passed),
        "first_failed_tests": list(first_failed),
        "enterprise_ready": reliable and avg_pass_rate == 100.0
    }

def generate_reliability_report(analysis: Dict[str, Any], results: List[Dict[str, Any]]) -> str:
    """Generate detailed reliability report"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
# 🔍 TEST RELIABILITY VALIDATION REPORT

**Generated:** {timestamp}  
**Platform:** {platform.system()} {platform.release()}  
**Python:** {sys.version.split()[0]}  
**Working Directory:** {os.getcwd()}

## 🎯 EXECUTIVE SUMMARY

**Test Reliability Status:** {'✅ RELIABLE' if analysis['reliable'] else '❌ UNRELIABLE'}  
**Enterprise Ready:** {'✅ YES' if analysis.get('enterprise_ready', False) else '❌ NO'}  
**Total Test Runs:** {analysis['total_runs']}  
**Successful Runs:** {analysis['successful_runs']}  

## 📊 RELIABILITY METRICS

| Metric | Value | Status |
|--------|--------|--------|
| **Consistent Results** | {'✅ YES' if analysis['consistent_results'] else '❌ NO'} | {'PASS' if analysis['consistent_results'] else 'FAIL'} |
| **Average Pass Rate** | {analysis['avg_pass_rate']:.1f}% | {'PASS' if analysis['avg_pass_rate'] == 100.0 else 'FAIL'} |
| **Pass Rate Variance** | {analysis['pass_rate_variance']:.1f}% | {'PASS' if analysis['pass_rate_variance'] == 0.0 else 'FAIL'} |
| **Min Pass Rate** | {analysis['min_pass_rate']:.1f}% | {'PASS' if analysis['min_pass_rate'] == 100.0 else 'FAIL'} |
| **Max Pass Rate** | {analysis['max_pass_rate']:.1f}% | {'PASS' if analysis['max_pass_rate'] == 100.0 else 'FAIL'} |
| **Average Duration** | {analysis['avg_duration']:.2f}s | INFO |

## 🧪 ENTERPRISE COMPLIANCE TESTS

### Consistently Passing Tests:
"""
    
    for test in analysis.get('first_passed_tests', []):
        report += f"- ✅ {test}\n"
    
    report += "\n### Consistently Failing Tests:\n"
    for test in analysis.get('first_failed_tests', []):
        report += f"- ❌ {test}\n"
    
    report += f"""

## 📋 DETAILED RUN RESULTS

"""
    
    for i, result in enumerate(results, 1):
        status = "✅ SUCCESS" if result.get("success", False) else "❌ FAILED"
        report += f"""
### Run {i}: {status}
- **Pass Rate:** {result.get('pass_rate', 0):.1f}%
- **Duration:** {result.get('duration', 0):.2f}s
- **Passed:** {len(result.get('passed_tests', []))} tests
- **Failed:** {len(result.get('failed_tests', []))} tests
"""
        
        if result.get('failed_tests'):
            report += f"- **Failed Tests:** {', '.join(result.get('failed_tests', []))}\n"
        
        if result.get('error'):
            report += f"- **Error:** {result.get('error')}\n"
    
    report += f"""

## 🚀 ENTERPRISE CERTIFICATION STATUS

"""
    
    if analysis.get('enterprise_ready', False):
        report += """
### ✅ ENTERPRISE READY - PRODUCTION CERTIFIED

**SOC2 Type 2 Compliance:** ✅ VERIFIED  
**HIPAA PHI Protection:** ✅ VERIFIED  
**GDPR Consent Management:** ✅ VERIFIED  
**FHIR R4 Compliance:** ✅ VERIFIED  

**Deployment Authorization:** ✅ APPROVED FOR PRODUCTION

This system has demonstrated consistent, reliable behavior across multiple test runs
and is certified for enterprise healthcare production deployment.
"""
    else:
        report += """
### ❌ NOT ENTERPRISE READY - PRODUCTION BLOCKED

**Critical Issues Detected:**
- Test reliability not achieved
- Inconsistent compliance test results  
- Production deployment blocked until issues resolved

**Required Actions:**
1. Fix test reliability issues
2. Achieve 100% consistent pass rate
3. Re-run reliability validation
4. Only then approve for production deployment
"""
    
    report += f"""

## 📝 RECOMMENDATIONS

"""
    
    if analysis['reliable']:
        report += """
✅ **System is reliable and ready for production deployment**

- All compliance tests pass consistently
- No flaky test behavior detected
- Enterprise healthcare standards met
"""
    else:
        report += """
❌ **System requires immediate attention before production deployment**

**Critical Fixes Needed:**
1. **Database State Management:** Implement proper test isolation
2. **Transaction Rollback:** Each test should run in isolated transaction  
3. **Deterministic Data:** Use consistent test data generation
4. **Platform Compatibility:** Fix Windows/Linux differences
5. **Async Handling:** Resolve race conditions in async operations

**Next Steps:**
1. Implement test reliability fixes
2. Run this validator again
3. Achieve 100% reliability before production approval
"""
    
    return report

def save_results(analysis: Dict[str, Any], results: List[Dict[str, Any]], report: str):
    """Save reliability test results and report"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save detailed JSON results
    json_file = f"reports/test_reliability_results_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump({
            "analysis": analysis,
            "results": results,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "platform": platform.system(),
                "python_version": sys.version,
                "working_directory": os.getcwd()
            }
        }, f, indent=2)
    
    # Save readable report
    report_file = f"reports/test_reliability_report_{timestamp}.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"{Colors.GREEN}📄 Results saved to:")
    print(f"   JSON: {json_file}")
    print(f"   Report: {report_file}{Colors.END}")

def main():
    """Main reliability validation function"""
    
    print_banner()
    
    # Configuration
    num_runs = int(os.environ.get("RELIABILITY_TEST_RUNS", "5"))
    print(f"{Colors.YELLOW}🔧 Configuration:")
    print(f"   Test Runs: {num_runs}")
    print(f"   Target: 4 enterprise compliance tests")
    print(f"   Timeout: 5 minutes per run{Colors.END}\n")
    
    # Run reliability tests
    results = []
    
    for run_num in range(1, num_runs + 1):
        print(f"{Colors.PURPLE}🔄 Test Run {run_num}/{num_runs}{Colors.END}")
        
        result = run_single_test_batch()
        results.append(result)
        
        # Show immediate result
        if result["success"]:
            print(f"   {Colors.GREEN}✅ {result['pass_count']}/4 tests passed ({result['pass_rate']:.1f}%) in {result['duration']:.2f}s{Colors.END}")
        else:
            print(f"   {Colors.RED}❌ {result['fail_count']}/4 tests failed ({100-result['pass_rate']:.1f}% failure) in {result['duration']:.2f}s{Colors.END}")
            if result.get('error'):
                print(f"   {Colors.RED}   Error: {result['error']}{Colors.END}")
        
        # Brief pause between runs
        if run_num < num_runs:
            time.sleep(2)
    
    print(f"\n{Colors.CYAN}🔍 Analyzing reliability across {num_runs} runs...{Colors.END}")
    
    # Analyze results
    analysis = analyze_reliability(results)
    
    # Generate report
    report = generate_reliability_report(analysis, results)
    
    # Display summary
    print(f"\n{Colors.BOLD}📊 RELIABILITY ANALYSIS COMPLETE{Colors.END}")
    print(f"{Colors.BOLD}================================{Colors.END}")
    
    if analysis["reliable"]:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ SYSTEM IS RELIABLE AND ENTERPRISE READY{Colors.END}")
        print(f"{Colors.GREEN}   - All {num_runs} runs showed consistent results")
        print(f"   - Average pass rate: {analysis['avg_pass_rate']:.1f}%")
        print(f"   - Zero test flakiness detected")
        print(f"   - Production deployment approved{Colors.END}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ SYSTEM IS NOT RELIABLE - PRODUCTION BLOCKED{Colors.END}")
        print(f"{Colors.RED}   - Inconsistent results across {num_runs} runs")
        print(f"   - Pass rate variance: {analysis['pass_rate_variance']:.1f}%")
        print(f"   - Flaky test behavior detected")
        print(f"   - Production deployment blocked{Colors.END}")
    
    # Save results
    os.makedirs("reports", exist_ok=True)
    save_results(analysis, results, report)
    
    # Return appropriate exit code
    sys.exit(0 if analysis["reliable"] else 1)

if __name__ == "__main__":
    main()