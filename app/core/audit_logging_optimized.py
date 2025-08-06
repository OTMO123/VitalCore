"""
Optimized Audit Logging Performance System

High-performance audit logging implementation for production healthcare environments:
- Asynchronous batch processing with configurable batch sizes
- Memory-efficient buffering with automatic flushing
- Database write optimization with bulk inserts
- Compression and archiving for long-term storage
- Performance monitoring and metrics collection
- SOC2 and HIPAA compliant immutable audit trails
- Circuit breaker pattern for resilience

This module provides enterprise-grade audit logging that can handle
high-volume PHI access events while maintaining compliance requirements.
"""

import asyncio
import json
import uuid
import time
import gzip
import hashlib
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import deque
import threading
import structlog

from sqlalchemy import text, insert, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as postgres_insert

from app.core.database_unified import get_db, AuditEventType
from app.core.config import get_settings
from app.core.redis_caching import cache_manager

logger = structlog.get_logger()


class AuditLogLevel(str, Enum):
    """Audit log levels for prioritization."""
    CRITICAL = "critical"  # Security violations, breaches
    HIGH = "high"  # PHI access, administrative changes
    MEDIUM = "medium"  # User actions, system events
    LOW = "low"  # Debug information, metrics


class BatchProcessingStatus(str, Enum):
    """Status of batch processing operations."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class AuditLogEntry:
    """Optimized audit log entry structure."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_type: str = ""
    user_id: Optional[str] = None
    patient_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: str = ""
    outcome: str = "success"
    client_info: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    phi_accessed: bool = False
    compliance_flags: List[str] = field(default_factory=list)
    log_level: AuditLogLevel = AuditLogLevel.MEDIUM
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "user_id": self.user_id,
            "patient_id": self.patient_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "outcome": self.outcome,
            "client_info": self.client_info,
            "metadata": self.metadata,
            "phi_accessed": self.phi_accessed,
            "compliance_flags": self.compliance_flags,
            "log_level": self.log_level.value
        }
    
    def calculate_hash(self) -> str:
        """Calculate cryptographic hash for immutability."""
        data = self.to_dict()
        # Sort for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(sorted_data.encode()).hexdigest()


@dataclass
class BatchMetrics:
    """Metrics for batch processing performance."""
    batch_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    entries_processed: int = 0
    entries_failed: int = 0
    processing_time_ms: float = 0
    database_write_time_ms: float = 0
    compression_time_ms: float = 0
    status: BatchProcessingStatus = BatchProcessingStatus.PENDING


class AuditLogBuffer:
    """High-performance memory buffer for audit log entries."""
    
    def __init__(self, max_size: int = 10000, auto_flush_interval: int = 30):
        self.max_size = max_size
        self.auto_flush_interval = auto_flush_interval
        self.buffer: deque[AuditLogEntry] = deque(maxlen=max_size)
        self.buffer_lock = threading.RLock()
        self.last_flush = time.time()
        self.total_entries_buffered = 0
        self.total_entries_flushed = 0
        
    def add_entry(self, entry: AuditLogEntry) -> bool:
        """Add entry to buffer with thread safety."""
        with self.buffer_lock:
            self.buffer.append(entry)
            self.total_entries_buffered += 1
            
            # Check if buffer needs flushing
            current_time = time.time()
            needs_flush = (
                len(self.buffer) >= self.max_size * 0.8 or  # 80% capacity
                (current_time - self.last_flush) >= self.auto_flush_interval
            )
            
            return needs_flush
    
    def get_batch(self, batch_size: Optional[int] = None) -> List[AuditLogEntry]:
        """Get batch of entries for processing."""
        with self.buffer_lock:
            if not self.buffer:
                return []
            
            actual_batch_size = min(batch_size or len(self.buffer), len(self.buffer))
            batch = []
            
            for _ in range(actual_batch_size):
                if self.buffer:
                    batch.append(self.buffer.popleft())
            
            return batch
    
    def get_buffer_stats(self) -> Dict[str, Any]:
        """Get buffer performance statistics."""
        with self.buffer_lock:
            return {
                "current_size": len(self.buffer),
                "max_size": self.max_size,
                "utilization_percent": (len(self.buffer) / self.max_size) * 100,
                "total_entries_buffered": self.total_entries_buffered,
                "total_entries_flushed": self.total_entries_flushed,
                "last_flush_seconds_ago": time.time() - self.last_flush
            }


