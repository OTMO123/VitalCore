"""
🏥 DICOM Role-Based Access Control (RBAC)
Extended RBAC for Orthanc DICOM integration
Compliance: SOC2 Type II + HIPAA + Role-based security

This module extends the existing RBAC system with DICOM-specific roles and permissions.
"""

from enum import Enum
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from datetime import datetime

import structlog

logger = structlog.get_logger(__name__)


class DicomRole(Enum):
    """DICOM-specific roles extending base system roles."""
    
    # Clinical roles
    RADIOLOGIST = "RADIOLOGIST"              # Full DICOM access, interpretation
    RADIOLOGY_TECHNICIAN = "RADIOLOGY_TECH"  # DICOM upload, basic viewing
    REFERRING_PHYSICIAN = "REFERRING_PHYSICIAN"  # Patient-specific DICOM viewing
    CLINICAL_STAFF = "CLINICAL_STAFF"        # Limited DICOM viewing
    
    # Administrative roles  
    DICOM_ADMINISTRATOR = "DICOM_ADMIN"      # System configuration, user management
    PACS_OPERATOR = "PACS_OPERATOR"         # PACS management, data migration
    
    # Technical roles
    SYSTEM_ADMINISTRATOR = "SYSTEM_ADMIN"    # Full system access
    INTEGRATION_SERVICE = "INTEGRATION_SVC"  # API access for services
    
    # Research roles
    RESEARCHER = "RESEARCHER"                # De-identified data access
    DATA_SCIENTIST = "DATA_SCIENTIST"        # Analytics and ML training data
    
    # External roles
    EXTERNAL_CLINICIAN = "EXTERNAL_CLINICIAN"  # Limited remote access
    STUDENT = "STUDENT"                      # Educational access with supervision


class DicomPermission(Enum):
    """DICOM-specific permissions for granular access control."""
    
    # DICOM Data Access
    DICOM_VIEW = "dicom:view"                # View DICOM images
    DICOM_DOWNLOAD = "dicom:download"        # Download DICOM files
    DICOM_UPLOAD = "dicom:upload"            # Upload new DICOM studies
    DICOM_DELETE = "dicom:delete"            # Delete DICOM studies
    
    # Metadata Access
    METADATA_READ = "metadata:read"          # Read DICOM metadata
    METADATA_WRITE = "metadata:write"        # Write/update metadata
    METADATA_GENERATE = "metadata:generate"  # AI-generated metadata
    
    # Patient Data Access
    PHI_DICOM_ACCESS = "phi:dicom"           # Access PHI in DICOM
    CROSS_PATIENT_VIEW = "patient:cross"     # View across patient boundaries
    PATIENT_SEARCH = "patient:search"        # Search patient DICOM studies
    
    # System Operations
    ORTHANC_CONFIG = "orthanc:config"        # Configure Orthanc server
    ORTHANC_STATS = "orthanc:stats"          # View system statistics
    ORTHANC_LOGS = "orthanc:logs"            # Access system logs
    
    # Quality Control
    QC_REVIEW = "qc:review"                  # Quality control review
    QC_APPROVE = "qc:approve"                # Approve DICOM studies
    QC_REJECT = "qc:reject"                  # Reject poor quality studies
    
    # Research and Analytics
    RESEARCH_ACCESS = "research:access"      # Access de-identified data
    ANALYTICS_READ = "analytics:read"        # View analytics dashboards
    ML_TRAINING_DATA = "ml:training"         # Access ML training datasets
    
    # Integration
    API_ACCESS = "api:access"                # API integration access
    WEBHOOK_MANAGE = "webhook:manage"        # Manage webhooks
    EXPORT_DATA = "export:data"              # Export DICOM data


@dataclass
class DicomAccessContext:
    """Context for DICOM access decisions."""
    user_id: str
    user_role: str
    patient_id: Optional[str] = None
    study_id: Optional[str] = None
    modality: Optional[str] = None
    institution: Optional[str] = None
    access_time: datetime = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    
    def __post_init__(self):
        if self.access_time is None:
            self.access_time = datetime.utcnow()


