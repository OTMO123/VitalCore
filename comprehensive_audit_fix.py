#!/usr/bin/env python3
"""
Comprehensive fix for audit_logs schema mismatch between SQLAlchemy model and database
"""

import asyncio
import asyncpg

async def comprehensive_audit_fix():
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        print("=== COMPREHENSIVE AUDIT LOGS FIX ===\n")
        
        # 1. Check current schema
        print("1. Current audit_logs schema:")
        current_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable FROM information_schema.columns 
            WHERE table_name = 'audit_logs' 
            ORDER BY ordinal_position
        """)
        
        column_names = []
        for col in current_columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            print(f"  {col['column_name']}: {col['data_type']} {nullable}")
            column_names.append(col['column_name'])
        
        # 2. The issue: SQLAlchemy model uses 'outcome' but INSERT uses 'result' 
        print(f"\n2. Schema Issues Found:")
        issues = []
        
        if 'outcome' not in column_names:
            issues.append("Missing 'outcome' column (SQLAlchemy expects this)")
        if 'result' in column_names:
            issues.append("Has 'result' column (but SQLAlchemy uses 'outcome')")
            
        for issue in issues:
            print(f"  - {issue}")
            
        # 3. Fix the schema mismatch
        print(f"\n3. Fixing schema mismatch...")
        
        if 'outcome' not in column_names and 'result' in column_names:
            print("  Renaming 'result' column to 'outcome'...")
            await conn.execute("ALTER TABLE audit_logs RENAME COLUMN result TO outcome")
            print("  OK Renamed result -> outcome")
        elif 'outcome' not in column_names:
            print("  Adding 'outcome' column...")
            await conn.execute("ALTER TABLE audit_logs ADD COLUMN outcome VARCHAR(50) DEFAULT 'success' NOT NULL")
            print("  OK Added outcome column")
        else:
            print("  OK outcome column already exists correctly")
            
        # 4. Ensure all required NOT NULL columns have defaults
        required_defaults = [
            ("outcome", "VARCHAR(50)", "success"),
            ("purge_hold", "BOOLEAN", "FALSE"),
            ("is_deleted", "BOOLEAN", "FALSE"),
            ("created_at", "TIMESTAMP", "CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP", "CURRENT_TIMESTAMP"),
        ]
        
        print(f"\n4. Setting defaults for required columns...")
        for col_name, col_type, default_value in required_defaults:
            try:
                if default_value == "CURRENT_TIMESTAMP":
                    await conn.execute(f"ALTER TABLE audit_logs ALTER COLUMN {col_name} SET DEFAULT {default_value}")
                elif default_value in ["TRUE", "FALSE"]:
                    await conn.execute(f"ALTER TABLE audit_logs ALTER COLUMN {col_name} SET DEFAULT {default_value}")
                else:
                    await conn.execute(f"ALTER TABLE audit_logs ALTER COLUMN {col_name} SET DEFAULT '{default_value}'")
                print(f"  OK Set default for {col_name}: {default_value}")
            except Exception as e:
                print(f"  - Could not set default for {col_name}: {e}")
        
        # 5. Test the fix
        print(f"\n5. Testing audit log creation...")
        try:
            test_user_id = await conn.fetchval("SELECT id FROM users WHERE username = 'admin' LIMIT 1")
            
            await conn.execute("""
                INSERT INTO audit_logs (
                    id, timestamp, event_type, user_id, action, outcome, 
                    ip_address, data_classification, purge_hold, is_deleted
                ) VALUES (
                    gen_random_uuid(), 
                    CURRENT_TIMESTAMP, 
                    'USER_LOGIN', 
                    $1,
                    'test_login', 
                    'success',
                    '127.0.0.1', 
                    'INTERNAL',
                    FALSE,
                    FALSE
                )
            """, test_user_id)
            print("  SUCCESS: Audit log creation works!")
            
            # Clean up test entry
            await conn.execute("DELETE FROM audit_logs WHERE action = 'test_login'")
            
        except Exception as e:
            print(f"  ERROR: Audit log creation still fails: {e}")
            
        # 6. Show final schema
        print(f"\n6. Final audit_logs schema:")
        final_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns 
            WHERE table_name = 'audit_logs' 
            ORDER BY ordinal_position
        """)
        
        for col in final_columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"  {col['column_name']}: {col['data_type']} {nullable}{default}")
            
        print(f"\n=== FIX COMPLETED ===")
        print("Now restart the server and test authentication again!")
        
    except Exception as e:
        print(f"Error in comprehensive fix: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(comprehensive_audit_fix())