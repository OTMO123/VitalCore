"""
Clinical Workflows Schemas

Pydantic schemas for clinical workflow management with comprehensive validation,
FHIR R4 compliance, and security features.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
from uuid import UUID

from app.core.database_unified import DataClassification


class WorkflowType(str, Enum):
    """Clinical workflow types."""
    ENCOUNTER = "encounter"
    CARE_PLAN = "care_plan"
    CONSULTATION = "consultation"
    PROCEDURE = "procedure"
    DISCHARGE = "discharge"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"
    PREVENTIVE_CARE = "preventive_care"


class WorkflowStatus(str, Enum):
    """Workflow status values."""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    ON_HOLD = "on_hold"


class WorkflowPriority(str, Enum):
    """Workflow priority levels."""
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENCY = "emergency"
    STAT = "stat"


class EncounterClass(str, Enum):
    """FHIR R4 Encounter class values."""
    AMBULATORY = "AMB"  # Ambulatory
    EMERGENCY = "EMER"  # Emergency
    INPATIENT = "IMP"   # Inpatient
    HOME_HEALTH = "HH"  # Home Health
    VIRTUAL = "VR"      # Virtual


class EncounterStatus(str, Enum):
    """FHIR R4 Encounter status values."""
    PLANNED = "planned"
    ARRIVED = "arrived"
    TRIAGED = "triaged"
    IN_PROGRESS = "in-progress"
    ON_LEAVE = "onleave"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Workflow step status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class DocumentationQuality(str, Enum):
    """Documentation quality levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    INCOMPLETE = "incomplete"


# Base schemas

class ClinicalWorkflowBase(BaseModel):
    """Base clinical workflow schema."""
    workflow_type: WorkflowType
    priority: WorkflowPriority = WorkflowPriority.ROUTINE
    category: Optional[str] = Field(None, max_length=100)
    
    # Basic clinical content (will be encrypted)
    chief_complaint: Optional[str] = Field(None, description="Patient's primary concern")
    history_present_illness: Optional[str] = Field(None, description="History of present illness")
    
    # Location and context
    location: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=100)
    unit: Optional[str] = Field(None, max_length=100)
    room_number: Optional[str] = Field(None, max_length=50)
    
    # Timing
    estimated_duration_minutes: Optional[int] = Field(None, ge=1, le=1440)  # Max 24 hours
    
    model_config = {
        "use_enum_values": True,
        "json_schema_extra": {
            "example": {
                "workflow_type": "encounter",
                "priority": "routine",
                "chief_complaint": "Chest pain",
                "history_present_illness": "Patient reports chest pain starting 2 hours ago",
                "location": "Emergency Department",
                "department": "Emergency Medicine",
                "estimated_duration_minutes": 60
            }
        }
    }


class SOAPNote(BaseModel):
    """SOAP note structure for clinical documentation."""
    subjective: Optional[str] = Field(None, description="Subjective findings (patient-reported)")
    objective: Optional[str] = Field(None, description="Objective findings (clinical observations)")
    assessment: Optional[str] = Field(None, description="Clinical assessment and diagnosis")
    plan: Optional[str] = Field(None, description="Treatment plan and next steps")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "subjective": "Patient reports chest pain, 7/10 severity, radiating to left arm",
                "objective": "BP 140/90, HR 95, RR 18, O2 98%. Chest clear to auscultation",
                "assessment": "Chest pain, rule out acute coronary syndrome",
                "plan": "EKG, cardiac enzymes, chest X-ray. Monitor in ED"
            }
        }
    }


class VitalSigns(BaseModel):
    """Structured vital signs data."""
    systolic_bp: Optional[int] = Field(None, ge=50, le=300, description="Systolic blood pressure")
    diastolic_bp: Optional[int] = Field(None, ge=30, le=200, description="Diastolic blood pressure")
    heart_rate: Optional[int] = Field(None, ge=20, le=250, description="Heart rate (bpm)")
    respiratory_rate: Optional[int] = Field(None, ge=5, le=60, description="Respiratory rate")
    temperature: Optional[float] = Field(None, ge=90.0, le=110.0, description="Temperature (F)")
    oxygen_saturation: Optional[int] = Field(None, ge=70, le=100, description="O2 saturation (%)")
    weight_kg: Optional[float] = Field(None, ge=0.5, le=500.0, description="Weight in kg")
    height_cm: Optional[float] = Field(None, ge=30.0, le=250.0, description="Height in cm")
    bmi: Optional[float] = Field(None, ge=10.0, le=100.0, description="Body Mass Index")
    pain_score: Optional[int] = Field(None, ge=0, le=10, description="Pain scale 0-10")
    
    @model_validator(mode='after')
    def validate_blood_pressure(self):
        """Validate blood pressure values."""
        if self.systolic_bp and self.diastolic_bp:
            if self.systolic_bp <= self.diastolic_bp:
                raise ValueError("Systolic BP must be greater than diastolic BP")
        return self
    
    @model_validator(mode='after')
    def calculate_bmi(self):
        """Auto-calculate BMI if weight and height provided."""
        if self.weight_kg and self.height_cm and not self.bmi:
            height_m = self.height_cm / 100
            self.bmi = round(self.weight_kg / (height_m ** 2), 1)
        return self


class ClinicalCode(BaseModel):
    """Clinical coding structure (ICD-10, CPT, SNOMED)."""
    code: str = Field(..., description="Clinical code")
    display: str = Field(..., description="Human-readable description")
    system: str = Field(..., description="Coding system URI")
    version: Optional[str] = Field(None, description="Code system version")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "code": "R06.02",
                "display": "Shortness of breath",
                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                "version": "2024"
            }
        }
    }


# Create schemas

class ClinicalWorkflowCreate(ClinicalWorkflowBase):
    """Schema for creating a new clinical workflow."""
    patient_id: UUID = Field(..., description="Patient UUID")
    provider_id: Optional[UUID] = Field(None, description="Primary provider UUID")
    organization_id: Optional[UUID] = Field(None, description="Organization UUID")
    
    # Extended clinical content
    review_of_systems: Optional[str] = Field(None, description="Review of systems")
    physical_examination: Optional[str] = Field(None, description="Physical examination findings")
    assessment: Optional[str] = Field(None, description="Clinical assessment")
    plan: Optional[str] = Field(None, description="Treatment plan")
    
    # Structured data
    vital_signs: Optional[VitalSigns] = None
    allergies: Optional[List[str]] = Field(None, description="Known allergies")
    current_medications: Optional[List[str]] = Field(None, description="Current medications")
    diagnosis_codes: Optional[List[ClinicalCode]] = Field(None, description="ICD-10 diagnosis codes")
    procedure_codes: Optional[List[ClinicalCode]] = Field(None, description="CPT procedure codes")
    
    # Clinical decision support
    clinical_alerts: Optional[List[str]] = Field(None, description="Clinical alerts")
    recommendations: Optional[List[str]] = Field(None, description="Clinical recommendations")
    
    # Consent and authorization
    consent_id: Optional[UUID] = Field(None, description="Consent record UUID")
    
    @field_validator('diagnosis_codes', 'procedure_codes')
    @classmethod
    def validate_clinical_codes(cls, v):
        """Validate clinical codes format."""
        if v:
            for code in v:
                if not code.code or not code.display or not code.system:
                    raise ValueError("Clinical codes must have code, display, and system")
        return v


class ClinicalWorkflowUpdate(BaseModel):
    """Schema for updating an existing clinical workflow."""
    status: Optional[WorkflowStatus] = None
    priority: Optional[WorkflowPriority] = None
    
    # Clinical content updates
    chief_complaint: Optional[str] = None
    history_present_illness: Optional[str] = None
    review_of_systems: Optional[str] = None
    physical_examination: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    
    # Structured updates
    vital_signs: Optional[VitalSigns] = None
    allergies: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    diagnosis_codes: Optional[List[ClinicalCode]] = None
    procedure_codes: Optional[List[ClinicalCode]] = None
    
    # Quality and completion
    completion_percentage: Optional[int] = Field(None, ge=0, le=100)
    documentation_quality: Optional[DocumentationQuality] = None
    
    # Timing updates
    workflow_end_time: Optional[datetime] = None
    actual_duration_minutes: Optional[int] = Field(None, ge=1)


