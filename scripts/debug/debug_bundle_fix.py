#!/usr/bin/env python3
"""
Debug FHIR Bundle 400 Error Fix
SOC2/HIPAA Enterprise Healthcare Compliance Testing
"""

import asyncio
import json
from httpx import AsyncClient, ASGITransport
import sys
import os

# Add project root to path
sys.path.insert(0, '/mnt/c/Users/aurik/Code_Projects/2_scraper')

from app.main import app
from app.core.database_unified import async_session_factory
from app.tests.helpers.auth_helpers import create_test_user, get_auth_headers
from app.modules.healthcare_records.schemas import FHIRBundleRequest

async def debug_bundle_400_error():
    """Debug the FHIR bundle 400 error in enterprise compliance tests."""
    
    print("🔧 ENTERPRISE HEALTHCARE BUNDLE DEBUG")
    print("SOC2 Type II + HIPAA + FHIR R4 Compliance Testing")
    print("=" * 60)
    
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with async_session_factory() as db_session:
            try:
                # Create test user with proper role
                print("\n1️⃣ Creating test user...")
                
                test_user = await create_test_user(
                    db_session=db_session,
                    username="debug_bundle_user",
                    role="physician",  # Try physician role instead of system_admin
                    email="debug.bundle@example.com",
                    password="DebugSecure123!"
                )
                print(f"✅ User created: {test_user.username}, Role: {test_user.role}")
                
                # Get authentication headers  
                print("\n2️⃣ Getting authentication headers...")
                auth_headers = await get_auth_headers(
                    async_client=client,
                    username="debug_bundle_user", 
                    password="DebugSecure123!"
                )
                print("✅ Authentication successful")
                
                # Test simple FHIR validation first
                print("\n3️⃣ Testing FHIR validation endpoint...")
                patient_resource = {
                    "resourceType": "Patient",
                    "id": "patient-debug-001", 
                    "active": True,
                    "name": [{
                        "use": "official",
                        "family": "Debug",
                        "given": ["Test"]
                    }],
                    "gender": "unknown",
                    "birthDate": "1990-01-01"
                }
                
                validation_request = {
                    "resource_type": "Patient",
                    "resource_data": patient_resource,
                    "strict_validation": True
                }
                
                validation_response = await client.post(
                    "/api/v1/healthcare/fhir/validate",
                    json=validation_request,
                    headers=auth_headers
                )
                
                print(f"Validation Status: {validation_response.status_code}")
                if validation_response.status_code != 200:
                    print(f"Validation Error: {validation_response.text}")
                    return
                else:
                    print("✅ FHIR validation successful")
                
                # Test bundle endpoint with correct structure
                print("\n4️⃣ Testing FHIR bundle transaction...")
                
                # Create proper transaction bundle structure
                transaction_bundle = {
                    "resourceType": "Bundle",
                    "id": "debug-transaction-001",
                    "type": "transaction", 
                    "entry": [{
                        "fullUrl": "urn:uuid:patient-debug-001",
                        "resource": {
                            "resourceType": "Patient",
                            "id": "patient-debug-001",
                            "active": True,
                            "name": [{
                                "use": "official", 
                                "family": "Debug",
                                "given": ["Transaction"]
                            }],
                            "gender": "unknown",
                            "birthDate": "1990-01-01"
                        },
                        "request": {
                            "method": "POST",
                            "url": "Patient"
                        }
                    }]
                }
                
                # Create proper bundle request  
                bundle_request_data = {
                    "bundle_type": "transaction",
                    "bundle_data": transaction_bundle,
                    "validate_resources": True,
                    "process_atomically": True
                }
                
                print("Bundle Request Structure:")
                print(json.dumps(bundle_request_data, indent=2))
                
                bundle_response = await client.post(
                    "/api/v1/healthcare/fhir/bundle", 
                    json=bundle_request_data,
                    headers=auth_headers
                )
                
                print(f"\n📊 Bundle Response Status: {bundle_response.status_code}")
                
                if bundle_response.status_code == 200 or bundle_response.status_code == 201:
                    print("✅ FHIR Bundle transaction successful!")
                    result = bundle_response.json()
                    print(f"Bundle ID: {result.get('bundle_id')}")
                    print(f"Status: {result.get('status')}")
                    print(f"Processed Resources: {result.get('processed_resources', 0)}")
                else:
                    print(f"❌ Bundle Error {bundle_response.status_code}")
                    print("Response Body:")
                    print(bundle_response.text)
                    
                    # Try to parse error details
                    try:
                        error_data = bundle_response.json()
                        print("\nParsed Error Details:")
                        print(json.dumps(error_data, indent=2))
                    except:
                        pass
                        
            except Exception as e:
                print(f"❌ Debug Error: {str(e)}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    print("Starting FHIR Bundle 400 Error Debug...")
    asyncio.run(debug_bundle_400_error())