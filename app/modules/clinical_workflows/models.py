"""
Clinical Workflows Database Models

SQLAlchemy models for clinical workflow management with PHI encryption,
FHIR R4 compliance, and comprehensive audit trails.
"""

from datetime import datetime
from uuid import uuid4
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, DateTime, Integer, Boolean, ForeignKey, 
    JSON, CheckConstraint, Index, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database_unified import Base, DataClassification, SoftDeleteMixin


class ClinicalWorkflow(Base, SoftDeleteMixin):
    """
    Main clinical workflow entity
    
    Represents complete clinical workflows including encounters, care plans,
    and clinical decision-making processes with full PHI encryption and audit trails.
    
    Security Features:
    - PHI field-level encryption
    - FHIR R4 compliance
    - Consent verification
    - Comprehensive audit logging
    """
    __tablename__ = "clinical_workflows"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    
    # Workflow metadata
    workflow_type = Column(String(100), nullable=False)  # "encounter", "care_plan", "consultation"
    status = Column(String(50), nullable=False, default="active")  # "active", "completed", "cancelled", "suspended"
    priority = Column(String(20), default="routine")  # "routine", "urgent", "emergency", "stat"
    category = Column(String(100))  # "inpatient", "outpatient", "emergency", "home_health"
    
    # Clinical workflow identifiers
    workflow_number = Column(String(50), unique=True)  # Human-readable workflow ID
    external_id = Column(String(100))  # External system reference
    
    # Encrypted PHI fields - Core clinical content
    chief_complaint_encrypted = Column(Text)  # Patient's main concern (encrypted)
    history_present_illness_encrypted = Column(Text)  # HPI details (encrypted)
    review_of_systems_encrypted = Column(Text)  # ROS (encrypted)
    physical_examination_encrypted = Column(Text)  # Physical exam findings (encrypted)
    assessment_encrypted = Column(Text)  # Clinical assessment/impression (encrypted)
    plan_encrypted = Column(Text)  # Treatment plan (encrypted)
    
    # Structured clinical data (encrypted JSON)
    vital_signs_encrypted = Column(Text)  # JSON with vitals (encrypted)
    allergies_encrypted = Column(Text)  # Known allergies (encrypted)
    medications_encrypted = Column(Text)  # Current medications (encrypted)
    diagnosis_codes_encrypted = Column(Text)  # ICD-10 codes (encrypted)
    procedure_codes_encrypted = Column(Text)  # CPT codes (encrypted)
    lab_orders_encrypted = Column(Text)  # Laboratory orders (encrypted)
    
    # Clinical decision support
    clinical_alerts_encrypted = Column(Text)  # Clinical alerts and warnings (encrypted)
    recommendations_encrypted = Column(Text)  # Clinical recommendations (encrypted)
    quality_measures_encrypted = Column(Text)  # Quality measure tracking (encrypted)
    
    # FHIR R4 compliance fields
    fhir_encounter_id = Column(String(255))  # FHIR Encounter resource ID
    fhir_version = Column(String(10), default="R4")
    fhir_profile = Column(String(255))  # FHIR profile URL
    fhir_last_updated = Column(DateTime(timezone=True))
    
    # Workflow timing
    workflow_start_time = Column(DateTime(timezone=True), default=func.now())
    workflow_end_time = Column(DateTime(timezone=True))
    estimated_duration_minutes = Column(Integer)
    actual_duration_minutes = Column(Integer)
    
    # Location and context
    location = Column(String(200))  # Physical location
    department = Column(String(100))  # Hospital department
    unit = Column(String(100))  # Hospital unit
    room_number = Column(String(50))  # Room number
    
    # Data classification and security
    data_classification = Column(String(50), default=DataClassification.PHI.value)
    encryption_key_id = Column(String(255))  # Reference to encryption key
    anonymized_version_id = Column(UUID(as_uuid=True))  # Reference to anonymized version
    
    # Consent and authorization
    consent_id = Column(UUID(as_uuid=True), ForeignKey("consents.id"))
    consent_verified_at = Column(DateTime(timezone=True))
    authorization_codes = Column(JSON)  # Authorization codes for data access
    
    # Quality and performance metrics
    quality_score = Column(Integer)  # 0-100 quality score
    completion_percentage = Column(Integer, default=0)  # 0-100 completion
    documentation_quality = Column(String(50))  # "excellent", "good", "fair", "poor"
    
    # Audit and tracking metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    last_modified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    last_accessed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    last_accessed_at = Column(DateTime(timezone=True))
    access_count = Column(Integer, default=0)
    
    # Version control
    version = Column(Integer, default=1)
    parent_workflow_id = Column(UUID(as_uuid=True), ForeignKey("clinical_workflows.id"))
    
    # Relationships
    patient = relationship("Patient", back_populates="clinical_workflows")
    provider = relationship("User", foreign_keys=[provider_id])
    created_by_user = relationship("User", foreign_keys=[created_by])
    workflow_steps = relationship("ClinicalWorkflowStep", back_populates="workflow", cascade="all, delete-orphan")
    encounters = relationship("ClinicalEncounter", back_populates="workflow", cascade="all, delete-orphan")
    audit_trail = relationship("ClinicalWorkflowAudit", back_populates="workflow", cascade="all, delete-orphan")
    child_workflows = relationship("ClinicalWorkflow", remote_side=[id])
    
    # Database constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'completed', 'cancelled', 'suspended')",
            name="valid_workflow_status"
        ),
        CheckConstraint(
            "priority IN ('routine', 'urgent', 'emergency', 'stat')",
            name="valid_workflow_priority"
        ),
        CheckConstraint(
            "completion_percentage >= 0 AND completion_percentage <= 100",
            name="valid_completion_percentage"
        ),
        Index("idx_workflow_patient_provider", "patient_id", "provider_id"),
        Index("idx_workflow_status_priority", "status", "priority"),
        Index("idx_workflow_type_priority", "workflow_type", "priority"),
        Index("idx_workflow_data_classification", "data_classification"),
        Index("idx_workflow_fhir_id", "fhir_encounter_id"),
    )


