#!/usr/bin/env python3
"""
Basic Patient API Test - Direct API Testing
"""
import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

async def test_patient_api():
    """Test Patient API endpoints directly."""
    try:
        import httpx
        from app.main import app
        from app.core.database_advanced import User, get_engine
        from app.core.security import get_password_hash, create_access_token
        from sqlalchemy.ext.asyncio import async_sessionmaker
        
        print("Setting up test environment...")
        
        # Set up database
        engine = get_engine()
        if engine is None:
            from sqlalchemy.ext.asyncio import create_async_engine
            database_url = "postgresql+asyncpg://test_user:test_password@localhost:5433/test_iris_db"
            engine = create_async_engine(database_url, echo=False)
        
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        
        # Create test user with admin role
        print("Creating test admin user...")
        async with session_factory() as session:
            admin_user = User(
                email="admin_test@example.com",
                username="admin_test",
                password_hash=get_password_hash("admin123"),
                email_verified=True,
                role="admin",
                is_active=True
            )
            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)
            
            # Create access token
            token_data = {
                "user_id": str(admin_user.id),
                "username": admin_user.username,
                "role": admin_user.role,
                "email": admin_user.email
            }
            access_token = create_access_token(data=token_data)
            headers = {"Authorization": f"Bearer {access_token}"}
        
        # Test Patient API
        print("Testing Patient API endpoints...")
        
        # Create ASGI transport for httpx
        transport = httpx.ASGITransport(app=app)
        
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            
            # Test 1: Create Patient
            print("1. Testing patient creation...")
            patient_data = {
                "identifier": [
                    {
                        "system": "http://example.org/patients",
                        "value": "TEST-001"
                    }
                ],
                "name": [
                    {
                        "given": ["John"],
                        "family": "Doe",
                        "use": "official"
                    }
                ],
                "gender": "male",
                "birthDate": "1990-01-01",
                "address": [
                    {
                        "line": ["123 Test St"],
                        "city": "Test City",
                        "state": "TS",
                        "postalCode": "12345",
                        "country": "US"
                    }
                ],
                "telecom": [
                    {
                        "system": "phone",
                        "value": "+1-555-123-4567",
                        "use": "home"
                    }
                ]
            }
            
            response = await client.post("/api/v1/patients", json=patient_data, headers=headers)
            print(f"   Create Patient Response: {response.status_code}")
            
            if response.status_code == 201:
                patient = response.json()
                patient_id = patient["id"]
                print(f"   Patient created successfully: {patient_id}")
                
                # Test 2: Get Patient
                print("2. Testing patient retrieval...")
                response = await client.get(f"/api/v1/patients/{patient_id}", headers=headers)
                print(f"   Get Patient Response: {response.status_code}")
                
                if response.status_code == 200:
                    print("   Patient retrieved successfully")
                    
                    # Test 3: List Patients
                    print("3. Testing patient listing...")
                    response = await client.get("/api/v1/patients", headers=headers)
                    print(f"   List Patients Response: {response.status_code}")
                    
                    if response.status_code == 200:
                        patients = response.json()
                        print(f"   Found {len(patients.get('items', []))} patients")
                        
                        # Test 4: Update Patient
                        print("4. Testing patient update...")
                        update_data = {
                            "name": [
                                {
                                    "given": ["John", "Updated"],
                                    "family": "Doe",
                                    "use": "official"
                                }
                            ]
                        }
                        response = await client.put(f"/api/v1/patients/{patient_id}", json=update_data, headers=headers)
                        print(f"   Update Patient Response: {response.status_code}")
                        
                        return True
                    else:
                        print(f"   List patients failed: {response.text}")
                else:
                    print(f"   Get patient failed: {response.text}")
            else:
                print(f"   Create patient failed: {response.text}")
        
        await engine.dispose()
        return False
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_patient_api())
    if success:
        print("\n✓ Patient API tests passed! Integration working correctly.")
    else:
        print("\n✗ Patient API tests failed.")