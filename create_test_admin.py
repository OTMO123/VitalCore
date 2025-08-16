#!/usr/bin/env python3
"""
Create test admin user with correct authentication setup
"""

import asyncio
import asyncpg
from passlib.context import CryptContext
import uuid

async def create_test_admin():
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        # Create password context with same settings as the app
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Delete existing test admin if it exists
        await conn.execute("DELETE FROM users WHERE username = $1", "testadmin")
        
        # Create password hash
        password = "test123"
        password_hash = pwd_context.hash(password)
        
        # Insert new test admin user
        user_id = uuid.uuid4()
        await conn.execute("""
            INSERT INTO users (
                id, username, email, password_hash, role, is_active, 
                email_verified, mfa_enabled, failed_login_attempts,
                must_change_password, is_system_user
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """, 
        user_id, "testadmin", "testadmin@test.com", password_hash, 
        "ADMIN", True, True, False, 0, False, False)
        
        print("SUCCESS: Created test admin user")
        print(f"Username: testadmin")
        print(f"Password: test123")
        print(f"Role: ADMIN")
        print(f"Email: testadmin@test.com")
        print(f"ID: {user_id}")
        
        # Verify the password hash works
        if pwd_context.verify(password, password_hash):
            print("Password verification: PASS")
        else:
            print("Password verification: FAIL")
        
    except Exception as e:
        print(f"Error creating test admin: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_test_admin())