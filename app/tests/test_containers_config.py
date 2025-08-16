"""
Test containers configuration for integration testing.

This module provides test container configurations for PostgreSQL, Redis,
and other external services needed for comprehensive integration testing.
"""

import os
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
import pytest
import pytest_asyncio
from contextlib import asynccontextmanager

# Test containers imports (optional dependency)
try:
    from testcontainers.postgres import PostgresContainer
    from testcontainers.redis import RedisContainer
    from testcontainers.compose import DockerCompose
    from testcontainers.core.generic import GenericContainer
    from testcontainers.core.waiting_utils import wait_for_logs
    TESTCONTAINERS_AVAILABLE = True
except ImportError:
    TESTCONTAINERS_AVAILABLE = False

# Database and async imports
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
import redis.asyncio as redis
import httpx

from app.core.config import Settings
from app.core.database_unified import Base


class TestContainerManager:
    """Manager for test containers lifecycle."""
    
    def __init__(self):
        self.containers: Dict[str, Any] = {}
        self.services_ready = False
    
    async def start_postgres(self, postgres_version: str = "15") -> PostgresContainer:
        """Start PostgreSQL test container."""
        if not TESTCONTAINERS_AVAILABLE:
            raise ImportError("testcontainers package not available")
        
        postgres = PostgresContainer(
            image=f"postgres:{postgres_version}",
            port=5432,
            username="test_user",
            password="test_password",
            dbname="test_iris_db"
        ).with_env("POSTGRES_INITDB_ARGS", "--auth-host=trust")
        
        postgres.start()
        
        # Wait for PostgreSQL to be ready
        await self._wait_for_postgres(postgres)
        
        self.containers['postgres'] = postgres
        return postgres
    
    async def start_redis(self, redis_version: str = "7-alpine") -> RedisContainer:
        """Start Redis test container."""
        if not TESTCONTAINERS_AVAILABLE:
            raise ImportError("testcontainers package not available")
        
        redis_container = RedisContainer(
            image=f"redis:{redis_version}",
            port=6379
        )
        
        redis_container.start()
        
        # Wait for Redis to be ready
        await self._wait_for_redis(redis_container)
        
        self.containers['redis'] = redis_container
        return redis_container
    
    async def start_mock_iris_api(self):
        """Start mock IRIS API container."""
        if not TESTCONTAINERS_AVAILABLE:
            raise ImportError("testcontainers package not available")
        
        # Create a simple mock server container
        from testcontainers.core.generic import GenericContainer
        mock_api = GenericContainer(
            image="wiremock/wiremock:latest",
            exposed_ports=[8080]
        ).with_command("--port 8080 --verbose")
        
        mock_api.start()
        
        # Wait for the mock API to be ready
        await self._wait_for_http_service(
            host=mock_api.get_container_host_ip(),
            port=mock_api.get_exposed_port(8080),
            path="/__admin/health"
        )
        
        self.containers['mock_iris_api'] = mock_api
        return mock_api
    
    async def start_all_services(self) -> Dict[str, str]:
        """Start all required test services."""
        services = {}
        
        # Start PostgreSQL
        postgres = await self.start_postgres()
        postgres_url = postgres.get_connection_url().replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        services['database_url'] = postgres_url
        
        # Start Redis
        redis_container = await self.start_redis()
        redis_url = f"redis://localhost:{redis_container.get_exposed_port(6379)}/0"
        services['redis_url'] = redis_url
        
        # Start Mock IRIS API
        mock_api = await self.start_mock_iris_api()
        iris_api_url = f"http://localhost:{mock_api.get_exposed_port(8080)}"
        services['iris_api_url'] = iris_api_url
        
        self.services_ready = True
        return services
    
    def stop_all_services(self):
        """Stop all test containers."""
        for name, container in self.containers.items():
            try:
                container.stop()
            except Exception as e:
                print(f"Error stopping container {name}: {e}")
        
        self.containers.clear()
        self.services_ready = False
    
    async def _wait_for_postgres(self, postgres: PostgresContainer, timeout: int = 30):
        """Wait for PostgreSQL to be ready."""
        connection_url = postgres.get_connection_url().replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        engine = create_async_engine(connection_url)
        
        for _ in range(timeout):
            try:
                async with engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                await engine.dispose()
                return
            except Exception:
                await asyncio.sleep(1)
        
        await engine.dispose()
        raise TimeoutError("PostgreSQL container did not start within timeout")
    
    async def _wait_for_redis(self, redis_container: RedisContainer, timeout: int = 30):
        """Wait for Redis to be ready."""
        redis_url = f"redis://localhost:{redis_container.get_exposed_port(6379)}/0"
        
        for _ in range(timeout):
            try:
                redis_client = redis.from_url(redis_url)
                await redis_client.ping()
                await redis_client.close()
                return
            except Exception:
                await asyncio.sleep(1)
        
        raise TimeoutError("Redis container did not start within timeout")
    
    async def _wait_for_http_service(self, host: str, port: int, path: str = "/", timeout: int = 30):
        """Wait for HTTP service to be ready."""
        url = f"http://{host}:{port}{path}"
        
        for _ in range(timeout):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, timeout=2.0)
                    if response.status_code < 500:  # Any non-server error is considered ready
                        return
            except Exception:
                await asyncio.sleep(1)
        
        raise TimeoutError(f"HTTP service at {url} did not start within timeout")


