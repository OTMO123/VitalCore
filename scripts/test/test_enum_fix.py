#!/usr/bin/env python3
"""
Test enum fix by querying database directly without enum conversion
"""

import asyncio
import sys
sys.path.append('/mnt/c/Users/aurik/Code_Projects/2_scraper')

from sqlalchemy import text
from app.core.database_unified import get_db

async def test_enum_fix():
    """Test raw SQL query to see actual data"""
    
    print("TESTING ENUM ISSUE")
    print("=" * 50)
    
    try:
        async for session in get_db():
            # Query patients directly with raw SQL
            result = await session.execute(text("SELECT id, external_id, mrn, data_classification, created_at FROM patients LIMIT 5"))
            rows = result.fetchall()
            
            print(f"Found {len(rows)} patients (raw SQL):")
            
            for row in rows:
                print(f"  ID: {row[0]}")
                print(f"  External ID: {row[1]}")
                print(f"  MRN: {row[2]}")
                print(f"  Data Classification: '{row[3]}' (type: {type(row[3])})")
                print(f"  Created: {row[4]}")
                print()
            
            # Check enum values in database
            enum_result = await session.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = (
                    SELECT oid 
                    FROM pg_type 
                    WHERE typname = 'dataclassification'
                )
                ORDER BY enumlabel;
            """))
            enum_values = [row[0] for row in enum_result.fetchall()]
            print(f"Database enum values: {enum_values}")
            
            break
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_enum_fix())
    sys.exit(0 if result else 1)