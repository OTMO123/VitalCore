#!/usr/bin/env python3
"""
Fix phi_access_logs table schema to add missing purpose column.

This script ensures the phi_access_logs table has the purpose column
that is expected by the PHI audit system for HIPAA compliance.
"""

import asyncio
import asyncpg
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings

async def fix_phi_purpose_column():
    """Fix the phi_access_logs table schema by adding purpose column."""
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
        # 1. Check current phi_access_logs table schema
        print("\n1. Checking current phi_access_logs table schema...")
        
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'phi_access_logs' 
            AND column_name = 'purpose'
            ORDER BY column_name;
        """)
        
        if result:
            print("✓ purpose column already exists:")
            for row in result:
                print(f"  - {row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']})")
            return True
        
        print("purpose column missing - adding it...")
        
        # 2. Add purpose column
        print("\n2. Adding purpose column...")
        
        await conn.execute("""
            ALTER TABLE phi_access_logs 
            ADD COLUMN purpose VARCHAR(100) DEFAULT 'treatment';
        """)
        
        print("  ✓ purpose column added as VARCHAR(100) with default 'treatment'")
        
        # 3. Create index for efficient querying
        print("\n3. Creating index for purpose queries...")
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS ix_phi_access_logs_purpose 
            ON phi_access_logs (purpose);
        """)
        
        print("  ✓ Index created for purpose column")
        
        # 4. Verify final schema
        print("\n4. Verifying final schema...")
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'phi_access_logs' 
            AND column_name IN ('purpose', 'accessed_fields')
            ORDER BY column_name;
        """)
        
        print("Final schema:")
        for row in result:
            print(f"  - {row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']})")
        
        print("\n✓ PHI access logs purpose column fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Error fixing schema: {e}")
        return False
    finally:
        await conn.close()


if __name__ == "__main__":
    success = asyncio.run(fix_phi_purpose_column())
    sys.exit(0 if success else 1)