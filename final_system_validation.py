#!/usr/bin/env python3
"""
🏥 IRIS Healthcare API - Final System Validation
Quick validation script for competition readiness
"""

import requests
import json
import time
from datetime import datetime

def validate_system():
    """Comprehensive system validation for competition readiness."""
    
    print("🏥 IRIS Healthcare API - System Validation")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "summary": {}
    }
    
    # Test 1: Health Check
    print("1️⃣  Testing Health Endpoint...")
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/health", timeout=5)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Health: {health_data.get('status', 'unknown')}")
            print(f"   ⏱️  Response time: {response_time:.0f}ms")
            results["tests"].append({
                "test": "Health Check",
                "status": "PASS",
                "response_time_ms": response_time,
                "data": health_data
            })
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            results["tests"].append({
                "test": "Health Check", 
                "status": "FAIL",
                "error": f"HTTP {response.status_code}"
            })
    except Exception as e:
        print(f"   ❌ Health check error: {str(e)}")
        results["tests"].append({
            "test": "Health Check",
            "status": "ERROR", 
            "error": str(e)
        })
    
    # Test 2: Root API Endpoint
    print("\n2️⃣  Testing Root API Endpoint...")
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/", timeout=5)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            root_data = response.json()
            print(f"   ✅ API Status: {root_data.get('status', 'unknown')}")
            print(f"   🤖 AI Ready: {root_data.get('ai_ready', 'unknown')}")
            print(f"   ⏱️  Response time: {response_time:.0f}ms")
            results["tests"].append({
                "test": "Root API",
                "status": "PASS",
                "response_time_ms": response_time,
                "data": root_data
            })
        else:
            print(f"   ❌ Root API failed: {response.status_code}")
            results["tests"].append({
                "test": "Root API",
                "status": "FAIL", 
                "error": f"HTTP {response.status_code}"
            })
    except Exception as e:
        print(f"   ❌ Root API error: {str(e)}")
        results["tests"].append({
            "test": "Root API",
            "status": "ERROR",
            "error": str(e)
        })
    
    # Test 3: Documentation
    print("\n3️⃣  Testing API Documentation...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("   ✅ API Documentation accessible")
            results["tests"].append({
                "test": "API Documentation",
                "status": "PASS"
            })
        else:
            print(f"   ❌ Documentation failed: {response.status_code}")
            results["tests"].append({
                "test": "API Documentation",
                "status": "FAIL",
                "error": f"HTTP {response.status_code}"
            })
    except Exception as e:
        print(f"   ❌ Documentation error: {str(e)}")
        results["tests"].append({
            "test": "API Documentation", 
            "status": "ERROR",
            "error": str(e)
        })
    
    # Test 4: Demo Documentation 
    print("\n4️⃣  Testing Demo Documentation...")
    try:
        response = requests.get(f"{base_url}/docs-demo", timeout=5)
        if response.status_code == 200:
            print("   ✅ Demo Documentation accessible")
            results["tests"].append({
                "test": "Demo Documentation",
                "status": "PASS"
            })
        else:
            print(f"   ❌ Demo docs failed: {response.status_code}")
            results["tests"].append({
                "test": "Demo Documentation",
                "status": "FAIL",
                "error": f"HTTP {response.status_code}"
            })
    except Exception as e:
        print(f"   ❌ Demo docs error: {str(e)}")
        results["tests"].append({
            "test": "Demo Documentation",
            "status": "ERROR", 
            "error": str(e)
        })
    
    # Calculate results
    passed = len([t for t in results["tests"] if t["status"] == "PASS"])
    failed = len([t for t in results["tests"] if t["status"] in ["FAIL", "ERROR"]])
    total = len(results["tests"])
    success_rate = (passed / total * 100) if total > 0 else 0
    
    results["summary"] = {
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "success_rate": success_rate
    }
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {total}")
    print(f"Passed: ✅ {passed}")
    print(f"Failed: ❌ {failed}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 100:
        print("\n🏆 SYSTEM READY FOR COMPETITION! 🎉")
        print("✅ All systems operational")
        print("✅ Competition submission ready")
    elif success_rate >= 75:
        print("\n⚠️  SYSTEM MOSTLY READY")
        print("✅ Core functionality working")  
        print("⚠️  Minor issues to address")
    else:
        print("\n❌ SYSTEM NEEDS ATTENTION")
        print("❌ Major issues detected")
        print("🔧 Troubleshooting required")
    
    # Save results
    with open("validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to: validation_results.json")
    return results

if __name__ == "__main__":
    validate_system()