class ClinicalWorkflowStep(Base):
    """
    Individual workflow steps for granular tracking
    
    Represents discrete steps within a clinical workflow for detailed
    audit trails and process optimization.
    """
    __tablename__ = "clinical_workflow_steps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("clinical_workflows.id"), nullable=False)
    
    # Step metadata
    step_name = Column(String(100), nullable=False)  # "triage", "assessment", "diagnosis", "treatment"
    step_type = Column(String(50))  # "data_entry", "decision_point", "documentation", "communication"
    step_order = Column(Integer, nullable=False)  # Sequential order within workflow
    status = Column(String(50), default="pending")  # "pending", "in_progress", "completed", "skipped", "failed"
    
    # Step content and data
    step_data_encrypted = Column(Text)  # Step-specific PHI data (encrypted)
    notes_encrypted = Column(Text)  # Provider notes for this step (encrypted)
    instructions_encrypted = Column(Text)  # Step instructions (encrypted)
    
    # Clinical content for this step
    observations_encrypted = Column(Text)  # Clinical observations (encrypted)
    decisions_encrypted = Column(Text)  # Clinical decisions made (encrypted)
    actions_encrypted = Column(Text)  # Actions taken (encrypted)
    
    # Step timing and performance
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    estimated_duration_minutes = Column(Integer)
    actual_duration_minutes = Column(Integer)
    
    # Quality metrics for this step
    quality_score = Column(Integer)  # 0-100 quality score for this step
    completion_quality = Column(String(50))  # "excellent", "good", "fair", "poor"
    requires_review = Column(Boolean, default=False)
    review_completed = Column(Boolean, default=False)
    
    # Dependencies and requirements
    prerequisites = Column(JSON)  # Required previous steps
    dependencies = Column(JSON)  # External dependencies
    blocking_issues = Column(JSON)  # Issues preventing completion
    
    # Step authorization and audit
    completed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    data_classification = Column(String(50), default=DataClassification.PHI.value)
    
    # AI training data collection flags
    collect_for_ai_training = Column(Boolean, default=True)
    ai_training_category = Column(String(100))  # "clinical_reasoning", "workflow_optimization", etc.
    
    # Relationships
    workflow = relationship("ClinicalWorkflow", back_populates="workflow_steps")
    completed_by_user = relationship("User", foreign_keys=[completed_by])
    reviewed_by_user = relationship("User", foreign_keys=[reviewed_by])
    
    # Database constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'skipped', 'failed')",
            name="valid_step_status"
        ),
        CheckConstraint(
            "step_order >= 1",
            name="valid_step_order"
        ),
        Index("idx_step_workflow_order", "workflow_id", "step_order"),
        Index("idx_step_status_started", "status", "started_at"),
        Index("idx_step_type_completed", "step_type", "completed_at"),
    )