class ClinicalWorkflowStepCreate(BaseModel):
    """Schema for creating workflow steps."""
    workflow_id: UUID
    step_name: str = Field(..., max_length=100)
    step_type: str = Field(..., max_length=50)
    step_order: int = Field(..., ge=1)
    
    # Step content
    step_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    instructions: Optional[str] = None
    observations: Optional[str] = None
    decisions: Optional[str] = None
    actions: Optional[str] = None
    
    # Timing
    estimated_duration_minutes: Optional[int] = Field(None, ge=1)
    
    # Dependencies
    prerequisites: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None


class ClinicalWorkflowStepUpdate(BaseModel):
    """Schema for updating workflow steps."""
    status: Optional[StepStatus] = None
    step_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    observations: Optional[str] = None
    decisions: Optional[str] = None
    actions: Optional[str] = None
    
    # Completion data
    completed_at: Optional[datetime] = None
    actual_duration_minutes: Optional[int] = Field(None, ge=1)
    quality_score: Optional[int] = Field(None, ge=0, le=100)
    completion_quality: Optional[DocumentationQuality] = None
    
    # Review flags
    requires_review: Optional[bool] = None
    review_completed: Optional[bool] = None


class ClinicalEncounterCreate(BaseModel):
    """Schema for creating clinical encounters."""
    workflow_id: Optional[UUID] = None
    patient_id: UUID
    provider_id: UUID
    
    # FHIR encounter fields
    encounter_class: EncounterClass
    encounter_type_code: Optional[str] = None
    encounter_type_display: Optional[str] = None
    service_type_code: Optional[str] = None
    service_type_display: Optional[str] = None
    
    # SOAP documentation
    soap_note: Optional[SOAPNote] = None
    
    # Additional documentation
    history: Optional[str] = None
    examination: Optional[str] = None
    procedures: Optional[str] = None
    medications_administered: Optional[List[str]] = None
    
    # Structured data
    vital_signs: Optional[VitalSigns] = None
    allergies: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    diagnosis_codes: Optional[List[ClinicalCode]] = None
    procedure_codes: Optional[List[ClinicalCode]] = None
    
    # Encounter logistics
    encounter_datetime: datetime
    location: Optional[str] = None
    facility: Optional[str] = None
    department: Optional[str] = None
    room: Optional[str] = None
    
    # Participants
    attending_provider_id: Optional[UUID] = None
    referring_provider_id: Optional[UUID] = None
    consulting_providers: Optional[List[UUID]] = None
    
    # Outcome
    disposition: Optional[str] = None
    outcome: Optional[str] = None
    follow_up_required: Optional[bool] = False
    follow_up_instructions: Optional[str] = None
    
    # Consent
    consent_id: Optional[UUID] = None


# Response schemas

class ClinicalWorkflowResponse(ClinicalWorkflowBase):
    """Response schema for clinical workflows."""
    id: UUID
    patient_id: UUID
    provider_id: UUID
    status: WorkflowStatus
    workflow_number: Optional[str] = None
    
    # Decrypted clinical content (when authorized)
    chief_complaint: Optional[str] = None
    history_present_illness: Optional[str] = None
    review_of_systems: Optional[str] = None
    physical_examination: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    
    # Structured data (decrypted when authorized)
    vital_signs: Optional[VitalSigns] = None
    allergies: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    diagnosis_codes: Optional[List[ClinicalCode]] = None
    procedure_codes: Optional[List[ClinicalCode]] = None
    
    # Workflow metadata
    workflow_start_time: datetime
    workflow_end_time: Optional[datetime] = None
    completion_percentage: int = 0
    quality_score: Optional[int] = None
    documentation_quality: Optional[DocumentationQuality] = None
    
    # FHIR compliance
    fhir_encounter_id: Optional[str] = None
    fhir_version: str = "R4"
    
    # Audit metadata
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: UUID
    last_accessed_at: Optional[datetime] = None
    access_count: int = 0
    version: int = 1
    
    model_config = {"from_attributes": True}


