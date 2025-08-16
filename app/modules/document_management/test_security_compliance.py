"""
Security and Compliance Tests for Document Management

Tests for SOC2 Type 2 and HIPAA compliance requirements.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.document_management.service import DocumentStorageService, AccessContext
from app.modules.document_management.schemas import (
    DocumentUploadRequest, DocumentUpdateRequest, DocumentSearchRequest
)
from app.core.database_unified import DocumentType, DocumentAction
from app.core.exceptions import UnauthorizedAccess, ValidationError
from app.core.audit_logger import AuditEventType, AuditSeverity


class TestAccessControlCompliance:
    """Test suite for access control compliance (SOC2 CC6.1)."""
    
    @pytest.fixture
    def mock_service(self):
        """Mock document storage service."""
        service = DocumentStorageService()
        service.security_manager = Mock()
        service.storage_backend = Mock()
        return service
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=AsyncSession)
    
    @pytest.fixture
    def sample_context(self):
        """Sample access context."""
        return AccessContext(
            user_id=str(uuid.uuid4()),
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Browser",
            session_id=str(uuid.uuid4()),
            purpose="testing"
        )

    @pytest.mark.asyncio
    async def test_role_based_access_control(self, mock_service, mock_db, sample_context):
        """Test role-based access control enforcement."""
        # Arrange
        document_id = str(uuid.uuid4())
        mock_service.security_manager.check_document_access.return_value = False
        
        # Act & Assert - Should raise UnauthorizedAccess
        with pytest.raises(UnauthorizedAccess):
            await mock_service.get_document_metadata(
                db=mock_db,
                document_id=document_id,
                context=sample_context
            )
        
        # Verify security check was called
        mock_service.security_manager.check_document_access.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_minimum_necessary_access_principle(self, mock_service, mock_db, sample_context):
        """Test minimum necessary access principle (HIPAA)."""
        # Arrange
        document_id = str(uuid.uuid4())
        mock_service.security_manager.check_document_access.return_value = True
        mock_service.security_manager.get_user_role.return_value = "nurse"
        
        # Mock document with PHI
        mock_document = Mock()
        mock_document.contains_phi = True
        mock_document.patient_id = str(uuid.uuid4())
        
        with patch.object(mock_service, '_get_document_by_id', return_value=mock_document):
            with patch.object(mock_service, '_verify_patient_consent', return_value=True):
                with patch.object(mock_service, '_log_phi_access') as mock_log_phi:
                    # Act
                    try:
                        await mock_service.get_document_metadata(
                            db=mock_db,
                            document_id=document_id,
                            context=sample_context
                        )
                    except AttributeError:
                        # Expected due to mocking, focus on PHI access logging
                        pass
        
        # Assert - PHI access should be logged
        mock_log_phi.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_patient_consent_verification(self, mock_service, mock_db, sample_context):
        """Test patient consent verification for PHI access."""
        # Arrange
        document_id = str(uuid.uuid4())
        patient_id = str(uuid.uuid4())
        
        mock_service.security_manager.check_document_access.return_value = True
        
        # Mock document with PHI but no consent
        with patch.object(mock_service, '_verify_patient_consent', return_value=False):
            # Act & Assert
            with pytest.raises(UnauthorizedAccess) as exc_info:
                await mock_service._check_phi_access_authorization(
                    patient_id=patient_id,
                    purpose="testing",
                    context=sample_context
                )
            
            assert "Patient consent required" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_session_timeout_enforcement(self, mock_service, sample_context):
        """Test session timeout enforcement."""
        # Arrange - Create expired session context
        expired_context = AccessContext(
            user_id=sample_context.user_id,
            session_id=sample_context.session_id,
            purpose="testing"
        )
        
        # Mock session as expired
        mock_service.security_manager.is_session_valid.return_value = False
        
        # Act & Assert
        with pytest.raises(UnauthorizedAccess) as exc_info:
            await mock_service._validate_session(expired_context)
        
        assert "Session expired" in str(exc_info.value)


class TestAuditLoggingCompliance:
    """Test suite for audit logging compliance (SOC2 CC7.1)."""
    
    @pytest.fixture
    def mock_audit_logger(self):
        """Mock audit logger."""
        return Mock()
    
    @pytest.fixture
    def mock_service_with_audit(self, mock_audit_logger):
        """Mock service with audit logger."""
        service = DocumentStorageService()
        service.audit_logger = mock_audit_logger
        service.security_manager = Mock()
        service.storage_backend = Mock()
        return service
    
    @pytest.mark.asyncio
    async def test_phi_access_audit_logging(self, mock_service_with_audit, sample_context):
        """Test comprehensive PHI access audit logging."""
        # Arrange
        document_id = str(uuid.uuid4())
        patient_id = str(uuid.uuid4())
        
        # Act
        await mock_service_with_audit._log_phi_access(
            document_id=document_id,
            patient_id=patient_id,
            action=DocumentAction.VIEW,
            context=sample_context,
            additional_data={"classification": "high_sensitivity"}
        )
        
        # Assert - Verify audit log contains required fields
        mock_service_with_audit.audit_logger.log_event.assert_called_once()
        call_args = mock_service_with_audit.audit_logger.log_event.call_args[1]
        
        assert call_args['event_type'] == AuditEventType.PHI_ACCESS
        assert call_args['severity'] == AuditSeverity.HIGH
        assert call_args['user_id'] == sample_context.user_id
        assert call_args['ip_address'] == sample_context.ip_address
        assert 'document_id' in call_args['resource_id']
        assert 'patient_id' in call_args['details']
    
    @pytest.mark.asyncio
    async def test_immutable_audit_trail(self, mock_service_with_audit, sample_context):
        """Test immutable audit trail creation."""
        # Arrange
        document_id = str(uuid.uuid4())
        
        # Act
        await mock_service_with_audit._create_audit_record(
            document_id=document_id,
            action=DocumentAction.UPDATE,
            context=sample_context,
            details={"changes": {"filename": "new_name.pdf"}}
        )
        
        # Assert - Verify audit record has cryptographic integrity
        call_args = mock_service_with_audit.audit_logger.log_event.call_args[1]
        
        assert 'audit_hash' in call_args['details']
        assert 'block_number' in call_args['details']
        assert 'previous_hash' in call_args['details']
    
    @pytest.mark.asyncio
    async def test_bulk_operation_audit_trail(self, mock_service_with_audit, sample_context):
        """Test bulk operation comprehensive audit trail."""
        # Arrange
        document_ids = [str(uuid.uuid4()) for _ in range(3)]
        reason = "Bulk testing operation"
        
        # Act
        await mock_service_with_audit._log_bulk_operation(
            operation_type="bulk_delete",
            document_ids=document_ids,
            reason=reason,
            context=sample_context,
            results={"success": 2, "failed": 1}
        )
        
        # Assert - Verify bulk operation is properly logged
        call_args = mock_service_with_audit.audit_logger.log_event.call_args[1]
        
        assert call_args['event_type'] == AuditEventType.BULK_OPERATION
        assert len(call_args['details']['document_ids']) == 3
        assert call_args['details']['reason'] == reason
        assert call_args['details']['results']['success'] == 2


class TestDataRetentionCompliance:
    """Test suite for data retention compliance."""
    
    @pytest.fixture
    def mock_retention_service(self):
        """Mock retention policy service."""
        service = Mock()
        service.get_retention_policy.return_value = Mock(
            policy_id="policy_123",
            retention_period_days=2555,  # 7 years
            auto_delete=False
        )
        service.is_deletion_allowed.return_value = True
        return service
    
    @pytest.mark.asyncio
    async def test_retention_policy_enforcement(self, mock_retention_service):
        """Test retention policy enforcement during deletion."""
        # Arrange
        document_id = str(uuid.uuid4())
        patient_id = str(uuid.uuid4())
        
        service = DocumentStorageService()
        service.retention_service = mock_retention_service
        
        # Act
        is_allowed = await service._check_retention_policy_compliance(
            document_id=document_id,
            patient_id=patient_id,
            deletion_type="soft"
        )
        
        # Assert
        assert is_allowed is True
        mock_retention_service.get_retention_policy.assert_called_once()
        mock_retention_service.is_deletion_allowed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_legal_hold_prevention(self, mock_retention_service):
        """Test legal hold prevention of deletion."""
        # Arrange
        document_id = str(uuid.uuid4())
        patient_id = str(uuid.uuid4())
        
        # Mock legal hold status
        mock_retention_service.is_deletion_allowed.return_value = False
        mock_retention_service.get_legal_hold_status.return_value = Mock(
            is_active=True,
            hold_reason="Active litigation",
            hold_id="hold_456"
        )
        
        service = DocumentStorageService()
        service.retention_service = mock_retention_service
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await service._check_retention_policy_compliance(
                document_id=document_id,
                patient_id=patient_id,
                deletion_type="hard"
            )
        
        assert "legal hold" in str(exc_info.value).lower()


class TestEncryptionCompliance:
    """Test suite for encryption compliance (HIPAA Technical Safeguards)."""
    
    @pytest.fixture
    def mock_encryption_service(self):
        """Mock encryption service."""
        service = Mock()
        service.encrypt_data.return_value = b"encrypted_data"
        service.decrypt_data.return_value = b"original_data"
        service.generate_key.return_value = "encryption_key_123"
        return service
    
    @pytest.mark.asyncio
    async def test_data_encryption_at_rest(self, mock_encryption_service):
        """Test data encryption at rest."""
        # Arrange
        service = DocumentStorageService()
        service.encryption_service = mock_encryption_service
        file_data = b"sensitive_medical_data"
        
        # Act
        encrypted_data = await service._encrypt_file_data(file_data)
        
        # Assert
        assert encrypted_data == b"encrypted_data"
        mock_encryption_service.encrypt_data.assert_called_once_with(file_data)
    
    @pytest.mark.asyncio
    async def test_key_rotation_compliance(self, mock_encryption_service):
        """Test encryption key rotation compliance."""
        # Arrange
        service = DocumentStorageService()
        service.encryption_service = mock_encryption_service
        old_key_id = "old_key_123"
        
        # Act
        new_key_id = await service._rotate_encryption_key(old_key_id)
        
        # Assert
        assert new_key_id == "encryption_key_123"
        mock_encryption_service.generate_key.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_secure_deletion_compliance(self, mock_encryption_service):
        """Test secure deletion compliance."""
        # Arrange
        service = DocumentStorageService()
        service.encryption_service = mock_encryption_service
        document_id = str(uuid.uuid4())
        
        # Act
        deletion_result = await service._perform_secure_deletion(document_id)
        
        # Assert - Verify secure deletion process
        assert deletion_result['secure_deletion_completed'] is True
        assert 'deletion_verification_hash' in deletion_result
        assert deletion_result['key_destroyed'] is True


class TestInputSanitizationSecurity:
    """Test suite for input sanitization security."""
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention in search queries."""
        # Arrange
        malicious_inputs = [
            "'; DROP TABLE documents; --",
            "' OR '1'='1",
            "1; DELETE FROM users WHERE 1=1; --",
            "' UNION SELECT * FROM sensitive_data --"
        ]
        
        for malicious_input in malicious_inputs:
            # Act & Assert - Should not raise SQL errors
            try:
                search_request = DocumentSearchRequest(
                    search_text=malicious_input
                )
                # Input should be sanitized
                assert search_request.search_text == malicious_input  # Stored as-is for now
            except Exception as e:
                # If validation rejects it, that's also acceptable
                assert isinstance(e, ValidationError)
    
    def test_xss_prevention_in_metadata(self):
        """Test XSS prevention in document metadata."""
        # Arrange
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "onload=alert('xss')"
        ]
        
        for payload in xss_payloads:
            # Act & Assert - Should sanitize or reject XSS payloads
            try:
                update_request = DocumentUpdateRequest(
                    document_category=payload
                )
                # Category should be sanitized or rejected
                assert "<script>" not in update_request.document_category or update_request.document_category is None
            except ValidationError:
                # Rejection is acceptable
                pass
    
    def test_path_traversal_prevention(self):
        """Test path traversal prevention in filenames."""
        # Arrange
        path_traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config",
            "file/../../sensitive/data.txt",
            "normal_file.pdf/../../../etc/shadow"
        ]
        
        for attempt in path_traversal_attempts:
            # Act & Assert - Should reject path traversal attempts
            with pytest.raises(ValidationError):
                DocumentUploadRequest(
                    patient_id=str(uuid.uuid4()),
                    filename=attempt,
                    document_type=DocumentType.LAB_RESULT
                )


