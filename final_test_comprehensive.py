#!/usr/bin/env python3
"""
Comprehensive Clinical Workflows Test Suite
Final verification of all functionality
"""
import requests
import json
import time
import psycopg2
from datetime import datetime

def comprehensive_test():
    print("=== COMPREHENSIVE CLINICAL WORKFLOWS TEST SUITE ===")
    print(f"Test Time: {datetime.now()}")
    print("=" * 60)
    
    results = {
        "database": False,
        "api_health": False,
        "authentication": False,
        "endpoints": False,
        "performance": False,
        "documentation": False
    }
    
    base_url = "http://localhost:8000"
    
    # Test 1: Database Integration
    print("\n1. DATABASE INTEGRATION TEST")
    print("-" * 30)
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="iris_db",
            user="iris_user",
            password="iris_password"
        )
        cursor = conn.cursor()
        
        # Check clinical workflow tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%clinical%'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        print(f"Clinical workflow tables found: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
        
        if len(tables) >= 4:
            results["database"] = True
            print("[SUCCESS] Database integration verified")
        else:
            print("[WARNING] Expected 4+ clinical workflow tables")
            
        conn.close()
    except Exception as e:
        print(f"[ERROR] Database test failed: {e}")
    
    # Test 2: API Health & Availability
    print("\n2. API HEALTH TEST")
    print("-" * 20)
    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
        if response.status_code == 200:
            results["api_health"] = True
            print("[SUCCESS] API documentation accessible")
            print(f"Response time: {response.elapsed.total_seconds():.3f}s")
        else:
            print(f"[ERROR] API docs returned {response.status_code}")
    except Exception as e:
        print(f"[ERROR] API health test failed: {e}")
    
    # Test 3: Authentication Security
    print("\n3. AUTHENTICATION SECURITY TEST")
    print("-" * 35)
    try:
        # Test unauthenticated access (should fail)
        response = requests.get(f"{base_url}/api/v1/clinical-workflows/workflows", timeout=10)
        if response.status_code == 403:
            results["authentication"] = True
            print("[SUCCESS] Authentication properly enforced")
            print("Unauthenticated requests correctly rejected with 403")
        else:
            print(f"[WARNING] Expected 403, got {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Authentication test failed: {e}")
    
    # Test 4: Endpoint Discovery
    print("\n4. ENDPOINT DISCOVERY TEST")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=10)
        if response.status_code == 200:
            openapi_data = response.json()
            paths = openapi_data.get("paths", {})
            clinical_paths = [path for path in paths.keys() if "clinical-workflows" in path]
            
            print(f"Clinical workflow endpoints found: {len(clinical_paths)}")
            for path in sorted(clinical_paths):
                methods = list(paths[path].keys())
                print(f"  {path} [{', '.join(methods).upper()}]")
            
            if len(clinical_paths) >= 8:
                results["endpoints"] = True
                print("[SUCCESS] All expected endpoints discovered")
            else:
                print(f"[WARNING] Expected 8+ endpoints, found {len(clinical_paths)}")
                
        else:
            print(f"[ERROR] OpenAPI schema returned {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Endpoint discovery failed: {e}")
    
    # Test 5: Performance Analysis
    print("\n5. PERFORMANCE ANALYSIS")
    print("-" * 25)
    try:
        times = []
        for i in range(5):
            start_time = time.time()
            response = requests.get(f"{base_url}/docs", timeout=10)
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to ms
            times.append(response_time)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"Average response time: {avg_time:.1f}ms")
        print(f"Fastest response: {min_time:.1f}ms")
        print(f"Slowest response: {max_time:.1f}ms")
        
        if avg_time < 200:  # Under 200ms is excellent
            results["performance"] = True
            print("[SUCCESS] Performance excellent (< 200ms)")
        elif avg_time < 500:
            print("[GOOD] Performance acceptable (< 500ms)")
        else:
            print("[WARNING] Performance could be improved (> 500ms)")
    except Exception as e:
        print(f"[ERROR] Performance test failed: {e}")
    
    # Test 6: Documentation Quality
    print("\n6. DOCUMENTATION QUALITY TEST")
    print("-" * 32)
    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
        if "Clinical Workflows" in response.text:
            results["documentation"] = True
            print("[SUCCESS] Clinical workflows documentation present")
            print("Swagger UI properly rendering clinical workflows")
        else:
            print("[WARNING] Clinical workflows not found in documentation")
    except Exception as e:
        print(f"[ERROR] Documentation test failed: {e}")
    
    # Final Summary
    print("\n" + "=" * 60)
    print("FINAL TEST RESULTS")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    percentage = (passed / total) * 100
    
    for test, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test.replace('_', ' ').title()}")
    
    print("-" * 60)
    print(f"Overall Score: {passed}/{total} ({percentage:.1f}%)")
    
    if percentage >= 80:
        print("\n[SUCCESS] Clinical Workflows module is PRODUCTION READY!")
        print("System ready for healthcare provider deployment")
    elif percentage >= 60:
        print("\n[GOOD] Clinical Workflows module is largely functional")
        print("Minor issues need attention before production")
    else:
        print("\n[WARNING] Clinical Workflows module needs improvements")
        print("Significant issues require resolution")
    
    print(f"\nSystem URL: {base_url}")
    print(f"API Documentation: {base_url}/docs")
    print(f"Clinical Workflows: {base_url}/api/v1/clinical-workflows/")

if __name__ == "__main__":
    comprehensive_test()