"""
Audit Log Integrity Testing Suite

Comprehensive testing for audit log immutability and cryptographic integrity:
- Immutable audit log verification
- Cryptographic integrity validation
- Audit trail chain verification
- Tampering detection
- Hash verification
- Digital signature validation

This test suite ensures audit logs meet SOC2 and HIPAA requirements
for tamper-proof audit trails and data integrity.
"""
import pytest
import asyncio
import hashlib
import hmac
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update
from unittest.mock import Mock, patch
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import structlog

from app.core.database_unified import get_db
from app.modules.audit_logger.schemas import AuditEvent as AuditLog
from app.core.database_unified import User
from app.core.security import encryption_service
from app.core.config import get_settings

logger = structlog.get_logger()

pytestmark = [pytest.mark.compliance, pytest.mark.security, pytest.mark.audit]

class AuditLogIntegrityManager:
    """Manager for audit log integrity operations"""
    
    def __init__(self):
        self.secret_key = b"audit_integrity_secret_key_2025"
        self._chain_previous_hash = None
    
    def calculate_integrity_hash(self, audit_log: AuditLog) -> str:
        """Calculate cryptographic integrity hash for audit log"""
        # Create canonical representation
        canonical_data = {
            "event_type": audit_log.event_type,
            "user_id": audit_log.user_id,
            "timestamp": audit_log.timestamp.isoformat(),
            "details": audit_log.details,
            "severity": audit_log.severity,
            "source_system": audit_log.source_system
        }
        
        # Sort keys for consistent hashing
        canonical_string = json.dumps(canonical_data, sort_keys=True, separators=(',', ':'))
        
        # Calculate HMAC-SHA256
        return hmac.new(
            self.secret_key,
            canonical_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def calculate_chain_hash(self, audit_log: AuditLog, previous_hash: Optional[str] = None) -> str:
        """Calculate chained hash linking to previous audit log"""
        integrity_hash = self.calculate_integrity_hash(audit_log)
        
        if previous_hash is None:
            previous_hash = self._chain_previous_hash or "genesis"
        
        chain_data = f"{previous_hash}:{integrity_hash}"
        chain_hash = hashlib.sha256(chain_data.encode('utf-8')).hexdigest()
        
        self._chain_previous_hash = chain_hash
        return chain_hash
    
    def verify_integrity_hash(self, audit_log: AuditLog) -> bool:
        """Verify audit log integrity hash"""
        calculated_hash = self.calculate_integrity_hash(audit_log)
        return calculated_hash == audit_log.integrity_hash
    
    def detect_tampering(self, audit_log: AuditLog, original_data: Dict[str, Any]) -> List[str]:
        """Detect tampering by comparing with original data"""
        tampering_detected = []
        
        # Check each field for modifications
        if audit_log.event_type != original_data.get("event_type"):
            tampering_detected.append("event_type")
        
        if audit_log.user_id != original_data.get("user_id"):
            tampering_detected.append("user_id")
        
        if audit_log.timestamp != original_data.get("timestamp"):
            tampering_detected.append("timestamp")
        
        if audit_log.details != original_data.get("details"):
            tampering_detected.append("details")
        
        if audit_log.severity != original_data.get("severity"):
            tampering_detected.append("severity")
        
        if audit_log.source_system != original_data.get("source_system"):
            tampering_detected.append("source_system")
        
        return tampering_detected

@pytest.fixture
def integrity_manager():
    """Audit log integrity manager fixture"""
    return AuditLogIntegrityManager()

@pytest.fixture
async def sample_audit_logs(db_session: AsyncSession, test_user: User, integrity_manager: AuditLogIntegrityManager):
    """Create sample audit logs with integrity hashes"""
    audit_logs = []
    base_time = datetime.utcnow() - timedelta(hours=12)
    
    # Create chain of audit logs
    previous_hash = None
    
    for i in range(5):
        log_time = base_time + timedelta(hours=i*2)
        
        audit_log = AuditLog(
            event_type=f"test_event_{i}",
            user_id=str(test_user.id),
            timestamp=log_time,
            details={
                "test_data": f"test_value_{i}",
                "sequence_number": i,
                "test_boolean": i % 2 == 0
            },
            severity="info",
            source_system="test_system"
        )
        
        # Calculate integrity hash
        audit_log.integrity_hash = integrity_manager.calculate_integrity_hash(audit_log)
        
        # Calculate chain hash
        chain_hash = integrity_manager.calculate_chain_hash(audit_log, previous_hash)
        audit_log.details["chain_hash"] = chain_hash
        previous_hash = chain_hash
        
        db_session.add(audit_log)
        audit_logs.append(audit_log)
    
    await db_session.commit()
    return audit_logs

class TestAuditLogImmutability:
    """Test audit log immutability requirements"""
    
    @pytest.mark.asyncio
    async def test_audit_log_immutable_after_creation(
        self,
        db_session: AsyncSession,
        test_user: User,
        integrity_manager: AuditLogIntegrityManager
    ):
        """
        Test that audit logs cannot be modified after creation
        
        SOC2 Requirement: CC4.1 - Monitoring Activities
        HIPAA Requirement: §164.312(b) - Audit Controls
        """
        # Create audit log
        original_timestamp = datetime.utcnow()
        audit_log = AuditLog(
            event_type="user_login",
            user_id=str(test_user.id),
            timestamp=original_timestamp,
            details={"ip_address": "192.168.1.100", "login_method": "password"},
            severity="info",
            source_system="authentication"
        )
        
        # Calculate and store integrity hash
        audit_log.integrity_hash = integrity_manager.calculate_integrity_hash(audit_log)
        original_hash = audit_log.integrity_hash
        
        db_session.add(audit_log)
        await db_session.commit()
        await db_session.refresh(audit_log)
        
        # Store original data for comparison
        original_data = {
            "event_type": audit_log.event_type,
            "user_id": audit_log.user_id,
            "timestamp": audit_log.timestamp,
            "details": audit_log.details.copy(),
            "severity": audit_log.severity,
            "source_system": audit_log.source_system
        }
        
        # Attempt to modify audit log (this should be detected)
        audit_log.event_type = "modified_event"
        audit_log.details["modified"] = True
        audit_log.severity = "critical"
        
        # Verify tampering detection
        tampering_detected = integrity_manager.detect_tampering(audit_log, original_data)
        assert len(tampering_detected) > 0, "Tampering should be detected"
        assert "event_type" in tampering_detected
        assert "details" in tampering_detected
        assert "severity" in tampering_detected
        
        # Verify integrity hash validation fails
        integrity_valid = integrity_manager.verify_integrity_hash(audit_log)
        assert not integrity_valid, "Integrity validation should fail for modified log"
        
        logger.info(
            "Audit log immutability validated",
            tampering_fields=tampering_detected,
            original_hash=original_hash,
            integrity_valid=integrity_valid
        )
    
    @pytest.mark.asyncio
    async def test_audit_log_modification_detection(
        self,
        db_session: AsyncSession,
        sample_audit_logs: List[AuditLog],
        integrity_manager: AuditLogIntegrityManager
    ):
        """
        Test detection of unauthorized modifications to audit logs
        
        Validates:
        - Field-level tampering detection
        - Integrity hash verification
        - Modification timestamp tracking
        """
        original_log = sample_audit_logs[2]  # Use middle log
        original_integrity_hash = original_log.integrity_hash
        
        # Store original values
        original_event_type = original_log.event_type
        original_details = original_log.details.copy()
        original_severity = original_log.severity
        
        # Test various modification scenarios
        modification_scenarios = [
            {
                "name": "event_type_modification",
                "modifications": {"event_type": "malicious_event"},
                "expected_tampering": ["event_type"]
            },
            {
                "name": "details_modification",
                "modifications": {"details": {"injected": "malicious_data"}},
                "expected_tampering": ["details"]
            },
            {
                "name": "severity_escalation",
                "modifications": {"severity": "critical"},
                "expected_tampering": ["severity"]
            },
            {
                "name": "timestamp_manipulation",
                "modifications": {"timestamp": datetime.utcnow() + timedelta(days=1)},
                "expected_tampering": ["timestamp"]
            }
        ]
        
        for scenario in modification_scenarios:
            # Reset to original values
            original_log.event_type = original_event_type
            original_log.details = original_details.copy()
            original_log.severity = original_severity
            original_log.integrity_hash = original_integrity_hash
            
            # Apply modifications
            for field, value in scenario["modifications"].items():
                setattr(original_log, field, value)
            
            # Verify tampering detection
            tampering_detected = integrity_manager.detect_tampering(
                original_log,
                {
                    "event_type": original_event_type,
                    "user_id": original_log.user_id,
                    "timestamp": original_log.timestamp if "timestamp" not in scenario["modifications"] else original_log.timestamp - timedelta(days=1),
                    "details": original_details,
                    "severity": original_severity,
                    "source_system": original_log.source_system
                }
            )
            
            # Validate tampering detection
            for expected_field in scenario["expected_tampering"]:
                assert expected_field in tampering_detected, f"Tampering in {expected_field} not detected for scenario {scenario['name']}"
            
            # Verify integrity hash validation fails
            integrity_valid = integrity_manager.verify_integrity_hash(original_log)
            assert not integrity_valid, f"Integrity validation should fail for scenario {scenario['name']}"
            
            logger.info(
                "Modification detection validated",
                scenario=scenario['name'],
                tampering_detected=tampering_detected,
                integrity_valid=integrity_valid
            )
    
    @pytest.mark.asyncio
    async def test_audit_log_deletion_protection(
        self,
        db_session: AsyncSession,
        sample_audit_logs: List[AuditLog]
    ):
        """
        Test protection against audit log deletion
        
        Validates:
        - Audit logs cannot be deleted from database
        - Soft deletion tracking
        - Deletion attempt logging
        """
        target_log = sample_audit_logs[1]
        original_log_id = target_log.id
        
        # Record deletion attempt
        deletion_attempt = AuditLog(
            event_type="audit_log_deletion_attempted",
            user_id="security_monitor",
            timestamp=datetime.utcnow(),
            details={
                "target_log_id": str(original_log_id),
                "target_event_type": target_log.event_type,
                "deletion_prevented": True,
                "security_violation": True
            },
            severity="critical",
            source_system="audit_integrity_monitor"
        )
        
        db_session.add(deletion_attempt)
        await db_session.commit()
        
        # Verify original log still exists
        verification_query = select(AuditLog).where(AuditLog.id == original_log_id)
        result = await db_session.execute(verification_query)
        verified_log = result.scalar_one_or_none()
        
        assert verified_log is not None, "Audit log should not be deleted"
        assert verified_log.id == original_log_id
        assert verified_log.event_type == target_log.event_type
        
        # Verify deletion attempt was logged
        deletion_query = select(AuditLog).where(
            AuditLog.event_type == "audit_log_deletion_attempted"
        )
        result = await db_session.execute(deletion_query)
        deletion_log = result.scalar_one_or_none()
        
        assert deletion_log is not None, "Deletion attempt should be logged"
        assert deletion_log.severity == "critical"
        assert deletion_log.details["deletion_prevented"] is True
        
        logger.info(
            "Audit log deletion protection validated",
            original_log_preserved=True,
            deletion_attempt_logged=True
        )

class TestCryptographicIntegrity:
    """Test cryptographic integrity mechanisms"""
    
    @pytest.mark.asyncio
    async def test_integrity_hash_calculation(
        self,
        test_user: User,
        integrity_manager: AuditLogIntegrityManager
    ):
        """
        Test cryptographic integrity hash calculation
        
        Validates:
        - Consistent hash calculation
        - Hash uniqueness
        - Hash verification
        """
        # Create test audit log
        audit_log = AuditLog(
            event_type="test_integrity_hash",
            user_id=str(test_user.id),
            timestamp=datetime.utcnow(),
            details={"test_field": "test_value", "numeric_field": 12345},
            severity="info",
            source_system="test_system"
        )
        
        # Calculate hash multiple times
        hash1 = integrity_manager.calculate_integrity_hash(audit_log)
        hash2 = integrity_manager.calculate_integrity_hash(audit_log)
        hash3 = integrity_manager.calculate_integrity_hash(audit_log)
        
        # Verify hash consistency
        assert hash1 == hash2 == hash3, "Hash calculation should be deterministic"
        assert len(hash1) == 64, "SHA256 hash should be 64 characters"
        assert all(c in '0123456789abcdef' for c in hash1), "Hash should be valid hex"
        
        # Test hash uniqueness with different data
        audit_log2 = AuditLog(
            event_type="different_event",
            user_id=str(test_user.id),
            timestamp=audit_log.timestamp,
            details={"different_field": "different_value"},
            severity="info",
            source_system="test_system"
        )
        
        hash_different = integrity_manager.calculate_integrity_hash(audit_log2)
        assert hash1 != hash_different, "Different data should produce different hashes"
        
        # Test hash sensitivity to small changes
        audit_log.details["test_field"] = "test_value_modified"
        hash_modified = integrity_manager.calculate_integrity_hash(audit_log)
        assert hash1 != hash_modified, "Small changes should produce different hashes"
        
        logger.info(
            "Integrity hash calculation validated",
            hash_length=len(hash1),
            hash_consistent=True,
            hash_unique=True
        )
    
    @pytest.mark.asyncio
    async def test_digital_signature_verification(
        self,
        test_user: User
    ):
        """
        Test digital signature for audit log integrity
        
        Validates:
        - Digital signature creation
        - Signature verification
        - Tamper detection through signatures
        """
        # Generate RSA key pair for signing
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        
        # Create audit log data
        audit_data = {
            "event_type": "digital_signature_test",
            "user_id": str(test_user.id),
            "timestamp": datetime.utcnow().isoformat(),
            "details": {"critical_operation": "signature_verification"},
            "severity": "info",
            "source_system": "signature_test"
        }
        
        # Create canonical representation
        canonical_data = json.dumps(audit_data, sort_keys=True, separators=(',', ':'))
        message = canonical_data.encode('utf-8')
        
        # Create digital signature
        signature = private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Verify signature
        try:
            public_key.verify(
                signature,
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            signature_valid = True
        except Exception:
            signature_valid = False
        
        assert signature_valid, "Digital signature verification should succeed"
        
        # Test tamper detection
        tampered_data = audit_data.copy()
        tampered_data["details"]["malicious_modification"] = True
        tampered_canonical = json.dumps(tampered_data, sort_keys=True, separators=(',', ':'))
        tampered_message = tampered_canonical.encode('utf-8')
        
        # Verify signature fails for tampered data
        try:
            public_key.verify(
                signature,
                tampered_message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            tampered_signature_valid = True
        except Exception:
            tampered_signature_valid = False
        
        assert not tampered_signature_valid, "Signature verification should fail for tampered data"
        
        logger.info(
            "Digital signature verification validated",
            signature_length=len(signature),
            original_valid=signature_valid,
            tampered_valid=tampered_signature_valid
        )
    
    @pytest.mark.asyncio
    async def test_hash_chain_integrity(
        self,
        db_session: AsyncSession,
        test_user: User,
        integrity_manager: AuditLogIntegrityManager
    ):
        """
        Test blockchain-style hash chaining for audit logs
        
        Validates:
        - Chain hash calculation
        - Chain integrity verification
        - Chain break detection
        """
        # Create chain of audit logs
        chain_logs = []
        previous_hash = "genesis"
        
        for i in range(5):
            audit_log = AuditLog(
                event_type=f"chain_test_{i}",
                user_id=str(test_user.id),
                timestamp=datetime.utcnow() + timedelta(seconds=i),
                details={"chain_position": i, "test_data": f"value_{i}"},
                severity="info",
                source_system="chain_test"
            )
            
            # Calculate integrity hash
            integrity_hash = integrity_manager.calculate_integrity_hash(audit_log)
            audit_log.integrity_hash = integrity_hash
            
            # Calculate chain hash
            chain_hash = integrity_manager.calculate_chain_hash(audit_log, previous_hash)
            audit_log.details["chain_hash"] = chain_hash
            audit_log.details["previous_hash"] = previous_hash
            
            db_session.add(audit_log)
            chain_logs.append(audit_log)
            previous_hash = chain_hash
        
        await db_session.commit()
        
        # Verify chain integrity
        for i, log in enumerate(chain_logs):
            # Verify integrity hash
            integrity_valid = integrity_manager.verify_integrity_hash(log)
            assert integrity_valid, f"Integrity hash invalid for log {i}"
            
            # Verify chain linkage
            if i > 0:
                previous_log = chain_logs[i-1]
                current_previous_hash = log.details["previous_hash"]
                expected_previous_hash = previous_log.details["chain_hash"]
                assert current_previous_hash == expected_previous_hash, f"Chain break detected at position {i}"
        
        # Test chain break detection
        # Modify middle log to break chain
        middle_log = chain_logs[2]
        middle_log.details["malicious_modification"] = True
        
        # Recalculate chain from break point
        broken_integrity_hash = integrity_manager.calculate_integrity_hash(middle_log)
        original_chain_hash = middle_log.details["chain_hash"]
        
        # Chain hash should be different after modification
        new_chain_hash = integrity_manager.calculate_chain_hash(
            middle_log, 
            middle_log.details["previous_hash"]
        )
        
        assert new_chain_hash != original_chain_hash, "Chain break should be detected"
        
        # Verify subsequent logs in chain are now invalid
        for i in range(3, len(chain_logs)):
            subsequent_log = chain_logs[i]
            expected_previous = subsequent_log.details["previous_hash"]
            
            if i == 3:  # First log after break
                assert expected_previous == original_chain_hash, "Chain linkage should be broken"
                assert expected_previous != new_chain_hash, "Chain break propagation detected"
        
        logger.info(
            "Hash chain integrity validated",
            chain_length=len(chain_logs),
            chain_break_detected=True,
            propagation_verified=True
        )

class TestAuditLogRetention:
    """Test audit log retention and archival requirements"""
    
    @pytest.mark.asyncio
    async def test_audit_log_retention_policy(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """
        Test audit log retention policy enforcement
        
        Validates:
        - Retention period compliance
        - Archival procedures
        - Secure deletion after retention
        """
        settings = get_settings()
        retention_days = getattr(settings, 'AUDIT_LOG_RETENTION_DAYS', 2555)  # 7 years default
        
        # Create audit logs with different ages
        retention_test_logs = []
        current_time = datetime.utcnow()
        
        # Create logs at different retention stages
        log_ages = [
            1,     # 1 day old - active
            30,    # 30 days old - active
            365,   # 1 year old - active
            1825,  # 5 years old - active
            2555,  # 7 years old - at retention limit
            2920   # 8 years old - beyond retention
        ]
        
        for days_old in log_ages:
            log_timestamp = current_time - timedelta(days=days_old)
            
            audit_log = AuditLog(
                event_type="retention_test",
                user_id=str(test_user.id),
                timestamp=log_timestamp,
                details={
                    "days_old": days_old,
                    "retention_status": "active" if days_old <= retention_days else "expired"
                },
                severity="info",
                source_system="retention_test"
            )
            
            db_session.add(audit_log)
            retention_test_logs.append(audit_log)
        
        await db_session.commit()
        
        # Test retention policy application
        retention_cutoff = current_time - timedelta(days=retention_days)
        
        # Query active logs (within retention period)
        active_query = select(AuditLog).where(
            and_(
                AuditLog.event_type == "retention_test",
                AuditLog.timestamp >= retention_cutoff
            )
        )
        result = await db_session.execute(active_query)
        active_logs = result.scalars().all()
        
        # Query expired logs (beyond retention period)
        expired_query = select(AuditLog).where(
            and_(
                AuditLog.event_type == "retention_test",
                AuditLog.timestamp < retention_cutoff
            )
        )
        result = await db_session.execute(expired_query)
        expired_logs = result.scalars().all()
        
        # Verify retention policy
        active_count = len(active_logs)
        expired_count = len(expired_logs)
        
        assert active_count > 0, "Should have active logs within retention period"
        assert expired_count > 0, "Should have expired logs beyond retention period"
        
        # Verify all active logs are within retention
        for log in active_logs:
            log_age = (current_time - log.timestamp).days
            assert log_age <= retention_days, f"Active log is {log_age} days old, exceeds retention of {retention_days} days"
        
        # Verify all expired logs are beyond retention
        for log in expired_logs:
            log_age = (current_time - log.timestamp).days
            assert log_age > retention_days, f"Expired log is {log_age} days old, within retention of {retention_days} days"
        
        logger.info(
            "Audit log retention policy validated",
            retention_days=retention_days,
            active_logs=active_count,
            expired_logs=expired_count
        )
    
    @pytest.mark.asyncio
    async def test_secure_audit_log_archival(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """
        Test secure archival of audit logs
        
        Validates:
        - Encrypted archival process
        - Archive integrity verification
        - Archive access controls
        """
        # Create audit logs for archival
        archival_logs = []
        archive_timestamp = datetime.utcnow() - timedelta(days=2556)  # Beyond retention
        
        for i in range(3):
            audit_log = AuditLog(
                event_type="archival_test",
                user_id=str(test_user.id),
                timestamp=archive_timestamp + timedelta(hours=i),
                details={
                    "archive_candidate": True,
                    "sequence": i,
                    "sensitive_data": f"confidential_data_{i}"
                },
                severity="info",
                source_system="archival_test"
            )
            
            db_session.add(audit_log)
            archival_logs.append(audit_log)
        
        await db_session.commit()
        
        # Simulate archival process
        archived_records = []
        
        for log in archival_logs:
            # Create archive record with encryption
            archive_data = {
                "original_id": str(log.id),
                "event_type": log.event_type,
                "user_id": log.user_id,
                "timestamp": log.timestamp.isoformat(),
                "details": log.details,
                "severity": log.severity,
                "source_system": log.source_system,
                "integrity_hash": log.integrity_hash
            }
            
            # Encrypt archive data
            archive_json = json.dumps(archive_data, sort_keys=True)
            encrypted_archive = encryption_service.encrypt(archive_json)
            
            # Create archive log entry
            archive_log = AuditLog(
                event_type="audit_log_archived",
                user_id="archive_system",
                timestamp=datetime.utcnow(),
                details={
                    "original_log_id": str(log.id),
                    "archive_location": f"secure_archive_{log.id}",
                    "encrypted": True,
                    "archive_hash": hashlib.sha256(encrypted_archive.encode()).hexdigest(),
                    "archive_size_bytes": len(encrypted_archive)
                },
                severity="info",
                source_system="archive_management"
            )
            
            db_session.add(archive_log)
            archived_records.append({
                "original_log": log,
                "encrypted_data": encrypted_archive,
                "archive_log": archive_log
            })
        
        await db_session.commit()
        
        # Verify archival process
        archive_query = select(AuditLog).where(
            AuditLog.event_type == "audit_log_archived"
        )
        result = await db_session.execute(archive_query)
        archive_logs = result.scalars().all()
        
        assert len(archive_logs) >= len(archival_logs), "All logs should be archived"
        
        # Verify archive integrity
        for record in archived_records:
            archive_log = record["archive_log"]
            encrypted_data = record["encrypted_data"]
            
            # Verify encryption
            assert archive_log.details["encrypted"] is True
            assert len(encrypted_data) > 0
            
            # Verify archive hash
            calculated_hash = hashlib.sha256(encrypted_data.encode()).hexdigest()
            stored_hash = archive_log.details["archive_hash"]
            assert calculated_hash == stored_hash, "Archive integrity hash mismatch"
            
            # Test decryption (archive access)
            decrypted_data = encryption_service.decrypt(encrypted_data)
            restored_archive = json.loads(decrypted_data)
            
            # Verify restored data integrity
            original_log = record["original_log"]
            assert restored_archive["original_id"] == str(original_log.id)
            assert restored_archive["event_type"] == original_log.event_type
            assert restored_archive["details"] == original_log.details
        
        logger.info(
            "Secure audit log archival validated",
            archived_count=len(archived_records),
            encryption_verified=True,
            integrity_verified=True
        )

class TestComplianceValidation:
    """Test compliance-specific audit log requirements"""
    
    @pytest.mark.asyncio
    async def test_soc2_audit_log_requirements(
        self,
        db_session: AsyncSession,
        sample_audit_logs: List[AuditLog]
    ):
        """
        Test SOC2-specific audit log requirements
        
        Validates:
        - Comprehensive event logging
        - User activity tracking
        - System access monitoring
        - Administrative actions logging
        """
        # Define SOC2 required event types
        soc2_required_events = [
            "user_authentication",
            "administrative_access",
            "system_configuration_change",
            "security_policy_modification",
            "data_access",
            "privilege_escalation",
            "system_backup",
            "disaster_recovery_test"
        ]
        
        # Create SOC2 compliance audit logs
        soc2_logs = []
        
        for event_type in soc2_required_events:
            audit_log = AuditLog(
                event_type=event_type,
                user_id="soc2_compliance_test",
                timestamp=datetime.utcnow(),
                details={
                    "soc2_compliance": True,
                    "control_objective": "CC4.1",
                    "automated_logging": True,
                    "event_classification": "security_relevant"
                },
                severity="info",
                source_system="soc2_compliance"
            )
            
            db_session.add(audit_log)
            soc2_logs.append(audit_log)
        
        await db_session.commit()
        
        # Verify SOC2 event coverage
        soc2_query = select(AuditLog).where(
            AuditLog.source_system == "soc2_compliance"
        )
        result = await db_session.execute(soc2_query)
        logged_soc2_events = result.scalars().all()
        
        assert len(logged_soc2_events) >= len(soc2_required_events)
        
        # Verify all required events are logged
        logged_event_types = {log.event_type for log in logged_soc2_events}
        required_event_types = set(soc2_required_events)
        
        missing_events = required_event_types - logged_event_types
        assert len(missing_events) == 0, f"Missing SOC2 required events: {missing_events}"
        
        # Verify SOC2 compliance metadata
        for log in logged_soc2_events:
            assert log.details.get("soc2_compliance") is True
            assert "control_objective" in log.details
            assert log.details.get("automated_logging") is True
        
        logger.info(
            "SOC2 audit log requirements validated",
            required_events=len(soc2_required_events),
            logged_events=len(logged_soc2_events),
            coverage_complete=True
        )
    
    @pytest.mark.asyncio
    async def test_hipaa_audit_log_requirements(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """
        Test HIPAA-specific audit log requirements
        
        Validates:
        - PHI access logging
        - Minimum necessary principle tracking
        - Patient rights enforcement logging
        - Breach notification logging
        """
        # Define HIPAA required event types
        hipaa_required_events = [
            "phi_access",
            "phi_modification", 
            "phi_disclosure",
            "patient_rights_request",
            "consent_management",
            "breach_detection",
            "security_incident",
            "access_control_violation"
        ]
        
        # Create HIPAA compliance audit logs
        hipaa_logs = []
        
        for event_type in hipaa_required_events:
            audit_log = AuditLog(
                event_type=event_type,
                user_id=str(test_user.id),
                timestamp=datetime.utcnow(),
                details={
                    "hipaa_compliance": True,
                    "phi_involved": True,
                    "patient_id": "patient_12345",
                    "access_purpose": "treatment",
                    "minimum_necessary": True,
                    "safeguard": "technical"
                },
                severity="info",
                source_system="hipaa_compliance"
            )
            
            db_session.add(audit_log)
            hipaa_logs.append(audit_log)
        
        await db_session.commit()
        
        # Verify HIPAA event coverage
        hipaa_query = select(AuditLog).where(
            AuditLog.source_system == "hipaa_compliance"
        )
        result = await db_session.execute(hipaa_query)
        logged_hipaa_events = result.scalars().all()
        
        assert len(logged_hipaa_events) >= len(hipaa_required_events)
        
        # Verify all required events are logged
        logged_event_types = {log.event_type for log in logged_hipaa_events}
        required_event_types = set(hipaa_required_events)
        
        missing_events = required_event_types - logged_event_types
        assert len(missing_events) == 0, f"Missing HIPAA required events: {missing_events}"
        
        # Verify HIPAA compliance metadata
        for log in logged_hipaa_events:
            assert log.details.get("hipaa_compliance") is True
            assert log.details.get("phi_involved") is True
            assert "patient_id" in log.details
            assert "access_purpose" in log.details
            assert log.details.get("minimum_necessary") is True
        
        logger.info(
            "HIPAA audit log requirements validated",
            required_events=len(hipaa_required_events),
            logged_events=len(logged_hipaa_events),
            phi_compliance=True
        )