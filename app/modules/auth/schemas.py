from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Set
from datetime import datetime
from enum import Enum
import uuid

# Enterprise UserRole System - SOC2 Type II, FHIR R4, PHI, GDPR Compliant

class UserRole(str, Enum):
    """
    Enterprise Healthcare User Roles with SOC2 Type II, FHIR R4, PHI, and GDPR compliance.
    
    Each role implements principle of least privilege and segregation of duties.
    All role assignments are audited and tracked for compliance reporting.
    """
    
    # Administrative Roles - SOC2 Segregation of Duties
    SUPER_ADMIN = "super_admin"                    # System administration only
    SYSTEM_ADMIN = "system_admin"                  # Infrastructure management
    SECURITY_ADMIN = "security_admin"              # Security configuration
    COMPLIANCE_OFFICER = "compliance_officer"      # SOC2/HIPAA compliance
    DATA_PROTECTION_OFFICER = "dpo"               # GDPR compliance officer
    AUDIT_ADMINISTRATOR = "audit_administrator"    # Audit log management
    
    # Clinical Roles - FHIR R4 Practitioner.qualification aligned
    PHYSICIAN = "physician"                        # MD, DO - full clinical access
    ATTENDING_PHYSICIAN = "attending_physician"    # Senior physician with teaching responsibilities
    RESIDENT_PHYSICIAN = "resident_physician"      # Physician in training
    NURSE_PRACTITIONER = "nurse_practitioner"      # Advanced practice nurse
    REGISTERED_NURSE = "registered_nurse"          # Licensed nurse
    LICENSED_PRACTICAL_NURSE = "lpn"               # Licensed practical nurse
    CLINICAL_TECHNICIAN = "clinical_technician"    # Lab/radiology technician
    PHARMACIST = "pharmacist"                      # Licensed pharmacist
    PHARMACY_TECHNICIAN = "pharmacy_technician"    # Pharmacy support
    PHYSICAL_THERAPIST = "physical_therapist"      # PT/OT specialist
    SOCIAL_WORKER = "social_worker"               # Clinical social worker
    CASE_MANAGER = "case_manager"                 # Care coordination
    
    # Operational Roles - Healthcare Operations
    PATIENT_REGISTRAR = "patient_registrar"        # Patient registration
    MEDICAL_RECORDS = "medical_records"           # Health information management
    BILLING_SPECIALIST = "billing_specialist"      # Medical billing
    INSURANCE_COORDINATOR = "insurance_coordinator" # Insurance verification
    APPOINTMENT_SCHEDULER = "appointment_scheduler" # Scheduling specialist
    QUALITY_ASSURANCE = "quality_assurance"       # Quality improvement
    PATIENT_ADVOCATE = "patient_advocate"         # Patient rights and support
    
    # Research & Analytics Roles - PHI De-identification
    CLINICAL_RESEARCHER = "clinical_researcher"    # De-identified data research
    DATA_ANALYST = "data_analyst"                 # Analytics on de-identified data
    BIOSTATISTICIAN = "biostatistician"          # Statistical analysis
    
    # System Integration Roles
    API_CLIENT = "api_client"                     # External system integration
    INTEGRATION_SERVICE = "integration_service"    # Internal service accounts
    FHIR_CLIENT = "fhir_client"                   # FHIR R4 API access
    HL7_INTERFACE = "hl7_interface"               # HL7 message processing
    
    # Audit & Compliance Roles
    AUDIT_VIEWER = "audit_viewer"                 # Read-only audit access
    COMPLIANCE_AUDITOR = "compliance_auditor"      # External auditor access
    SECURITY_ANALYST = "security_analyst"         # Security monitoring
    
    # Patient Portal Roles
    PATIENT = "patient"                           # Patient portal access
    PATIENT_PROXY = "patient_proxy"               # Legal guardian/proxy
    CAREGIVER = "caregiver"                       # Authorized caregiver
    
    # Emergency Access
    BREAK_GLASS_PROVIDER = "break_glass_provider" # Emergency clinical access
    EMERGENCY_RESPONDER = "emergency_responder"   # EMS/emergency access
    
    # Legacy Compatibility Roles (deprecated - use specific roles above)
    USER = "user"                                 # Legacy general user role
    ADMIN = "admin"                               # Legacy admin role
    OPERATOR = "operator"                         # Legacy operator role


