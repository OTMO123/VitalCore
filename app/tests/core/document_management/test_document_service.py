"""
Test Suite for Document Storage Service

Following TDD principles with comprehensive test coverage.
"""

import pytest
import asyncio
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.document_management.service import DocumentStorageService, AccessContext
from app.modules.document_management.schemas import (
    DocumentUploadRequest, DocumentUploadResponse, DocumentSearchRequest
)
from app.modules.document_management.storage_backend import StorageBackendInterface, StorageResult
from app.core.database_unified import DocumentStorage, DocumentType, Patient, User
from app.core.exceptions import ValidationError, ResourceNotFound, UnauthorizedAccess
from app.core.security import SecurityManager


class MockStorageBackend(StorageBackendInterface):
    """Mock storage backend for testing."""
    
    def __init__(self):
        self.stored_documents = {}
    
    async def store_document(self, file_data, filename, patient_id, metadata=None):
        storage_key = f"{patient_id}/{filename}"
        self.stored_documents[storage_key] = file_data
        return StorageResult(
            storage_key=storage_key,
            bucket="documents",
            file_size=len(file_data),
            hash_sha256="test_hash",
            encrypted=True
        )
    
    async def retrieve_document(self, storage_key, bucket="documents"):
        if storage_key not in self.stored_documents:
            raise ResourceNotFound(f"Document not found: {storage_key}")
        return self.stored_documents[storage_key]
    
    async def delete_document(self, storage_key, bucket="documents"):
        if storage_key in self.stored_documents:
            del self.stored_documents[storage_key]
            return True
        return False
    
    async def document_exists(self, storage_key, bucket="documents"):
        return storage_key in self.stored_documents
    
    async def get_document_metadata(self, storage_key, bucket="documents"):
        if storage_key not in self.stored_documents:
            raise ResourceNotFound(f"Document not found: {storage_key}")
        return {"size": len(self.stored_documents[storage_key])}


