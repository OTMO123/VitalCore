#!/usr/bin/env python3
"""
Add missing columns to users table to match SQLAlchemy model
"""

import asyncio
import asyncpg

async def add_missing_columns():
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        print("Adding missing columns to users table...")
        
        # Check which columns exist
        existing_columns = await conn.fetch("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users'
        """)
        column_names = [col['column_name'] for col in existing_columns]
        
        # Add missing columns that the SQLAlchemy model expects
        missing_columns = [
            ("mfa_secret", "VARCHAR(255)"),
            ("last_login_at", "TIMESTAMP"),
            ("last_login_ip", "INET"),
        ]
        
        for col_name, col_type in missing_columns:
            if col_name not in column_names:
                print(f"Adding column: {col_name} ({col_type})")
                await conn.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            else:
                print(f"Column {col_name} already exists")
        
        print("All missing columns added successfully!")
        
        # Show final schema
        final_columns = await conn.fetch("""
            SELECT column_name, data_type FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        
        print("\nFinal users table schema:")
        for col in final_columns:
            print(f"  {col['column_name']}: {col['data_type']}")
        
    except Exception as e:
        print(f"Error adding columns: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_missing_columns())