class Permission(str, Enum):
    """
    Granular permissions for PHI access control and GDPR compliance.
    Implements minimum necessary standard for HIPAA compliance.
    """
    
    # Patient Data Permissions
    PATIENT_CREATE = "patient:create"
    PATIENT_READ_ALL = "patient:read:all"           # All patients
    PATIENT_READ_ASSIGNED = "patient:read:assigned" # Only assigned patients
    PATIENT_READ_OWN = "patient:read:own"           # Own patient record
    PATIENT_UPDATE = "patient:update"
    PATIENT_DELETE = "patient:delete"               # Rarely granted
    PATIENT_MERGE = "patient:merge"                 # Duplicate resolution
    
    # PHI Access Permissions - HIPAA Minimum Necessary
    PHI_READ_DEMOGRAPHICS = "phi:read:demographics" # Name, DOB, address
    PHI_READ_CONTACT = "phi:read:contact"           # Phone, email
    PHI_READ_INSURANCE = "phi:read:insurance"       # Insurance information
    PHI_READ_CLINICAL = "phi:read:clinical"         # Clinical notes, diagnoses
    PHI_READ_MEDICATIONS = "phi:read:medications"   # Medication history
    PHI_READ_LABS = "phi:read:labs"                 # Laboratory results
    PHI_READ_IMAGING = "phi:read:imaging"           # Radiology, imaging
    PHI_READ_VITALS = "phi:read:vitals"             # Vital signs
    PHI_EXPORT = "phi:export"                       # Data export capability
    PHI_PRINT = "phi:print"                         # Print PHI documents
    
    # Clinical Documentation
    CLINICAL_NOTES_CREATE = "clinical_notes:create"
    CLINICAL_NOTES_READ = "clinical_notes:read"
    CLINICAL_NOTES_UPDATE = "clinical_notes:update"
    CLINICAL_NOTES_SIGN = "clinical_notes:sign"     # Electronic signature
    
    # Orders and Results
    ORDERS_CREATE = "orders:create"                 # Lab, imaging orders
    ORDERS_READ = "orders:read"
    ORDERS_MODIFY = "orders:modify"
    RESULTS_READ = "results:read"
    RESULTS_RELEASE = "results:release"             # Release to patient
    
    # Medication Management
    PRESCRIPTIONS_CREATE = "prescriptions:create"
    PRESCRIPTIONS_READ = "prescriptions:read"
    PRESCRIPTIONS_MODIFY = "prescriptions:modify"
    PRESCRIPTIONS_CANCEL = "prescriptions:cancel"
    
    # Administrative Permissions
    USER_MANAGEMENT = "user:management"             # User account management
    ROLE_MANAGEMENT = "role:management"             # Role assignments
    SYSTEM_CONFIG = "system:config"                # System configuration
    SECURITY_CONFIG = "security:config"            # Security settings
    
    # Audit and Compliance
    AUDIT_READ = "audit:read"                       # Read audit logs
    AUDIT_EXPORT = "audit:export"                   # Export audit reports
    COMPLIANCE_REPORT = "compliance:report"         # Generate compliance reports
    
    # GDPR Rights Management
    GDPR_DATA_ACCESS = "gdpr:data_access"           # Data subject access requests
    GDPR_DATA_RECTIFICATION = "gdpr:rectification" # Data correction
    GDPR_DATA_ERASURE = "gdpr:erasure"             # Right to be forgotten
    GDPR_DATA_PORTABILITY = "gdpr:portability"     # Data portability
    
    # Emergency Access
    BREAK_GLASS_ACCESS = "break_glass:access"       # Emergency override
    EMERGENCY_OVERRIDE = "emergency:override"       # Critical patient access


class DataClassificationLevel(str, Enum):
    """
    Data classification levels for PHI protection and access control.
    """
    PUBLIC = "public"                               # No restrictions
    INTERNAL = "internal"                           # Internal use only
    CONFIDENTIAL = "confidential"                   # Limited access
    RESTRICTED = "restricted"                       # PHI, highly sensitive
    TOP_SECRET = "top_secret"                       # Maximum protection


