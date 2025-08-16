#!/usr/bin/env python3
"""
Check users in database with detailed info
"""

import asyncio
import asyncpg

async def check_users():
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        # Get all users with detailed info
        users = await conn.fetch("""
            SELECT username, role, is_active, email_verified, email, 
                   created_at, failed_login_attempts, last_login
            FROM users
        """)
        
        print(f"Found {len(users)} users in database:")
        print("-" * 80)
        
        for user in users:
            print(f"Username: {user['username']}")
            print(f"Email: {user['email']}")
            print(f"Role: {user['role']}")
            print(f"Active: {user['is_active']}")
            print(f"Email Verified: {user['email_verified']}")
            print(f"Failed Login Attempts: {user['failed_login_attempts']}")
            print(f"Last Login: {user['last_login']}")
            print(f"Created: {user['created_at']}")
            print("-" * 40)
        
    except Exception as e:
        print(f"Error checking users: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_users())