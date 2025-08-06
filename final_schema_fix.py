#!/usr/bin/env python3
"""
Final schema fix - convert user_id to UUID type and remove duplicate result column
"""

import asyncio
import asyncpg

async def final_schema_fix():
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        print("=== FINAL SCHEMA FIX ===\n")
        
        # 1. Check user_id column type
        user_id_info = await conn.fetchrow("""
            SELECT data_type FROM information_schema.columns 
            WHERE table_name = 'audit_logs' AND column_name = 'user_id'
        """)
        
        print(f"1. Current user_id type: {user_id_info['data_type']}")
        
        # 2. Convert user_id to UUID if it's not already
        if user_id_info['data_type'] != 'uuid':
            print("2. Converting user_id to UUID type...")
            try:
                # First, update any existing records to ensure they're valid UUIDs or NULL
                await conn.execute("UPDATE audit_logs SET user_id = NULL WHERE user_id = ''")
                
                # Convert the column type
                await conn.execute("ALTER TABLE audit_logs ALTER COLUMN user_id TYPE UUID USING user_id::UUID")
                print("  OK user_id converted to UUID")
            except Exception as e:
                print(f"  ERROR converting user_id: {e}")
        else:
            print("2. user_id is already UUID type")
        
        # 3. Remove duplicate result column since we have outcome
        print("3. Removing duplicate 'result' column...")
        try:
            await conn.execute("ALTER TABLE audit_logs DROP COLUMN IF EXISTS result")
            print("  OK removed result column")
        except Exception as e:
            print(f"  ERROR removing result column: {e}")
        
        # 4. Test audit log creation
        print("4. Testing audit log creation...")
        try:
            test_user_id = await conn.fetchval("SELECT id FROM users WHERE username = 'admin' LIMIT 1")
            
            await conn.execute("""
                INSERT INTO audit_logs (
                    event_type, user_id, action, outcome, 
                    ip_address, data_classification
                ) VALUES (
                    'USER_LOGIN', 
                    $1,
                    'test_final', 
                    'success',
                    '127.0.0.1', 
                    'INTERNAL'
                )
            """, test_user_id)
            print("  SUCCESS: Audit log creation works!")
            
            # Clean up test entry
            await conn.execute("DELETE FROM audit_logs WHERE action = 'test_final'")
            
        except Exception as e:
            print(f"  ERROR: {e}")
        
        print("\n=== FINAL SCHEMA FIX COMPLETED ===")
        print("Restart the server and test authentication!")
        
    except Exception as e:
        print(f"Error in final schema fix: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(final_schema_fix())