class DicomRBACManager:
    """
    DICOM Role-Based Access Control Manager
    
    Manages permissions for different user roles accessing DICOM data.
    Integrates with existing IRIS Healthcare API RBAC system.
    """
    
    def __init__(self):
        self.logger = logger.bind(component="DicomRBAC")
        
        # Define role-permission mappings
        self.role_permissions = self._initialize_role_permissions()
        
        # Define role hierarchy (higher number = more permissions)
        self.role_hierarchy = {
            DicomRole.STUDENT: 0,
            DicomRole.EXTERNAL_CLINICIAN: 1,
            DicomRole.CLINICAL_STAFF: 2,
            DicomRole.REFERRING_PHYSICIAN: 3,
            DicomRole.RADIOLOGY_TECHNICIAN: 4,
            DicomRole.RESEARCHER: 4,
            DicomRole.RADIOLOGIST: 5,
            DicomRole.DATA_SCIENTIST: 5,
            DicomRole.PACS_OPERATOR: 6,
            DicomRole.DICOM_ADMINISTRATOR: 7,
            DicomRole.INTEGRATION_SERVICE: 8,
            DicomRole.SYSTEM_ADMINISTRATOR: 9
        }
    
    def _initialize_role_permissions(self) -> Dict[DicomRole, Set[DicomPermission]]:
        """Initialize role-permission mappings."""
        return {
            # Clinical roles
            DicomRole.RADIOLOGIST: {
                DicomPermission.DICOM_VIEW,
                DicomPermission.DICOM_DOWNLOAD,
                DicomPermission.METADATA_READ,
                DicomPermission.METADATA_WRITE,
                DicomPermission.PHI_DICOM_ACCESS,
                DicomPermission.CROSS_PATIENT_VIEW,
                DicomPermission.PATIENT_SEARCH,
                DicomPermission.QC_REVIEW,
                DicomPermission.QC_APPROVE,
                DicomPermission.QC_REJECT,
                DicomPermission.ANALYTICS_READ,
            },
            
            DicomRole.RADIOLOGY_TECHNICIAN: {
                DicomPermission.DICOM_VIEW,
                DicomPermission.DICOM_UPLOAD,
                DicomPermission.METADATA_READ,
                DicomPermission.PHI_DICOM_ACCESS,
                DicomPermission.PATIENT_SEARCH,
                DicomPermission.QC_REVIEW,
            },
            
            DicomRole.REFERRING_PHYSICIAN: {
                DicomPermission.DICOM_VIEW,
                DicomPermission.DICOM_DOWNLOAD,
                DicomPermission.METADATA_READ,
                DicomPermission.PHI_DICOM_ACCESS,
                # Note: No cross-patient access for referring physicians
            },
            
            DicomRole.CLINICAL_STAFF: {
                DicomPermission.DICOM_VIEW,
                DicomPermission.METADATA_READ,
                DicomPermission.PHI_DICOM_ACCESS,
            },
            
            # Administrative roles
            DicomRole.DICOM_ADMINISTRATOR: {
                DicomPermission.DICOM_VIEW,
                DicomPermission.DICOM_DOWNLOAD,
                DicomPermission.DICOM_UPLOAD,
                DicomPermission.DICOM_DELETE,
                DicomPermission.METADATA_READ,
                DicomPermission.METADATA_WRITE,
                DicomPermission.PHI_DICOM_ACCESS,
                DicomPermission.CROSS_PATIENT_VIEW,
                DicomPermission.PATIENT_SEARCH,
                DicomPermission.ORTHANC_CONFIG,
                DicomPermission.ORTHANC_STATS,
                DicomPermission.ORTHANC_LOGS,
                DicomPermission.QC_REVIEW,
                DicomPermission.QC_APPROVE,
                DicomPermission.QC_REJECT,
                DicomPermission.ANALYTICS_READ,
                DicomPermission.API_ACCESS,
                DicomPermission.WEBHOOK_MANAGE,
                DicomPermission.EXPORT_DATA,
            },
            
            DicomRole.PACS_OPERATOR: {
                DicomPermission.DICOM_VIEW,
                DicomPermission.DICOM_UPLOAD,
                DicomPermission.DICOM_DELETE,
                DicomPermission.METADATA_READ,
                DicomPermission.METADATA_WRITE,
                DicomPermission.PHI_DICOM_ACCESS,
                DicomPermission.CROSS_PATIENT_VIEW,
                DicomPermission.PATIENT_SEARCH,
                DicomPermission.ORTHANC_STATS,
                DicomPermission.QC_REVIEW,
                DicomPermission.EXPORT_DATA,
            },
            
            # Technical roles
            DicomRole.SYSTEM_ADMINISTRATOR: set(DicomPermission),  # All permissions
            
            DicomRole.INTEGRATION_SERVICE: {
                DicomPermission.DICOM_VIEW,
                DicomPermission.DICOM_UPLOAD,
                DicomPermission.METADATA_READ,
                DicomPermission.METADATA_WRITE,
                DicomPermission.METADATA_GENERATE,
                DicomPermission.PHI_DICOM_ACCESS,
                DicomPermission.CROSS_PATIENT_VIEW,
                DicomPermission.PATIENT_SEARCH,
                DicomPermission.ORTHANC_STATS,
                DicomPermission.API_ACCESS,
                DicomPermission.ML_TRAINING_DATA,
            },
            
            # Research roles
            DicomRole.RESEARCHER: {
                DicomPermission.DICOM_VIEW,
                DicomPermission.DICOM_DOWNLOAD,
                DicomPermission.METADATA_READ,
                DicomPermission.RESEARCH_ACCESS,
                DicomPermission.ANALYTICS_READ,
                # Note: No PHI access for researchers (de-identified only)
            },
            
            DicomRole.DATA_SCIENTIST: {
                DicomPermission.DICOM_VIEW,
                DicomPermission.DICOM_DOWNLOAD,
                DicomPermission.METADATA_READ,
                DicomPermission.METADATA_GENERATE,
                DicomPermission.RESEARCH_ACCESS,
                DicomPermission.ANALYTICS_READ,
                DicomPermission.ML_TRAINING_DATA,
                DicomPermission.API_ACCESS,
            },
            
            # External roles
            DicomRole.EXTERNAL_CLINICIAN: {
                DicomPermission.DICOM_VIEW,
                DicomPermission.METADATA_READ,
                DicomPermission.PHI_DICOM_ACCESS,
                # Limited access for external users
            },
            
            DicomRole.STUDENT: {
                DicomPermission.DICOM_VIEW,
                DicomPermission.METADATA_READ,
                # No PHI access for students
            },
        }
    
    def has_permission(
        self,
        user_role: str,
        permission: DicomPermission,
        context: DicomAccessContext
    ) -> bool:
        """
        Check if user has specific permission in given context.
        
        Args:
            user_role: User's DICOM role
            permission: Required permission
            context: Access context with patient/study info
            
        Returns:
            True if user has permission, False otherwise
        """
        try:
            # Convert string role to enum
            role_enum = DicomRole(user_role.upper())
        except ValueError:
            self.logger.warning("Invalid DICOM role", role=user_role)
            return False
        
        # Check basic permission
        role_permissions = self.role_permissions.get(role_enum, set())
        if permission not in role_permissions:
            return False
        
        # Apply context-specific rules
        return self._check_contextual_rules(role_enum, permission, context)
    
    def _check_contextual_rules(
        self,
        role: DicomRole,
        permission: DicomPermission,
        context: DicomAccessContext
    ) -> bool:
        """Apply contextual access rules."""
        
        # PHI access requires special handling
        if permission == DicomPermission.PHI_DICOM_ACCESS:
            # Students and external researchers cannot access PHI
            if role in [DicomRole.STUDENT, DicomRole.RESEARCHER]:
                return False
            
            # External clinicians need additional verification
            if role == DicomRole.EXTERNAL_CLINICIAN:
                return self._verify_external_access(context)
        
        # Cross-patient access restrictions
        if permission == DicomPermission.CROSS_PATIENT_VIEW:
            # Referring physicians can only see their own patients
            if role == DicomRole.REFERRING_PHYSICIAN:
                return self._verify_patient_relationship(context)
        
        # Modality-specific restrictions
        if context.modality and not self._check_modality_access(role, context.modality):
            return False
        
        return True
    
    def _verify_external_access(self, context: DicomAccessContext) -> bool:
        """Verify external clinician has authorized access."""
        # Implement additional security checks for external users
        # This could include VPN verification, time restrictions, etc.
        self.logger.info(
            "External clinician access",
            user_id=context.user_id,
            patient_id=context.patient_id,
            client_ip=context.client_ip
        )
        return True  # Simplified for now
    
    def _verify_patient_relationship(self, context: DicomAccessContext) -> bool:
        """Verify physician has relationship with patient."""
        # In real system, this would check physician-patient relationships
        self.logger.info(
            "Patient relationship verification",
            user_id=context.user_id,
            patient_id=context.patient_id
        )
        return True  # Simplified for now
    
    def _check_modality_access(self, role: DicomRole, modality: str) -> bool:
        """Check if role has access to specific modality."""
        # Some roles might be restricted to certain modalities
        restricted_modalities = {
            DicomRole.STUDENT: ["CT", "MR"],  # Only basic modalities for students
        }
        
        if role in restricted_modalities:
            return modality in restricted_modalities[role]
        
        return True
    
    def get_user_permissions(self, user_role: str) -> Set[DicomPermission]:
        """Get all permissions for a user role."""
        try:
            role_enum = DicomRole(user_role.upper())
            return self.role_permissions.get(role_enum, set())
        except ValueError:
            return set()
    
    def audit_access_attempt(
        self,
        context: DicomAccessContext,
        permission: DicomPermission,
        granted: bool,
        reason: Optional[str] = None
    ):
        """Audit DICOM access attempts for compliance."""
        self.logger.info(
            "DICOM access attempt",
            user_id=context.user_id,
            user_role=context.user_role,
            permission=permission.value,
            granted=granted,
            reason=reason,
            patient_id=context.patient_id,
            study_id=context.study_id,
            modality=context.modality,
            client_ip=context.client_ip,
            compliance_tags=["HIPAA", "SOC2", "RBAC", "DICOM"]
        )


