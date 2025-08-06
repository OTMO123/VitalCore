"""
Schemas for Doctor History Mode - Linked Medical Timeline
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid


class EventPriority(str, Enum):
    """Medical event priority levels for timeline display."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class EventType(str, Enum):
    """Types of medical events in the timeline."""
    ADMISSION = "admission"
    DISCHARGE = "discharge"
    DIAGNOSIS = "diagnosis"
    MEDICATION = "medication"
    PROCEDURE = "procedure"
    LAB_RESULT = "lab_result"
    IMAGING = "imaging"
    CONSULTATION = "consultation"
    VITAL_SIGNS = "vital_signs"
    ALLERGIES = "allergies"
    IMMUNIZATION = "immunization"
    CARE_PLAN = "care_plan"
    PROGRESS_NOTE = "progress_note"
    DISCHARGE_SUMMARY = "discharge_summary"


class CarePhase(str, Enum):
    """Care cycle phases for medical care management."""
    ASSESSMENT = "assessment"
    PLANNING = "planning"
    INTERVENTION = "intervention"
    EVALUATION = "evaluation"
    MAINTENANCE = "maintenance"
    TRANSITION = "transition"
    FOLLOW_UP = "follow_up"


class MedicalEventBase(BaseModel):
    """Base medical event for timeline display."""
    model_config = ConfigDict(from_attributes=True)
    
    event_id: uuid.UUID
    event_type: EventType
    title: str = Field(..., description="Event title for display")
    description: Optional[str] = Field(None, description="Detailed description")
    event_date: datetime = Field(..., description="When the event occurred")
    priority: EventPriority = Field(EventPriority.MEDIUM, description="Event priority")
    provider_name: Optional[str] = Field(None, description="Provider or department")
    location: Optional[str] = Field(None, description="Location where event occurred")
    
    # Linked events for medical timeline
    linked_events: Optional[List[uuid.UUID]] = Field(
        default=None, 
        description="IDs of related medical events"
    )
    parent_case_id: Optional[uuid.UUID] = Field(
        None, 
        description="Parent case for this event"
    )


class LinkedTimelineEvent(MedicalEventBase):
    """Enhanced medical event with linking information."""
    correlation_id: Optional[uuid.UUID] = Field(
        None, 
        description="Correlation ID for linked events"
    )
    sequence_number: Optional[int] = Field(
        None, 
        description="Sequence in care timeline"
    )
    care_phase: Optional[CarePhase] = Field(
        None, 
        description="Phase of care this event belongs to"
    )
    outcome_status: Optional[str] = Field(
        None, 
        description="Outcome or status of this event"
    )
    
    # Clinical data
    clinical_data: Optional[Dict[str, Any]] = Field(
        None, 
        description="Associated clinical data"
    )
    diagnostic_codes: Optional[List[str]] = Field(
        None, 
        description="ICD-10 or other diagnostic codes"
    )
    medication_data: Optional[Dict[str, Any]] = Field(
        None, 
        description="Medication information if applicable"
    )
    
    # FHIR compatibility
    fhir_resource_type: Optional[str] = Field(
        None, 
        description="FHIR resource type for interoperability"
    )
    fhir_resource_id: Optional[str] = Field(
        None, 
        description="FHIR resource identifier"
    )


class CaseSummary(BaseModel):
    """Summary of a medical case for doctor history view."""
    model_config = ConfigDict(from_attributes=True)
    
    case_id: uuid.UUID
    patient_id: uuid.UUID
    case_title: str = Field(..., description="Case title or primary diagnosis")
    case_status: str = Field(..., description="Current status of the case")
    start_date: datetime = Field(..., description="When case started")
    last_updated: datetime = Field(..., description="Last case update")
    
    primary_diagnosis: Optional[str] = Field(None, description="Primary diagnosis")
    secondary_diagnoses: Optional[List[str]] = Field(None, description="Secondary diagnoses")
    attending_physician: Optional[str] = Field(None, description="Attending physician")
    care_team: Optional[List[str]] = Field(None, description="Care team members")
    
    # Timeline summary
    total_events: int = Field(0, description="Total number of events")
    critical_events: int = Field(0, description="Number of critical events")
    last_critical_event: Optional[datetime] = Field(None, description="Last critical event")
    
    # Care metrics
    length_of_stay: Optional[int] = Field(None, description="Length of stay in days")
    admission_type: Optional[str] = Field(None, description="Type of admission")
    discharge_disposition: Optional[str] = Field(None, description="Discharge disposition")


