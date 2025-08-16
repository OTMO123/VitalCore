#!/usr/bin/env python3
"""
Fix audit event type enum to include USER_LOGIN
"""

import asyncio
import asyncpg

async def fix_audit_enum():
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        print("Fixing audit event type enum...")
        
        # Check current enum values
        current_values = await conn.fetch("""
            SELECT e.enumlabel
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'auditeventtype'
            ORDER BY e.enumsortorder
        """)
        
        print("Current audit event type enum values:")
        enum_values = [row['enumlabel'] for row in current_values]
        for value in enum_values:
            print(f"  - {value}")
        
        # Add missing enum values that the application expects
        missing_values = [
            'USER_LOGIN',
            'USER_LOGOUT', 
            'USER_LOGIN_FAILED',
            'USER_CREATED',
            'USER_UPDATED',
            'USER_DELETED',
            'PHI_ACCESSED',
            'PHI_CREATED',
            'PHI_UPDATED',
            'PHI_DELETED',
            'PHI_EXPORTED',
            'PATIENT_CREATED',
            'PATIENT_UPDATED',
            'PATIENT_ACCESSED',
            'PATIENT_SEARCH',
            'DOCUMENT_CREATED',
            'DOCUMENT_ACCESSED',
            'DOCUMENT_UPDATED',
            'DOCUMENT_DELETED',
            'CONSENT_GRANTED',
            'CONSENT_WITHDRAWN',
            'CONSENT_UPDATED',
            'SYSTEM_ACCESS',
            'CONFIG_CHANGED',
            'SECURITY_VIOLATION',
            'DATA_BREACH_DETECTED'
        ]
        
        added_count = 0
        for value in missing_values:
            if value not in enum_values:
                print(f"Adding enum value: {value}")
                await conn.execute(f"ALTER TYPE auditeventtype ADD VALUE '{value}'")
                added_count += 1
            else:
                print(f"Enum value {value} already exists")
        
        print(f"\nAdded {added_count} new enum values")
        
        # Verify final enum values
        final_values = await conn.fetch("""
            SELECT e.enumlabel
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'auditeventtype'
            ORDER BY e.enumsortorder
        """)
        
        print(f"\nFinal audit event type enum values ({len(final_values)} total):")
        for row in final_values:
            print(f"  - {row['enumlabel']}")
        
        print("\nAudit enum fix completed!")
        
    except Exception as e:
        print(f"Error fixing audit enum: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_audit_enum())