"""
Test Suite for Document Storage Backend

Following TDD principles with comprehensive test coverage.
"""

import pytest
import asyncio
import hashlib
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any
from io import BytesIO

from app.modules.document_management.storage_backend import (
    MinIOStorageBackend, StorageResult, StorageBackendInterface,
    create_storage_backend, get_storage_backend
)
from app.core.exceptions import ValidationError, ResourceNotFound
from app.core.security import SecurityManager


class TestStorageBackendInterface:
    """Test the abstract storage backend interface."""
    
    def test_interface_cannot_be_instantiated(self):
        """Test that abstract interface cannot be instantiated."""
        with pytest.raises(TypeError):
            StorageBackendInterface()


class TestMinIOStorageBackend:
    """Test MinIO storage backend implementation."""
    
    @pytest.fixture
    def mock_minio_client(self):
        """Mock MinIO client for testing."""
        with patch('app.modules.document_management.storage_backend.Minio') as mock_minio:
            mock_client = Mock()
            mock_minio.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def mock_security_manager(self):
        """Mock security manager for testing."""
        with patch('app.modules.document_management.storage_backend.SecurityManager') as mock_sm:
            mock_security = Mock()
            mock_security.encrypt_data.return_value = "encrypted_data"
            mock_security.decrypt_data.return_value = "decrypted_data"
            mock_sm.return_value = mock_security
            yield mock_security
    
    @pytest.fixture
    async def storage_backend(self, mock_minio_client, mock_security_manager):
        """Create MinIO storage backend for testing."""
        backend = MinIOStorageBackend(
            endpoint="localhost:9000",
            access_key="test_key",
            secret_key="test_secret"
        )
        return backend
    
    @pytest.mark.asyncio
    async def test_upload_document_encrypts_content(self, storage_backend, mock_minio_client):
        """Test that uploaded documents are encrypted."""
        # Arrange
        file_data = b"sensitive medical data"
        filename = "test.pdf"
        patient_id = "123e4567-e89b-12d3-a456-426614174000"
        
        mock_minio_client.bucket_exists.return_value = True
        mock_minio_client.put_object.return_value = None
        
        # Act
        storage_result = await storage_backend.store_document(
            file_data, filename, patient_id
        )
        
        # Assert
        assert storage_result.encrypted == True
        assert storage_result.encryption_algorithm == "AES-256-GCM"
        assert storage_result.file_size == len(file_data)
        assert storage_result.hash_sha256 == hashlib.sha256(file_data).hexdigest()
        
        # Verify MinIO client was called with encrypted data
        mock_minio_client.put_object.assert_called_once()
        call_args = mock_minio_client.put_object.call_args
        assert call_args[0][0] == "documents"  # bucket
        assert patient_id in call_args[0][1]  # storage_key contains patient_id
        assert isinstance(call_args[0][2], BytesIO)  # file stream
    
    @pytest.mark.asyncio
    async def test_upload_document_validates_input(self, storage_backend):
        """Test input validation for document upload."""
        # Test empty file data
        with pytest.raises(ValidationError, match="File data cannot be empty"):
            await storage_backend.store_document(b"", "test.pdf", "patient_id")
        
        # Test empty filename
        with pytest.raises(ValidationError, match="Filename cannot be empty"):
            await storage_backend.store_document(b"data", "", "patient_id")
        
        # Test empty patient ID
        with pytest.raises(ValidationError, match="Patient ID cannot be empty"):
            await storage_backend.store_document(b"data", "test.pdf", "")
    
    @pytest.mark.asyncio
    async def test_generate_storage_key_hierarchical(self, storage_backend):
        """Test storage key generation creates hierarchical structure."""
        filename = "test_document.pdf"
        patient_id = "patient_123"
        
        storage_key = storage_backend._generate_storage_key(filename, patient_id)
        
        # Should be in format: patient_id/year/month/day/timestamp_uuid_filename
        parts = storage_key.split('/')
        assert parts[0] == patient_id
        assert len(parts) == 5  # patient_id/year/month/day/filename
        assert "test_document.pdf" in parts[-1]
    
    @pytest.mark.asyncio
    async def test_retrieve_document_decrypts_content(self, storage_backend, mock_minio_client):
        """Test document retrieval and decryption."""
        # Arrange
        storage_key = "patient/2023/06/29/test_file.pdf"
        encrypted_data = b"encrypted_content"
        
        mock_response = Mock()
        mock_response.read.return_value = encrypted_data
        mock_response.close.return_value = None
        mock_response.release_conn.return_value = None
        
        mock_minio_client.stat_object.return_value = Mock()  # Document exists
        mock_minio_client.get_object.return_value = mock_response
        
        # Act
        decrypted_data = await storage_backend.retrieve_document(storage_key)
        
        # Assert
        assert decrypted_data == b"decrypted_data"
        mock_minio_client.get_object.assert_called_once_with("documents", storage_key)
    
    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_document_raises_error(self, storage_backend, mock_minio_client):
        """Test retrieving non-existent document raises ResourceNotFound."""
        from minio.error import S3Error
        
        # Arrange
        storage_key = "nonexistent/file.pdf"
        mock_minio_client.stat_object.side_effect = S3Error(
            "NoSuchKey", "Key not found", "GET", "bucket", "key"
        )
        
        # Act & Assert
        with pytest.raises(ResourceNotFound, match="Document not found"):
            await storage_backend.retrieve_document(storage_key)
    
    @pytest.mark.asyncio
    async def test_document_exists_returns_correct_status(self, storage_backend, mock_minio_client):
        """Test document existence check."""
        storage_key = "patient/file.pdf"
        
        # Test existing document
        mock_minio_client.stat_object.return_value = Mock()
        exists = await storage_backend.document_exists(storage_key)
        assert exists == True
        
        # Test non-existent document
        from minio.error import S3Error
        mock_minio_client.stat_object.side_effect = S3Error(
            "NoSuchKey", "Key not found", "GET", "bucket", "key"
        )
        exists = await storage_backend.document_exists(storage_key)
        assert exists == False
    
    @pytest.mark.asyncio
    async def test_delete_document_removes_from_storage(self, storage_backend, mock_minio_client):
        """Test document deletion."""
        storage_key = "patient/file.pdf"
        
        # Mock document exists
        mock_minio_client.stat_object.return_value = Mock()
        mock_minio_client.remove_object.return_value = None
        
        # Act
        result = await storage_backend.delete_document(storage_key)
        
        # Assert
        assert result == True
        mock_minio_client.remove_object.assert_called_once_with("documents", storage_key)
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_document_returns_false(self, storage_backend, mock_minio_client):
        """Test deleting non-existent document returns False."""
        from minio.error import S3Error
        
        storage_key = "nonexistent/file.pdf"
        mock_minio_client.stat_object.side_effect = S3Error(
            "NoSuchKey", "Key not found", "GET", "bucket", "key"
        )
        
        result = await storage_backend.delete_document(storage_key)
        assert result == False
    
    @pytest.mark.asyncio
    async def test_get_document_metadata_returns_info(self, storage_backend, mock_minio_client):
        """Test retrieving document metadata."""
        storage_key = "patient/file.pdf"
        
        # Mock metadata
        mock_stat = Mock()
        mock_stat.size = 1024
        mock_stat.last_modified = "2023-06-29T12:00:00Z"
        mock_stat.etag = "abc123"
        mock_stat.content_type = "application/pdf"
        mock_stat.metadata = {"patient-id": "123", "encrypted": "true"}
        
        mock_minio_client.stat_object.return_value = mock_stat
        
        # Act
        metadata = await storage_backend.get_document_metadata(storage_key)
        
        # Assert
        assert metadata["size"] == 1024
        assert metadata["content_type"] == "application/pdf"
        assert metadata["patient-id"] == "123"
        assert metadata["encrypted"] == "true"
    
    @pytest.mark.asyncio
    async def test_bucket_creation_with_encryption(self, storage_backend, mock_minio_client):
        """Test bucket creation with encryption settings."""
        bucket_name = "test-bucket"
        
        mock_minio_client.bucket_exists.return_value = False
        mock_minio_client.make_bucket.return_value = None
        
        # Act
        await storage_backend._ensure_bucket_exists(bucket_name)
        
        # Assert
        mock_minio_client.make_bucket.assert_called_once_with(bucket_name, "us-east-1")
    
    def test_calculate_file_hash_returns_sha256(self, storage_backend):
        """Test file hash calculation."""
        file_data = b"test content"
        expected_hash = hashlib.sha256(file_data).hexdigest()
        
        calculated_hash = storage_backend._calculate_file_hash(file_data)
        
        assert calculated_hash == expected_hash