class AuditLogProcessor:
    """Optimized audit log processor with batch operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.buffer = AuditLogBuffer(
            max_size=int(getattr(self.settings, 'audit_buffer_size', 10000)),
            auto_flush_interval=int(getattr(self.settings, 'audit_flush_interval', 30))
        )
        
        # Processing configuration
        self.batch_size = int(getattr(self.settings, 'audit_batch_size', 500))
        self.max_retries = int(getattr(self.settings, 'audit_max_retries', 3))
        self.compression_enabled = getattr(self.settings, 'audit_compression_enabled', True)
        
        # Performance tracking
        self.processing_metrics: List[BatchMetrics] = []
        self.is_processing = False
        self.circuit_breaker_failures = 0
        self.circuit_breaker_threshold = 5
        
    async def log_audit_event(
        self,
        event_type: Union[str, AuditEventType],
        user_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        action: str = "",
        outcome: str = "success",
        **kwargs
    ) -> str:
        """Log audit event with optimized buffering."""
        
        # Create audit log entry
        entry = AuditLogEntry(
            event_type=event_type.value if isinstance(event_type, AuditEventType) else event_type,
            user_id=user_id,
            patient_id=patient_id,
            action=action,
            outcome=outcome,
            **kwargs
        )
        
        # Determine log level and PHI flag
        entry.log_level = self._determine_log_level(entry)
        entry.phi_accessed = self._is_phi_access_event(entry)
        
        # Add compliance flags
        entry.compliance_flags = self._get_compliance_flags(entry)
        
        # Add to buffer
        needs_flush = self.buffer.add_entry(entry)
        
        # Trigger background processing if needed
        if needs_flush and not self.is_processing:
            asyncio.create_task(self._process_buffer_batch())
        
        return entry.event_id
    
    async def _process_buffer_batch(self) -> Optional[BatchMetrics]:
        """Process a batch of audit log entries."""
        if self.is_processing:
            return None
        
        self.is_processing = True
        batch_metrics = BatchMetrics(
            batch_id=str(uuid.uuid4()),
            start_time=datetime.utcnow()
        )
        
        try:
            # Check circuit breaker
            if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
                logger.warning("Audit logging circuit breaker open", failures=self.circuit_breaker_failures)
                await asyncio.sleep(30)  # Wait before retry
                self.circuit_breaker_failures = 0
            
            # Get batch from buffer
            batch = self.buffer.get_batch(self.batch_size)
            if not batch:
                return None
            
            batch_metrics.entries_processed = len(batch)
            
            # Process batch with database operations
            success = await self._write_batch_to_database(batch, batch_metrics)
            
            if success:
                # Cache aggregation data for performance
                await self._cache_audit_aggregations(batch)
                
                # Update metrics
                batch_metrics.status = BatchProcessingStatus.COMPLETED
                batch_metrics.end_time = datetime.utcnow()
                batch_metrics.processing_time_ms = (
                    (batch_metrics.end_time - batch_metrics.start_time).total_seconds() * 1000
                )
                
                # Reset circuit breaker
                self.circuit_breaker_failures = 0
                
                self.buffer.total_entries_flushed += len(batch)
                self.buffer.last_flush = time.time()
                
                logger.info(
                    "Audit batch processed successfully",
                    batch_id=batch_metrics.batch_id,
                    entries=len(batch),
                    processing_time_ms=batch_metrics.processing_time_ms
                )
                
            else:
                batch_metrics.status = BatchProcessingStatus.FAILED
                batch_metrics.entries_failed = len(batch)
                self.circuit_breaker_failures += 1
                
                # Re-queue failed entries for retry
                for entry in batch:
                    self.buffer.add_entry(entry)
                
                logger.error(
                    "Audit batch processing failed",
                    batch_id=batch_metrics.batch_id,
                    entries=len(batch),
                    circuit_breaker_failures=self.circuit_breaker_failures
                )
            
            # Store metrics
            self.processing_metrics.append(batch_metrics)
            
            # Keep only recent metrics
            if len(self.processing_metrics) > 100:
                self.processing_metrics = self.processing_metrics[-50:]
            
            return batch_metrics
            
        except Exception as e:
            logger.error("Audit batch processing exception", error=str(e), batch_id=batch_metrics.batch_id)
            batch_metrics.status = BatchProcessingStatus.FAILED
            self.circuit_breaker_failures += 1
            return batch_metrics
            
        finally:
            self.is_processing = False
    
    async def _write_batch_to_database(self, batch: List[AuditLogEntry], metrics: BatchMetrics) -> bool:
        """Write batch of audit entries to database with optimization."""
        start_time = time.time()
        
        try:
            async for session in get_db():
                # Prepare batch data for bulk insert
                batch_data = []
                
                for entry in batch:
                    # Calculate hash for immutability
                    entry_hash = entry.calculate_hash()
                    
                    # Compress metadata if enabled
                    metadata_json = json.dumps(entry.metadata, default=str)
                    if self.compression_enabled and len(metadata_json) > 1000:
                        compression_start = time.time()
                        compressed_metadata = gzip.compress(metadata_json.encode())
                        metrics.compression_time_ms += (time.time() - compression_start) * 1000
                        metadata_stored = compressed_metadata
                        is_compressed = True
                    else:
                        metadata_stored = metadata_json
                        is_compressed = False
                    
                    batch_data.append({
                        "id": uuid.uuid4(),
                        "event_id": entry.event_id,
                        "timestamp": entry.timestamp,
                        "event_type": entry.event_type,
                        "user_id": entry.user_id,
                        "patient_id": entry.patient_id,
                        "resource_type": entry.resource_type,
                        "resource_id": entry.resource_id,
                        "action": entry.action,
                        "outcome": entry.outcome,
                        "client_info": json.dumps(entry.client_info, default=str),
                        "metadata": metadata_stored,
                        "metadata_compressed": is_compressed,
                        "phi_accessed": entry.phi_accessed,
                        "compliance_flags": entry.compliance_flags,
                        "log_level": entry.log_level.value,
                        "event_hash": entry_hash,
                        "created_at": datetime.utcnow()
                    })
                
                # Perform bulk insert
                db_start_time = time.time()
                
                insert_stmt = postgres_insert("audit_logs").values(batch_data)
                # Handle conflicts with upsert (in case of duplicate event_ids)
                upsert_stmt = insert_stmt.on_conflict_do_nothing(index_elements=["event_id"])
                
                await session.execute(upsert_stmt)
                await session.commit()
                
                metrics.database_write_time_ms = (time.time() - db_start_time) * 1000
                
                logger.debug(
                    "Audit batch written to database",
                    entries=len(batch_data),
                    db_write_time_ms=metrics.database_write_time_ms
                )
                
                return True
                
        except Exception as e:
            logger.error("Database write failed for audit batch", error=str(e))
            return False
    
    async def _cache_audit_aggregations(self, batch: List[AuditLogEntry]) -> None:
        """Cache audit aggregation data for performance dashboards."""
        try:
            # Aggregate by event type and hour
            hourly_aggregations = {}
            phi_access_count = 0
            security_events = 0
            
            current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            
            for entry in batch:
                # Count PHI access events
                if entry.phi_accessed:
                    phi_access_count += 1
                
                # Count security events
                if entry.log_level in [AuditLogLevel.CRITICAL, AuditLogLevel.HIGH]:
                    security_events += 1
                
                # Aggregate by event type
                if entry.event_type not in hourly_aggregations:
                    hourly_aggregations[entry.event_type] = 0
                hourly_aggregations[entry.event_type] += 1
            
            # Cache aggregations
            aggregation_data = {
                "hour": current_hour.isoformat(),
                "event_type_counts": hourly_aggregations,
                "phi_access_count": phi_access_count,
                "security_events": security_events,
                "total_events": len(batch)
            }
            
            cache_key = f"audit_agg:{current_hour.isoformat()}"
            await cache_manager.redis_cache.set(
                cache_manager.redis_cache.strategy_manager.cache_configs["audit_aggregation"].key_type,
                cache_key,
                aggregation_data,
                ttl_override=3600  # 1 hour
            )
            
        except Exception as e:
            logger.error("Failed to cache audit aggregations", error=str(e))
    
    def _determine_log_level(self, entry: AuditLogEntry) -> AuditLogLevel:
        """Determine appropriate log level for audit entry."""
        # Critical events
        if entry.event_type in [
            AuditEventType.SECURITY_VIOLATION.value,
            AuditEventType.DATA_BREACH_DETECTED.value,
            "unauthorized_access"
        ]:
            return AuditLogLevel.CRITICAL
        
        # High priority events
        if entry.event_type in [
            AuditEventType.PHI_ACCESSED.value,
            AuditEventType.PHI_CREATED.value,
            AuditEventType.PHI_UPDATED.value,
            AuditEventType.PHI_DELETED.value,
            AuditEventType.PHI_EXPORTED.value
        ] or entry.phi_accessed:
            return AuditLogLevel.HIGH
        
        # Medium priority events
        if entry.event_type in [
            AuditEventType.USER_LOGIN.value,
            AuditEventType.USER_LOGOUT.value,
            AuditEventType.PATIENT_CREATED.value,
            AuditEventType.PATIENT_UPDATED.value
        ]:
            return AuditLogLevel.MEDIUM
        
        # Default to low
        return AuditLogLevel.LOW
    
    def _is_phi_access_event(self, entry: AuditLogEntry) -> bool:
        """Determine if audit entry involves PHI access."""
        phi_event_types = [
            AuditEventType.PHI_ACCESSED.value,
            AuditEventType.PHI_CREATED.value,
            AuditEventType.PHI_UPDATED.value,
            AuditEventType.PHI_DELETED.value,
            AuditEventType.PHI_EXPORTED.value,
            AuditEventType.PATIENT_ACCESSED.value,
            AuditEventType.DOCUMENT_ACCESSED.value
        ]
        
        return (
            entry.event_type in phi_event_types or
            entry.patient_id is not None or
            "phi" in entry.action.lower() or
            any("phi" in flag.lower() for flag in entry.compliance_flags)
        )
    
    def _get_compliance_flags(self, entry: AuditLogEntry) -> List[str]:
        """Get compliance flags for audit entry."""
        flags = []
        
        # HIPAA compliance flags
        if entry.phi_accessed or entry.patient_id:
            flags.append("HIPAA_APPLICABLE")
        
        # SOC2 compliance flags
        if entry.user_id and entry.action:
            flags.append("SOC2_ACCESS_CONTROL")
        
        # High-risk flags
        if entry.log_level == AuditLogLevel.CRITICAL:
            flags.append("HIGH_RISK_EVENT")
        
        # Administrative flags
        if "admin" in (entry.action or "").lower():
            flags.append("ADMINISTRATIVE_ACTION")
        
        return flags
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive audit logging performance metrics."""
        buffer_stats = self.buffer.get_buffer_stats()
        
        # Calculate processing metrics
        recent_metrics = self.processing_metrics[-10:] if self.processing_metrics else []
        
        if recent_metrics:
            avg_processing_time = sum(m.processing_time_ms for m in recent_metrics) / len(recent_metrics)
            avg_db_write_time = sum(m.database_write_time_ms for m in recent_metrics) / len(recent_metrics)
            total_processed = sum(m.entries_processed for m in recent_metrics)
            total_failed = sum(m.entries_failed for m in recent_metrics)
            success_rate = ((total_processed - total_failed) / total_processed * 100) if total_processed > 0 else 0
        else:
            avg_processing_time = 0
            avg_db_write_time = 0
            success_rate = 100
        
        return {
            "buffer_statistics": buffer_stats,
            "processing_performance": {
                "average_batch_processing_time_ms": avg_processing_time,
                "average_db_write_time_ms": avg_db_write_time,
                "batch_success_rate_percent": success_rate,
                "circuit_breaker_failures": self.circuit_breaker_failures,
                "compression_enabled": self.compression_enabled,
                "current_batch_size": self.batch_size
            },
            "recent_batches": len(recent_metrics),
            "is_processing": self.is_processing
        }
    
    async def force_flush(self) -> BatchMetrics:
        """Force flush buffer for immediate processing."""
        logger.info("Forcing audit buffer flush")
        
        if self.is_processing:
            logger.warning("Audit processing already in progress")
            return None
        
        return await self._process_buffer_batch()


