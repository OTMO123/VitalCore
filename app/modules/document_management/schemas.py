"""
Document Management Pydantic Schemas

Request/response validation schemas for document operations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict
import structlog

from app.core.database_unified import DocumentType, DocumentAction

logger = structlog.get_logger(__name__)


class DocumentUploadRequest(BaseModel):
    """Request schema for document upload."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    patient_id: str = Field(..., description="Patient UUID")
    filename: str = Field(..., min_length=1, max_length=255, description="Original filename")
    document_type: DocumentType = Field(..., description="Type of document")
    document_category: Optional[str] = Field(None, max_length=100, description="Document category")
    tags: Optional[List[str]] = Field(default=[], description="Document tags")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")
    
    @field_validator('patient_id')
    @classmethod
    def validate_patient_id(cls, v):
        """Validate patient ID is a valid UUID."""
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError('Patient ID must be a valid UUID')
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v):
        """Validate filename doesn't contain dangerous characters."""
        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
        if any(char in v for char in dangerous_chars):
            raise ValueError('Filename contains invalid characters')
        return v
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate tags are reasonable."""
        if v and len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        return v or []


class DocumentUploadResponse(BaseModel):
    """Response schema for document upload."""
    
    document_id: str = Field(..., description="Generated document UUID")
    storage_key: str = Field(..., description="Storage system key")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    hash_sha256: str = Field(..., description="SHA256 hash of original file")
    document_type: DocumentType = Field(..., description="Document type")
    encrypted: bool = Field(..., description="Whether file is encrypted")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    version: int = Field(..., description="Document version")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: str
        }
    )


class DocumentDownloadResponse(BaseModel):
    """Response schema for document download."""
    
    document_id: str = Field(..., description="Document UUID")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., description="File size in bytes")
    hash_sha256: str = Field(..., description="SHA256 hash for verification")
    last_modified: datetime = Field(..., description="Last modification time")
    
    # File content is handled separately as binary data
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class DocumentMetadataResponse(BaseModel):
    """Response schema for document metadata."""
    
    document_id: str = Field(..., description="Document UUID")
    patient_id: str = Field(..., description="Patient UUID")
    filename: str = Field(..., description="Original filename")
    storage_key: str = Field(..., description="Storage system key")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    hash_sha256: str = Field(..., description="SHA256 hash")
    
    # Classification
    document_type: DocumentType = Field(..., description="Document type")
    document_category: Optional[str] = Field(None, description="Document category")
    auto_classification_confidence: Optional[float] = Field(None, description="AI classification confidence")
    
    # Content
    extracted_text: Optional[str] = Field(None, description="Extracted text content")
    tags: List[str] = Field(default=[], description="Document tags")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    
    # Versioning
    version: int = Field(..., description="Document version")
    parent_document_id: Optional[str] = Field(None, description="Parent document UUID")
    is_latest_version: bool = Field(..., description="Is this the latest version")
    
    # Audit
    uploaded_by: str = Field(..., description="Uploader user UUID")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    updated_by: Optional[str] = Field(None, description="Last updater user UUID")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class DocumentListResponse(BaseModel):
    """Response schema for document list."""
    
    documents: List[DocumentMetadataResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")
    offset: int = Field(..., description="Pagination offset")
    limit: int = Field(..., description="Pagination limit")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class DocumentSearchRequest(BaseModel):
    """Request schema for document search."""
    
    patient_id: Optional[str] = Field(None, description="Filter by patient UUID")
    document_types: Optional[List[DocumentType]] = Field(None, description="Filter by document types")
    document_category: Optional[str] = Field(None, description="Filter by category")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    search_text: Optional[str] = Field(None, description="Full-text search in extracted content")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    
    # Pagination
    offset: int = Field(0, ge=0, description="Pagination offset")
    limit: int = Field(50, ge=1, le=1000, description="Pagination limit")
    
    # Sorting
    sort_by: str = Field("uploaded_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")
    
    @field_validator('patient_id')
    @classmethod
    def validate_patient_id(cls, v):
        """Validate patient ID if provided."""
        if v:
            try:
                UUID(v)
                return v
            except ValueError:
                raise ValueError('Patient ID must be a valid UUID')
        return v
    
    @field_validator('sort_by')
    @classmethod
    def validate_sort_by(cls, v):
        """Validate sort field."""
        allowed_fields = ['uploaded_at', 'filename', 'document_type', 'file_size']
        if v not in allowed_fields:
            raise ValueError(f'Sort field must be one of: {allowed_fields}')
        return v
    
    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v):
        """Validate sort order."""
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('Sort order must be "asc" or "desc"')
        return v.lower()


class DocumentUpdateRequest(BaseModel):
    """Request schema for document metadata update."""
    
    document_type: Optional[DocumentType] = Field(None, description="Update document type")
    document_category: Optional[str] = Field(None, max_length=100, description="Update category")
    tags: Optional[List[str]] = Field(None, description="Update tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Update metadata")
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate tags are reasonable."""
        if v and len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        return v