class TestStorageBackendFactory:
    """Test storage backend factory functions."""
    
    def test_create_storage_backend_minio(self):
        """Test creating MinIO storage backend."""
        backend = create_storage_backend("minio")
        assert isinstance(backend, MinIOStorageBackend)
    
    def test_create_storage_backend_invalid_type(self):
        """Test creating invalid storage backend type."""
        with pytest.raises(ValidationError, match="Unknown storage backend type"):
            create_storage_backend("invalid")
    
    def test_create_storage_backend_not_implemented(self):
        """Test creating not-yet-implemented storage backends."""
        with pytest.raises(NotImplementedError):
            create_storage_backend("s3")
        
        with pytest.raises(NotImplementedError):
            create_storage_backend("azure")
    
    def test_get_storage_backend_singleton(self):
        """Test storage backend singleton pattern."""
        backend1 = get_storage_backend()
        backend2 = get_storage_backend()
        
        # Should return the same instance
        assert backend1 is backend2


class TestStorageResult:
    """Test storage result data class."""
    
    def test_storage_result_creation(self):
        """Test StorageResult creation with all fields."""
        result = StorageResult(
            storage_key="patient/file.pdf",
            bucket="documents",
            file_size=1024,
            hash_sha256="abc123",
            encrypted=True,
            encryption_algorithm="AES-256-GCM",
            metadata={"test": "value"}
        )
        
        assert result.storage_key == "patient/file.pdf"
        assert result.bucket == "documents"
        assert result.file_size == 1024
        assert result.hash_sha256 == "abc123"
        assert result.encrypted == True
        assert result.encryption_algorithm == "AES-256-GCM"
        assert result.metadata == {"test": "value"}
    
    def test_storage_result_defaults(self):
        """Test StorageResult with default values."""
        result = StorageResult(
            storage_key="test",
            bucket="bucket",
            file_size=100,
            hash_sha256="hash"
        )
        
        assert result.encrypted == True
        assert result.encryption_algorithm == "AES-256-GCM"
        assert result.metadata == {}


