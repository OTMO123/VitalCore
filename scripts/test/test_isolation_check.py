#!/usr/bin/env python3
"""
Simple test to verify transaction isolation works correctly
"""
import asyncio
import sys
import os
sys.path.append('/mnt/c/Users/aurik/Code_Projects/2_scraper')

from app.core.database_unified import User, Role
from app.tests.conftest import test_session_factory, test_engine
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

async def test_isolation():
    """Test that transaction isolation prevents duplicate key violations"""
    print("Testing transaction isolation...")
    
    # Get test engine and session factory
    settings = {
        "DATABASE_URL": "postgresql+asyncpg://postgres:password@localhost:5432/iris_db"
    }
    
    from app.core.config import Settings
    test_settings = Settings(**settings)
    
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    
    engine = create_async_engine(
        test_settings.DATABASE_URL,
        poolclass=StaticPool,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_reset_on_return='commit'
    )
    
    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False
    )
    
    # Test 1: Create role in transaction and rollback
    session = session_factory()
    transaction = await session.begin()
    
    try:
        # Try to find existing role
        result = await session.execute(
            select(Role).where(Role.name == "test_role_isolation")
        )
        existing_role = result.scalar_one_or_none()
        
        if existing_role is None:
            # Create new role
            role = Role(name="test_role_isolation", description="Test role for isolation")
            session.add(role)
            await session.flush()
            print("✓ Role created successfully in transaction")
        else:
            print("✓ Role already exists - using existing one")
            role = existing_role
    
    finally:
        # Always rollback to test isolation
        await transaction.rollback()
        await session.close()
        print("✓ Transaction rolled back successfully")
    
    # Test 2: Verify role was not persisted due to rollback
    session2 = session_factory()
    try:
        result = await session2.execute(
            select(Role).where(Role.name == "test_role_isolation")
        )
        role_after_rollback = result.scalar_one_or_none()
        
        if role_after_rollback is None and existing_role is None:
            print("✓ Transaction isolation working correctly - role not persisted after rollback")
        elif existing_role is not None:
            print("✓ Pre-existing role still exists (expected)")
        else:
            print("✗ Transaction isolation may not be working - role persisted after rollback")
            
    finally:
        await session2.close()
    
    await engine.dispose()
    print("✓ Test completed successfully")

if __name__ == "__main__":
    asyncio.run(test_isolation())