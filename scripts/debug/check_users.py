#!/usr/bin/env python3

import asyncio
import asyncpg
from passlib.context import CryptContext

# Password context for verification
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def check_users():
    """Check what users exist in the database"""
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host="localhost",
            port=5433,
            user="test_user", 
            password="test_password",
            database="test_iris_db"
        )
        
        print("Connected to database successfully!")
        
        # Check if users table exists
        tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        table_names = [row['tablename'] for row in tables]
        
        print(f"Available tables: {table_names}")
        
        if 'users' not in table_names:
            print("❌ Users table does not exist!")
            return
            
        # Get all users
        users = await conn.fetch("SELECT username, email, password_hash, role, is_active FROM users")
        
        print(f"\nFound {len(users)} users:")
        for user in users:
            print(f"- Username: {user['username']}")
            print(f"  Email: {user['email']}")
            print(f"  Role: {user['role']}")
            print(f"  Active: {user['is_active']}")
            print(f"  Password hash: {user['password_hash'][:50]}...")
            
            # Test password
            if user['username'] == 'admin':
                test_password = 'admin123'
                is_valid = pwd_context.verify(test_password, user['password_hash'])
                print(f"  Password '{test_password}' is valid: {is_valid}")
            print()
            
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_users())