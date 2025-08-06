"""
Clinical Validation Framework Schemas for Healthcare Platform V2.0

Comprehensive data models for clinical validation, quality assurance,
and regulatory compliance in healthcare AI systems.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
import uuid

# Validation enums

class ValidationStatus(str, Enum):
    """Clinical validation status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"
    APPROVED = "approved"
    REJECTED = "rejected"

class ValidationLevel(str, Enum):
    """Clinical validation level."""
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    REGULATORY = "regulatory"
    FDA_SUBMISSION = "fda_submission"

class ValidationCategory(str, Enum):
    """Clinical validation category."""
    SAFETY = "safety"
    EFFICACY = "efficacy"
    PERFORMANCE = "performance"
    USABILITY = "usability"
    INTEROPERABILITY = "interoperability"
    SECURITY = "security"
    REGULATORY = "regulatory"

class ClinicalDomain(str, Enum):
    """Clinical domain for validation."""
    CARDIOLOGY = "cardiology"
    RADIOLOGY = "radiology"
    PATHOLOGY = "pathology"
    EMERGENCY = "emergency"
    ONCOLOGY = "oncology"
    PEDIATRICS = "pediatrics"
    SURGERY = "surgery"
    CRITICAL_CARE = "critical_care"
    PRIMARY_CARE = "primary_care"
    MENTAL_HEALTH = "mental_health"

class EvidenceLevel(str, Enum):
    """Level of clinical evidence."""
    LEVEL_1 = "level_1"  # Systematic review, meta-analysis
    LEVEL_2 = "level_2"  # RCT
    LEVEL_3 = "level_3"  # Controlled cohort
    LEVEL_4 = "level_4"  # Case-control
    LEVEL_5 = "level_5"  # Case series
    EXPERT_OPINION = "expert_opinion"

class RegulatoryStandard(str, Enum):
    """Regulatory standards."""
    FDA_510K = "fda_510k"
    FDA_PMA = "fda_pma"
    CE_MARK = "ce_mark"
    ISO_13485 = "iso_13485"
    ISO_14155 = "iso_14155"
    ICH_GCP = "ich_gcp"
    HIPAA = "hipaa"
    GDPR = "gdpr"

# Core validation models

class ClinicalMetrics(BaseModel):
    """Clinical performance metrics."""
    sensitivity: Optional[float] = Field(None, ge=0.0, le=1.0)
    specificity: Optional[float] = Field(None, ge=0.0, le=1.0)
    ppv: Optional[float] = Field(None, ge=0.0, le=1.0)  # Positive predictive value
    npv: Optional[float] = Field(None, ge=0.0, le=1.0)  # Negative predictive value
    accuracy: Optional[float] = Field(None, ge=0.0, le=1.0)
    auc_roc: Optional[float] = Field(None, ge=0.0, le=1.0)
    f1_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    precision: Optional[float] = Field(None, ge=0.0, le=1.0)
    recall: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Clinical-specific metrics
    false_positive_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    false_negative_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    diagnostic_odds_ratio: Optional[float] = Field(None, gt=0.0)
    likelihood_ratio_positive: Optional[float] = Field(None, gt=0.0)
    likelihood_ratio_negative: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Performance metrics
    processing_time_ms: Optional[float] = Field(None, gt=0.0)
    throughput_per_hour: Optional[int] = Field(None, gt=0)
    memory_usage_mb: Optional[float] = Field(None, gt=0.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "sensitivity": 0.92,
                "specificity": 0.88,
                "ppv": 0.85,
                "npv": 0.94,
                "accuracy": 0.90,
                "auc_roc": 0.93,
                "f1_score": 0.89,
                "processing_time_ms": 150.5,
                "throughput_per_hour": 2400
            }
        }

