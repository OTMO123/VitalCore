#!/usr/bin/env python3
"""
Check the actual structure of the users table.
"""
import asyncio
import sys
import logging
from sqlalchemy import text

# Suppress SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

from app.core.database import get_db

async def check_users_table():
    """Check what columns exist in the users table."""
    print("Checking users table structure...")
    
    async for session in get_db():
        try:
            # Get table structure
            result = await session.execute(
                text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    ORDER BY ordinal_position
                """)
            )
            columns = result.fetchall()
            
            if columns:
                print("\nUsers table columns:")
                for column in columns:
                    print(f"  - {column[0]}: {column[1]} (nullable: {column[2]})")
            else:
                print("\nNo users table found or no columns returned")
                
            # Also check if table exists at all
            result = await session.execute(
                text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
            )
            tables = result.fetchall()
            
            print(f"\nAll tables in database:")
            for table in tables:
                print(f"  - {table[0]}")
                
        except Exception as e:
            print(f"[ERROR] Error checking table: {e}")
            return False
        finally:
            break
            
    return True

if __name__ == "__main__":
    success = asyncio.run(check_users_table())
    sys.exit(0 if success else 1)