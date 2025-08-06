"""
Risk Stratification Schemas
SOC2 Type 2 Compliant Data Models for Risk Assessment
Following SOLID principles and TDD approach
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime
import uuid

# ============================================
# ENUMS AND CONSTANTS
# ============================================

class RiskLevel(str, Enum):
    """Patient risk levels for clinical decision support"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class RiskFactorCategory(str, Enum):
    """Categories of risk factors for classification"""
    CLINICAL = "clinical"
    BEHAVIORAL = "behavioral"
    SOCIAL_DETERMINANTS = "social_determinants"
    UTILIZATION = "utilization"
    MEDICATION = "medication"
    LABORATORY = "laboratory"

class CareCategory(str, Enum):
    """Categories of care recommendations"""
    MEDICATION_MANAGEMENT = "medication_management"
    LIFESTYLE_MODIFICATION = "lifestyle_modification"
    CLINICAL_FOLLOW_UP = "clinical_follow_up"
    SPECIALIST_REFERRAL = "specialist_referral"
    DIAGNOSTIC_TESTING = "diagnostic_testing"
    PATIENT_EDUCATION = "patient_education"
    CARE_COORDINATION = "care_coordination"
    EMERGENCY_INTERVENTION = "emergency_intervention"

class RecommendationPriority(str, Enum):
    """Priority levels for care recommendations"""
    IMMEDIATE = "immediate"
    URGENT = "urgent"
    ROUTINE = "routine"
    PREVENTIVE = "preventive"

class EvidenceLevel(str, Enum):
    """Evidence levels for clinical recommendations"""
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"

# ============================================
# REQUEST SCHEMAS
# ============================================

class RiskScoreRequest(BaseModel):
    """Request schema for risk score calculation - SOC2 compliant"""
    patient_id: str = Field(..., description="Patient UUID", pattern=r'^[0-9a-f-]{36}$')
    include_recommendations: bool = Field(default=True, description="Include care recommendations")
    include_readmission_risk: bool = Field(default=False, description="Include readmission risk assessment")
    time_horizon: Optional[str] = Field(default="30_days", description="Time horizon for risk assessment")
    clinical_context: Optional[Dict[str, Any]] = Field(default={}, description="Additional clinical context")
    
    # SOC2 CC6.1: Access control metadata
    requesting_user_id: str = Field(..., description="User requesting risk calculation")
    access_purpose: str = Field(default="clinical_care", description="Purpose of risk assessment")
    
    class Config:
        schema_extra = {
            "example": {
                "patient_id": "123e4567-e89b-12d3-a456-426614174000",
                "include_recommendations": True,
                "include_readmission_risk": True,
                "time_horizon": "30_days",
                "requesting_user_id": "user123",
                "access_purpose": "clinical_care"
            }
        }

class BatchRiskRequest(BaseModel):
    """Request schema for batch risk calculation - SOC2 compliant"""
    patient_ids: List[str] = Field(..., max_items=1000, description="List of patient UUIDs")
    include_recommendations: bool = Field(default=False, description="Include care recommendations")
    batch_size: int = Field(default=50, le=100, description="Processing batch size")
    
    # SOC2 CC6.1: Access control metadata
    requesting_user_id: str = Field(..., description="User requesting batch calculation")
    access_purpose: str = Field(default="population_analytics", description="Purpose of batch assessment")
    organization_id: Optional[str] = Field(None, description="Organization filter")
    
    @field_validator('patient_ids')
    @classmethod
    def validate_patient_ids(cls, v):
        """Validate patient ID format and prevent injection attacks"""
        import re
        uuid_pattern = re.compile(r'^[0-9a-f-]{36}$')
        for patient_id in v:
            if not uuid_pattern.match(patient_id):
                raise ValueError(f'Invalid patient ID format: {patient_id}')
        return v

class PopulationMetricsRequest(BaseModel):
    """Request schema for population health metrics"""
    cohort_criteria: Dict[str, Any] = Field(default={}, description="Cohort selection criteria")
    metrics_requested: List[str] = Field(default=["risk_distribution"], description="Metrics to calculate")
    time_range_days: int = Field(default=90, le=365, description="Time range for analysis")
    
    # SOC2 CC6.1: Access control
    requesting_user_id: str = Field(..., description="User requesting population metrics")
    organization_id: Optional[str] = Field(None, description="Organization scope")

# ============================================
# CORE DATA MODELS
# ============================================