class StudyPopulation(BaseModel):
    """Clinical study population characteristics."""
    total_subjects: int = Field(..., gt=0)
    age_range: Dict[str, float] = Field(..., description="min and max age")
    gender_distribution: Dict[str, float] = Field(default_factory=dict)
    ethnicity_distribution: Dict[str, float] = Field(default_factory=dict)
    comorbidity_prevalence: Dict[str, float] = Field(default_factory=dict)
    inclusion_criteria: List[str] = Field(default_factory=list)
    exclusion_criteria: List[str] = Field(default_factory=list)
    recruitment_period: Dict[str, datetime] = Field(default_factory=dict)
    dropout_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    @field_validator('age_range')
    @classmethod
    def validate_age_range(cls, v):
        if 'min' not in v or 'max' not in v:
            raise ValueError('Age range must contain min and max values')
        if v['min'] >= v['max']:
            raise ValueError('Minimum age must be less than maximum age')
        return v

class ClinicalEndpoint(BaseModel):
    """Clinical study endpoint definition."""
    endpoint_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    endpoint_name: str
    endpoint_type: str = Field(..., pattern="^(primary|secondary|exploratory)$")
    description: str
    measurement_method: str
    measurement_units: Optional[str] = None
    target_value: Optional[float] = None
    target_range: Optional[Dict[str, float]] = None
    clinical_significance_threshold: Optional[float] = None
    statistical_power: Optional[float] = Field(None, ge=0.0, le=1.0)
    
class ValidationProtocol(BaseModel):
    """Clinical validation protocol."""
    protocol_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    protocol_name: str
    protocol_version: str = Field(default="1.0")
    validation_level: ValidationLevel
    clinical_domain: ClinicalDomain
    regulatory_standards: List[RegulatoryStandard]
    
    # Study design
    study_design: str  # RCT, observational, retrospective, etc.
    study_duration_days: int = Field(..., gt=0)
    sample_size_calculation: Dict[str, Any]
    randomization_method: Optional[str] = None
    blinding_method: Optional[str] = None
    
    # Endpoints
    primary_endpoints: List[ClinicalEndpoint]
    secondary_endpoints: List[ClinicalEndpoint] = Field(default_factory=list)
    
    # Population
    target_population: StudyPopulation
    
    # Validation criteria
    success_criteria: Dict[str, Any]
    stopping_rules: List[str] = Field(default_factory=list)
    interim_analysis_plan: Optional[Dict[str, Any]] = None
    
    # Regulatory
    irb_approval_required: bool = True
    informed_consent_required: bool = True
    data_monitoring_committee: bool = False
    
    created_by: str
    created_date: datetime = Field(default_factory=datetime.utcnow)
    approved_by: Optional[str] = None
    approval_date: Optional[datetime] = None

class ValidationEvidence(BaseModel):
    """Clinical validation evidence."""
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    evidence_type: str  # study_result, literature_review, expert_opinion
    evidence_level: EvidenceLevel
    study_reference: Optional[str] = None
    publication_reference: Optional[str] = None
    
    # Study details
    study_population_size: Optional[int] = None
    study_design: Optional[str] = None
    study_duration: Optional[str] = None
    
    # Results
    primary_outcome_results: Dict[str, Any] = Field(default_factory=dict)
    secondary_outcome_results: Dict[str, Any] = Field(default_factory=dict)
    safety_outcomes: Dict[str, Any] = Field(default_factory=dict)
    
    # Statistical analysis
    statistical_methods: List[str] = Field(default_factory=list)
    confidence_intervals: Dict[str, List[float]] = Field(default_factory=dict)
    p_values: Dict[str, float] = Field(default_factory=dict)
    effect_sizes: Dict[str, float] = Field(default_factory=dict)
    
    # Quality assessment
    bias_assessment: Dict[str, str] = Field(default_factory=dict)
    quality_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    limitations: List[str] = Field(default_factory=list)
    
    # Metadata
    extracted_by: str
    extraction_date: datetime = Field(default_factory=datetime.utcnow)
    verified_by: Optional[str] = None
    verification_date: Optional[datetime] = None

