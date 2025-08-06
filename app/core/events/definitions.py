"""
Domain Event Definitions for Inter-Module Communication

Comprehensive event definitions for all major healthcare operations including:
- Patient lifecycle events
- Immunization record events  
- Document management events
- Clinical workflow events
- Security and audit events
- IRIS API integration events
- Analytics and reporting events

All events inherit from BaseEvent and provide type-safe, serializable
event contracts for cross-module communication.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Union, Literal
from enum import Enum
from pydantic import Field, validator
import uuid

from app.core.event_bus_advanced import BaseEvent, EventPriority, DeliveryMode


# ============================================
# EVENT CATEGORIES
# ============================================

class EventCategory(str, Enum):
    """Event categories for organization and filtering."""
    PATIENT = "patient"
    IMMUNIZATION = "immunization"
    DOCUMENT = "document"
    CLINICAL_WORKFLOW = "clinical_workflow"
    SECURITY = "security"
    AUDIT = "audit"
    IRIS_API = "iris_api"
    ANALYTICS = "analytics"
    CONSENT = "consent"
    COMPLIANCE = "compliance"


# ============================================
# PATIENT LIFECYCLE EVENTS
# ============================================

class PatientCreated(BaseEvent):
    """Event published when a new patient is created."""
    
    event_type: Literal["patient.created"] = Field(default="patient.created")
    aggregate_type: Literal["patient"] = Field(default="patient")
    category: Literal[EventCategory.PATIENT] = Field(default=EventCategory.PATIENT)
    
    # Patient data
    patient_id: str = Field(..., description="Unique patient identifier")
    mrn: Optional[str] = Field(None, description="Medical record number")
    fhir_id: Optional[str] = Field(None, description="FHIR patient ID")
    
    # Demographics (non-PHI identifiers only)
    gender: Optional[str] = Field(None, description="Patient gender")
    birth_year: Optional[int] = Field(None, description="Birth year for analytics")
    active_status: bool = Field(True, description="Patient active status")
    
    # Metadata
    created_by_user_id: str = Field(..., description="User who created patient")
    data_classification: str = Field(default="PHI", description="Data classification level")
    consent_obtained: bool = Field(False, description="Initial consent status")
    
    # Integration flags
    fhir_compliance_verified: bool = Field(False, description="FHIR R4 compliance status")
    phi_encryption_applied: bool = Field(True, description="PHI encryption status")


class PatientUpdated(BaseEvent):
    """Event published when patient information is updated."""
    
    event_type: Literal["patient.updated"] = Field(default="patient.updated")
    aggregate_type: Literal["patient"] = Field(default="patient")
    category: Literal[EventCategory.PATIENT] = Field(default=EventCategory.PATIENT)
    
    patient_id: str = Field(..., description="Patient identifier")
    updated_fields: List[str] = Field(..., description="List of updated field names")
    update_reason: Optional[str] = Field(None, description="Reason for update")
    updated_by_user_id: str = Field(..., description="User who updated patient")
    
    # Change tracking
    previous_version: Optional[int] = Field(None, description="Previous record version")
    new_version: int = Field(..., description="New record version")
    
    # Compliance
    phi_fields_updated: bool = Field(False, description="Whether PHI fields were updated")
    audit_required: bool = Field(True, description="Whether audit logging is required")


class PatientDeactivated(BaseEvent):
    """Event published when a patient is deactivated."""
    
    event_type: Literal["patient.deactivated"] = Field(default="patient.deactivated")
    aggregate_type: Literal["patient"] = Field(default="patient")
    category: Literal[EventCategory.PATIENT] = Field(default=EventCategory.PATIENT)
    
    patient_id: str = Field(..., description="Patient identifier")
    deactivation_reason: str = Field(..., description="Reason for deactivation")
    deactivated_by_user_id: str = Field(..., description="User who deactivated patient")
    effective_date: datetime = Field(..., description="Effective deactivation date")
    
    # Data retention
    data_retention_required: bool = Field(True, description="Whether data retention applies")
    purge_eligible_date: Optional[datetime] = Field(None, description="Date eligible for purging")


class PatientMerged(BaseEvent):
    """Event published when patient records are merged."""
    
    event_type: Literal["patient.merged"] = Field(default="patient.merged")
    aggregate_type: Literal["patient"] = Field(default="patient")
    category: Literal[EventCategory.PATIENT] = Field(default=EventCategory.PATIENT)
    priority: Literal[EventPriority.HIGH] = Field(default=EventPriority.HIGH)
    
    primary_patient_id: str = Field(..., description="Primary patient identifier (target)")
    merged_patient_ids: List[str] = Field(..., description="Patient IDs that were merged")
    merge_reason: str = Field(..., description="Reason for merge")
    merged_by_user_id: str = Field(..., description="User who performed merge")
    
    # Audit and compliance
    audit_trail_preserved: bool = Field(True, description="Whether audit trails are preserved")
    data_integrity_verified: bool = Field(True, description="Data integrity verification status")


# ============================================
# IMMUNIZATION EVENTS
# ============================================

class ImmunizationRecorded(BaseEvent):
    """Event published when an immunization is recorded."""
    
    event_type: Literal["immunization.recorded"] = Field(default="immunization.recorded")
    aggregate_type: Literal["immunization"] = Field(default="immunization")
    category: Literal[EventCategory.IMMUNIZATION] = Field(default=EventCategory.IMMUNIZATION)
    
    immunization_id: str = Field(..., description="Immunization record identifier")
    patient_id: str = Field(..., description="Patient identifier")
    vaccine_code: str = Field(..., description="Vaccine code (CVX)")
    vaccine_name: str = Field(..., description="Vaccine name")
    administration_date: datetime = Field(..., description="Date administered")
    
    # Clinical details
    lot_number: Optional[str] = Field(None, description="Vaccine lot number")
    manufacturer: Optional[str] = Field(None, description="Vaccine manufacturer")
    route: Optional[str] = Field(None, description="Route of administration")
    site: Optional[str] = Field(None, description="Administration site")
    dose_number: Optional[int] = Field(None, description="Dose number in series")
    
    # Provider information
    administering_provider_id: Optional[str] = Field(None, description="Provider identifier")
    facility_id: Optional[str] = Field(None, description="Facility identifier")
    
    # Source and validation
    source_system: str = Field(..., description="Source system (IRIS, manual, etc.)")
    fhir_compliant: bool = Field(True, description="FHIR R4 compliance status")
    iris_synchronized: bool = Field(False, description="IRIS synchronization status")


class ImmunizationUpdated(BaseEvent):
    """Event published when an immunization record is updated."""
    
    event_type: Literal["immunization.updated"] = Field(default="immunization.updated")
    aggregate_type: Literal["immunization"] = Field(default="immunization")
    category: Literal[EventCategory.IMMUNIZATION] = Field(default=EventCategory.IMMUNIZATION)
    
    immunization_id: str = Field(..., description="Immunization record identifier")
    patient_id: str = Field(..., description="Patient identifier")
    updated_fields: List[str] = Field(..., description="Updated field names")
    update_reason: str = Field(..., description="Reason for update")
    updated_by_user_id: str = Field(..., description="User who updated record")


class ImmunizationDeleted(BaseEvent):
    """Event published when an immunization record is deleted."""
    
    event_type: Literal["immunization.deleted"] = Field(default="immunization.deleted")
    aggregate_type: Literal["immunization"] = Field(default="immunization")
    category: Literal[EventCategory.IMMUNIZATION] = Field(default=EventCategory.IMMUNIZATION)
    priority: Literal[EventPriority.HIGH] = Field(default=EventPriority.HIGH)
    
    immunization_id: str = Field(..., description="Immunization record identifier")
    patient_id: str = Field(..., description="Patient identifier")
    deletion_reason: str = Field(..., description="Reason for deletion")
    deleted_by_user_id: str = Field(..., description="User who deleted record")
    
    # Audit preservation
    soft_delete: bool = Field(True, description="Whether this is a soft delete")
    audit_preserved: bool = Field(True, description="Audit trail preservation status")


# ============================================
# DOCUMENT MANAGEMENT EVENTS
# ============================================

class DocumentUploaded(BaseEvent):
    """Event published when a document is uploaded."""
    
    event_type: Literal["document.uploaded"] = Field(default="document.uploaded")
    aggregate_type: Literal["document"] = Field(default="document")
    category: Literal[EventCategory.DOCUMENT] = Field(default=EventCategory.DOCUMENT)
    
    document_id: str = Field(..., description="Document identifier")
    patient_id: Optional[str] = Field(None, description="Associated patient ID")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    
    # Classification
    document_type: str = Field(..., description="Document type")
    data_classification: str = Field(..., description="Data classification level")
    phi_detected: bool = Field(False, description="PHI detection status")
    
    # Processing
    auto_classification_applied: bool = Field(False, description="Auto-classification status")
    ocr_required: bool = Field(False, description="OCR processing required")
    encryption_applied: bool = Field(True, description="Encryption status")
    
    # Metadata
    uploaded_by_user_id: str = Field(..., description="User who uploaded document")
    storage_backend: str = Field(..., description="Storage backend used")


class DocumentClassified(BaseEvent):
    """Event published when a document is classified."""
    
    event_type: Literal["document.classified"] = Field(default="document.classified")
    aggregate_type: Literal["document"] = Field(default="document")
    category: Literal[EventCategory.DOCUMENT] = Field(default=EventCategory.DOCUMENT)
    
    document_id: str = Field(..., description="Document identifier")
    previous_classification: Optional[str] = Field(None, description="Previous classification")
    new_classification: str = Field(..., description="New classification")
    classification_confidence: float = Field(..., description="Classification confidence score")
    
    # Classification details
    classification_method: str = Field(..., description="Classification method (auto/manual)")
    classifier_version: Optional[str] = Field(None, description="Classifier version used")
    tags_applied: List[str] = Field(default_factory=list, description="Applied tags")
    
    # Compliance
    compliance_verified: bool = Field(False, description="Compliance verification status")
    phi_handling_updated: bool = Field(False, description="PHI handling updated")


class DocumentProcessed(BaseEvent):
    """Event published when document processing is complete."""
    
    event_type: Literal["document.processed"] = Field(default="document.processed")
    aggregate_type: Literal["document"] = Field(default="document")
    category: Literal[EventCategory.DOCUMENT] = Field(default=EventCategory.DOCUMENT)
    
    document_id: str = Field(..., description="Document identifier")
    processing_steps: List[str] = Field(..., description="Completed processing steps")
    processing_duration_ms: int = Field(..., description="Processing time in milliseconds")
    
    # Results
    text_extracted: bool = Field(False, description="Text extraction status")
    text_content_length: Optional[int] = Field(None, description="Extracted text length")
    metadata_extracted: Dict[str, Any] = Field(default_factory=dict, description="Extracted metadata")
    
    # Quality
    processing_quality_score: Optional[float] = Field(None, description="Processing quality score")
    errors_encountered: List[str] = Field(default_factory=list, description="Processing errors")


class DocumentVersionCreated(BaseEvent):
    """Event published when a new document version is created."""
    
    event_type: Literal["document.version_created"] = Field(default="document.version_created")
    aggregate_type: Literal["document"] = Field(default="document")
    category: Literal[EventCategory.DOCUMENT] = Field(default=EventCategory.DOCUMENT)
    
    document_id: str = Field(..., description="Document identifier")
    version_number: int = Field(..., description="New version number")
    previous_version: Optional[int] = Field(None, description="Previous version number")
    version_reason: str = Field(..., description="Reason for new version")
    
    # Change tracking
    changes_summary: str = Field(..., description="Summary of changes")
    created_by_user_id: str = Field(..., description="User who created version")
    
    # Version metadata
    is_major_version: bool = Field(False, description="Major version flag")
    retention_policy_applied: bool = Field(True, description="Retention policy status")


# ============================================
# CLINICAL WORKFLOW EVENTS
# ============================================

class WorkflowInstanceCreated(BaseEvent):
    """Event published when a workflow instance is created."""
    
    event_type: Literal["workflow.instance_created"] = Field(default="workflow.instance_created")
    aggregate_type: Literal["workflow"] = Field(default="workflow")
    category: Literal[EventCategory.CLINICAL_WORKFLOW] = Field(default=EventCategory.CLINICAL_WORKFLOW)
    
    workflow_instance_id: str = Field(..., description="Workflow instance identifier")
    workflow_template_id: str = Field(..., description="Workflow template identifier")
    patient_id: Optional[str] = Field(None, description="Associated patient ID")
    
    # Workflow details
    workflow_name: str = Field(..., description="Workflow name")
    workflow_version: str = Field(..., description="Workflow version")
    priority: str = Field(default="normal", description="Workflow priority")
    
    # Participants
    initiated_by_user_id: str = Field(..., description="User who initiated workflow")
    assigned_participants: List[str] = Field(default_factory=list, description="Assigned participant IDs")
    
    # Scheduling
    scheduled_start: Optional[datetime] = Field(None, description="Scheduled start time")
    expected_duration_minutes: Optional[int] = Field(None, description="Expected duration")
    
    # Context
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Workflow context")


class WorkflowStepCompleted(BaseEvent):
    """Event published when a workflow step is completed."""
    
    event_type: Literal["workflow.step_completed"] = Field(default="workflow.step_completed")
    aggregate_type: Literal["workflow"] = Field(default="workflow")
    category: Literal[EventCategory.CLINICAL_WORKFLOW] = Field(default=EventCategory.CLINICAL_WORKFLOW)
    
    workflow_instance_id: str = Field(..., description="Workflow instance identifier")
    step_id: str = Field(..., description="Completed step identifier")
    step_name: str = Field(..., description="Step name")
    step_type: str = Field(..., description="Step type")
    
    # Completion details
    completed_by_user_id: str = Field(..., description="User who completed step")
    completion_time: datetime = Field(default_factory=datetime.utcnow, description="Completion timestamp")
    duration_minutes: Optional[int] = Field(None, description="Step duration")
    
    # Results
    outcome: str = Field(..., description="Step outcome")
    output_data: Dict[str, Any] = Field(default_factory=dict, description="Step output data")
    quality_indicators: Dict[str, Any] = Field(default_factory=dict, description="Quality metrics")
    
    # Next steps
    next_steps_triggered: List[str] = Field(default_factory=list, description="Triggered next steps")


class WorkflowInstanceCompleted(BaseEvent):
    """Event published when a workflow instance is completed."""
    
    event_type: Literal["workflow.instance_completed"] = Field(default="workflow.instance_completed")
    aggregate_type: Literal["workflow"] = Field(default="workflow")
    category: Literal[EventCategory.CLINICAL_WORKFLOW] = Field(default=EventCategory.CLINICAL_WORKFLOW)
    
    workflow_instance_id: str = Field(..., description="Workflow instance identifier")
    completion_status: str = Field(..., description="Completion status (success/failure/cancelled)")
    total_duration_minutes: int = Field(..., description="Total workflow duration")
    
    # Results
    final_outcome: str = Field(..., description="Final workflow outcome")
    outcomes_achieved: List[str] = Field(default_factory=list, description="Achieved outcomes")
    quality_metrics: Dict[str, Any] = Field(default_factory=dict, description="Workflow quality metrics")
    
    # Analysis
    steps_completed: int = Field(..., description="Number of completed steps")
    steps_skipped: int = Field(default=0, description="Number of skipped steps")
    efficiency_score: Optional[float] = Field(None, description="Workflow efficiency score")


# ============================================
# SECURITY EVENTS
# ============================================

class SecurityViolationDetected(BaseEvent):
    """Event published when a security violation is detected."""
    
    event_type: Literal["security.violation_detected"] = Field(default="security.violation_detected")
    aggregate_type: Literal["security"] = Field(default="security")
    category: Literal[EventCategory.SECURITY] = Field(default=EventCategory.SECURITY)
    priority: Literal[EventPriority.CRITICAL] = Field(default=EventPriority.CRITICAL)
    delivery_mode: Literal[DeliveryMode.EXACTLY_ONCE] = Field(default=DeliveryMode.EXACTLY_ONCE)
    
    violation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Violation identifier")
    violation_type: str = Field(..., description="Type of security violation")
    severity: str = Field(..., description="Violation severity level")
    
    # Context
    user_id: Optional[str] = Field(None, description="User involved in violation")
    resource_type: str = Field(..., description="Type of resource accessed")
    resource_id: Optional[str] = Field(None, description="Resource identifier")
    
    # Details
    violation_description: str = Field(..., description="Detailed violation description")
    detection_method: str = Field(..., description="How violation was detected")
    source_ip: Optional[str] = Field(None, description="Source IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    
    # Response
    immediate_action_taken: Optional[str] = Field(None, description="Immediate response action")
    requires_investigation: bool = Field(True, description="Investigation required flag")
    incident_created: bool = Field(False, description="Security incident created")


class UnauthorizedAccessAttempt(BaseEvent):
    """Event published for unauthorized access attempts."""
    
    event_type: Literal["security.unauthorized_access"] = Field(default="security.unauthorized_access")
    aggregate_type: Literal["security"] = Field(default="security")
    category: Literal[EventCategory.SECURITY] = Field(default=EventCategory.SECURITY)
    priority: Literal[EventPriority.HIGH] = Field(default=EventPriority.HIGH)
    
    attempt_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Attempt identifier")
    user_id: Optional[str] = Field(None, description="User attempting access")
    resource_type: str = Field(..., description="Type of resource")
    resource_id: str = Field(..., description="Resource identifier")
    
    # Access details
    requested_action: str = Field(..., description="Requested action")
    permission_required: str = Field(..., description="Required permission")
    actual_permissions: List[str] = Field(default_factory=list, description="User's actual permissions")
    
    # Context
    endpoint: str = Field(..., description="API endpoint or page")
    method: str = Field(..., description="HTTP method or action type")
    source_ip: Optional[str] = Field(None, description="Source IP address")
    
    # Response
    access_denied: bool = Field(True, description="Access denial status")
    rate_limit_triggered: bool = Field(False, description="Rate limiting triggered")


class PHIAccessLogged(BaseEvent):
    """Event published when PHI is accessed."""
    
    event_type: Literal["security.phi_access"] = Field(default="security.phi_access")
    aggregate_type: Literal["security"] = Field(default="security")
    category: Literal[EventCategory.SECURITY] = Field(default=EventCategory.SECURITY)
    priority: Literal[EventPriority.HIGH] = Field(default=EventPriority.HIGH)
    
    access_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Access log identifier")
    user_id: str = Field(..., description="User accessing PHI")
    patient_id: str = Field(..., description="Patient whose PHI was accessed")
    
    # Access details
    phi_fields_accessed: List[str] = Field(..., description="PHI fields accessed")
    access_purpose: str = Field(..., description="Purpose of access")
    access_method: str = Field(..., description="Method of access (view/edit/export)")
    
    # Legal basis
    legal_basis: str = Field(..., description="Legal basis for access")
    consent_verified: bool = Field(..., description="Patient consent verification")
    minimum_necessary_verified: bool = Field(..., description="Minimum necessary standard verified")
    
    # Context
    session_id: str = Field(..., description="User session identifier")
    source_ip: Optional[str] = Field(None, description="Source IP address")
    access_duration_seconds: Optional[int] = Field(None, description="Access duration")


# ============================================
# AUDIT EVENTS
# ============================================

class AuditLogCreated(BaseEvent):
    """Event published when an audit log entry is created."""
    
    event_type: Literal["audit.log_created"] = Field(default="audit.log_created")
    aggregate_type: Literal["audit"] = Field(default="audit")
    category: Literal[EventCategory.AUDIT] = Field(default=EventCategory.AUDIT)
    
    audit_log_id: str = Field(..., description="Audit log identifier")
    log_type: str = Field(..., description="Type of audit log")
    user_id: Optional[str] = Field(None, description="User associated with action")
    
    # Action details
    action: str = Field(..., description="Action performed")
    resource_type: str = Field(..., description="Type of resource")
    resource_id: Optional[str] = Field(None, description="Resource identifier")
    outcome: str = Field(..., description="Action outcome")
    
    # Compliance
    compliance_framework: List[str] = Field(default_factory=list, description="Applicable compliance frameworks")
    retention_required_until: Optional[datetime] = Field(None, description="Retention requirement")
    tamper_proof: bool = Field(True, description="Tamper-proof status")


class ComplianceViolationDetected(BaseEvent):
    """Event published when a compliance violation is detected."""
    
    event_type: Literal["audit.compliance_violation"] = Field(default="audit.compliance_violation")
    aggregate_type: Literal["audit"] = Field(default="audit")
    category: Literal[EventCategory.COMPLIANCE] = Field(default=EventCategory.COMPLIANCE)
    priority: Literal[EventPriority.CRITICAL] = Field(default=EventPriority.CRITICAL)
    
    violation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Violation identifier")
    compliance_framework: str = Field(..., description="Violated compliance framework")
    regulation: str = Field(..., description="Specific regulation violated")
    severity: str = Field(..., description="Violation severity")
    
    # Details
    violation_description: str = Field(..., description="Detailed description")
    affected_resources: List[str] = Field(default_factory=list, description="Affected resource IDs")
    detection_method: str = Field(..., description="Detection method")
    
    # Response
    remediation_required: bool = Field(True, description="Remediation required")
    notification_required: bool = Field(True, description="Notification required")
    investigation_triggered: bool = Field(False, description="Investigation status")


# ============================================
# IRIS API EVENTS
# ============================================

class IRISConnectionEstablished(BaseEvent):
    """Event published when IRIS API connection is established."""
    
    event_type: Literal["iris.connection_established"] = Field(default="iris.connection_established")
    aggregate_type: Literal["iris"] = Field(default="iris")
    category: Literal[EventCategory.IRIS_API] = Field(default=EventCategory.IRIS_API)
    
    endpoint_id: str = Field(..., description="IRIS endpoint identifier")
    endpoint_url: str = Field(..., description="IRIS endpoint URL")
    connection_id: str = Field(..., description="Connection identifier")
    
    # Connection details
    authentication_method: str = Field(..., description="Authentication method used")
    connection_latency_ms: Optional[int] = Field(None, description="Connection latency")
    api_version: Optional[str] = Field(None, description="IRIS API version")
    
    # Health check
    health_check_passed: bool = Field(True, description="Initial health check status")
    capabilities_verified: bool = Field(False, description="Capabilities verification")


class IRISDataSynchronized(BaseEvent):
    """Event published when data is synchronized with IRIS."""
    
    event_type: Literal["iris.data_synchronized"] = Field(default="iris.data_synchronized")
    aggregate_type: Literal["iris"] = Field(default="iris")
    category: Literal[EventCategory.IRIS_API] = Field(default=EventCategory.IRIS_API)
    
    sync_id: str = Field(..., description="Synchronization identifier")
    endpoint_id: str = Field(..., description="IRIS endpoint identifier")
    sync_type: str = Field(..., description="Type of synchronization")
    
    # Sync details
    records_processed: int = Field(..., description="Number of records processed")
    records_successful: int = Field(..., description="Successful records")
    records_failed: int = Field(default=0, description="Failed records")
    
    # Performance
    sync_duration_ms: int = Field(..., description="Synchronization duration")
    throughput_records_per_second: float = Field(..., description="Processing throughput")
    
    # Quality
    data_quality_score: Optional[float] = Field(None, description="Data quality score")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")


class IRISAPIError(BaseEvent):
    """Event published when IRIS API error occurs."""
    
    event_type: Literal["iris.api_error"] = Field(default="iris.api_error")
    aggregate_type: Literal["iris"] = Field(default="iris")
    category: Literal[EventCategory.IRIS_API] = Field(default=EventCategory.IRIS_API)
    priority: Literal[EventPriority.HIGH] = Field(default=EventPriority.HIGH)
    
    error_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Error identifier")
    endpoint_id: str = Field(..., description="IRIS endpoint identifier")
    operation: str = Field(..., description="Failed operation")
    
    # Error details
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Error type category")
    
    # Context
    request_data: Optional[Dict[str, Any]] = Field(None, description="Request data (sanitized)")
    response_status: Optional[int] = Field(None, description="HTTP response status")
    retry_count: int = Field(default=0, description="Retry attempt count")
    
    # Circuit breaker
    circuit_breaker_triggered: bool = Field(False, description="Circuit breaker status")
    service_degraded: bool = Field(False, description="Service degradation flag")


# ============================================
# ANALYTICS EVENTS
# ============================================

class AnalyticsCalculationCompleted(BaseEvent):
    """Event published when analytics calculation is completed."""
    
    event_type: Literal["analytics.calculation_completed"] = Field(default="analytics.calculation_completed")
    aggregate_type: Literal["analytics"] = Field(default="analytics")
    category: Literal[EventCategory.ANALYTICS] = Field(default=EventCategory.ANALYTICS)
    
    calculation_id: str = Field(..., description="Calculation identifier")
    calculation_type: str = Field(..., description="Type of calculation")
    scope: str = Field(..., description="Calculation scope (patient/population/system)")
    
    # Calculation details
    data_points_processed: int = Field(..., description="Data points processed")
    calculation_duration_ms: int = Field(..., description="Calculation duration")
    results_generated: int = Field(..., description="Number of results generated")
    
    # Quality
    confidence_score: Optional[float] = Field(None, description="Result confidence score")
    data_completeness: float = Field(..., description="Data completeness percentage")
    
    # Metadata
    algorithm_version: str = Field(..., description="Algorithm version used")
    baseline_comparison: Optional[Dict[str, Any]] = Field(None, description="Baseline comparison data")


class ReportGenerated(BaseEvent):
    """Event published when a report is generated."""
    
    event_type: Literal["analytics.report_generated"] = Field(default="analytics.report_generated")
    aggregate_type: Literal["analytics"] = Field(default="analytics")
    category: Literal[EventCategory.ANALYTICS] = Field(default=EventCategory.ANALYTICS)
    
    report_id: str = Field(..., description="Report identifier")
    report_type: str = Field(..., description="Type of report")
    report_format: str = Field(..., description="Report format (PDF/Excel/JSON)")
    
    # Report details
    generated_by_user_id: str = Field(..., description="User who generated report")
    report_period_start: Optional[datetime] = Field(None, description="Report period start")
    report_period_end: Optional[datetime] = Field(None, description="Report period end")
    
    # Content
    pages_generated: Optional[int] = Field(None, description="Number of pages")
    charts_included: int = Field(default=0, description="Number of charts")
    data_sources: List[str] = Field(default_factory=list, description="Data sources used")
    
    # Distribution
    scheduled_delivery: bool = Field(False, description="Scheduled delivery flag")
    recipients: List[str] = Field(default_factory=list, description="Report recipients")


# ============================================
# CONSENT EVENTS
# ============================================

class ConsentProvided(BaseEvent):
    """Event published when patient consent is provided."""
    
    event_type: Literal["consent.provided"] = Field(default="consent.provided")
    aggregate_type: Literal["consent"] = Field(default="consent")
    category: Literal[EventCategory.CONSENT] = Field(default=EventCategory.CONSENT)
    priority: Literal[EventPriority.HIGH] = Field(default=EventPriority.HIGH)
    
    consent_id: str = Field(..., description="Consent record identifier")
    patient_id: str = Field(..., description="Patient identifier")
    consent_type: str = Field(..., description="Type of consent")
    
    # Consent details
    consent_scope: List[str] = Field(..., description="Scope of consent")
    purposes: List[str] = Field(..., description="Purposes for which consent is given")
    data_categories: List[str] = Field(..., description="Data categories covered")
    
    # Legal
    legal_basis: str = Field(..., description="Legal basis for processing")
    consent_mechanism: str = Field(..., description="How consent was obtained")
    witness_present: bool = Field(False, description="Witness present flag")
    
    # Validity
    effective_date: datetime = Field(..., description="Consent effective date")
    expiration_date: Optional[datetime] = Field(None, description="Consent expiration")
    revocable: bool = Field(True, description="Whether consent can be revoked")
    
    # Metadata
    obtained_by_user_id: str = Field(..., description="User who obtained consent")
    consent_version: str = Field(..., description="Consent form version")


class ConsentRevoked(BaseEvent):
    """Event published when patient consent is revoked."""
    
    event_type: Literal["consent.revoked"] = Field(default="consent.revoked")
    aggregate_type: Literal["consent"] = Field(default="consent")
    category: Literal[EventCategory.CONSENT] = Field(default=EventCategory.CONSENT)
    priority: Literal[EventPriority.CRITICAL] = Field(default=EventPriority.CRITICAL)
    
    consent_id: str = Field(..., description="Consent record identifier")
    patient_id: str = Field(..., description="Patient identifier")
    revocation_reason: str = Field(..., description="Reason for revocation")
    
    # Revocation details
    revoked_by_patient: bool = Field(True, description="Revoked by patient flag")
    effective_immediately: bool = Field(True, description="Immediate effect flag")
    partial_revocation: bool = Field(False, description="Partial revocation flag")
    affected_data_categories: List[str] = Field(default_factory=list, description="Affected data categories")
    
    # Actions required
    data_processing_halt_required: bool = Field(True, description="Halt processing requirement")
    data_deletion_required: bool = Field(False, description="Data deletion requirement")
    notification_required: bool = Field(True, description="Notification requirement")
    
    # Metadata
    revoked_by_user_id: Optional[str] = Field(None, description="User who processed revocation")
    revocation_effective_date: datetime = Field(default_factory=datetime.utcnow)


# ============================================
# EVENT TYPE REGISTRY
# ============================================

# Registry of all event types for validation and introspection
EVENT_TYPE_REGISTRY = {
    # Patient events
    "patient.created": PatientCreated,
    "patient.updated": PatientUpdated,
    "patient.deactivated": PatientDeactivated,
    "patient.merged": PatientMerged,
    
    # Immunization events
    "immunization.recorded": ImmunizationRecorded,
    "immunization.updated": ImmunizationUpdated,
    "immunization.deleted": ImmunizationDeleted,
    
    # Document events
    "document.uploaded": DocumentUploaded,
    "document.classified": DocumentClassified,
    "document.processed": DocumentProcessed,
    "document.version_created": DocumentVersionCreated,
    
    # Clinical workflow events
    "workflow.instance_created": WorkflowInstanceCreated,
    "workflow.step_completed": WorkflowStepCompleted,
    "workflow.instance_completed": WorkflowInstanceCompleted,
    
    # Security events
    "security.violation_detected": SecurityViolationDetected,
    "security.unauthorized_access": UnauthorizedAccessAttempt,
    "security.phi_access": PHIAccessLogged,
    
    # Audit events
    "audit.log_created": AuditLogCreated,
    "audit.compliance_violation": ComplianceViolationDetected,
    
    # IRIS API events
    "iris.connection_established": IRISConnectionEstablished,
    "iris.data_synchronized": IRISDataSynchronized,
    "iris.api_error": IRISAPIError,
    
    # Analytics events
    "analytics.calculation_completed": AnalyticsCalculationCompleted,
    "analytics.report_generated": ReportGenerated,
    
    # Consent events
    "consent.provided": ConsentProvided,
    "consent.revoked": ConsentRevoked
}


def get_event_class(event_type: str) -> Optional[type]:
    """Get event class by event type string."""
    return EVENT_TYPE_REGISTRY.get(event_type)


def validate_event_type(event_type: str) -> bool:
    """Validate that event type is registered."""
    return event_type in EVENT_TYPE_REGISTRY


def get_events_by_category(category: EventCategory) -> List[type]:
    """Get all event classes for a specific category."""
    return [
        event_class for event_class in EVENT_TYPE_REGISTRY.values()
        if hasattr(event_class, 'category') and 
        getattr(event_class.category, 'default', None) == category
    ]


def get_event_categories() -> List[EventCategory]:
    """Get all available event categories."""
    return list(EventCategory)
