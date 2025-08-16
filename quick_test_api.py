#!/usr/bin/env python3
"""
Quick API Test Script - Test critical endpoints for 100% reliability
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

async def test_api_endpoints():
    """Test critical API endpoints"""
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        print("🧪 Testing API Endpoints")
        print("=" * 50)
        
        # Test 1: Health check
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    print("✅ Root Health: OK")
                else:
                    print(f"❌ Root Health: {response.status}")
        except Exception as e:
            print(f"❌ Root Health: Error - {e}")
        
        # Test 2: Authentication
        token = None
        try:
            auth_data = "username=admin&password=admin123"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            
            async with session.post(f"{base_url}/api/v1/auth/login", 
                                  data=auth_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    token = result.get("access_token")
                    print("✅ Authentication: OK")
                else:
                    print(f"❌ Authentication: {response.status}")
        except Exception as e:
            print(f"❌ Authentication: Error - {e}")
        
        if not token:
            print("❌ Cannot continue without authentication")
            return
        
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        # Test 3: Documents Health (fixed endpoint)
        try:
            async with session.get(f"{base_url}/api/v1/documents/health", 
                                 headers=auth_headers) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Documents Health: {result.get('status', 'OK')}")
                else:
                    result = await response.json()
                    print(f"❌ Documents Health: {response.status} - {result}")
        except Exception as e:
            print(f"❌ Documents Health: Error - {e}")
        
        # Test 4: Create Patient (to get valid patient ID)
        patient_id = None
        try:
            patient_data = {
                "resourceType": "Patient",
                "identifier": [{"value": f"TEST-{int(datetime.now().timestamp())}"}],
                "name": [{"family": "TestQuick", "given": ["API"]}],
                "gender": "male",
                "birthDate": "1990-01-01",
                "active": True,
                "organization_id": "550e8400-e29b-41d4-a716-446655440000",
                "consent_status": "pending",
                "consent_types": ["treatment"]
            }
            
            async with session.post(f"{base_url}/api/v1/healthcare/patients",
                                  json=patient_data, headers=auth_headers) as response:
                if response.status == 201:
                    result = await response.json()
                    patient_id = result.get("id")
                    print(f"✅ Create Patient: {patient_id}")
                else:
                    result = await response.json()
                    print(f"❌ Create Patient: {response.status} - {result}")
        except Exception as e:
            print(f"❌ Create Patient: Error - {e}")
        
        # Test 5: Get Patient by ID (fixed endpoint)
        if patient_id:
            try:
                async with session.get(f"{base_url}/api/v1/healthcare/patients/{patient_id}",
                                     headers=auth_headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Get Patient: {result.get('id', 'OK')}")
                    else:
                        result = await response.json()
                        print(f"❌ Get Patient: {response.status} - {result}")
            except Exception as e:
                print(f"❌ Get Patient: Error - {e}")
        
        # Test 6: Update Patient (if we have patient_id)
        if patient_id:
            try:
                update_data = {"gender": "female", "consent_status": "active"}
                async with session.put(f"{base_url}/api/v1/healthcare/patients/{patient_id}",
                                     json=update_data, headers=auth_headers) as response:
                    if response.status == 200:
                        print("✅ Update Patient: OK")
                    else:
                        result = await response.json()
                        print(f"❌ Update Patient: {response.status} - {result}")
            except Exception as e:
                print(f"❌ Update Patient: Error - {e}")
        
        # Test 7: Audit Logs
        try:
            async with session.get(f"{base_url}/api/v1/audit/logs",
                                 headers=auth_headers) as response:
                if response.status == 200:
                    print("✅ Audit Logs: OK")
                else:
                    result = await response.json()
                    print(f"❌ Audit Logs: {response.status} - {result}")
        except Exception as e:
            print(f"❌ Audit Logs: Error - {e}")
        
        # Test 8: Error handling - Non-existent patient
        try:
            fake_id = "00000000-0000-0000-0000-000000000000"
            async with session.get(f"{base_url}/api/v1/healthcare/patients/{fake_id}",
                                 headers=auth_headers) as response:
                if response.status == 404:
                    print("✅ Error Handling: 404 for non-existent patient")
                else:
                    print(f"❌ Error Handling: Expected 404, got {response.status}")
        except Exception as e:
            print(f"❌ Error Handling: Error - {e}")

        print("=" * 50)
        print("🏁 Quick API Test Complete")

if __name__ == "__main__":
    asyncio.run(test_api_endpoints())