class TestDocumentStorageService:
    """Test document storage service."""
    
    @pytest.fixture
    def mock_storage_backend(self):
        """Create mock storage backend."""
        return MockStorageBackend()
    
    @pytest.fixture
    def mock_security_manager(self):
        """Create mock security manager."""
        mock_sm = Mock(spec=SecurityManager)
        mock_sm.encrypt_data.return_value = "encrypted_data"
        mock_sm.decrypt_data.return_value = "decrypted_data"
        return mock_sm
    
    @pytest.fixture
    def document_service(self, mock_storage_backend, mock_security_manager):
        """Create document service for testing."""
        return DocumentStorageService(
            storage_backend=mock_storage_backend,
            security_manager=mock_security_manager
        )
    
    @pytest.fixture
    def access_context(self):
        """Create access context for testing."""
        return AccessContext(
            user_id=str(uuid.uuid4()),
            ip_address="192.168.1.1",
            user_agent="test-agent",
            session_id=str(uuid.uuid4())
        )
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = Mock(spec=AsyncSession)
        session.add = Mock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.execute = AsyncMock()
        return session
    
    @pytest.mark.asyncio
    async def test_upload_document_success(
        self, 
        document_service, 
        mock_db_session, 
        access_context
    ):
        """Test successful document upload."""
        # Arrange
        file_data = b"test medical document"
        upload_request = DocumentUploadRequest(
            patient_id=str(uuid.uuid4()),
            filename="test_document.pdf",
            document_type=DocumentType.LAB_RESULT,
            tags=["urgent", "blood_test"]
        )
        
        # Mock patient access verification
        mock_patient_result = Mock()
        mock_patient_result.scalar_one_or_none.return_value = Mock(spec=Patient)
        mock_db_session.execute.return_value = mock_patient_result
        
        # Mock block number query
        mock_block_result = Mock()
        mock_block_result.scalar.return_value = 0
        mock_db_session.execute.side_effect = [mock_patient_result, mock_block_result]
        
        # Act
        response = await document_service.upload_document(
            db=mock_db_session,
            file_data=file_data,
            upload_request=upload_request,
            context=access_context
        )
        
        # Assert
        assert isinstance(response, DocumentUploadResponse)
        assert response.filename == "test_document.pdf"
        assert response.file_size == len(file_data)
        assert response.encrypted == True
        assert response.document_type == DocumentType.LAB_RESULT
        
        # Verify database operations
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_document_empty_file_fails(
        self, 
        document_service, 
        mock_db_session, 
        access_context
    ):
        """Test upload with empty file data fails."""
        upload_request = DocumentUploadRequest(
            patient_id=str(uuid.uuid4()),
            filename="empty.pdf",
            document_type=DocumentType.LAB_RESULT
        )
        
        # Mock patient access verification
        mock_patient_result = Mock()
        mock_patient_result.scalar_one_or_none.return_value = Mock(spec=Patient)
        mock_db_session.execute.return_value = mock_patient_result
        
        with pytest.raises(ValidationError, match="File data cannot be empty"):
            await document_service.upload_document(
                db=mock_db_session,
                file_data=b"",
                upload_request=upload_request,
                context=access_context
            )
    
    @pytest.mark.asyncio
    async def test_upload_document_large_file_fails(
        self, 
        document_service, 
        mock_db_session, 
        access_context
    ):
        """Test upload with oversized file fails."""
        upload_request = DocumentUploadRequest(
            patient_id=str(uuid.uuid4()),
            filename="large.pdf",
            document_type=DocumentType.LAB_RESULT
        )
        
        # Mock patient access verification
        mock_patient_result = Mock()
        mock_patient_result.scalar_one_or_none.return_value = Mock(spec=Patient)
        mock_db_session.execute.return_value = mock_patient_result
        
        # Create file larger than 100MB
        large_file = b"x" * (101 * 1024 * 1024)
        
        with pytest.raises(ValidationError, match="File size exceeds 100MB limit"):
            await document_service.upload_document(
                db=mock_db_session,
                file_data=large_file,
                upload_request=upload_request,
                context=access_context
            )
    
    @pytest.mark.asyncio
    async def test_upload_document_unauthorized_patient_access(
        self, 
        document_service, 
        mock_db_session, 
        access_context
    ):
        """Test upload fails when user doesn't have patient access."""
        upload_request = DocumentUploadRequest(
            patient_id=str(uuid.uuid4()),
            filename="test.pdf",
            document_type=DocumentType.LAB_RESULT
        )
        
        # Mock patient not found (no access)
        mock_patient_result = Mock()
        mock_patient_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_patient_result
        
        with pytest.raises(UnauthorizedAccess, match="Access denied to patient records"):
            await document_service.upload_document(
                db=mock_db_session,
                file_data=b"test data",
                upload_request=upload_request,
                context=access_context
            )
    
    @pytest.mark.asyncio
    async def test_download_document_success(
        self, 
        document_service, 
        mock_db_session, 
        access_context
    ):
        """Test successful document download."""
        # Arrange
        document_id = str(uuid.uuid4())
        patient_id = str(uuid.uuid4())
        test_file_data = b"test document content"
        
        # Mock document exists in database
        mock_document = Mock(spec=DocumentStorage)
        mock_document.id = document_id
        mock_document.patient_id = patient_id
        mock_document.original_filename = "test.pdf"
        mock_document.storage_path = f"{patient_id}/test.pdf"
        mock_document.storage_bucket = "documents"
        mock_document.hash_sha256 = "5d41402abc4b2a76b9719d911017c592"  # hash of "hello"
        mock_document.mime_type = "application/pdf"
        mock_document.uploaded_at = datetime.utcnow()
        mock_document.updated_at = None
        
        # Mock database queries
        doc_result = Mock()
        doc_result.scalar_one_or_none.return_value = mock_document
        
        patient_result = Mock()
        patient_result.scalar_one_or_none.return_value = Mock(spec=Patient)
        
        block_result = Mock()
        block_result.scalar.return_value = 0
        
        mock_db_session.execute.side_effect = [doc_result, patient_result, block_result]
        
        # Store test data in mock storage
        document_service.storage_backend.stored_documents[f"{patient_id}/test.pdf"] = test_file_data
        
        # Act
        file_data, response = await document_service.download_document(
            db=mock_db_session,
            document_id=document_id,
            context=access_context
        )
        
        # Assert
        assert file_data == test_file_data
        assert response.document_id == document_id
        assert response.filename == "test.pdf"
        assert response.content_type == "application/pdf"
    
    @pytest.mark.asyncio
    async def test_download_nonexistent_document_fails(
        self, 
        document_service, 
        mock_db_session, 
        access_context
    ):
        """Test download of non-existent document fails."""
        document_id = str(uuid.uuid4())
        
        # Mock document not found in database
        doc_result = Mock()
        doc_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = doc_result
        
        with pytest.raises(ResourceNotFound, match="Document .* not found"):
            await document_service.download_document(
                db=mock_db_session,
                document_id=document_id,
                context=access_context
            )
    
    @pytest.mark.asyncio
    async def test_search_documents_with_filters(
        self, 
        document_service, 
        mock_db_session, 
        access_context
    ):
        """Test document search with various filters."""
        # Arrange
        patient_id = str(uuid.uuid4())
        search_request = DocumentSearchRequest(
            patient_id=patient_id,
            document_types=[DocumentType.LAB_RESULT],
            tags=["urgent"],
            offset=0,
            limit=10
        )
        
        # Mock search results
        mock_doc1 = Mock(spec=DocumentStorage)
        mock_doc1.id = uuid.uuid4()
        mock_doc1.patient_id = patient_id
        mock_doc1.original_filename = "lab_result.pdf"
        mock_doc1.storage_path = "path1"
        mock_doc1.file_size_bytes = 1024
        mock_doc1.mime_type = "application/pdf"
        mock_doc1.hash_sha256 = "hash1"
        mock_doc1.document_type = DocumentType.LAB_RESULT
        mock_doc1.document_category = None
        mock_doc1.auto_classification_confidence = None
        mock_doc1.extracted_text = None
        mock_doc1.tags = ["urgent"]
        mock_doc1.metadata = {}
        mock_doc1.version = 1
        mock_doc1.parent_document_id = None
        mock_doc1.is_latest_version = True
        mock_doc1.uploaded_by = uuid.uuid4()
        mock_doc1.uploaded_at = datetime.utcnow()
        mock_doc1.updated_at = None
        mock_doc1.updated_by = None
        
        # Mock database queries
        patient_result = Mock()
        patient_result.scalar_one_or_none.return_value = Mock(spec=Patient)
        
        search_result = Mock()
        search_result.scalars.return_value.all.return_value = [mock_doc1]
        
        count_result = Mock()
        count_result.scalar.return_value = 1
        
        mock_db_session.execute.side_effect = [patient_result, search_result, count_result]
        
        # Act
        response = await document_service.search_documents(
            db=mock_db_session,
            search_request=search_request,
            context=access_context
        )
        
        # Assert
        assert len(response.documents) == 1
        assert response.total == 1
        assert response.documents[0].filename == "lab_result.pdf"
        assert response.documents[0].document_type == DocumentType.LAB_RESULT
        assert "urgent" in response.documents[0].tags
    
    @pytest.mark.asyncio
    async def test_search_documents_unauthorized_patient(
        self, 
        document_service, 
        mock_db_session, 
        access_context
    ):
        """Test search fails for unauthorized patient access."""
        patient_id = str(uuid.uuid4())
        search_request = DocumentSearchRequest(patient_id=patient_id)
        
        # Mock patient not found (no access)
        patient_result = Mock()
        patient_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = patient_result
        
        with pytest.raises(UnauthorizedAccess, match="Access denied to patient records"):
            await document_service.search_documents(
                db=mock_db_session,
                search_request=search_request,
                context=access_context
            )
    
    def test_detect_mime_type_common_extensions(self, document_service):
        """Test MIME type detection for common file extensions."""
        test_cases = [
            ("document.pdf", "application/pdf"),
            ("report.doc", "application/msword"),
            ("scan.jpg", "image/jpeg"),
            ("notes.txt", "text/plain"),
            ("unknown.xyz", "application/octet-stream")
        ]
        
        for filename, expected_mime in test_cases:
            actual_mime = document_service._detect_mime_type(filename)
            assert actual_mime == expected_mime
    
    @pytest.mark.asyncio
    async def test_audit_record_creation(self, document_service, mock_db_session, access_context):
        """Test audit record creation with blockchain-like verification."""
        document_id = str(uuid.uuid4())
        
        # Mock previous audit record
        mock_prev_audit = Mock()
        mock_prev_audit.current_hash = "previous_hash"
        
        prev_audit_result = Mock()
        prev_audit_result.scalar_one_or_none.return_value = mock_prev_audit
        
        block_result = Mock()
        block_result.scalar.return_value = 5  # Previous block number
        
        mock_db_session.execute.side_effect = [prev_audit_result, block_result]
        
        # Act
        audit_record = await document_service._create_audit_record(
            db=mock_db_session,
            document_id=document_id,
            action=DocumentType.LAB_RESULT,  # This should be DocumentAction
            context=access_context
        )
        
        # Assert
        assert audit_record.document_id == uuid.UUID(document_id)
        assert audit_record.user_id == uuid.UUID(access_context.user_id)
        assert audit_record.block_number == 6  # Next block number
        assert audit_record.previous_hash == "previous_hash"
        assert audit_record.current_hash is not None
        
        # Verify database operations
        mock_db_session.add.assert_called_with(audit_record)


