#!/usr/bin/env python3
"""
Simple IRIS API System Validation
Tests basic server functionality without Unicode issues
"""

import requests
import json
import sys

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get("http://localhost:8003/health", timeout=5)
        print(f"Health endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"Health response: {response.json()}")
            return True
    except Exception as e:
        print(f"Health endpoint failed: {e}")
    return False

def test_root():
    """Test the root endpoint"""
    try:
        response = requests.get("http://localhost:8003/", timeout=5)
        print(f"Root endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"Root response: {response.json()}")
            return True
    except Exception as e:
        print(f"Root endpoint failed: {e}")
    return False

def test_docs():
    """Test the documentation endpoint"""
    try:
        response = requests.get("http://localhost:8003/docs", timeout=5)
        print(f"Docs endpoint: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Docs endpoint failed: {e}")
    return False

def main():
    print("IRIS Healthcare API - Simple Validation")
    print("=" * 50)
    
    tests = [
        ("Health Endpoint", test_health),
        ("Root API Endpoint", test_root),
        ("API Documentation", test_docs)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\nTesting {name}...")
        if test_func():
            print(f"✓ {name}: PASSED")
            passed += 1
        else:
            print(f"✗ {name}: FAILED")
    
    print("\n" + "=" * 50)
    print(f"VALIDATION SUMMARY")
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n✓ SYSTEM READY FOR TESTING!")
        return 0
    else:
        print(f"\n✗ System has issues - {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())