class ValidationStudy(BaseModel):
    """Clinical validation study."""
    study_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    study_name: str
    study_type: str  # prospective, retrospective, meta_analysis
    protocol_id: str
    
    # Study status
    status: ValidationStatus = ValidationStatus.PENDING
    enrollment_status: str = Field(default="not_started")
    
    # Study sites and investigators
    principal_investigator: Dict[str, str]
    study_sites: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Timeline
    planned_start_date: datetime
    planned_end_date: datetime
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    
    # Population
    target_enrollment: int = Field(..., gt=0)
    actual_enrollment: int = Field(default=0, ge=0)
    screened_subjects: int = Field(default=0, ge=0)
    randomized_subjects: int = Field(default=0, ge=0)
    completed_subjects: int = Field(default=0, ge=0)
    
    # Data collection
    data_collection_progress: float = Field(default=0.0, ge=0.0, le=1.0)
    case_report_forms_completed: int = Field(default=0, ge=0)
    data_quality_checks_passed: int = Field(default=0, ge=0)
    
    # Interim results
    interim_analyses: List[Dict[str, Any]] = Field(default_factory=list)
    safety_reports: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Final results
    final_metrics: Optional[ClinicalMetrics] = None
    final_report_date: Optional[datetime] = None
    regulatory_submission_date: Optional[datetime] = None
    
    # Metadata
    created_by: str
    created_date: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class ValidationReport(BaseModel):
    """Clinical validation report."""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_type: str  # interim, final, regulatory
    study_id: str
    protocol_id: str
    
    # Report metadata
    report_version: str = Field(default="1.0")
    report_date: datetime = Field(default_factory=datetime.utcnow)
    reporting_period_start: datetime
    reporting_period_end: datetime
    
    # Executive summary
    executive_summary: str
    key_findings: List[str]
    recommendations: List[str]
    
    # Study results
    primary_endpoint_results: Dict[str, Any]
    secondary_endpoint_results: Dict[str, Any] = Field(default_factory=dict)
    safety_analysis: Dict[str, Any] = Field(default_factory=dict)
    
    # Statistical analysis
    statistical_analysis_plan: str
    statistical_methods_used: List[str]
    missing_data_handling: str
    sensitivity_analyses: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Quality metrics
    overall_metrics: ClinicalMetrics
    subgroup_analyses: Dict[str, ClinicalMetrics] = Field(default_factory=dict)
    
    # Regulatory compliance
    regulatory_compliance_status: Dict[RegulatoryStandard, str] = Field(default_factory=dict)
    deviations_from_protocol: List[Dict[str, Any]] = Field(default_factory=list)
    adverse_events: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Evidence summary
    supporting_evidence: List[str] = Field(default_factory=list)  # Evidence IDs
    evidence_synthesis: str
    grade_of_evidence: EvidenceLevel
    
    # Conclusions
    conclusions: str
    limitations: List[str]
    future_research_needs: List[str] = Field(default_factory=list)
    
    # Approval workflow
    prepared_by: str
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None
    approval_date: Optional[datetime] = None
    
    class Config:
        use_enum_values = True

class ValidationDashboard(BaseModel):
    """Clinical validation dashboard data."""
    dashboard_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generated_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Summary statistics
    total_studies: int = Field(default=0, ge=0)
    active_studies: int = Field(default=0, ge=0)
    completed_studies: int = Field(default=0, ge=0)
    
    # Status distribution
    study_status_distribution: Dict[ValidationStatus, int] = Field(default_factory=dict)
    validation_level_distribution: Dict[ValidationLevel, int] = Field(default_factory=dict)
    clinical_domain_distribution: Dict[ClinicalDomain, int] = Field(default_factory=dict)
    
    # Performance metrics
    average_study_duration_days: Optional[float] = None
    average_enrollment_rate: Optional[float] = None
    overall_success_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Quality indicators
    protocol_adherence_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    data_quality_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    regulatory_compliance_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Recent activities
    recent_study_completions: List[Dict[str, Any]] = Field(default_factory=list)
    upcoming_milestones: List[Dict[str, Any]] = Field(default_factory=list)
    overdue_activities: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Alerts and notifications
    critical_alerts: List[Dict[str, Any]] = Field(default_factory=list)
    safety_notifications: List[Dict[str, Any]] = Field(default_factory=list)
    regulatory_updates: List[Dict[str, Any]] = Field(default_factory=list)

