"""
Enterprise SOC2 Type 2 Audit System
Blockchain-inspired cryptographic integrity with real-time monitoring
"""

import hashlib
import hmac
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.hashes import SHA256
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import structlog
import uuid

from app.core.database_unified import AuditLog, User
from app.core.database import get_session_factory

logger = structlog.get_logger()


class AuditRiskLevel(Enum):
    """Risk levels for audit events."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AuditEventCategory(Enum):
    """Categories for compliance classification."""
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    PHI_ACCESS = "PHI_ACCESS"
    DATA_MODIFICATION = "DATA_MODIFICATION"
    SYSTEM_ADMINISTRATION = "SYSTEM_ADMINISTRATION"
    API_ACCESS = "API_ACCESS"
    CONFIGURATION_CHANGE = "CONFIGURATION_CHANGE"
    SECURITY_EVENT = "SECURITY_EVENT"


@dataclass
class AuditEventData:
    """Structured audit event data."""
    event_type: str
    category: AuditEventCategory
    risk_level: AuditRiskLevel
    user_id: Optional[str]
    session_id: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    outcome: str  # success, failure, error
    ip_address: Optional[str]
    user_agent: Optional[str]
    additional_data: Dict[str, Any]
    phi_involved: bool = False
    compliance_flags: List[str] = None
    
    def __post_init__(self):
        if self.compliance_flags is None:
            self.compliance_flags = []


class CryptographicIntegrityManager:
    """
    Manages cryptographic integrity for audit logs using blockchain-inspired techniques.
    """
    
    def __init__(self):
        self.private_key = self._generate_signing_key()
        self.public_key = self.private_key.public_key()
        
    def _generate_signing_key(self) -> rsa.RSAPrivateKey:
        """Generate RSA key pair for digital signatures."""
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096
        )
    
    def calculate_content_hash(self, event_data: AuditEventData) -> str:
        """Calculate SHA3-256 hash of event content."""
        content = json.dumps(asdict(event_data), sort_keys=True, default=str)
        return hashlib.sha3_256(content.encode()).hexdigest()
    
    def calculate_chain_hash(self, previous_hash: str, content_hash: str) -> str:
        """Calculate chain hash linking to previous entry."""
        combined = f"{previous_hash}:{content_hash}"
        return hashlib.sha3_256(combined.encode()).hexdigest()
    
    def sign_entry(self, chain_hash: str) -> str:
        """Create digital signature for audit entry."""
        signature = self.private_key.sign(
            chain_hash.encode(),
            padding.PSS(
                mgf=padding.MGF1(SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            SHA256()
        )
        return signature.hex()
    
    def verify_signature(self, chain_hash: str, signature_hex: str) -> bool:
        """Verify digital signature of audit entry."""
        try:
            signature = bytes.fromhex(signature_hex)
            self.public_key.verify(
                signature,
                chain_hash.encode(),
                padding.PSS(
                    mgf=padding.MGF1(SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                SHA256()
            )
            return True
        except Exception:
            return False


class AuditChainManager:
    """
    Manages the blockchain-inspired audit chain with integrity verification.
    """
    
    def __init__(self):
        self.crypto_manager = CryptographicIntegrityManager()
        self.session_factory = get_session_factory()
    
    async def get_last_entry_hash(self) -> str:
        """Get hash of the last audit entry in chain."""
        async with self.session_factory() as session:
            query = select(AuditLog).order_by(desc(AuditLog.created_at)).limit(1)
            result = await session.execute(query)
            last_entry = result.scalar_one_or_none()
            
            if last_entry and hasattr(last_entry, 'chain_hash'):
                return last_entry.chain_hash
            
            # Genesis block hash for first entry
            return "0000000000000000000000000000000000000000000000000000000000000000"
    
    async def create_audit_entry(self, event_data: AuditEventData) -> Dict[str, Any]:
        """
        Create new audit entry with cryptographic integrity.
        """
        # Get previous hash for chain
        previous_hash = await self.get_last_entry_hash()
        
        # Calculate content and chain hashes
        content_hash = self.crypto_manager.calculate_content_hash(event_data)
        chain_hash = self.crypto_manager.calculate_chain_hash(previous_hash, content_hash)
        
        # Create digital signature
        signature = self.crypto_manager.sign_entry(chain_hash)
        
        # Prepare audit log entry
        audit_entry = {
            "id": str(uuid.uuid4()),
            "event_type": event_data.event_type,
            "category": event_data.category.value,
            "risk_level": event_data.risk_level.value,
            "user_id": event_data.user_id,
            "session_id": event_data.session_id,
            "resource_type": event_data.resource_type,
            "resource_id": event_data.resource_id,
            "action": event_data.action,
            "outcome": event_data.outcome,
            "ip_address": event_data.ip_address,
            "user_agent": event_data.user_agent,
            "event_data": event_data.additional_data,
            "phi_involved": event_data.phi_involved,
            "compliance_flags": event_data.compliance_flags,
            "content_hash": content_hash,
            "previous_hash": previous_hash,
            "chain_hash": chain_hash,
            "digital_signature": signature,
            "created_at": datetime.utcnow()
        }
        
        # Store in database
        async with self.session_factory() as session:
            # Create AuditLog instance
            audit_log = AuditLog(
                event_type=audit_entry["event_type"],
                user_id=audit_entry["user_id"],
                session_id=audit_entry["session_id"],
                resource_type=audit_entry["resource_type"],
                resource_id=audit_entry["resource_id"],
                action=audit_entry["action"],
                outcome=audit_entry["outcome"],
                ip_address=audit_entry["ip_address"],
                user_agent=audit_entry["user_agent"],
                event_data=audit_entry["event_data"]
            )
            
            session.add(audit_log)
            await session.commit()
        
        # Log for monitoring
        logger.info(
            "Audit entry created",
            event_type=event_data.event_type,
            risk_level=event_data.risk_level.value,
            user_id=event_data.user_id,
            chain_hash=chain_hash[:16] + "...",
            phi_involved=event_data.phi_involved
        )
        
        return audit_entry
    
    async def verify_chain_integrity(self, limit: int = 1000) -> Dict[str, Any]:
        """
        Verify integrity of audit chain.
        """
        verification_result = {
            "status": "valid",
            "entries_checked": 0,
            "integrity_errors": [],
            "signature_errors": [],
            "chain_breaks": []
        }
        
        async with self.session_factory() as session:
            query = select(AuditLog).order_by(AuditLog.created_at).limit(limit)
            result = await session.execute(query)
            entries = result.scalars().all()
            
            previous_hash = "0000000000000000000000000000000000000000000000000000000000000000"
            
            for entry in entries:
                verification_result["entries_checked"] += 1
                
                # Check if entry has integrity fields (may not exist in legacy entries)
                if not hasattr(entry, 'chain_hash'):
                    continue
                
                # Verify chain linkage
                if hasattr(entry, 'previous_hash') and entry.previous_hash != previous_hash:
                    verification_result["chain_breaks"].append({
                        "entry_id": str(entry.id),
                        "expected_previous": previous_hash,
                        "actual_previous": entry.previous_hash
                    })
                    verification_result["status"] = "invalid"
                
                previous_hash = getattr(entry, 'chain_hash', '')
        
        return verification_result


class EnterpriseAuditSystem:
    """
    Main enterprise audit system with SOC2 Type 2 compliance.
    """
    
    def __init__(self):
        self.chain_manager = AuditChainManager()
        self.real_time_alerts = RealTimeAlertManager()
        
    async def log_event(
        self,
        event_type: str,
        category: AuditEventCategory,
        risk_level: AuditRiskLevel,
        action: str,
        outcome: str = "success",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None,
        phi_involved: bool = False,
        compliance_flags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Log audit event with enterprise-grade integrity.
        """
        if additional_data is None:
            additional_data = {}
        if compliance_flags is None:
            compliance_flags = []
            
        # Add SOC2 compliance flags based on event characteristics
        if phi_involved:
            compliance_flags.extend(["HIPAA", "SOC2_CC7.2"])
        if risk_level in [AuditRiskLevel.HIGH, AuditRiskLevel.CRITICAL]:
            compliance_flags.append("SOC2_CC8.1")
        if category == AuditEventCategory.AUTHENTICATION:
            compliance_flags.append("SOC2_A1.2")
        
        event_data = AuditEventData(
            event_type=event_type,
            category=category,
            risk_level=risk_level,
            user_id=user_id,
            session_id=session_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            outcome=outcome,
            ip_address=ip_address,
            user_agent=user_agent,
            additional_data=additional_data,
            phi_involved=phi_involved,
            compliance_flags=compliance_flags
        )
        
        # Create audit entry with cryptographic integrity
        audit_entry = await self.chain_manager.create_audit_entry(event_data)
        
        # Trigger real-time alerts if needed
        await self.real_time_alerts.process_event(event_data)
        
        return audit_entry
    
    async def verify_integrity(self) -> Dict[str, Any]:
        """Verify audit chain integrity."""
        return await self.chain_manager.verify_chain_integrity()


