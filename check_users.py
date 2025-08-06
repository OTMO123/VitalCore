#!/usr/bin/env python3
"""
Check users in database
"""

import asyncio
import asyncpg

async def check_users():
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        # Get all users
        users = await conn.fetch("SELECT id, username, email, role, is_active, email_verified FROM users")
        
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"  ID: {user['id']}")
            print(f"  Username: {user['username']}")
            print(f"  Email: {user['email']}")
            print(f"  Role: {user['role']}")
            print(f"  Active: {user['is_active']}")
            print(f"  Email Verified: {user['email_verified']}")
            print("  ---")
        
    except Exception as e:
        print(f"Error checking users: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_users())