# Request/Response models

class ValidationStudyRequest(BaseModel):
    """Request to create a validation study."""
    study_name: str
    study_type: str
    protocol_id: str
    principal_investigator: Dict[str, str]
    planned_start_date: datetime
    planned_end_date: datetime
    target_enrollment: int = Field(..., gt=0)
    study_sites: List[Dict[str, Any]] = Field(default_factory=list)

class ValidationReportRequest(BaseModel):
    """Request to generate a validation report."""
    report_type: str
    study_id: str
    reporting_period_start: datetime
    reporting_period_end: datetime
    include_interim_data: bool = True
    include_safety_analysis: bool = True
    regulatory_standards: List[RegulatoryStandard] = Field(default_factory=list)

class EvidenceExtractionRequest(BaseModel):
    """Request for evidence extraction."""
    study_reference: str
    extraction_type: str  # automated, manual, hybrid
    target_endpoints: List[str] = Field(default_factory=list)
    quality_assessment_required: bool = True

class ValidationConfiguration(BaseModel):
    """Clinical validation system configuration."""
    default_validation_level: ValidationLevel = ValidationLevel.STANDARD
    require_irb_approval: bool = True
    require_informed_consent: bool = True
    minimum_sample_size: int = Field(default=30, gt=0)
    maximum_study_duration_days: int = Field(default=365, gt=0)
    
    # Quality thresholds
    minimum_sensitivity: float = Field(default=0.8, ge=0.0, le=1.0)
    minimum_specificity: float = Field(default=0.8, ge=0.0, le=1.0)
    minimum_accuracy: float = Field(default=0.85, ge=0.0, le=1.0)
    
    # Regulatory settings
    fda_submission_required_for: List[ClinicalDomain] = Field(default_factory=list)
    ce_mark_required_for_eu: bool = True
    
    # Notification settings
    send_milestone_notifications: bool = True
    send_safety_alerts: bool = True
    notification_recipients: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True

# Create/Update/Response schemas for CRUD operations

class ValidationStudyCreate(BaseModel):
    """Create schema for validation study."""
    study_name: str
    study_type: str
    protocol_id: str
    principal_investigator: Dict[str, str]
    planned_start_date: datetime
    planned_end_date: datetime
    target_enrollment: int = Field(..., gt=0)
    study_sites: List[Dict[str, Any]] = Field(default_factory=list)

class ValidationStudyUpdate(BaseModel):
    """Update schema for validation study."""
    study_name: Optional[str] = None
    status: Optional[ValidationStatus] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    actual_enrollment: Optional[int] = None
    data_collection_progress: Optional[float] = Field(None, ge=0.0, le=1.0)

class ValidationStudyResponse(BaseModel):
    """Response schema for validation study."""
    study_id: str
    study_name: str
    study_type: str
    protocol_id: str
    status: ValidationStatus
    enrollment_status: str
    target_enrollment: int
    actual_enrollment: int
    created_date: datetime
    last_updated: datetime
    
    class Config:
        from_attributes = True

class ValidationProtocolCreate(BaseModel):
    """Create schema for validation protocol."""
    protocol_name: str
    protocol_version: str = Field(default="1.0")
    validation_level: ValidationLevel
    clinical_domain: ClinicalDomain
    regulatory_standards: List[RegulatoryStandard]
    study_design: str
    study_duration_days: int = Field(..., gt=0)
    sample_size_calculation: Dict[str, Any]
    success_criteria: Dict[str, Any]

