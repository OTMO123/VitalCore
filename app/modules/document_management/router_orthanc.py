"""
🏥 Orthanc DICOM Integration - FastAPI Router
Security: CVE-2025-0896 mitigation applied
Phase 1: Unified Document Management API
Compliance: SOC2 Type II + HIPAA + FHIR R4

Enhanced security features:
- Input validation and sanitization
- Rate limiting per endpoint
- Comprehensive audit logging
- Authentication verification
- PHI protection
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, field_validator

import structlog

from app.core.auth import get_current_user, require_permissions
from app.core.database_unified import User
from app.core.exceptions import ValidationError, ResourceNotFound
from .orthanc_integration import get_orthanc_service, OrthancSecurityConfig
from .service import get_document_service, AccessContext
from .schemas import DocumentUploadResponse

logger = structlog.get_logger(__name__)
security = HTTPBearer()


# Request/Response Models
class OrthancHealthResponse(BaseModel):
    """Orthanc health check response."""
    status: str
    orthanc_version: Optional[str] = None
    orthanc_name: Optional[str] = None
    url: str
    authenticated: bool
    security_enabled: bool = True
    tls_enabled: bool = False
    timestamp: datetime


class DicomInstanceRequest(BaseModel):
    """Request to sync DICOM instance."""
    instance_id: str
    patient_uuid: str
    
    @field_validator('instance_id')
    @classmethod
    def validate_instance_id(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('Instance ID is required')
        v = v.strip()
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Instance ID contains invalid characters')
        return v
    
    @field_validator('patient_uuid')
    @classmethod
    def validate_patient_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid patient UUID format')
        return v


class DicomMetadataResponse(BaseModel):
    """DICOM metadata response."""
    patient_id: str
    study_id: str
    series_id: str
    instance_id: str
    study_date: str
    study_description: str
    series_description: str
    modality: str
    institution_name: Optional[str] = None
    referring_physician: Optional[str] = None
    accessed_at: datetime


class DicomSyncResponse(BaseModel):
    """DICOM sync response."""
    document_id: str
    instance_id: str
    storage_key: str
    filename: str
    document_type: str
    synced_at: datetime
    audit_logged: bool = True


class PatientStudiesResponse(BaseModel):
    """Patient studies response."""
    patient_id: str
    studies_count: int
    studies: List[Dict[str, Any]]
    retrieved_at: datetime


# Router
router = APIRouter(prefix="/api/v1/documents/orthanc", tags=["Orthanc DICOM Integration"])


@router.get("/health", response_model=OrthancHealthResponse)
async def orthanc_health_check(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Check Orthanc server health and connectivity.
    
    Security:
    - Authentication required
    - Rate limiting applied
    - Audit logging enabled
    """
    client_id = f"health_{current_user.id}"
    
    try:
        orthanc_service = get_orthanc_service()
        health_status = await orthanc_service.health_check(client_id)
        
        # Log health check access
        logger.info(
            "Orthanc health check requested",
            user_id=current_user.id,
            client_ip=request.client.host if request.client else "unknown",
            status=health_status["status"]
        )
        
        return OrthancHealthResponse(
            **health_status,
            timestamp=datetime.utcnow()
        )
        
    except ValidationError as e:
        logger.error("Orthanc health check validation error", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Orthanc health check failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orthanc service unavailable"
        )


