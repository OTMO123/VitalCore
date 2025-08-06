"""
Document Management API Router - Minimal Version for Phase 1
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
import uuid
import structlog

from app.core.database_unified import get_db
from app.core.security import get_current_user_id

# Service imports for real implementation
from .service import DocumentStorageService, get_document_service, AccessContext
from .secure_storage import SecureStorageService, get_secure_storage_service
from .storage_backend import get_storage_backend
from .schemas import (
    DocumentUploadRequest, DocumentUploadResponse, DocumentDownloadResponse,
    DocumentMetadataResponse, DocumentListResponse, DocumentSearchRequest
)

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check for document management services."""
    try:
        return {
            "status": "healthy",
            "service": "document_management",
            "timestamp": datetime.utcnow().isoformat(),
            "endpoints": {
                "upload": "available",
                "health": "available"
            },
            "note": "Document management service operational - Phase 1 fixes applied",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error("Document health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    patient_id: str = Form(...),
    document_type: str = Form("general"),
    document_category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user_id = Depends(get_current_user_id),
    secure_storage: SecureStorageService = Depends(get_secure_storage_service)
):
    """
    Upload document with secure storage and encryption.
    Real implementation using SecureStorageService.
    """
    try:
        logger.info(
            "Document upload request",
            filename=file.filename,
            patient_id=patient_id,
            user_id=str(current_user_id)
        )
        
        # Validate required fields
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        if not patient_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient ID is required"
            )
        
        # Read file content
        try:
            file_content = await file.read()
            file_size = len(file_content)
        except Exception as e:
            logger.error("Failed to read uploaded file", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to read uploaded file"
            )
        
        # File validation
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        if file_size > 100 * 1024 * 1024:  # 100MB limit
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 100MB limit"
            )
        
        # Create access context
        context = AccessContext(
            user_id=str(current_user_id),
            purpose="document_upload"
        )
        
        # Parse tags if provided
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Store document securely
        storage_result = await secure_storage.secure_store(
            file_data=file_content,
            filename=file.filename,
            patient_id=patient_id,
            document_type=document_type,
            context=context,
            metadata={
                "document_category": document_category,
                "tags": tag_list,
                "content_type": file.content_type,
                "upload_source": "api"
            }
        )
        
        logger.info(
            "Document uploaded successfully",
            storage_key=storage_result.storage_key,
            filename=file.filename,
            file_size=file_size,
            encrypted=storage_result.encrypted
        )
        
        # Return success response
        return {
            "id": str(uuid.uuid4()),  # This would be the document DB ID in real implementation
            "status": "uploaded",
            "filename": file.filename,
            "file_size": file_size,
            "patient_id": patient_id,
            "document_type": document_type,
            "storage_key": storage_result.storage_key,
            "storage_bucket": storage_result.bucket,
            "hash_sha256": storage_result.hash_sha256,
            "encrypted": storage_result.encrypted,
            "encryption_algorithm": storage_result.encryption_algorithm,
            "upload_time": datetime.utcnow().isoformat(),
            "user_id": str(current_user_id),
            "message": "Document uploaded and encrypted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Document upload failed", 
            error=str(e), 
            filename=file.filename if file else None,
            patient_id=patient_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload failed: {str(e)}"
        )


@router.get("/download/{storage_key}")
async def download_document(
    storage_key: str,
    bucket: str = "documents",
    current_user_id = Depends(get_current_user_id),
    secure_storage: SecureStorageService = Depends(get_secure_storage_service)
):
    """
    Download document from secure storage with decryption.
    Real implementation using SecureStorageService.
    """
    try:
        logger.info(
            "Document download request",
            storage_key=storage_key,
            bucket=bucket,
            user_id=str(current_user_id)
        )
        
        # Create access context
        context = AccessContext(
            user_id=str(current_user_id),
            purpose="document_download"
        )
        
        # Retrieve document securely
        file_data, metadata = await secure_storage.secure_retrieve(
            storage_key=storage_key,
            bucket=bucket,
            context=context,
            purpose="api_download"
        )
        
        # Prepare response headers
        filename = metadata.get("original-filename", "document")
        content_type = metadata.get("content_type", "application/octet-stream")
        
        logger.info(
            "Document downloaded successfully",
            storage_key=storage_key,
            filename=filename,
            file_size=len(file_data)
        )
        
        # Return file data with proper headers
        return Response(
            content=file_data,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename=\"{filename}\"",
                "Content-Length": str(len(file_data)),
                "X-Storage-Key": storage_key,
                "X-Encrypted": metadata.get("encrypted", "true"),
                "X-Hash-SHA256": metadata.get("original-hash", "unknown")
            }
        )
        
    except Exception as e:
        logger.error(
            "Document download failed",
            error=str(e),
            storage_key=storage_key,
            user_id=str(current_user_id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document download failed: {str(e)}"
        )