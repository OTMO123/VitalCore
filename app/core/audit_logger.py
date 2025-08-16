"""
Immutable Audit Logging System with Hash Chaining

SOC2-compliant audit logging with blockchain-style integrity verification
and HIPAA-compliant PHI access tracking.
"""

import asyncio
import hashlib
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from dataclasses import dataclass, asdict
import structlog

from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, ConfigDict

from app.core.database_unified import get_db, AuditLog, DataClassification
from app.core.security import security_manager
from app.core.config import get_settings

logger = structlog.get_logger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events for classification."""
    # Authentication Events
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    USER_LOGIN_FAILED = "USER_LOGIN_FAILED"
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"
    
    # Data Access Events
    PHI_ACCESSED = "PHI_ACCESSED"
    PHI_CREATED = "PHI_CREATED"
    PHI_UPDATED = "PHI_UPDATED"
    PHI_DELETED = "PHI_DELETED"
    PHI_EXPORTED = "PHI_EXPORTED"
    
    # Patient Management Events
    PATIENT_CREATED = "PATIENT_CREATED"
    PATIENT_UPDATED = "PATIENT_UPDATED"
    PATIENT_ACCESSED = "PATIENT_ACCESSED"
    PATIENT_SEARCH = "PATIENT_SEARCH"
    
    # Clinical Document Events
    DOCUMENT_CREATED = "DOCUMENT_CREATED"
    DOCUMENT_ACCESSED = "DOCUMENT_ACCESSED"
    DOCUMENT_UPDATED = "DOCUMENT_UPDATED"
    DOCUMENT_DELETED = "DOCUMENT_DELETED"
    
    # Consent Management Events
    CONSENT_GRANTED = "CONSENT_GRANTED"
    CONSENT_WITHDRAWN = "CONSENT_WITHDRAWN"
    CONSENT_UPDATED = "CONSENT_UPDATED"
    
    # System Events
    SYSTEM_ACCESS = "SYSTEM_ACCESS"
    CONFIG_CHANGED = "CONFIG_CHANGED"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"
    DATA_BREACH_DETECTED = "DATA_BREACH_DETECTED"
    
    # API Events
    API_REQUEST = "API_REQUEST"
    API_RESPONSE = "API_RESPONSE"
    API_ERROR = "API_ERROR"
    
    # IRIS Integration Events
    IRIS_SYNC_STARTED = "IRIS_SYNC_STARTED"
    IRIS_SYNC_COMPLETED = "IRIS_SYNC_COMPLETED"
    IRIS_SYNC_FAILED = "IRIS_SYNC_FAILED"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditContext:
    """Context information for audit events."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    tenant_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class AuditEntry(BaseModel):
    """Immutable audit log entry."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now())
    event_type: AuditEventType
    severity: AuditSeverity
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    
    # Security fields
    checksum: str = ""
    previous_hash: str = ""
    sequence_number: int = 0
    
    # PHI/PII classification
    contains_phi: bool = False
    data_classification: DataClassification = DataClassification.PUBLIC
    
    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class ImmutableAuditLogger:
    """
    Immutable audit logger with hash chaining for integrity verification.
    
    Implements blockchain-style integrity checks to detect tampering
    and ensure SOC2/HIPAA compliance.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._lock = asyncio.Lock()
        self._sequence_counter = 0
        self._last_hash = "genesis"  # Genesis hash for chain start
        
    async def log_event(
        self,
        event_type: AuditEventType,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[AuditContext] = None,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        contains_phi: bool = False,
        data_classification: DataClassification = DataClassification.PUBLIC,
        db: Optional[AsyncSession] = None
    ) -> str:
        """
        Log an audit event with immutable hash chaining.
        
        Args:
            event_type: Type of audit event
            message: Human-readable message
            details: Additional event details
            context: Audit context (user, session, etc.)
            severity: Event severity level
            contains_phi: Whether event contains PHI data
            data_classification: Data classification level
            db: Database session
        
        Returns:
            Unique audit entry ID
        """
        async with self._lock:
            try:
                # Get database session if not provided
                external_session = db is not None
                if db is None:
                    async for session in get_db():
                        db = session
                        break
                
                # Increment sequence counter
                self._sequence_counter += 1
                
                # Create audit entry
                entry = AuditEntry(
                    event_type=event_type,
                    severity=severity,
                    message=message,
                    details=details or {},
                    context=context.to_dict() if context else {},
                    contains_phi=contains_phi,
                    data_classification=data_classification,
                    sequence_number=self._sequence_counter,
                    previous_hash=self._last_hash
                )
                
                # Calculate entry hash (excluding checksum field)
                entry_data = entry.model_dump(exclude={"checksum"})
                entry_json = json.dumps(entry_data, sort_keys=True, default=str)
                entry_hash = hashlib.sha256(entry_json.encode()).hexdigest()
                entry.checksum = entry_hash
                
                # Create database record with timezone-naive timestamp
                timestamp_naive = entry.timestamp.replace(tzinfo=None) if entry.timestamp.tzinfo else entry.timestamp
                audit_record = AuditLog(
                    id=entry.id,
                    timestamp=timestamp_naive,
                    event_type=entry.event_type.value if hasattr(entry.event_type, 'value') else entry.event_type,
                    action=entry.message,  # Map message to action field
                    outcome="success",  # Default to success
                    config_metadata=entry.details,  # Map details to config_metadata
                    data_classification=entry.data_classification,
                    previous_log_hash=entry.previous_hash,
                    log_hash=entry.checksum
                )
                
                # Save to database
                db.add(audit_record)
                
                # Handle commit/flush based on session ownership
                if external_session:
                    # Using external session (bundle mode) - just flush
                    # The external session manager will handle the commit
                    await db.flush()
                else:
                    # Using our own session - commit immediately
                    await db.commit()
                
                # Update last hash for chain
                self._last_hash = entry_hash
                
                # Log to structured logger
                logger.info(
                    "Audit event logged",
                    audit_id=entry.id,
                    event_type=entry.event_type if isinstance(entry.event_type, str) else entry.event_type.value,
                    severity=entry.severity if isinstance(entry.severity, str) else entry.severity.value,
                    sequence=entry.sequence_number,
                    checksum=entry.checksum[:16],  # Partial checksum for logs
                    contains_phi=entry.contains_phi
                )
                
                return entry.id
                
            except Exception as e:
                logger.error("Failed to log audit event", error=str(e))
                # Fallback: Log to structured logger only
                logger.critical(
                    "AUDIT_FAILURE",
                    event_type=event_type if isinstance(event_type, str) else event_type.value,
                    message=message,
                    error=str(e),
                    fallback_log=True
                )
                raise
    
    async def verify_audit_integrity(
        self,
        start_sequence: Optional[int] = None,
        end_sequence: Optional[int] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Verify audit log integrity using hash chain validation.
        
        Args:
            start_sequence: Starting sequence number (default: 1)
            end_sequence: Ending sequence number (default: latest)
            db: Database session
        
        Returns:
            Integrity verification report
        """
        try:
            # Get database session if not provided
            if db is None:
                async for session in get_db():
                    db = session
                    break
            
            # Build query
            query = select(AuditLog).order_by(AuditLog.sequence_number)
            
            if start_sequence:
                query = query.where(AuditLog.sequence_number >= start_sequence)
            if end_sequence:
                query = query.where(AuditLog.sequence_number <= end_sequence)
            
            # Execute query
            result = await db.execute(query)
            audit_logs = result.scalars().all()
            
            if not audit_logs:
                return {
                    "status": "no_records",
                    "message": "No audit records found in specified range",
                    "verified_count": 0,
                    "integrity_violations": []
                }
            
            # Verify integrity
            verification_report = {
                "status": "valid",
                "verified_count": 0,
                "integrity_violations": [],
                "start_sequence": audit_logs[0].sequence_number,
                "end_sequence": audit_logs[-1].sequence_number,
                "verification_timestamp": datetime.utcnow().isoformat()
            }
            
            expected_previous_hash = "genesis"
            
            for audit_log in audit_logs:
                # Verify hash chain
                if audit_log.previous_hash != expected_previous_hash:
                    verification_report["integrity_violations"].append({
                        "type": "broken_chain",
                        "sequence": audit_log.sequence_number,
                        "expected_previous_hash": expected_previous_hash,
                        "actual_previous_hash": audit_log.previous_hash,
                        "audit_id": audit_log.id
                    })
                
                # Verify checksum
                entry_data = {
                    "id": audit_log.id,
                    "timestamp": audit_log.created_at.isoformat(),
                    "event_type": audit_log.event_type,
                    "severity": audit_log.severity,
                    "message": audit_log.message,
                    "details": audit_log.details,
                    "context": audit_log.context,
                    "previous_hash": audit_log.previous_hash,
                    "sequence_number": audit_log.sequence_number,
                    "contains_phi": audit_log.contains_phi,
                    "data_classification": audit_log.data_classification.value
                }
                
                entry_json = json.dumps(entry_data, sort_keys=True, default=str)
                expected_checksum = hashlib.sha256(entry_json.encode()).hexdigest()
                
                if audit_log.checksum != expected_checksum:
                    verification_report["integrity_violations"].append({
                        "type": "checksum_mismatch",
                        "sequence": audit_log.sequence_number,
                        "expected_checksum": expected_checksum,
                        "actual_checksum": audit_log.checksum,
                        "audit_id": audit_log.id
                    })
                
                # Update for next iteration
                expected_previous_hash = audit_log.checksum
                verification_report["verified_count"] += 1
            
            # Set overall status
            if verification_report["integrity_violations"]:
                verification_report["status"] = "violations_detected"
                logger.warning(
                    "Audit integrity violations detected",
                    violations=len(verification_report["integrity_violations"]),
                    verified_count=verification_report["verified_count"]
                )
            else:
                logger.info(
                    "Audit integrity verification passed",
                    verified_count=verification_report["verified_count"]
                )
            
            return verification_report
            
        except Exception as e:
            logger.error("Audit integrity verification failed", error=str(e))
            return {
                "status": "verification_failed",
                "error": str(e),
                "verification_timestamp": datetime.utcnow().isoformat()
            }
    
    async def search_audit_logs(
        self,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[AuditSeverity] = None,
        contains_phi: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
        db: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """
        Search audit logs with filtering.
        
        Args:
            event_type: Filter by event type
            user_id: Filter by user ID
            start_time: Start time filter
            end_time: End time filter
            severity: Filter by severity
            contains_phi: Filter by PHI content
            limit: Maximum records to return
            offset: Records to skip
            db: Database session
        
        Returns:
            List of matching audit log entries
        """
        try:
            # Get database session if not provided
            if db is None:
                async for session in get_db():
                    db = session
                    break
            
            # Build query
            query = select(AuditLog).order_by(desc(AuditLog.created_at))
            
            # Apply filters
            if event_type:
                query = query.where(AuditLog.event_type == event_type.value)
            
            if user_id:
                query = query.where(AuditLog.context["user_id"].astext == user_id)
            
            if start_time:
                query = query.where(AuditLog.created_at >= start_time)
            
            if end_time:
                query = query.where(AuditLog.created_at <= end_time)
            
            if severity:
                query = query.where(AuditLog.severity == severity.value)
            
            if contains_phi is not None:
                query = query.where(AuditLog.contains_phi == contains_phi)
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            # Execute query
            result = await db.execute(query)
            audit_logs = result.scalars().all()
            
            # Convert to dict format
            audit_entries = []
            for log in audit_logs:
                entry = {
                    "id": log.id,
                    "timestamp": log.created_at.isoformat(),
                    "event_type": log.event_type,
                    "severity": log.severity,
                    "message": log.message,
                    "details": log.details,
                    "context": log.context,
                    "sequence_number": log.sequence_number,
                    "contains_phi": log.contains_phi,
                    "data_classification": log.data_classification.value,
                    "checksum": log.checksum
                }
                audit_entries.append(entry)
            
            logger.info(
                "Audit log search completed",
                results_count=len(audit_entries),
                filters={
                    "event_type": event_type.value if event_type else None,
                    "user_id": user_id,
                    "severity": severity.value if severity else None
                }
            )
            
            return audit_entries
            
        except Exception as e:
            logger.error("Audit log search failed", error=str(e))
            return []
    
    async def get_phi_access_audit(
        self,
        patient_id: Optional[str] = None,
        user_id: Optional[str] = None,
        hours: int = 24,
        db: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """
        Get PHI access audit logs for HIPAA compliance.
        
        Args:
            patient_id: Filter by patient ID
            user_id: Filter by accessing user
            hours: Hours to look back
            db: Database session
        
        Returns:
            List of PHI access events
        """
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        phi_events = await self.search_audit_logs(
            event_type=AuditEventType.PHI_ACCESSED,
            user_id=user_id,
            start_time=start_time,
            contains_phi=True,
            db=db
        )
        
        # Filter by patient ID if specified
        if patient_id:
            phi_events = [
                event for event in phi_events
                if event.get("details", {}).get("patient_id") == patient_id
            ]
        
        return phi_events


# Global audit logger instance
audit_logger = ImmutableAuditLogger()


# Convenience functions for common audit events
async def log_user_login(user_id: str, context: AuditContext, success: bool = True, db: Optional[AsyncSession] = None):
    """Log user login event."""
    event_type = AuditEventType.USER_LOGIN if success else AuditEventType.USER_LOGIN_FAILED
    severity = AuditSeverity.MEDIUM if success else AuditSeverity.HIGH
    message = f"User {'login successful' if success else 'login failed'}"
    
    await audit_logger.log_event(
        event_type=event_type,
        message=message,
        details={"user_id": user_id, "success": success},
        context=context,
        severity=severity,
        db=db
    )


async def log_phi_access(
    user_id: str,
    patient_id: str,
    fields_accessed: List[str],
    purpose: str,
    context: AuditContext,
    db: Optional[AsyncSession] = None
):
    """Log PHI data access event."""
    await audit_logger.log_event(
        event_type=AuditEventType.PHI_ACCESSED,
        message=f"PHI data accessed for patient {patient_id}",
        details={
            "patient_id": patient_id,
            "fields_accessed": fields_accessed,
            "access_purpose": purpose,
            "field_count": len(fields_accessed)
        },
        context=context,
        severity=AuditSeverity.HIGH,
        contains_phi=True,
        data_classification=DataClassification.PHI.value,
        db=db
    )


async def log_security_violation(
    violation_type: str,
    description: str,
    context: AuditContext,
    details: Optional[Dict[str, Any]] = None,
    db: Optional[AsyncSession] = None
):
    """Log security violation event."""
    await audit_logger.log_event(
        event_type=AuditEventType.SECURITY_VIOLATION,
        message=f"Security violation detected: {violation_type}",
        details={
            "violation_type": violation_type,
            "description": description,
            **(details or {})
        },
        context=context,
        severity=AuditSeverity.CRITICAL,
        db=db
    )


async def log_patient_operation(
    operation: str,
    patient_id: str,
    user_id: str,
    context: AuditContext,
    details: Optional[Dict[str, Any]] = None,
    db: Optional[AsyncSession] = None
):
    """Log patient management operation."""
    event_type_map = {
        "create": AuditEventType.PATIENT_CREATED,
        "update": AuditEventType.PATIENT_UPDATED,
        "access": AuditEventType.PATIENT_ACCESSED,
        "search": AuditEventType.PATIENT_SEARCH
    }
    
    event_type = event_type_map.get(operation, AuditEventType.PATIENT_ACCESSED)
    
    await audit_logger.log_event(
        event_type=event_type,
        message=f"Patient {operation} operation",
        details={
            "patient_id": patient_id,
            "operation": operation,
            **(details or {})
        },
        context=context,
        severity=AuditSeverity.MEDIUM,
        contains_phi=True,
        data_classification=DataClassification.PHI.value,
        db=db
    )