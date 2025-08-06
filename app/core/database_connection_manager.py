"""
Enterprise Database Connection Manager for SOC2 Compliance

Handles high-concurrency database operations with proper session isolation,
connection pooling, and transaction management for healthcare compliance.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.exc import DisconnectionError, TimeoutError as SQLTimeoutError
from sqlalchemy import text
import structlog

logger = structlog.get_logger()

class DatabaseConnectionManager:
    """Enterprise-grade database connection manager with SOC2 compliance features."""
    
    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory
        self._connection_semaphore = asyncio.Semaphore(50)  # Limit concurrent connections
        self._active_sessions = set()
        
    @asynccontextmanager
    async def get_session(
        self, 
        isolation_level: str = "READ_COMMITTED",
        retry_count: int = 3
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session with proper connection management and retry logic.
        
        Args:
            isolation_level: Transaction isolation level
            retry_count: Number of retry attempts for failed connections
            
        Yields:
            AsyncSession: Database session with proper isolation
        """
        async with self._connection_semaphore:
            session = None
            attempt = 0
            
            while attempt < retry_count:
                try:
                    # Create new session
                    session = self.session_factory()
                    self._active_sessions.add(session)
                    
                    # Verify connection and set isolation level
                    async with session.begin():
                        await session.execute(text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"))
                        
                        # Test connection
                        await session.execute(text("SELECT 1"))
                    
                    logger.debug("Database session created", 
                               isolation_level=isolation_level,
                               attempt=attempt + 1)
                    
                    yield session
                    break
                    
                except (DisconnectionError, SQLTimeoutError, OSError) as e:
                    attempt += 1
                    if session:
                        try:
                            await session.close()
                        except Exception:
                            pass
                        if session in self._active_sessions:
                            self._active_sessions.remove(session)
                    
                    if attempt < retry_count:
                        wait_time = min(2.0 ** attempt, 10.0)  # Exponential backoff, max 10s
                        logger.warning(f"Database connection failed, retrying in {wait_time}s",
                                     attempt=attempt, error=str(e))
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error("Database connection failed after all retries",
                                   attempts=retry_count, error=str(e))
                        raise
                        
                except Exception as e:
                    if session:
                        try:
                            await session.rollback()
                            await session.close()
                        except Exception:
                            pass
                        if session in self._active_sessions:
                            self._active_sessions.remove(session)
                    logger.error("Unexpected database error", error=str(e))
                    raise
                    
            # Cleanup
            if session and session in self._active_sessions:
                try:
                    await session.close()
                except Exception as e:
                    logger.warning("Error closing session", error=str(e))
                finally:
                    self._active_sessions.remove(session)
    
    @asynccontextmanager
    async def get_serializable_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a session with SERIALIZABLE isolation for audit operations."""
        async with self.get_session(isolation_level="SERIALIZABLE") as session:
            yield session
    
    async def health_check(self) -> bool:
        """Perform database health check."""
        try:
            async with self.get_session() as session:
                result = await session.execute(text("SELECT version()"))
                version = result.scalar()
                logger.info("Database health check passed", version=version)
                return True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False
    
    async def cleanup_stale_connections(self):
        """Clean up any stale database connections."""
        stale_sessions = list(self._active_sessions)
        for session in stale_sessions:
            try:
                await session.close()
                self._active_sessions.remove(session)
            except Exception as e:
                logger.warning("Error cleaning up stale session", error=str(e))
        
        logger.info("Cleaned up stale connections", count=len(stale_sessions))
    
    def get_connection_stats(self) -> dict:
        """Get connection statistics for monitoring."""
        return {
            "active_sessions": len(self._active_sessions),
            "semaphore_available": self._connection_semaphore._value,
            "semaphore_locked": self._connection_semaphore.locked()
        }

# Global connection manager instance
_connection_manager: Optional[DatabaseConnectionManager] = None

def get_connection_manager() -> DatabaseConnectionManager:
    """Get the global connection manager instance."""
    global _connection_manager
    if _connection_manager is None:
        raise RuntimeError("Database connection manager not initialized")
    return _connection_manager

def initialize_connection_manager(session_factory: async_sessionmaker) -> DatabaseConnectionManager:
    """Initialize the global connection manager."""
    global _connection_manager
    _connection_manager = DatabaseConnectionManager(session_factory)
    return _connection_manager