"""
Document Management Module

Secure document storage, processing, and retrieval with SOC2/HIPAA compliance.
"""

from .service import DocumentStorageService
from .storage_backend import MinIOStorageBackend, StorageBackendInterface
from .schemas import (
    DocumentUploadRequest, DocumentUploadResponse, 
    DocumentDownloadResponse, DocumentListResponse
)

__all__ = [
    "DocumentStorageService",
    "MinIOStorageBackend", 
    "StorageBackendInterface",
    "DocumentUploadRequest",
    "DocumentUploadResponse", 
    "DocumentDownloadResponse",
    "DocumentListResponse"
]