class ValidationProtocolUpdate(BaseModel):
    """Update schema for validation protocol."""
    protocol_name: Optional[str] = None
    protocol_version: Optional[str] = None
    study_duration_days: Optional[int] = Field(None, gt=0)
    success_criteria: Optional[Dict[str, Any]] = None
    approved_by: Optional[str] = None
    approval_date: Optional[datetime] = None

class ValidationProtocolResponse(BaseModel):
    """Response schema for validation protocol."""
    protocol_id: str
    protocol_name: str
    protocol_version: str
    validation_level: ValidationLevel
    clinical_domain: ClinicalDomain
    regulatory_standards: List[RegulatoryStandard]
    study_design: str
    created_date: datetime
    approved_by: Optional[str] = None
    
    class Config:
        from_attributes = True

class ValidationEvidenceCreate(BaseModel):
    """Create schema for validation evidence."""
    evidence_type: str
    evidence_level: EvidenceLevel
    study_reference: Optional[str] = None
    publication_reference: Optional[str] = None
    study_population_size: Optional[int] = None
    study_design: Optional[str] = None

class ValidationEvidenceUpdate(BaseModel):
    """Update schema for validation evidence."""
    evidence_level: Optional[EvidenceLevel] = None
    study_population_size: Optional[int] = None
    quality_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    verified_by: Optional[str] = None
    verification_date: Optional[datetime] = None

class ValidationEvidenceResponse(BaseModel):
    """Response schema for validation evidence."""
    evidence_id: str
    evidence_type: str
    evidence_level: EvidenceLevel
    study_reference: Optional[str] = None
    publication_reference: Optional[str] = None
    quality_score: Optional[float] = None
    extraction_date: datetime
    
    class Config:
        from_attributes = True

class ValidationReportResponse(BaseModel):
    """Response schema for validation report."""
    report_id: str
    report_type: str
    study_id: str
    protocol_id: str
    report_version: str
    report_date: datetime
    executive_summary: str
    key_findings: List[str]
    conclusions: str
    prepared_by: str
    approved_by: Optional[str] = None
    
    class Config:
        from_attributes = True

class ClinicalMetricsResponse(BaseModel):
    """Response schema for clinical metrics."""
    sensitivity: Optional[float] = None
    specificity: Optional[float] = None
    accuracy: Optional[float] = None
    auc_roc: Optional[float] = None
    f1_score: Optional[float] = None
    processing_time_ms: Optional[float] = None
    throughput_per_hour: Optional[int] = None
    
    class Config:
        from_attributes = True

class ValidationDashboardResponse(BaseModel):
    """Response schema for validation dashboard."""
    dashboard_id: str
    generated_date: datetime
    total_studies: int
    active_studies: int
    completed_studies: int
    study_status_distribution: Dict[str, int]
    average_study_duration_days: Optional[float] = None
    overall_success_rate: Optional[float] = None
    
    class Config:
        from_attributes = True

# Request schemas for complex operations

class StudyProgressRequest(BaseModel):
    """Request schema for study progress monitoring."""
    study_id: str
    progress_metrics: Dict[str, Any]
    milestone_updates: List[Dict[str, Any]] = Field(default_factory=list)
    safety_updates: List[Dict[str, Any]] = Field(default_factory=list)

class StatisticalAnalysisRequest(BaseModel):
    """Request schema for statistical analysis."""
    study_id: str
    analysis_type: str
    data_points: List[Dict[str, Any]]
    confidence_level: float = Field(default=0.95, ge=0.0, le=1.0)
    include_subgroup_analysis: bool = False

class EvidenceSynthesisRequest(BaseModel):
    """Request schema for evidence synthesis."""
    evidence_ids: List[str]
    synthesis_method: str = Field(default="meta_analysis")
    quality_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    include_unpublished: bool = False