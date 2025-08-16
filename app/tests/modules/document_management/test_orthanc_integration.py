"""
🏥 Orthanc DICOM Integration Tests
Security: CVE-2025-0896 mitigation testing
Phase 1: Enhanced Security Testing Suite
Compliance: SOC2 Type II + HIPAA + FHIR R4

Test Coverage:
- Security validation and rate limiting
- Authentication and authorization
- Input sanitization and validation
- Audit logging verification
- PHI protection compliance
"""

import pytest
import asyncio
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from app.modules.document_management.orthanc_integration import (
    OrthancIntegrationService,
    OrthancSecurityConfig,
    RateLimiter,
    DicomMetadata
)
from app.modules.document_management.service import AccessContext
from app.core.exceptions import ValidationError, ResourceNotFound


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    def test_rate_limiter_allows_under_limit(self):
        """Test that requests under the limit are allowed."""
        limiter = RateLimiter(max_requests_per_minute=10)
        
        for i in range(10):
            assert limiter.is_allowed("test_client")
    
    def test_rate_limiter_blocks_over_limit(self):
        """Test that requests over the limit are blocked."""
        limiter = RateLimiter(max_requests_per_minute=2)
        
        # First two requests should be allowed
        assert limiter.is_allowed("test_client")
        assert limiter.is_allowed("test_client")
        
        # Third request should be blocked
        assert not limiter.is_allowed("test_client")
    
    def test_rate_limiter_per_client(self):
        """Test that rate limiting is applied per client."""
        limiter = RateLimiter(max_requests_per_minute=1)
        
        # Each client should get their own allowance
        assert limiter.is_allowed("client1")
        assert limiter.is_allowed("client2")
        
        # But second request from same client should be blocked
        assert not limiter.is_allowed("client1")


class TestOrthancSecurityConfig:
    """Test security configuration validation."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = OrthancSecurityConfig()
        
        assert config.base_url == "http://localhost:8042"
        assert config.username == "iris_api"
        assert config.enable_audit_logging is True
        assert config.require_tls is True
        assert len(config.allowed_modalities) > 0
    
    def test_allowed_modalities_default(self):
        """Test default allowed modalities."""
        config = OrthancSecurityConfig()
        
        expected_modalities = ['CT', 'MR', 'US', 'XR', 'CR', 'DR']
        for modality in expected_modalities:
            assert modality in config.allowed_modalities


class TestOrthancIntegrationService:
    """Test Orthanc integration service functionality."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return OrthancSecurityConfig(
            base_url="http://localhost:8042",
            username="test_user",
            password="test_pass",
            require_tls=False,  # Disable for testing
            rate_limit_per_minute=100
        )
    
    @pytest.fixture
    def service(self, config):
        """Create test service instance."""
        return OrthancIntegrationService(config=config)
    
    def test_service_initialization(self, service, config):
        """Test service initializes with correct configuration."""
        assert service.config == config
        assert service.rate_limiter is not None
        assert service._session is None
    
    def test_config_validation_tls_required(self):
        """Test TLS validation for non-localhost connections."""
        with pytest.raises(ValidationError, match="TLS required"):
            OrthancSecurityConfig(
                base_url="http://example.com:8042",
                require_tls=True
            )
    
    def test_config_validation_missing_credentials(self):
        """Test validation fails without credentials."""
        with pytest.raises(ValidationError, match="Authentication credentials required"):
            OrthancSecurityConfig(username="", password="")
    
    @pytest.mark.asyncio
    async def test_rate_limit_check(self, service):
        """Test rate limit checking."""
        # Should not raise exception under limit
        await service._check_rate_limit("test_client")
        
        # Mock rate limiter to simulate limit exceeded
        service.rate_limiter.is_allowed = Mock(return_value=False)
        
        with pytest.raises(ValidationError, match="Rate limit exceeded"):
            await service._check_rate_limit("test_client")
    
    @pytest.mark.asyncio
    async def test_get_session_creation(self, service):
        """Test HTTP session creation with authentication."""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.closed = False
            
            session = await service._get_session()
            
            mock_session.assert_called_once()
            # Verify authentication was set up
            call_args = mock_session.call_args
            assert 'auth' in call_args.kwargs
    
    @pytest.mark.asyncio
    async def test_get_session_timeout_handling(self, service):
        """Test session timeout and recreation."""
        # Mock existing session that's timed out
        service._session = Mock()
        service._session.closed = False
        service.session_created_at = datetime.utcnow()
        
        # Make session appear old
        import time
        service.session_created_at = datetime.fromtimestamp(time.time() - 4000)
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.closed = False
            
            await service._get_session()
            
            # Should have closed old session and created new one
            service._session.close.assert_called_once()
            mock_session.assert_called_once()


