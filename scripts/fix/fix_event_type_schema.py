#!/usr/bin/env python3
"""
Fix event_type schema to handle string values instead of enum constraint
"""
import asyncio
import asyncpg

async def fix_event_type_schema():
    """Fix event_type schema to allow string values"""
    database_url = "postgresql://postgres:password@localhost:5432/iris_db"
    
    try:
        conn = await asyncpg.connect(database_url)
        
        # Change event_type to VARCHAR to handle any string value
        await conn.execute("""
            ALTER TABLE audit_logs ALTER COLUMN event_type TYPE VARCHAR(255);
        """)
        print("✅ event_type column type updated to VARCHAR(255)")
        
        # Add index for performance
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
        """)
        print("✅ event_type index created")
        
        await conn.close()
        print("✅ Event type schema fixes completed!")
        
    except Exception as e:
        print(f"❌ Schema fix failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(fix_event_type_schema())
    exit(0 if success else 1)