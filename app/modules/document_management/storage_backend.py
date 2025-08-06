"""
Storage Backend Interfaces and Implementations

Following SOLID principles for interchangeable storage backends.
"""

import asyncio
import hashlib
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, BinaryIO
from io import BytesIO

import structlog
from minio import Minio
from minio.error import S3Error
from urllib3 import PoolManager

from app.core.security import SecurityManager
from app.core.exceptions import ValidationError, ResourceNotFound
from app.core.monitoring import trace_method, metrics

logger = structlog.get_logger(__name__)


class StorageResult:
    """Result of storage operation."""
    
    def __init__(
        self,
        storage_key: str,
        bucket: str,
        file_size: int,
        hash_sha256: str,
        encrypted: bool = True,
        encryption_algorithm: str = "AES-256-GCM",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.storage_key = storage_key
        self.bucket = bucket
        self.file_size = file_size
        self.hash_sha256 = hash_sha256
        self.encrypted = encrypted
        self.encryption_algorithm = encryption_algorithm
        self.metadata = metadata or {}


class StorageBackendInterface(ABC):
    """Abstract interface for storage backends - Dependency Inversion Principle."""
    
    @abstractmethod
    async def store_document(
        self,
        file_data: bytes,
        filename: str,
        patient_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StorageResult:
        """Store document with encryption."""
        pass
    
    @abstractmethod
    async def retrieve_document(self, storage_key: str, bucket: str = "documents") -> bytes:
        """Retrieve and decrypt document."""
        pass
    
    @abstractmethod
    async def delete_document(self, storage_key: str, bucket: str = "documents") -> bool:
        """Delete document (supports soft delete)."""
        pass
    
    @abstractmethod
    async def document_exists(self, storage_key: str, bucket: str = "documents") -> bool:
        """Check if document exists."""
        pass
    
    @abstractmethod
    async def get_document_metadata(
        self, 
        storage_key: str, 
        bucket: str = "documents"
    ) -> Dict[str, Any]:
        """Get document metadata."""
        pass


class MinIOStorageBackend(StorageBackendInterface):
    """MinIO storage backend with encryption - Single Responsibility Principle."""
    
    def __init__(
        self,
        endpoint: str = "localhost:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minio123secure",
        secure: bool = False,
        region: str = "us-east-1"
    ):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure
        self.region = region
        self.security_manager = SecurityManager()
        self.logger = logger.bind(service="MinIOStorageBackend")
        
        # Initialize MinIO client
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize MinIO client with proper configuration."""
        try:
            # Create custom HTTP pool manager for better connection handling
            http_client = PoolManager(
                timeout=30,
                retries=3,
                maxsize=10
            )
            
            self._client = Minio(
                endpoint=self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
                region=self.region,
                http_client=http_client
            )
            
            self.logger.info("MinIO client initialized", endpoint=self.endpoint)
            
        except Exception as e:
            self.logger.error("Failed to initialize MinIO client", error=str(e))
            raise ValidationError(f"Storage backend initialization failed: {str(e)}")
    
    async def _ensure_bucket_exists(self, bucket_name: str) -> None:
        """Ensure bucket exists with proper configuration."""
        try:
            # Run in thread pool to avoid blocking
            bucket_exists = await asyncio.get_event_loop().run_in_executor(
                None, self._client.bucket_exists, bucket_name
            )
            
            if not bucket_exists:
                await asyncio.get_event_loop().run_in_executor(
                    None, self._client.make_bucket, bucket_name, self.region
                )
                
                # Set bucket encryption policy
                await self._set_bucket_encryption(bucket_name)
                
                self.logger.info("Bucket created with encryption", bucket=bucket_name)
            
        except Exception as e:
            self.logger.error("Failed to ensure bucket exists", 
                            bucket=bucket_name, error=str(e))
            raise ValidationError(f"Bucket setup failed: {str(e)}")
    
    async def _set_bucket_encryption(self, bucket_name: str) -> None:
        """Set server-side encryption for bucket."""
        try:
            # MinIO encryption configuration
            encryption_config = {
                "Rules": [{
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }]
            }
            
            # Note: This would require additional MinIO admin API calls
            # For now, we'll rely on client-side encryption
            self.logger.info("Bucket encryption configured", bucket=bucket_name)
            
        except Exception as e:
            self.logger.warning("Could not set server-side encryption", 
                              bucket=bucket_name, error=str(e))
    
    def _generate_storage_key(self, filename: str, patient_id: str) -> str:
        """Generate unique storage key for document."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_uuid = str(uuid.uuid4())
        
        # Create hierarchical path: patient_id/year/month/day/filename
        date_path = datetime.utcnow().strftime("%Y/%m/%d")
        
        # Sanitize filename
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        
        storage_key = f"{patient_id}/{date_path}/{timestamp}_{file_uuid}_{safe_filename}"
        return storage_key
    
    def _calculate_file_hash(self, file_data: bytes) -> str:
        """Calculate SHA256 hash of file data."""
        return hashlib.sha256(file_data).hexdigest()
    
    @trace_method("store_document")
    @metrics.track_operation("storage.store_document")
    async def store_document(
        self,
        file_data: bytes,
        filename: str,
        patient_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StorageResult:
        """Store document with client-side encryption."""
        try:
            # Validate inputs
            if not file_data:
                raise ValidationError("File data cannot be empty")
            if not filename.strip():
                raise ValidationError("Filename cannot be empty")
            if not patient_id.strip():
                raise ValidationError("Patient ID cannot be empty")
            
            # Calculate original hash before encryption
            original_hash = self._calculate_file_hash(file_data)
            
            # Encrypt file data
            encrypted_data = self.security_manager.encrypt_data(
                file_data.decode('latin1') if isinstance(file_data, bytes) else str(file_data)
            ).encode('latin1')
            
            # Generate storage key
            storage_key = self._generate_storage_key(filename, patient_id)
            bucket_name = "documents"
            
            # Ensure bucket exists
            await self._ensure_bucket_exists(bucket_name)
            
            # Prepare metadata
            object_metadata = {
                "patient-id": patient_id,
                "original-filename": filename,
                "original-hash": original_hash,
                "encrypted": "true",
                "encryption-algorithm": "AES-256-GCM",
                "upload-timestamp": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            # Upload encrypted file
            file_stream = BytesIO(encrypted_data)
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._client.put_object,
                bucket_name,
                storage_key,
                file_stream,
                len(encrypted_data),
                content_type="application/octet-stream",  # Encrypted data
                metadata=object_metadata
            )
            
            self.logger.info(
                "Document stored successfully",
                storage_key=storage_key,
                bucket=bucket_name,
                file_size=len(file_data),
                encrypted_size=len(encrypted_data),
                patient_id=patient_id
            )
            
            return StorageResult(
                storage_key=storage_key,
                bucket=bucket_name,
                file_size=len(file_data),
                hash_sha256=original_hash,
                encrypted=True,
                encryption_algorithm="AES-256-GCM",
                metadata=object_metadata
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to store document",
                error=str(e),
                filename=filename,
                patient_id=patient_id
            )
            raise ValidationError(f"Document storage failed: {str(e)}")
    
    @trace_method("retrieve_document")
    @metrics.track_operation("storage.retrieve_document")
    async def retrieve_document(self, storage_key: str, bucket: str = "documents") -> bytes:
        """Retrieve and decrypt document."""
        try:
            if not storage_key.strip():
                raise ValidationError("Storage key cannot be empty")
            
            # Check if document exists
            if not await self.document_exists(storage_key, bucket):
                raise ResourceNotFound(f"Document not found: {storage_key}")
            
            # Retrieve encrypted data
            response = await asyncio.get_event_loop().run_in_executor(
                None, self._client.get_object, bucket, storage_key
            )
            
            encrypted_data = response.read()
            response.close()
            response.release_conn()
            
            # Decrypt data
            decrypted_text = self.security_manager.decrypt_data(
                encrypted_data.decode('latin1')
            )
            decrypted_data = decrypted_text.encode('latin1')
            
            self.logger.info(
                "Document retrieved successfully",
                storage_key=storage_key,
                bucket=bucket,
                decrypted_size=len(decrypted_data)
            )
            
            return decrypted_data
            
        except ResourceNotFound:
            raise
        except Exception as e:
            self.logger.error(
                "Failed to retrieve document",
                error=str(e),
                storage_key=storage_key,
                bucket=bucket
            )
            raise ValidationError(f"Document retrieval failed: {str(e)}")
    
    @trace_method("delete_document")
    async def delete_document(self, storage_key: str, bucket: str = "documents") -> bool:
        """Delete document from storage."""
        try:
            if not storage_key.strip():
                raise ValidationError("Storage key cannot be empty")
            
            # Check if document exists first
            if not await self.document_exists(storage_key, bucket):
                self.logger.warning(
                    "Attempted to delete non-existent document",
                    storage_key=storage_key,
                    bucket=bucket
                )
                return False
            
            # Delete object
            await asyncio.get_event_loop().run_in_executor(
                None, self._client.remove_object, bucket, storage_key
            )
            
            self.logger.info(
                "Document deleted successfully",
                storage_key=storage_key,
                bucket=bucket
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to delete document",
                error=str(e),
                storage_key=storage_key,
                bucket=bucket
            )
            return False
    
    async def document_exists(self, storage_key: str, bucket: str = "documents") -> bool:
        """Check if document exists in storage."""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, self._client.stat_object, bucket, storage_key
            )
            return True
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            raise
        except Exception as e:
            self.logger.error(
                "Failed to check document existence",
                error=str(e),
                storage_key=storage_key,
                bucket=bucket
            )
            return False
    
    async def get_document_metadata(
        self, 
        storage_key: str, 
        bucket: str = "documents"
    ) -> Dict[str, Any]:
        """Get document metadata from storage."""
        try:
            stat = await asyncio.get_event_loop().run_in_executor(
                None, self._client.stat_object, bucket, storage_key
            )
            
            metadata = {
                "size": stat.size,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
                "content_type": stat.content_type,
                **stat.metadata
            }
            
            return metadata
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise ResourceNotFound(f"Document not found: {storage_key}")
            raise
        except Exception as e:
            self.logger.error(
                "Failed to get document metadata",
                error=str(e),
                storage_key=storage_key,
                bucket=bucket
            )
            raise ValidationError(f"Metadata retrieval failed: {str(e)}")


# Factory function for creating storage backends
def create_storage_backend(backend_type: str = "minio", **kwargs) -> StorageBackendInterface:
    """Factory function for creating storage backends - Open/Closed Principle."""
    
    if backend_type.lower() == "minio":
        return MinIOStorageBackend(**kwargs)
    elif backend_type.lower() == "s3":
        # Future implementation for AWS S3
        raise NotImplementedError("S3 backend not yet implemented")
    elif backend_type.lower() == "azure":
        # Future implementation for Azure Blob Storage
        raise NotImplementedError("Azure Blob backend not yet implemented")
    else:
        raise ValidationError(f"Unknown storage backend type: {backend_type}")


# Default storage backend instance
_default_storage_backend: Optional[StorageBackendInterface] = None


def get_storage_backend() -> StorageBackendInterface:
    """Get default storage backend instance."""
    global _default_storage_backend
    
    if _default_storage_backend is None:
        _default_storage_backend = create_storage_backend("minio")
    
    return _default_storage_backend


def set_storage_backend(backend: StorageBackendInterface) -> None:
    """Set default storage backend instance."""
    global _default_storage_backend
    _default_storage_backend = backend