class RiskFactor(BaseModel):
    """Individual risk factor with clinical evidence"""
    factor_id: str = Field(..., description="Unique risk factor identifier")
    category: RiskFactorCategory = Field(..., description="Risk factor category")
    severity: str = Field(..., pattern=r'^(low|moderate|high|critical)$', description="Risk severity level")
    description: str = Field(..., min_length=10, description="Human-readable description")
    clinical_basis: str = Field(..., min_length=20, description="Clinical evidence and rationale")
    weight: float = Field(..., ge=0.0, le=1.0, description="Impact weight on overall score")
    evidence_level: EvidenceLevel = Field(..., description="Strength of clinical evidence")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Config:
        use_enum_values = True

class ActionItem(BaseModel):
    """Actionable item within a care recommendation"""
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique action identifier")
    description: str = Field(..., min_length=10, description="Action description")
    responsible: str = Field(..., description="Responsible care team member/role")
    due_date: Optional[datetime] = Field(None, description="Due date for action")
    is_completed: bool = Field(default=False, description="Completion status")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

class CareRecommendation(BaseModel):
    """Evidence-based care recommendation"""
    recommendation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique recommendation ID")
    priority: RecommendationPriority = Field(..., description="Clinical priority level")
    category: CareCategory = Field(..., description="Type of care intervention")
    description: str = Field(..., min_length=20, description="Recommendation description")
    clinical_rationale: str = Field(..., min_length=30, description="Clinical justification")
    action_items: List[ActionItem] = Field(default=[], description="Specific actionable steps")
    timeframe: str = Field(..., description="Recommended timeframe for implementation")
    assigned_to: Optional[str] = Field(None, description="Assigned care team member")
    status: str = Field(default="pending", pattern=r'^(pending|in_progress|completed|overdue)$')
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    due_date: Optional[datetime] = Field(None, description="Due date for recommendation")
    
    class Config:
        use_enum_values = True

class ModelMetadata(BaseModel):
    """Machine learning model metadata for transparency"""
    model_version: str = Field(..., description="Model version identifier")
    accuracy: float = Field(..., ge=0.0, le=1.0, description="Model accuracy score")
    precision: float = Field(..., ge=0.0, le=1.0, description="Model precision score")
    recall: float = Field(..., ge=0.0, le=1.0, description="Model recall score")
    last_trained: str = Field(..., description="Last training date")
    training_data_size: int = Field(..., ge=0, description="Training dataset size")

# ============================================
# RESPONSE SCHEMAS
# ============================================

class RiskScoreResponse(BaseModel):
    """Response schema for risk score calculation - SOC2 compliant"""
    patient_id: str = Field(..., description="Patient UUID")
    calculated_at: datetime = Field(..., description="Calculation timestamp")
    calculated_by: str = Field(..., description="User who calculated score")
    score: float = Field(..., ge=0.0, le=100.0, description="Risk score (0-100)")
    level: RiskLevel = Field(..., description="Risk level classification")
    factors: List[RiskFactor] = Field(default=[], description="Contributing risk factors")
    recommendations: Optional[List[CareRecommendation]] = Field(None, description="Care recommendations")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score")
    expires_at: datetime = Field(..., description="Score expiration timestamp")
    
    # SOC2 CC7.2: Audit trail
    audit_trail: List[Dict[str, Any]] = Field(default=[], description="Audit log entries")
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "patient_id": "123e4567-e89b-12d3-a456-426614174000",
                "calculated_at": "2024-01-15T10:30:00Z",
                "calculated_by": "user123",
                "score": 65.5,
                "level": "high",
                "confidence": 0.87,
                "expires_at": "2024-01-16T10:30:00Z"
            }
        }

class BatchRiskResponse(BaseModel):
    """Response schema for batch risk calculation"""
    batch_id: str = Field(..., description="Batch processing identifier")
    requested_count: int = Field(..., description="Number of patients requested")
    processed_count: int = Field(..., description="Number successfully processed")
    failed_count: int = Field(..., description="Number of failed calculations")
    risk_scores: List[RiskScoreResponse] = Field(..., description="Calculated risk scores")
    processing_time_ms: int = Field(..., description="Total processing time")
    
    # SOC2 CC7.2: Batch processing audit
    audit_summary: Dict[str, Any] = Field(default={}, description="Batch processing audit summary")

class RiskFactorsResponse(BaseModel):
    """Response schema for risk factors analysis"""
    patient_id: str = Field(..., description="Patient UUID")
    factors: List[RiskFactor] = Field(..., description="Identified risk factors")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Composite risk score")
    analysis_timestamp: datetime = Field(..., description="Analysis timestamp")
    clinical_summary: str = Field(..., description="Clinical interpretation")

class ReadmissionRiskFactor(BaseModel):
    """Specific risk factor for readmission"""
    factor: str = Field(..., description="Risk factor name")
    impact: float = Field(..., ge=0.0, le=1.0, description="Impact on readmission risk")
    modifiable: bool = Field(..., description="Whether factor is modifiable")
    intervention_required: bool = Field(..., description="Whether intervention is needed")

