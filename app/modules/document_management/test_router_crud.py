"""
Unit Tests for Document Management CRUD Endpoints

Tests for the new document management endpoints with SOC2/HIPAA compliance.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.document_management.router import router
from app.modules.document_management.schemas import (
    DocumentMetadataResponse, DocumentUpdateRequest, DocumentDeletionResponse,
    DocumentStatsResponse, BulkDeleteRequest, BulkUpdateTagsRequest, BulkOperationResponse
)
from app.core.database_unified import DocumentType, DocumentAction
from app.core.exceptions import ResourceNotFound, UnauthorizedAccess, ValidationError


class TestDocumentMetadataEndpoint:
    """Test suite for GET /documents/{document_id} endpoint."""
    
    @pytest.fixture
    def mock_document_service(self):
        """Mock document service for testing."""
        service = Mock()
        service.get_document_metadata = AsyncMock()
        return service
    
    @pytest.fixture
    def sample_document_response(self):
        """Sample document metadata response."""
        return DocumentMetadataResponse(
            document_id=str(uuid.uuid4()),
            patient_id=str(uuid.uuid4()),
            filename="test_document.pdf",
            storage_key="documents/test_document.pdf",
            file_size=1024,
            mime_type="application/pdf",
            hash_sha256="abc123def456",
            document_type=DocumentType.LAB_RESULT,
            document_category="Laboratory",
            auto_classification_confidence=0.95,
            extracted_text="Sample extracted text",
            tags=["urgent", "lab"],
            metadata={"test": "value"},
            version=1,
            parent_document_id=None,
            is_latest_version=True,
            uploaded_by=str(uuid.uuid4()),
            uploaded_at=datetime.now(),
            updated_at=None,
            updated_by=None
        )

    @pytest.mark.asyncio
    async def test_get_document_metadata_success(self, mock_document_service, sample_document_response):
        """Test successful document metadata retrieval."""
        # Arrange
        document_id = str(uuid.uuid4())
        mock_document_service.get_document_metadata.return_value = sample_document_response
        
        with patch('app.modules.document_management.router.get_document_service', return_value=mock_document_service):
            with patch('app.modules.document_management.router.get_current_user_id', return_value=str(uuid.uuid4())):
                # Act
                from app.modules.document_management.router import get_document_metadata
                result = await get_document_metadata(
                    document_id=document_id,
                    db=Mock(spec=AsyncSession),
                    current_user_id=str(uuid.uuid4())
                )
        
        # Assert
        assert result == sample_document_response
        mock_document_service.get_document_metadata.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_document_metadata_invalid_uuid(self):
        """Test document metadata retrieval with invalid UUID."""
        # Arrange
        invalid_id = "not-a-uuid"
        
        with patch('app.modules.document_management.router.get_current_user_id', return_value=str(uuid.uuid4())):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                from app.modules.document_management.router import get_document_metadata
                await get_document_metadata(
                    document_id=invalid_id,
                    db=Mock(spec=AsyncSession),
                    current_user_id=str(uuid.uuid4())
                )
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid document ID format" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_document_metadata_not_found(self, mock_document_service):
        """Test document metadata retrieval when document not found."""
        # Arrange
        document_id = str(uuid.uuid4())
        mock_document_service.get_document_metadata.side_effect = ResourceNotFound("Document not found")
        
        with patch('app.modules.document_management.router.get_document_service', return_value=mock_document_service):
            with patch('app.modules.document_management.router.get_current_user_id', return_value=str(uuid.uuid4())):
                # Act & Assert
                with pytest.raises(HTTPException) as exc_info:
                    from app.modules.document_management.router import get_document_metadata
                    await get_document_metadata(
                        document_id=document_id,
                        db=Mock(spec=AsyncSession),
                        current_user_id=str(uuid.uuid4())
                    )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_get_document_metadata_unauthorized(self, mock_document_service):
        """Test document metadata retrieval with unauthorized access."""
        # Arrange
        document_id = str(uuid.uuid4())
        mock_document_service.get_document_metadata.side_effect = UnauthorizedAccess("Access denied")
        
        with patch('app.modules.document_management.router.get_document_service', return_value=mock_document_service):
            with patch('app.modules.document_management.router.get_current_user_id', return_value=str(uuid.uuid4())):
                # Act & Assert
                with pytest.raises(HTTPException) as exc_info:
                    from app.modules.document_management.router import get_document_metadata
                    await get_document_metadata(
                        document_id=document_id,
                        db=Mock(spec=AsyncSession),
                        current_user_id=str(uuid.uuid4())
                    )
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestDocumentUpdateEndpoint:
    """Test suite for PATCH /documents/{document_id} endpoint."""
    
    @pytest.fixture
    def mock_document_service(self):
        """Mock document service for testing."""
        service = Mock()
        service.update_document_metadata = AsyncMock()
        return service
    
    @pytest.fixture
    def sample_update_request(self):
        """Sample document update request."""
        return DocumentUpdateRequest(
            filename="updated_document.pdf",
            document_type=DocumentType.CLINICAL_NOTE,
            document_category="Clinical",
            tags=["updated", "clinical"],
            metadata={"updated": True}
        )
    
    @pytest.fixture
    def sample_updated_response(self):
        """Sample updated document response."""
        return DocumentMetadataResponse(
            document_id=str(uuid.uuid4()),
            patient_id=str(uuid.uuid4()),
            filename="updated_document.pdf",
            storage_key="documents/updated_document.pdf",
            file_size=1024,
            mime_type="application/pdf",
            hash_sha256="abc123def456",
            document_type=DocumentType.CLINICAL_NOTE,
            document_category="Clinical",
            auto_classification_confidence=0.95,
            extracted_text="Sample extracted text",
            tags=["updated", "clinical"],
            metadata={"updated": True},
            version=2,
            parent_document_id=None,
            is_latest_version=True,
            uploaded_by=str(uuid.uuid4()),
            uploaded_at=datetime.now() - timedelta(hours=1),
            updated_at=datetime.now(),
            updated_by=str(uuid.uuid4())
        )

    @pytest.mark.asyncio
    async def test_update_document_metadata_success(self, mock_document_service, sample_update_request, sample_updated_response):
        """Test successful document metadata update."""
        # Arrange
        document_id = str(uuid.uuid4())
        reason = "Updated for testing purposes"
        mock_document_service.update_document_metadata.return_value = sample_updated_response
        
        with patch('app.modules.document_management.router.get_document_service', return_value=mock_document_service):
            with patch('app.modules.document_management.router.get_current_user_id', return_value=str(uuid.uuid4())):
                # Act
                from app.modules.document_management.router import update_document_metadata
                result = await update_document_metadata(
                    document_id=document_id,
                    updates=sample_update_request,
                    reason=reason,
                    db=Mock(spec=AsyncSession),
                    current_user_id=str(uuid.uuid4())
                )
        
        # Assert
        assert result == sample_updated_response
        mock_document_service.update_document_metadata.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_document_metadata_invalid_reason(self, sample_update_request):
        """Test document update with invalid reason."""
        # Arrange
        document_id = str(uuid.uuid4())
        invalid_reason = "x"  # Too short
        
        with patch('app.modules.document_management.router.get_current_user_id', return_value=str(uuid.uuid4())):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                from app.modules.document_management.router import update_document_metadata
                await update_document_metadata(
                    document_id=document_id,
                    updates=sample_update_request,
                    reason=invalid_reason,
                    db=Mock(spec=AsyncSession),
                    current_user_id=str(uuid.uuid4())
                )
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "at least 3 characters" in str(exc_info.value.detail)


class TestDocumentDeletionEndpoint:
    """Test suite for DELETE /documents/{document_id} endpoint."""
    
    @pytest.fixture
    def mock_document_service(self):
        """Mock document service for testing."""
        service = Mock()
        service.delete_document = AsyncMock()
        return service
    
    @pytest.fixture
    def sample_deletion_response(self):
        """Sample document deletion response."""
        return DocumentDeletionResponse(
            document_id=str(uuid.uuid4()),
            deletion_type="soft",
            deleted_at=datetime.now(),
            deleted_by=str(uuid.uuid4()),
            reason="Test deletion",
            retention_policy_id=None,
            secure_deletion_scheduled=False
        )

    @pytest.mark.asyncio
    async def test_delete_document_success(self, mock_document_service, sample_deletion_response):
        """Test successful document deletion."""
        # Arrange
        document_id = str(uuid.uuid4())
        deletion_reason = "Testing document deletion"
        mock_document_service.delete_document.return_value = sample_deletion_response
        
        with patch('app.modules.document_management.router.get_document_service', return_value=mock_document_service):
            with patch('app.modules.document_management.router.get_current_user_id', return_value=str(uuid.uuid4())):
                # Act
                from app.modules.document_management.router import delete_document
                result = await delete_document(
                    document_id=document_id,
                    deletion_reason=deletion_reason,
                    hard_delete=False,
                    db=Mock(spec=AsyncSession),
                    current_user_id=str(uuid.uuid4())
                )
        
        # Assert
        assert result == sample_deletion_response
        mock_document_service.delete_document.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_document_invalid_reason(self):
        """Test document deletion with invalid reason."""
        # Arrange
        document_id = str(uuid.uuid4())
        invalid_reason = "x"  # Too short
        
        with patch('app.modules.document_management.router.get_current_user_id', return_value=str(uuid.uuid4())):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                from app.modules.document_management.router import delete_document
                await delete_document(
                    document_id=document_id,
                    deletion_reason=invalid_reason,
                    hard_delete=False,
                    db=Mock(spec=AsyncSession),
                    current_user_id=str(uuid.uuid4())
                )
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "at least 3 characters" in str(exc_info.value.detail)


class TestDocumentStatsEndpoint:
    """Test suite for GET /documents/stats endpoint."""
    
    @pytest.fixture
    def mock_document_service(self):
        """Mock document service for testing."""
        service = Mock()
        service.get_document_statistics = AsyncMock()
        return service
    
    @pytest.fixture
    def sample_stats_response(self):
        """Sample document statistics response."""
        return DocumentStatsResponse(
            total_documents=100,
            documents_by_type={
                "LAB_RESULT": 50,
                "CLINICAL_NOTE": 30,
                "IMAGING": 20
            },
            recent_uploads=[],
            storage_usage_bytes=1024000,
            classification_accuracy=0.92,
            upload_trends={"2024-06": 50, "2024-05": 30},
            access_frequency={"daily": 100, "weekly": 500}
        )

    @pytest.mark.asyncio
    async def test_get_document_statistics_success(self, mock_document_service, sample_stats_response):
        """Test successful document statistics retrieval."""
        # Arrange
        mock_document_service.get_document_statistics.return_value = sample_stats_response
        
        with patch('app.modules.document_management.router.get_document_service', return_value=mock_document_service):
            with patch('app.modules.document_management.router.get_current_user_id', return_value=str(uuid.uuid4())):
                # Act
                from app.modules.document_management.router import get_document_statistics
                result = await get_document_statistics(
                    patient_id=None,
                    date_from=None,
                    date_to=None,
                    include_phi=False,
                    db=Mock(spec=AsyncSession),
                    current_user_id=str(uuid.uuid4())
                )
        
        # Assert
        assert result == sample_stats_response
        mock_document_service.get_document_statistics.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_document_statistics_with_patient_filter(self, mock_document_service, sample_stats_response):
        """Test document statistics with patient ID filter."""
        # Arrange
        patient_id = str(uuid.uuid4())
        mock_document_service.get_document_statistics.return_value = sample_stats_response
        
        with patch('app.modules.document_management.router.get_document_service', return_value=mock_document_service):
            with patch('app.modules.document_management.router.get_current_user_id', return_value=str(uuid.uuid4())):
                # Act
                from app.modules.document_management.router import get_document_statistics
                result = await get_document_statistics(
                    patient_id=patient_id,
                    date_from=None,
                    date_to=None,
                    include_phi=False,
                    db=Mock(spec=AsyncSession),
                    current_user_id=str(uuid.uuid4())
                )
        
        # Assert
        assert result == sample_stats_response
        # Verify patient_id was passed to service
        call_args = mock_document_service.get_document_statistics.call_args
        assert call_args[1]['patient_id'] == patient_id


class TestBulkOperationsEndpoints:
    """Test suite for bulk operation endpoints."""
    
    @pytest.fixture
    def mock_document_service(self):
        """Mock document service for testing."""
        service = Mock()
        service.bulk_delete_documents = AsyncMock()
        service.bulk_update_tags = AsyncMock()
        return service
    
    @pytest.fixture
    def sample_bulk_delete_request(self):
        """Sample bulk delete request."""
        return BulkDeleteRequest(
            document_ids=[str(uuid.uuid4()), str(uuid.uuid4())],
            reason="Bulk testing deletion",
            hard_delete=False
        )
    
    @pytest.fixture
    def sample_bulk_operation_response(self):
        """Sample bulk operation response."""
        return BulkOperationResponse(
            success_count=2,
            failed_count=0,
            total_count=2,
            failed_documents=[],
            operation_id=str(uuid.uuid4()),
            completed_at=datetime.now()
        )

    @pytest.mark.asyncio
    async def test_bulk_delete_documents_success(self, mock_document_service, sample_bulk_delete_request, sample_bulk_operation_response):
        """Test successful bulk document deletion."""
        # Arrange
        mock_document_service.bulk_delete_documents.return_value = sample_bulk_operation_response
        
        with patch('app.modules.document_management.router.get_document_service', return_value=mock_document_service):
            with patch('app.modules.document_management.router.get_current_user_id', return_value=str(uuid.uuid4())):
                # Act
                from app.modules.document_management.router import bulk_delete_documents
                result = await bulk_delete_documents(
                    request=sample_bulk_delete_request,
                    db=Mock(spec=AsyncSession),
                    current_user_id=str(uuid.uuid4())
                )
        
        # Assert
        assert result == sample_bulk_operation_response
        mock_document_service.bulk_delete_documents.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_bulk_update_tags_success(self, mock_document_service, sample_bulk_operation_response):
        """Test successful bulk tag update."""
        # Arrange
        bulk_tags_request = BulkUpdateTagsRequest(
            document_ids=[str(uuid.uuid4()), str(uuid.uuid4())],
            tags=["test", "bulk"],
            action="replace"
        )
        mock_document_service.bulk_update_tags.return_value = sample_bulk_operation_response
        
        with patch('app.modules.document_management.router.get_document_service', return_value=mock_document_service):
            with patch('app.modules.document_management.router.get_current_user_id', return_value=str(uuid.uuid4())):
                # Act
                from app.modules.document_management.router import bulk_update_tags
                result = await bulk_update_tags(
                    request=bulk_tags_request,
                    db=Mock(spec=AsyncSession),
                    current_user_id=str(uuid.uuid4())
                )
        
        # Assert
        assert result == sample_bulk_operation_response
        mock_document_service.bulk_update_tags.assert_called_once()


class TestInputValidation:
    """Test suite for input validation security."""
    
    def test_document_update_request_validation(self):
        """Test document update request validation."""
        # Test valid request
        valid_request = DocumentUpdateRequest(
            filename="valid_file.pdf",
            tags=["tag1", "tag2"]
        )
        assert valid_request.filename == "valid_file.pdf"
        assert valid_request.tags == ["tag1", "tag2"]
        
        # Test filename with dangerous characters should be rejected by validation
        with pytest.raises(ValueError):
            DocumentUpdateRequest(filename="../../../etc/passwd")
        
        # Test too many tags
        with pytest.raises(ValueError):
            DocumentUpdateRequest(tags=["tag"] * 25)  # More than 20 tags
    
    def test_bulk_delete_request_validation(self):
        """Test bulk delete request validation."""
        # Test valid request
        valid_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        valid_request = BulkDeleteRequest(
            document_ids=valid_ids,
            reason="Valid deletion reason"
        )
        assert valid_request.document_ids == valid_ids
        
        # Test invalid UUID should be rejected
        with pytest.raises(ValueError):
            BulkDeleteRequest(
                document_ids=["not-a-uuid"],
                reason="Valid reason"
            )
        
        # Test short reason should be rejected
        with pytest.raises(ValueError):
            BulkDeleteRequest(
                document_ids=valid_ids,
                reason="x"  # Too short
            )


# Test Configuration and Fixtures
@pytest.fixture
def anyio_backend():
    """Use asyncio backend for async tests."""
    return 'asyncio'


@pytest.fixture
def test_app():
    """Create test application."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router, prefix="/documents")
    return app


if __name__ == "__main__":
    # Run tests with: python -m pytest app/modules/document_management/test_router_crud.py -v
    pytest.main([__file__, "-v"])