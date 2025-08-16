#!/usr/bin/env python3
"""
Simple Test Runner for Clinical Workflows
Fixes Windows encoding issues and provides clean test execution.
"""

import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path

def run_tests_simple():
    """Run tests with Windows-compatible output."""
    
    print("Clinical Workflows Test Suite")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print(f"Working directory: {project_root}")
    
    # Test commands in order of priority
    test_commands = [
        {
            "name": "Fast Unit Tests",
            "cmd": ["python", "-m", "pytest", "app/modules/clinical_workflows/tests/unit/", "-v", "-x"],
            "description": "Quick validation of core components"
        },
        {
            "name": "Integration Tests", 
            "cmd": ["python", "-m", "pytest", "app/modules/clinical_workflows/tests/integration/", "-v", "-x"],
            "description": "API endpoint validation"
        },
        {
            "name": "Security Tests",
            "cmd": ["python", "-m", "pytest", "app/modules/clinical_workflows/tests/security/", "-v", "-x"],
            "description": "PHI protection and compliance"
        }
    ]
    
    results = []
    
    for test in test_commands:
        print(f"\n{'-' * 60}")
        print(f"Running: {test['name']}")
        print(f"Description: {test['description']}")
        print(f"Command: {' '.join(test['cmd'])}")
        print(f"{'-' * 60}")
        
        start_time = time.time()
        
        try:
            # Run test with proper encoding
            result = subprocess.run(
                test['cmd'], 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                errors='replace',  # Replace problematic characters
                timeout=300
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            success = result.returncode == 0
            
            # Clean output for Windows
            stdout_clean = result.stdout.replace('✅', '[PASS]').replace('❌', '[FAIL]').replace('⚠️', '[WARN]')
            stderr_clean = result.stderr.replace('✅', '[PASS]').replace('❌', '[FAIL]').replace('⚠️', '[WARN]')
            
            print(f"Result: {'PASSED' if success else 'FAILED'}")
            print(f"Duration: {duration:.2f} seconds")
            print(f"Return code: {result.returncode}")
            
            if stdout_clean:
                print(f"\nOutput:")
                # Show last 1000 characters to avoid overwhelming output
                print(stdout_clean[-1000:] if len(stdout_clean) > 1000 else stdout_clean)
            
            if stderr_clean and not success:
                print(f"\nErrors:")
                print(stderr_clean[-500:] if len(stderr_clean) > 500 else stderr_clean)
            
            results.append({
                "name": test['name'],
                "success": success,
                "duration": duration,
                "return_code": result.returncode
            })
            
            # Stop on first failure for quick feedback
            if not success:
                print(f"\n[STOP] {test['name']} failed - stopping execution for quick feedback")
                break
                
        except subprocess.TimeoutExpired:
            print(f"[TIMEOUT] {test['name']} timed out after 300 seconds")
            results.append({
                "name": test['name'], 
                "success": False,
                "duration": 300,
                "error": "Timeout"
            })
            break
            
        except Exception as e:
            print(f"[ERROR] Failed to run {test['name']}: {e}")
            results.append({
                "name": test['name'],
                "success": False,
                "duration": 0,
                "error": str(e)
            })
            break
    
    # Summary
    print(f"\n{'=' * 60}")
    print("TEST EXECUTION SUMMARY")
    print(f"{'=' * 60}")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.get("success", False))
    total_duration = sum(r.get("duration", 0) for r in results)
    
    print(f"Total test categories: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
    print(f"Total duration: {total_duration:.2f} seconds")
    
    print(f"\nDetailed Results:")
    for result in results:
        status = "[PASS]" if result.get("success", False) else "[FAIL]"
        name = result.get("name", "Unknown")
        duration = result.get("duration", 0)
        print(f"  {status} {name:<20} ({duration:.2f}s)")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Return appropriate exit code
    all_passed = all(r.get("success", False) for r in results)
    
    if all_passed:
        print(f"\n[SUCCESS] All tests passed!")
        return 0
    else:
        print(f"\n[FAILURE] Some tests failed.")
        return 1

if __name__ == "__main__":
    exit_code = run_tests_simple()
    sys.exit(exit_code)