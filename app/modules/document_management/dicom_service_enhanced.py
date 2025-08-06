"""
🏥 Enhanced DICOM Service with Full Database Integration
Real database operations for DICOM document management
Integrates with existing DocumentStorage system + Orthanc integration

Features:
- Full CRUD operations for DICOM documents
- Role-based access control
- Real database persistence
- Comprehensive audit logging
- Document versioning and metadata management
"""

import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload

from app.core.database_unified import (
    DocumentStorage, DocumentAccessAudit, DocumentShare, 
    DocumentType, AuditEventType, DataClassification
)
from app.modules.document_management.service import DocumentStorageService, AccessContext
from app.modules.document_management.orthanc_integration import (
    OrthancIntegrationService, DicomMetadata, get_orthanc_service
)
from app.modules.document_management.rbac_dicom import (
    DicomRBACManager, DicomAccessContext, DicomPermission, 
    get_dicom_rbac_manager, map_user_role_to_dicom_role
)
from app.modules.document_management.schemas import (
    DocumentUploadRequest, DocumentUploadResponse, 
    DocumentMetadataResponse, DocumentListResponse
)
from app.core.exceptions import ValidationError, ResourceNotFound, PermissionDeniedError

logger = structlog.get_logger(__name__)


@dataclass
class DicomDocumentRequest:
    """Enhanced request for DICOM document operations."""
    patient_id: str
    study_id: Optional[str] = None
    series_id: Optional[str] = None
    instance_id: Optional[str] = None
    modality: Optional[str] = None
    study_description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


@dataclass
class DicomSyncResult:
    """Result of DICOM synchronization operation."""
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