class ClinicalWorkflowStepResponse(BaseModel):
    """Response schema for workflow steps."""
    id: UUID
    workflow_id: UUID
    step_name: str
    step_type: str
    step_order: int
    status: StepStatus
    
    # Decrypted content (when authorized)
    step_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    observations: Optional[str] = None
    decisions: Optional[str] = None
    actions: Optional[str] = None
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration_minutes: Optional[int] = None
    actual_duration_minutes: Optional[int] = None
    
    # Quality
    quality_score: Optional[int] = None
    completion_quality: Optional[DocumentationQuality] = None
    requires_review: bool = False
    review_completed: bool = False
    
    # Audit
    completed_by: Optional[UUID] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ClinicalEncounterResponse(BaseModel):
    """Response schema for clinical encounters."""
    id: UUID
    workflow_id: Optional[UUID] = None
    patient_id: UUID
    provider_id: UUID
    
    # FHIR fields
    encounter_class: EncounterClass
    encounter_status: EncounterStatus
    encounter_type_code: Optional[str] = None
    encounter_type_display: Optional[str] = None
    fhir_encounter_id: Optional[str] = None
    
    # SOAP note (decrypted when authorized)
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    
    # Additional documentation (decrypted when authorized)
    history: Optional[str] = None
    examination: Optional[str] = None
    procedures: Optional[str] = None
    
    # Structured data (decrypted when authorized)
    vital_signs: Optional[VitalSigns] = None
    allergies: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    diagnosis_codes: Optional[List[ClinicalCode]] = None
    procedure_codes: Optional[List[ClinicalCode]] = None
    
    # Encounter logistics
    encounter_datetime: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    length_minutes: Optional[int] = None
    location: Optional[str] = None
    department: Optional[str] = None
    
    # Outcome
    disposition: Optional[str] = None
    outcome: Optional[str] = None
    follow_up_required: bool = False
    follow_up_instructions: Optional[str] = None
    
    # Quality
    documentation_complete: bool = False
    quality_measures_met: Optional[List[str]] = None
    
    # Audit
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: UUID
    
    model_config = {"from_attributes": True}


# List and pagination schemas

class ClinicalWorkflowListResponse(BaseModel):
    """Response schema for workflow lists."""
    workflows: List[ClinicalWorkflowResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class ClinicalWorkflowSearchFilters(BaseModel):
    """Search filters for workflows."""
    patient_id: Optional[UUID] = None
    provider_id: Optional[UUID] = None
    workflow_type: Optional[WorkflowType] = None
    status: Optional[List[WorkflowStatus]] = None
    priority: Optional[List[WorkflowPriority]] = None
    department: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    
    # Text search
    search_text: Optional[str] = Field(None, max_length=255)
    
    # Pagination
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    
    # Sorting
    sort_by: Optional[str] = Field("created_at", pattern="^(created_at|updated_at|workflow_start_time|priority)$")
    sort_direction: Optional[str] = Field("desc", pattern="^(asc|desc)$")


# Audit and analytics schemas

class WorkflowAnalytics(BaseModel):
    """Workflow analytics and metrics."""
    total_workflows: int
    completed_workflows: int
    average_duration_minutes: Optional[float] = None
    completion_rate: float
    quality_score_average: Optional[float] = None
    
    # By type
    workflows_by_type: Dict[str, int]
    workflows_by_status: Dict[str, int]
    workflows_by_priority: Dict[str, int]
    
    # Performance metrics
    average_time_to_completion: Optional[float] = None
    documentation_quality_distribution: Dict[str, int]
    
    # Date range
    period_start: date
    period_end: date


class WorkflowAuditEvent(BaseModel):
    """Audit event for workflows."""
    id: UUID
    workflow_id: UUID
    event_type: str
    action: str
    user_id: UUID
    timestamp: datetime
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    
    # PHI access
    phi_accessed: bool = False
    phi_fields_accessed: Optional[List[str]] = None
    access_purpose: Optional[str] = None
    
    # Risk assessment
    risk_level: str = "low"
    anomaly_score: Optional[int] = None
    
    model_config = {"from_attributes": True}