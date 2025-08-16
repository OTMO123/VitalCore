#!/usr/bin/env python3
"""
Fix missing profile_data column in users table.
Enterprise Healthcare Compliance Fix for SOC2 Type II + HIPAA.
"""

import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings

async def fix_missing_column():
    """Add missing profile_data column to users table."""
    settings = get_settings()
    
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    try:
        async with engine.begin() as conn:
            # Check if column exists
            check_column_sql = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'profile_data'
            """)
            
            result = await conn.execute(check_column_sql)
            column_exists = result.fetchone()
            
            if column_exists:
                print("✅ profile_data column already exists in users table")
                return True
            
            # Add missing column
            print("🔧 Adding missing profile_data column to users table...")
            
            add_column_sql = text("""
                ALTER TABLE users 
                ADD COLUMN profile_data JSONB
            """)
            
            await conn.execute(add_column_sql)
            print("✅ Successfully added profile_data column to users table")
            
            # Verify column was added
            verify_result = await conn.execute(check_column_sql)
            if verify_result.fetchone():
                print("✅ Column verification successful")
                return True
            else:
                print("❌ Column verification failed")
                return False
                
    except Exception as e:
        print(f"❌ Error fixing missing column: {e}")
        return False
    finally:
        await engine.dispose()

async def main():
    """Main function to fix missing database column."""
    print("🏥 Enterprise Healthcare Database Fix")
    print("SOC2 Type II + HIPAA Compliance - Adding missing profile_data column")
    print("=" * 70)
    
    success = await fix_missing_column()
    
    if success:
        print("✅ Database fix completed successfully!")
        sys.exit(0)
    else:
        print("❌ Database fix failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())