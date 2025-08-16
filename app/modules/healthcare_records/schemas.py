"""
Healthcare Records Schemas

Pydantic schemas for the Healthcare Records bounded context, implementing
FHIR R4 compliance and PHI/PII data structures.
"""

from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
from uuid import UUID, uuid4

from app.core.database_unified import DataClassification


class ConsentStatus(str, Enum):
    """Patient consent status for data usage."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    WITHDRAWN = "withdrawn"
    PENDING = "pending"
    EXPIRED = "expired"


class ConsentType(str, Enum):
    """Types of consent."""
    TREATMENT = "treatment"
    RESEARCH = "research"
    MARKETING = "marketing"
    DATA_SHARING = "data_sharing"
    DATA_ACCESS = "data_access"
    DATA_DELETION = "data_deletion"
    EMERGENCY_ACCESS = "emergency_access"
    IMMUNIZATION_REGISTRY = "immunization_registry"


class PHIFieldType(str, Enum):
    """Types of PHI fields for encryption."""
    SSN = "ssn"
    MRN = "mrn"
    DOB = "dob"
    PHONE = "phone"
    EMAIL = "email"
    ADDRESS = "address"
    NAME = "name"


class DocumentType(str, Enum):
    """Clinical document types."""
    IMMUNIZATION_RECORD = "immunization_record"
    CLINICAL_NOTE = "clinical_note"
    LAB_RESULT = "lab_result"
    DISCHARGE_SUMMARY = "discharge_summary"
    CONSENT_FORM = "consent_form"


class FHIRResource(BaseModel):
    """Base FHIR R4 resource structure."""
    resourceType: str
    id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    identifier: Optional[List[Dict[str, Any]]] = None
    active: Optional[bool] = True


# Patient Aggregate Schemas

class PatientIdentifier(BaseModel):
    """Patient identifier structure."""
    use: str = Field(default="official", description="Identifier use (official, temp, secondary)")
    type: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}]
        }, 
        description="Identifier type coding"
    )
    system: str = Field(default="http://hospital.smarthit.org", description="Identifier system URI")
    value: str = Field(..., description="Identifier value (will be encrypted)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "use": "official",
                "type": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}]
                },
                "system": "http://hospital.smarthit.org",
                "value": "MRN123456789"
            }
        }
    }


class PatientName(BaseModel):
    """Patient name structure (encrypted)."""
    use: str = Field(default="official", description="Name use")
    family: str = Field(..., description="Family name (encrypted)")
    given: List[str] = Field(..., description="Given names (encrypted)")
    prefix: Optional[List[str]] = Field(None, description="Name prefix")
    suffix: Optional[List[str]] = Field(None, description="Name suffix")


class PatientAddress(BaseModel):
    """Patient address structure (encrypted)."""
    use: str = Field(default="home", description="Address use")
    type: str = Field(default="physical", description="Address type")
    line: List[str] = Field(..., description="Street address lines (encrypted)")
    city: str = Field(..., description="City (encrypted)")
    state: str = Field(..., description="State/Province (encrypted)")
    postalCode: str = Field(..., description="Postal code (encrypted)")
    country: str = Field(..., description="Country")


class PatientContact(BaseModel):
    """Patient contact information (encrypted)."""
    relationship: Optional[List[Dict[str, Any]]] = Field(None, description="Contact relationship")
    name: Optional[PatientName] = Field(None, description="Contact name")
    telecom: Optional[List[Dict[str, Any]]] = Field(None, description="Contact telecoms")
    address: Optional[PatientAddress] = Field(None, description="Contact address")


class PatientCreate(BaseModel):
    """Schema for creating a new patient."""
    identifier: List[PatientIdentifier] = Field(..., description="Patient identifiers")
    active: bool = Field(default=True, description="Patient record is active")
    name: List[PatientName] = Field(..., description="Patient names")
    telecom: Optional[List[Dict[str, Any]]] = Field(None, description="Contact details")
    gender: Optional[str] = Field(None, description="Administrative gender")
    birthDate: Optional[date] = Field(None, description="Date of birth (encrypted)")
    address: Optional[List[PatientAddress]] = Field(None, description="Patient addresses")
    contact: Optional[List[PatientContact]] = Field(None, description="Patient contacts")
    generalPractitioner: Optional[List[Dict[str, Any]]] = Field(None, description="GP references")
    
    # Consent information
    consent_status: ConsentStatus = Field(default=ConsentStatus.PENDING)
    consent_types: List[ConsentType] = Field(default_factory=list)
    
    # Metadata
    organization_id: Optional[UUID] = Field(
        default=None, 
        description="Organization this patient belongs to"
    )
    
    @field_validator('identifier')
    @classmethod
    def validate_identifier(cls, v):
        if not v:
            raise ValueError("At least one identifier is required")
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v:
            raise ValueError("At least one name is required")
        return v


class PatientUpdate(BaseModel):
    """Schema for updating a patient."""
    active: Optional[bool] = None
    name: Optional[List[PatientName]] = None
    telecom: Optional[List[Dict[str, Any]]] = None
    gender: Optional[str] = None
    birthDate: Optional[date] = None
    address: Optional[List[PatientAddress]] = None
    contact: Optional[List[PatientContact]] = None
    
    # Consent updates
    consent_status: Optional[ConsentStatus] = None
    consent_types: Optional[List[ConsentType]] = None


class PatientResponse(FHIRResource):
    """Schema for patient response (with encrypted fields marked)."""
    resourceType: str = Field(default="Patient")
    id: str
    identifier: List[PatientIdentifier]
    active: bool
    name: List[PatientName]  # Encrypted
    telecom: Optional[List[Dict[str, Any]]] = None  # Encrypted
    gender: Optional[str] = None
    birthDate: Optional[date] = None  # Encrypted
    address: Optional[List[PatientAddress]] = None  # Encrypted
    contact: Optional[List[PatientContact]] = None  # Encrypted
    
    # Consent information
    consent_status: ConsentStatus
    consent_types: List[ConsentType]
    
    # Metadata
    organization_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class PatientListResponse(BaseModel):
    """Paginated response for patient list endpoints."""
    patients: List[PatientResponse]
    total: int = Field(..., description="Total number of patients matching criteria")
    limit: int = Field(..., description="Maximum number of patients returned")
    offset: int = Field(..., description="Number of patients skipped")


# Clinical Document Aggregate Schemas

class DocumentMetadata(BaseModel):
    """Clinical document metadata."""
    title: str = Field(..., description="Document title")
    type: DocumentType = Field(..., description="Document type")
    status: str = Field(default="final", description="Document status")
    category: List[Dict[str, Any]] = Field(..., description="Document category")
    subject: str = Field(..., description="Patient reference")
    author: List[str] = Field(..., description="Document authors")
    created: datetime = Field(..., description="Creation timestamp")
    
    # Classification and security
    classification: DataClassification = Field(default=DataClassification.PHI)
    confidentiality: str = Field(default="R", description="Confidentiality level")


class ClinicalDocumentCreate(BaseModel):
    """Schema for creating a clinical document."""
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    content: str = Field(..., description="Document content (will be encrypted)")
    content_type: str = Field(default="text/plain", description="Content MIME type")
    
    # FHIR specific
    patient_id: UUID = Field(..., description="Patient this document belongs to")
    encounter_id: Optional[UUID] = Field(None, description="Associated encounter")
    
    # Access control
    access_level: str = Field(default="restricted", description="Access level")
    authorized_roles: List[str] = Field(default_factory=list, description="Authorized roles")
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Document content cannot be empty")
        return v


class ClinicalDocumentUpdate(BaseModel):
    """Schema for updating a clinical document."""
    metadata: Optional[DocumentMetadata] = None
    content: Optional[str] = None
    content_type: Optional[str] = None
    access_level: Optional[str] = None
    authorized_roles: Optional[List[str]] = None


class ClinicalDocumentResponse(BaseModel):
    """Schema for clinical document response."""
    id: UUID
    metadata: DocumentMetadata
    content_encrypted: bool = Field(description="Whether content is encrypted")
    content_hash: str = Field(description="Content hash for integrity")
    content_type: str
    
    # Patient and encounter
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    
    # Access control
    access_level: str
    authorized_roles: List[str]
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    
    model_config = {"from_attributes": True}


# Consent Management Schemas

class ConsentRequest(BaseModel):
    """Schema for consent requests."""
    patient_id: UUID = Field(..., description="Patient ID")
    consent_types: List[ConsentType] = Field(..., description="Types of consent")
    status: ConsentStatus = Field(default=ConsentStatus.ACTIVE)
    effective_period_start: datetime = Field(..., description="Consent start date")
    effective_period_end: Optional[datetime] = Field(None, description="Consent end date")
    
    # Consent details
    purpose: List[str] = Field(..., description="Purpose of consent")
    data_types: List[str] = Field(..., description="Types of data covered")
    
    # Legal
    legal_basis: str = Field(..., description="Legal basis for processing")
    witness_signature: Optional[str] = Field(None, description="Witness signature")
    
    @field_validator('consent_types')
    @classmethod
    def validate_consent_types(cls, v):
        if not v:
            raise ValueError("At least one consent type is required")
        return v


class ConsentResponse(BaseModel):
    """Schema for consent response."""
    id: UUID
    patient_id: UUID
    consent_types: List[ConsentType]
    status: ConsentStatus
    effective_period_start: datetime
    effective_period_end: Optional[datetime] = None
    
    # Consent details
    purpose: List[str]
    data_types: List[str]
    legal_basis: str
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    
    model_config = {"from_attributes": True}


# PHI Access Management Schemas

class PHIAccessRequest(BaseModel):
    """Schema for PHI access requests."""
    patient_id: UUID = Field(..., description="Patient ID")
    requested_fields: List[PHIFieldType] = Field(..., description="Requested PHI fields")
    access_purpose: str = Field(..., description="Purpose of access")
    requester_role: str = Field(..., description="Role of requester")
    
    # Legal and compliance
    legal_basis: str = Field(..., description="Legal basis for access")
    retention_period: Optional[int] = Field(None, description="Days to retain access")
    
    @field_validator('requested_fields')
    @classmethod
    def validate_requested_fields(cls, v):
        if not v:
            raise ValueError("At least one PHI field must be requested")
        return v


class PHIAccessResponse(BaseModel):
    """Schema for PHI access response."""
    id: UUID
    patient_id: UUID
    requested_fields: List[PHIFieldType]
    access_purpose: str
    requester_id: UUID
    requester_role: str
    
    # Access details
    granted: bool
    granted_fields: List[PHIFieldType]
    access_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    # Audit
    created_at: datetime
    accessed_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


# Bulk Operations

class BulkPatientCreate(BaseModel):
    """Schema for bulk patient creation."""
    patients: List[PatientCreate] = Field(..., description="List of patients to create")
    
    @field_validator('patients')
    @classmethod
    def validate_patients(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one patient is required")
        if len(v) > 1000:
            raise ValueError("Maximum 1000 patients per bulk operation")
        return v


class BulkOperationResponse(BaseModel):
    """Schema for bulk operation responses."""
    operation_id: UUID
    total_records: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime] = None


# FHIR Validation Schemas - NOTE: Main definition moved below to resolve import order


class FHIRValidationSeverity(str, Enum):
    """FHIR validation issue severity levels."""
    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFORMATION = "information"


class FHIRValidationIssue(BaseModel):
    """FHIR validation issue details."""
    severity: FHIRValidationSeverity
    code: str = Field(..., description="Issue code")
    diagnostics: Optional[str] = Field(None, description="Additional diagnostic information")
    location: Optional[List[str]] = Field(None, description="Path to the issue location")
    expression: Optional[List[str]] = Field(None, description="FHIRPath expression")


class FHIRValidationResponse(BaseModel):
    """Response schema for FHIR resource validation with SOC2/HIPAA compliance."""
    is_valid: bool = Field(..., description="Overall validation result - explicit naming for compliance")
    resource_type: str = Field(..., description="Type of FHIR resource validated")
    issues: List[FHIRValidationIssue] = Field(default_factory=list, description="Validation issues")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    compliance_score: Optional[float] = Field(None, description="Compliance score (0-100)")
    
    # Validation metadata
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    validation_duration_ms: Optional[int] = Field(None, description="Validation duration in milliseconds")
    profile_validated: Optional[str] = Field(None, description="Profile used for validation")
    
    # Enterprise compliance fields
    security_labels: Optional[List[str]] = Field(default_factory=list, description="Security classification labels")
    audit_trail_id: Optional[str] = Field(None, description="Audit trail identifier for compliance tracking")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "is_valid": True,
                "resource_type": "Patient",
                "issues": [],
                "warnings": [],
                "compliance_score": 95.5,
                "validated_at": "2024-01-01T00:00:00Z",
                "validation_duration_ms": 150,
                "profile_validated": "http://hl7.org/fhir/StructureDefinition/Patient",
                "security_labels": ["PHI", "CONFIDENTIAL"],
                "audit_trail_id": "audit-12345-abcd"
            }
        }
    }


# FHIR Bundle Schemas
class FHIRBundleRequest(BaseModel):
    """Schema for FHIR bundle requests."""
    bundle_type: str = Field(..., description="FHIR bundle type (transaction, batch, collection)")
    bundle_data: Dict[str, Any] = Field(..., description="Complete FHIR Bundle resource structure")
    validate_resources: bool = Field(default=True, description="Whether to validate individual resources")
    process_atomically: bool = Field(default=True, description="Whether to process the entire bundle atomically")
    
    @field_validator('bundle_type')
    @classmethod
    def validate_bundle_type(cls, v):
        valid_types = ['transaction', 'batch', 'collection', 'searchset', 'history']
        if v not in valid_types:
            raise ValueError(f"Bundle type must be one of {valid_types}")
        return v
    
    @field_validator('bundle_data')
    @classmethod
    def validate_bundle_data(cls, v):
        if not v:
            raise ValueError("Bundle data cannot be empty")
        
        # Validate FHIR Bundle structure
        if v.get('resourceType') != 'Bundle':
            raise ValueError("Bundle data must have resourceType 'Bundle'")
        
        if 'type' not in v:
            raise ValueError("Bundle must have a type field")
        
        if 'entry' not in v or not v['entry']:
            raise ValueError("Bundle must contain at least one entry")
        
        if len(v['entry']) > 1000:
            raise ValueError("Maximum 1000 entries per bundle")
        
        return v


class FHIRBundleResponse(BaseModel):
    """Schema for FHIR bundle responses."""
    resourceType: str = Field(default="Bundle", description="FHIR resource type")
    id: Optional[str] = Field(None, description="Bundle resource ID (FHIR compliance)")
    bundle_id: str = Field(..., description="Generated bundle ID")
    bundle_type: str = Field(..., description="FHIR bundle type")
    type: Optional[str] = Field(None, description="FHIR Bundle type field")
    
    # FHIR-compliant and enterprise compliance timestamps
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Bundle processing timestamp (FHIR standard)")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Bundle creation timestamp (SOC2/HIPAA audit)")
    updated_at: Optional[datetime] = Field(None, description="Bundle last update timestamp (SOC2/HIPAA audit)")
    
    total_resources: int = Field(..., description="Total number of resources in bundle")
    processed_resources: int = Field(..., description="Number of successfully processed resources")
    failed_resources: int = Field(..., description="Number of failed resources")
    validation_results: List[FHIRValidationResponse] = Field(default_factory=list, description="Validation results for each resource")
    resource_ids: List[str] = Field(default_factory=list, description="IDs of created/updated resources")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    status: str = Field(..., description="Overall processing status")
    errors: List[str] = Field(default_factory=list, description="Bundle-level errors")
    entry: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="FHIR Bundle entry responses")
    
    model_config = {"populate_by_name": True, "validate_assignment": True}
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['success', 'partial_success', 'failed', 'validation_failed']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v


# Data Anonymization Schemas
class AnonymizationRequest(BaseModel):
    """Schema for data anonymization requests."""
    request_id: str = Field(..., description="Unique request identifier")
    patient_ids: List[str] = Field(..., description="List of patient IDs to anonymize")
    preserve_fields: Optional[List[str]] = Field(default_factory=list, description="Fields to preserve without anonymization")
    batch_size: Optional[int] = Field(None, description="Batch size for processing")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Anonymization configuration")
    
    @field_validator('patient_ids')
    @classmethod
    def validate_patient_ids(cls, v):
        if not v:
            raise ValueError("At least one patient ID is required")
        if len(v) > 10000:
            raise ValueError("Maximum 10,000 patients per anonymization request")
        return v


class AnonymizationResponse(BaseModel):
    """Schema for anonymization responses."""
    request_id: str = Field(..., description="Request identifier")
    status: str = Field(..., description="Processing status")
    message: Optional[str] = Field(None, description="Status message")
    records_processed: Optional[int] = Field(None, description="Number of records processed")
    anonymization_techniques: Optional[List[str]] = Field(default_factory=list, description="Techniques applied")
    quality_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Data quality metrics")


# Update ConsentCreate and ConsentResponse to match expected structure
class ConsentCreate(BaseModel):
    """Schema for creating patient consent."""
    patient_id: UUID = Field(..., description="Patient ID")
    consent_type: str = Field(..., description="Type of consent")
    expires_at: Optional[datetime] = Field(None, description="Consent expiration date")
    scope: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Consent scope")
    
    @field_validator('consent_type')
    @classmethod
    def validate_consent_type(cls, v):
        valid_types = ['treatment', 'research', 'marketing', 'data_sharing', 'data_access']
        if v not in valid_types:
            raise ValueError(f"Consent type must be one of {valid_types}")
        return v


class ConsentUpdate(BaseModel):
    """Schema for updating patient consent."""
    status: Optional[str] = Field(None, description="Updated consent status")
    expires_at: Optional[datetime] = Field(None, description="Updated expiration date")
    scope: Optional[Dict[str, Any]] = Field(None, description="Updated consent scope")


# Update ClinicalDocumentCreate to match expected structure  
class ClinicalDocumentCreate(BaseModel):
    """Schema for creating clinical documents."""
    patient_id: UUID = Field(..., description="Patient ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content (will be encrypted)")
    document_type: str = Field(..., description="Type of clinical document")
    content_type: str = Field(default="text/plain", description="MIME type of content")
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Document content cannot be empty")
        return v


class ClinicalDocumentUpdate(BaseModel):
    """Schema for updating clinical documents."""
    title: Optional[str] = Field(None, description="Updated document title")
    content: Optional[str] = Field(None, description="Updated document content")
    document_type: Optional[str] = Field(None, description="Updated document type")


# Patient Search and Filtering Schemas

class PatientFilters(BaseModel):
    """Schema for patient search filters."""
    gender: Optional[str] = Field(None, description="Filter by gender")
    age_min: Optional[int] = Field(None, ge=0, description="Minimum age filter")
    age_max: Optional[int] = Field(None, le=120, description="Maximum age filter")
    department_id: Optional[str] = Field(None, description="Filter by department ID")
    tenant_id: Optional[str] = Field(None, description="Filter by tenant ID")
    mrn: Optional[str] = Field(None, description="Search by Medical Record Number")
    ssn: Optional[str] = Field(None, description="Search by SSN")


# ============================================
# IMMUNIZATION SCHEMAS
# ============================================

class ImmunizationStatus(str, Enum):
    """FHIR R4 Immunization status values."""
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    NOT_DONE = "not-done"


class VaccineCode(str, Enum):
    """Common vaccine codes from CVX."""
    COVID19_PFIZER = "208"
    COVID19_MODERNA = "207" 
    COVID19_JANSSEN = "212"
    INFLUENZA = "88"
    HEPATITIS_B = "08"
    MMR = "03"
    TDAP = "115"
    HPV = "62"


class ImmunizationCreate(BaseModel):
    """Schema for creating a new immunization record."""
    patient_id: UUID = Field(..., description="Patient ID")
    status: ImmunizationStatus = Field(default=ImmunizationStatus.COMPLETED)
    vaccine_code: str = Field(..., description="CVX vaccine code")
    vaccine_display: Optional[str] = Field(None, description="Human readable vaccine name")
    vaccine_system: str = Field(default="http://hl7.org/fhir/sid/cvx")
    occurrence_datetime: datetime = Field(..., description="When vaccination was performed")
    
    # Location and provider (will be encrypted)
    location: Optional[str] = Field(None, description="Location/clinic name")
    primary_source: bool = Field(default=True)
    
    # Vaccine details (will be encrypted)
    lot_number: Optional[str] = Field(None, description="Vaccine lot number")
    expiration_date: Optional[date] = Field(None, description="Vaccine expiration date")
    manufacturer: Optional[str] = Field(None, description="Manufacturer name")
    
    # Administration details
    route_code: Optional[str] = Field(None, description="Route of administration code")
    route_display: Optional[str] = Field(None, description="Route description")
    site_code: Optional[str] = Field(None, description="Body site code")
    site_display: Optional[str] = Field(None, description="Body site description")
    dose_quantity: Optional[str] = Field(None, description="Dose amount")
    dose_unit: Optional[str] = Field(None, description="Dose unit")
    
    # Provider information (will be encrypted)
    performer_type: Optional[str] = Field(None, description="Type of performer")
    performer_name: Optional[str] = Field(None, description="Performer name")
    performer_organization: Optional[str] = Field(None, description="Organization")
    
    # Clinical information
    indication_codes: Optional[List[str]] = Field(default_factory=list)
    contraindication_codes: Optional[List[str]] = Field(default_factory=list)
    reactions: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    
    # Series completion tracking (enterprise compliance fields)
    series_complete: bool = Field(default=False, description="Whether vaccine series is complete")
    series_dosed: Optional[int] = Field(default=1, description="Number of doses administered in series")
    
    # Metadata
    tenant_id: Optional[UUID] = Field(None, description="Tenant ID")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    
    @field_validator('vaccine_code')
    @classmethod
    def validate_vaccine_code(cls, v):
        if not v:
            raise ValueError("Vaccine code is required")
        return v
    
    @field_validator('occurrence_datetime')
    @classmethod
    def validate_occurrence_datetime(cls, v):
        # Use timezone-aware datetime for comparison to handle both timezone-naive and timezone-aware inputs
        now = datetime.now(timezone.utc)
        
        # If v is timezone-naive, assume UTC for comparison
        if v.tzinfo is None:
            v_utc = v.replace(tzinfo=timezone.utc)
        else:
            v_utc = v
            
        if v_utc > now:
            raise ValueError("Occurrence datetime cannot be in the future")
        return v


class ImmunizationUpdate(BaseModel):
    """Schema for updating an immunization record."""
    status: Optional[ImmunizationStatus] = None
    location: Optional[str] = None
    lot_number: Optional[str] = None
    manufacturer: Optional[str] = None
    route_code: Optional[str] = None
    route_display: Optional[str] = None
    site_code: Optional[str] = None
    site_display: Optional[str] = None
    dose_quantity: Optional[str] = None
    dose_unit: Optional[str] = None
    performer_name: Optional[str] = None
    performer_organization: Optional[str] = None
    reactions: Optional[List[Dict[str, Any]]] = None


class ImmunizationResponse(BaseModel):
    """Schema for immunization response."""
    resourceType: str = Field(default="Immunization")
    id: UUID
    fhir_id: Optional[str] = None
    patient_id: UUID
    status: str
    vaccine_code: str
    vaccine_display: Optional[str] = None
    vaccine_system: str
    occurrence_datetime: datetime
    recorded_date: Optional[datetime] = None
    
    # Administration details
    location: Optional[str] = None  # Decrypted for response
    primary_source: bool
    lot_number: Optional[str] = None  # Decrypted for response
    expiration_date: Optional[date] = None
    manufacturer: Optional[str] = None  # Decrypted for response
    
    route_code: Optional[str] = None
    route_display: Optional[str] = None
    site_code: Optional[str] = None
    site_display: Optional[str] = None
    dose_quantity: Optional[str] = None
    dose_unit: Optional[str] = None
    
    # Provider information (decrypted for response)
    performer_type: Optional[str] = None
    performer_name: Optional[str] = None  # Decrypted for response
    performer_organization: Optional[str] = None  # Decrypted for response
    
    # Clinical information
    indication_codes: List[str] = Field(default_factory=list)
    contraindication_codes: List[str] = Field(default_factory=list)
    reactions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Series completion tracking (enterprise compliance fields)
    series_complete: bool = Field(default=False)
    series_dosed: Optional[int] = Field(default=1)
    
    # Metadata
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: UUID
    
    model_config = {"from_attributes": True}


class ImmunizationListResponse(BaseModel):
    """Paginated response for immunization list endpoints."""
    immunizations: List[ImmunizationResponse]
    total: int = Field(..., description="Total number of immunizations matching criteria")
    limit: int = Field(..., description="Maximum number of immunizations returned")
    offset: int = Field(..., description="Number of immunizations skipped")


class ImmunizationFilters(BaseModel):
    """Schema for immunization search filters."""
    patient_id: Optional[UUID] = Field(None, description="Filter by patient ID")
    vaccine_codes: Optional[List[str]] = Field(None, description="Filter by vaccine codes")
    date_from: Optional[datetime] = Field(None, description="Filter by date range start")
    date_to: Optional[datetime] = Field(None, description="Filter by date range end")
    status_filter: Optional[str] = Field(None, description="Filter by status")
    location: Optional[str] = Field(None, description="Filter by location")
    performer: Optional[str] = Field(None, description="Filter by performer")


# Adverse Reaction Schemas

class ImmunizationReactionCreate(BaseModel):
    """Schema for reporting an adverse reaction."""
    immunization_id: UUID = Field(..., description="Immunization ID")
    reaction_date: Optional[datetime] = Field(None, description="When reaction occurred")
    onset_period: Optional[str] = Field(None, description="Onset period description")
    
    # Clinical manifestation
    manifestation_code: Optional[str] = Field(None, description="Reaction manifestation code")
    manifestation_display: Optional[str] = Field(None, description="Human readable manifestation")
    
    # Severity and outcome
    severity: Optional[str] = Field(None, description="Reaction severity")
    outcome_code: Optional[str] = Field(None, description="Outcome code")
    outcome_display: Optional[str] = Field(None, description="Outcome description")
    
    # Clinical details (will be encrypted)
    description: Optional[str] = Field(None, description="Reaction description")
    treatment: Optional[str] = Field(None, description="Treatment details")
    reported_by: Optional[str] = Field(None, description="Reporter information")


class ImmunizationReactionResponse(BaseModel):
    """Schema for immunization reaction response."""
    id: UUID
    immunization_id: UUID
    reaction_date: Optional[datetime] = None
    onset_period: Optional[str] = None
    manifestation_code: Optional[str] = None
    manifestation_display: Optional[str] = None
    severity: Optional[str] = None
    outcome_code: Optional[str] = None
    outcome_display: Optional[str] = None
    
    # Clinical details (decrypted for response)
    description: Optional[str] = None
    treatment: Optional[str] = None
    reported_by: Optional[str] = None
    
    report_date: Optional[datetime] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


# FHIR Validation Schemas (moved above for proper imports)

class FHIRValidationRequest(BaseModel):
    """Request schema for FHIR resource validation."""
    resource: Dict[str, Any] = Field(..., description="FHIR resource to validate")
    profile: Optional[str] = Field(None, description="FHIR profile URL to validate against")
    terminology_validation: bool = Field(True, description="Enable terminology validation")
    business_rules: bool = Field(True, description="Enable business rules validation")
    security_validation: bool = Field(True, description="Enable security validation")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "resource": {
                    "resourceType": "Patient",
                    "id": "example-patient",
                    "active": True,
                    "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
                    "gender": "male",
                    "birthDate": "1990-01-01"
                },
                "profile": "http://hl7.org/fhir/StructureDefinition/Patient",
                "terminology_validation": True,
                "business_rules": True,
                "security_validation": True
            }
        }
    }


# FHIRValidationResponse definition moved above FHIRBundleResponse for proper imports


# =============================================================================
# FHIR ENTERPRISE RESOURCE SCHEMAS
# =============================================================================

class AppointmentCreate(BaseModel):
    """Schema for creating a new appointment."""
    # FHIR required fields
    status: str = Field(..., description="Appointment status")
    
    # Patient reference (optional for some appointment types)
    patient_id: Optional[UUID] = Field(None, description="Patient ID if patient-specific appointment")
    
    # Timing
    start: Optional[datetime] = Field(None, description="Start time of appointment")
    end: Optional[datetime] = Field(None, description="End time of appointment")
    
    # Details
    appointment_type: Optional[str] = Field(None, description="Type of appointment")
    service_type: Optional[List[str]] = Field(None, description="Service types")
    priority: Optional[int] = Field(None, description="Priority level")
    description: Optional[str] = Field(None, description="Appointment description")
    comment: Optional[str] = Field(None, description="Additional comments")
    participant_instructions: Optional[str] = Field(None, description="Instructions for participants")
    
    # FHIR metadata
    fhir_resource_id: Optional[str] = Field(None, description="FHIR resource ID")


class AppointmentResponse(BaseModel):
    """Schema for appointment response."""
    resourceType: str = Field(default="Appointment")
    id: UUID
    fhir_resource_id: Optional[str] = None
    patient_id: Optional[UUID] = None
    status: str
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    appointment_type: Optional[str] = None
    service_type: Optional[List[str]] = None
    priority: Optional[int] = None
    description: Optional[str] = None
    comment: Optional[str] = None  # Decrypted for response
    participant_instructions: Optional[str] = None  # Decrypted for response
    created_at: datetime
    updated_at: Optional[datetime] = None


class CarePlanCreate(BaseModel):
    """Schema for creating a new care plan."""
    # FHIR required fields
    status: str = Field(..., description="Care plan status")
    intent: str = Field(..., description="Care plan intent")
    patient_id: UUID = Field(..., description="Patient ID")
    
    # Timing
    period_start: Optional[datetime] = Field(None, description="Care plan start date")
    period_end: Optional[datetime] = Field(None, description="Care plan end date")
    
    # Details
    category: Optional[List[str]] = Field(None, description="Care plan categories")
    title: Optional[str] = Field(None, description="Care plan title")
    description: Optional[str] = Field(None, description="Care plan description")
    note: Optional[str] = Field(None, description="Additional notes")
    
    # FHIR metadata
    fhir_resource_id: Optional[str] = Field(None, description="FHIR resource ID")


class CarePlanResponse(BaseModel):
    """Schema for care plan response."""
    resourceType: str = Field(default="CarePlan")
    id: UUID
    fhir_resource_id: Optional[str] = None
    patient_id: UUID
    status: str
    intent: str
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    category: Optional[List[str]] = None
    title: Optional[str] = None
    description: Optional[str] = None  # Decrypted for response
    note: Optional[str] = None  # Decrypted for response
    created_at: datetime
    updated_at: Optional[datetime] = None


class ProcedureCreate(BaseModel):
    """Schema for creating a new procedure."""
    # FHIR required fields
    status: str = Field(..., description="Procedure status")
    patient_id: UUID = Field(..., description="Patient ID")
    
    # Procedure code
    code_system: Optional[str] = Field(None, description="Code system (e.g., SNOMED CT)")
    code_value: Optional[str] = Field(None, description="Procedure code")
    code_display: Optional[str] = Field(None, description="Code display name")
    
    # Timing
    performed_datetime: Optional[datetime] = Field(None, description="When procedure was performed")
    performed_period_start: Optional[datetime] = Field(None, description="Procedure period start")
    performed_period_end: Optional[datetime] = Field(None, description="Procedure period end")
    
    # Details
    category: Optional[List[str]] = Field(None, description="Procedure categories")
    outcome: Optional[str] = Field(None, description="Procedure outcome")
    note: Optional[str] = Field(None, description="Additional notes")
    follow_up: Optional[str] = Field(None, description="Follow-up instructions")
    
    # FHIR metadata
    fhir_resource_id: Optional[str] = Field(None, description="FHIR resource ID")


class ProcedureResponse(BaseModel):
    """Schema for procedure response."""
    resourceType: str = Field(default="Procedure")
    id: UUID
    fhir_resource_id: Optional[str] = None
    patient_id: UUID
    status: str
    code_system: Optional[str] = None
    code_value: Optional[str] = None
    code_display: Optional[str] = None
    performed_datetime: Optional[datetime] = None
    performed_period_start: Optional[datetime] = None
    performed_period_end: Optional[datetime] = None
    category: Optional[List[str]] = None
    outcome: Optional[str] = None
    note: Optional[str] = None  # Decrypted for response
    follow_up: Optional[str] = None  # Decrypted for response
    created_at: datetime
    updated_at: Optional[datetime] = None