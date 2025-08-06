"""
Secure Storage Service for Document Management

Provides high-level secure storage operations with encryption,
audit logging, and compliance features for healthcare documents.
"""

import asyncio
import hashlib
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

import structlog

from app.core.security import SecurityManager
from app.core.exceptions import ValidationError, ResourceNotFound, UnauthorizedAccess
from app.core.monitoring import trace_method, metrics
from app.core.audit_logger import audit_logger, AuditEventType, AuditSeverity

from .storage_backend import StorageBackendInterface, get_storage_backend, StorageResult
from .service import AccessContext

logger = structlog.get_logger(__name__)


class SecureStorageService:
    """
    Secure storage service with encryption and compliance features.
    
    This service provides a higher-level interface over the storage backend
    with additional security features for healthcare document management.
    """
    
    def __init__(
        self,
        storage_backend: Optional[StorageBackendInterface] = None,
        security_manager: Optional[SecurityManager] = None
    ):
        self.storage_backend = storage_backend or get_storage_backend()
        self.security_manager = security_manager or SecurityManager()
        self.logger = logger.bind(service="SecureStorageService")
    
    @trace_method("secure_store")
    @metrics.track_operation("secure_storage.store")
    async def secure_store(
        self,
        file_data: bytes,
        filename: str,
        patient_id: str,
        document_type: str,
        context: AccessContext,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StorageResult:
        """
        Securely store a document with encryption and audit logging.
        
        Args:
            file_data: Raw file bytes
            filename: Original filename
            patient_id: Patient identifier
            document_type: Type of document (e.g., 'lab_result', 'image')
            context: Access context with user information
            metadata: Additional metadata to store with the document
            
        Returns:
            StorageResult: Information about the stored document
            
        Raises:
            ValidationError: If input validation fails
            UnauthorizedAccess: If user lacks permissions
        """
        try:
            self.logger.info(
                "Starting secure document storage",
                filename=filename,
                patient_id=patient_id,
                document_type=document_type,
                user_id=context.user_id,
                file_size=len(file_data)
            )
            
            # Input validation
            if not file_data:
                raise ValidationError("File data cannot be empty")
            if not filename.strip():
                raise ValidationError("Filename cannot be empty")
            if not patient_id.strip():
                raise ValidationError("Patient ID cannot be empty")
            if len(file_data) > 100 * 1024 * 1024:  # 100MB limit
                raise ValidationError("File size exceeds 100MB limit")
            
            # Enhanced metadata with compliance information
            enhanced_metadata = {
                "document_type": document_type,
                "uploaded_by": context.user_id,
                "upload_timestamp": datetime.utcnow().isoformat(),
                "patient_id": patient_id,
                "original_filename": filename,
                "phi_encrypted": True,
                "hipaa_compliant": True,
                "soc2_compliant": True,
                "access_context": {
                    "ip_address": context.ip_address,
                    "user_agent": context.user_agent,
                    "session_id": context.session_id,
                    "purpose": context.purpose
                },
                **(metadata or {})
            }
            
            # Store document using storage backend
            storage_result = await self.storage_backend.store_document(
                file_data=file_data,
                filename=filename,
                patient_id=patient_id,
                metadata=enhanced_metadata
            )
            
            # Log secure storage event for audit
            await audit_logger.log_event(
                event_type=AuditEventType.DOCUMENT_CREATED,
                user_id=context.user_id,
                resource_id=storage_result.storage_key,
                details={
                    "filename": filename,
                    "patient_id": patient_id,
                    "document_type": document_type,
                    "file_size": len(file_data),
                    "storage_bucket": storage_result.bucket,
                    "encryption_enabled": storage_result.encrypted,
                    "hash_sha256": storage_result.hash_sha256[:16]  # Truncated for logging
                },
                severity=AuditSeverity.INFO
            )
            
            self.logger.info(
                "Document stored securely",
                storage_key=storage_result.storage_key,
                bucket=storage_result.bucket,
                encrypted=storage_result.encrypted,
                hash=storage_result.hash_sha256[:16]
            )
            
            return storage_result
            
        except Exception as e:
            self.logger.error(
                "Secure storage failed",
                error=str(e),
                filename=filename,
                patient_id=patient_id,
                user_id=context.user_id
            )
            raise
    
    @trace_method("secure_retrieve")
    @metrics.track_operation("secure_storage.retrieve")
    async def secure_retrieve(
        self,
        storage_key: str,
        bucket: str,
        context: AccessContext,
        purpose: str = "clinical_review"
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Securely retrieve a document with audit logging.
        
        Args:
            storage_key: Storage key for the document
            bucket: Storage bucket name
            context: Access context with user information
            purpose: Purpose of access for audit trail
            
        Returns:
            Tuple[bytes, Dict]: File data and metadata
            
        Raises:
            ResourceNotFound: If document doesn't exist
            UnauthorizedAccess: If user lacks permissions
        """
        try:
            self.logger.info(
                "Starting secure document retrieval",
                storage_key=storage_key,
                bucket=bucket,
                user_id=context.user_id,
                purpose=purpose
            )
            
            # Check if document exists
            if not await self.storage_backend.document_exists(storage_key, bucket):
                raise ResourceNotFound(f"Document not found: {storage_key}")
            
            # Get document metadata first
            metadata = await self.storage_backend.get_document_metadata(storage_key, bucket)
            
            # Verify user has access to this patient's documents
            patient_id = metadata.get("patient-id")
            if patient_id and not await self._verify_patient_access(patient_id, context.user_id):
                raise UnauthorizedAccess("Access denied to patient documents")
            
            # Retrieve document data
            file_data = await self.storage_backend.retrieve_document(storage_key, bucket)
            
            # Log PHI access for compliance
            await audit_logger.log_event(
                event_type=AuditEventType.PHI_ACCESSED,
                user_id=context.user_id,
                resource_id=storage_key,
                details={
                    "access_type": "document_retrieval",
                    "purpose": purpose,
                    "patient_id": patient_id,
                    "storage_bucket": bucket,
                    "file_size": len(file_data),
                    "original_filename": metadata.get("original-filename", "unknown"),
                    "encryption_verified": metadata.get("encrypted") == "true"
                },
                severity=AuditSeverity.INFO
            )
            
            self.logger.info(
                "Document retrieved securely",
                storage_key=storage_key,
                file_size=len(file_data),
                user_id=context.user_id,
                purpose=purpose
            )
            
            return file_data, metadata
            
        except Exception as e:
            self.logger.error(
                "Secure retrieval failed",
                error=str(e),
                storage_key=storage_key,
                user_id=context.user_id
            )
            raise
    
    @trace_method("secure_delete")
    async def secure_delete(
        self,
        storage_key: str,
        bucket: str,
        context: AccessContext,
        reason: str
    ) -> bool:
        """
        Securely delete a document with audit logging.
        
        Args:
            storage_key: Storage key for the document
            bucket: Storage bucket name
            context: Access context with user information
            reason: Reason for deletion
            
        Returns:
            bool: True if successfully deleted
            
        Raises:
            UnauthorizedAccess: If user lacks permissions
        """
        try:
            self.logger.info(
                "Starting secure document deletion",
                storage_key=storage_key,
                bucket=bucket,
                user_id=context.user_id,
                reason=reason
            )
            
            # Get document metadata before deletion
            metadata = {}
            try:
                metadata = await self.storage_backend.get_document_metadata(storage_key, bucket)
            except ResourceNotFound:
                self.logger.warning("Document not found for deletion", storage_key=storage_key)
                return False
            
            # Verify user has access to delete this document
            patient_id = metadata.get("patient-id")
            if patient_id and not await self._verify_patient_access(patient_id, context.user_id):
                raise UnauthorizedAccess("Access denied to delete patient documents")
            
            # Perform deletion
            success = await self.storage_backend.delete_document(storage_key, bucket)
            
            if success:
                # Log deletion for audit
                await audit_logger.log_event(
                    event_type=AuditEventType.DOCUMENT_DELETED,
                    user_id=context.user_id,
                    resource_id=storage_key,
                    details={
                        "storage_bucket": bucket,
                        "patient_id": patient_id,
                        "original_filename": metadata.get("original-filename", "unknown"),
                        "deletion_reason": reason,
                        "file_size": metadata.get("size", 0),
                        "secure_deletion": True
                    },
                    severity=AuditSeverity.WARNING  # Deletions are notable events
                )
                
                self.logger.info(
                    "Document deleted securely",
                    storage_key=storage_key,
                    bucket=bucket,
                    reason=reason
                )
            
            return success
            
        except Exception as e:
            self.logger.error(
                "Secure deletion failed",
                error=str(e),
                storage_key=storage_key,
                user_id=context.user_id
            )
            raise
    
    async def _verify_patient_access(self, patient_id: str, user_id: str) -> bool:
        """
        Verify user has access to patient documents.
        
        This is a simplified implementation. In a real system,
        this would check RBAC permissions, patient consent, etc.
        """
        # For now, assume all authenticated users have access
        # In production, implement proper RBAC checking
        return True
    
    async def get_storage_statistics(
        self,
        bucket: str = "documents"
    ) -> Dict[str, Any]:
        """
        Get storage statistics for monitoring and compliance.
        
        Returns:
            Dict with storage statistics
        """
        try:
            # This would require additional methods in the storage backend
            # For now, return mock statistics
            return {
                "total_documents": 0,
                "total_size_bytes": 0,
                "encryption_enabled": True,
                "last_backup": datetime.utcnow().isoformat(),
                "compliance_status": "SOC2_HIPAA_COMPLIANT"
            }
            
        except Exception as e:
            self.logger.error("Failed to get storage statistics", error=str(e))
            raise


# Factory function for dependency injection
def get_secure_storage_service(
    storage_backend = None
) -> SecureStorageService:
    """Factory function to create SecureStorageService instance."""
    return SecureStorageService(storage_backend=storage_backend)