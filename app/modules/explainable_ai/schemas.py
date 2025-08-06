"""
Explainable AI Schemas for Healthcare Platform V2.0

Pydantic schemas for explainable AI components including SHAP explanations,
attention visualizations, uncertainty quantification, and clinical reasoning.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Tuple
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid

class ExplanationMethod(str, Enum):
    """Available explanation methods."""
    SHAP = "shap"
    LIME = "lime"
    INTEGRATED_GRADIENTS = "integrated_gradients"
    GRAD_CAM = "grad_cam"
    ATTENTION_MAPS = "attention_maps"
    COUNTERFACTUALS = "counterfactuals"
    RULE_BASED = "rule_based"

class ExplanationType(str, Enum):
    """Types of explanations."""
    GLOBAL = "global"
    LOCAL = "local"
    INSTANCE = "instance"
    COHORT = "cohort"

class UncertaintyType(str, Enum):
    """Types of uncertainty."""
    ALEATORIC = "aleatoric"  # Data uncertainty
    EPISTEMIC = "epistemic"  # Model uncertainty
    COMBINED = "combined"

class VisualizationType(str, Enum):
    """Types of visualizations."""
    HEATMAP = "heatmap"
    BAR_CHART = "bar_chart"
    SCATTER_PLOT = "scatter_plot"
    LINE_PLOT = "line_plot"
    ATTENTION_MAP = "attention_map"
    SALIENCY_MAP = "saliency_map"

class XAIConfig(BaseModel):
    """Configuration for explainable AI engine."""
    
    # Core XAI settings
    enable_shap_explanations: bool = Field(default=True)
    enable_attention_visualization: bool = Field(default=True)
    enable_uncertainty_quantification: bool = Field(default=True)
    enable_counterfactuals: bool = Field(default=True)
    
    # Explanation settings
    max_features_to_explain: int = Field(default=20, description="Maximum features to explain")
    explanation_sample_size: int = Field(default=1000, description="Sample size for explanations")
    confidence_threshold: float = Field(default=0.7, description="Confidence threshold")
    uncertainty_threshold: float = Field(default=0.3, description="Uncertainty threshold")
    
    # Visualization settings
    generate_visualizations: bool = Field(default=True)
    save_explanation_plots: bool = Field(default=True)
    interactive_explanations: bool = Field(default=True)
    
    # Clinical settings
    use_medical_terminology: bool = Field(default=True)
    specialty_specific_explanations: bool = Field(default=True)
    patient_friendly_mode: bool = Field(default=False)
    
    # Performance settings
    explanation_timeout_seconds: int = Field(default=300)
    cache_explanations: bool = Field(default=True)
    batch_explanations: bool = Field(default=True)
    
    @validator('confidence_threshold', 'uncertainty_threshold')
    def validate_thresholds(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Thresholds must be between 0.0 and 1.0')
        return v

class SHAPExplanation(BaseModel):
    """SHAP explanation for model predictions."""
    
    explanation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    shap_values: List[List[float]] = Field(..., description="SHAP values for features")
    feature_importance: Dict[str, float] = Field(..., description="Feature importance scores")
    feature_names: List[str] = Field(..., description="Names of features")
    base_value: float = Field(..., description="Model base/expected value")
    
    # Clinical interpretation
    clinical_interpretation: str = Field(..., description="Clinical interpretation of SHAP values")
    medical_relevance: Dict[str, str] = Field(default_factory=dict, description="Medical relevance of features")
    
    # Visualizations
    visualizations: Dict[str, Any] = Field(default_factory=dict, description="Generated visualizations")
    
    # Metadata
    explanation_method: str = Field(default="TreeSHAP", description="SHAP method used")
    confidence_score: float = Field(..., description="Confidence in explanation")
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence score must be between 0.0 and 1.0')
        return v

class AttentionMaps(BaseModel):
    """Attention maps for transformer models."""
    
    attention_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    attention_weights: List[List[float]] = Field(..., description="Attention weight matrices")
    input_tokens: List[str] = Field(..., description="Input tokens/features")
    
    # Attention analysis
    attention_statistics: Dict[str, float] = Field(..., description="Attention statistics")
    medical_entity_attention: Dict[str, float] = Field(default_factory=dict, description="Medical entity attention")
    
    # Layer and head analysis
    layer_wise_attention: Dict[str, List[float]] = Field(default_factory=dict, description="Layer-wise attention")
    head_wise_attention: Dict[str, List[float]] = Field(default_factory=dict, description="Head-wise attention")
    
    # Visualizations
    visualizations: Dict[str, Any] = Field(default_factory=dict, description="Attention visualizations")
    
    # Clinical interpretation
    clinical_interpretation: str = Field(..., description="Clinical interpretation of attention patterns")
    focused_medical_concepts: List[str] = Field(default_factory=list, description="Medical concepts with high attention")
    
    # Metadata
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow)

class MultimodalExplanation(BaseModel):
    """Explanation for multimodal AI decisions."""
    
    explanation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Modality contributions
    modality_contributions: Dict[str, float] = Field(..., description="Contribution of each modality")
    modality_explanations: Dict[str, Dict[str, Any]] = Field(..., description="Modality-specific explanations")
    
    # Cross-modal analysis
    cross_modal_interactions: Dict[str, Any] = Field(..., description="Cross-modal interaction analysis")
    fusion_explanation: Dict[str, Any] = Field(..., description="Fusion mechanism explanation")
    
    # Attention analysis
    attention_analysis: Dict[str, Any] = Field(default_factory=dict, description="Multi-modal attention analysis")
    
    # Uncertainty analysis
    uncertainty_analysis: Dict[str, Any] = Field(default_factory=dict, description="Uncertainty across modalities")
    
    # Clinical summary
    clinical_summary: str = Field(..., description="Clinical summary of multimodal decision")
    explanation_confidence: float = Field(..., description="Overall explanation confidence")
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list, description="Clinical recommendations")
    
    # Metadata
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('explanation_confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Explanation confidence must be between 0.0 and 1.0')
        return v

class CounterfactualExamples(BaseModel):
    """Counterfactual examples for clinical decisions."""
    
    counterfactual_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_prediction: Dict[str, Any] = Field(..., description="Original model prediction")
    
    # Counterfactual scenarios
    counterfactual_scenarios: List[Dict[str, Any]] = Field(..., description="Generated counterfactual scenarios")
    modifiable_features: List[str] = Field(..., description="Features that can be modified")
    
    # Analysis
    feasibility_analysis: Dict[str, Any] = Field(..., description="Feasibility of counterfactual changes")
    clinical_impact: Dict[str, Any] = Field(..., description="Clinical impact assessment")
    
    # Recommendations
    actionable_recommendations: List[str] = Field(..., description="Actionable clinical recommendations")
    
    # Validation
    explanation_confidence: float = Field(..., description="Confidence in counterfactual explanations")
    clinical_validity: Dict[str, bool] = Field(..., description="Clinical validity assessment")
    
    # Metadata
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('explanation_confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Explanation confidence must be between 0.0 and 1.0')
        return v

class RuleExplanation(BaseModel):
    """Rule-based explanation for clinical decisions."""
    
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Rule information
    applicable_rules: Dict[str, Any] = Field(..., description="Applicable clinical rules")
    rule_evaluations: Dict[str, Any] = Field(..., description="Rule evaluation results")
    rule_reasoning: str = Field(..., description="Rule-based reasoning")
    
    # Rule conflicts and consistency
    rule_conflicts: List[str] = Field(default_factory=list, description="Detected rule conflicts")
    evidence_level: str = Field(..., description="Overall evidence level")
    
    # References
    guideline_references: List[str] = Field(default_factory=list, description="Clinical guideline references")
    
    # Confidence and validation
    clinical_confidence: float = Field(..., description="Confidence in rule-based decision")
    validation_status: Dict[str, bool] = Field(..., description="Rule validation status")
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list, description="Rule-based recommendations")
    
    # Metadata
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('clinical_confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Clinical confidence must be between 0.0 and 1.0')
        return v

class FeatureImportance(BaseModel):
    """Feature importance analysis."""
    
    importance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Importance scores
    feature_scores: Dict[str, float] = Field(..., description="Feature importance scores")
    feature_ranking: List[Tuple[str, float]] = Field(..., description="Features ranked by importance")
    
    # Different importance methods
    importance_methods: Dict[str, Dict[str, float]] = Field(..., description="Different importance calculation methods")
    
    # Clinical analysis
    feature_insights: Dict[str, str] = Field(..., description="Clinical insights for each feature")
    clinical_relevance: Dict[str, float] = Field(..., description="Clinical relevance scores")
    
    # Statistical significance
    statistical_significance: Dict[str, float] = Field(..., description="Statistical significance of features")
    importance_stability: float = Field(..., description="Stability of importance scores")
    
    # Visualizations
    visualization_data: Dict[str, Any] = Field(default_factory=dict, description="Visualization data")
    
    # Metadata
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('importance_stability')
    def validate_stability(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Importance stability must be between 0.0 and 1.0')
        return v

class UncertaintyExplanation(BaseModel):
    """Explanation of prediction uncertainty."""
    
    uncertainty_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Uncertainty sources
    uncertainty_sources: Dict[str, float] = Field(..., description="Sources of uncertainty")
    aleatoric_analysis: Dict[str, Any] = Field(..., description="Data uncertainty analysis")
    epistemic_analysis: Dict[str, Any] = Field(..., description="Model uncertainty analysis")
    
    # Uncertainty explanations
    uncertainty_explanations: Dict[str, str] = Field(..., description="Explanations for uncertainty sources")
    
    # Impact analysis
    decision_impact: Dict[str, Any] = Field(..., description="Impact of uncertainty on decisions")
    clinical_implications: Dict[str, Any] = Field(..., description="Clinical implications of uncertainty")
    
    # Mitigation
    mitigation_recommendations: List[str] = Field(..., description="Uncertainty mitigation recommendations")
    
    # Confidence intervals
    confidence_intervals: Dict[str, Tuple[float, float]] = Field(..., description="Confidence intervals for predictions")
    
    # Visualizations
    uncertainty_visualization: Dict[str, Any] = Field(default_factory=dict, description="Uncertainty visualizations")
    
    # Metadata
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow)

class TemporalExplanation(BaseModel):
    """Temporal explanation for time-series data."""
    
    temporal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Temporal analysis
    time_series_importance: Dict[str, List[float]] = Field(..., description="Importance over time")
    temporal_patterns: Dict[str, Any] = Field(..., description="Identified temporal patterns")
    
    # Change point detection
    change_points: List[datetime] = Field(default_factory=list, description="Detected change points")
    trend_analysis: Dict[str, Any] = Field(..., description="Trend analysis")
    
    # Seasonality
    seasonal_patterns: Dict[str, Any] = Field(default_factory=dict, description="Seasonal patterns")
    
    # Clinical interpretation
    temporal_clinical_insights: str = Field(..., description="Clinical insights from temporal analysis")
    
    # Metadata
    analysis_window: Tuple[datetime, datetime] = Field(..., description="Analysis time window")
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow)

class ImageExplanation(BaseModel):
    """Explanation for medical image-based decisions."""
    
    image_explanation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Saliency maps
    saliency_maps: Dict[str, List[List[float]]] = Field(..., description="Saliency maps for image regions")
    attention_regions: List[Dict[str, Any]] = Field(..., description="Regions with high attention")
    
    # Anatomical analysis
    anatomical_focus: Dict[str, float] = Field(..., description="Focus on anatomical structures")
    pathological_indicators: List[str] = Field(default_factory=list, description="Pathological indicators")
    
    # Radiological interpretation
    radiological_findings: Dict[str, Any] = Field(..., description="Radiological findings explanation")
    diagnostic_confidence: float = Field(..., description="Diagnostic confidence")
    
    # Comparative analysis
    similar_cases: List[str] = Field(default_factory=list, description="Similar case references")
    differential_diagnosis: List[str] = Field(default_factory=list, description="Differential diagnosis considerations")
    
    # Visualizations
    overlay_visualizations: Dict[str, bytes] = Field(default_factory=dict, description="Overlay visualizations")
    
    # Metadata
    image_modality: str = Field(..., description="Medical imaging modality")
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('diagnostic_confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Diagnostic confidence must be between 0.0 and 1.0')
        return v

class ValidationMetrics(BaseModel):
    """Validation metrics for explanations."""
    
    validation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Explanation quality metrics
    faithfulness_score: float = Field(..., description="How faithful the explanation is to the model")
    stability_score: float = Field(..., description="Stability of explanations across similar inputs")
    comprehensiveness_score: float = Field(..., description="How comprehensive the explanation is")
    
    # Clinical validation
    clinical_accuracy: float = Field(..., description="Clinical accuracy of explanations")
    expert_agreement: float = Field(..., description="Agreement with clinical experts")
    
    # User validation
    user_satisfaction: Optional[float] = Field(default=None, description="User satisfaction score")
    usability_score: Optional[float] = Field(default=None, description="Explanation usability")
    
    # Consistency metrics
    consistency_across_methods: float = Field(..., description="Consistency across different explanation methods")
    temporal_consistency: Optional[float] = Field(default=None, description="Consistency over time")
    
    # Validation details
    validation_method: str = Field(..., description="Method used for validation")
    validation_dataset_size: int = Field(..., description="Size of validation dataset")
    expert_evaluators: int = Field(default=0, description="Number of expert evaluators")
    
    # Metadata
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('faithfulness_score', 'stability_score', 'comprehensiveness_score', 'clinical_accuracy', 'expert_agreement')
    def validate_scores(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Validation scores must be between 0.0 and 1.0')
        return v

class ExplanationRequest(BaseModel):
    """Request for generating explanations."""
    
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Request details
    explanation_methods: List[ExplanationMethod] = Field(..., description="Requested explanation methods")
    explanation_type: ExplanationType = Field(..., description="Type of explanation needed")
    
    # Input data
    model_prediction: Dict[str, Any] = Field(..., description="Model prediction to explain")
    input_data: Dict[str, Any] = Field(..., description="Input data used for prediction")
    model_metadata: Dict[str, Any] = Field(default_factory=dict, description="Model metadata")
    
    # Configuration
    max_features: int = Field(default=10, description="Maximum features to include in explanation")
    include_visualizations: bool = Field(default=True, description="Whether to include visualizations")
    clinical_context: Optional[str] = Field(default=None, description="Clinical context for explanation")
    
    # Target audience
    target_audience: str = Field(default="clinician", description="Target audience (clinician, patient, researcher)")
    explanation_depth: str = Field(default="standard", description="Depth of explanation (basic, standard, detailed)")
    
    # Metadata
    request_timestamp: datetime = Field(default_factory=datetime.utcnow)
    requester_id: str = Field(..., description="ID of the explanation requester")

class ExplanationResponse(BaseModel):
    """Response containing generated explanations."""
    
    response_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = Field(..., description="Original request ID")
    
    # Generated explanations
    shap_explanation: Optional[SHAPExplanation] = Field(default=None)
    attention_maps: Optional[AttentionMaps] = Field(default=None)
    multimodal_explanation: Optional[MultimodalExplanation] = Field(default=None)
    counterfactual_examples: Optional[CounterfactualExamples] = Field(default=None)
    rule_explanation: Optional[RuleExplanation] = Field(default=None)
    feature_importance: Optional[FeatureImportance] = Field(default=None)
    uncertainty_explanation: Optional[UncertaintyExplanation] = Field(default=None)
    
    # Response metadata
    generation_time_seconds: float = Field(..., description="Time taken to generate explanations")
    explanation_confidence: float = Field(..., description="Overall confidence in explanations")
    
    # Validation
    validation_metrics: Optional[ValidationMetrics] = Field(default=None)
    
    # Clinical summary
    clinical_summary: str = Field(..., description="Clinical summary of all explanations")
    key_insights: List[str] = Field(default_factory=list, description="Key insights from explanations")
    
    # Metadata
    response_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('explanation_confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Explanation confidence must be between 0.0 and 1.0')
        return v