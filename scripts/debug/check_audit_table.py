#!/usr/bin/env python3
"""Check if audit_logs table exists and show its structure."""

import asyncio
import asyncpg
from datetime import datetime

async def check_audit_table():
    try:
        # Connect to database using the same config as the app
        conn = await asyncpg.connect(
            "postgresql://test_user:test_password@localhost:5433/test_iris_db"
        )
        
        print("=== CHECKING AUDIT_LOGS TABLE ===")
        
        # Check if table exists
        exists_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'audit_logs'
        );
        """
        
        table_exists = await conn.fetchval(exists_query)
        print(f"audit_logs table exists: {table_exists}")
        
        if table_exists:
            # Get table structure
            structure_query = """
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'audit_logs' 
            ORDER BY ordinal_position;
            """
            
            columns = await conn.fetch(structure_query)
            print("\nTable structure:")
            for col in columns:
                print(f"  {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
            
            # Count records
            count = await conn.fetchval("SELECT COUNT(*) FROM audit_logs;")
            print(f"\nTotal records in audit_logs: {count}")
            
            # Show recent records if any
            if count > 0:
                recent_query = """
                SELECT id, event_type, user_id, action, result, timestamp 
                FROM audit_logs 
                ORDER BY timestamp DESC 
                LIMIT 5;
                """
                records = await conn.fetch(recent_query)
                print("\nRecent audit logs:")
                for record in records:
                    print(f"  {record['timestamp']}: {record['event_type']} - {record['action']} ({record['result']})")
        else:
            print("❌ audit_logs table does not exist!")
            print("You need to run database migration first.")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_audit_table())