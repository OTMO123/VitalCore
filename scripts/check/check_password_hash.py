#!/usr/bin/env python3
"""
Check password hash format and create correct admin user
"""

import asyncio
import asyncpg
import uuid
from passlib.context import CryptContext

async def check_and_fix_password():
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        # Check current admin user
        admin_user = await conn.fetchrow("SELECT username, password_hash FROM users WHERE username = 'admin'")
        
        if admin_user:
            print(f"Found admin user: {admin_user['username']}")
            print(f"Current password hash: {admin_user['password_hash'][:50]}...")
        
        # Create password context using same method as FastAPI app
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Hash the password correctly
        correct_hash = pwd_context.hash("admin123")
        print(f"Correct hash format: {correct_hash[:50]}...")
        
        # Update the admin user with correct hash
        await conn.execute("UPDATE users SET password_hash = $1 WHERE username = 'admin'", correct_hash)
        print("Updated admin password hash")
        
        # Verify the hash works
        if pwd_context.verify("admin123", correct_hash):
            print("Password verification works!")
        else:
            print("Password verification failed!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_and_fix_password())