# Global RBAC manager instance
_dicom_rbac_manager: Optional[DicomRBACManager] = None


def get_dicom_rbac_manager() -> DicomRBACManager:
    """Get or create DICOM RBAC manager instance."""
    global _dicom_rbac_manager
    if _dicom_rbac_manager is None:
        _dicom_rbac_manager = DicomRBACManager()
    return _dicom_rbac_manager


# Convenience functions for FastAPI dependencies
def require_dicom_permission(permission: DicomPermission):
    """FastAPI dependency for DICOM permission checking."""
    
    def permission_dependency(
        user_id: str,  # From JWT token
        user_role: str,  # From JWT token  
        patient_id: Optional[str] = None,
        study_id: Optional[str] = None,
        client_ip: Optional[str] = None
    ) -> bool:
        rbac = get_dicom_rbac_manager()
        context = DicomAccessContext(
            user_id=user_id,
            user_role=user_role,
            patient_id=patient_id,
            study_id=study_id,
            client_ip=client_ip
        )
        
        has_access = rbac.has_permission(user_role, permission, context)
        
        # Audit the access attempt
        rbac.audit_access_attempt(
            context=context,
            permission=permission,
            granted=has_access,
            reason="API access attempt"
        )
        
        if not has_access:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: {permission.value} required"
            )
        
        return True
    
    return permission_dependency


# Role mapping helpers
def map_user_role_to_dicom_role(user_role: str) -> Optional[DicomRole]:
    """Map standard user roles to DICOM-specific roles."""
    role_mapping = {
        "USER": DicomRole.CLINICAL_STAFF,
        "OPERATOR": DicomRole.RADIOLOGY_TECHNICIAN,
        "ADMIN": DicomRole.DICOM_ADMINISTRATOR,
        "SUPER_ADMIN": DicomRole.SYSTEM_ADMINISTRATOR,
        # Add custom mappings
        "RADIOLOGIST": DicomRole.RADIOLOGIST,
        "PHYSICIAN": DicomRole.REFERRING_PHYSICIAN,
        "RESEARCHER": DicomRole.RESEARCHER,
        "DATA_SCIENTIST": DicomRole.DATA_SCIENTIST,
    }
    
    try:
        return role_mapping.get(user_role.upper())
    except (AttributeError, KeyError):
        return None