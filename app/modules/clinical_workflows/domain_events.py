"""
Clinical Workflows Domain Events

Domain events for clinical workflow operations to integrate with the event bus
for comprehensive audit trails and system-wide coordination.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.core.event_bus_advanced import BaseEvent


@dataclass
class ClinicalWorkflowStarted(BaseEvent):
    """Clinical workflow initiated by provider."""
    event_type: str = "ClinicalWorkflowStarted"
    aggregate_type: str = "ClinicalWorkflow"
    
    # Workflow identifiers
    workflow_id: str
    workflow_type: str
    patient_id: str
    provider_id: str
    
    # Workflow metadata
    priority: str
    category: Optional[str] = None
    location: Optional[str] = None
    department: Optional[str] = None
    
    # Risk assessment
    risk_score: Optional[int] = None
    consent_verified: bool = False
    
    # Timing
    estimated_duration_minutes: Optional[int] = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.aggregate_id:
            self.aggregate_id = self.workflow_id


@dataclass
class ClinicalWorkflowStepCompleted(BaseEvent):
    """Individual workflow step completed."""
    event_type: str = "ClinicalWorkflowStepCompleted"
    aggregate_type: str = "ClinicalWorkflow"
    
    # Step identifiers
    workflow_id: str
    step_id: str
    step_name: str
    step_type: str
    step_order: int
    
    # Completion details
    completed_by: str
    completed_at: datetime
    duration_minutes: Optional[int] = None
    
    # Quality metrics
    quality_score: Optional[int] = None
    completion_quality: Optional[str] = None
    requires_review: bool = False
    
    # Clinical data indicators
    phi_data_updated: bool = False
    diagnosis_updated: bool = False
    treatment_plan_updated: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        if not self.aggregate_id:
            self.aggregate_id = self.workflow_id


@dataclass
class ClinicalDataAccessed(BaseEvent):
    """PHI clinical data accessed by provider."""
    event_type: str = "ClinicalDataAccessed"
    aggregate_type: str = "ClinicalWorkflow"
    
    # Access details
    workflow_id: str
    patient_id: str
    accessed_by: str
    access_timestamp: datetime
    
    # Data access specifics
    data_type: str  # "workflow", "encounter", "step_data"
    phi_fields_accessed: List[str]
    access_purpose: str
    access_method: str  # "web_ui", "api", "mobile_app"
    
    # Context
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Security
    consent_verified: bool = False
    authorization_level: str = "standard"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.aggregate_id:
            self.aggregate_id = self.workflow_id


@dataclass
class DiagnosisAssigned(BaseEvent):
    """Clinical diagnosis assigned to patient."""
    event_type: str = "DiagnosisAssigned"
    aggregate_type: str = "ClinicalWorkflow"
    
    # Diagnosis details
    workflow_id: str
    patient_id: str
    assigned_by: str
    assigned_at: datetime
    
    # Clinical codes
    diagnosis_codes: List[Dict[str, str]]  # [{"code": "R06.02", "display": "Shortness of breath", "system": "ICD-10"}]
    primary_diagnosis_code: Optional[str] = None
    
    # Clinical context
    confidence_level: str = "confirmed"  # "suspected", "probable", "confirmed"
    diagnosis_type: str = "primary"  # "primary", "secondary", "differential"
    
    # Supporting data
    supporting_observations: Optional[List[str]] = None
    clinical_reasoning: Optional[str] = None
    
    # Quality indicators
    evidence_based: bool = True
    guidelines_followed: Optional[List[str]] = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.aggregate_id:
            self.aggregate_id = self.workflow_id


@dataclass
class TreatmentPlanCreated(BaseEvent):
    """Treatment plan created or updated."""
    event_type: str = "TreatmentPlanCreated"
    aggregate_type: str = "ClinicalWorkflow"
    
    # Plan details
    workflow_id: str
    patient_id: str
    created_by: str
    created_at: datetime
    
    # Plan content
    plan_type: str  # "treatment", "discharge", "follow_up", "preventive"
    treatment_goals: List[str]
    
    # Clinical interventions
    medications_count: int = 0
    procedures_count: int = 0
    referrals_count: int = 0
    
    # Timeline
    plan_duration_days: Optional[int] = None
    follow_up_required: bool = False
    follow_up_timeframe: Optional[str] = None
    
    # Quality measures
    evidence_based_interventions: int = 0
    quality_measures_addressed: List[str] = None
    
    # Patient engagement
    patient_education_provided: bool = False
    shared_decision_making: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        if not self.aggregate_id:
            self.aggregate_id = self.workflow_id


@dataclass
class ClinicalEncounterCompleted(BaseEvent):
    """Clinical encounter completed."""
    event_type: str = "ClinicalEncounterCompleted"
    aggregate_type: str = "ClinicalEncounter"
    
    # Encounter details
    encounter_id: str
    workflow_id: Optional[str] = None
    patient_id: str
    provider_id: str
    
    # Encounter metadata
    encounter_class: str  # "AMB", "EMER", "IMP"
    encounter_type: str
    disposition: str  # "home", "admitted", "transferred"
    
    # Timing
    encounter_start: datetime
    encounter_end: datetime
    duration_minutes: int
    
    # Clinical outcomes
    diagnosis_count: int = 0
    procedure_count: int = 0
    medication_changes: int = 0
    
    # Quality indicators
    documentation_complete: bool = False
    quality_measures_met: List[str] = None
    care_gaps_addressed: int = 0
    
    # Follow-up
    follow_up_scheduled: bool = False
    referrals_made: int = 0
    
    def __post_init__(self):
        super().__post_init__()
        if not self.aggregate_id:
            self.aggregate_id = self.encounter_id


@dataclass
class WorkflowQualityAlert(BaseEvent):
    """Quality issue detected in workflow."""
    event_type: str = "WorkflowQualityAlert"
    aggregate_type: str = "ClinicalWorkflow"
    
    # Alert details
    workflow_id: str
    alert_type: str  # "documentation_incomplete", "care_gap", "safety_concern"
    severity: str  # "low", "medium", "high", "critical"
    
    # Quality issue
    issue_description: str
    affected_areas: List[str]
    potential_impact: str
    
    # Context
    detected_at: datetime
    detected_by: str  # "system", "provider", "quality_reviewer"
    
    # Resolution
    requires_immediate_action: bool = False
    suggested_actions: List[str] = None
    auto_resolvable: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        if not self.aggregate_id:
            self.aggregate_id = self.workflow_id


@dataclass
class ClinicalAlertTriggered(BaseEvent):
    """Clinical alert triggered for patient safety."""
    event_type: str = "ClinicalAlertTriggered"
    aggregate_type: str = "ClinicalWorkflow"
    
    # Alert identifiers
    workflow_id: str
    patient_id: str
    alert_id: str
    alert_type: str  # "drug_interaction", "allergy", "critical_value", "care_gap"
    
    # Alert details
    severity: str  # "info", "warning", "critical", "emergency"
    alert_message: str
    clinical_context: str
    
    # Triggering data
    triggering_value: Optional[str] = None
    normal_range: Optional[str] = None
    previous_value: Optional[str] = None
    
    # Response required
    requires_immediate_attention: bool = False
    acknowledgment_required: bool = True
    auto_dismissible: bool = False
    
    # Safety indicators
    patient_safety_impact: str = "low"  # "low", "medium", "high", "critical"
    regulatory_significance: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        if not self.aggregate_id:
            self.aggregate_id = self.workflow_id


@dataclass
class WorkflowCompleted(BaseEvent):
    """Clinical workflow completed."""
    event_type: str = "WorkflowCompleted"
    aggregate_type: str = "ClinicalWorkflow"
    
    # Completion details
    workflow_id: str
    patient_id: str
    completed_by: str
    completed_at: datetime
    
    # Workflow metrics
    total_duration_minutes: int
    steps_completed: int
    quality_score: Optional[int] = None
    
    # Clinical outcomes
    diagnoses_assigned: int = 0
    procedures_performed: int = 0
    medications_prescribed: int = 0
    
    # Documentation quality
    documentation_complete: bool = False
    documentation_quality: Optional[str] = None
    missing_documentation: List[str] = None
    
    # Patient outcomes
    patient_satisfaction_score: Optional[int] = None
    clinical_goals_met: int = 0
    adverse_events: int = 0
    
    # Follow-up planning
    follow_up_appointments_scheduled: int = 0
    referrals_completed: int = 0
    care_coordination_needed: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        if not self.aggregate_id:
            self.aggregate_id = self.workflow_id


@dataclass
class WorkflowAuditEvent(BaseEvent):
    """Comprehensive audit event for workflow operations."""
    event_type: str = "WorkflowAuditEvent"
    aggregate_type: str = "ClinicalWorkflow"
    
    # Audit details
    workflow_id: str
    audit_action: str  # "created", "updated", "accessed", "completed", "cancelled"
    audit_category: str  # "workflow", "step", "encounter", "data_access"
    
    # Actor information
    user_id: str
    user_role: str
    session_id: Optional[str] = None
    
    # Request context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    
    # Data changes
    fields_modified: List[str] = None
    change_summary: Optional[str] = None
    
    # PHI tracking
    phi_accessed: bool = False
    phi_fields: List[str] = None
    access_purpose: Optional[str] = None
    consent_verified: bool = False
    
    # Compliance tags
    compliance_tags: List[str] = None  # ["SOC2", "HIPAA", "FHIR"]
    
    # Risk assessment
    risk_level: str = "low"
    anomaly_score: Optional[int] = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.aggregate_id:
            self.aggregate_id = self.workflow_id


@dataclass
class AITrainingDataCollected(BaseEvent):
    """AI training data collected from workflow."""
    event_type: str = "AITrainingDataCollected"
    aggregate_type: str = "ClinicalWorkflow"
    
    # Data collection details
    workflow_id: str
    data_type: str  # "clinical_reasoning", "workflow_optimization", "decision_support"
    collection_timestamp: datetime
    
    # Data characteristics
    data_category: str
    data_size_bytes: int
    anonymization_level: str  # "full", "partial", "pseudonymized"
    
    # Quality indicators
    data_quality_score: int  # 0-100
    completeness_percentage: int
    clinical_validity: bool = True
    
    # Usage permissions
    training_approved: bool = False
    research_approved: bool = False
    consent_status: str = "pending"
    
    # Gemma 3n specific
    model_training_category: str  # "multimodal", "text", "reasoning", "classification"
    expected_training_value: str = "medium"  # "low", "medium", "high"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.aggregate_id:
            self.aggregate_id = self.workflow_id