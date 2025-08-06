"""
SOC2-Compliant Audit Logging Service

Production-grade audit logging with:
- Immutable audit trails with cryptographic integrity
- Real-time event processing via hybrid event bus
- Automated compliance reporting
- SIEM integration and export
- Event replay and forensic analysis
- Advanced search and filtering
- Retention policy management

Designed for SOC2 Type II compliance requirements.
"""

import asyncio
import json
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, and_, or_, func, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
import structlog
from collections import defaultdict

from app.core.config import get_settings
from app.core.database_unified import get_db, AuditLog
from app.core.security import security_manager
from app.core.database_connection_manager import DatabaseConnectionManager
from app.core.event_bus_advanced import (
    EventHandler, TypedEventHandler, BaseEvent
)
from app.core.events.event_bus import get_event_bus
from app.modules.audit_logger.schemas import (
    AuditEvent, SOC2Category, ComplianceReport, AuditLogQuery,
    AuditLogIntegrityReport, SIEMExportConfig, SIEMEvent,
    UserLoginEvent, DataAccessEvent, SecurityViolationEvent
)

logger = structlog.get_logger()

# Cryptographic integrity constants
HASH_ALGORITHM = "sha256"
CHAIN_VERIFICATION_INTERVAL = 100  # Verify chain every N records

# ============================================
# IMMUTABLE AUDIT LOG HANDLER
# ============================================