class AuditLogArchiver:
    """Handles archiving and compression of old audit logs."""
    
    def __init__(self, processor: AuditLogProcessor):
        self.processor = processor
        self.settings = get_settings()
        self.retention_days = int(getattr(self.settings, 'audit_log_retention_days', 2555))  # 7 years
    
    async def archive_old_logs(self, archive_before_days: int = 90) -> Dict[str, Any]:
        """Archive audit logs older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=archive_before_days)
        
        try:
            async for session in get_db():
                # Find logs to archive
                count_query = select(func.count()).select_from(
                    text("audit_logs")
                ).where(text("created_at < :cutoff_date"))
                
                result = await session.execute(count_query, {"cutoff_date": cutoff_date})
                logs_to_archive = result.scalar()
                
                if logs_to_archive == 0:
                    return {"message": "No logs to archive", "archived_count": 0}
                
                # Create archive table if needed
                await self._create_archive_table(session)
                
                # Move logs to archive
                archive_query = text("""
                    INSERT INTO audit_logs_archive 
                    SELECT * FROM audit_logs 
                    WHERE created_at < :cutoff_date
                """)
                
                await session.execute(archive_query, {"cutoff_date": cutoff_date})
                
                # Delete from main table
                delete_query = text("DELETE FROM audit_logs WHERE created_at < :cutoff_date")
                await session.execute(delete_query, {"cutoff_date": cutoff_date})
                
                await session.commit()
                
                logger.info(
                    "Audit logs archived successfully",
                    archived_count=logs_to_archive,
                    cutoff_date=cutoff_date.isoformat()
                )
                
                return {
                    "message": "Audit logs archived successfully",
                    "archived_count": logs_to_archive,
                    "cutoff_date": cutoff_date.isoformat()
                }
                
        except Exception as e:
            logger.error("Audit log archiving failed", error=str(e))
            return {"error": str(e)}
    
    async def _create_archive_table(self, session: AsyncSession) -> None:
        """Create archive table with same structure as main audit table."""
        create_archive_table_sql = text("""
            CREATE TABLE IF NOT EXISTS audit_logs_archive (
                LIKE audit_logs INCLUDING ALL
            )
        """)
        
        await session.execute(create_archive_table_sql)


# =============================================================================
# OPTIMIZED AUDIT LOGGING FACADE
# =============================================================================

class OptimizedAuditLogger:
    """Main interface for optimized audit logging."""
    
    def __init__(self):
        self.processor = AuditLogProcessor()
        self.archiver = AuditLogArchiver(self.processor)
    
    async def log_event(
        self,
        event_type: Union[str, AuditEventType],
        user_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        action: str = "",
        outcome: str = "success",
        **kwargs
    ) -> str:
        """Log audit event with high performance."""
        return await self.processor.log_audit_event(
            event_type=event_type,
            user_id=user_id,
            patient_id=patient_id,
            action=action,
            outcome=outcome,
            **kwargs
        )
    
    async def log_phi_access(
        self,
        user_id: str,
        patient_id: str,
        resource_type: str,
        action: str,
        client_info: Dict[str, Any],
        **kwargs
    ) -> str:
        """Log PHI access event with compliance flags."""
        return await self.processor.log_audit_event(
            event_type=AuditEventType.PHI_ACCESSED,
            user_id=user_id,
            patient_id=patient_id,
            resource_type=resource_type,
            action=action,
            client_info=client_info,
            phi_accessed=True,
            log_level=AuditLogLevel.HIGH,
            **kwargs
        )
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        return await self.processor.get_performance_metrics()
    
    async def force_flush(self) -> Optional[BatchMetrics]:
        """Force flush buffer for testing or emergency."""
        return await self.processor.force_flush()
    
    async def archive_old_logs(self, archive_before_days: int = 90) -> Dict[str, Any]:
        """Archive old audit logs."""
        return await self.archiver.archive_old_logs(archive_before_days)


# Global optimized audit logger instance
optimized_audit_logger = OptimizedAuditLogger()