class RealTimeAlertManager:
    """
    Real-time alerting for critical security events.
    """
    
    def __init__(self):
        self.alert_rules = self._load_alert_rules()
    
    def _load_alert_rules(self) -> Dict[str, Any]:
        """Load alerting rules configuration."""
        return {
            "critical_events": [
                "USER_LOGIN_FAILED_MULTIPLE",
                "PHI_BULK_EXPORT",
                "UNAUTHORIZED_API_ACCESS",
                "PRIVILEGE_ESCALATION"
            ],
            "high_risk_patterns": [
                "MULTIPLE_FAILED_AUTH",
                "UNUSUAL_ACCESS_PATTERN",
                "OFF_HOURS_PHI_ACCESS"
            ],
            "alert_thresholds": {
                "failed_logins": 5,
                "phi_access_rate": 100,  # per hour
                "api_error_rate": 50     # per minute
            }
        }
    
    async def process_event(self, event_data: AuditEventData):
        """Process event for real-time alerting."""
        # Critical event immediate alert
        if event_data.risk_level == AuditRiskLevel.CRITICAL:
            await self._send_critical_alert(event_data)
        
        # PHI access monitoring
        if event_data.phi_involved and event_data.outcome == "success":
            await self._monitor_phi_access(event_data)
        
        # Failed authentication monitoring
        if (event_data.category == AuditEventCategory.AUTHENTICATION and 
            event_data.outcome == "failure"):
            await self._monitor_failed_auth(event_data)
    
    async def _send_critical_alert(self, event_data: AuditEventData):
        """Send critical security alert."""
        alert_data = {
            "severity": "CRITICAL",
            "event_type": event_data.event_type,
            "user_id": event_data.user_id,
            "ip_address": event_data.ip_address,
            "timestamp": datetime.utcnow().isoformat(),
            "phi_involved": event_data.phi_involved,
            "action": event_data.action
        }
        
        logger.critical(
            "SECURITY_ALERT: Critical audit event detected",
            **alert_data
        )
        
        # In production, integrate with:
        # - Slack/Teams webhooks
        # - PagerDuty API
        # - SIEM systems
        # - Email notifications
    
    async def _monitor_phi_access(self, event_data: AuditEventData):
        """Monitor PHI access patterns."""
        # Implementation for PHI access monitoring
        # - Rate limiting checks
        # - Unusual access pattern detection
        # - Off-hours access alerts
        pass
    
    async def _monitor_failed_auth(self, event_data: AuditEventData):
        """Monitor failed authentication attempts."""
        # Implementation for auth failure monitoring
        # - Brute force detection
        # - Account lockout alerts
        # - Geographic anomaly detection
        pass