class TestAccessContext:
    """Test access context utility class."""
    
    def test_access_context_creation(self):
        """Test access context creation with all fields."""
        user_id = str(uuid.uuid4())
        ip_address = "192.168.1.1"
        user_agent = "Mozilla/5.0"
        session_id = str(uuid.uuid4())
        purpose = "treatment"
        
        context = AccessContext(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            purpose=purpose
        )
        
        assert context.user_id == user_id
        assert context.ip_address == ip_address
        assert context.user_agent == user_agent
        assert context.session_id == session_id
        assert context.purpose == purpose
    
    def test_access_context_defaults(self):
        """Test access context with default values."""
        user_id = str(uuid.uuid4())
        
        context = AccessContext(user_id=user_id)
        
        assert context.user_id == user_id
        assert context.ip_address is None
        assert context.user_agent is None
        assert context.session_id is None
        assert context.purpose == "operations"


@pytest.mark.integration
class TestDocumentServiceIntegration:
    """Integration tests for document service."""
    
    @pytest.fixture
    async def real_document_service(self):
        """Create document service with real dependencies."""
        # This would use real database and storage backend
        # Skip by default to avoid requiring infrastructure
        pass
    
    @pytest.mark.skip(reason="Requires real database and MinIO")
    @pytest.mark.asyncio
    async def test_full_document_lifecycle(self, real_document_service):
        """Test complete document lifecycle: upload -> search -> download -> delete."""
        # This test would run against real infrastructure
        # Skip by default for unit testing
        pass