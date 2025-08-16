#!/usr/bin/env python3
"""
Fix enum case mismatch in database
"""

import asyncio
import asyncpg

async def fix_enum_case():
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        print("Fixing enum case mismatch...")
        
        # Update role values to match enum
        role_mapping = {
            'admin': 'ADMIN',
            'user': 'USER', 
            'super_admin': 'SUPER_ADMIN',
            'operator': 'OPERATOR'
        }
        
        for old_role, new_role in role_mapping.items():
            result = await conn.execute(f"UPDATE users SET role = '{new_role}' WHERE role = '{old_role}'")
            count = int(result.split()[-1])
            if count > 0:
                print(f"Updated {count} users from '{old_role}' to '{new_role}'")
        
        # Check final role values
        print("\nFinal role values in users table:")
        roles = await conn.fetch("SELECT DISTINCT role FROM users")
        for role in roles:
            print(f"  - '{role['role']}'")
            
        print("Enum case mismatch fixed!")
        
    except Exception as e:
        print(f"Error fixing enum case: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_enum_case())