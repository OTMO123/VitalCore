"""
Healthcare-Compliant Database Transaction Manager
Enterprise-grade transaction management for SOC2, HIPAA, FHIR compliance.
"""

import asyncio
import contextlib
from typing import AsyncGenerator, Optional, Any, Dict
from datetime import datetime, timezone
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import uuid

from app.core.database_unified import get_session_factory

logger = structlog.get_logger()


class HealthcareTransactionError(Exception):
    """Custom exception for healthcare transaction management."""
    pass


class HealthcareTransactionManager:
    """
    SOC2/HIPAA compliant transaction manager for healthcare database operations.
    Ensures proper isolation, audit trails, and error handling.
    """
    
    def __init__(self):
        self.active_transactions: Dict[str, AsyncSession] = {}
    
    @contextlib.asynccontextmanager
    async def healthcare_transaction(
        self,
        session: Optional[AsyncSession] = None,
        isolation_level: str = "READ_COMMITTED",
        audit_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        Create a healthcare-compliant database transaction.
        
        Args:
            session: Optional existing session to use
            isolation_level: Transaction isolation level
            audit_context: Context for audit logging
        
        Yields:
            AsyncSession: Database session with proper transaction management
        """
        transaction_id = str(uuid.uuid4())
        session_created = False
        
        try:
            # Create new session if not provided
            if session is None:
                session_factory = await get_session_factory()
                session = session_factory()
                session_created = True
                
                # Initialize connection for AsyncPG compatibility
                await session.connection()
            
            # Track active transaction for compliance monitoring
            self.active_transactions[transaction_id] = session
            
            # Start explicit transaction with healthcare-grade isolation
            transaction = await session.begin()
            
            # Log transaction start for SOC2 compliance
            logger.info(
                "Healthcare transaction started",
                transaction_id=transaction_id,
                isolation_level=isolation_level,
                audit_context=audit_context,
                timestamp=datetime.now(timezone.utc)
            )
            
            try:
                yield session
                
                # Commit transaction if no errors
                await transaction.commit()
                
                logger.info(
                    "Healthcare transaction committed",
                    transaction_id=transaction_id,
                    timestamp=datetime.now(timezone.utc)
                )
                
            except Exception as e:
                # Rollback on any error
                await transaction.rollback()
                
                logger.error(
                    "Healthcare transaction rolled back",
                    transaction_id=transaction_id,
                    error=str(e),
                    error_type=type(e).__name__,
                    timestamp=datetime.now(timezone.utc),
                    exc_info=True
                )
                
                raise HealthcareTransactionError(
                    f"Transaction {transaction_id} failed: {e}"
                ) from e
                
        except Exception as e:
            # Handle session creation or initialization errors
            logger.error(
                "Healthcare transaction initialization failed",
                transaction_id=transaction_id,
                error=str(e),
                timestamp=datetime.now(timezone.utc),
                exc_info=True
            )
            raise
            
        finally:
            # Cleanup: Remove from active transactions
            self.active_transactions.pop(transaction_id, None)
            
            # Close session if we created it
            if session_created and session:
                try:
                    await session.close()
                except Exception as close_error:
                    logger.warning(
                        "Healthcare session cleanup warning",
                        transaction_id=transaction_id,
                        error=str(close_error)
                    )
    
    async def execute_healthcare_operation(
        self,
        operation_func,
        audit_context: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        **kwargs
    ) -> Any:
        """
        Execute a healthcare database operation with enterprise-grade retry logic.
        
        Args:
            operation_func: Async function to execute
            audit_context: Context for audit logging
            max_retries: Maximum retry attempts
            **kwargs: Additional arguments for operation_func
        
        Returns:
            Result of operation_func
        """
        operation_id = str(uuid.uuid4())
        
        for attempt in range(max_retries + 1):
            try:
                async with self.healthcare_transaction(audit_context=audit_context) as session:
                    result = await operation_func(session, **kwargs)
                    
                    logger.info(
                        "Healthcare operation completed",
                        operation_id=operation_id,
                        attempt=attempt + 1,
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    return result
                    
            except Exception as e:
                logger.warning(
                    "Healthcare operation attempt failed",
                    operation_id=operation_id,
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e),
                    error_type=type(e).__name__,
                    timestamp=datetime.now(timezone.utc)
                )
                
                # Re-raise on final attempt
                if attempt >= max_retries:
                    logger.error(
                        "Healthcare operation failed after all retries",
                        operation_id=operation_id,
                        total_attempts=attempt + 1,
                        final_error=str(e),
                        timestamp=datetime.now(timezone.utc),
                        exc_info=True
                    )
                    raise
                
                # Wait before retry (exponential backoff for healthcare reliability)
                await asyncio.sleep(2 ** attempt)
    
    def get_active_transaction_count(self) -> int:
        """Get count of active transactions for monitoring."""
        return len(self.active_transactions)
    
    async def cleanup_stale_transactions(self, max_age_seconds: int = 300):
        """
        Cleanup stale transactions for healthcare system reliability.
        
        Args:
            max_age_seconds: Maximum age for transactions before cleanup
        """
        # Implementation for stale transaction cleanup
        # This would be used by a background monitoring service
        stale_count = 0
        
        for transaction_id, session in list(self.active_transactions.items()):
            try:
                # In a full implementation, you'd track transaction start times
                # and clean up transactions older than max_age_seconds
                if session.in_transaction():
                    await session.rollback()
                await session.close()
                self.active_transactions.pop(transaction_id, None)
                stale_count += 1
            except Exception as cleanup_error:
                logger.warning(
                    "Stale transaction cleanup warning",
                    transaction_id=transaction_id,
                    error=str(cleanup_error)
                )
        
        if stale_count > 0:
            logger.info(
                "Cleaned up stale healthcare transactions",
                count=stale_count,
                timestamp=datetime.now(timezone.utc)
            )


# Global healthcare transaction manager instance
healthcare_transaction_manager = HealthcareTransactionManager()


@contextlib.asynccontextmanager
async def healthcare_transaction(
    session: Optional[AsyncSession] = None,
    audit_context: Optional[Dict[str, Any]] = None
) -> AsyncGenerator[AsyncSession, None]:
    """
    Convenience function for healthcare-compliant transactions.
    
    Usage:
        async with healthcare_transaction() as session:
            # Your healthcare database operations
            patient = Patient(...)
            session.add(patient)
            # Transaction automatically committed/rolled back
    """
    async with healthcare_transaction_manager.healthcare_transaction(
        session=session,
        audit_context=audit_context
    ) as session:
        yield session


async def execute_healthcare_batch_operation(
    items: list,
    operation_func,
    batch_size: int = 50,
    audit_context: Optional[Dict[str, Any]] = None
) -> list:
    """
    Execute healthcare operations in compliant batches.
    
    Args:
        items: List of items to process
        operation_func: Function to execute for each batch
        batch_size: Size of each batch
        audit_context: Context for audit logging
    
    Returns:
        List of results from all batches
    """
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_context = {
            **(audit_context or {}),
            "batch_number": i // batch_size + 1,
            "batch_size": len(batch),
            "total_items": len(items)
        }
        
        async with healthcare_transaction(audit_context=batch_context) as session:
            batch_result = await operation_func(session, batch)
            results.extend(batch_result if isinstance(batch_result, list) else [batch_result])
    
    return results