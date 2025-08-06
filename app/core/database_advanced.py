from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import (
    DateTime, String, Boolean, Text, Integer, JSON, UUID, 
    Enum, ForeignKey, CheckConstraint, Index, DECIMAL, DATE, 
    BigInteger, func
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, INET
from datetime import datetime, date
from typing import AsyncGenerator, Optional, List, Dict, Any
from enum import Enum as PyEnum
import structlog
import uuid

from app.core.config import get_settings

logger = structlog.get_logger()

# Enums matching PostgreSQL custom types
class APIStatus(PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"

class RequestStatus(PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CIRCUIT_BROKEN = "circuit_broken"

class AuditEventType(PyEnum):
    ACCESS = "access"
    MODIFY = "modify"
    DELETE = "delete"
    AUTHENTICATE = "authenticate"
    AUTHORIZE = "authorize"
    API_CALL = "api_call"
    PURGE = "purge"
    EXPORT = "export"
    CONFIGURATION_CHANGE = "configuration_change"

class DataClassification(PyEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PHI = "phi"
    PII = "pii"

class PurgeStatus(PyEnum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    OVERRIDDEN = "overridden"
    SUSPENDED = "suspended"

class RetentionReason(PyEnum):
    LEGAL_HOLD = "legal_hold"
    ACTIVE_INVESTIGATION = "active_investigation"
    COMPLIANCE_AUDIT = "compliance_audit"
    USER_REQUEST = "user_request"
    SYSTEM_DEPENDENCY = "system_dependency"

# Healthcare-specific enums
class ConsentStatus(PyEnum):
    PENDING = "pending"
    GRANTED = "granted"
    DENIED = "denied"
    REVOKED = "revoked"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"

class ConsentType(PyEnum):
    TREATMENT = "treatment"
    RESEARCH = "research"
    MARKETING = "marketing"
    DATA_SHARING = "data_sharing"
    DATA_ACCESS = "data_access"
    DATA_DELETION = "data_deletion"
    EMERGENCY_ACCESS = "emergency_access"
    IMMUNIZATION_REGISTRY = "immunization_registry"

class DocumentType(PyEnum):
    IMMUNIZATION_RECORD = "immunization_record"
    CLINICAL_NOTE = "clinical_note"
    LAB_RESULT = "lab_result"
    DISCHARGE_SUMMARY = "discharge_summary"
    CONSENT_FORM = "consent_form"
    RADIOLOGY_REPORT = "radiology_report"
    PRESCRIPTION = "prescription"
    REFERRAL = "referral"

class Base(DeclarativeBase):
    """Base class for all database models."""
    pass

class BaseModel(Base):
    """Base model with common fields for audit and tracking."""
    __abstract__ = True
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=func.now(), 
        onupdate=func.now()
    )

# ============================================
# CORE SYSTEM TABLES
# ============================================

class SystemConfiguration(BaseModel):
    """System configuration with audit capability."""
    __tablename__ = "system_configuration"
    
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    value: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    encrypted: Mapped[bool] = mapped_column(Boolean, default=False)
    data_classification: Mapped[DataClassification] = mapped_column(
        Enum(DataClassification), default=DataClassification.INTERNAL
    )
    description: Mapped[Optional[str]] = mapped_column(Text)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    modified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    modified_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    __table_args__ = (
        CheckConstraint('valid_to IS NULL OR valid_to > valid_from', name='check_valid_dates'),
    )

# ============================================
# USER & ACCESS MANAGEMENT
# ============================================

class User(BaseModel):
    """Users table with enhanced security fields."""
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    username: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(255))
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login_ip: Mapped[Optional[str]] = mapped_column(INET)
    password_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    api_key_hash: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    api_key_last_used: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system_user: Mapped[bool] = mapped_column(Boolean, default=False)
    deactivated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # RBAC field for simple role assignment (compatible with basic model)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="user")
    
    # Relationships
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole", 
        back_populates="user",
        foreign_keys="UserRole.user_id"
    )
    
    __table_args__ = (
        CheckConstraint(
            'locked_until IS NULL OR locked_until > CURRENT_TIMESTAMP', 
            name='check_lock_validity'
        ),
    )

class Role(BaseModel):
    """Roles with hierarchical support."""
    __tablename__ = "roles"
    
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    parent_role_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id")
    )
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Self-referential relationship
    parent_role: Mapped[Optional["Role"]] = relationship("Role", remote_side="Role.id")
    child_roles: Mapped[List["Role"]] = relationship("Role", back_populates="parent_role")
    
    # Relationships
    role_permissions: Mapped[List["RolePermission"]] = relationship("RolePermission", back_populates="role")
    user_roles: Mapped[List["UserRole"]] = relationship("UserRole", back_populates="role")

class Permission(BaseModel):
    """Permissions granular control."""
    __tablename__ = "permissions"
    
    resource: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_system_permission: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    role_permissions: Mapped[List["RolePermission"]] = relationship("RolePermission", back_populates="permission")
    
    __table_args__ = (
        Index('unique_resource_action', resource, action, unique=True),
    )

class RolePermission(Base):
    """Role-Permission mapping."""
    __tablename__ = "role_permissions"
    
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True
    )
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    granted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    
    # Relationships
    role: Mapped[Role] = relationship("Role", back_populates="role_permissions")
    permission: Mapped[Permission] = relationship("Permission", back_populates="role_permissions")