class DockerComposeManager:
    """Manager for Docker Compose-based test environments."""
    
    def __init__(self, compose_file_path: str = "docker-compose.test.yml"):
        self.compose_file_path = compose_file_path
        self.compose: Optional[DockerCompose] = None
    
    async def start_services(self) -> Dict[str, str]:
        """Start services using Docker Compose."""
        if not TESTCONTAINERS_AVAILABLE:
            raise ImportError("testcontainers package not available")
        
        # Check if compose file exists
        if not os.path.exists(self.compose_file_path):
            raise FileNotFoundError(f"Docker Compose file not found: {self.compose_file_path}")
        
        self.compose = DockerCompose(
            filepath=".",
            compose_file_name=self.compose_file_path,
            pull=True
        )
        
        self.compose.start()
        
        # Wait for services to be ready
        await self._wait_for_compose_services()
        
        # Return service URLs
        return {
            'database_url': 'postgresql+asyncpg://test_user:test_password@localhost:5432/test_iris_db',
            'redis_url': 'redis://localhost:6379/0',
            'iris_api_url': 'http://localhost:8001'
        }
    
    def stop_services(self):
        """Stop Docker Compose services."""
        if self.compose:
            self.compose.stop()
            self.compose = None
    
    async def _wait_for_compose_services(self):
        """Wait for all compose services to be ready."""
        # Wait for database
        await self._wait_for_postgres_compose()
        
        # Wait for Redis
        await self._wait_for_redis_compose()
        
        # Wait for mock API (if included)
        try:
            await self._wait_for_http_service("localhost", 8001, "/health")
        except TimeoutError:
            pass  # Mock API might not be included
    
    async def _wait_for_postgres_compose(self):
        """Wait for PostgreSQL in compose setup."""
        connection_url = 'postgresql+asyncpg://test_user:test_password@localhost:5432/test_iris_db'
        engine = create_async_engine(connection_url)
        
        for _ in range(30):
            try:
                async with engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                await engine.dispose()
                return
            except Exception:
                await asyncio.sleep(1)
        
        await engine.dispose()
        raise TimeoutError("PostgreSQL compose service did not start")
    
    async def _wait_for_redis_compose(self):
        """Wait for Redis in compose setup."""
        for _ in range(30):
            try:
                redis_client = redis.from_url('redis://localhost:6379/0')
                await redis_client.ping()
                await redis_client.close()
                return
            except Exception:
                await asyncio.sleep(1)
        
        raise TimeoutError("Redis compose service did not start")
    
    async def _wait_for_http_service(self, host: str, port: int, path: str = "/"):
        """Wait for HTTP service in compose setup."""
        url = f"http://{host}:{port}{path}"
        
        for _ in range(30):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, timeout=2.0)
                    if response.status_code < 500:
                        return
            except Exception:
                await asyncio.sleep(1)
        
        raise TimeoutError(f"HTTP service at {url} did not start")


# Global container manager instance
container_manager = TestContainerManager()


# ==================== Fixtures ====================

@pytest.fixture(scope="session")
def test_container_manager() -> TestContainerManager:
    """Get the test container manager."""
    return container_manager


@pytest_asyncio.fixture(scope="session")
async def container_services() -> AsyncGenerator[Dict[str, str], None]:
    """Start all test containers for the session."""
    if not TESTCONTAINERS_AVAILABLE:
        pytest.skip("testcontainers not available")
    
    try:
        services = await container_manager.start_all_services()
        yield services
    finally:
        container_manager.stop_all_services()


@pytest.fixture(scope="session")
def container_settings(container_services: Dict[str, str]) -> Settings:
    """Settings configured for test containers."""
    return Settings(
        DEBUG=True,
        ENVIRONMENT="test",
        DATABASE_URL=container_services['database_url'],
        REDIS_URL=container_services['redis_url'],
        IRIS_API_BASE_URL=container_services['iris_api_url'],
        SECRET_KEY="test_secret_key_32_characters_long",
        ENCRYPTION_KEY="test_encryption_key_32_chars_long",
        AUDIT_LOG_ENCRYPTION=False,
    )


@pytest_asyncio.fixture
async def container_db_session(container_services: Dict[str, str]) -> AsyncGenerator[AsyncSession, None]:
    """Database session using test containers."""
    engine = create_async_engine(container_services['database_url'])
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()
    
    await engine.dispose()


@pytest_asyncio.fixture
async def container_redis_client(container_services: Dict[str, str]):
    """Redis client using test containers."""
    redis_client = redis.from_url(container_services['redis_url'])
    yield redis_client
    await redis_client.close()


# Docker Compose fixtures
@pytest.fixture(scope="session")
def compose_manager() -> DockerComposeManager:
    """Get Docker Compose manager."""
    return DockerComposeManager()


@pytest_asyncio.fixture(scope="session")
async def compose_services(compose_manager: DockerComposeManager) -> AsyncGenerator[Dict[str, str], None]:
    """Start services using Docker Compose."""
    if not TESTCONTAINERS_AVAILABLE:
        pytest.skip("testcontainers not available")
    
    try:
        services = await compose_manager.start_services()
        yield services
    finally:
        compose_manager.stop_services()


# Helper functions
def skip_if_no_containers():
    """Skip test if testcontainers is not available."""
    if not TESTCONTAINERS_AVAILABLE:
        pytest.skip("testcontainers package not available")


def requires_containers(func):
    """Decorator to skip test if containers are not available."""
    return pytest.mark.skipif(
        not TESTCONTAINERS_AVAILABLE,
        reason="testcontainers package not available"
    )(func)