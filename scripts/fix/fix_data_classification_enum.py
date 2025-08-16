#!/usr/bin/env python3
"""
Fix data classification enum to include INTERNAL
"""

import asyncio
import asyncpg

async def fix_data_classification_enum():
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        print("Fixing data classification enum...")
        
        # Check current enum values
        current_values = await conn.fetch("""
            SELECT e.enumlabel
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'dataclassification'
            ORDER BY e.enumsortorder
        """)
        
        print("Current data classification enum values:")
        enum_values = [row['enumlabel'] for row in current_values]
        for value in enum_values:
            print(f"  - {value}")
        
        # Add missing enum values that the application expects
        missing_values = [
            'INTERNAL'  # This is the one causing the error
        ]
        
        added_count = 0
        for value in missing_values:
            if value not in enum_values:
                print(f"Adding enum value: {value}")
                await conn.execute(f"ALTER TYPE dataclassification ADD VALUE '{value}'")
                added_count += 1
            else:
                print(f"Enum value {value} already exists")
        
        print(f"\nAdded {added_count} new enum values")
        
        # Verify final enum values
        final_values = await conn.fetch("""
            SELECT e.enumlabel
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'dataclassification'
            ORDER BY e.enumsortorder
        """)
        
        print(f"\nFinal data classification enum values ({len(final_values)} total):")
        for row in final_values:
            print(f"  - {row['enumlabel']}")
        
        print("\nData classification enum fix completed!")
        
    except Exception as e:
        print(f"Error fixing data classification enum: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_data_classification_enum())