class ClinicalEncounter(Base, SoftDeleteMixin):
    """
    FHIR R4 compliant clinical encounter
    
    Represents specific clinical encounters within workflows,
    following FHIR R4 Encounter resource specification.
    """
    __tablename__ = "clinical_encounters"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("clinical_workflows.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # FHIR Encounter required fields
    encounter_class = Column(String(50), nullable=False)  # "AMB", "EMER", "IMP", "HH" (ambulatory, emergency, inpatient, home health)
    encounter_status = Column(String(50), default="planned")  # "planned", "arrived", "triaged", "in-progress", "onleave", "finished", "cancelled"
    
    # FHIR Encounter type
    encounter_type_code = Column(String(100))  # SNOMED CT code
    encounter_type_display = Column(String(200))  # Human-readable type
    encounter_type_system = Column(String(255), default="http://snomed.info/sct")
    
    # Service type
    service_type_code = Column(String(100))  # Service type code
    service_type_display = Column(String(200))  # Service type display
    
    # Clinical SOAP structure (encrypted PHI)
    subjective_encrypted = Column(Text)  # S - Subjective (patient-reported)
    objective_encrypted = Column(Text)  # O - Objective (clinical findings)
    assessment_encrypted = Column(Text)  # A - Assessment (clinical judgment)
    plan_encrypted = Column(Text)  # P - Plan (treatment plan)
    
    # Additional clinical documentation
    history_encrypted = Column(Text)  # Medical history (encrypted)
    examination_encrypted = Column(Text)  # Physical examination (encrypted)
    procedures_encrypted = Column(Text)  # Procedures performed (encrypted)
    medications_administered_encrypted = Column(Text)  # Medications given (encrypted)
    
    # Structured clinical data (encrypted JSON)
    vital_signs_encrypted = Column(Text)  # Vital signs measurements
    allergies_encrypted = Column(Text)  # Known allergies
    current_medications_encrypted = Column(Text)  # Current medication list
    diagnosis_codes_encrypted = Column(Text)  # ICD-10 diagnosis codes
    procedure_codes_encrypted = Column(Text)  # CPT procedure codes
    
    # Encounter logistics
    encounter_datetime = Column(DateTime(timezone=True), nullable=False)
    arrival_time = Column(DateTime(timezone=True))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    length_minutes = Column(Integer)
    
    # Location details
    location = Column(String(200))
    facility = Column(String(200))
    department = Column(String(100))
    room = Column(String(50))
    bed = Column(String(50))
    
    # Encounter participants
    attending_provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    referring_provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    consulting_providers = Column(JSON)  # Array of provider IDs
    
    # FHIR compliance metadata
    fhir_encounter_id = Column(String(255), unique=True)
    fhir_version = Column(String(10), default="R4")
    fhir_profile = Column(String(255))
    fhir_last_updated = Column(DateTime(timezone=True))
    
    # Clinical quality indicators
    documentation_complete = Column(Boolean, default=False)
    quality_measures_met = Column(JSON)  # Quality measures achieved
    care_gaps_identified = Column(JSON)  # Care gaps found
    
    # Outcome and disposition
    disposition = Column(String(100))  # "home", "admitted", "transferred", "ama", "deceased"
    outcome = Column(String(100))  # "improved", "stable", "worsened", "resolved"
    follow_up_required = Column(Boolean, default=False)
    follow_up_instructions_encrypted = Column(Text)
    
    # Data classification and consent
    data_classification = Column(String(50), default=DataClassification.PHI.value)
    consent_id = Column(UUID(as_uuid=True), ForeignKey("consents.id"))
    consent_verified_at = Column(DateTime(timezone=True))
    
    # Audit metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    last_modified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    documentation_locked = Column(Boolean, default=False)
    locked_at = Column(DateTime(timezone=True))
    locked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    workflow = relationship("ClinicalWorkflow", back_populates="encounters")
    patient = relationship("Patient")
    provider = relationship("User", foreign_keys=[provider_id])
    attending_provider = relationship("User", foreign_keys=[attending_provider_id])
    referring_provider = relationship("User", foreign_keys=[referring_provider_id])
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    # Database constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "encounter_class IN ('AMB', 'EMER', 'IMP', 'HH', 'VR')",
            name="valid_encounter_class"
        ),
        CheckConstraint(
            "encounter_status IN ('planned', 'arrived', 'triaged', 'in-progress', 'onleave', 'finished', 'cancelled')",
            name="valid_encounter_status"
        ),
        Index("idx_encounter_patient_date", "patient_id", "encounter_datetime"),
        Index("idx_encounter_provider_date", "provider_id", "encounter_datetime"),
        Index("idx_encounter_fhir_id", "fhir_encounter_id"),
        Index("idx_encounter_class_status", "encounter_class", "encounter_status"),
    )