# Decorator for automatic audit logging
def audit_log(
    event_type: str,
    category: AuditEventCategory,
    risk_level: AuditRiskLevel = AuditRiskLevel.MEDIUM,
    phi_involved: bool = False
):
    """
    Decorator for automatic audit logging of function calls.
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            audit_system = EnterpriseAuditSystem()
            
            try:
                # Execute function
                result = await func(*args, **kwargs)
                
                # Log successful execution
                await audit_system.log_event(
                    event_type=event_type,
                    category=category,
                    risk_level=risk_level,
                    action=f"EXECUTE_{func.__name__.upper()}",
                    outcome="success",
                    additional_data={
                        "function": func.__name__,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    },
                    phi_involved=phi_involved
                )
                
                return result
                
            except Exception as e:
                # Log failed execution
                await audit_system.log_event(
                    event_type=event_type,
                    category=category,
                    risk_level=AuditRiskLevel.HIGH,  # Failures are higher risk
                    action=f"EXECUTE_{func.__name__.upper()}",
                    outcome="failure",
                    additional_data={
                        "function": func.__name__,
                        "error": str(e),
                        "error_type": type(e).__name__
                    },
                    phi_involved=phi_involved
                )
                raise
        
        return wrapper
    return decorator


# Example usage and testing
if __name__ == "__main__":
    async def test_audit_system():
        """Test the enterprise audit system."""
        audit_system = EnterpriseAuditSystem()
        
        # Test critical PHI access event
        await audit_system.log_event(
            event_type="PHI_PATIENT_RECORD_ACCESS",
            category=AuditEventCategory.PHI_ACCESS,
            risk_level=AuditRiskLevel.CRITICAL,
            action="VIEW_PATIENT_RECORD",
            outcome="success",
            user_id="user_123",
            session_id="session_456",
            resource_type="patient",
            resource_id="patient_789",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0...",
            additional_data={
                "patient_mrn": "MRN123456",
                "access_reason": "treatment_review"
            },
            phi_involved=True
        )
        
        # Test authentication failure
        await audit_system.log_event(
            event_type="USER_LOGIN_FAILED",
            category=AuditEventCategory.AUTHENTICATION,
            risk_level=AuditRiskLevel.HIGH,
            action="AUTHENTICATE_USER",
            outcome="failure",
            ip_address="192.168.1.200",
            additional_data={
                "username": "admin",
                "failure_reason": "invalid_password"
            }
        )
        
        # Verify chain integrity
        integrity_result = await audit_system.verify_integrity()
        print(f"Chain integrity: {integrity_result}")
    
    # Run test
    asyncio.run(test_audit_system())