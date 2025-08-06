#!/usr/bin/env python3
"""
Direct schema fix for last_login_ip column type
Addresses Phase 1 infrastructure test failure
"""
import asyncpg
import asyncio
import sys

async def fix_last_login_ip():
    """Fix the last_login_ip column type from VARCHAR to INET"""
    conn = None
    try:
        # Connect to database
        conn = await asyncpg.connect(
            "postgresql://postgres:password@localhost:5432/iris_db"
        )
        
        # Check current column type
        result = await conn.fetchrow("""
            SELECT data_type, character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'last_login_ip'
        """)
        
        if not result:
            print("ERROR: Column 'last_login_ip' not found in users table")
            return False
            
        current_type = result['data_type']
        print(f"INFO: Current column type: {current_type}")
        
        if current_type == 'inet':
            print("SUCCESS: Column is already INET type - no changes needed")
            return True
            
        elif current_type == 'character varying':
            print("INFO: Converting VARCHAR to INET...")
            
            # First, check if there are any non-IP values
            invalid_ips = await conn.fetchval(r"""
                SELECT COUNT(*) 
                FROM users 
                WHERE last_login_ip IS NOT NULL 
                AND last_login_ip !~ '^([0-9]{1,3}\.){3}[0-9]{1,3}$|^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
            """)
            
            if invalid_ips > 0:
                print(f"WARNING: Found {invalid_ips} rows with non-IP values. Cleaning up...")
                # Set invalid IP addresses to NULL
                await conn.execute(r"""
                    UPDATE users 
                    SET last_login_ip = NULL 
                    WHERE last_login_ip IS NOT NULL 
                    AND last_login_ip !~ '^([0-9]{1,3}\.){3}[0-9]{1,3}$|^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
                """)
            
            # Convert the column type
            await conn.execute(r"""
                ALTER TABLE users 
                ALTER COLUMN last_login_ip 
                TYPE INET 
                USING CASE 
                    WHEN last_login_ip ~ '^([0-9]{1,3}\.){3}[0-9]{1,3}$|^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
                    THEN last_login_ip::INET
                    ELSE NULL
                END
            """)
            
            print("SUCCESS: Successfully converted last_login_ip to INET type")
            return True
            
        else:
            print(f"ERROR: Unexpected column type: {current_type}")
            return False
            
    except Exception as e:
        print(f"ERROR: Error fixing schema: {str(e)}")
        return False
    finally:
        if conn:
            await conn.close()

async def set_pythonpath():
    """Set PYTHONPATH environment variable"""
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Get current PYTHONPATH
    current_pythonpath = os.environ.get('PYTHONPATH', '')
    
    if current_dir not in current_pythonpath:
        if current_pythonpath:
            new_pythonpath = f"{current_dir};{current_pythonpath}"
        else:
            new_pythonpath = current_dir
            
        os.environ['PYTHONPATH'] = new_pythonpath
        print(f"SUCCESS: Set PYTHONPATH to: {new_pythonpath}")
        return True
    else:
        print(f"SUCCESS: PYTHONPATH already includes: {current_dir}")
        return True

async def main():
    """Main execution function"""
    print("Phase 1 Infrastructure Fix - Healthcare System")
    print("=" * 50)
    
    # Fix 1: Database schema
    print("\n1. Fixing database schema (last_login_ip column)...")
    schema_fixed = await fix_last_login_ip()
    
    # Fix 2: Environment variables  
    print("\n2. Setting environment variables...")
    env_fixed = await set_pythonpath()
    
    # Summary
    print("\nSUMMARY")
    print("=" * 50)
    print(f"Database schema fix: {'PASSED' if schema_fixed else 'FAILED'}")
    print(f"Environment variables: {'PASSED' if env_fixed else 'FAILED'}")
    
    if schema_fixed and env_fixed:
        print("\nAll Phase 1 infrastructure fixes applied successfully!")
        print("Ready to re-run: pytest app/tests/infrastructure/test_system_health.py -v")
        return 0
    else:
        print("\nSome fixes failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)