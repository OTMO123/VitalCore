#!/usr/bin/env python3
"""
Simple Endpoint Test Script - Copy to PowerShell
"""

import requests
import json

def test_all_endpoints():
    base_url = "http://localhost:8003"
    api_base = f"{base_url}/api/v1"
    
    print("🎯 TESTING ALL 5 ENDPOINTS")
    print("=" * 40)
    
    # Step 1: Authenticate
    print("🔐 Step 1: Authenticating...")
    auth_data = {"username": "admin@example.com", "password": "admin123"}
    try:
        auth_response = requests.post(f"{api_base}/auth/login", data=auth_data)
        if auth_response.status_code != 200:
            print(f"❌ Auth failed: {auth_response.status_code}")
            print(f"Response: {auth_response.text}")
            return
        
        token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        print("✅ Authentication successful")
    except Exception as e:
        print(f"❌ Auth error: {e}")
        return
    
    patient_id = "f791266f-feed-4953-83e8-07db9fc60df7"
    success_count = 0
    total_endpoints = 5
    
    # Test 1: Risk Calculation
    print("\n🔥 Test 1: Risk Calculation...")
    try:
        risk_data = {
            "patient_id": patient_id,
            "include_recommendations": True,
            "include_readmission_risk": False,
            "time_horizon": "30_days",
            "requesting_user_id": "admin@example.com",
            "access_purpose": "clinical_care"
        }
        
        response = requests.post(f"{api_base}/patients/risk/calculate", json=risk_data, headers=headers)
        if response.status_code == 200:
            print("✅ Risk calculation: SUCCESS")
            success_count += 1
        else:
            print(f"❌ Risk calculation: FAILED ({response.status_code})")
            print(f"   Error: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Risk calculation: ERROR - {e}")
    
    # Test 2: Risk Factors
    print("\n🔥 Test 2: Risk Factors...")
    try:
        response = requests.get(f"{api_base}/patients/risk/factors/{patient_id}", headers=headers)
        if response.status_code == 200:
            print("✅ Risk factors: SUCCESS")
            success_count += 1
        else:
            print(f"❌ Risk factors: FAILED ({response.status_code})")
            print(f"   Error: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Risk factors: ERROR - {e}")
    
    # Test 3: Clinical Documents
    print("\n🔥 Test 3: Clinical Documents...")
    try:
        document_data = {
            "title": "Test Clinical Document",
            "document_type": "progress_note",
            "content": "Test clinical content for diagnostic purposes",
            "content_type": "text/plain",
            "patient_id": patient_id,
            "access_level": "restricted",
            "authorized_roles": ["admin"]
        }
        
        response = requests.post(f"{api_base}/healthcare/documents", json=document_data, headers=headers)
        if response.status_code in [200, 201]:
            print("✅ Clinical documents: SUCCESS")
            success_count += 1
        else:
            print(f"❌ Clinical documents: FAILED ({response.status_code})")
            print(f"   Error: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Clinical documents: ERROR - {e}")
    
    # Test 4: Readmission Risk
    print("\n🔥 Test 4: Readmission Risk...")
    try:
        response = requests.get(f"{api_base}/patients/risk/readmission/{patient_id}?time_frame=30_days", headers=headers)
        if response.status_code == 200:
            print("✅ Readmission risk: SUCCESS")
            success_count += 1
        else:
            print(f"❌ Readmission risk: FAILED ({response.status_code})")
            print(f"   Error: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Readmission risk: ERROR - {e}")
    
    # Test 5: Population Analytics
    print("\n🔥 Test 5: Population Analytics...")
    try:
        metrics_data = {
            "cohort_criteria": {"age_range": [18, 65]},
            "metrics_requested": ["risk_distribution"],
            "time_range_days": 90,
            "requesting_user_id": "admin@example.com"
        }
        
        response = requests.post(f"{api_base}/analytics/population/metrics", json=metrics_data, headers=headers)
        if response.status_code == 200:
            print("✅ Population analytics: SUCCESS")
            success_count += 1
        else:
            print(f"❌ Population analytics: FAILED ({response.status_code})")
            print(f"   Error: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Population analytics: ERROR - {e}")
    
    # Final Results
    success_rate = (success_count / total_endpoints) * 100
    print(f"\n{'='*40}")
    print(f"🎯 FINAL RESULTS:")
    print(f"✅ Successful: {success_count}/{total_endpoints}")
    print(f"📊 Success rate: {success_rate:.0f}%")
    
    if success_rate == 100:
        print("🎉🎉🎉 TARGET ACHIEVED: 100% SUCCESS! 🎉🎉🎉")
    elif success_rate >= 80:
        print(f"🎯 GREAT PROGRESS: {success_rate:.0f}% success!")
    else:
        print(f"⚠️ More work needed: {total_endpoints - success_count} endpoints still failing")

if __name__ == "__main__":
    test_all_endpoints()