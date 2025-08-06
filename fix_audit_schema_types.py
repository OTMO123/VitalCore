#!/usr/bin/env python3
"""
Fix audit_logs schema types to match unified database model.

This script ensures the audit_logs table matches the expected schema:
- user_id: VARCHAR (string) not UUID
- outcome: VARCHAR (not result)
"""

import asyncio
import asyncpg
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings

async def fix_audit_schema():
    """Fix the audit_logs table schema."""
    settings = get_settings()
    
    # Extract connection parameters from database URL
    import re
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgres://", 1)
    
    # Connect to database
    try:
        conn = await asyncpg.connect(db_url)
        print("✓ Connected to database")
    except Exception as e:
        print(f"✗ Failed to connect to database: {e}")
        return False
    
    try:
        # 1. Check current schema
        print("\n1. Checking current audit_logs schema...")
        
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'audit_logs' 
            AND column_name IN ('user_id', 'outcome', 'result')
            ORDER BY column_name;
        """)
        
        print("Current schema:")
        for row in result:
            print(f"  - {row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']})")
        
        # 2. Fix user_id type if it's UUID
        user_id_info = [r for r in result if r['column_name'] == 'user_id']
        if user_id_info and user_id_info[0]['data_type'] == 'uuid':
            print("\n2. Converting user_id from UUID to VARCHAR...")
            
            # Add temporary column
            await conn.execute("ALTER TABLE audit_logs ADD COLUMN user_id_temp VARCHAR(255);")
            
            # Copy data with conversion
            await conn.execute("UPDATE audit_logs SET user_id_temp = user_id::text WHERE user_id IS NOT NULL;")
            
            # Drop old column and rename
            await conn.execute("ALTER TABLE audit_logs DROP COLUMN user_id;")
            await conn.execute("ALTER TABLE audit_logs RENAME COLUMN user_id_temp TO user_id;")
            
            # Add index
            await conn.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs (user_id);")
            
            print("  ✓ user_id converted to VARCHAR(255)")
        else:
            print("2. user_id type is already correct (VARCHAR)")
        
        # 3. Fix outcome column if result exists
        has_result = any(r['column_name'] == 'result' for r in result)
        has_outcome = any(r['column_name'] == 'outcome' for r in result)
        
        if has_result and not has_outcome:
            print("\n3. Converting result column to outcome...")
            
            # Add outcome column
            await conn.execute("ALTER TABLE audit_logs ADD COLUMN outcome VARCHAR(50) DEFAULT 'success';")
            
            # Copy data
            await conn.execute("UPDATE audit_logs SET outcome = COALESCE(result, 'success');")
            
            # Make it not null
            await conn.execute("ALTER TABLE audit_logs ALTER COLUMN outcome SET NOT NULL;")
            
            # Drop old column
            await conn.execute("ALTER TABLE audit_logs DROP COLUMN result;")
            
            print("  ✓ result column converted to outcome")
        elif has_outcome:
            print("3. outcome column already exists")
        else:
            print("3. Adding outcome column...")
            await conn.execute("ALTER TABLE audit_logs ADD COLUMN outcome VARCHAR(50) DEFAULT 'success' NOT NULL;")
            print("  ✓ outcome column added")
        
        # 4. Verify final schema
        print("\n4. Verifying final schema...")
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'audit_logs' 
            AND column_name IN ('user_id', 'outcome')
            ORDER BY column_name;
        """)
        
        print("Final schema:")
        for row in result:
            print(f"  - {row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']})")
        
        print("\n✓ Audit logs schema fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Error fixing schema: {e}")
        return False
    finally:
        await conn.close()


if __name__ == "__main__":
    success = asyncio.run(fix_audit_schema())
    sys.exit(0 if success else 1)