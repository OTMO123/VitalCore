"""
🏥 Enhanced DICOM Router - Full Integration
Complete DICOM management API with database persistence and RBAC
Integrates all components: Orthanc + Database + Permissions + Audit
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, validator

import structlog

from app.core.database_unified import get_db
from app.core.auth import get_current_user
from app.modules.auth.schemas import UserResponse  # Assuming this exists
from app.modules.document_management.dicom_service_enhanced import (
    EnhancedDicomService, get_enhanced_dicom_service,
    DicomDocumentRequest, DicomSyncResult
)
from app.modules.document_management.rbac_dicom import (
    DicomRole, DicomPermission, get_dicom_rbac_manager
)
from app.modules.document_management.schemas import DocumentMetadataResponse
from app.modules.document_management.service import AccessContext

logger = structlog.get_logger(__name__)
security = HTTPBearer()


# Enhanced Request/Response Models
class DicomSyncRequest(BaseModel):
    """Request to sync DICOM instance with full validation."""
    instance_id: str
    patient_uuid: str
    
    @validator('instance_id')
    def validate_instance_id(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('Instance ID is required')
        v = v.strip()
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Instance ID contains invalid characters')
        return v
    
    @validator('patient_uuid')
    def validate_patient_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid patient UUID format')
        return v


class DicomSearchRequest(BaseModel):
    """Request for DICOM document search."""
    patient_id: Optional[str] = None
    modality: Optional[str] = None
    study_date_from: Optional[datetime] = None
    study_date_to: Optional[datetime] = None
    study_description: Optional[str] = None
    limit: int = 50
    offset: int = 0
    
    @validator('limit')
    def validate_limit(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Limit must be between 1 and 100')
        return v


class DicomSyncResponse(BaseModel):
    """Enhanced DICOM sync response."""
    document_id: str
    storage_key: str
    orthanc_instance_id: str
    patient_id: str
    study_id: Optional[str]
    series_id: Optional[str]
    metadata: Dict[str, Any]
    file_size: int
    created_at: datetime
    audit_logged: bool
    permissions_verified: bool
    compliance_tags: List[str]


class DicomSearchResponse(BaseModel):
    """DICOM search results."""
    documents: List[DocumentMetadataResponse]
    total_count: int
    page: int
    per_page: int
    has_more: bool
    search_permissions: List[str]


class PatientStudiesResponse(BaseModel):
    """Patient DICOM studies response."""
    patient_id: str
    studies: List[Dict[str, Any]]
    studies_count: int
    total_instances: int
    phi_access_granted: bool
    retrieved_at: datetime


class DicomMetadataUpdateRequest(BaseModel):
    """Request to update DICOM metadata."""
    metadata_updates: Dict[str, Any]
    update_reason: Optional[str] = None
    
    @validator('metadata_updates')
    def validate_metadata_updates(cls, v):
        if not v or not isinstance(v, dict):
            raise ValueError('Metadata updates must be a non-empty dictionary')
        return v


class DicomPermissionsResponse(BaseModel):
    """User's DICOM permissions response."""
    user_id: str
    user_role: str
    dicom_role: Optional[str]
    permissions: List[str]
    restrictions: List[str]
    can_access_phi: bool
    can_cross_patient_view: bool


# Router
router = APIRouter(prefix="/api/v1/dicom", tags=["Enhanced DICOM Management"])


@router.post("/sync", response_model=DicomSyncResponse)
async def sync_dicom_instance(
    sync_request: DicomSyncRequest,
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    dicom_service: EnhancedDicomService = Depends(get_enhanced_dicom_service)
):
    """
    Sync DICOM instance from Orthanc to database.
    
    Full workflow:
    1. Validates user permissions
    2. Retrieves DICOM metadata from Orthanc
    3. Creates document record in database
    4. Logs all operations for compliance
    """
    
    try:
        # Create access context
        context = AccessContext(
            user_id=current_user.id,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        # Sync the DICOM instance
        result = await dicom_service.sync_dicom_instance_to_database(
            instance_id=sync_request.instance_id,
            patient_uuid=sync_request.patient_uuid,
            user_id=str(current_user.id),
            user_role=current_user.role,
            db=db,
            context=context
        )
        
        logger.info(
            "DICOM instance synced successfully",
            user_id=current_user.id,
            instance_id=sync_request.instance_id,
            document_id=result.document_id,
            patient_id=sync_request.patient_uuid
        )
        
        return DicomSyncResponse(
            document_id=result.document_id,
            storage_key=result.storage_key,
            orthanc_instance_id=result.orthanc_instance_id,
            patient_id=result.patient_id,
            study_id=result.study_id,
            series_id=result.series_id,
            metadata=result.metadata,
            file_size=result.file_size,
            created_at=result.created_at,
            audit_logged=result.audit_logged,
            permissions_verified=True,
            compliance_tags=["HIPAA", "SOC2", "DICOM_SYNC", "PHI_ACCESS"]
        )
        
    except Exception as e:
        logger.error(
            "DICOM sync failed",
            user_id=current_user.id,
            instance_id=sync_request.instance_id,
            error=str(e)
        )
        
        if "permission" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        elif "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to sync DICOM instance"
            )