class ClinicalWorkflowAudit(Base):
    """
    Comprehensive audit trail for clinical workflows
    
    Immutable audit records for all clinical workflow operations
    for SOC2 Type II compliance.
    """
    __tablename__ = "clinical_workflow_audit"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("clinical_workflows.id"), nullable=False)
    
    # Audit event details
    event_type = Column(String(100), nullable=False)  # "created", "updated", "accessed", "completed"
    event_category = Column(String(50))  # "workflow", "step", "encounter", "data_access"
    action = Column(String(100), nullable=False)  # Specific action taken
    
    # Actor information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user_role = Column(String(100))  # Role at time of action
    session_id = Column(String(255))  # Session identifier
    
    # Request context
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)  # Browser/client information
    request_id = Column(String(255))  # Request correlation ID
    
    # Data changes
    field_name = Column(String(100))  # Field that was changed
    old_value_hash = Column(String(255))  # Hash of old value (for non-PHI)
    new_value_hash = Column(String(255))  # Hash of new value (for non-PHI)
    change_type = Column(String(50))  # "create", "update", "delete", "access"
    
    # PHI access tracking
    phi_accessed = Column(Boolean, default=False)
    phi_fields_accessed = Column(JSON)  # List of PHI fields accessed
    access_purpose = Column(String(200))  # Purpose of PHI access
    consent_verified = Column(Boolean, default=False)
    
    # Compliance metadata
    compliance_tags = Column(JSON)  # SOC2, HIPAA compliance tags
    retention_period_days = Column(Integer, default=2555)  # 7 years
    legal_hold = Column(Boolean, default=False)
    
    # Audit timing
    timestamp = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    processing_time_ms = Column(Integer)  # Time to process request
    
    # Integrity verification
    audit_hash = Column(String(255))  # Hash for integrity verification
    previous_audit_hash = Column(String(255))  # Chain integrity
    
    # Risk assessment
    risk_level = Column(String(20), default="low")  # "low", "medium", "high", "critical"
    anomaly_score = Column(Integer)  # 0-100 anomaly detection score
    
    # Relationships
    workflow = relationship("ClinicalWorkflow", back_populates="audit_trail")
    user = relationship("User")
    
    # Database constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "risk_level IN ('low', 'medium', 'high', 'critical')",
            name="valid_risk_level"
        ),
        Index("idx_audit_workflow_timestamp", "workflow_id", "timestamp"),
        Index("idx_audit_user_timestamp", "user_id", "timestamp"),
        Index("idx_audit_event_type", "event_type", "timestamp"),
        Index("idx_audit_phi_access", "phi_accessed", "timestamp"),
        Index("idx_audit_risk_level", "risk_level", "timestamp"),
    )