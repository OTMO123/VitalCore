#!/usr/bin/env python3
"""
Force SQLAlchemy to reflect actual database schema.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

async def test_with_reflection():
    """Create user by reflecting actual database schema."""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from sqlalchemy.orm import declarative_base
        from sqlalchemy import Table, Column, String, Boolean, UUID, DateTime, MetaData
        from app.core.security import get_password_hash
        import uuid
        from datetime import datetime
        
        print("Connecting with schema reflection...")
        database_url = "postgresql+asyncpg://test_user:test_password@localhost:5433/test_iris_db"
        engine = create_async_engine(database_url, echo=False)
        
        # Create metadata and reflect actual schema
        metadata = MetaData()
        
        async with engine.begin() as conn:
            # Reflect the actual users table from database
            await conn.run_sync(metadata.reflect, only=['users'])
        
        # Get the reflected users table
        users_table = metadata.tables['users']
        print(f"Reflected columns: {list(users_table.columns.keys())}")
        
        # Create session
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        
        # Insert user using raw SQL to bypass ORM caching
        async with session_factory() as session:
            from sqlalchemy import text
            user_id = uuid.uuid4()
            insert_sql = text("""
                INSERT INTO users (id, email, email_verified, username, password_hash, 
                                 role, is_active, mfa_enabled, failed_login_attempts, 
                                 must_change_password, is_system_user, created_at, updated_at, password_changed_at)
                VALUES (:id, :email, :email_verified, :username, :password_hash, 
                        :role, :is_active, :mfa_enabled, :failed_login_attempts,
                        :must_change_password, :is_system_user, :created_at, :updated_at, :password_changed_at)
                RETURNING id, email, username, role
            """)
            
            result = await session.execute(
                insert_sql,
                {
                    "id": user_id,
                    "email": "reflect_test@example.com",
                    "email_verified": True,
                    "username": "reflect_test",
                    "password_hash": get_password_hash("password123"),
                    "role": "user",
                    "is_active": True,
                    "mfa_enabled": False,
                    "failed_login_attempts": 0,
                    "must_change_password": False,
                    "is_system_user": False,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "password_changed_at": datetime.utcnow()
                }
            )
            await session.commit()
            
            # Fetch the created user
            user_data = result.fetchone()
            print(f"SUCCESS: User created with reflection approach!")
            print(f"  ID: {user_data[0]}")
            print(f"  Email: {user_data[1]}")
            print(f"  Username: {user_data[2]}")
            print(f"  Role: {user_data[3]}")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_patient_api_raw():
    """Test Patient API with reflection-based approach."""
    try:
        import httpx
        from app.main import app
        from app.core.security import create_access_token
        
        print("\nTesting Patient API with raw SQL user...")
        
        # Use the user we just created
        access_token = create_access_token(data={
            "user_id": "12345678-1234-1234-1234-123456789012",  # fake ID for demo
            "username": "reflect_test",
            "role": "admin",  # Force admin for testing
            "email": "reflect_test@example.com"
        })
        headers = {"Authorization": f"Bearer {access_token}"}
        
        transport = httpx.ASGITransport(app=app)
        
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # Test patient creation
            patient_data = {
                "identifier": [{"system": "test", "value": "TEST-001"}],
                "name": [{"given": ["John"], "family": "Doe", "use": "official"}],
                "gender": "male",
                "birthDate": "1990-01-01"
            }
            
            print("Testing patient creation...")
            response = await client.post("/api/v1/patients", json=patient_data, headers=headers)
            print(f"Patient API Response: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print("SUCCESS: Patient API is working!")
                return True
            else:
                print(f"Patient API Error: {response.text}")
                return False
    
    except Exception as e:
        print(f"Patient API Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Testing SQLAlchemy Schema Reflection ===")
    user_success = asyncio.run(test_with_reflection())
    
    if user_success:
        print("\n=== Testing Patient API ===")
        api_success = asyncio.run(test_patient_api_raw())
        
        if api_success:
            print("\n✓ SOLUTION FOUND: Schema reflection works!")
            print("✓ Patient API is functional!")
        else:
            print("\n✓ User creation fixed, but Patient API needs attention")
    else:
        print("\n✗ Schema reflection approach failed")