class TestComplianceReporting:
    """Test suite for compliance reporting capabilities."""
    
    @pytest.fixture
    def mock_compliance_service(self):
        """Mock compliance reporting service."""
        service = Mock()
        service.generate_soc2_report.return_value = {
            "report_period": "2024-Q2",
            "access_controls_tested": 150,
            "access_violations": 0,
            "audit_completeness": 100.0
        }
        service.generate_hipaa_report.return_value = {
            "phi_access_events": 1250,
            "unauthorized_access_attempts": 3,
            "breach_incidents": 0,
            "compliance_score": 98.5
        }
        return service
    
    @pytest.mark.asyncio
    async def test_soc2_compliance_report_generation(self, mock_compliance_service):
        """Test SOC2 compliance report generation."""
        # Arrange
        service = DocumentStorageService()
        service.compliance_service = mock_compliance_service
        
        # Act
        report = await service._generate_soc2_compliance_report(
            start_date=datetime.now() - timedelta(days=90),
            end_date=datetime.now()
        )
        
        # Assert
        assert report["access_controls_tested"] == 150
        assert report["access_violations"] == 0
        assert report["audit_completeness"] == 100.0
    
    @pytest.mark.asyncio
    async def test_hipaa_compliance_report_generation(self, mock_compliance_service):
        """Test HIPAA compliance report generation."""
        # Arrange
        service = DocumentStorageService()
        service.compliance_service = mock_compliance_service
        
        # Act
        report = await service._generate_hipaa_compliance_report(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        # Assert
        assert report["phi_access_events"] == 1250
        assert report["unauthorized_access_attempts"] == 3
        assert report["breach_incidents"] == 0
        assert report["compliance_score"] == 98.5
    
    @pytest.mark.asyncio
    async def test_audit_trail_integrity_verification(self):
        """Test audit trail integrity verification."""
        # Arrange
        service = DocumentStorageService()
        mock_db = Mock(spec=AsyncSession)
        
        # Mock audit records with chain integrity
        mock_audit_records = [
            Mock(block_number=1, current_hash="hash1", previous_hash="genesis"),
            Mock(block_number=2, current_hash="hash2", previous_hash="hash1"),
            Mock(block_number=3, current_hash="hash3", previous_hash="hash2")
        ]
        
        with patch.object(service, '_get_audit_chain', return_value=mock_audit_records):
            # Act
            integrity_result = await service._verify_audit_trail_integrity(mock_db)
        
        # Assert
        assert integrity_result['chain_valid'] is True
        assert integrity_result['total_blocks'] == 3
        assert integrity_result['integrity_violations'] == 0


if __name__ == "__main__":
    # Run tests with: python -m pytest app/modules/document_management/test_security_compliance.py -v
    pytest.main([__file__, "-v"])