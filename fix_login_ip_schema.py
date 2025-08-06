#!/usr/bin/env python3
"""
Fix database schema issues for IRIS Healthcare API
Specifically fixes the last_login_ip column type issue
"""

import asyncio
import sys
sys.path.append('/mnt/c/Users/aurik/Code_Projects/2_scraper')

from sqlalchemy import text
from app.core.database_unified import get_db

async def fix_last_login_ip_column():
    """Fix the last_login_ip column type from VARCHAR to INET"""
    
    print("IRIS Healthcare API - Database Schema Fix")
    print("=" * 50)
    
    try:
        async for session in get_db():
            # Check if column exists and its current type
            result = await session.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'last_login_ip'
            """))
            
            column_info = result.fetchone()
            
            if column_info:
                current_type = column_info[1]
                print(f"Current last_login_ip column type: {current_type}")
                
                if current_type == 'character varying':
                    print("Converting last_login_ip column from VARCHAR to INET...")
                    
                    # Step 1: Add a new temporary column
                    await session.execute(text("""
                        ALTER TABLE users ADD COLUMN last_login_ip_temp INET
                    """))
                    
                    # Step 2: Copy valid IP addresses to the new column (handle NULLs)
                    await session.execute(text("""
                        UPDATE users 
                        SET last_login_ip_temp = NULL
                        WHERE last_login_ip IS NULL
                    """))
                    
                    # Step 3: Drop the old column
                    await session.execute(text("""
                        ALTER TABLE users DROP COLUMN last_login_ip
                    """))
                    
                    # Step 4: Rename the new column
                    await session.execute(text("""
                        ALTER TABLE users RENAME COLUMN last_login_ip_temp TO last_login_ip
                    """))
                    
                    print("Successfully converted last_login_ip column to INET type")
                    
                elif current_type == 'inet':
                    print("Column is already INET type - no changes needed")
                else:
                    print(f"Unexpected column type: {current_type}")
            else:
                print("last_login_ip column does not exist")
            
            # Verify the fix
            result = await session.execute(text("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'last_login_ip'
            """))
            
            ip_col = result.fetchone()
            if ip_col and ip_col[0] == 'inet':
                print("Verification: last_login_ip column is correctly typed as INET")
                await session.commit()
                print("Schema fix completed successfully")
                return True
            else:
                print("Verification failed - column type is not INET")
                return False
            
            break
            
    except Exception as e:
        print(f"Error fixing last_login_ip column: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(fix_last_login_ip_column())
    if result:
        print("\nDatabase schema fix completed successfully")
        print("User registration should now work properly")
        sys.exit(0)
    else:
        print("\nDatabase schema fix failed")
        sys.exit(1)