class AccessContext(str, Enum):
    """
    Access context for conditional permissions.
    """
    DIRECT_CARE = "direct_care"                     # Direct patient care
    CARE_COORDINATION = "care_coordination"         # Care team coordination
    QUALITY_IMPROVEMENT = "quality_improvement"     # QI activities
    RESEARCH = "research"                           # De-identified research
    BILLING = "billing"                             # Billing and coding
    AUDIT = "audit"                                 # Compliance auditing
    EMERGENCY = "emergency"                         # Emergency situations

class UserCreate(BaseModel):
    """Schema for user creation."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")
    role: UserRole = Field(default=UserRole.PATIENT, description="User role")
    email_verified: Optional[bool] = Field(default=False, description="Email verification status (for testing)")
    is_active: Optional[bool] = Field(default=True, description="User active status")
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username can only contain letters, numbers, hyphens, and underscores")
        return v.lower()
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

class UserLogin(BaseModel):
    """Schema for user login."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")

class UserResponse(BaseModel):
    """Schema for user response."""
    id: uuid.UUID
    username: str
    email: str
    role: UserRole
    is_active: bool
    email_verified: bool  # Changed from is_verified to email_verified
    created_at: datetime
    last_login_at: Optional[datetime] = None  # Changed from last_login to last_login_at
    
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user: Optional[UserResponse] = None

class PasswordReset(BaseModel):
    """Schema for password reset."""
    email: EmailStr = Field(..., description="Email address")

class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

class UserUpdate(BaseModel):
    """Schema for user updates."""
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None

class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

class RoleResponse(BaseModel):
    """Schema for role information."""
    name: str
    description: str
    permissions: list[str]
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PermissionResponse(BaseModel):
    """Schema for permission information."""
    name: str
    description: str
    resource_type: str
    action: str
    
    model_config = ConfigDict(from_attributes=True)

class UserPermissionsResponse(BaseModel):
    """Schema for user permissions response."""
    user_id: uuid.UUID
    username: str
    role: str
    permissions: list[str]
    effective_permissions: list[str]
    last_updated: datetime

class RoleCreate(BaseModel):
    """Schema for role creation."""
    name: str = Field(..., min_length=2, max_length=50)
    description: str = Field(..., min_length=5, max_length=200)
    permissions: list[str] = Field(default=[])
    is_active: bool = Field(default=True)
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Role name can only contain letters, numbers, hyphens, and underscores")
        return v.lower()

class RoleUpdate(BaseModel):
    """Schema for role updates."""
    description: Optional[str] = None
    permissions: Optional[list[str]] = None
    is_active: Optional[bool] = None

class UserRoleAssignment(BaseModel):
    """Schema for user role assignment."""
    user_id: uuid.UUID
    role_name: UserRole
    assigned_by: Optional[str] = None
    reason: Optional[str] = None
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    access_context: Optional[AccessContext] = None


# Enterprise Role Management and Compliance Schemas

class RolePermissionMapping(BaseModel):
    """Defines permissions for each role - SOC2 principle of least privilege."""
    role: UserRole
    permissions: List[Permission]
    data_classification_access: List[DataClassificationLevel]
    contexts: List[AccessContext]
    requires_mfa: bool = False
    max_session_duration: int = Field(default=480, description="Max session in minutes")
    emergency_access: bool = False
    
    model_config = ConfigDict(use_enum_values=True)


class BreakGlassAccessRequest(BaseModel):
    """Schema for emergency break-glass access requests."""
    user_id: uuid.UUID
    patient_id: uuid.UUID
    emergency_reason: str = Field(..., min_length=20, description="Detailed emergency justification")
    clinical_context: str = Field(..., description="Clinical situation requiring emergency access")
    requested_permissions: List[Permission]
    supervisor_approval: Optional[str] = None
    time_limit_minutes: int = Field(default=60, le=240, description="Emergency access duration")
    
    @field_validator("emergency_reason")
    @classmethod
    def validate_emergency_reason(cls, v):
        """Ensure emergency justification is substantial."""
        if len(v.strip()) < 20:
            raise ValueError("Emergency reason must be at least 20 characters")
        return v.strip()