@router.get("/search", response_model=DicomSearchResponse)
async def search_dicom_documents(
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    modality: Optional[str] = Query(None, description="Filter by modality (CT, MR, XR, etc.)"),
    study_description: Optional[str] = Query(None, description="Filter by study description"),
    limit: int = Query(50, ge=1, le=100, description="Number of results per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    dicom_service: EnhancedDicomService = Depends(get_enhanced_dicom_service)
):
    """
    Search DICOM documents with role-based filtering.
    
    Features:
    - Role-based access control
    - Cross-patient view restrictions
    - Comprehensive audit logging
    - PHI protection
    """
    
    try:
        # Perform search
        documents, total_count = await dicom_service.search_dicom_documents(
            user_id=str(current_user.id),
            user_role=current_user.role,
            db=db,
            patient_id=patient_id,
            modality=modality,
            study_description=study_description,
            limit=limit,
            offset=offset
        )
        
        # Get user permissions for response
        rbac_manager = get_dicom_rbac_manager()
        permissions = rbac_manager.get_user_permissions(current_user.role)
        
        return DicomSearchResponse(
            documents=documents,
            total_count=total_count,
            page=offset // limit + 1,
            per_page=limit,
            has_more=(offset + limit) < total_count,
            search_permissions=[perm.value for perm in permissions]
        )
        
    except Exception as e:
        logger.error(
            "DICOM search failed",
            user_id=current_user.id,
            error=str(e)
        )
        
        if "permission" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search DICOM documents"
            )


@router.get("/documents/{document_id}", response_model=DocumentMetadataResponse)
async def get_dicom_document_metadata(
    document_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    dicom_service: EnhancedDicomService = Depends(get_enhanced_dicom_service)
):
    """
    Get DICOM document metadata with permission checking.
    
    Includes comprehensive audit logging and PHI protection.
    """
    
    try:
        metadata = await dicom_service.get_dicom_document_metadata(
            document_id=document_id,
            user_id=str(current_user.id),
            user_role=current_user.role,
            db=db
        )
        
        return metadata
        
    except Exception as e:
        logger.error(
            "Failed to get DICOM document metadata",
            user_id=current_user.id,
            document_id=document_id,
            error=str(e)
        )
        
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "permission" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve document metadata"
            )


@router.put("/documents/{document_id}/metadata", response_model=DocumentMetadataResponse)
async def update_dicom_metadata(
    document_id: str,
    update_request: DicomMetadataUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    dicom_service: EnhancedDicomService = Depends(get_enhanced_dicom_service)
):
    """
    Update DICOM document metadata with permission checking.
    
    Requires METADATA_WRITE permission.
    """
    
    try:
        updated_metadata = await dicom_service.update_dicom_metadata(
            document_id=document_id,
            metadata_updates=update_request.metadata_updates,
            user_id=str(current_user.id),
            user_role=current_user.role,
            db=db
        )
        
        return updated_metadata
        
    except Exception as e:
        logger.error(
            "Failed to update DICOM metadata",
            user_id=current_user.id,
            document_id=document_id,
            error=str(e)
        )
        
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "permission" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update metadata"
            )


@router.delete("/documents/{document_id}")
async def delete_dicom_document(
    document_id: str,
    hard_delete: bool = Query(False, description="Perform hard delete (permanent removal)"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    dicom_service: EnhancedDicomService = Depends(get_enhanced_dicom_service)
):
    """
    Delete DICOM document with permission checking.
    
    Requires DICOM_DELETE permission.
    Default is soft delete (marked as deleted).
    """
    
    try:
        success = await dicom_service.delete_dicom_document(
            document_id=document_id,
            user_id=str(current_user.id),
            user_role=current_user.role,
            db=db,
            hard_delete=hard_delete
        )
        
        return {
            "success": success,
            "document_id": document_id,
            "deletion_type": "hard" if hard_delete else "soft",
            "deleted_by": str(current_user.id),
            "deleted_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(
            "Failed to delete DICOM document",
            user_id=current_user.id,
            document_id=document_id,
            error=str(e)
        )
        
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "permission" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document"
            )


