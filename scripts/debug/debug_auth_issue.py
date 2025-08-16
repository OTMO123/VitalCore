#!/usr/bin/env python3
"""
Debug authentication issue by testing each step
"""

import asyncio
import asyncpg
from passlib.context import CryptContext

async def debug_auth():
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        print("=== DEBUGGING AUTHENTICATION ISSUE ===\n")
        
        # 1. Check if users exist
        print("1. Checking users...")
        users = await conn.fetch("SELECT id, username, role, is_active FROM users LIMIT 5")
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"  - {user['username']} (role: {user['role']}, active: {user['is_active']})")
        
        if not users:
            print("ERROR: No users found in database!")
            return
            
        # 2. Check password hashes
        print("\n2. Checking password hashes...")
        user_with_hash = await conn.fetchrow("SELECT username, password_hash FROM users WHERE username = 'admin'")
        if user_with_hash:
            print(f"Admin user found with hash length: {len(user_with_hash['password_hash'])}")
            
            # Test password verification
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            test_password = "admin123"
            is_valid = pwd_context.verify(test_password, user_with_hash['password_hash'])
            print(f"Password verification for 'admin123': {is_valid}")
        else:
            print("ERROR: Admin user not found!")
            
        # 3. Check enum values that might cause issues
        print("\n3. Checking enum values...")
        
        # Check audit event types
        audit_enums = await conn.fetch("""
            SELECT e.enumlabel
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'auditeventtype'
            ORDER BY e.enumsortorder
        """)
        print(f"Audit event types ({len(audit_enums)} total):")
        enum_labels = [row['enumlabel'] for row in audit_enums]
        if 'USER_LOGIN' in enum_labels:
            print("  OK USER_LOGIN enum exists")
        else:
            print("  ERROR USER_LOGIN enum missing!")
            
        # Check data classification
        data_class_enums = await conn.fetch("""
            SELECT e.enumlabel
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'dataclassification'
            ORDER BY e.enumsortorder
        """)
        print(f"Data classification types ({len(data_class_enums)} total):")
        data_labels = [row['enumlabel'] for row in data_class_enums]
        if 'INTERNAL' in data_labels:
            print("  OK INTERNAL enum exists")
        else:
            print("  ERROR INTERNAL enum missing!")
            
        # 4. Try to manually create an audit log entry to see what fails
        print("\n4. Testing audit log creation...")
        try:
            await conn.execute("""
                INSERT INTO audit_logs (
                    id, timestamp, event_type, user_id, action, result, 
                    ip_address, data_classification
                ) VALUES (
                    gen_random_uuid(), 
                    CURRENT_TIMESTAMP, 
                    'USER_LOGIN', 
                    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
                    'login_attempt', 
                    'test', 
                    '127.0.0.1', 
                    'INTERNAL'
                )
            """)
            print("  OK Audit log creation succeeded")
            
            # Delete the test entry
            await conn.execute("DELETE FROM audit_logs WHERE result = 'test'")
            
        except Exception as e:
            print(f"  ERROR Audit log creation failed: {e}")
            
        print("\n=== DEBUG COMPLETE ===")
        
    except Exception as e:
        print(f"Debug error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(debug_auth())