class UserRole(Base):
    """User-Role assignments with temporal validity."""
    __tablename__ = "user_roles"
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), primary_key=True
    )
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    assigned_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    assignment_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships  
    user: Mapped[User] = relationship(
        "User", 
        back_populates="user_roles",
        foreign_keys="UserRole.user_id"
    )
    assigned_by_user: Mapped[User] = relationship(
        "User",
        foreign_keys="UserRole.assigned_by"
    )
    role: Mapped[Role] = relationship("Role", back_populates="user_roles")
    
    __table_args__ = (
        CheckConstraint('valid_to IS NULL OR valid_to > valid_from', name='check_role_validity'),
    )

# ============================================
# API INTEGRATION TABLES
# ============================================

class APIEndpoint(BaseModel):
    """API Endpoints configuration."""
    __tablename__ = "api_endpoints"
    
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    api_version: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[APIStatus] = mapped_column(Enum(APIStatus), default=APIStatus.ACTIVE)
    auth_type: Mapped[str] = mapped_column(String(50), nullable=False)
    rate_limit_requests: Mapped[Optional[int]] = mapped_column(Integer)
    rate_limit_window_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30)
    retry_attempts: Mapped[int] = mapped_column(Integer, default=3)
    retry_delay_seconds: Mapped[int] = mapped_column(Integer, default=1)
    circuit_breaker_threshold: Mapped[int] = mapped_column(Integer, default=5)
    circuit_breaker_timeout_seconds: Mapped[int] = mapped_column(Integer, default=60)
    ssl_verify: Mapped[bool] = mapped_column(Boolean, default=True)
    health_check_endpoint: Mapped[Optional[str]] = mapped_column(String(500))
    health_check_interval_seconds: Mapped[int] = mapped_column(Integer, default=300)
    last_health_check_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_health_check_status: Mapped[Optional[bool]] = mapped_column(Boolean)
    config_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Relationships
    api_credentials: Mapped[List["APICredential"]] = relationship("APICredential", back_populates="api_endpoint")
    api_requests: Mapped[List["APIRequest"]] = relationship("APIRequest", back_populates="api_endpoint")
    
    __table_args__ = (
        CheckConstraint(
            "auth_type IN ('oauth2', 'hmac', 'jwt', 'api_key', 'basic')", 
            name='check_auth_type'
        ),
    )

class APICredential(BaseModel):
    """API Credentials vault (encrypted storage)."""
    __tablename__ = "api_credentials"
    
    api_endpoint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("api_endpoints.id", ondelete="CASCADE"), nullable=False
    )
    credential_name: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_value: Mapped[str] = mapped_column(Text, nullable=False)  # Always encrypted
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_rotated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    rotation_reminder_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    
    # Relationships
    api_endpoint: Mapped[APIEndpoint] = relationship("APIEndpoint", back_populates="api_credentials")
    
    __table_args__ = (
        Index('unique_endpoint_credential', api_endpoint_id, credential_name, unique=True),
    )