@router.get("/patients/{patient_id}/studies", response_model=PatientStudiesResponse)
async def get_patient_dicom_studies(
    patient_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    dicom_service: EnhancedDicomService = Depends(get_enhanced_dicom_service)
):
    """
    Get all DICOM studies for a patient.
    
    Requires PHI_DICOM_ACCESS permission.
    Comprehensive audit logging for patient data access.
    """
    
    try:
        studies = await dicom_service.get_patient_dicom_studies(
            patient_id=patient_id,
            user_id=str(current_user.id),
            user_role=current_user.role,
            db=db
        )
        
        # Calculate totals
        total_instances = sum(study.get("instance_count", 0) for study in studies)
        
        return PatientStudiesResponse(
            patient_id=patient_id,
            studies=studies,
            studies_count=len(studies),
            total_instances=total_instances,
            phi_access_granted=True,
            retrieved_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(
            "Failed to get patient DICOM studies",
            user_id=current_user.id,
            patient_id=patient_id,
            error=str(e)
        )
        
        if "permission" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve patient studies"
            )


@router.get("/permissions", response_model=DicomPermissionsResponse)
async def get_user_dicom_permissions(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get current user's DICOM permissions and capabilities.
    
    Useful for frontend UI to show/hide features based on permissions.
    """
    
    try:
        rbac_manager = get_dicom_rbac_manager()
        
        # Get user permissions
        permissions = rbac_manager.get_user_permissions(current_user.role)
        
        # Map to DICOM role if possible
        from app.modules.document_management.rbac_dicom import map_user_role_to_dicom_role
        dicom_role = map_user_role_to_dicom_role(current_user.role)
        
        # Check specific capabilities
        from app.modules.document_management.rbac_dicom import DicomAccessContext
        context = DicomAccessContext(
            user_id=str(current_user.id),
            user_role=current_user.role
        )
        
        can_access_phi = rbac_manager.has_permission(
            current_user.role, DicomPermission.PHI_DICOM_ACCESS, context
        )
        
        can_cross_patient_view = rbac_manager.has_permission(
            current_user.role, DicomPermission.CROSS_PATIENT_VIEW, context
        )
        
        # Determine restrictions
        restrictions = []
        if not can_access_phi:
            restrictions.append("No PHI access")
        if not can_cross_patient_view:
            restrictions.append("Single patient view only")
        
        return DicomPermissionsResponse(
            user_id=str(current_user.id),
            user_role=current_user.role,
            dicom_role=dicom_role.value if dicom_role else None,
            permissions=[perm.value for perm in permissions],
            restrictions=restrictions,
            can_access_phi=can_access_phi,
            can_cross_patient_view=can_cross_patient_view
        )
        
    except Exception as e:
        logger.error(
            "Failed to get user DICOM permissions",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user permissions"
        )


@router.get("/statistics")
async def get_dicom_statistics(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get DICOM system statistics for authorized users.
    
    Requires ORTHANC_STATS permission.
    """
    
    try:
        # Check permissions
        rbac_manager = get_dicom_rbac_manager()
        context = DicomAccessContext(
            user_id=str(current_user.id),
            user_role=current_user.role
        )
        
        if not rbac_manager.has_permission(
            current_user.role, DicomPermission.ORTHANC_STATS, context
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for DICOM statistics"
            )
        
        # Get statistics from database
        from sqlalchemy import select, func
        from app.core.database_unified import DocumentStorage, DocumentType
        
        # Count DICOM documents
        dicom_query = select(func.count()).select_from(DocumentStorage).where(
            DocumentStorage.document_type.in_([
                DocumentType.DICOM_IMAGE,
                DocumentType.DICOM_SERIES,
                DocumentType.DICOM_STUDY
            ])
        )
        
        total_dicom_docs = await db.scalar(dicom_query)
        
        # Count by modality
        modality_query = select(
            DocumentStorage.dicom_metadata.op('->>')('modality').label('modality'),
            func.count().label('count')
        ).where(
            DocumentStorage.document_type.in_([
                DocumentType.DICOM_IMAGE,
                DocumentType.DICOM_SERIES,
                DocumentType.DICOM_STUDY
            ])
        ).group_by(
            DocumentStorage.dicom_metadata.op('->>')('modality')
        )
        
        modality_result = await db.execute(modality_query)
        modality_stats = {row.modality: row.count for row in modality_result}
        
        # Get unique patient count
        patient_query = select(func.count(func.distinct(DocumentStorage.patient_id))).select_from(
            DocumentStorage
        ).where(
            DocumentStorage.document_type.in_([
                DocumentType.DICOM_IMAGE,
                DocumentType.DICOM_SERIES,
                DocumentType.DICOM_STUDY
            ])
        )
        
        unique_patients = await db.scalar(patient_query)
        
        return {
            "total_dicom_documents": total_dicom_docs or 0,
            "unique_patients": unique_patients or 0,
            "modality_breakdown": modality_stats,
            "generated_at": datetime.utcnow().isoformat(),
            "user_permissions": [perm.value for perm in rbac_manager.get_user_permissions(current_user.role)]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get DICOM statistics",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )