"""
Example integration tests demonstrating the comprehensive pytest configuration.

This module shows how to use the various fixtures and markers for different
types of integration testing scenarios.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

from app.core.database_unified import User, AuditLog
from app.core.event_bus import EventBus, Event, EventType
from app.modules.auth.service import AuthService
from app.modules.iris_api.client import IRISAPIClient


# ==================== Database Integration Tests ====================

@pytest.mark.integration
@pytest.mark.database
@pytest_asyncio.fixture
@pytest.mark.asyncio
async def test_database_integration(db_session: AsyncSession, test_user: User):
    """Test database operations with real database session."""
    # Test user creation
    assert test_user.id is not None
    assert test_user.username == "testuser"
    assert test_user.is_active is True
    
    # Test user retrieval
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.id == test_user.id))
    retrieved_user = result.scalar_one_or_none()
    
    assert retrieved_user is not None
    assert retrieved_user.username == test_user.username
    assert retrieved_user.email == test_user.email


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.audit
@pytest_asyncio.fixture
@pytest.mark.asyncio
async def test_audit_log_creation(db_session: AsyncSession, test_user: User):
    """Test audit log creation and retrieval."""
    # Create audit log
    audit_log = AuditLog(
        event_type="test.integration",
        user_id=str(test_user.id),
        action="test_action",
        outcome="success",
        event_data={"test": "integration_test"}
    )
    
    db_session.add(audit_log)
    await db_session.commit()
    await db_session.refresh(audit_log)
    
    # Verify audit log
    assert audit_log.id is not None
    assert audit_log.event_type == "test.integration"
    assert audit_log.user_id == str(test_user.id)
    assert audit_log.event_data["test"] == "integration_test"


# ==================== Event Bus Integration Tests ====================

@pytest.mark.integration
@pytest.mark.event_bus
@pytest_asyncio.fixture
@pytest.mark.asyncio
async def test_event_bus_integration(test_event_bus: EventBus, mock_event_handler: AsyncMock):
    """Test event bus with real async operations."""
    # Subscribe to events
    test_event_bus.subscribe(EventType.USER_LOGIN_SUCCESS, mock_event_handler)
    
    # Publish event
    test_event = Event(
        event_type=EventType.USER_LOGIN_SUCCESS,
        user_id="integration_test_user",
        action="login",
        outcome="success"
    )
    
    await test_event_bus.publish(test_event)
    
    # Wait for event processing
    import asyncio
    await asyncio.sleep(0.1)
    
    # Verify handler was called
    mock_event_handler.assert_called_once()
    called_event = mock_event_handler.call_args[0][0]
    assert called_event.event_type == EventType.USER_LOGIN_SUCCESS
    assert called_event.user_id == "integration_test_user"


# ==================== API Integration Tests ====================

@pytest.mark.integration
@pytest.mark.api
@pytest_asyncio.fixture
@pytest.mark.asyncio
async def test_api_authentication_flow(
    async_test_client: AsyncClient,
    db_session: AsyncSession,
    test_user: User
):
    """Test complete authentication flow."""
    # Test login
    login_data = {
        "username": test_user.username,
        "password": "testpassword"
    }
    
    response = await async_test_client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    
    # Test authenticated request
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    profile_response = await async_test_client.get("/auth/profile", headers=headers)
    
    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    assert profile_data["username"] == test_user.username


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.security
@pytest_asyncio.fixture
@pytest.mark.asyncio
async def test_api_security_headers(async_test_client: AsyncClient):
    """Test that API responses include required security headers."""
    response = await async_test_client.get("/health")
    
    # Check for security headers
    expected_headers = [
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection"
    ]
    
    for header in expected_headers:
        assert header in response.headers, f"Missing security header: {header}"


# ==================== IRIS API Integration Tests ====================

@pytest.mark.integration
@pytest.mark.iris_api
@pytest.mark.mock
@pytest_asyncio.fixture
@pytest.mark.asyncio
async def test_iris_api_client_integration(mock_iris_api_client: AsyncMock):
    """Test IRIS API client with mocked responses."""
    # Test user data retrieval
    user_data = await mock_iris_api_client.get_user_data("test_user_123")
    
    assert user_data is not None
    assert user_data["user_id"] == "test_user"
    assert "name" in user_data
    assert "email" in user_data
    
    # Verify the mock was called correctly
    mock_iris_api_client.get_user_data.assert_called_once_with("test_user_123")


@pytest.mark.integration
@pytest.mark.iris_api
@pytest.mark.performance
@pytest_asyncio.fixture
@pytest.mark.asyncio
async def test_iris_api_performance(mock_iris_api_client: AsyncMock, performance_timer):
    """Test IRIS API performance with timing."""
    # Configure mock to simulate delay
    import asyncio
    
    async def slow_response(*args, **kwargs):
        await asyncio.sleep(0.1)  # 100ms delay
        return {"status": "success", "data": "test"}
    
    mock_iris_api_client.get_user_data.side_effect = slow_response
    
    # Time the API call
    performance_timer.start()
    result = await mock_iris_api_client.get_user_data("test_user")
    performance_timer.stop()
    
    # Assert performance requirements
    assert performance_timer.elapsed is not None
    assert performance_timer.elapsed < 1.0, "API call took too long"
    assert result["status"] == "success"


# ==================== Service Integration Tests ====================

@pytest.mark.integration
@pytest.mark.auth
@pytest_asyncio.fixture
@pytest.mark.asyncio
async def test_auth_service_integration(
    db_session: AsyncSession,
    mock_auth_service: AsyncMock,
    test_user: User
):
    """Test authentication service integration."""
    # Test user authentication
    is_authenticated = await mock_auth_service.authenticate_user(
        test_user.username, "testpassword"
    )
    
    assert is_authenticated is True
    mock_auth_service.authenticate_user.assert_called_once_with(
        test_user.username, "testpassword"
    )


# ==================== End-to-End Integration Tests ====================

@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.slow
@pytest_asyncio.fixture
@pytest.mark.asyncio
async def test_complete_user_workflow(
    async_test_client: AsyncClient,
    db_session: AsyncSession,
    test_event_bus: EventBus,
    mock_event_handler: AsyncMock
):
    """Test complete user workflow from registration to data access."""
    # Subscribe to audit events
    test_event_bus.subscribe(EventType.USER_LOGIN_SUCCESS, mock_event_handler)
    
    # 1. Register new user
    registration_data = {
        "username": "integration_user",
        "email": "integration@example.com",
        "password": "securepassword"
    }
    
    register_response = await async_test_client.post("/auth/register", json=registration_data)
    assert register_response.status_code == 201
    
    # 2. Login with new user
    login_data = {
        "username": "integration_user",
        "password": "securepassword"
    }
    
    login_response = await async_test_client.post("/auth/login", json=login_data)
    assert login_response.status_code == 200
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Access protected resource
    profile_response = await async_test_client.get("/auth/profile", headers=headers)
    assert profile_response.status_code == 200
    
    profile = profile_response.json()
    assert profile["username"] == "integration_user"
    
    # 4. Verify audit logging occurred
    import asyncio
    await asyncio.sleep(0.1)  # Allow event processing
    
    # Should have login event
    assert mock_event_handler.call_count >= 1


# ==================== Performance Integration Tests ====================

@pytest.mark.integration
@pytest.mark.performance
@pytest.mark.slow
@pytest_asyncio.fixture
@pytest.mark.asyncio
async def test_database_performance(db_session: AsyncSession):
    """Test database performance with bulk operations."""
    import time
    
    # Test bulk user creation
    users = []
    start_time = time.perf_counter()
    
    for i in range(100):
        user = User(
            username=f"perf_user_{i}",
            email=f"perf_user_{i}@example.com",
            hashed_password="hashed_password",
            role="user"
        )
        users.append(user)
    
    db_session.add_all(users)
    await db_session.commit()
    
    end_time = time.perf_counter()
    creation_time = end_time - start_time
    
    # Assert performance requirements
    assert creation_time < 5.0, f"Bulk user creation took {creation_time:.2f}s, expected < 5s"
    
    # Test bulk query performance
    from sqlalchemy import select
    
    start_time = time.perf_counter()
    result = await db_session.execute(select(User).where(User.username.like("perf_user_%")))
    retrieved_users = result.scalars().all()
    end_time = time.perf_counter()
    
    query_time = end_time - start_time
    
    assert len(retrieved_users) == 100
    assert query_time < 1.0, f"Bulk query took {query_time:.2f}s, expected < 1s"


# ==================== Container Integration Tests ====================

@pytest.mark.integration
@pytest.mark.requires_containers
@pytest_asyncio.fixture
@pytest.mark.asyncio
async def test_with_real_containers(container_db_session: AsyncSession):
    """Test using real PostgreSQL container."""
    # This test would only run if testcontainers is available
    # and containers are started
    
    # Test basic database operations with real PostgreSQL
    test_user = User(
        username="container_user",
        email="container@example.com",
        hashed_password="hashed_password",
        role="user"
    )
    
    container_db_session.add(test_user)
    await container_db_session.commit()
    await container_db_session.refresh(test_user)
    
    assert test_user.id is not None
    assert test_user.username == "container_user"


# ==================== Regression Tests ====================

@pytest.mark.integration
@pytest.mark.regression
@pytest_asyncio.fixture
@pytest.mark.asyncio
async def test_user_password_hash_regression(db_session: AsyncSession):
    """Regression test for password hashing issue."""
    from app.core.security import verify_password, get_password_hash
    
    # Test known password hash format
    password = "test_password_123"
    hashed = get_password_hash(password)
    
    # Verify hash format hasn't changed
    assert hashed.startswith("$2b$")
    assert len(hashed) > 50
    
    # Verify password verification still works
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


@pytest.mark.integration
@pytest.mark.regression
@pytest_asyncio.fixture
@pytest.mark.asyncio
async def test_audit_log_retention_regression(db_session: AsyncSession):
    """Regression test for audit log retention functionality."""
    # Create old audit logs
    old_date = datetime.utcnow() - timedelta(days=400)  # > 1 year old
    
    old_log = AuditLog(
        event_type="test.old",
        action="old_action",
        outcome="success",
        created_at=old_date
    )
    
    db_session.add(old_log)
    await db_session.commit()
    
    # Verify old log exists
    from sqlalchemy import select
    result = await db_session.execute(
        select(AuditLog).where(AuditLog.event_type == "test.old")
    )
    retrieved_log = result.scalar_one_or_none()
    
    assert retrieved_log is not None
    assert retrieved_log.created_at.date() == old_date.date()