#!/usr/bin/env python3
"""
Fix phi_access_logs table schema to add missing accessed_fields column.

This script ensures the phi_access_logs table has the accessed_fields column
that is expected by the PHI audit system for HIPAA compliance.
"""

import asyncio
import asyncpg
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings

async def fix_phi_access_logs_schema():
    """Fix the phi_access_logs table schema by adding accessed_fields column."""
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
            AND column_name = 'accessed_fields'
            ORDER BY column_name;
        """)
        
        if result:
            print("✓ accessed_fields column already exists:")
            for row in result:
                print(f"  - {row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']})")
            return True
        
        print("accessed_fields column missing - adding it...")
        
        # 2. Add accessed_fields column
        print("\n2. Adding accessed_fields column...")
        
        await conn.execute("""
            ALTER TABLE phi_access_logs 
            ADD COLUMN accessed_fields VARCHAR[] DEFAULT '{}';
        """)
        
        print("  ✓ accessed_fields column added as VARCHAR[] with default empty array")
        
        # 3. Create index for efficient querying
        print("\n3. Creating index for accessed_fields queries...")
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS ix_phi_access_logs_accessed_fields 
            ON phi_access_logs USING gin(accessed_fields);
        """)
        
        print("  ✓ GIN index created for accessed_fields")
        
        # 4. Verify final schema
        print("\n4. Verifying final schema...")
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'phi_access_logs' 
            AND column_name = 'accessed_fields'
            ORDER BY column_name;
        """)
        
        print("Final schema:")
        for row in result:
            print(f"  - {row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']})")
        
        print("\n✓ PHI access logs schema fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Error fixing schema: {e}")
        return False
    finally:
        await conn.close()


if __name__ == "__main__":
    success = asyncio.run(fix_phi_access_logs_schema())
    sys.exit(0 if success else 1)