@pytest.mark.integration
class TestMinIOIntegration:
    """Integration tests with actual MinIO instance (requires MinIO running)."""
    
    @pytest.fixture
    async def real_storage_backend(self):
        """Create real MinIO backend for integration testing."""
        backend = MinIOStorageBackend(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minio123secure"
        )
        yield backend
    
    @pytest.mark.skip(reason="Requires running MinIO instance")
    @pytest.mark.asyncio
    async def test_real_upload_download_cycle(self, real_storage_backend):
        """Test full upload/download cycle with real MinIO."""
        # This test would run against a real MinIO instance
        # Skip by default to avoid requiring MinIO for unit tests
        
        file_data = b"Test medical document content"
        filename = "integration_test.pdf"
        patient_id = "test_patient_123"
        
        # Upload
        storage_result = await real_storage_backend.store_document(
            file_data, filename, patient_id
        )
        
        assert storage_result.storage_key is not None
        assert storage_result.encrypted == True
        
        # Verify exists
        exists = await real_storage_backend.document_exists(storage_result.storage_key)
        assert exists == True
        
        # Download
        retrieved_data = await real_storage_backend.retrieve_document(storage_result.storage_key)
        assert retrieved_data == file_data
        
        # Cleanup
        deleted = await real_storage_backend.delete_document(storage_result.storage_key)
        assert deleted == True
        
        # Verify deleted
        exists_after = await real_storage_backend.document_exists(storage_result.storage_key)
        assert exists_after == False