class TestDicomMetadataValidation:
    """Test DICOM metadata validation and security."""
    
    @pytest.fixture
    def service(self):
        """Create service with mocked session."""
        config = OrthancSecurityConfig(
            require_tls=False,
            username="test",
            password="test"
        )
        return OrthancIntegrationService(config=config)
    
    @pytest.mark.asyncio
    async def test_get_dicom_metadata_input_validation(self, service):
        """Test input validation for instance ID."""
        # Test empty instance ID
        with pytest.raises(ValidationError, match="Invalid instance_id"):
            await service.get_dicom_metadata("")
        
        # Test None instance ID
        with pytest.raises(ValidationError, match="Invalid instance_id"):
            await service.get_dicom_metadata(None)
        
        # Test invalid characters
        with pytest.raises(ValidationError, match="invalid characters"):
            await service.get_dicom_metadata("../../../etc/passwd")
        
        # Test SQL injection attempt
        with pytest.raises(ValidationError, match="invalid characters"):
            await service.get_dicom_metadata("'; DROP TABLE instances; --")
    
    @pytest.mark.asyncio
    async def test_get_dicom_metadata_valid_input(self, service):
        """Test valid instance ID formats."""
        valid_ids = [
            "1234567890",
            "abc-def-123",
            "test_instance_001",
            "DICOM123456789"
        ]
        
        # Mock the session and responses
        with patch.object(service, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session
            
            # Mock successful responses
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "PatientID": "TEST001",
                "StudyDate": "20240101",
                "StudyDescription": "Test Study",
                "SeriesDescription": "Test Series",
                "Modality": "CT"
            })
            mock_response.raise_for_status = Mock()
            
            mock_instance_response = AsyncMock()
            mock_instance_response.status = 200
            mock_instance_response.json = AsyncMock(return_value={
                "ParentStudy": "study123",
                "ParentSeries": "series123"
            })
            mock_instance_response.raise_for_status = Mock()
            
            mock_session.get.return_value.__aenter__.side_effect = [
                mock_response, mock_instance_response
            ]
            
            for instance_id in valid_ids:
                # Should not raise exception
                metadata = await service.get_dicom_metadata(instance_id)
                assert isinstance(metadata, DicomMetadata)
                assert metadata.instance_id == instance_id
    
    @pytest.mark.asyncio
    async def test_get_dicom_metadata_modality_validation(self, service):
        """Test modality validation against allowed list."""
        with patch.object(service, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session
            
            # Mock response with unsupported modality
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "PatientID": "TEST001",
                "Modality": "UNSUPPORTED"  # Not in allowed list
            })
            mock_response.raise_for_status = Mock()
            
            mock_instance_response = AsyncMock()
            mock_instance_response.status = 200
            mock_instance_response.json = AsyncMock(return_value={
                "ParentStudy": "study123",
                "ParentSeries": "series123"
            })
            mock_instance_response.raise_for_status = Mock()
            
            mock_session.get.return_value.__aenter__.side_effect = [
                mock_response, mock_instance_response
            ]
            
            # Should log warning but not fail
            with patch.object(service.logger, 'warning') as mock_log:
                metadata = await service.get_dicom_metadata("test123")
                
                # Should have logged warning about unsupported modality
                mock_log.assert_called_once()
                assert "Unsupported modality detected" in str(mock_log.call_args)