class DocumentShareRequest(BaseModel):
    """Request schema for document sharing."""
    
    shared_with: Optional[str] = Field(None, description="User UUID to share with (null for public)")
    permissions: Dict[str, bool] = Field(
        default={'view': True}, 
        description="Permission set"
    )
    expires_at: Optional[datetime] = Field(None, description="Share expiration time")
    
    @field_validator('shared_with')
    @classmethod
    def validate_shared_with(cls, v):
        """Validate shared_with user ID if provided."""
        if v:
            try:
                UUID(v)
                return v
            except ValueError:
                raise ValueError('Shared with must be a valid UUID')
        return v
    
    @field_validator('permissions')
    @classmethod
    def validate_permissions(cls, v):
        """Validate permissions."""
        allowed_permissions = {'view', 'download', 'print'}
        for perm in v.keys():
            if perm not in allowed_permissions:
                raise ValueError(f'Invalid permission: {perm}')
        return v


class DocumentShareResponse(BaseModel):
    """Response schema for document sharing."""
    
    share_id: str = Field(..., description="Share UUID")
    document_id: str = Field(..., description="Document UUID")
    share_token: str = Field(..., description="Secure share token")
    shared_with: Optional[str] = Field(None, description="User UUID")
    permissions: Dict[str, bool] = Field(..., description="Permission set")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")
    created_at: datetime = Field(..., description="Share creation time")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class DocumentAuditLogResponse(BaseModel):
    """Response schema for document audit logs."""
    
    audit_id: str = Field(..., description="Audit log UUID")
    document_id: str = Field(..., description="Document UUID")
    user_id: str = Field(..., description="User UUID")
    action: DocumentAction = Field(..., description="Action performed")
    ip_address: Optional[str] = Field(None, description="User IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    accessed_at: datetime = Field(..., description="Access timestamp")
    
    # Blockchain verification
    current_hash: str = Field(..., description="Audit record hash")
    block_number: int = Field(..., description="Block number")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class DocumentAuditListResponse(BaseModel):
    """Response schema for document audit log list."""
    
    audit_logs: List[DocumentAuditLogResponse] = Field(..., description="Audit log entries")
    total: int = Field(..., description="Total number of entries")
    offset: int = Field(..., description="Pagination offset")
    limit: int = Field(..., description="Pagination limit")


class DocumentVersionResponse(BaseModel):
    """Response schema for document version information."""
    
    document_id: str = Field(..., description="Document UUID")
    version: int = Field(..., description="Version number")
    parent_document_id: Optional[str] = Field(None, description="Parent document UUID")
    is_latest_version: bool = Field(..., description="Is latest version")
    created_at: datetime = Field(..., description="Version creation time")
    created_by: str = Field(..., description="Version creator UUID")
    change_summary: Optional[str] = Field(None, description="Summary of changes")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class DocumentClassificationResponse(BaseModel):
    """Response schema for document classification."""
    
    document_type: DocumentType = Field(..., description="Classified document type")
    confidence: float = Field(..., description="Classification confidence (0-100)")
    alternative_types: List[Dict[str, Union[DocumentType, float]]] = Field(
        default=[], 
        description="Alternative classifications"
    )
    extracted_entities: List[Dict[str, Any]] = Field(
        default=[], 
        description="Extracted entities (dates, names, etc.)"
    )
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")


class DocumentProcessingStatus(BaseModel):
    """Status of document processing operations."""
    
    document_id: str = Field(..., description="Document UUID")
    status: str = Field(..., description="Processing status")
    progress: int = Field(..., description="Progress percentage (0-100)")
    current_step: str = Field(..., description="Current processing step")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class ClassificationResponse(BaseModel):
    """Response schema for document classification."""
    
    document_type: str = Field(..., description="Classified document type")
    confidence: float = Field(..., description="Classification confidence (0-1)")
    category: str = Field(..., description="Document category")
    subcategory: Optional[str] = Field(None, description="Document subcategory")
    tags: List[str] = Field(default=[], description="Extracted tags")
    classification_method: str = Field(..., description="Classification method used")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")


class FilenameGenerationResponse(BaseModel):
    """Response schema for filename generation."""
    
    filename: str = Field(..., description="Generated filename")
    original_filename: str = Field(..., description="Original filename")
    confidence: float = Field(..., description="Generation confidence (0-1)")
    generation_method: str = Field(..., description="Generation method used")
    suggestions: List[str] = Field(default=[], description="Alternative filename suggestions")
    metadata: Dict[str, Any] = Field(default={}, description="Generation metadata")


class VersionHistoryResponse(BaseModel):
    """Response schema for document version history."""
    
    document_id: str = Field(..., description="Document UUID")
    versions: List[Dict[str, Any]] = Field(..., description="Version history list")
    total_versions: int = Field(..., description="Total number of versions")


# ============================================================================
# NEW SCHEMAS FOR ADDITIONAL CRUD ENDPOINTS
# ============================================================================

class DocumentUpdateRequest(BaseModel):
    """Request schema for document metadata updates."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    filename: Optional[str] = Field(None, max_length=255, description="Updated filename")
    document_type: Optional[DocumentType] = Field(None, description="Updated document type")
    document_category: Optional[str] = Field(None, max_length=100, description="Updated document category")
    tags: Optional[List[str]] = Field(None, max_length=20, description="Updated document tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")
    
    @field_validator('filename')
    @classmethod
    def validate_filename_security(cls, v):
        """Validate filename doesn't contain dangerous characters."""
        if v:
            dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
            if any(char in v for char in dangerous_chars):
                raise ValueError('Filename contains prohibited characters')
            if len(v.strip()) == 0:
                raise ValueError('Filename cannot be empty')
        return v
    
    @field_validator('tags')
    @classmethod
    def validate_tags_limit(cls, v):
        """Validate tags are reasonable."""
        if v and len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        # Remove duplicates and empty tags
        if v:
            v = list(set(tag.strip() for tag in v if tag.strip()))
        return v


class DocumentDeletionResponse(BaseModel):
    """Response schema for document deletion."""
    
    document_id: str = Field(..., description="Deleted document UUID")
    deletion_type: str = Field(..., description="Type of deletion (soft/hard)")
    deleted_at: datetime = Field(..., description="Deletion timestamp")
    deleted_by: str = Field(..., description="User who deleted the document")
    reason: str = Field(..., description="Reason for deletion")
    retention_policy_id: Optional[str] = Field(None, description="Applied retention policy")
    secure_deletion_scheduled: bool = Field(..., description="Whether secure deletion is scheduled")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class DocumentStatsResponse(BaseModel):
    """Response schema for document statistics."""
    
    total_documents: int = Field(..., description="Total number of documents")
    documents_by_type: Dict[str, int] = Field(..., description="Document count by type")
    recent_uploads: List[DocumentMetadataResponse] = Field(..., description="Recent uploads")
    storage_usage_bytes: int = Field(..., description="Total storage usage in bytes")
    classification_accuracy: float = Field(..., description="AI classification accuracy (0-1)")
    upload_trends: Dict[str, int] = Field(default={}, description="Upload trends by month")
    access_frequency: Dict[str, int] = Field(default={}, description="Document access frequency")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class BulkDeleteRequest(BaseModel):
    """Request schema for bulk document deletion."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    document_ids: List[str] = Field(..., min_items=1, max_items=100, description="Document UUIDs to delete")
    reason: str = Field(..., min_length=3, max_length=500, description="Business justification for deletion")
    hard_delete: bool = Field(False, description="Whether to perform hard deletion (admin only)")
    
    @field_validator('document_ids')
    @classmethod
    def validate_document_ids(cls, v):
        """Validate all document IDs are valid UUIDs."""
        for doc_id in v:
            try:
                UUID(doc_id)
            except ValueError:
                raise ValueError(f'Invalid document ID: {doc_id}')
        # Remove duplicates
        return list(set(v))
    
    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v):
        """Validate deletion reason is meaningful."""
        if len(v.strip()) < 3:
            raise ValueError('Deletion reason must be at least 3 characters')
        return v.strip()


class BulkUpdateTagsRequest(BaseModel):
    """Request schema for bulk tag updates."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    document_ids: List[str] = Field(..., min_items=1, max_items=100, description="Document UUIDs to update")
    tags: List[str] = Field(..., min_items=1, max_items=20, description="Tags to apply")
    action: str = Field(default="replace", description="Action: add, remove, or replace")
    
    @field_validator('document_ids')
    @classmethod
    def validate_document_ids(cls, v):
        """Validate all document IDs are valid UUIDs."""
        for doc_id in v:
            try:
                UUID(doc_id)
            except ValueError:
                raise ValueError(f'Invalid document ID: {doc_id}')
        return list(set(v))
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate and clean tags."""
        cleaned_tags = []
        for tag in v:
            tag = tag.strip()
            if tag and len(tag) <= 50:  # Max tag length
                cleaned_tags.append(tag)
        if not cleaned_tags:
            raise ValueError('At least one valid tag is required')
        return list(set(cleaned_tags))  # Remove duplicates
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Validate action type."""
        allowed_actions = ['add', 'remove', 'replace']
        if v not in allowed_actions:
            raise ValueError(f'Action must be one of: {", ".join(allowed_actions)}')
        return v


class BulkOperationResponse(BaseModel):
    """Response schema for bulk operations."""
    
    success_count: int = Field(..., description="Number of successful operations")
    failed_count: int = Field(..., description="Number of failed operations")
    total_count: int = Field(..., description="Total number of operations attempted")
    failed_documents: List[Dict[str, str]] = Field(
        default=[], 
        description="Details of failed operations"
    )
    operation_id: str = Field(..., description="Unique operation identifier")
    completed_at: datetime = Field(..., description="Operation completion timestamp")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class DocumentAccessLogEntry(BaseModel):
    """Schema for document access log entry (for compliance)."""
    
    access_id: str = Field(..., description="Access log UUID")
    document_id: str = Field(..., description="Accessed document UUID")
    user_id: str = Field(..., description="User who accessed the document")
    access_type: str = Field(..., description="Type of access (view, download, etc.)")
    ip_address: Optional[str] = Field(None, description="User IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    purpose: str = Field(..., description="Business purpose for access")
    phi_accessed: bool = Field(..., description="Whether PHI was accessed")
    consent_verified: bool = Field(..., description="Whether patient consent was verified")
    accessed_at: datetime = Field(..., description="Access timestamp")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )