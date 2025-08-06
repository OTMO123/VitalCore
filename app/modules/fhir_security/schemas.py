"""
FHIR Security Schemas for Healthcare Platform V2.0

Data models and schemas for enhanced FHIR security labels, consent management,
access control, and provenance tracking with SOC2/HIPAA compliance.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid


class SecurityClassification(str, Enum):
    """FHIR security classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


class ConsentStatus(str, Enum):
    """Consent status values."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROPOSED = "proposed"
    REJECTED = "rejected"
    ENTERED_IN_ERROR = "entered-in-error"


class AccessCategory(str, Enum):
    """Access category classifications."""
    TREATMENT = "treatment"
    PAYMENT = "payment"
    OPERATIONS = "operations"
    RESEARCH = "research"
    EMERGENCY = "emergency"
    DISCLOSURE = "disclosure"


class AccessType(str, Enum):
    """FHIR resource access types."""
    READ = "read"
    WRITE = "write"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    HISTORY = "history"


class SecurityLabelCategory(str, Enum):
    """Security label categories."""
    CONFIDENTIALITY = "confidentiality"
    INTEGRITY = "integrity"
    HANDLING = "handling"
    COMPARTMENT = "compartment"
    PURPOSE = "purpose"


class ProvenanceAction(str, Enum):
    """Provenance action types."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    ACCESS = "access"
    TRANSFORM = "transform"
    SIGN = "sign"
    VERIFY = "verify"


class EncryptionAlgorithm(str, Enum):
    """Supported encryption algorithms."""
    AES_256_GCM = "AES-256-GCM"
    AES_256_CBC = "AES-256-CBC"
    CHACHA20_POLY1305 = "ChaCha20-Poly1305"
    RSA_OAEP = "RSA-OAEP"