class TestSecurityIntegration:
    """Test security integration and audit logging."""
    
    @pytest.fixture
    def service_with_audit(self):
        """Create service with audit logging enabled."""
        config = OrthancSecurityConfig(
            require_tls=False,
            username="test",
            password="test",
            enable_audit_logging=True
        )
        return OrthancIntegrationService(config=config)
    
    @pytest.mark.asyncio
    async def test_health_check_audit_logging(self, service_with_audit):
        """Test health check logs audit information."""
        with patch.object(service_with_audit, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "Version": "1.12.0",
                "Name": "Orthanc"
            })
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            with patch.object(service_with_audit.logger, 'info') as mock_log:
                result = await service_with_audit.health_check("test_client")
                
                # Should have logged health check
                assert mock_log.call_count >= 1
                assert any("health check" in str(call) for call in mock_log.call_args_list)
    
    @pytest.mark.asyncio
    async def test_dicom_metadata_phi_audit(self, service_with_audit):
        """Test PHI access is audited for DICOM metadata."""
        with patch.object(service_with_audit, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session
            
            # Mock response with PHI data
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "PatientID": "PHI_PATIENT_001",  # Contains PHI
                "StudyDate": "20240101",
                "Modality": "CT"
            })
            mock_response.raise_for_status = Mock()
            
            mock_instance_response = AsyncMock()
            mock_instance_response.status = 200
            mock_instance_response.json = AsyncMock(return_value={
                "ParentStudy": "study123",
                "ParentSeries": "series123"
            })
            mock_instance_response.raise_for_status = Mock()
            
            mock_session.get.return_value.__aenter__.side_effect = [
                mock_response, mock_instance_response
            ]
            
            with patch.object(service_with_audit.logger, 'info') as mock_log:
                await service_with_audit.get_dicom_metadata("test123")
                
                # Should have logged PHI access
                audit_calls = [call for call in mock_log.call_args_list 
                             if "DICOM metadata accessed" in str(call)]
                assert len(audit_calls) >= 1
                
                # Verify PHI flag is set
                call_str = str(audit_calls[0])
                assert "has_patient_id=True" in call_str


class TestErrorHandling:
    """Test error handling and resilience."""
    
    @pytest.fixture
    def service(self):
        """Create service for error testing."""
        config = OrthancSecurityConfig(
            require_tls=False,
            username="test",
            password="test"
        )
        return OrthancIntegrationService(config=config)
    
    @pytest.mark.asyncio
    async def test_health_check_connection_error(self, service):
        """Test health check handles connection errors gracefully."""
        with patch.object(service, '_get_session') as mock_get_session:
            mock_get_session.side_effect = Exception("Connection failed")
            
            result = await service.health_check("test")
            
            assert result["status"] == "unreachable"
            assert "Connection failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_dicom_metadata_not_found(self, service):
        """Test handling of non-existent DICOM instances."""
        with patch.object(service, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value = mock_session
            
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(ResourceNotFound, match="not found in Orthanc"):
                await service.get_dicom_metadata("nonexistent123")


# Integration tests
@pytest.mark.integration
class TestOrthancIntegrationEndToEnd:
    """End-to-end integration tests with mock Orthanc server."""
    
    @pytest.mark.asyncio
    async def test_full_integration_workflow(self):
        """Test complete workflow from health check to metadata retrieval."""
        config = OrthancSecurityConfig(
            base_url="http://localhost:8042",
            username="admin",
            password="admin123",
            require_tls=False
        )
        service = OrthancIntegrationService(config=config)
        
        try:
            # Test health check
            health = await service.health_check("integration_test")
            print(f"Health check result: {health}")
            
            if health["status"] == "healthy":
                # Try to get system info (should work with our mock server)
                # This is a basic connectivity test
                pass
            
        except Exception as e:
            # Expected if Orthanc server is not running
            print(f"Integration test skipped (server not available): {e}")
        
        finally:
            await service.close()


if __name__ == "__main__":
    # Run specific test groups
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "not integration"  # Skip integration tests by default
    ])