class PHIAccessLog(BaseModel):
    """Schema for PHI access logging - HIPAA compliance."""
    user_id: uuid.UUID
    patient_id: uuid.UUID
    accessed_phi_fields: List[str]
    access_reason: AccessContext
    access_timestamp: datetime
    ip_address: str
    user_agent: str
    session_id: str
    minimum_necessary_justification: str
    data_exported: bool = False
    printed: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class ComplianceAuditReport(BaseModel):
    """Schema for SOC2/HIPAA compliance reporting."""
    report_id: uuid.UUID
    report_type: str = Field(..., pattern="^(SOC2|HIPAA|GDPR|ACCESS_REVIEW)$")
    generated_by: uuid.UUID
    report_period_start: datetime
    report_period_end: datetime
    total_users: int
    total_phi_accesses: int
    failed_login_attempts: int
    role_changes: int
    emergency_accesses: int
    data_exports: int
    compliance_violations: List[Dict]
    recommendations: List[str]
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class GDPRDataSubjectRequest(BaseModel):
    """Schema for GDPR data subject rights requests."""
    request_id: uuid.UUID
    subject_id: uuid.UUID  # Patient or user ID
    request_type: str = Field(..., pattern="^(ACCESS|RECTIFICATION|ERASURE|PORTABILITY|RESTRICTION)$")
    requester_email: EmailStr
    legal_basis_verification: str
    request_details: str
    processing_notes: Optional[str] = None
    fulfillment_deadline: datetime
    status: str = Field(default="PENDING", pattern="^(PENDING|IN_PROGRESS|COMPLETED|REJECTED)$")
    assigned_to: Optional[uuid.UUID] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class RoleAccessReview(BaseModel):
    """Schema for periodic role access reviews - SOC2 requirement."""
    review_id: uuid.UUID
    user_id: uuid.UUID
    current_role: UserRole
    reviewer_id: uuid.UUID
    review_date: datetime
    access_still_required: bool
    role_change_recommended: Optional[UserRole] = None
    additional_permissions_needed: List[Permission] = []
    permissions_to_remove: List[Permission] = []
    justification: str
    next_review_date: datetime
    manager_approval: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class SecurityIncident(BaseModel):
    """Schema for security incident reporting."""
    incident_id: uuid.UUID
    incident_type: str = Field(..., pattern="^(UNAUTHORIZED_ACCESS|DATA_BREACH|FAILED_LOGIN|SUSPICIOUS_ACTIVITY|POLICY_VIOLATION)$")
    severity: str = Field(..., pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    affected_users: List[uuid.UUID] = []
    affected_patients: List[uuid.UUID] = []
    incident_description: str
    discovery_date: datetime
    reported_by: uuid.UUID
    investigation_status: str = Field(default="OPEN", pattern="^(OPEN|INVESTIGATING|RESOLVED|CLOSED)$")
    phi_involved: bool = False
    notification_required: bool = False
    remediation_actions: List[str] = []
    
    model_config = ConfigDict(from_attributes=True)


class FHIRConsentRecord(BaseModel):
    """Schema for FHIR R4 compliant consent management."""
    consent_id: uuid.UUID
    patient_id: uuid.UUID
    consent_type: str = Field(..., pattern="^(TREATMENT|PAYMENT|OPERATIONS|RESEARCH|MARKETING)$")
    status: str = Field(..., pattern="^(ACTIVE|INACTIVE|REJECTED|PENDING)$")
    category: List[str]  # FHIR consent categories
    policy_reference: str
    granted_scope: List[Permission]
    denied_scope: List[Permission] = []
    granted_period_start: datetime
    granted_period_end: Optional[datetime] = None
    authorized_parties: List[uuid.UUID] = []  # Healthcare providers
    consent_method: str = Field(..., pattern="^(WRITTEN|VERBAL|ELECTRONIC|IMPLIED)$")
    witness: Optional[str] = None
    created_at: datetime
    last_updated: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Role-Permission Matrix for Enterprise Healthcare Operations
ROLE_PERMISSION_MATRIX: Dict[UserRole, RolePermissionMapping] = {
    # Physician Roles - Full clinical access with appropriate restrictions
    UserRole.PHYSICIAN: RolePermissionMapping(
        role=UserRole.PHYSICIAN,
        permissions=[
            Permission.PATIENT_READ_ALL, Permission.PATIENT_UPDATE,
            Permission.PHI_READ_DEMOGRAPHICS, Permission.PHI_READ_CONTACT,
            Permission.PHI_READ_CLINICAL, Permission.PHI_READ_MEDICATIONS,
            Permission.PHI_READ_LABS, Permission.PHI_READ_IMAGING,
            Permission.PHI_READ_VITALS, Permission.CLINICAL_NOTES_CREATE,
            Permission.CLINICAL_NOTES_READ, Permission.CLINICAL_NOTES_UPDATE,
            Permission.CLINICAL_NOTES_SIGN, Permission.ORDERS_CREATE,
            Permission.ORDERS_READ, Permission.ORDERS_MODIFY,
            Permission.RESULTS_READ, Permission.RESULTS_RELEASE,
            Permission.PRESCRIPTIONS_CREATE, Permission.PRESCRIPTIONS_READ,
            Permission.PRESCRIPTIONS_MODIFY, Permission.PRESCRIPTIONS_CANCEL
        ],
        data_classification_access=[
            DataClassificationLevel.PUBLIC, DataClassificationLevel.INTERNAL,
            DataClassificationLevel.CONFIDENTIAL, DataClassificationLevel.RESTRICTED
        ],
        contexts=[AccessContext.DIRECT_CARE, AccessContext.CARE_COORDINATION],
        requires_mfa=True,
        max_session_duration=480,
        emergency_access=True
    ),
    
    # Nurse Roles - Clinical access with appropriate scope
    UserRole.REGISTERED_NURSE: RolePermissionMapping(
        role=UserRole.REGISTERED_NURSE,
        permissions=[
            Permission.PATIENT_READ_ASSIGNED, Permission.PATIENT_UPDATE,
            Permission.PHI_READ_DEMOGRAPHICS, Permission.PHI_READ_CONTACT,
            Permission.PHI_READ_CLINICAL, Permission.PHI_READ_MEDICATIONS,
            Permission.PHI_READ_VITALS, Permission.CLINICAL_NOTES_CREATE,
            Permission.CLINICAL_NOTES_READ, Permission.ORDERS_READ,
            Permission.RESULTS_READ
        ],
        data_classification_access=[
            DataClassificationLevel.PUBLIC, DataClassificationLevel.INTERNAL,
            DataClassificationLevel.CONFIDENTIAL, DataClassificationLevel.RESTRICTED
        ],
        contexts=[AccessContext.DIRECT_CARE, AccessContext.CARE_COORDINATION],
        requires_mfa=True,
        max_session_duration=360
    ),
    
    # Administrative Roles - System access with segregation of duties
    UserRole.SUPER_ADMIN: RolePermissionMapping(
        role=UserRole.SUPER_ADMIN,
        permissions=[
            Permission.USER_MANAGEMENT, Permission.ROLE_MANAGEMENT,
            Permission.SYSTEM_CONFIG, Permission.AUDIT_READ,
            Permission.AUDIT_EXPORT, Permission.COMPLIANCE_REPORT
        ],
        data_classification_access=[DataClassificationLevel.TOP_SECRET],
        contexts=[AccessContext.AUDIT],
        requires_mfa=True,
        max_session_duration=120  # Shorter sessions for admin roles
    ),
    
    # Patient Role - Own data access only
    UserRole.PATIENT: RolePermissionMapping(
        role=UserRole.PATIENT,
        permissions=[
            Permission.PATIENT_READ_OWN, Permission.PHI_READ_DEMOGRAPHICS,
            Permission.PHI_READ_CONTACT, Permission.PHI_READ_CLINICAL,
            Permission.PHI_READ_MEDICATIONS, Permission.PHI_READ_LABS,
            Permission.PHI_READ_IMAGING, Permission.PHI_READ_VITALS,
            Permission.RESULTS_READ
        ],
        data_classification_access=[DataClassificationLevel.RESTRICTED],
        contexts=[AccessContext.DIRECT_CARE],
        requires_mfa=False,
        max_session_duration=240
    )
}