class APIRequest(BaseModel):
    """API Request tracking with comprehensive audit."""
    __tablename__ = "api_requests"
    
    api_endpoint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("api_endpoints.id"), nullable=False
    )
    correlation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    endpoint_path: Mapped[str] = mapped_column(String(500), nullable=False)
    request_headers: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    request_body: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    request_hash: Mapped[Optional[str]] = mapped_column(String(64))  # For deduplication
    response_status_code: Mapped[Optional[int]] = mapped_column(Integer)
    response_headers: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    response_body: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    status: Mapped[RequestStatus] = mapped_column(Enum(RequestStatus), default=RequestStatus.PENDING)
    attempt_count: Mapped[int] = mapped_column(Integer, default=1)
    total_duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_stack_trace: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    api_endpoint: Mapped[APIEndpoint] = relationship("APIEndpoint", back_populates="api_requests")
    
    # Note: Temporarily removed constraint to resolve enum creation issue
    # __table_args__ = (
    #     CheckConstraint(
    #         "(status = 'completed' OR status = 'failed' OR status = 'timeout') AND completed_at IS NOT NULL OR "
    #         "(status = 'pending' OR status = 'in_progress') AND completed_at IS NULL",
    #         name='check_completion'
    #     ),
    # )

# ============================================
# AUDIT LOGGING TABLES (SOC2 COMPLIANT)
# ============================================

class AuditLog(Base):
    """Immutable audit log table."""
    __tablename__ = "audit_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True, default=func.now()
    )
    event_type: Mapped[AuditEventType] = mapped_column(Enum(AuditEventType), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    correlation_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    resource_type: Mapped[Optional[str]] = mapped_column(String(100))
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    result: Mapped[str] = mapped_column(String(50), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    request_method: Mapped[Optional[str]] = mapped_column(String(20))
    request_path: Mapped[Optional[str]] = mapped_column(String(500))
    request_body_hash: Mapped[Optional[str]] = mapped_column(String(64))
    response_status_code: Mapped[Optional[int]] = mapped_column(Integer)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    config_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    compliance_tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    data_classification: Mapped[Optional[DataClassification]] = mapped_column(Enum(DataClassification))
    
    # Integrity fields
    previous_log_hash: Mapped[Optional[str]] = mapped_column(String(64))
    log_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    
    __table_args__ = (
        CheckConstraint("result IN ('success', 'failure', 'error', 'denied')", name='check_result'),
    )

# ============================================
# HEALTHCARE SPECIFIC (IRIS/FHIR)
# ============================================

class Patient(BaseModel):
    """Patient data with PHI classification."""
    __tablename__ = "patients"
    
    external_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)  # IRIS patient ID
    mrn: Mapped[Optional[str]] = mapped_column(String(100))  # Medical Record Number (encrypted)
    first_name_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    last_name_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    date_of_birth_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    ssn_encrypted: Mapped[Optional[str]] = mapped_column(Text)
    data_classification: Mapped[DataClassification] = mapped_column(
        Enum(DataClassification), default=DataClassification.PHI
    )
    consent_status: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    iris_sync_status: Mapped[Optional[str]] = mapped_column(String(50))
    iris_last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    soft_deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships - Enterprise healthcare model relationships with proper module references
    immunizations: Mapped[List["app.modules.healthcare_records.models.Immunization"]] = relationship(
        "app.modules.healthcare_records.models.Immunization", 
        back_populates="patient",
        lazy="select"  # Enterprise-grade lazy loading for performance
    )
    clinical_documents: Mapped[List["ClinicalDocument"]] = relationship("ClinicalDocument", back_populates="patient")
    consents: Mapped[List["Consent"]] = relationship("Consent", back_populates="patient")
    phi_access_logs: Mapped[List["PHIAccessLog"]] = relationship("PHIAccessLog", back_populates="patient")

# REMOVED: Duplicate Immunization class - use healthcare_records.models instead
# class Immunization(BaseModel):
#     """Immunization records."""
#     __tablename__ = "immunizations"
#     __table_args__ = {'extend_existing': True}
#     
#     patient_id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False
#     )
#     vaccine_code: Mapped[str] = mapped_column(String(50), nullable=False)
#     vaccine_name: Mapped[Optional[str]] = mapped_column(String(255))
#     administration_date: Mapped[date] = mapped_column(DATE, nullable=False)
#     lot_number: Mapped[Optional[str]] = mapped_column(String(100))
#     manufacturer: Mapped[Optional[str]] = mapped_column(String(255))
#     dose_number: Mapped[Optional[int]] = mapped_column(Integer)
#     series_complete: Mapped[bool] = mapped_column(Boolean, default=False)
#     administered_by: Mapped[Optional[str]] = mapped_column(String(255))
#     administration_site: Mapped[Optional[str]] = mapped_column(String(100))
#     route: Mapped[Optional[str]] = mapped_column(String(50))
#     iris_record_id: Mapped[Optional[str]] = mapped_column(String(255))
#     data_source: Mapped[Optional[str]] = mapped_column(String(100))
#     soft_deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
#     
#     # Relationships
#     patient: Mapped[Patient] = relationship("Patient", back_populates="immunizations")
# 
class ClinicalDocument(BaseModel):
    """Clinical documents with encryption and FHIR compliance."""
    __tablename__ = "clinical_documents"
    
    # Document identification
    document_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="final")
    
    # Patient and clinical context
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True
    )
    encounter_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    
    # Content (encrypted)
    content_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), default="text/plain")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    
    # Classification and security
    data_classification: Mapped[DataClassification] = mapped_column(
        Enum(DataClassification), default=DataClassification.PHI
    )
    confidentiality_level: Mapped[str] = mapped_column(String(20), default="R")
    access_level: Mapped[str] = mapped_column(String(50), default="restricted")
    
    # FHIR compliance fields
    fhir_resource_type: Mapped[str] = mapped_column(String(100), default="DocumentReference")
    fhir_identifier: Mapped[Optional[str]] = mapped_column(String(255))
    category: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    
    # Author and custodian
    author_references: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    custodian_reference: Mapped[Optional[str]] = mapped_column(String(255))
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    
    # Access control
    authorized_roles: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    authorized_users: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    
    # Audit and retention
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    retention_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    soft_deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="clinical_documents")
    phi_access_logs: Mapped[List["PHIAccessLog"]] = relationship("PHIAccessLog", back_populates="clinical_document")
    
    __table_args__ = (
        CheckConstraint(
            "status IN ('preliminary', 'final', 'amended', 'entered-in-error')", 
            name='check_document_status'
        ),
        CheckConstraint(
            "access_level IN ('public', 'restricted', 'confidential', 'secret')", 
            name='check_access_level'
        ),
        Index('idx_patient_document_type', patient_id, document_type),
        Index('idx_document_created_at', 'created_at'),
    )

