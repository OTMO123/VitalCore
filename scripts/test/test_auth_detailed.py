#!/usr/bin/env python3
"""
Test authentication directly using the same libraries as the app
"""
import asyncio
import asyncpg
from app.core.security import security_manager

async def test_authentication():
    print("=== DETAILED AUTHENTICATION TEST ===")
    
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        # Get user from database
        user_record = await conn.fetchrow("""
            SELECT id, username, password_hash, role, is_active, email_verified, 
                   failed_login_attempts, locked_until 
            FROM users WHERE username = 'admin'
        """)
        
        if not user_record:
            print("FAIL: User not found in database")
            return
            
        print("SUCCESS: User found in database")
        print(f"   Username: {user_record['username']}")
        print(f"   Role: {user_record['role']}")
        print(f"   Active: {user_record['is_active']}")
        print(f"   Email Verified: {user_record['email_verified']}")
        print(f"   Failed Attempts: {user_record['failed_login_attempts']}")
        print(f"   Locked Until: {user_record['locked_until']}")
        
        # Test password verification
        test_password = "admin123"
        stored_hash = user_record['password_hash']
        
        print(f"\nTesting password verification...")
        print(f"   Test Password: {test_password}")
        print(f"   Stored Hash: {stored_hash[:50]}...")
        
        try:
            is_valid = security_manager.verify_password(test_password, stored_hash)
            print(f"   Password Valid: {'YES' if is_valid else 'NO'}")
            
            if is_valid:
                print("\nSUCCESS: Authentication should work!")
                print("   The password hash verification passes locally")
            else:
                print("\nFAIL: Password verification failed!")
                print("   This explains why authentication returns 401")
                
        except Exception as e:
            print(f"   Password Verification Error: {e}")
        
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_authentication())