#!/usr/bin/env python3
"""
Create admin user for testing
"""

import asyncio
import asyncpg
import uuid
import bcrypt
from datetime import datetime

async def create_admin_user():
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        # Check if admin user exists
        existing_user = await conn.fetchrow("SELECT id FROM users WHERE username = 'admin'")
        
        if existing_user:
            print("Admin user already exists")
            return
        
        # Hash password
        password = "admin123"
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create admin user
        user_id = uuid.uuid4()
        await conn.execute("""
            INSERT INTO users (id, username, email, password_hash, role, is_active, email_verified, 
                             mfa_enabled, failed_login_attempts, must_change_password, is_system_user,
                             created_at, updated_at, password_changed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        """, user_id, "admin", "admin@test.com", password_hash, "ADMIN", True, True, 
             False, 0, False, False, 
             datetime.utcnow(), datetime.utcnow(), datetime.utcnow())
        
        print("Admin user created successfully!")
        print(f"Username: admin")
        print(f"Password: admin123")
        print(f"ID: {user_id}")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_admin_user())