class SecurityLabel(BaseModel):
    """FHIR security label implementation."""
    
    label_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    system: str = Field(..., description="Coding system URI")
    code: str = Field(..., description="Security label code")
    display: str = Field(..., description="Human-readable display")
    category: SecurityLabelCategory
    classification: SecurityClassification
    handling_caveats: List[str] = Field(default_factory=list)
    access_restrictions: List[str] = Field(default_factory=list)
    retention_period: Optional[int] = Field(None, description="Retention period in days")
    geographical_restrictions: List[str] = Field(default_factory=list)
    purpose_limitations: List[str] = Field(default_factory=list)
    created_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('retention_period')
    def validate_retention_period(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Retention period must be positive')
        return v


class ConsentPolicy(BaseModel):
    """Consent policy configuration."""
    
    policy_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    policy_name: str
    policy_version: str = "1.0"
    purpose_codes: List[str]
    data_categories: List[str]
    access_categories: List[AccessCategory]
    retention_period_days: int = Field(ge=1, le=365*10)  # Max 10 years
    geographical_restrictions: List[str] = Field(default_factory=list)
    requires_explicit_consent: bool = True
    allows_data_sharing: bool = False
    allows_research_use: bool = False
    allows_commercial_use: bool = False
    minimum_age_requirement: Optional[int] = None
    special_populations_handling: List[str] = Field(default_factory=list)
    withdrawal_procedures: List[str] = Field(default_factory=list)
    created_timestamp: datetime = Field(default_factory=datetime.utcnow)
    effective_date: datetime = Field(default_factory=datetime.utcnow)
    expiry_date: Optional[datetime] = None
    
    @validator('retention_period_days')
    def validate_retention_period(cls, v):
        if v > 365 * 10:  # 10 years max
            raise ValueError('Retention period cannot exceed 10 years')
        return v


class ConsentContext(BaseModel):
    """Consent context for data access."""
    
    context_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    consent_id: str
    consent_status: ConsentStatus
    granted_purposes: List[str]
    granted_data_categories: List[str]
    granted_access_types: List[AccessType]
    restrictions: List[str] = Field(default_factory=list)
    conditions: List[str] = Field(default_factory=list)
    consent_date: datetime
    expiry_date: datetime
    last_verified: datetime = Field(default_factory=datetime.utcnow)
    verification_method: str = "digital_signature"
    witness_information: Optional[Dict[str, Any]] = None
    withdrawal_date: Optional[datetime] = None
    withdrawal_reason: Optional[str] = None


class UserContext(BaseModel):
    """User context for access control."""
    
    user_id: str
    user_role: str
    organization_id: str
    department: Optional[str] = None
    access_scopes: List[str]
    security_clearance: SecurityClassification
    consent_agreements: List[str] = Field(default_factory=list)
    session_id: str
    authentication_method: str = "multi_factor"
    login_timestamp: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_id: Optional[str] = None
    geographic_location: Optional[str] = None


class ResourceAccess(BaseModel):
    """Resource access tracking."""
    
    access_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    resource_type: str
    resource_id: str
    access_type: AccessType
    access_timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_context: UserContext
    access_purpose: str
    data_elements_accessed: List[str] = Field(default_factory=list)
    access_duration_seconds: Optional[int] = None
    bytes_transferred: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    compliance_flags: List[str] = Field(default_factory=list)


class AccessDecision(BaseModel):
    """Access control decision."""
    
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision: str = Field(..., regex="^(allow|deny|conditional)$")
    reasoning: str
    required_conditions: List[str] = Field(default_factory=list)
    access_level: str = Field(..., regex="^(full|restricted|read_only|emergency)$")
    security_warnings: List[str] = Field(default_factory=list)
    policy_violations: List[str] = Field(default_factory=list)
    decision_timestamp: datetime = Field(default_factory=datetime.utcnow)
    decision_validity_seconds: int = 300  # 5 minutes default
    reviewer_required: bool = False
    emergency_override: bool = False
    audit_level: str = "standard"


class ProvenanceRecord(BaseModel):
    """Provenance record for resource tracking."""
    
    provenance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_resource_type: str
    target_resource_id: str
    action: ProvenanceAction
    action_timestamp: datetime = Field(default_factory=datetime.utcnow)
    recorded_timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_id: str
    agent_name: str
    agent_role: str
    agent_organization: str
    activity_code: str
    activity_display: str
    location: Optional[str] = None
    reason: Optional[str] = None
    digital_signature: Optional[str] = None
    signature_algorithm: Optional[str] = None
    witness_signatures: List[Dict[str, Any]] = Field(default_factory=list)
    related_provenance: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EncryptionMetadata(BaseModel):
    """Encryption metadata for FHIR resources."""
    
    encryption_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    resource_id: str
    resource_type: str
    encrypted_elements: List[str]
    encryption_algorithm: EncryptionAlgorithm
    key_id: str
    key_derivation_method: str = "PBKDF2"
    initialization_vector: str
    authentication_tag: str
    encrypted_timestamp: datetime = Field(default_factory=datetime.utcnow)
    encryption_purpose: str
    key_rotation_date: Optional[datetime] = None
    decryption_authorized_roles: List[str] = Field(default_factory=list)
    encryption_policy_version: str = "1.0"


class DigitalSignature(BaseModel):
    """Digital signature for FHIR resources."""
    
    signature_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    resource_id: str
    resource_type: str
    signature_value: str
    signature_algorithm: str = "RS256"
    certificate_thumbprint: str
    certificate_chain: List[str] = Field(default_factory=list)
    signing_timestamp: datetime = Field(default_factory=datetime.utcnow)
    signer_id: str
    signer_name: str
    signer_role: str
    signing_purpose: str
    signature_policy: str
    verification_status: Optional[str] = None
    verification_timestamp: Optional[datetime] = None
    revocation_status: Optional[str] = None


class ComplianceResult(BaseModel):
    """Compliance validation result."""
    
    compliance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    resource_id: str
    resource_type: str
    compliant: bool
    compliance_score: float = Field(ge=0.0, le=1.0)
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    compliance_standards: List[str] = Field(default_factory=list)
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    validator_id: str
    policy_version: str
    remediation_required: bool = False
    remediation_deadline: Optional[datetime] = None
    compliance_level: str = Field(..., regex="^(full|partial|non_compliant|under_review)$")


class SecurityAuditEvent(BaseModel):
    """Security audit event for FHIR operations."""
    
    audit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    event_subtype: Optional[str] = None
    severity: str = Field(..., regex="^(info|warning|error|critical)$")
    source_system: str = "FHIR_Security_Module"
    event_timestamp: datetime = Field(default_factory=datetime.utcnow)
    recorded_timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_context: Optional[UserContext] = None
    resource_access: Optional[ResourceAccess] = None
    security_labels: List[SecurityLabel] = Field(default_factory=list)
    access_decision: Optional[AccessDecision] = None
    compliance_result: Optional[ComplianceResult] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    event_details: Dict[str, Any] = Field(default_factory=dict)
    outcome: str = Field(..., regex="^(success|failure|partial|unknown)$")
    outcome_description: Optional[str] = None


class FHIRSecurityConfig(BaseModel):
    """Configuration for FHIR security implementation."""
    
    # Security settings
    enable_security_labels: bool = True
    require_consent_validation: bool = True
    enable_encryption: bool = True
    enable_digital_signatures: bool = True
    enable_access_control: bool = True
    
    # Audit settings
    audit_all_access: bool = True
    audit_retention_days: int = Field(default=2555, ge=1, le=3650)  # 7 years max
    enable_detailed_logging: bool = True
    audit_compression_enabled: bool = True
    
    # Consent settings
    default_consent_period_days: int = Field(default=365, ge=1, le=3650)
    require_explicit_consent: bool = True
    granular_consent_enabled: bool = True
    consent_withdrawal_grace_period_hours: int = 24
    
    # Encryption settings
    default_encryption_algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM
    key_rotation_period_days: int = Field(default=90, ge=1, le=365)
    encryption_key_length: int = Field(default=256, ge=128, le=512)
    
    # Access control settings
    enable_rbac: bool = True
    enable_abac: bool = True
    enable_purpose_limitation: bool = True
    access_decision_cache_ttl_seconds: int = Field(default=300, ge=60, le=3600)
    emergency_access_enabled: bool = True
    break_glass_audit_required: bool = True
    
    # Performance settings
    cache_consent_decisions: bool = True
    cache_ttl_minutes: int = Field(default=60, ge=1, le=1440)
    batch_audit_events: bool = True
    batch_size: int = Field(default=100, ge=1, le=1000)
    
    # Compliance settings
    hipaa_compliance_enabled: bool = True
    gdpr_compliance_enabled: bool = True
    soc2_compliance_enabled: bool = True
    fhir_version: str = "R4"
    security_framework_version: str = "2.0"


class SecurityLabelRequest(BaseModel):
    """Request for applying security labels."""
    
    resource_type: str
    resource_id: str
    sensitivity_level: str
    classification_reason: Optional[str] = None
    handling_instructions: List[str] = Field(default_factory=list)
    access_restrictions: List[str] = Field(default_factory=list)
    requester_id: str
    business_justification: str


class ConsentRequest(BaseModel):
    """Request for consent validation."""
    
    patient_id: str
    requesting_user_id: str
    purpose: str
    data_categories: List[str]
    access_duration_hours: int = Field(default=24, ge=1, le=8760)  # Max 1 year
    urgency_level: str = Field(default="normal", regex="^(normal|urgent|emergency)$")
    clinical_justification: Optional[str] = None


class AccessRequest(BaseModel):
    """Request for resource access."""
    
    resource_type: str
    resource_id: str
    access_type: AccessType
    user_context: UserContext
    purpose: str
    duration_hours: int = Field(default=1, ge=1, le=24)
    emergency_access: bool = False
    break_glass_reason: Optional[str] = None
    supervisor_approval: Optional[str] = None


class SecurityReport(BaseModel):
    """Security compliance and audit report."""
    
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_type: str = Field(..., regex="^(compliance|audit|security|breach)$")
    report_period_start: datetime
    report_period_end: datetime
    generated_timestamp: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str
    
    # Summary metrics
    total_access_events: int = 0
    compliant_access_events: int = 0
    non_compliant_access_events: int = 0
    security_violations: int = 0
    consent_violations: int = 0
    
    # Detailed findings
    compliance_results: List[ComplianceResult] = Field(default_factory=list)
    security_events: List[SecurityAuditEvent] = Field(default_factory=list)
    access_decisions: List[AccessDecision] = Field(default_factory=list)
    
    # Recommendations
    security_recommendations: List[str] = Field(default_factory=list)
    policy_updates_required: List[str] = Field(default_factory=list)
    training_requirements: List[str] = Field(default_factory=list)
    
    # Compliance status
    overall_compliance_score: float = Field(ge=0.0, le=1.0)
    hipaa_compliance_score: float = Field(ge=0.0, le=1.0)
    gdpr_compliance_score: float = Field(ge=0.0, le=1.0)
    soc2_compliance_score: float = Field(ge=0.0, le=1.0)


class BreachNotification(BaseModel):
    """Security breach notification."""
    
    breach_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    severity: str = Field(..., regex="^(low|medium|high|critical)$")
    breach_type: str
    discovery_timestamp: datetime = Field(default_factory=datetime.utcnow)
    breach_timestamp: Optional[datetime] = None
    affected_resources: List[str] = Field(default_factory=list)
    affected_patients: List[str] = Field(default_factory=list)
    data_elements_involved: List[str] = Field(default_factory=list)
    breach_description: str
    root_cause: Optional[str] = None
    immediate_actions_taken: List[str] = Field(default_factory=list)
    notification_required: bool = True
    notification_deadline: Optional[datetime] = None
    regulatory_reporting_required: bool = False
    estimated_impact: str
    mitigation_plan: List[str] = Field(default_factory=list)
    lessons_learned: List[str] = Field(default_factory=list)
    
    discovered_by: str
    investigation_lead: str
    notification_status: str = "pending"
    resolution_status: str = "investigating"