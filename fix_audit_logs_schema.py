#!/usr/bin/env python3
"""
Fix audit_logs table schema to match SQLAlchemy model
"""

import asyncio
import asyncpg

async def fix_audit_logs_schema():
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        print("Checking audit_logs table schema...")
        
        # Check current columns in audit_logs table
        current_columns = await conn.fetch("""
            SELECT column_name, data_type FROM information_schema.columns 
            WHERE table_name = 'audit_logs' 
            ORDER BY ordinal_position
        """)
        
        print("Current audit_logs columns:")
        column_names = []
        for col in current_columns:
            print(f"  {col['column_name']}: {col['data_type']}")
            column_names.append(col['column_name'])
        
        # Add missing timestamp column if it doesn't exist
        if 'timestamp' not in column_names:
            print("\nAdding missing 'timestamp' column...")
            await conn.execute("ALTER TABLE audit_logs ADD COLUMN timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("Added timestamp column")
        else:
            print("timestamp column already exists")
        
        # Check if we need to add other missing columns that the model expects
        expected_columns = [
            ("timestamp", "TIMESTAMP"),
            ("event_type", "VARCHAR"),
            ("user_id", "UUID"),
            ("session_id", "UUID"),
            ("correlation_id", "UUID"), 
            ("resource_type", "VARCHAR"),
            ("resource_id", "UUID"),
            ("action", "VARCHAR"),
            ("result", "VARCHAR"),
            ("ip_address", "INET"),
            ("user_agent", "VARCHAR"),
            ("request_method", "VARCHAR"),
            ("request_path", "VARCHAR"),
            ("request_body_hash", "VARCHAR"),
            ("response_status_code", "INTEGER"),
            ("error_message", "TEXT"),
            ("config_metadata", "JSON"),
            ("compliance_tags", "VARCHAR[]"),
            ("data_classification", "VARCHAR"),
            ("previous_log_hash", "VARCHAR"),
            ("log_hash", "VARCHAR"),
            ("sequence_number", "INTEGER")
        ]
        
        # Refresh column list
        current_columns = await conn.fetch("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'audit_logs'
        """)
        column_names = [col['column_name'] for col in current_columns]
        
        print(f"\nChecking for missing columns...")
        for col_name, col_type in expected_columns:
            if col_name not in column_names:
                print(f"Adding missing column: {col_name} ({col_type})")
                if col_type == "VARCHAR[]":
                    await conn.execute(f"ALTER TABLE audit_logs ADD COLUMN {col_name} VARCHAR[]")
                elif col_type == "INET":
                    await conn.execute(f"ALTER TABLE audit_logs ADD COLUMN {col_name} INET")
                elif col_type == "UUID":
                    await conn.execute(f"ALTER TABLE audit_logs ADD COLUMN {col_name} UUID")
                elif col_type == "JSON":
                    await conn.execute(f"ALTER TABLE audit_logs ADD COLUMN {col_name} JSON")
                elif col_type == "TEXT":
                    await conn.execute(f"ALTER TABLE audit_logs ADD COLUMN {col_name} TEXT")
                elif col_type == "INTEGER":
                    await conn.execute(f"ALTER TABLE audit_logs ADD COLUMN {col_name} INTEGER")
                elif col_type == "TIMESTAMP":
                    await conn.execute(f"ALTER TABLE audit_logs ADD COLUMN {col_name} TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                else:
                    await conn.execute(f"ALTER TABLE audit_logs ADD COLUMN {col_name} {col_type}")
            else:
                print(f"Column {col_name} already exists")
        
        print("\nAudit logs schema fix completed!")
        
        # Show final schema
        final_columns = await conn.fetch("""
            SELECT column_name, data_type FROM information_schema.columns 
            WHERE table_name = 'audit_logs' 
            ORDER BY ordinal_position
        """)
        
        print("\nFinal audit_logs table schema:")
        for col in final_columns:
            print(f"  {col['column_name']}: {col['data_type']}")
        
    except Exception as e:
        print(f"Error fixing audit_logs schema: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_audit_logs_schema())