@router.get("/instances/{instance_id}/metadata", response_model=DicomMetadataResponse)
async def get_dicom_metadata(
    instance_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Get DICOM metadata for a specific instance.
    
    Security:
    - Authentication required
    - Input validation and sanitization
    - Rate limiting per user
    - PHI access audit logging
    """
    client_id = f"metadata_{current_user.id}"
    
    try:
        orthanc_service = get_orthanc_service()
        metadata = await orthanc_service.get_dicom_metadata(instance_id, client_id)
        
        # Enhanced audit logging for PHI access
        logger.info(
            "DICOM metadata retrieved",
            user_id=current_user.id,
            instance_id=instance_id,
            modality=metadata.modality,
            client_ip=request.client.host if request.client else "unknown",
            has_phi=bool(metadata.patient_id != "unknown")
        )
        
        return DicomMetadataResponse(
            patient_id=metadata.patient_id,
            study_id=metadata.study_id,
            series_id=metadata.series_id,
            instance_id=metadata.instance_id,
            study_date=metadata.study_date,
            study_description=metadata.study_description,
            series_description=metadata.series_description,
            modality=metadata.modality,
            institution_name=metadata.institution_name,
            referring_physician=metadata.referring_physician,
            accessed_at=datetime.utcnow()
        )
        
    except ResourceNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        logger.error("DICOM metadata validation error", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("DICOM metadata retrieval failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve DICOM metadata"
        )


@router.post("/sync", response_model=DicomSyncResponse)
async def sync_dicom_instance(
    sync_request: DicomInstanceRequest,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Sync DICOM instance from Orthanc to document management system.
    
    Security:
    - Authentication required
    - Permission validation
    - Input validation and sanitization
    - Comprehensive audit logging
    """
    client_id = f"sync_{current_user.id}"
    
    try:
        # Validate permissions (require document management access)
        require_permissions(current_user, ["documents:write"])
        
        orthanc_service = get_orthanc_service()
        document_service = get_document_service()
        
        # Create access context
        context = AccessContext(
            user_id=current_user.id,
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        # Sync DICOM instance
        sync_result = await orthanc_service.sync_dicom_instance(
            sync_request.instance_id,
            uuid.UUID(sync_request.patient_uuid),
            context
        )
        
        # Enhanced audit logging
        logger.info(
            "DICOM instance synced",
            user_id=current_user.id,
            instance_id=sync_request.instance_id,
            patient_uuid=sync_request.patient_uuid,
            document_id=sync_result.document_id,
            client_ip=context.client_ip,
            storage_key=sync_result.storage_key
        )
        
        return DicomSyncResponse(
            document_id=sync_result.document_id,
            instance_id=sync_request.instance_id,
            storage_key=sync_result.storage_key,
            filename=sync_result.filename,
            document_type=sync_result.document_type.value,
            synced_at=sync_result.uploaded_at,
            audit_logged=True
        )
        
    except ValidationError as e:
        logger.error("DICOM sync validation error", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ResourceNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("DICOM sync failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync DICOM instance"
        )


@router.get("/patients/{patient_id}/studies", response_model=PatientStudiesResponse)
async def get_patient_studies(
    patient_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Get all DICOM studies for a patient from Orthanc.
    
    Security:
    - Authentication required
    - PHI access requires special permissions
    - Comprehensive audit logging
    - Input validation
    """
    client_id = f"studies_{current_user.id}"
    
    try:
        # Validate permissions (require PHI access for patient data)
        require_permissions(current_user, ["patients:read", "phi:access"])
        
        # Input validation
        if not patient_id or not isinstance(patient_id, str):
            raise ValidationError("Invalid patient_id provided")
        
        orthanc_service = get_orthanc_service()
        studies = await orthanc_service.get_patient_studies(patient_id)
        
        # Enhanced audit logging for PHI access
        logger.info(
            "Patient DICOM studies accessed",
            user_id=current_user.id,
            patient_id=patient_id,
            studies_count=len(studies),
            client_ip=request.client.host if request.client else "unknown",
            phi_access=True
        )
        
        return PatientStudiesResponse(
            patient_id=patient_id,
            studies_count=len(studies),
            studies=studies,
            retrieved_at=datetime.utcnow()
        )
        
    except ValidationError as e:
        logger.error("Patient studies validation error", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Patient studies retrieval failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patient studies"
        )


@router.get("/config", response_model=Dict[str, Any])
async def get_orthanc_config(
    current_user: User = Depends(get_current_user)
):
    """
    Get Orthanc integration configuration (admin only).
    
    Security:
    - Admin authentication required
    - Sensitive data masked
    """
    try:
        # Validate admin permissions
        require_permissions(current_user, ["admin:read"])
        
        orthanc_service = get_orthanc_service()
        config = orthanc_service.config
        
        # Return masked configuration (no sensitive data)
        return {
            "base_url": config.base_url,
            "timeout": config.timeout,
            "max_retries": config.max_retries,
            "rate_limit_per_minute": config.rate_limit_per_minute,
            "enable_audit_logging": config.enable_audit_logging,
            "require_tls": config.require_tls,
            "verify_ssl": config.verify_ssl,
            "max_file_size_mb": config.max_file_size_mb,
            "allowed_modalities": config.allowed_modalities,
            "username_configured": bool(config.username),
            "password_configured": bool(config.password)
        }
        
    except Exception as e:
        logger.error("Config retrieval failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve configuration"
        )