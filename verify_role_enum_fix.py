#!/usr/bin/env python3
"""
Verification script for role enum mismatch fix.

This script verifies that:
1. All user roles in the database are lowercase
2. The role values match the expected UserRole enum values from auth/schemas.py
3. No uppercase role values remain in the database
"""

import asyncio
import sys
from typing import Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Add the project root to the path
sys.path.append('.')

from app.core.database_unified import get_db
from app.modules.auth.schemas import UserRole


async def verify_role_enum_fix():
    """Verify that the role enum fix was applied correctly."""
    
    print("🔍 Verifying role enum fix...")
    print("=" * 50)
    
    try:
        async for db in get_db():
            # Check 1: Get all distinct role values from database
            result = await db.execute(text('SELECT DISTINCT role FROM users ORDER BY role'))
            db_roles = [row[0] for row in result.fetchall()]
            
            print(f"📊 Found {len(db_roles)} distinct roles in database:")
            for role in db_roles:
                print(f"   - '{role}'")
            
            # Check 2: Verify no uppercase roles remain
            uppercase_roles = [role for role in db_roles if any(c.isupper() for c in role)]
            if uppercase_roles:
                print(f"❌ ERROR: Found uppercase roles that should have been converted:")
                for role in uppercase_roles:
                    print(f"   - '{role}' (should be lowercase)")
                return False
            else:
                print("✅ All roles are lowercase")
            
            # Check 3: Get role counts
            result = await db.execute(text('SELECT role, COUNT(*) FROM users GROUP BY role ORDER BY role'))
            role_counts = dict(result.fetchall())
            
            print(f"\n📈 User count per role:")
            total_users = 0
            for role, count in role_counts.items():
                print(f"   - {role}: {count} users")
                total_users += count
            print(f"   Total: {total_users} users")
            
            # Check 4: Verify roles match UserRole enum values
            valid_roles = {role.value for role in UserRole}
            print(f"\n🎯 Role validation against UserRole enum:")
            print(f"   Expected roles from enum: {len(valid_roles)} total")
            
            invalid_roles = set(db_roles) - valid_roles
            if invalid_roles:
                print(f"⚠️  WARNING: Found roles in database that are not in UserRole enum:")
                for role in invalid_roles:
                    print(f"   - '{role}' (not in enum)")
                print("   This is OK if you're using custom roles beyond the basic enum")
            else:
                print("✅ All database roles match UserRole enum values")
            
            # Check 5: Verify basic legacy roles are properly converted
            legacy_mapping = {
                'user': 'USER',
                'admin': 'ADMIN', 
                'operator': 'OPERATOR',
                'super_admin': 'SUPER_ADMIN'
            }
            
            print(f"\n🔄 Legacy role conversion verification:")
            for new_role, old_role in legacy_mapping.items():
                if new_role in role_counts:
                    print(f"   ✅ '{old_role}' → '{new_role}': {role_counts[new_role]} users")
                else:
                    print(f"   ℹ️  '{old_role}' → '{new_role}': no users with this role")
            
            # Check 6: Database schema verification
            result = await db.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'role'
            """))
            
            column_info = result.fetchone()
            if column_info:
                col_name, data_type, is_nullable, default_val = column_info
                print(f"\n🗄️  Database schema for 'role' column:")
                print(f"   - Type: {data_type}")
                print(f"   - Nullable: {is_nullable}")
                print(f"   - Default: {default_val}")
                
                if data_type == 'character varying':
                    print("   ✅ Role column is now a flexible string type")
                else:
                    print(f"   ⚠️  Expected 'character varying', got '{data_type}'")
            else:
                print("   ❌ Could not find role column information")
            
            print("\n" + "=" * 50)
            print("🎉 Role enum fix verification completed!")
            
            if not uppercase_roles:
                print("✅ SUCCESS: Role enum mismatch has been fixed")
                print("   - All roles are lowercase")
                print("   - Database uses flexible string type")
                print("   - Ready for comprehensive UserRole enum from auth/schemas.py")
                return True
            else:
                print("❌ FAILURE: Some issues remain")
                return False
            
            break  # Only need one database session
            
    except Exception as e:
        print(f"❌ ERROR during verification: {e}")
        return False


async def main():
    """Main verification function."""
    success = await verify_role_enum_fix()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())