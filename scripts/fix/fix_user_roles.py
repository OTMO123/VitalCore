#!/usr/bin/env python3
"""
Fix User Roles - Convert uppercase roles to lowercase
This script fixes the UserRole enum mismatch issue where database has 'USER', 'ADMIN', 'OPERATOR'
but the UserRole enum expects 'user', 'admin', 'operator'
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import structlog

logger = structlog.get_logger()


async def fix_user_roles():
    """Fix uppercase roles in the database."""
    logger.info("Starting user role fix")
    
    try:
        engine = create_async_engine(
            'postgresql+asyncpg://postgres:healthcare_2024@localhost:5432/healthcare_prod'
        )
        
        async with engine.begin() as conn:
            # Check current roles
            logger.info("Checking for users with uppercase roles")
            result = await conn.execute(
                text("SELECT id, email, username, role FROM users WHERE role IN ('ADMIN', 'USER', 'OPERATOR')")
            )
            rows = result.fetchall()
            
            if not rows:
                logger.info("No users with uppercase roles found")
                return
            
            logger.info("Found users with uppercase roles", count=len(rows))
            for row in rows:
                logger.info("User with uppercase role", 
                          id=str(row[0]), 
                          email=row[1], 
                          username=row[2], 
                          role=row[3])
            
            # Fix the roles
            logger.info("Converting uppercase roles to lowercase")
            
            admin_result = await conn.execute(
                text("UPDATE users SET role = 'admin' WHERE role = 'ADMIN'")
            )
            logger.info("Fixed ADMIN roles", count=admin_result.rowcount)
            
            user_result = await conn.execute(
                text("UPDATE users SET role = 'user' WHERE role = 'USER'")
            )
            logger.info("Fixed USER roles", count=user_result.rowcount)
            
            operator_result = await conn.execute(
                text("UPDATE users SET role = 'operator' WHERE role = 'OPERATOR'")
            )
            logger.info("Fixed OPERATOR roles", count=operator_result.rowcount)
            
            # Verify the fix
            logger.info("Verifying role fixes")
            verify_result = await conn.execute(
                text("SELECT id, email, username, role FROM users")
            )
            verify_rows = verify_result.fetchall()
            
            logger.info("All users after fix:")
            for row in verify_rows:
                logger.info("User role", 
                          id=str(row[0]), 
                          email=row[1], 
                          username=row[2], 
                          role=row[3])
            
            logger.info("User role fix completed successfully")
            
        await engine.dispose()
        
    except Exception as e:
        logger.error("Failed to fix user roles", error=str(e))
        raise


async def main():
    """Main execution function."""
    try:
        await fix_user_roles()
        print("\nUser role fix completed successfully!")
        print("All user roles have been converted to lowercase format.")
        
    except Exception as e:
        logger.error("User role fix failed", error=str(e))
        print(f"\nFailed to fix user roles: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Configure logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the fix
    asyncio.run(main())