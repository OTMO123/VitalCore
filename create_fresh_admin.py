#!/usr/bin/env python3
"""
Create fresh admin user with correct password hashing
"""

import asyncio
import asyncpg
import uuid
from app.core.security import security_manager
from datetime import datetime

async def create_fresh_admin():
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        # Delete existing admin
        await conn.execute("DELETE FROM users WHERE username = 'admin'")
        print("Deleted existing admin user")
        
        # Create new admin with proper password hashing
        password = "admin123"
        password_hash = security_manager.hash_password(password)
        
        user_id = uuid.uuid4()
        await conn.execute("""
            INSERT INTO users (id, username, email, password_hash, role, is_active, email_verified, 
                             mfa_enabled, failed_login_attempts, must_change_password, is_system_user,
                             created_at, updated_at, password_changed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        """, user_id, "admin", "admin@test.com", password_hash, "ADMIN", True, True, 
             False, 0, False, False, 
             datetime.utcnow(), datetime.utcnow(), datetime.utcnow())
        
        print("Fresh admin user created successfully!")
        print(f"Username: admin")
        print(f"Password: admin123")
        print(f"ID: {user_id}")
        
        # Verify password hash
        is_valid = security_manager.verify_password(password, password_hash)
        print(f"Password verification test: {'PASS' if is_valid else 'FAIL'}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_fresh_admin())