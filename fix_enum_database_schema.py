#!/usr/bin/env python3
"""
Fix Database Enum Schema for 100% Healthcare Compliance Test Pass Rate

This script addresses the root cause of PHI audit logging failures:
- Database enum case mismatch (uppercase vs lowercase)
- Missing enum values
- Schema constraint conflicts

SOC2/HIPAA/GDPR Compliance: Ensures audit logging works correctly
"""

import asyncio
import asyncpg
import os
from typing import List, Dict, Any

async def check_and_fix_dataclassification_enum():
    """
    Check and fix the dataclassification enum in the database.
    
    Root Cause: Migration 2025_08_02_0218 introduced uppercase enum values,
    but Python code uses lowercase values, causing insertion failures.
    """
    
    # Database connection
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/iris_healthcare_test")
    
    print("🔍 PHASE 1: Database Enum Schema Verification & Fix")
    print("=" * 60)
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database")
        
        # Step 1: Check current enum values
        print("\n📋 Step 1: Checking current dataclassification enum values...")
        
        enum_query = """
        SELECT enumlabel 
        FROM pg_enum 
        WHERE enumtypid = (
            SELECT oid FROM pg_type WHERE typname = 'dataclassification'
        )
        ORDER BY enumlabel;
        """
        
        current_values = await conn.fetch(enum_query)
        print(f"Current enum values: {[row['enumlabel'] for row in current_values]}")
        
        # Expected values (lowercase as per original schema)
        expected_values = ['public', 'internal', 'confidential', 'restricted', 'phi', 'pii']
        current_enum_values = [row['enumlabel'] for row in current_values]
        
        # Step 2: Add missing lowercase values
        print("\n🔧 Step 2: Adding missing lowercase enum values...")
        
        for value in expected_values:
            if value not in current_enum_values:
                try:
                    add_value_query = f"ALTER TYPE dataclassification ADD VALUE IF NOT EXISTS '{value}'"
                    await conn.execute(add_value_query)
                    print(f"✅ Added enum value: '{value}'")
                except Exception as e:
                    print(f"⚠️  Could not add '{value}': {e}")
        
        # Step 3: Check for uppercase duplicates
        print("\n📋 Step 3: Checking for problematic uppercase values...")
        
        uppercase_values = ['PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED', 'PHI', 'PII']
        problematic_values = []
        
        for uppercase_val in uppercase_values:
            if uppercase_val in current_enum_values:
                problematic_values.append(uppercase_val)
                print(f"⚠️  Found problematic uppercase value: '{uppercase_val}'")
        
        if problematic_values:
            print(f"\n🚨 WARNING: Found {len(problematic_values)} uppercase enum values!")
            print("   These may cause conflicts. Consider recreating the enum type.")
            
            # Option 1: Try to remove uppercase values (PostgreSQL doesn't support this directly)
            print("\n💡 SOLUTION: We'll ensure lowercase values exist and update application code")
            print("   to handle both cases gracefully.")
        
        # Step 4: Verify final state
        print("\n✅ Step 4: Verifying final enum state...")
        final_values = await conn.fetch(enum_query)
        final_enum_list = [row['enumlabel'] for row in final_values]
        print(f"Final enum values: {final_enum_list}")
        
        # Step 5: Test enum insertion
        print("\n🧪 Step 5: Testing enum value insertion...")
        
        test_table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'enum_test_temp'
            );
        """)
        
        if not test_table_exists:
            await conn.execute("""
                CREATE TEMP TABLE enum_test_temp (
                    id SERIAL PRIMARY KEY,
                    classification dataclassification
                );
            """)
        
        # Test inserting lowercase values (what our Python code uses)
        test_values = ['phi', 'internal', 'confidential']
        successful_insertions = []
        failed_insertions = []
        
        for test_val in test_values:
            try:
                await conn.execute(
                    "INSERT INTO enum_test_temp (classification) VALUES ($1)",
                    test_val
                )
                successful_insertions.append(test_val)
                print(f"✅ Successfully inserted: '{test_val}'")
            except Exception as e:
                failed_insertions.append((test_val, str(e)))
                print(f"❌ Failed to insert '{test_val}': {e}")
        
        # Summary
        print(f"\n📊 ENUM FIX SUMMARY:")
        print(f"   Current enum values: {len(final_enum_list)}")
        print(f"   Expected values present: {len([v for v in expected_values if v in final_enum_list])}")
        print(f"   Successful test insertions: {len(successful_insertions)}")
        print(f"   Failed test insertions: {len(failed_insertions)}")
        
        if len(successful_insertions) == len(test_values):
            print("✅ DATABASE ENUM STATUS: READY FOR PHI AUDIT LOGGING")
            return True
        else:
            print("❌ DATABASE ENUM STATUS: NEEDS ADDITIONAL FIXES")
            return False
            
    except Exception as e:
        print(f"❌ Database connection or operation failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            await conn.close()
            print("🔌 Database connection closed")

async def verify_phi_access_log_table():
    """
    Verify the PHI access log table schema matches our application expectations.
    """
    print("\n🔍 PHASE 2: PHI Access Log Table Schema Verification")
    print("=" * 60)
    
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/iris_healthcare_test")
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Check if phi_access_logs table exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'phi_access_logs'
            );
        """)
        
        if not table_exists:
            print("❌ phi_access_logs table does not exist!")
            return False
        
        print("✅ phi_access_logs table exists")
        
        # Check data_classification column
        column_info = await conn.fetch("""
            SELECT column_name, data_type, udt_name, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'phi_access_logs' 
            AND column_name = 'data_classification';
        """)
        
        if column_info:
            col = column_info[0]
            print(f"📋 data_classification column:")
            print(f"   Type: {col['data_type']}")
            print(f"   UDT Name: {col['udt_name']}")
            print(f"   Nullable: {col['is_nullable']}")
            
            if col['udt_name'] == 'dataclassification':
                print("✅ Column uses correct enum type")
                return True
            else:
                print(f"❌ Column uses wrong type: {col['udt_name']}")
                return False
        else:
            print("❌ data_classification column not found!")
            return False
            
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            await conn.close()

async def main():
    """
    Main function to fix database schema issues for 100% test pass rate.
    """
    print("🎯 COMPREHENSIVE DATABASE FIX FOR 100% HEALTHCARE COMPLIANCE TEST SUCCESS")
    print("=" * 80)
    print("Target: Fix PHI audit logging failures causing 500 errors")
    print("Compliance: SOC2 Type 2, HIPAA, GDPR, FHIR R4")
    print("=" * 80)
    
    # Phase 1: Fix enum schema
    enum_fixed = await check_and_fix_dataclassification_enum()
    
    # Phase 2: Verify table schema  
    table_verified = await verify_phi_access_log_table()
    
    # Final assessment
    print(f"\n🎯 FINAL ASSESSMENT:")
    print(f"   Enum Schema Fixed: {'✅' if enum_fixed else '❌'}")
    print(f"   Table Schema Verified: {'✅' if table_verified else '❌'}")
    
    if enum_fixed and table_verified:
        print("\n🚀 DATABASE STATUS: READY FOR 100% TEST PASS RATE!")
        print("   Next steps:")
        print("   1. Run the healthcare compliance tests")
        print("   2. PHI audit logging should now work correctly")
        print("   3. Access control should return proper 403 codes")
        print("   4. Consent management should serialize correctly")
        return True
    else:
        print("\n⚠️  DATABASE STATUS: NEEDS ADDITIONAL FIXES")
        print("   Review the output above for specific issues to address")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)