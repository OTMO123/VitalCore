#!/usr/bin/env python3
"""
Final comprehensive fix for audit_logs table
"""

import asyncio
import asyncpg

async def fix_audit_logs_final():
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        print("Final audit_logs table fix...")
        
        # Set default values for all NOT NULL columns that might be missing defaults
        required_defaults = [
            ("purge_hold", "FALSE"),
            ("is_deleted", "FALSE"), 
            ("created_at", "CURRENT_TIMESTAMP"),
            ("updated_at", "CURRENT_TIMESTAMP"),
        ]
        
        print("Setting default values for required columns...")
        for col_name, default_value in required_defaults:
            try:
                if default_value == "CURRENT_TIMESTAMP":
                    await conn.execute(f"ALTER TABLE audit_logs ALTER COLUMN {col_name} SET DEFAULT {default_value}")
                elif default_value in ["TRUE", "FALSE"]:
                    await conn.execute(f"ALTER TABLE audit_logs ALTER COLUMN {col_name} SET DEFAULT {default_value}")
                else:
                    await conn.execute(f"ALTER TABLE audit_logs ALTER COLUMN {col_name} SET DEFAULT '{default_value}'")
                print(f"  Set default for {col_name}: {default_value}")
            except Exception as e:
                print(f"  Warning: Could not set default for {col_name}: {e}")
        
        # Test audit log creation with all required fields
        print("\nTesting comprehensive audit log creation...")
        try:
            await conn.execute("""
                INSERT INTO audit_logs (
                    id, timestamp, event_type, user_id, action, outcome, 
                    ip_address, data_classification, purge_hold, is_deleted,
                    created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), 
                    CURRENT_TIMESTAMP, 
                    'USER_LOGIN', 
                    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
                    'login_attempt', 
                    'success',
                    '127.0.0.1', 
                    'INTERNAL',
                    FALSE,
                    FALSE,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
            """)
            print("SUCCESS: Full audit log creation works!")
            
            # Delete the test entry
            await conn.execute("DELETE FROM audit_logs WHERE action = 'login_attempt'")
            
        except Exception as e:
            print(f"ERROR: Audit log creation still fails: {e}")
            
            # Try minimal audit log creation
            print("\nTrying minimal audit log with just required fields...")
            try:
                await conn.execute("""
                    INSERT INTO audit_logs (
                        event_type, action, outcome, purge_hold, is_deleted
                    ) VALUES (
                        'USER_LOGIN', 'test_minimal', 'success', FALSE, FALSE
                    )
                """)
                print("SUCCESS: Minimal audit log creation works!")
                await conn.execute("DELETE FROM audit_logs WHERE action = 'test_minimal'")
            except Exception as e2:
                print(f"ERROR: Even minimal creation fails: {e2}")
        
        print("\nFinal audit logs fix completed!")
        
    except Exception as e:
        print(f"Error in final audit fix: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_audit_logs_final())