class PreventiveIntervention(BaseModel):
    """Preventive intervention to reduce readmission risk"""
    intervention_id: str = Field(..., description="Intervention identifier")
    description: str = Field(..., description="Intervention description")
    evidence_level: EvidenceLevel = Field(..., description="Evidence level")
    cost_effectiveness: float = Field(..., ge=0.0, le=1.0, description="Cost-effectiveness score")
    time_to_implement: str = Field(..., description="Implementation timeframe")

class ReadmissionRiskResponse(BaseModel):
    """Response schema for readmission risk assessment"""
    patient_id: str = Field(..., description="Patient UUID")
    probability: float = Field(..., ge=0.0, le=1.0, description="Readmission probability")
    time_frame: str = Field(..., pattern=r'^(30_days|90_days|1_year)$', description="Risk timeframe")
    risk_factors: List[ReadmissionRiskFactor] = Field(..., description="Contributing risk factors")
    interventions: List[PreventiveIntervention] = Field(..., description="Recommended interventions")
    calculated_at: datetime = Field(..., description="Calculation timestamp")
    model: ModelMetadata = Field(..., description="Model metadata")

class RiskDistribution(BaseModel):
    """Population risk distribution"""
    low: int = Field(..., ge=0, description="Patients with low risk")
    moderate: int = Field(..., ge=0, description="Patients with moderate risk")
    high: int = Field(..., ge=0, description="Patients with high risk")
    critical: int = Field(..., ge=0, description="Patients with critical risk")

class OutcomeTrend(BaseModel):
    """Outcome trend data point"""
    metric: str = Field(..., description="Metric name")
    time_points: List[Dict[str, Union[str, float]]] = Field(..., description="Time series data")
    trend_direction: str = Field(..., pattern=r'^(improving|stable|declining)$')
    significance_level: float = Field(..., ge=0.0, le=1.0, description="Statistical significance")

class CostMetrics(BaseModel):
    """Population cost analytics"""
    total_cost: float = Field(..., ge=0.0, description="Total healthcare cost")
    cost_per_patient: float = Field(..., ge=0.0, description="Average cost per patient")
    estimated_savings: float = Field(..., ge=0.0, description="Estimated cost savings")
    roi: float = Field(..., description="Return on investment multiple")

class QualityMeasure(BaseModel):
    """Healthcare quality measure"""
    measure_id: str = Field(..., description="Quality measure identifier")
    name: str = Field(..., description="Measure name")
    description: str = Field(..., description="Measure description")
    current_score: float = Field(..., ge=0.0, le=100.0, description="Current performance score")
    benchmark: float = Field(..., ge=0.0, le=100.0, description="Benchmark score")
    improvement: float = Field(..., description="Improvement delta")
    measure_type: str = Field(..., pattern=r'^(process|outcome|structure)$')

class PopulationMetricsResponse(BaseModel):
    """Response schema for population health metrics"""
    cohort_id: str = Field(..., description="Cohort identifier")
    cohort_name: str = Field(..., description="Cohort name")
    total_patients: int = Field(..., ge=0, description="Total patients in cohort")
    risk_distribution: RiskDistribution = Field(..., description="Risk level distribution")
    outcome_trends: List[OutcomeTrend] = Field(..., description="Clinical outcome trends")
    cost_metrics: CostMetrics = Field(..., description="Cost analytics")
    quality_measures: List[QualityMeasure] = Field(..., description="Quality performance measures")
    generated_at: datetime = Field(..., description="Report generation timestamp")
    data_range: Dict[str, str] = Field(..., description="Data time range")

# ============================================
# ERROR RESPONSE SCHEMAS
# ============================================
# Note: Actual exception classes are defined in app/core/exceptions.py
# These schemas are for API error responses only

class RiskCalculationErrorResponse(BaseModel):
    """Error response schema for risk calculation failures"""
    error_code: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Human-readable error message")
    patient_id: Optional[str] = Field(None, description="Patient ID (if applicable)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    correlation_id: str = Field(..., description="Request correlation ID")

class SOC2ComplianceErrorResponse(BaseModel):
    """SOC2 compliance violation error response schema"""
    control_id: str = Field(..., description="SOC2 control identifier")
    violation_type: str = Field(..., description="Type of compliance violation")
    severity: str = Field(..., pattern=r'^(low|medium|high|critical)$')
    message: str = Field(..., description="Compliance violation description")
    remediation_required: bool = Field(..., description="Whether remediation is required")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Violation timestamp")