class DoctorHistoryResponse(BaseModel):
    """Response for doctor history endpoint."""
    model_config = ConfigDict(from_attributes=True)
    
    case_summary: CaseSummary
    timeline_events: List[MedicalEventBase]
    patient_demographics: Dict[str, Any]
    care_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional care context information"
    )
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    total_events: int = Field(..., description="Total events in timeline")
    date_range: Dict[str, datetime] = Field(..., description="Date range of events")


class LinkedTimelineResponse(BaseModel):
    """Response for linked medical timeline."""
    model_config = ConfigDict(from_attributes=True)
    
    case_id: uuid.UUID
    patient_id: uuid.UUID
    timeline_events: List[LinkedTimelineEvent]
    
    # Linking analysis
    event_correlations: Dict[str, List[uuid.UUID]] = Field(
        default_factory=dict,
        description="Event correlation analysis"
    )
    care_transitions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Care transition points"
    )
    critical_paths: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Critical care pathways identified"
    )
    
    # Timeline metadata
    timeline_start: datetime = Field(..., description="Timeline start date")
    timeline_end: datetime = Field(..., description="Timeline end date")
    total_linked_events: int = Field(..., description="Number of linked events")
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class CareCycle(BaseModel):
    """A complete care cycle with phases."""
    model_config = ConfigDict(from_attributes=True)
    
    cycle_id: uuid.UUID
    patient_id: uuid.UUID
    cycle_name: str = Field(..., description="Name/description of care cycle")
    care_phase: CarePhase = Field(..., description="Current phase of care")
    
    start_date: datetime = Field(..., description="Cycle start date")
    target_end_date: Optional[datetime] = Field(None, description="Target completion date")
    actual_end_date: Optional[datetime] = Field(None, description="Actual completion date")
    
    # Care cycle components
    assessment_data: Optional[Dict[str, Any]] = Field(None, description="Assessment phase data")
    care_plan: Optional[Dict[str, Any]] = Field(None, description="Care plan details")
    interventions: Optional[List[Dict[str, Any]]] = Field(None, description="Interventions performed")
    outcomes: Optional[Dict[str, Any]] = Field(None, description="Care outcomes")
    
    # Progress tracking
    completion_percentage: float = Field(0.0, description="Cycle completion percentage")
    milestones_achieved: List[str] = Field(default_factory=list, description="Achieved milestones")
    pending_actions: List[str] = Field(default_factory=list, description="Pending actions")
    
    # Quality metrics
    quality_indicators: Optional[Dict[str, Any]] = Field(None, description="Quality metrics")
    patient_satisfaction: Optional[float] = Field(None, description="Patient satisfaction score")
    
    # Team and resources
    care_team_members: List[str] = Field(default_factory=list, description="Care team")
    resources_utilized: Optional[List[str]] = Field(None, description="Resources used")


class CareCyclesResponse(BaseModel):
    """Response for care cycles endpoint."""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: uuid.UUID
    active_cycles: List[CareCycle] = Field(..., description="Currently active care cycles")
    completed_cycles: List[CareCycle] = Field(..., description="Completed care cycles")
    
    # Summary statistics
    total_active_cycles: int = Field(..., description="Number of active cycles")
    total_completed_cycles: int = Field(..., description="Number of completed cycles")
    average_cycle_duration: Optional[float] = Field(None, description="Average cycle duration in days")
    
    # Patient care overview
    care_complexity_score: Optional[float] = Field(None, description="Care complexity assessment")
    primary_care_areas: List[str] = Field(default_factory=list, description="Primary care areas")
    care_coordination_notes: Optional[str] = Field(None, description="Care coordination notes")
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Request schemas for creating/updating
class MedicalEventCreate(BaseModel):
    """Schema for creating medical events."""
    model_config = ConfigDict(from_attributes=True)
    
    event_type: EventType
    title: str
    description: Optional[str] = None
    event_date: datetime
    priority: EventPriority = EventPriority.MEDIUM
    provider_name: Optional[str] = None
    location: Optional[str] = None
    
    clinical_data: Optional[Dict[str, Any]] = None
    diagnostic_codes: Optional[List[str]] = None
    medication_data: Optional[Dict[str, Any]] = None


class CareCycleCreate(BaseModel):
    """Schema for creating care cycles."""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: uuid.UUID
    cycle_name: str
    care_phase: CarePhase = CarePhase.ASSESSMENT
    target_end_date: Optional[datetime] = None
    
    assessment_data: Optional[Dict[str, Any]] = None
    care_plan: Optional[Dict[str, Any]] = None
    care_team_members: List[str] = Field(default_factory=list)


# Filter and query schemas
class TimelineFilters(BaseModel):
    """Filters for timeline queries."""
    event_types: Optional[List[EventType]] = None
    priority_levels: Optional[List[EventPriority]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    provider_filter: Optional[str] = None
    include_linked_only: bool = False