class EnhancedDicomService:
    """
    Enhanced DICOM service with full database integration.
    
    Combines Orthanc integration with comprehensive document management,
    including role-based access control, audit logging, and database persistence.
    """
    
    def __init__(
        self,
        document_service: DocumentStorageService,
        orthanc_service: Optional[OrthancIntegrationService] = None,
        rbac_manager: Optional[DicomRBACManager] = None
    ):
        self.document_service = document_service
        self.orthanc_service = orthanc_service or get_orthanc_service()
        self.rbac_manager = rbac_manager or get_dicom_rbac_manager()
        self.logger = logger.bind(service="EnhancedDicomService")
    
    async def sync_dicom_instance_to_database(
        self,
        instance_id: str,
        patient_uuid: str,
        user_id: str,
        user_role: str,
        db: AsyncSession,
        context: Optional[AccessContext] = None
    ) -> DicomSyncResult:
        """
        Sync DICOM instance from Orthanc to database with full audit trail.
        
        This method:
        1. Validates user permissions
        2. Retrieves DICOM metadata from Orthanc
        3. Creates document record in database
        4. Logs all operations for compliance
        """
        
        # Create DICOM access context
        dicom_context = DicomAccessContext(
            user_id=user_id,
            user_role=user_role,
            patient_id=patient_uuid,
            client_ip=context.client_ip if context else None,
            user_agent=context.user_agent if context else None
        )
        
        # Check permissions
        if not self.rbac_manager.has_permission(
            user_role, DicomPermission.DICOM_VIEW, dicom_context
        ):
            self.rbac_manager.audit_access_attempt(
                dicom_context, DicomPermission.DICOM_VIEW, False, "Insufficient permissions"
            )
            raise PermissionDeniedError("Insufficient permissions to sync DICOM instance")
        
        try:
            # Get DICOM metadata from Orthanc
            self.logger.info("Retrieving DICOM metadata", instance_id=instance_id)
            dicom_metadata = await self.orthanc_service.get_dicom_metadata(
                instance_id, f"sync_{user_id}"
            )
            
            # Create document upload request
            filename = f"{dicom_metadata.series_description}_{instance_id}.dcm"
            
            # Enhanced metadata combining DICOM and system metadata
            enhanced_metadata = {
                "dicom": {
                    "patient_id": dicom_metadata.patient_id,
                    "study_id": dicom_metadata.study_id,
                    "series_id": dicom_metadata.series_id,
                    "instance_id": dicom_metadata.instance_id,
                    "study_date": dicom_metadata.study_date,
                    "study_description": dicom_metadata.study_description,
                    "series_description": dicom_metadata.series_description,
                    "modality": dicom_metadata.modality,
                    "institution_name": dicom_metadata.institution_name,
                    "referring_physician": dicom_metadata.referring_physician
                },
                "sync": {
                    "synced_at": datetime.utcnow().isoformat(),
                    "synced_by": user_id,
                    "orthanc_server": self.orthanc_service.config.base_url,
                    "sync_version": "1.0"
                },
                "compliance": {
                    "data_classification": DataClassification.PHI.value,
                    "phi_present": True,
                    "retention_required": True
                }
            }
            
            # Generate tags
            tags = [
                "dicom", "orthanc", dicom_metadata.modality.lower(),
                f"study_{dicom_metadata.study_id}",
                f"series_{dicom_metadata.series_id}"
            ]
            
            if dicom_metadata.institution_name:
                tags.append(f"institution_{dicom_metadata.institution_name.lower().replace(' ', '_')}")
            
            # Create document storage record
            document = DocumentStorage(
                id=uuid.uuid4(),
                patient_id=uuid.UUID(patient_uuid),
                original_filename=filename,
                storage_path=f"orthanc://{instance_id}",  # Special Orthanc reference
                storage_bucket="orthanc-dicom",
                file_size_bytes=0,  # Will be updated when actual file is accessed
                mime_type="application/dicom",
                hash_sha256="",  # Will be updated when file is accessed
                document_type=DocumentType.DICOM_IMAGE,
                document_category="radiology",
                extracted_text=None,  # DICOM images don't have extractable text
                document_metadata=enhanced_metadata,
                tags=tags,
                version=1,
                is_latest_version=True,
                uploaded_by=uuid.UUID(user_id),
                updated_by=uuid.UUID(user_id),
                # Orthanc-specific fields
                orthanc_instance_id=instance_id,
                orthanc_series_id=dicom_metadata.series_id,
                orthanc_study_id=dicom_metadata.study_id,
                dicom_metadata=dicom_metadata.__dict__,
                # Compliance fields
                is_phi=True,
                data_classification=DataClassification.PHI
            )
            
            # Save to database
            db.add(document)
            await db.commit()
            await db.refresh(document)
            
            self.logger.info(
                "DICOM document created in database",
                document_id=str(document.id),
                patient_id=patient_uuid,
                instance_id=instance_id
            )
            
            # Create audit log entry
            audit_entry = DocumentAccessAudit(
                id=uuid.uuid4(),
                document_id=document.id,
                user_id=uuid.UUID(user_id),
                action="SYNC_FROM_ORTHANC",
                ip_address=context.client_ip if context else None,
                user_agent=context.user_agent if context else None,
                request_details={
                    "orthanc_instance_id": instance_id,
                    "modality": dicom_metadata.modality,
                    "study_description": dicom_metadata.study_description,
                    "sync_operation": True
                },
                session_id=context.session_id if context else None,
                compliance_tags=["HIPAA", "SOC2", "DICOM", "PHI_ACCESS"],
                block_number=await self._get_next_block_number(db)
            )
            
            # Set blockchain-like hashing for audit trail integrity
            audit_entry.current_hash = self._calculate_audit_hash(audit_entry)
            
            db.add(audit_entry)
            await db.commit()
            
            # Log successful sync for RBAC auditing
            self.rbac_manager.audit_access_attempt(
                dicom_context, DicomPermission.DICOM_VIEW, True, "DICOM sync successful"
            )
            
            return DicomSyncResult(
                document_id=str(document.id),
                storage_key=document.storage_path,
                orthanc_instance_id=instance_id,
                patient_id=patient_uuid,
                study_id=dicom_metadata.study_id,
                series_id=dicom_metadata.series_id,
                metadata=enhanced_metadata,
                file_size=0,
                created_at=document.created_at,
                audit_logged=True
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to sync DICOM instance",
                instance_id=instance_id,
                patient_id=patient_uuid,
                error=str(e)
            )
            
            # Log failed attempt
            self.rbac_manager.audit_access_attempt(
                dicom_context, DicomPermission.DICOM_VIEW, False, f"Sync failed: {str(e)}"
            )
            
            await db.rollback()
            raise
    
    async def search_dicom_documents(
        self,
        user_id: str,
        user_role: str,
        db: AsyncSession,
        patient_id: Optional[str] = None,
        modality: Optional[str] = None,
        study_date_from: Optional[datetime] = None,
        study_date_to: Optional[datetime] = None,
        study_description: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[DocumentMetadataResponse], int]:
        """
        Search DICOM documents with role-based filtering.
        """
        
        # Create DICOM access context
        dicom_context = DicomAccessContext(
            user_id=user_id,
            user_role=user_role,
            patient_id=patient_id
        )
        
        # Check basic search permissions
        if not self.rbac_manager.has_permission(
            user_role, DicomPermission.PATIENT_SEARCH, dicom_context
        ):
            raise PermissionDeniedError("Insufficient permissions for DICOM search")
        
        # Build query
        query = select(DocumentStorage).where(
            DocumentStorage.document_type.in_([
                DocumentType.DICOM_IMAGE,
                DocumentType.DICOM_SERIES, 
                DocumentType.DICOM_STUDY
            ])
        )
        
        # Apply filters based on permissions and parameters
        if patient_id:
            query = query.where(DocumentStorage.patient_id == uuid.UUID(patient_id))
        elif not self.rbac_manager.has_permission(
            user_role, DicomPermission.CROSS_PATIENT_VIEW, dicom_context
        ):
            # If user can't see cross-patient data, return empty results
            # In real system, this would filter to user's assigned patients
            self.logger.warning(
                "User attempted cross-patient search without permissions",
                user_id=user_id,
                user_role=user_role
            )
            return [], 0
        
        # Apply additional filters
        if modality:
            query = query.where(
                DocumentStorage.dicom_metadata.op('->>')('modality') == modality
            )
        
        if study_date_from:
            query = query.where(DocumentStorage.created_at >= study_date_from)
        
        if study_date_to:
            query = query.where(DocumentStorage.created_at <= study_date_to)
        
        if study_description:
            query = query.where(
                DocumentStorage.document_metadata.op('->>')('dicom').op('->>')('study_description')
                .ilike(f"%{study_description}%")
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_count = await db.scalar(count_query)
        
        # Apply pagination and execute
        query = query.order_by(DocumentStorage.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        documents = result.scalars().all()
        
        # Convert to response format
        document_responses = []
        for doc in documents:
            # Check individual document access
            doc_context = DicomAccessContext(
                user_id=user_id,
                user_role=user_role,
                patient_id=str(doc.patient_id),
                study_id=doc.orthanc_study_id,
                modality=doc.dicom_metadata.get('modality') if doc.dicom_metadata else None
            )
            
            if self.rbac_manager.has_permission(
                user_role, DicomPermission.DICOM_VIEW, doc_context
            ):
                document_responses.append(
                    self._convert_to_metadata_response(doc, user_role)
                )
        
        # Log search for audit
        self.logger.info(
            "DICOM search performed",
            user_id=user_id,
            user_role=user_role,
            patient_id=patient_id,
            modality=modality,
            results_count=len(document_responses),
            total_available=total_count
        )
        
        return document_responses, len(document_responses)
    
    async def get_dicom_document_metadata(
        self,
        document_id: str,
        user_id: str,
        user_role: str,
        db: AsyncSession
    ) -> DocumentMetadataResponse:
        """
        Get DICOM document metadata with permission checking.
        """
        
        # Get document from database
        query = select(DocumentStorage).where(DocumentStorage.id == uuid.UUID(document_id))
        result = await db.execute(query)
        document = result.scalar_one_or_none()
        
        if not document:
            raise ResourceNotFound(f"Document {document_id} not found")
        
        # Check permissions
        dicom_context = DicomAccessContext(
            user_id=user_id,
            user_role=user_role,
            patient_id=str(document.patient_id),
            study_id=document.orthanc_study_id,
            modality=document.dicom_metadata.get('modality') if document.dicom_metadata else None
        )
        
        if not self.rbac_manager.has_permission(
            user_role, DicomPermission.METADATA_READ, dicom_context
        ):
            raise PermissionDeniedError("Insufficient permissions to view document metadata")
        
        # Log access for audit
        await self._log_document_access(document, user_id, "METADATA_VIEW", db)
        
        return self._convert_to_metadata_response(document, user_role)
    
    async def update_dicom_metadata(
        self,
        document_id: str,
        metadata_updates: Dict[str, Any],
        user_id: str,
        user_role: str,
        db: AsyncSession
    ) -> DocumentMetadataResponse:
        """
        Update DICOM document metadata with permission checking.
        """
        
        # Get document
        document = await self._get_document_with_permissions(
            document_id, user_id, user_role, DicomPermission.METADATA_WRITE, db
        )
        
        # Update metadata
        current_metadata = document.document_metadata or {}
        current_metadata.update(metadata_updates)
        current_metadata['last_updated'] = {
            'timestamp': datetime.utcnow().isoformat(),
            'updated_by': user_id,
            'update_type': 'metadata_update'
        }
        
        document.document_metadata = current_metadata
        document.updated_by = uuid.UUID(user_id)
        document.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(document)
        
        # Log update
        await self._log_document_access(document, user_id, "METADATA_UPDATE", db, {
            "updated_fields": list(metadata_updates.keys()),
            "update_timestamp": datetime.utcnow().isoformat()
        })
        
        self.logger.info(
            "DICOM metadata updated",
            document_id=document_id,
            user_id=user_id,
            updated_fields=list(metadata_updates.keys())
        )
        
        return self._convert_to_metadata_response(document, user_role)
    
    async def delete_dicom_document(
        self,
        document_id: str,
        user_id: str,
        user_role: str,
        db: AsyncSession,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete DICOM document with permission checking.
        """
        
        # Get document with delete permissions
        document = await self._get_document_with_permissions(
            document_id, user_id, user_role, DicomPermission.DICOM_DELETE, db
        )
        
        if hard_delete:
            # Complete removal from database
            await db.delete(document)
            self.logger.warning(
                "DICOM document hard deleted",
                document_id=document_id,
                user_id=user_id,
                patient_id=str(document.patient_id)
            )
        else:
            # Soft delete - mark as deleted
            document.deleted_at = datetime.utcnow()
            document.deleted_by = uuid.UUID(user_id)
            document.is_latest_version = False
            
        await db.commit()
        
        # Log deletion
        await self._log_document_access(document, user_id, "DELETE", db, {
            "deletion_type": "hard" if hard_delete else "soft",
            "deletion_timestamp": datetime.utcnow().isoformat()
        })
        
        return True
    
    async def get_patient_dicom_studies(
        self,
        patient_id: str,
        user_id: str,
        user_role: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Get all DICOM studies for a patient with role-based access control.
        """
        
        # Create access context
        dicom_context = DicomAccessContext(
            user_id=user_id,
            user_role=user_role,
            patient_id=patient_id
        )
        
        # Check PHI access permissions
        if not self.rbac_manager.has_permission(
            user_role, DicomPermission.PHI_DICOM_ACCESS, dicom_context
        ):
            raise PermissionDeniedError("Insufficient permissions for patient DICOM access")
        
        # Query patient's DICOM documents
        query = select(DocumentStorage).where(
            and_(
                DocumentStorage.patient_id == uuid.UUID(patient_id),
                DocumentStorage.document_type.in_([
                    DocumentType.DICOM_IMAGE,
                    DocumentType.DICOM_SERIES,
                    DocumentType.DICOM_STUDY
                ]),
                DocumentStorage.deleted_at.is_(None)
            )
        ).order_by(DocumentStorage.created_at.desc())
        
        result = await db.execute(query)
        documents = result.scalars().all()
        
        # Group by study
        studies = {}
        for doc in documents:
            study_id = doc.orthanc_study_id or "unknown"
            if study_id not in studies:
                studies[study_id] = {
                    "study_id": study_id,
                    "study_date": doc.dicom_metadata.get('study_date') if doc.dicom_metadata else None,
                    "study_description": doc.dicom_metadata.get('study_description') if doc.dicom_metadata else None,
                    "modality": doc.dicom_metadata.get('modality') if doc.dicom_metadata else None,
                    "series_count": 0,
                    "instance_count": 0,
                    "documents": []
                }
            
            studies[study_id]["instance_count"] += 1
            studies[study_id]["documents"].append({
                "document_id": str(doc.id),
                "filename": doc.original_filename,
                "series_id": doc.orthanc_series_id,
                "instance_id": doc.orthanc_instance_id,
                "created_at": doc.created_at.isoformat()
            })
        
        # Calculate series counts
        for study in studies.values():
            series_ids = set(doc["series_id"] for doc in study["documents"] if doc["series_id"])
            study["series_count"] = len(series_ids)
        
        # Log patient studies access
        self.logger.info(
            "Patient DICOM studies accessed",
            patient_id=patient_id,
            user_id=user_id,
            user_role=user_role,
            studies_count=len(studies),
            phi_access=True,
            compliance_tags=["HIPAA", "PHI_ACCESS"]
        )
        
        return list(studies.values())
    
    async def _get_document_with_permissions(
        self,
        document_id: str,
        user_id: str,
        user_role: str,
        required_permission: DicomPermission,
        db: AsyncSession
    ) -> DocumentStorage:
        """Get document with permission validation."""
        
        query = select(DocumentStorage).where(DocumentStorage.id == uuid.UUID(document_id))
        result = await db.execute(query)
        document = result.scalar_one_or_none()
        
        if not document:
            raise ResourceNotFound(f"Document {document_id} not found")
        
        # Check permissions
        dicom_context = DicomAccessContext(
            user_id=user_id,
            user_role=user_role,
            patient_id=str(document.patient_id),
            study_id=document.orthanc_study_id,
            modality=document.dicom_metadata.get('modality') if document.dicom_metadata else None
        )
        
        if not self.rbac_manager.has_permission(user_role, required_permission, dicom_context):
            raise PermissionDeniedError(f"Insufficient permissions: {required_permission.value}")
        
        return document
    
    def _convert_to_metadata_response(
        self, 
        document: DocumentStorage, 
        user_role: str
    ) -> DocumentMetadataResponse:
        """Convert document to metadata response with role-based filtering."""
        
        # Determine what metadata to include based on role
        dicom_role = map_user_role_to_dicom_role(user_role)
        
        # Basic metadata always included
        metadata = {
            "document_id": str(document.id),
            "patient_id": str(document.patient_id),
            "filename": document.original_filename,
            "document_type": document.document_type.value,
            "file_size": document.file_size_bytes,
            "created_at": document.created_at.isoformat(),
            "tags": document.tags or []
        }
        
        # Add DICOM-specific metadata
        if document.dicom_metadata:
            metadata["dicom"] = document.dicom_metadata
        
        # Add full metadata for authorized roles
        if self.rbac_manager.has_permission(
            user_role, DicomPermission.METADATA_READ,
            DicomAccessContext(user_id="", user_role=user_role)
        ):
            metadata["full_metadata"] = document.document_metadata
        
        # Remove PHI for unauthorized roles (students, researchers)
        if dicom_role in ["STUDENT", "RESEARCHER"]:
            # Remove identifiable information
            if "dicom" in metadata and metadata["dicom"]:
                metadata["dicom"].pop("patient_id", None)
                metadata["dicom"].pop("referring_physician", None)
            metadata.pop("patient_id", None)
        
        return DocumentMetadataResponse(**metadata)
    
    async def _log_document_access(
        self,
        document: DocumentStorage,
        user_id: str,
        action: str,
        db: AsyncSession,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log document access for audit trail."""
        
        audit_entry = DocumentAccessAudit(
            id=uuid.uuid4(),
            document_id=document.id,
            user_id=uuid.UUID(user_id),
            action=action,
            request_details=details or {},
            block_number=await self._get_next_block_number(db),
            compliance_tags=["HIPAA", "SOC2", "DICOM"]
        )
        
        audit_entry.current_hash = self._calculate_audit_hash(audit_entry)
        db.add(audit_entry)
    
    async def _get_next_block_number(self, db: AsyncSession) -> int:
        """Get next block number for audit chain."""
        result = await db.execute(
            select(func.max(DocumentAccessAudit.block_number))
        )
        max_block = result.scalar() or 0
        return max_block + 1
    
    def _calculate_audit_hash(self, audit_entry: DocumentAccessAudit) -> str:
        """Calculate hash for audit entry integrity."""
        import hashlib
        
        hash_data = f"{audit_entry.document_id}{audit_entry.user_id}{audit_entry.action}{audit_entry.created_at}"
        return hashlib.sha256(hash_data.encode()).hexdigest()


# Global service instance
_enhanced_dicom_service: Optional[EnhancedDicomService] = None


def get_enhanced_dicom_service(
    document_service: Optional[DocumentStorageService] = None
) -> EnhancedDicomService:
    """Get or create enhanced DICOM service instance."""
    global _enhanced_dicom_service
    
    if _enhanced_dicom_service is None:
        from app.modules.document_management.service import get_document_service
        doc_service = document_service or get_document_service()
        
        _enhanced_dicom_service = EnhancedDicomService(
            document_service=doc_service
        )
    
    return _enhanced_dicom_service