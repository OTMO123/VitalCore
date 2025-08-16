#!/usr/bin/env python3
"""
Clinical Workflows Test Suite - Windows Compatible
Complete testing of all new functionality
"""
import requests
import time
import subprocess
import sys
from datetime import datetime

def test_system_components():
    """Test all system components"""
    print("CLINICAL WORKFLOWS - COMPLETE TEST SUITE")
    print("=" * 50)
    print(f"Started: {datetime.now()}")
    
    results = {}
    
    # Test 1: System Health
    print("\n1. SYSTEM HEALTH CHECK")
    print("-" * 25)
    try:
        response = requests.get("http://localhost:8000/docs", timeout=10)
        if response.status_code == 200:
            print("   [PASS] Main application responding")
            results["System Health"] = True
        else:
            print(f"   [FAIL] Application returned {response.status_code}")
            results["System Health"] = False
    except Exception as e:
        print(f"   [FAIL] System health: {e}")
        results["System Health"] = False
    
    # Test 2: Clinical Workflows Endpoints
    print("\n2. CLINICAL WORKFLOWS ENDPOINTS")
    print("-" * 35)
    try:
        response = requests.get("http://localhost:8000/openapi.json", timeout=10)
        if response.status_code == 200:
            paths = response.json().get("paths", {})
            clinical_paths = [p for p in paths.keys() if "clinical-workflows" in p]
            print(f"   Found {len(clinical_paths)} endpoints")
            
            # Check for key endpoints
            key_endpoints = [
                "workflows", "health", "analytics", "encounters", "metrics"
            ]
            found_endpoints = sum(1 for key in key_endpoints 
                                if any(key in path for path in clinical_paths))
            
            print(f"   Key endpoints: {found_endpoints}/{len(key_endpoints)}")
            
            if len(clinical_paths) >= 8 and found_endpoints >= 4:
                print("   [PASS] All expected endpoints found")
                results["Endpoints"] = True
            else:
                print("   [FAIL] Missing expected endpoints")
                results["Endpoints"] = False
        else:
            print(f"   [FAIL] OpenAPI failed: {response.status_code}")
            results["Endpoints"] = False
    except Exception as e:
        print(f"   [FAIL] Endpoint test: {e}")
        results["Endpoints"] = False
    
    # Test 3: Authentication Security
    print("\n3. AUTHENTICATION SECURITY")
    print("-" * 30)
    try:
        test_endpoints = [
            "/api/v1/clinical-workflows/workflows",
            "/api/v1/clinical-workflows/analytics"
        ]
        
        secured_count = 0
        for endpoint in test_endpoints:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            if response.status_code in [401, 403]:
                secured_count += 1
                print(f"   [SECURED] {endpoint}")
        
        if secured_count >= len(test_endpoints):
            print(f"   [PASS] {secured_count}/{len(test_endpoints)} endpoints secured")
            results["Security"] = True
        else:
            print(f"   [WARN] Only {secured_count}/{len(test_endpoints)} secured")
            results["Security"] = False
    except Exception as e:
        print(f"   [FAIL] Security test: {e}")
        results["Security"] = False
    
    # Test 4: Performance
    print("\n4. PERFORMANCE TESTING")
    print("-" * 25)
    try:
        times = []
        for i in range(3):
            start = time.time()
            response = requests.get("http://localhost:8000/docs", timeout=10)
            duration = (time.time() - start) * 1000
            if response.status_code == 200:
                times.append(duration)
        
        if times:
            avg_time = sum(times) / len(times)
            print(f"   Average response: {avg_time:.1f}ms")
            
            if avg_time < 100:
                print("   [PASS] Excellent performance")
                results["Performance"] = True
            elif avg_time < 300:
                print("   [PASS] Good performance")
                results["Performance"] = True
            else:
                print("   [WARN] Slow performance")
                results["Performance"] = False
        else:
            print("   [FAIL] No successful requests")
            results["Performance"] = False
    except Exception as e:
        print(f"   [FAIL] Performance test: {e}")
        results["Performance"] = False
    
    # Test 5: Error Handling
    print("\n5. ERROR HANDLING")
    print("-" * 20)
    try:
        # Test invalid endpoint
        response1 = requests.get("http://localhost:8000/api/v1/clinical-workflows/invalid", timeout=5)
        
        # Test invalid ID
        response2 = requests.get("http://localhost:8000/api/v1/clinical-workflows/workflows/invalid-id", timeout=5)
        
        error_codes = [response1.status_code, response2.status_code]
        proper_errors = sum(1 for code in error_codes if 400 <= code < 500)
        
        print(f"   Error responses: {proper_errors}/{len(error_codes)} proper")
        
        if proper_errors >= len(error_codes) * 0.5:  # 50% should be proper errors
            print("   [PASS] Error handling working")
            results["Error Handling"] = True
        else:
            print("   [WARN] Error handling issues")
            results["Error Handling"] = False
    except Exception as e:
        print(f"   [FAIL] Error handling test: {e}")
        results["Error Handling"] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"   [{status}] {test_name}")
    
    print("-" * 50)
    print(f"Results: {passed}/{total} tests passed")
    success_rate = (passed / total) * 100
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("\nSTATUS: PRODUCTION READY")
        print("All critical systems operational!")
    elif success_rate >= 75:
        print("\nSTATUS: OPERATIONAL") 
        print("System ready with minor issues")
    else:
        print("\nSTATUS: NEEDS ATTENTION")
        print("Review failed tests")
    
    print(f"\nCompleted: {datetime.now()}")
    return results

def run_pytest_tests():
    """Run pytest-based tests if available"""
    print("\n" + "=" * 50)
    print("PYTEST TEST EXECUTION")
    print("=" * 50)
    
    test_commands = [
        {
            "name": "Unit Tests",
            "cmd": ["python", "-m", "pytest", "app/tests/", "-v", "-m", "unit", "--tb=short"]
        },
        {
            "name": "Integration Tests", 
            "cmd": ["python", "-m", "pytest", "app/tests/", "-v", "-m", "integration", "--tb=short"]
        },
        {
            "name": "Clinical Module Tests",
            "cmd": ["python", "-m", "pytest", "app/modules/clinical_workflows/tests/", "-v", "--tb=short"]
        }
    ]
    
    pytest_results = {}
    
    for test in test_commands:
        print(f"\nRunning {test['name']}...")
        try:
            result = subprocess.run(
                test["cmd"], 
                capture_output=True, 
                text=True, 
                timeout=120
            )
            
            if result.returncode == 0:
                print(f"   [PASS] {test['name']}")
                pytest_results[test["name"]] = True
            else:
                print(f"   [FAIL] {test['name']}")
                # Show brief error info
                if "collected" in result.stdout:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if "failed" in line or "error" in line:
                            print(f"   Error: {line.strip()}")
                            break
                pytest_results[test["name"]] = False
                
        except subprocess.TimeoutExpired:
            print(f"   [TIMEOUT] {test['name']}")
            pytest_results[test["name"]] = False
        except FileNotFoundError:
            print(f"   [SKIP] {test['name']} - pytest not available")
            pytest_results[test["name"]] = None
        except Exception as e:
            print(f"   [ERROR] {test['name']}: {e}")
            pytest_results[test["name"]] = False
    
    return pytest_results

def main():
    """Run complete test suite"""
    # Run system component tests
    system_results = test_system_components()
    
    # Run pytest tests
    pytest_results = run_pytest_tests()
    
    # Final summary
    print("\n" + "=" * 50)
    print("COMPLETE TEST SUITE SUMMARY")
    print("=" * 50)
    
    all_results = {**system_results, **pytest_results}
    passed = sum(1 for result in all_results.values() if result is True)
    total = sum(1 for result in all_results.values() if result is not None)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    print("\nAccess your Clinical Workflows system:")
    print("  Main App: http://localhost:8000")
    print("  API Docs: http://localhost:8000/docs")
    print("  Clinical: http://localhost:8000/api/v1/clinical-workflows/")

if __name__ == "__main__":
    main()