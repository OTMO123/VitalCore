#!/usr/bin/env python3
"""
Fix user_id schema mismatch - ensure proper VARCHAR handling
"""
import asyncio
import asyncpg

async def fix_user_id_schema():
    """Fix user_id schema to handle both UUID and VARCHAR properly"""
    database_url = "postgresql://postgres:password@localhost:5432/iris_db"
    
    try:
        conn = await asyncpg.connect(database_url)
        
        # Ensure user_id is VARCHAR and can handle both UUID strings and regular strings
        await conn.execute("""
            ALTER TABLE audit_logs ALTER COLUMN user_id TYPE VARCHAR(255);
        """)
        print("✅ user_id column type updated to VARCHAR(255)")
        
        # Add an index for performance
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
        """)
        print("✅ user_id index created")
        
        # Update any NULL action fields to prevent NOT NULL constraint issues
        await conn.execute("""
            UPDATE audit_logs SET action = 'system_action' WHERE action IS NULL;
        """)
        print("✅ NULL action fields updated")
        
        # Make action field optional
        await conn.execute("""
            ALTER TABLE audit_logs ALTER COLUMN action DROP NOT NULL;
        """)
        print("✅ action field made optional")
        
        await conn.close()
        print("✅ Database schema fixes completed!")
        
    except Exception as e:
        print(f"❌ Schema fix failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(fix_user_id_schema())
    exit(0 if success else 1)