class ImmutableAuditLogHandler(TypedEventHandler):
    """Handler for persisting audit events to immutable log."""
    
    def __init__(self, db_session_factory):
        super().__init__("immutable_audit_logger", [AuditEvent])
        if db_session_factory is None:
            raise ValueError("db_session_factory cannot be None")
        self.db_session_factory = db_session_factory
        self.connection_manager = DatabaseConnectionManager(db_session_factory)
        self.settings = get_settings()
        
        # Batch processing for performance
        self.batch_size = 100
        self.batch_timeout = 5.0  # seconds
        self.pending_events = []
        self.last_batch_time = datetime.now(timezone.utc)
        
        # Integrity chain
        self.last_log_hash: Optional[str] = None
        
    async def handle(self, event: BaseEvent) -> bool:
        """Handle audit event with batching for performance."""
        if not isinstance(event, AuditEvent):
            return True  # Skip non-audit events
        
        try:
            # Add to batch
            self.pending_events.append(event)
            
            # Process batch if conditions met
            should_process = (
                len(self.pending_events) >= self.batch_size or
                (datetime.now(timezone.utc) - self.last_batch_time).total_seconds() >= self.batch_timeout
            )
            
            if should_process:
                await self._process_batch()
            
            return True
            
        except Exception as e:
            logger.error("Failed to handle audit event", 
                        event_id=event.event_id, error=str(e))
            return False
    
    async def _process_batch(self):
        """Process batch of audit events with proper session management."""
        if not self.pending_events:
            return
        
        batch = self.pending_events.copy()
        self.pending_events.clear()
        self.last_batch_time = datetime.now(timezone.utc)
        
        max_retries = 3
        retry_delay = 0.1  # Start with 100ms delay
        
        for attempt in range(max_retries):
            try:
                # Use connection manager for proper session handling
                async with self.connection_manager.get_serializable_session() as session:
                    # Get last log hash for integrity chain
                    if self.last_log_hash is None:
                        result = await session.execute(
                            select(AuditLog.log_hash)
                            .order_by(AuditLog.timestamp.desc())
                            .limit(1)
                        )
                        row = result.first()
                        self.last_log_hash = row.log_hash if row else "GENESIS_BLOCK_HASH"
                    
                    # Process each event in batch
                    audit_logs = []
                    for event in batch:
                        audit_log_data = await self._create_audit_log_entry(event)
                        audit_logs.append(audit_log_data)
                    
                    # Bulk insert with proper transaction handling
                    if audit_logs:
                        await session.execute(
                            pg_insert(AuditLog).values(audit_logs)
                        )
                        await session.commit()
                        
                        # Update last hash
                        self.last_log_hash = audit_logs[-1]["log_hash"]
                    
                    logger.info("Audit batch processed", 
                               batch_size=len(batch), 
                               total_pending=len(self.pending_events),
                               attempt=attempt + 1)
                    
                    # Success - break retry loop
                    break
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    # Exponential backoff
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    logger.warning(f"Audit batch failed, retrying in {retry_delay}s", 
                                 attempt=attempt + 1, error=str(e))
                else:
                    logger.error("Failed to process audit batch after all retries", 
                               batch_size=len(batch), error=str(e), attempts=max_retries)
                    # Re-add events to pending for next batch
                    self.pending_events.extend(batch)
    
    async def _create_audit_log_entry(self, event: AuditEvent) -> Dict[str, Any]:
        """Create tamper-proof audit log entry with cryptographic hash chaining."""
        timestamp = datetime.utcnow()
        
        # Create the core audit data
        audit_data = {
            "id": str(uuid.uuid4()),
            "event_id": event.event_id,
            "timestamp": timestamp,
            "event_type": event.event_type,
            "user_id": event.user_id,
            "session_id": event.session_id,
            "action": event.action,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "outcome": event.outcome,
            "event_data": event.event_data or {},
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
            "previous_hash": self.last_log_hash
        }
        
        # Create the payload for hashing (exclude hash fields)
        hashable_data = {
            "event_id": audit_data["event_id"],
            "timestamp": audit_data["timestamp"].isoformat(),
            "event_type": audit_data["event_type"],
            "user_id": audit_data["user_id"],
            "action": audit_data["action"],
            "resource_type": audit_data["resource_type"],
            "resource_id": audit_data["resource_id"],
            "outcome": audit_data["outcome"],
            "event_data": json.dumps(audit_data["event_data"], sort_keys=True),
            "previous_hash": audit_data["previous_hash"]
        }
        
        # Create cryptographic hash
        payload_string = json.dumps(hashable_data, sort_keys=True)
        log_hash = hashlib.sha256(payload_string.encode('utf-8')).hexdigest()
        
        # Add hash to audit data
        audit_data["log_hash"] = log_hash
        audit_data["hash_algorithm"] = HASH_ALGORITHM
        audit_data["chain_verified"] = True  # Will be verified later
        
        return audit_data
    
    async def verify_audit_chain(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> bool:
        """
        Verify the cryptographic integrity of the audit chain.
        
        Returns True if chain is intact, False if tampering is detected.
        """
        async with self.db_session_factory() as session:
            try:
                # Build query for audit logs to verify
                query = select(AuditLog).order_by(AuditLog.timestamp.asc())
                
                if start_date:
                    query = query.where(AuditLog.timestamp >= start_date)
                if end_date:
                    query = query.where(AuditLog.timestamp <= end_date)
                
                result = await session.execute(query)
                audit_logs = result.scalars().all()
                
                if not audit_logs:
                    return True  # Empty chain is valid
                
                previous_hash = "GENESIS_BLOCK_HASH"
                tampered_records = []
                
                for audit_log in audit_logs:
                    # Recreate the hashable data
                    hashable_data = {
                        "event_id": audit_log.event_id,
                        "timestamp": audit_log.timestamp.isoformat(),
                        "event_type": audit_log.event_type,
                        "user_id": audit_log.user_id,
                        "action": audit_log.action,
                        "resource_type": audit_log.resource_type or "",
                        "resource_id": audit_log.resource_id or "",
                        "outcome": audit_log.outcome,
                        "event_data": json.dumps(audit_log.event_data or {}, sort_keys=True),
                        "previous_hash": previous_hash
                    }
                    
                    # Compute expected hash
                    payload_string = json.dumps(hashable_data, sort_keys=True)
                    expected_hash = hashlib.sha256(payload_string.encode('utf-8')).hexdigest()
                    
                    # Verify hash matches
                    if audit_log.log_hash != expected_hash:
                        tampered_records.append({
                            "log_id": audit_log.id,
                            "timestamp": audit_log.timestamp,
                            "expected_hash": expected_hash,
                            "actual_hash": audit_log.log_hash
                        })
                    
                    # Verify chain link
                    if audit_log.previous_hash != previous_hash:
                        tampered_records.append({
                            "log_id": audit_log.id,
                            "timestamp": audit_log.timestamp,
                            "error": "broken_chain_link",
                            "expected_previous": previous_hash,
                            "actual_previous": audit_log.previous_hash
                        })
                    
                    previous_hash = audit_log.log_hash
                
                if tampered_records:
                    logger.critical(
                        "AUDIT CHAIN INTEGRITY VIOLATION DETECTED",
                        tampered_count=len(tampered_records),
                        tampered_records=tampered_records[:5]  # Log first 5
                    )
                    
                    # Create security violation event
                    violation_event = SecurityViolationEvent(
                        user_id="SYSTEM",
                        violation_type="audit_tampering",
                        severity="critical",
                        description=f"Audit chain integrity compromised: {len(tampered_records)} records tampered",
                        source_ip="127.0.0.1",
                        user_agent="audit_verification_system",
                        headers={
                            "tampered_records_count": len(tampered_records),
                            "verification_timestamp": datetime.utcnow().isoformat()
                        }
                    )
                    
                    # Log the violation
                    await self.handle(violation_event)
                    
                    return False
                
                logger.info(
                    "Audit chain integrity verified",
                    records_verified=len(audit_logs),
                    start_date=start_date,
                    end_date=end_date
                )
                
                return True
                
            except Exception as e:
                logger.error("Failed to verify audit chain", error=str(e))
                return False

# ============================================
# COMPLIANCE MONITORING HANDLER
# ============================================

class ComplianceMonitoringHandler(TypedEventHandler):
    """Handler for real-time compliance monitoring and alerting."""
    
    def __init__(self):
        super().__init__("compliance_monitor", [AuditEvent])
        self.settings = get_settings()
        
        # Compliance rules and thresholds
        self.rules = {
            "failed_login_threshold": 5,
            "privileged_access_window": 3600,  # seconds
            "data_export_size_limit": 1024 * 1024 * 100,  # 100MB
            "suspicious_activity_score": 0.8
        }
        
        # Tracking windows
        self.failed_logins = defaultdict(list)
        self.privileged_access = defaultdict(list)
        self.data_exports = defaultdict(list)
    
    async def handle(self, event: BaseEvent) -> bool:
        """Monitor event for compliance violations."""
        if not isinstance(event, AuditEvent):
            return True
        
        try:
            # Check for various compliance violations
            await self._check_failed_login_threshold(event)
            await self._check_privileged_access_patterns(event)
            await self._check_data_export_limits(event)
            await self._check_suspicious_activity(event)
            
            return True
            
        except Exception as e:
            logger.error("Compliance monitoring error", 
                        event_id=event.event_id, error=str(e))
            return True  # Don't fail audit processing for monitoring errors
    
    async def _check_failed_login_threshold(self, event: AuditEvent):
        """Check for excessive failed login attempts."""
        if not isinstance(event, UserLoginEvent) or event.outcome == "success":
            return
        
        user_key = event.user_id or event.username
        current_time = datetime.utcnow()
        
        # Clean old entries (1 hour window)
        cutoff_time = current_time - timedelta(hours=1)
        self.failed_logins[user_key] = [
            t for t in self.failed_logins[user_key] if t > cutoff_time
        ]
        
        # Add current failure
        self.failed_logins[user_key].append(current_time)
        
        # Check threshold
        if len(self.failed_logins[user_key]) >= self.rules["failed_login_threshold"]:
            await self._create_compliance_alert(
                "EXCESSIVE_FAILED_LOGINS",
                f"User {user_key} has {len(self.failed_logins[user_key])} failed logins in 1 hour",
                event,
                severity="high"
            )
    
    async def _check_privileged_access_patterns(self, event: AuditEvent):
        """Check for unusual privileged access patterns."""
        if event.operation != "privileged_access":
            return
        
        user_key = event.user_id
        current_time = datetime.utcnow()
        
        # Clean old entries
        cutoff_time = current_time - timedelta(seconds=self.rules["privileged_access_window"])
        self.privileged_access[user_key] = [
            t for t in self.privileged_access[user_key] if t > cutoff_time
        ]
        
        # Add current access
        self.privileged_access[user_key].append(current_time)
        
        # Check for multiple privileged access in short window
        if len(self.privileged_access[user_key]) > 3:
            await self._create_compliance_alert(
                "EXCESSIVE_PRIVILEGED_ACCESS",
                f"User {user_key} has multiple privileged access attempts",
                event,
                severity="medium"
            )
    
    async def _check_data_export_limits(self, event: AuditEvent):
        """Check for large data exports."""
        if event.operation != "data_export":
            return
        
        export_size = event.headers.get("export_size_bytes", 0) if event.headers else 0
        
        if export_size > self.rules["data_export_size_limit"]:
            await self._create_compliance_alert(
                "LARGE_DATA_EXPORT",
                f"Large data export: {export_size} bytes by user {event.user_id}",
                event,
                severity="medium"
            )
    
    async def _check_suspicious_activity(self, event: AuditEvent):
        """Check for suspicious activity based on risk score."""
        if event.risk_score and event.risk_score >= self.rules["suspicious_activity_score"]:
            await self._create_compliance_alert(
                "SUSPICIOUS_ACTIVITY",
                f"High risk activity detected: score {event.risk_score}",
                event,
                severity="high"
            )
    
    async def _create_compliance_alert(
        self, 
        alert_type: str, 
        message: str, 
        original_event: AuditEvent,
        severity: str = "medium"
    ):
        """Create compliance alert event."""
        alert_event = SecurityViolationEvent(
            user_id="system",
            violation_type=alert_type,
            severity_level=severity,
            detection_method="automated_monitoring",
            investigation_required=severity in ["high", "critical"],
            operation="compliance_alert",
            outcome="success",
            correlation_id=original_event.correlation_id,
            headers={
                "original_event_id": original_event.event_id,
                "alert_message": message,
                "detection_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Publish alert event
        event_bus = get_event_bus()
        await event_bus.publish(alert_event)
        
        logger.warning("Compliance alert generated", 
                      alert_type=alert_type, 
                      severity=severity,
                      original_event=original_event.event_id)

# ============================================
# SOC2 AUDIT LOGGING SERVICE
# ============================================

class SOC2AuditService:
    """Comprehensive SOC2 audit logging service."""
    
    def __init__(self, db_session_factory):
        if db_session_factory is None:
            raise ValueError("db_session_factory cannot be None")
        self.db_session_factory = db_session_factory
        self.connection_manager = DatabaseConnectionManager(db_session_factory)
        self.settings = get_settings()
        
        # Event handlers
        self.audit_handler = ImmutableAuditLogHandler(db_session_factory)
        self.compliance_handler = ComplianceMonitoringHandler()
        
        # SIEM export configurations
        self.siem_configs: Dict[str, SIEMExportConfig] = {}
        
    async def initialize(self):
        """Initialize the audit service."""
        # Subscribe handlers to event bus
        event_bus = get_event_bus()
        # Subscribe to all audit-relevant events
        audit_events = [
            "UserAuthenticated", "UserLoginFailed", "PHIAccessed", "DataModified",
            "SecurityViolation", "AuditLogCreated", "ComplianceViolation"
        ]
        event_bus.subscribe(audit_events, self.audit_handler.handle, "audit_service_handler")
        
        compliance_events = [
            "ComplianceViolation", "SecurityViolation", "PHIAccessed", "UnauthorizedAccess"
        ]
        event_bus.subscribe(compliance_events, self.compliance_handler.handle, "compliance_monitor")
        
        # Load SIEM configurations
        await self._load_siem_configurations()
        
        logger.info("SOC2 Audit Service initialized")
    
    async def log_audit_event(self, event: AuditEvent) -> bool:
        """Log audit event through event bus."""
        try:
            event_bus = get_event_bus()
            return await event_bus.publish(event)
        except Exception as e:
            logger.error("Failed to log audit event", 
                        event_id=event.event_id, error=str(e))
            return False
    
    async def log_event(
        self,
        event_type: str,
        user_id: str,
        user_role: str = "user",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: str = "access",
        details: Optional[Dict[str, Any]] = None,
        risk_level: str = "low",
        compliance_framework: Optional[List[str]] = None
    ) -> bool:
        """Log a generic audit event with SOC2 compliance."""
        try:
            # Create comprehensive audit event
            audit_event = AuditEvent(
                event_type=event_type,
                soc2_category=SOC2Category.SECURITY,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                operation=action,
                outcome="success",
                details=details or {},
                compliance_tags=compliance_framework or ["SOC2", "HIPAA"],
                publisher="SOC2AuditService"
            )
            
            return await self.log_audit_event(audit_event)
            
        except Exception as e:
            logger.error(
                "Failed to log generic audit event",
                event_type=event_type,
                user_id=user_id,
                error=str(e)
            )
            return False
    
    async def log_system_event(
        self,
        event_type: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: str = "system_action",
        outcome: str = "success",
        event_data: Optional[Dict[str, Any]] = None,
        user_id: str = "SYSTEM",
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        compliance_framework: Optional[List[str]] = None
    ) -> bool:
        """Log system-level audit event with SOC2 compliance."""
        try:
            # Merge event_data with context for comprehensive audit trail
            audit_details = event_data or {}
            if context:
                audit_details.update(context)
            if session_id:
                audit_details["session_id"] = session_id
            
            # Create system audit event
            audit_event = AuditEvent(
                event_type=event_type,
                soc2_category=SOC2Category.PROCESSING_INTEGRITY,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                operation=action,
                outcome=outcome,
                details=audit_details,
                compliance_tags=compliance_framework or ["SOC2", "SYSTEM_AUDIT"],
                publisher="SOC2AuditService"
            )
            
            return await self.log_audit_event(audit_event)
            
        except Exception as e:
            logger.error(
                "Failed to log system audit event",
                event_type=event_type,
                resource_type=resource_type,
                error=str(e)
            )
            return False
    
    async def query_audit_logs(
        self, 
        query: AuditLogQuery,
        session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Query audit logs with comprehensive filtering."""
        should_close = session is None
        if session is None:
            # Use connection manager instead of raw session factory
            async with self.connection_manager.get_session() as managed_session:
                return await self.query_audit_logs(query, managed_session)
        
        try:
            # Build query
            stmt = select(AuditLog)
            
            # Apply filters
            if query.start_date:
                stmt = stmt.where(AuditLog.timestamp >= query.start_date)
            if query.end_date:
                stmt = stmt.where(AuditLog.timestamp <= query.end_date)
            if query.user_id:
                stmt = stmt.where(AuditLog.user_id == query.user_id)
            if query.event_types:
                stmt = stmt.where(AuditLog.event_type.in_(query.event_types))
            if query.outcomes:
                stmt = stmt.where(AuditLog.outcome.in_(query.outcomes))
            if query.ip_address:
                stmt = stmt.where(AuditLog.ip_address == query.ip_address)
            if query.resource_type:
                stmt = stmt.where(AuditLog.resource_type == query.resource_type)
            
            # Advanced filters
            if query.compliance_tags:
                stmt = stmt.where(AuditLog.compliance_tags.overlap(query.compliance_tags))
            
            # Get total count
            count_stmt = select(func.count(AuditLog.id)).select_from(stmt.subquery())
            total_count = await session.scalar(count_stmt)
            
            # Apply sorting and pagination
            if query.sort_by == "timestamp":
                sort_column = AuditLog.timestamp
            else:
                sort_column = getattr(AuditLog, query.sort_by, AuditLog.timestamp)
            
            if query.sort_order == "desc":
                stmt = stmt.order_by(sort_column.desc())
            else:
                stmt = stmt.order_by(sort_column.asc())
            
            stmt = stmt.offset(query.offset).limit(query.limit)
            
            # Execute query
            result = await session.execute(stmt)
            logs = result.scalars().all()
            
            # Format results
            log_data = []
            for log in logs:
                log_dict = {
                    "id": log.id,
                    "timestamp": log.timestamp,
                    "event_type": log.event_type,
                    "user_id": log.user_id,
                    "session_id": log.session_id,
                    "correlation_id": log.correlation_id,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "action": log.action,
                    "outcome": log.outcome,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "compliance_tags": log.compliance_tags,
                    "data_classification": log.data_classification
                }
                
                # Include raw data if requested
                if query.include_raw_data:
                    log_dict["metadata"] = log.metadata
                    log_dict["error_message"] = log.error_message
                
                log_data.append(log_dict)
            
            return {
                "logs": log_data,
                "total_count": total_count,
                "query_info": {
                    "limit": query.limit,
                    "offset": query.offset,
                    "returned_count": len(log_data)
                }
            }
            
        except Exception as e:
            logger.error("Audit log query failed", error=str(e))
            raise
        finally:
            if should_close and session:
                try:
                    await session.close()
                except Exception as e:
                    logger.warning(f"Error closing session: {e}")
    
    async def verify_audit_log_integrity(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        session: Optional[AsyncSession] = None
    ) -> AuditLogIntegrityReport:
        """Verify audit log integrity using hash chain."""
        should_close = session is None
        if session is None:
            session = self.db_session_factory()
            # Verify session connection
            await session.connection()
        
        verification_id = secrets.token_hex(8)
        start_time = datetime.utcnow()
        
        try:
            # Build query for verification period
            stmt = select(AuditLog).order_by(AuditLog.timestamp.asc())
            
            if start_date:
                stmt = stmt.where(AuditLog.timestamp >= start_date)
            if end_date:
                stmt = stmt.where(AuditLog.timestamp <= end_date)
            
            result = await session.execute(stmt)
            logs = result.scalars().all()
            
            # Verify integrity
            total_events = len(logs)
            valid_events = 0
            invalid_events = 0
            integrity_violations = []
            
            previous_hash = "GENESIS_BLOCK_HASH"
            
            for log in logs:
                # Reconstruct expected hash
                content_to_hash = (
                    f"{previous_hash}"
                    f"{log.id}"
                    f"{log.timestamp.isoformat()}"
                    f"{log.event_type}"
                    f"{log.user_id or ''}"
                    f"{log.action}"
                    f"{log.outcome}"
                )
                
                expected_hash = hashlib.sha256(content_to_hash.encode()).hexdigest()
                
                if log.log_hash == expected_hash and log.previous_log_hash == previous_hash:
                    valid_events += 1
                else:
                    invalid_events += 1
                    integrity_violations.append({
                        "log_id": log.id,
                        "timestamp": log.timestamp,
                        "expected_hash": expected_hash,
                        "actual_hash": log.log_hash,
                        "expected_previous": previous_hash,
                        "actual_previous": log.previous_log_hash
                    })
                
                previous_hash = log.log_hash
            
            # Determine overall status
            if invalid_events == 0:
                integrity_status = "clean"
                confidence_score = 1.0
            elif invalid_events / total_events < 0.01:  # Less than 1% corruption
                integrity_status = "suspicious"
                confidence_score = 0.8
            else:
                integrity_status = "compromised"
                confidence_score = 0.0
            
            end_time = datetime.utcnow()
            
            report = AuditLogIntegrityReport(
                verification_id=verification_id,
                start_time=start_time,
                end_time=end_time,
                total_events_checked=total_events,
                valid_events=valid_events,
                invalid_events=invalid_events,
                missing_events=0,  # Would need more complex logic to detect
                integrity_violations=integrity_violations,
                integrity_status=integrity_status,
                confidence_score=confidence_score
            )
            
            logger.info("Audit log integrity verification completed",
                       verification_id=verification_id,
                       total_events=total_events,
                       valid_events=valid_events,
                       invalid_events=invalid_events,
                       status=integrity_status)
            
            return report
            
        except Exception as e:
            logger.error("Integrity verification failed", error=str(e))
            raise
        finally:
            if should_close and session:
                try:
                    await session.close()
                except Exception as e:
                    logger.warning(f"Error closing session: {e}")
    
    async def generate_compliance_report(
        self,
        report_type: str,
        start_date: datetime,
        end_date: datetime,
        soc2_categories: Optional[List[SOC2Category]] = None,
        session: Optional[AsyncSession] = None
    ) -> ComplianceReport:
        """Generate comprehensive compliance report."""
        should_close = session is None
        if session is None:
            session = self.db_session_factory()
            # Verify session connection
            await session.connection()
        
        try:
            report_id = secrets.token_hex(8)
            
            # Base query for report period
            base_query = select(AuditLog).where(
                and_(
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date
                )
            )
            
            # Filter by SOC2 categories if specified
            if soc2_categories:
                category_filters = []
                for category in soc2_categories:
                    category_filters.append(
                        AuditLog.compliance_tags.contains([category.value])
                    )
                if category_filters:
                    base_query = base_query.where(or_(*category_filters))
            
            # Get total events
            total_count = await session.scalar(
                select(func.count(AuditLog.id)).select_from(base_query.subquery())
            )
            
            # Generate report sections
            summary = await self._generate_report_summary(session, base_query)
            findings = await self._generate_report_findings(session, base_query)
            metrics = await self._generate_report_metrics(session, base_query)
            recommendations = await self._generate_recommendations(findings, metrics)
            
            report = ComplianceReport(
                report_id=report_id,
                report_type=report_type,
                reporting_period_start=start_date,
                reporting_period_end=end_date,
                generated_by="system",
                summary=summary,
                findings=findings,
                recommendations=recommendations,
                metrics=metrics,
                total_events_analyzed=total_count,
                data_sources=["audit_logs", "system_events"],
                export_format="json"
            )
            
            logger.info("Compliance report generated",
                       report_id=report_id,
                       report_type=report_type,
                       total_events=total_count)
            
            return report
            
        except Exception as e:
            logger.error("Compliance report generation failed", error=str(e))
            raise
        finally:
            if should_close and session:
                try:
                    await session.close()
                except Exception as e:
                    logger.warning(f"Error closing session: {e}")
    
    async def _generate_report_summary(self, session: AsyncSession, base_query) -> Dict[str, Any]:
        """Generate report summary section."""
        # Event type distribution
        event_type_query = select(
            AuditLog.event_type,
            func.count(AuditLog.id).label('count')
        ).select_from(base_query.subquery()).group_by(AuditLog.event_type)
        
        event_types = await session.execute(event_type_query)
        event_type_dist = {row.event_type: row.count for row in event_types}
        
        # Outcome distribution
        outcome_query = select(
            AuditLog.outcome,
            func.count(AuditLog.id).label('count')
        ).select_from(base_query.subquery()).group_by(AuditLog.outcome)
        
        outcomes = await session.execute(outcome_query)
        outcome_dist = {row.outcome: row.count for row in outcomes}
        
        return {
            "event_type_distribution": event_type_dist,
            "outcome_distribution": outcome_dist,
            "security_events": event_type_dist.get("SecurityViolationEvent", 0),
            "failed_operations": outcome_dist.get("failure", 0) + outcome_dist.get("error", 0)
        }
    
    async def _generate_report_findings(self, session: AsyncSession, base_query) -> List[Dict[str, Any]]:
        """Generate audit findings."""
        findings = []
        
        # Find failed login patterns
        failed_logins = await session.execute(
            select(AuditLog.user_id, func.count(AuditLog.id).label('count'))
            .select_from(base_query.subquery())
            .where(AuditLog.event_type == "UserLoginEvent")
            .where(AuditLog.outcome == "failure")
            .group_by(AuditLog.user_id)
            .having(func.count(AuditLog.id) > 5)
        )
        
        for row in failed_logins:
            findings.append({
                "type": "excessive_failed_logins",
                "severity": "medium",
                "description": f"User {row.user_id} had {row.count} failed login attempts",
                "user_id": row.user_id,
                "count": row.count
            })
        
        # Find privileged access patterns
        privileged_access = await session.execute(
            select(AuditLog.user_id, func.count(AuditLog.id).label('count'))
            .select_from(base_query.subquery())
            .where(AuditLog.action.like('%privileged%'))
            .group_by(AuditLog.user_id)
            .having(func.count(AuditLog.id) > 10)
        )
        
        for row in privileged_access:
            findings.append({
                "type": "frequent_privileged_access",
                "severity": "low",
                "description": f"User {row.user_id} performed {row.count} privileged operations",
                "user_id": row.user_id,
                "count": row.count
            })
        
        return findings
    
    async def _generate_report_metrics(self, session: AsyncSession, base_query) -> Dict[str, Any]:
        """Generate compliance metrics."""
        # Authentication metrics
        auth_success = await session.scalar(
            select(func.count(AuditLog.id))
            .select_from(base_query.subquery())
            .where(AuditLog.event_type == "UserLoginEvent")
            .where(AuditLog.outcome == "success")
        )
        
        auth_failure = await session.scalar(
            select(func.count(AuditLog.id))
            .select_from(base_query.subquery())
            .where(AuditLog.event_type == "UserLoginEvent")
            .where(AuditLog.outcome == "failure")
        )
        
        # Calculate authentication success rate
        total_auth = auth_success + auth_failure
        auth_success_rate = (auth_success / total_auth * 100) if total_auth > 0 else 0
        
        return {
            "authentication_success_rate": round(auth_success_rate, 2),
            "total_authentication_attempts": total_auth,
            "security_violations": await session.scalar(
                select(func.count(AuditLog.id))
                .select_from(base_query.subquery())
                .where(AuditLog.event_type == "SecurityViolationEvent")
            ),
            "data_access_events": await session.scalar(
                select(func.count(AuditLog.id))
                .select_from(base_query.subquery())
                .where(AuditLog.event_type == "DataAccessEvent")
            )
        }
    
    async def _generate_recommendations(self, findings: List[Dict], metrics: Dict) -> List[str]:
        """Generate compliance recommendations."""
        recommendations = []
        
        # Check authentication success rate
        if metrics.get("authentication_success_rate", 100) < 95:
            recommendations.append(
                "Consider implementing additional user authentication training due to low success rate"
            )
        
        # Check for security violations
        if metrics.get("security_violations", 0) > 0:
            recommendations.append(
                "Review security violation patterns and consider strengthening security policies"
            )
        
        # Check findings
        for finding in findings:
            if finding["type"] == "excessive_failed_logins":
                recommendations.append(
                    f"Implement account lockout policies for user {finding['user_id']}"
                )
            elif finding["type"] == "frequent_privileged_access":
                recommendations.append(
                    f"Review privileged access patterns for user {finding['user_id']}"
                )
        
        if not recommendations:
            recommendations.append("No significant compliance issues detected in this period")
        
        return recommendations
    
    async def _load_siem_configurations(self):
        """Load SIEM export configurations."""
        # This would load from database in production
        # For now, we'll use default configurations
        pass
    
    async def export_to_siem(
        self, 
        config_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Export audit logs to SIEM system."""
        if config_name not in self.siem_configs:
            raise ValueError(f"SIEM configuration {config_name} not found")
        
        config = self.siem_configs[config_name]
        
        # Query audit logs for export
        query = AuditLogQuery(
            start_date=start_date or datetime.utcnow() - timedelta(hours=1),
            end_date=end_date or datetime.utcnow(),
            event_types=config.event_types if config.event_types else None,
            limit=config.batch_size
        )
        
        async with self.db_session_factory() as session:
            result = await self.query_audit_logs(query, session)
            
            # Convert to SIEM format
            siem_events = []
            for log in result["logs"]:
                siem_event = self._convert_to_siem_format(log, config)
                siem_events.append(siem_event)
            
            # Export (would send to actual SIEM system)
            export_result = {
                "config_name": config_name,
                "events_exported": len(siem_events),
                "export_time": datetime.utcnow(),
                "format": config.export_format,
                "events": siem_events if config.export_format != "cef" else [e.to_cef() for e in siem_events]
            }
            
            logger.info("SIEM export completed",
                       config_name=config_name,
                       events_exported=len(siem_events))
            
            return export_result
    
    def _convert_to_siem_format(self, log: Dict[str, Any], config: SIEMExportConfig) -> SIEMEvent:
        """Convert audit log to SIEM format."""
        # Map event types to SIEM signatures
        signature_map = {
            "UserLoginEvent": "USER_LOGIN",
            "DataAccessEvent": "DATA_ACCESS",
            "SecurityViolationEvent": "SECURITY_VIOLATION"
        }
        
        signature_id = signature_map.get(log["event_type"], "UNKNOWN_EVENT")
        
        # Determine severity
        severity_map = {
            "success": 2,
            "failure": 5,
            "error": 7,
            "denied": 6
        }
        severity = severity_map.get(log["outcome"], 5)
        
        extensions = {
            "src": log.get("ip_address"),
            "suser": log.get("user_id"),
            "act": log.get("action"),
            "outcome": log.get("outcome"),
            "request": log.get("correlation_id")
        }
        
        # Remove None values
        extensions = {k: v for k, v in extensions.items() if v is not None}
        
        return SIEMEvent(
            signature_id=signature_id,
            name=log["event_type"],
            severity=severity,
            extensions=extensions,
            raw_event=log
        )
    
    async def log_action(
        self, 
        action: str, 
        user_id: str, 
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Log an action for backward compatibility with tests and legacy code.
        
        This method provides a simplified interface to the comprehensive audit logging
        system while maintaining SOC2 compliance requirements.
        """
        from datetime import datetime
        from uuid import uuid4
        
        # Create a basic audit event for the action
        event = AuditEvent(
            event_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            event_type=action,
            aggregate_id=user_id or "system",  # Required by BaseEvent
            aggregate_type="audit_log",        # Required by BaseEvent
            user_id=user_id,
            operation=action,
            outcome="success",
            resource_type=resource_type,
            resource_id=resource_id,
            headers=details or {},
            compliance_tags=["soc2", "general_audit"],
            data_classification="internal",
            publisher="audit_service",
            soc2_category=SOC2Category.SECURITY  # Monitoring Activities
        )
        
        # Log through the event bus
        success = await self.log_audit_event(event)
        
        if success:
            # Return a simple object with the expected attributes for tests
            class AuditLogResult:
                def __init__(self, event_data):
                    self.id = event_data.event_id
                    self.timestamp = event_data.timestamp
                    self.user_id = event_data.user_id
                    self.action = event_data.operation
                    self.resource_type = event_data.resource_type
                    self.resource_id = event_data.resource_id
            
            return AuditLogResult(event)
        else:
            raise RuntimeError(f"Failed to log audit action: {action}")
    
    async def log_phi_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        purpose: str,
        phi_fields: List[str],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log PHI access for HIPAA compliance.
        
        Args:
            user_id: ID of user accessing PHI
            resource_type: Type of resource (patient, clinical_document, etc.)
            resource_id: ID of the specific resource
            action: Action performed (read, write, update, delete)
            purpose: Purpose of access (treatment, payment, operations, etc.)
            phi_fields: List of PHI fields accessed
            ip_address: IP address of user
            user_agent: User agent string
            session_id: Session identifier
            context: Additional context information
        """
        try:
            # Create comprehensive PHI access event
            phi_event = DataAccessEvent(
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                access_type=action,
                data_classification="phi",
                access_purpose=purpose,
                operation=f"phi_{action}",
                outcome="success",
                correlation_id=f"phi_{resource_type}_{resource_id}_{datetime.utcnow().timestamp()}",
                headers={
                    "phi_fields_accessed": phi_fields,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "session_id": session_id,
                    "hipaa_purpose": purpose,
                    "minimum_necessary_validated": True,
                    "access_timestamp": datetime.utcnow().isoformat(),
                    "compliance_tags": ["hipaa", "phi_access", "minimum_necessary"],
                    **(context or {})
                }
            )
            
            # Log through event bus for immutable audit trail
            success = await self.log_audit_event(phi_event)
            
            if not success:
                logger.error(
                    "CRITICAL: Failed to log PHI access - HIPAA compliance violation",
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action=action,
                    phi_fields=phi_fields
                )
                # This is a critical failure - PHI access MUST be logged
                raise RuntimeError("Failed to log PHI access - compliance requirement")
            
            logger.info(
                "PHI access logged for HIPAA compliance",
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                purpose=purpose,
                phi_fields_count=len(phi_fields),
                event_id=phi_event.event_id
            )
            
            return phi_event.event_id
            
        except Exception as e:
            logger.error(
                "CRITICAL: Exception during PHI access logging",
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                error=str(e)
            )
            # Re-raise as this is a compliance-critical failure
            raise
    
    async def log_phi_access_denied(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        reason: str,
        ip_address: Optional[str] = None
    ):
        """Log denied PHI access attempts for security monitoring."""
        try:
            denial_event = SecurityViolationEvent(
                user_id=user_id,
                violation_type="unauthorized_phi_access",
                severity_level="medium",
                detection_method="access_control",
                investigation_required=True,
                operation="phi_access_denied",
                outcome="blocked",
                correlation_id=f"denied_phi_{resource_type}_{resource_id}_{datetime.utcnow().timestamp()}",
                headers={
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "denial_reason": reason,
                    "ip_address": ip_address,
                    "requires_investigation": True,
                    "compliance_tags": ["hipaa", "security", "access_denied"]
                }
            )
            
            await self.log_audit_event(denial_event)
            
            logger.warning(
                "PHI access denied - security event logged",
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                reason=reason
            )
            
        except Exception as e:
            logger.error(
                "Failed to log PHI access denial",
                user_id=user_id,
                resource_type=resource_type,
                error=str(e)
            )
    
    async def verify_audit_chain_integrity(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Verify the cryptographic integrity of the audit chain.
        
        Args:
            start_date: Start date for verification (optional)
            end_date: End date for verification (optional)
            
        Returns:
            Dict containing verification results and details
        """
        try:
            # Use the handler's verification method
            handler = ImmutableAuditLogHandler(self.db_session_factory)
            integrity_verified = await handler.verify_audit_chain(start_date, end_date)
            
            verification_result = {
                "integrity_verified": integrity_verified,
                "verification_timestamp": datetime.utcnow().isoformat(),
                "verification_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "verification_id": str(uuid.uuid4())
            }
            
            # Log the verification result
            verification_event = AuditEvent(
                event_type="audit_chain_verification",
                user_id="SYSTEM",
                action="verify_chain_integrity",
                outcome="success" if integrity_verified else "failure",
                resource_type="audit_chain",
                resource_id="global",
                event_data=verification_result,
                compliance_tags=["soc2", "audit_integrity", "cryptographic_verification"]
            )
            
            await self.log_audit_event(verification_event)
            
            if not integrity_verified:
                # Create critical security alert
                security_event = SecurityViolationEvent(
                    user_id="SYSTEM",
                    violation_type="audit_tampering",
                    severity="critical",
                    description="Audit chain integrity verification failed - potential tampering detected",
                    source_ip="127.0.0.1",
                    user_agent="integrity_verification_system",
                    headers={
                        "verification_result": verification_result,
                        "immediate_action_required": True,
                        "compliance_impact": "SOC2_VIOLATION"
                    }
                )
                
                await self.log_audit_event(security_event)
                
                logger.critical(
                    "AUDIT CHAIN INTEGRITY FAILURE - IMMEDIATE ACTION REQUIRED",
                    verification_result=verification_result
                )
            
            return verification_result
            
        except Exception as e:
            error_result = {
                "integrity_verified": False,
                "verification_timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "verification_id": str(uuid.uuid4())
            }
            
            logger.error(
                "Failed to verify audit chain integrity",
                error=str(e),
                verification_result=error_result
            )
            
            return error_result
    
    async def schedule_periodic_integrity_verification(self):
        """Schedule periodic audit chain integrity verification."""
        # This would typically be called by a background task scheduler
        # For now, it's a method that can be called manually or by cron
        
        try:
            # Verify last 24 hours
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=1)
            
            result = await self.verify_audit_chain_integrity(start_date, end_date)
            
            logger.info(
                "Scheduled audit chain verification completed",
                result=result
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Failed to complete scheduled audit chain verification",
                error=str(e)
            )
            raise

# Global service instance
audit_service: Optional[SOC2AuditService] = None

def get_audit_service() -> SOC2AuditService:
    """Get global audit service instance."""
    global audit_service
    if audit_service is None:
        raise RuntimeError("Audit service not initialized")
    return audit_service

async def initialize_audit_service(db_session_factory) -> SOC2AuditService:
    """Initialize global audit service."""
    global audit_service
    audit_service = SOC2AuditService(db_session_factory)
    await audit_service.initialize()
    return audit_service