class Consent(BaseModel):
    """Patient consent records for data usage and sharing."""
    __tablename__ = "consents"
    
    # Patient and consent identification
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True
    )
    consent_types: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    
    # Consent scope
    purpose_codes: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    data_types: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    categories: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    
    # Validity period
    effective_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Legal and compliance
    legal_basis: Mapped[str] = mapped_column(String(255), nullable=False)
    jurisdiction: Mapped[Optional[str]] = mapped_column(String(100))
    policy_references: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    
    # Consent capture
    consent_method: Mapped[str] = mapped_column(String(100), nullable=False)
    consent_source: Mapped[Optional[str]] = mapped_column(String(255))
    witness_signature: Mapped[Optional[str]] = mapped_column(Text)
    signature_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    
    # Parties involved
    patient_signature: Mapped[Optional[str]] = mapped_column(Text)
    guardian_signature: Mapped[Optional[str]] = mapped_column(Text)
    guardian_relationship: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Audit fields
    granted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    verification_method: Mapped[Optional[str]] = mapped_column(String(100))
    verification_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Data subject rights
    withdrawal_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    withdrawal_method: Mapped[Optional[str]] = mapped_column(String(255))
    objection_handling: Mapped[Optional[str]] = mapped_column(Text)
    
    # Revision tracking
    version: Mapped[int] = mapped_column(Integer, default=1)
    superseded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consents.id")
    )
    supersedes: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    
    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="consents")
    phi_access_logs: Mapped[List["PHIAccessLog"]] = relationship("PHIAccessLog", back_populates="consent")
    
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'proposed', 'active', 'rejected', 'inactive', 'entered-in-error')", 
            name='check_consent_status'
        ),
        CheckConstraint(
            'effective_period_end IS NULL OR effective_period_end > effective_period_start', 
            name='check_consent_validity'
        ),
        CheckConstraint(
            "consent_method IN ('written', 'verbal', 'electronic', 'implied')", 
            name='check_consent_method'
        ),
        Index('idx_patient_consent_status', patient_id, status),
        Index('idx_consent_effective_period', effective_period_start, effective_period_end),
    )

