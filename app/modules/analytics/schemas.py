"""
Analytics Module Schemas
SOC2 Type 2 Compliant Population Health Analytics
Following SOLID principles and TDD approach
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime, date
import uuid

# ============================================
# ENUMS AND CONSTANTS
# ============================================

class TimeRange(str, Enum):
    """Time range options for analytics"""
    DAILY = "1d"
    WEEKLY = "7d"
    MONTHLY = "30d"
    QUARTERLY = "90d"
    YEARLY = "365d"

class TrendDirection(str, Enum):
    """Trend direction indicators"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"

class InterventionPriority(str, Enum):
    """Priority levels for intervention opportunities"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class QualityMeasureType(str, Enum):
    """Types of quality measures"""
    PROCESS = "process"
    OUTCOME = "outcome"
    STRUCTURE = "structure"

# ============================================
# REQUEST SCHEMAS
# ============================================

class PopulationMetricsRequest(BaseModel):
    """Request schema for population health metrics"""
    time_range: TimeRange = Field(default=TimeRange.QUARTERLY, description="Analysis time range")
    organization_filter: Optional[str] = Field(None, description="Organization filter")
    cohort_criteria: Optional[Dict[str, Any]] = Field(default={}, description="Patient cohort criteria")
    metrics_requested: List[str] = Field(
        default=["risk_distribution", "quality_measures", "cost_metrics", "intervention_opportunities"],
        description="Specific metrics to calculate"
    )
    
    # SOC2 CC6.1: Access control
    requesting_user_id: str = Field(..., description="User requesting analytics")
    access_purpose: str = Field(default="population_health_analysis", description="Purpose of analysis")

class RiskDistributionRequest(BaseModel):
    """Request schema for risk distribution analytics"""
    time_range: TimeRange = Field(default=TimeRange.QUARTERLY, description="Analysis time range")
    organization_filter: Optional[str] = Field(None, description="Organization filter")
    demographic_breakdown: bool = Field(default=False, description="Include demographic breakdown")
    
    # SOC2 CC6.1: Access control
    requesting_user_id: str = Field(..., description="User requesting risk distribution")

class QualityMeasuresRequest(BaseModel):
    """Request schema for quality measures analysis"""
    measure_ids: Optional[List[str]] = Field(None, description="Specific quality measures to analyze")
    time_range: TimeRange = Field(default=TimeRange.QUARTERLY, description="Analysis time range")
    include_benchmarks: bool = Field(default=True, description="Include benchmark comparisons")
    
    # SOC2 CC6.1: Access control
    requesting_user_id: str = Field(..., description="User requesting quality measures")

class CostAnalyticsRequest(BaseModel):
    """Request schema for cost analytics"""
    time_range: TimeRange = Field(default=TimeRange.QUARTERLY, description="Analysis time range")
    cost_categories: Optional[List[str]] = Field(None, description="Specific cost categories")
    include_roi_analysis: bool = Field(default=True, description="Include ROI analysis")
    
    # SOC2 CC6.1: Access control
    requesting_user_id: str = Field(..., description="User requesting cost analytics")

# ============================================
# CORE DATA MODELS
# ============================================

class RiskDistributionData(BaseModel):
    """Risk distribution breakdown"""
    low: int = Field(..., ge=0, description="Patients with low risk")
    moderate: int = Field(..., ge=0, description="Patients with moderate risk")
    high: int = Field(..., ge=0, description="Patients with high risk")
    critical: int = Field(..., ge=0, description="Patients with critical risk")
    total: int = Field(..., ge=0, description="Total patients analyzed")
    
    @field_validator('total')
    @classmethod
    def validate_total(cls, v, info):
        """Validate that total equals sum of risk levels"""
        values = info.data if info else {}
        expected_total = sum([
            values.get('low', 0),
            values.get('moderate', 0), 
            values.get('high', 0),
            values.get('critical', 0)
        ])
        if v != expected_total:
            raise ValueError(f'Total {v} does not match sum of risk levels {expected_total}')
        return v

class TimeSeriesPoint(BaseModel):
    """Individual data point in time series"""
    date: str = Field(..., description="Date in ISO format")
    value: float = Field(..., description="Metric value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level")

class TrendAnalysis(BaseModel):
    """Trend analysis for a metric"""
    metric_name: str = Field(..., description="Name of the metric")
    time_points: List[TimeSeriesPoint] = Field(..., description="Time series data")
    trend_direction: TrendDirection = Field(..., description="Overall trend direction")
    significance_level: float = Field(..., ge=0.0, le=1.0, description="Statistical significance")
    percent_change: float = Field(..., description="Percentage change over period")

class CostBreakdown(BaseModel):
    """Cost breakdown by category"""
    category: str = Field(..., description="Cost category name")
    current_cost: float = Field(..., ge=0.0, description="Current period cost")
    previous_cost: float = Field(..., ge=0.0, description="Previous period cost")
    percent_change: float = Field(..., description="Percentage change")
    patient_count: int = Field(..., ge=0, description="Number of patients in category")

class QualityMeasure(BaseModel):
    """Individual quality measure"""
    measure_id: str = Field(..., description="Quality measure identifier")
    name: str = Field(..., description="Human-readable measure name")
    description: str = Field(..., description="Measure description")
    current_score: float = Field(..., ge=0.0, le=100.0, description="Current performance score")
    benchmark: float = Field(..., ge=0.0, le=100.0, description="Benchmark target")
    improvement: float = Field(..., description="Improvement from previous period")
    measure_type: QualityMeasureType = Field(..., description="Type of quality measure")
    patient_count: int = Field(..., ge=0, description="Number of patients included")
    
    @property
    def performance_status(self) -> str:
        """Calculate performance status relative to benchmark"""
        if self.current_score >= self.benchmark:
            return "above_benchmark"
        elif self.current_score >= (self.benchmark * 0.9):
            return "near_benchmark"
        else:
            return "below_benchmark"

class InterventionOpportunity(BaseModel):
    """High-impact intervention opportunity"""
    opportunity_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique opportunity ID")
    priority: InterventionPriority = Field(..., description="Priority level")
    title: str = Field(..., min_length=10, description="Opportunity title")
    description: str = Field(..., min_length=20, description="Detailed description")
    estimated_impact: str = Field(..., description="Expected impact (e.g., cost savings)")
    affected_patient_count: int = Field(..., ge=0, description="Number of patients affected")
    implementation_effort: str = Field(..., description="Implementation complexity")
    estimated_timeline: str = Field(..., description="Implementation timeline")
    roi_estimate: float = Field(..., ge=0.0, description="Return on investment estimate")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Confidence in estimates")

# ============================================
# RESPONSE SCHEMAS
# ============================================

class PopulationMetricsResponse(BaseModel):
    """Comprehensive population health metrics response"""
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Analysis identifier")
    total_patients: int = Field(..., ge=0, description="Total patients in analysis")
    analysis_period: Dict[str, str] = Field(..., description="Analysis time period")
    
    # Core metrics
    risk_distribution: RiskDistributionData = Field(..., description="Risk level distribution")
    trends: List[TrendAnalysis] = Field(..., description="Key metric trends")
    cost_metrics: Dict[str, Any] = Field(..., description="Cost analytics")
    quality_measures: List[QualityMeasure] = Field(..., description="Quality performance measures")
    intervention_opportunities: List[InterventionOpportunity] = Field(..., description="High-impact opportunities")
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Report generation timestamp")
    generated_by: str = Field(..., description="User who generated the report")
    data_freshness: Dict[str, Any] = Field(default={}, description="Data freshness indicators")
    
    class Config:
        schema_extra = {
            "example": {
                "analysis_id": "analysis_123",
                "total_patients": 2847,
                "analysis_period": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-03-31"
                },
                "generated_by": "user123"
            }
        }

class RiskDistributionResponse(BaseModel):
    """Risk distribution analytics response"""
    distribution: RiskDistributionData = Field(..., description="Risk level distribution")
    demographic_breakdown: Optional[Dict[str, RiskDistributionData]] = Field(
        None, description="Breakdown by demographics"
    )
    trends: List[TrendAnalysis] = Field(..., description="Risk distribution trends")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")

class QualityMeasuresResponse(BaseModel):
    """Quality measures analytics response"""
    measures: List[QualityMeasure] = Field(..., description="Quality performance measures")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall quality score")
    benchmark_comparison: Dict[str, Any] = Field(..., description="Benchmark performance summary")
    improvement_trends: List[TrendAnalysis] = Field(..., description="Quality improvement trends")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")

class CostAnalyticsResponse(BaseModel):
    """Cost analytics response"""
    total_cost: float = Field(..., ge=0.0, description="Total healthcare cost")
    cost_per_patient: float = Field(..., ge=0.0, description="Average cost per patient")
    cost_breakdown: List[CostBreakdown] = Field(..., description="Cost breakdown by category")
    cost_trends: List[TrendAnalysis] = Field(..., description="Cost trend analysis")
    estimated_savings: float = Field(..., ge=0.0, description="Estimated cost savings")
    roi_metrics: Dict[str, float] = Field(..., description="Return on investment metrics")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")

class InterventionOpportunitiesResponse(BaseModel):
    """Intervention opportunities response"""
    opportunities: List[InterventionOpportunity] = Field(..., description="Prioritized opportunities")
    total_estimated_savings: float = Field(..., ge=0.0, description="Total estimated savings")
    high_priority_count: int = Field(..., ge=0, description="Number of high priority opportunities")
    affected_patient_total: int = Field(..., ge=0, description="Total patients affected by all opportunities")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")

# ============================================
# ERROR SCHEMAS
# ============================================

class AnalyticsErrorResponse(BaseModel):
    """Error response for analytics failures"""
    error_code: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Human-readable error message")
    analysis_id: Optional[str] = Field(None, description="Analysis ID (if applicable)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    correlation_id: str = Field(..., description="request correlation ID")

class DataQualityWarning(BaseModel):
    """Warning for data quality issues"""
    warning_type: str = Field(..., description="Type of data quality issue")
    affected_metrics: List[str] = Field(..., description="Metrics affected by the issue")
    severity: str = Field(..., pattern=r'^(low|medium|high)$', description="Warning severity")
    description: str = Field(..., description="Description of the issue")
    recommendations: List[str] = Field(..., description="Recommended actions")

# ============================================
# ANALYTICS CONFIGURATION
# ============================================

class AnalyticsConfig(BaseModel):
    """Configuration for analytics calculations"""
    enable_real_time_updates: bool = Field(default=False, description="Enable real-time metric updates")
    cache_duration_hours: int = Field(default=24, ge=1, le=168, description="Cache duration in hours")
    minimum_sample_size: int = Field(default=30, ge=10, description="Minimum sample size for analysis")
    confidence_threshold: float = Field(default=0.95, ge=0.8, le=0.99, description="Statistical confidence threshold")
    include_projections: bool = Field(default=True, description="Include future projections")
    projection_horizon_days: int = Field(default=90, ge=30, le=365, description="Projection horizon in days")