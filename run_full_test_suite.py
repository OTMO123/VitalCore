#!/usr/bin/env python3
"""
Complete Clinical Workflows Test Suite
Comprehensive testing of all new functionality
"""
import subprocess
import sys
import os
import time
from datetime import datetime

def run_test_suite():
    print("=" * 60)
    print("CLINICAL WORKFLOWS - COMPLETE TEST SUITE")
    print("=" * 60)
    print(f"Started: {datetime.now()}")
    print()
    
    # Test categories to run
    test_categories = [
        {
            "name": "Unit Tests",
            "command": ["python", "-m", "pytest", "app/tests/", "-v", "-m", "unit"],
            "description": "Fast isolated component tests"
        },
        {
            "name": "Integration Tests", 
            "command": ["python", "-m", "pytest", "app/tests/", "-v", "-m", "integration"],
            "description": "Database and service integration tests"
        },
        {
            "name": "Security Tests",
            "command": ["python", "-m", "pytest", "app/tests/", "-v", "-m", "security"],
            "description": "Authentication and authorization tests"
        },
        {
            "name": "Clinical Workflows Module Tests",
            "command": ["python", "-m", "pytest", "app/modules/clinical_workflows/tests/", "-v"],
            "description": "Complete clinical workflows functionality"
        },
        {
            "name": "API Endpoint Tests",
            "command": ["python", "-m", "pytest", "app/tests/", "-k", "clinical", "-v"],
            "description": "Clinical workflows API endpoint testing"
        },
        {
            "name": "Performance Tests",
            "command": ["python", "-m", "pytest", "app/tests/", "-v", "-m", "performance"],
            "description": "Load and response time testing"
        },
        {
            "name": "Smoke Tests",
            "command": ["python", "-m", "pytest", "app/tests/smoke/", "-v"],
            "description": "Basic functionality verification"
        }
    ]
    
    results = {}
    
    for category in test_categories:
        print(f"\n{'='*20} {category['name']} {'='*20}")
        print(f"Description: {category['description']}")
        print(f"Command: {' '.join(category['command'])}")
        print("-" * 60)
        
        try:
            start_time = time.time()
            result = subprocess.run(
                category['command'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per test category
            )
            duration = time.time() - start_time
            
            if result.returncode == 0:
                results[category['name']] = "PASS"
                print(f"[SUCCESS] {category['name']} completed in {duration:.1f}s")
                # Show summary of passed tests
                if "collected" in result.stdout:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if "passed" in line and "failed" in line:
                            print(f"Result: {line.strip()}")
                        elif "collected" in line:
                            print(f"Tests: {line.strip()}")
            else:
                results[category['name']] = "FAIL"
                print(f"[FAILED] {category['name']} failed after {duration:.1f}s")
                print("Error output:")
                print(result.stderr[:500])  # Show first 500 chars of error
                
        except subprocess.TimeoutExpired:
            results[category['name']] = "TIMEOUT"
            print(f"[TIMEOUT] {category['name']} exceeded 5 minute limit")
        except FileNotFoundError:
            results[category['name']] = "SKIP"
            print(f"[SKIP] {category['name']} - pytest not found or path issue")
        except Exception as e:
            results[category['name']] = "ERROR"
            print(f"[ERROR] {category['name']} - {str(e)}")
    
    # Final Summary
    print("\n" + "="*60)
    print("TEST SUITE SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result == "PASS")
    total = len(results)
    
    for category, result in results.items():
        status_symbol = {
            "PASS": "[✓]",
            "FAIL": "[✗]", 
            "TIMEOUT": "[T]",
            "SKIP": "[S]",
            "ERROR": "[E]"
        }.get(result, "[?]")
        print(f"{status_symbol} {category:<30} {result}")
    
    print("-" * 60)
    print(f"Total: {passed}/{total} test categories passed")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Clinical Workflows PRODUCTION READY!")
    elif passed >= total * 0.8:
        print("\n✅ MOSTLY SUCCESSFUL - Clinical Workflows ready with minor issues")
    else:
        print("\n⚠️ ISSUES DETECTED - Review failed tests before deployment")
    
    print(f"\nCompleted: {datetime.now()}")
    return results

if __name__ == "__main__":
    run_test_suite()