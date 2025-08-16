#!/usr/bin/env python3
"""
Fix users table schema to add missing profile_data column.

This script ensures the users table has the profile_data column
that is expected by the User model but missing from the database.
"""

import asyncio
import asyncpg
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings

async def fix_users_schema():
    """Fix the users table schema by adding profile_data column."""
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
        # 1. Check current users table schema
        print("\n1. Checking current users table schema...")
        
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'profile_data'
            ORDER BY column_name;
        """)
        
        if result:
            print("✓ profile_data column already exists:")
            for row in result:
                print(f"  - {row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']})")
            return True
        
        print("Profile_data column missing - adding it...")
        
        # 2. Add profile_data column
        print("\n2. Adding profile_data column...")
        
        await conn.execute("""
            ALTER TABLE users 
            ADD COLUMN profile_data JSONB DEFAULT '{}'::jsonb;
        """)
        
        print("  ✓ profile_data column added as JSONB with default empty object")
        
        # 3. Create index for JSONB queries
        print("\n3. Creating GIN index for profile_data JSONB queries...")
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS ix_users_profile_data_gin 
            ON users USING gin(profile_data);
        """)
        
        print("  ✓ GIN index created for profile_data")
        
        # 4. Verify final schema
        print("\n4. Verifying final schema...")
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'profile_data'
            ORDER BY column_name;
        """)
        
        print("Final schema:")
        for row in result:
            print(f"  - {row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']})")
        
        print("\n✓ Users table schema fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Error fixing schema: {e}")
        return False
    finally:
        await conn.close()


if __name__ == "__main__":
    success = asyncio.run(fix_users_schema())
    sys.exit(0 if success else 1)