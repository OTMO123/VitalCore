#!/usr/bin/env python3
"""
Complete Patient API Integration Test - Final Validation
This demonstrates all Patient API operations working correctly.
"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

async def run_patient_api_validation():
    """Complete Patient API validation suite."""
    print("PATIENT API INTEGRATION TEST SUITE")
    print("=" * 50)
    
    try:
        import httpx
        from app.main import app
        from app.core.security import create_access_token, get_password_hash
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from sqlalchemy import text
        import uuid
        from datetime import datetime
        
        # Setup database and create admin user
        print("1. Setting up test environment...")
        database_url = "postgresql+asyncpg://test_user:test_password@localhost:5433/test_iris_db"
        engine = create_async_engine(database_url, echo=False)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        
        # Create admin user with raw SQL (use unique credentials)
        admin_id = uuid.uuid4()
        unique_id = str(uuid.uuid4())[:8]
        unique_email = f"admin_{unique_id}@test.com"
        unique_username = f"admin_{unique_id}"
        async with session_factory() as session:
            insert_sql = text("""
                INSERT INTO users (id, email, email_verified, username, password_hash, 
                                 role, is_active, mfa_enabled, failed_login_attempts, 
                                 must_change_password, is_system_user, created_at, updated_at, password_changed_at)
                VALUES (:id, :email, :email_verified, :username, :password_hash, 
                        :role, :is_active, :mfa_enabled, :failed_login_attempts,
                        :must_change_password, :is_system_user, :created_at, :updated_at, :password_changed_at)
            """)
            
            await session.execute(insert_sql, {
                "id": admin_id,
                "email": unique_email,
                "email_verified": True,
                "username": unique_username,
                "password_hash": get_password_hash("admin123"),
                "role": "admin",
                "is_active": True,
                "mfa_enabled": False,
                "failed_login_attempts": 0,
                "must_change_password": False,
                "is_system_user": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "password_changed_at": datetime.utcnow()
            })
            await session.commit()
        
        # Create access token
        access_token = create_access_token(data={
            "user_id": str(admin_id),
            "username": unique_username,
            "role": "admin",
            "email": unique_email
        })
        headers = {"Authorization": f"Bearer {access_token}"}
        
        print("   [PASS] Admin user created")
        print("   [PASS] Authentication token generated")
        
        # Test Patient API endpoints
        transport = httpx.ASGITransport(app=app)
        test_results = []
        patient_id = None
        
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            
            # Test 1: Create Patient
            print("\n2. Testing Patient Creation...")
            patient_data = {
                "identifier": [
                    {
                        "use": "official",
                        "type": {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                    "code": "MR",
                                    "display": "Medical Record Number"
                                }
                            ]
                        },
                        "system": "http://example.org/patients",
                        "value": "TEST-12345"
                    }
                ],
                "name": [
                    {
                        "given": ["John", "Michael"],
                        "family": "Doe",
                        "use": "official"
                    }
                ],
                "gender": "male",
                "birthDate": "1990-01-15",
                "address": [
                    {
                        "line": ["123 Healthcare Ave"],
                        "city": "Medical City",
                        "state": "HC",
                        "postalCode": "12345",
                        "country": "US"
                    }
                ],
                "telecom": [
                    {
                        "system": "phone",
                        "value": "+1-555-PATIENT",
                        "use": "home"
                    },
                    {
                        "system": "email",
                        "value": "john.doe@example.com",
                        "use": "home"
                    }
                ],
                "organization_id": str(uuid.uuid4())
            }
            
            try:
                response = await client.post("/api/v1/healthcare/patients", json=patient_data, headers=headers)
                if response.status_code in [200, 201]:
                    patient = response.json()
                    patient_id = patient.get("id")
                    print(f"   [PASS] Patient created successfully (ID: {patient_id})")
                    test_results.append(("CREATE", "PASS", response.status_code))
                else:
                    print(f"   [FAIL] Patient creation failed: {response.status_code}")
                    print(f"     Response: {response.text}")
                    test_results.append(("CREATE", "FAIL", response.status_code))
            except Exception as e:
                print(f"   [ERROR] Patient creation error: {e}")
                test_results.append(("CREATE", "ERROR", str(e)))
            
            # Test 2: Get Patient by ID
            if patient_id:
                print("\n3. Testing Patient Retrieval...")
                try:
                    response = await client.get(f"/api/v1/healthcare/patients/{patient_id}", headers=headers)
                    if response.status_code == 200:
                        patient = response.json()
                        print(f"   [PASS] Patient retrieved successfully")
                        print(f"     Name: {patient.get('name', [{}])[0].get('family', 'N/A')}")
                        test_results.append(("GET", "PASS", response.status_code))
                    else:
                        print(f"   [FAIL] Patient retrieval failed: {response.status_code}")
                        test_results.append(("GET", "FAIL", response.status_code))
                except Exception as e:
                    print(f"   [ERROR] Patient retrieval error: {e}")
                    test_results.append(("GET", "ERROR", str(e)))
            
            # Test 3: List Patients
            print("\n4. Testing Patient Listing...")
            try:
                response = await client.get("/api/v1/healthcare/patients", headers=headers)
                if response.status_code == 200:
                    patients = response.json()
                    count = len(patients.get('items', []))
                    print(f"   [PASS] Patient listing successful ({count} patients found)")
                    test_results.append(("LIST", "PASS", response.status_code))
                else:
                    print(f"   [FAIL] Patient listing failed: {response.status_code}")
                    test_results.append(("LIST", "FAIL", response.status_code))
            except Exception as e:
                print(f"   [ERROR] Patient listing error: {e}")
                test_results.append(("LIST", "ERROR", str(e)))
            
            # Test 4: Update Patient
            if patient_id:
                print("\n5. Testing Patient Update...")
                update_data = {
                    "name": [
                        {
                            "given": ["John", "Michael", "Updated"],
                            "family": "Doe",
                            "use": "official"
                        }
                    ]
                }
                try:
                    response = await client.put(f"/api/v1/healthcare/patients/{patient_id}", json=update_data, headers=headers)
                    if response.status_code in [200, 204]:
                        print(f"   [PASS] Patient updated successfully")
                        test_results.append(("UPDATE", "PASS", response.status_code))
                    else:
                        print(f"   [FAIL] Patient update failed: {response.status_code}")
                        test_results.append(("UPDATE", "FAIL", response.status_code))
                except Exception as e:
                    print(f"   [ERROR] Patient update error: {e}")
                    test_results.append(("UPDATE", "ERROR", str(e)))
            
            # Test 5: Search Patients
            print("\n6. Testing Patient Search...")
            try:
                response = await client.get("/api/v1/healthcare/patients/search?name=Doe", headers=headers)
                if response.status_code == 200:
                    results = response.json()
                    print(f"   [PASS] Patient search successful")
                    test_results.append(("SEARCH", "PASS", response.status_code))
                else:
                    print(f"   [FAIL] Patient search failed: {response.status_code}")
                    test_results.append(("SEARCH", "FAIL", response.status_code))
            except Exception as e:
                print(f"   [ERROR] Patient search error: {e}")
                test_results.append(("SEARCH", "ERROR", str(e)))
        
        await engine.dispose()
        
        # Print Results Summary
        print("\n" + "=" * 50)
        print("PATIENT API TEST RESULTS SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for _, status, _ in test_results if status == "PASS")
        total = len(test_results)
        
        for operation, status, code in test_results:
            status_icon = "PASS" if status == "PASS" else "FAIL"
            print(f"{status_icon} {operation:<8} {status:<6} ({code})")
        
        print("-" * 50)
        print(f"PASSED: {passed}/{total} tests")
        
        if passed == total:
            print("ALL PATIENT API TESTS PASSED!")
            print("Patient API is fully functional and ready for production")
            return True
        else:
            print(f"{total - passed} tests failed - Patient API needs attention")
            return False
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_patient_api_validation())
    print("\n" + "=" * 50)
    if success:
        print("PATIENT API INTEGRATION VALIDATION: COMPLETE")
    else:
        print("PATIENT API INTEGRATION VALIDATION: ISSUES FOUND")