class PHIAccessLog(BaseModel):
    """Log of PHI access for audit and compliance."""
    __tablename__ = "phi_access_logs"
    
    # Access identification
    access_session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    correlation_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    
    # Patient and resource
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True
    )
    clinical_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinical_documents.id")
    )
    consent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consents.id")
    )
    
    # Accessor information
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    user_role: Mapped[str] = mapped_column(String(100), nullable=False)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    
    # Access details
    access_type: Mapped[str] = mapped_column(String(50), nullable=False)
    phi_fields_accessed: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    access_purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_basis: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Request details
    request_method: Mapped[Optional[str]] = mapped_column(String(20))
    request_path: Mapped[Optional[str]] = mapped_column(String(500))
    request_parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    
    # Response and outcome
    access_granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    denial_reason: Mapped[Optional[str]] = mapped_column(String(255))
    data_returned: Mapped[bool] = mapped_column(Boolean, default=False)
    data_hash: Mapped[Optional[str]] = mapped_column(String(64))
    
    # Session and network info
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    session_duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Compliance and audit
    consent_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    minimum_necessary_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    data_classification: Mapped[DataClassification] = mapped_column(
        Enum(DataClassification), default=DataClassification.PHI
    )
    retention_category: Mapped[str] = mapped_column(String(100), default="audit_log")
    
    # Breakglass and emergency access
    emergency_access: Mapped[bool] = mapped_column(Boolean, default=False)
    emergency_justification: Mapped[Optional[str]] = mapped_column(Text)
    supervisor_approval: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    
    # Data breach detection
    unusual_access_pattern: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_score: Mapped[Optional[int]] = mapped_column(Integer)
    flagged_for_review: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    access_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    access_ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="phi_access_logs")
    clinical_document: Mapped[Optional["ClinicalDocument"]] = relationship("ClinicalDocument", back_populates="phi_access_logs")
    consent: Mapped[Optional["Consent"]] = relationship("Consent", back_populates="phi_access_logs")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    supervisor: Mapped[Optional["User"]] = relationship("User", foreign_keys=[supervisor_approval])
    
    __table_args__ = (
        CheckConstraint(
            "access_type IN ('view', 'edit', 'print', 'export', 'delete', 'bulk_access')", 
            name='check_access_type'
        ),
        CheckConstraint(
            'access_ended_at IS NULL OR access_ended_at >= access_started_at', 
            name='check_access_duration'
        ),
        CheckConstraint(
            'risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 100)', 
            name='check_risk_score_range'
        ),
        Index('idx_access_timestamp', access_started_at.desc()),
        Index('idx_patient_access_audit', patient_id, access_started_at),
        Index('idx_user_access_audit', user_id, access_started_at),
        Index('idx_unusual_access', unusual_access_pattern, flagged_for_review),
    )

# Database engine and session management
# Lazy initialization to avoid module-level database connection
engine = None
AsyncSessionLocal = None

def get_engine():
    """Get or create the database engine."""
    global engine
    if engine is None:
        settings = get_settings()
        database_url = settings.DATABASE_URL
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        elif database_url.startswith("sqlite://"):
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")

        # Create engine with appropriate parameters based on database type
        if database_url.startswith("sqlite"):
            engine = create_async_engine(
                database_url,
                echo=settings.DEBUG,
                future=True
            )
        else:
            engine = create_async_engine(
                database_url,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                echo=settings.DEBUG,
                future=True
            )
    return engine

def get_session_factory():
    """Get or create the session factory."""
    global AsyncSessionLocal
    if AsyncSessionLocal is None:
        AsyncSessionLocal = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False
        )
    return AsyncSessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            await session.close()

async def init_db() -> None:
    """Initialize database tables."""
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise

# Alias for backwards compatibility
get_async_session = get_db

async def close_db() -> None:
    """Close database connections."""
    engine = get_engine()
    await engine.dispose()
    logger.info("Database connections closed")