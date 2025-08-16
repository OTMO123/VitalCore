#!/usr/bin/env python3
"""
Fix audit_logs table - add missing outcome column
"""

import asyncio
import asyncpg

async def fix_audit_outcome():
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        print("Checking audit_logs table structure...")
        
        # Check current columns
        current_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable FROM information_schema.columns 
            WHERE table_name = 'audit_logs' 
            ORDER BY ordinal_position
        """)
        
        print("Current audit_logs columns:")
        column_names = []
        for col in current_columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            print(f"  {col['column_name']}: {col['data_type']} {nullable}")
            column_names.append(col['column_name'])
        
        # Add missing outcome column if it doesn't exist
        if 'outcome' not in column_names:
            print("\nAdding missing 'outcome' column...")
            await conn.execute("ALTER TABLE audit_logs ADD COLUMN outcome VARCHAR(50) DEFAULT 'success'")
            print("Added outcome column with default 'success'")
        else:
            print("\noutcome column already exists")
            
        # Check if outcome column is nullable and make it not null if needed
        outcome_col = await conn.fetchrow("""
            SELECT is_nullable FROM information_schema.columns 
            WHERE table_name = 'audit_logs' AND column_name = 'outcome'
        """)
        
        if outcome_col and outcome_col['is_nullable'] == 'YES':
            print("Making outcome column NOT NULL...")
            # First update any NULL values
            await conn.execute("UPDATE audit_logs SET outcome = 'success' WHERE outcome IS NULL")
            # Then add NOT NULL constraint
            await conn.execute("ALTER TABLE audit_logs ALTER COLUMN outcome SET NOT NULL")
            print("outcome column is now NOT NULL")
            
        # Also check for other missing required columns
        required_columns = [
            ("outcome", "VARCHAR(50)", "NOT NULL"),
            ("session_id", "UUID", "NULL"),
            ("correlation_id", "UUID", "NULL"),
        ]
        
        print("\nChecking other required columns...")
        for col_name, col_type, nullable in required_columns:
            if col_name not in column_names:
                print(f"Adding missing column: {col_name}")
                if nullable == "NOT NULL":
                    await conn.execute(f"ALTER TABLE audit_logs ADD COLUMN {col_name} {col_type} DEFAULT 'default_value'")
                else:
                    await conn.execute(f"ALTER TABLE audit_logs ADD COLUMN {col_name} {col_type}")
            else:
                print(f"Column {col_name} already exists")
        
        print("\nAudit logs table fix completed!")
        
        # Test audit log creation again
        print("\nTesting audit log creation...")
        try:
            await conn.execute("""
                INSERT INTO audit_logs (
                    id, timestamp, event_type, user_id, action, outcome, 
                    ip_address, data_classification
                ) VALUES (
                    gen_random_uuid(), 
                    CURRENT_TIMESTAMP, 
                    'USER_LOGIN', 
                    (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
                    'login_attempt', 
                    'success',
                    '127.0.0.1', 
                    'INTERNAL'
                )
            """)
            print("SUCCESS: Audit log creation now works!")
            
            # Delete the test entry
            await conn.execute("DELETE FROM audit_logs WHERE action = 'login_attempt'")
            
        except Exception as e:
            print(f"ERROR: Audit log creation still fails: {e}")
        
    except Exception as e:
        print(f"Error fixing audit outcome: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_audit_outcome())