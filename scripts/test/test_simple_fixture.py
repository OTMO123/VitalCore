#!/usr/bin/env python3
"""
Simple test to verify the fixed fixtures work
"""
import pytest
import pytest_asyncio
import asyncio
import secrets
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

# Import the fixtures and models
import sys
sys.path.append('/mnt/c/Users/aurik/Code_Projects/2_scraper')

from app.core.database_unified import User, Role
from app.tests.conftest import db_session
from app.tests.integration.test_iris_api_comprehensive import isolated_db_transaction, iris_integration_users

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture  
async def simple_isolated_transaction(db_session):
    """Simple isolated transaction fixture for testing"""
    transaction = await db_session.begin()
    try:
        yield db_session
    finally:
        await transaction.rollback()

async def test_role_creation_isolation(simple_isolated_transaction):
    """Test that role creation works with proper isolation"""
    session = simple_isolated_transaction
    test_run_id = secrets.token_hex(4)
    
    # Try to create a role
    role_name = f"test_role_{test_run_id}"
    
    # Check if role exists
    result = await session.execute(
        select(Role).where(Role.name == role_name)
    )
    existing_role = result.scalar_one_or_none()
    
    if existing_role is None:
        # Create new role
        role = Role(name=role_name, description="Test role")
        session.add(role)
        await session.flush()
        
        # Verify it was created
        result = await session.execute(
            select(Role).where(Role.name == role_name)
        )
        created_role = result.scalar_one()
        assert created_role is not None
        assert created_role.name == role_name
        print(f"✓ Role {role_name} created successfully")
    else:
        print(f"✓ Role {role_name} already exists")

async def test_user_creation_with_unique_id(simple_isolated_transaction):
    """Test that user creation works with unique identifiers"""
    session = simple_isolated_transaction
    test_run_id = secrets.token_hex(4)
    
    # Create a unique user
    username = f"test_user_{test_run_id}"
    email = f"test_{test_run_id}@example.com"
    
    user = User(
        username=username,
        email=email,
        password_hash="$2b$12$test.hash.for.testing",
        is_active=True,
        role="user"
    )
    
    session.add(user)
    await session.flush()
    
    # Verify user was created
    result = await session.execute(
        select(User).where(User.username == username)
    )
    created_user = result.scalar_one()
    assert created_user is not None
    assert created_user.username == username
    assert created_user.email == email
    print(f"✓ User {username} created successfully")

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])