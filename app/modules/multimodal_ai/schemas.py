"""
Multimodal AI Schemas for Healthcare Platform V2.0

Pydantic schemas for multimodal data processing, fusion, and prediction
with healthcare-specific data structures and validation.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Tuple
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid

class ModalityType(str, Enum):
    """Types of medical data modalities."""
    CLINICAL_TEXT = "clinical_text"
    MEDICAL_IMAGE = "medical_image"
    AUDIO = "audio"
    LAB_DATA = "lab_data"
    GENOMIC_DATA = "genomic_data"
    VITAL_SIGNS = "vital_signs"
    WAVEFORM = "waveform"

class ImageModality(str, Enum):
    """Medical imaging modalities."""
    XRAY = "xray"
    CT = "ct"
    MRI = "mri"
    ULTRASOUND = "ultrasound"
    MAMMOGRAPHY = "mammography"
    DERMATOLOGY = "dermatology"
    ENDOSCOPY = "endoscopy"
    FUNDUS = "fundus"
    OCT = "oct"

class AudioType(str, Enum):
    """Types of medical audio data."""
    SPEECH = "speech"
    HEART_SOUNDS = "heart_sounds"
    LUNG_SOUNDS = "lung_sounds"
    BOWEL_SOUNDS = "bowel_sounds"
    DICTATION = "dictation"

class FusionMethod(str, Enum):
    """Methods for multimodal data fusion."""
    EARLY_FUSION = "early_fusion"
    LATE_FUSION = "late_fusion"
    ATTENTION_FUSION = "attention_fusion"
    CROSS_MODAL_ATTENTION = "cross_modal_attention"
    HIERARCHICAL_FUSION = "hierarchical_fusion"

class UncertaintyType(str, Enum):
    """Types of prediction uncertainty."""
    ALEATORIC = "aleatoric"  # Data uncertainty
    EPISTEMIC = "epistemic"  # Model uncertainty
    COMBINED = "combined"

class ClinicalTextEmbedding(BaseModel):
    """Clinical text embedding with medical context."""
    
    embedding_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text_content: str = Field(..., description="Original clinical text")
    embedding_vector: List[float] = Field(..., description="768-dimensional Clinical BERT embedding")
    medical_entities: List[str] = Field(default_factory=list, description="Extracted medical entities")
    clinical_concepts: List[str] = Field(default_factory=list, description="SNOMED/ICD concepts")
    sentiment_score: Optional[float] = Field(default=None, description="Clinical sentiment (-1 to 1)")
    urgency_score: float = Field(default=0.0, description="Clinical urgency (0 to 1)")
    confidence_score: float = Field(..., description="Embedding confidence (0 to 1)")
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('embedding_vector')
    def validate_embedding_dimension(cls, v):
        if len(v) != 768:
            raise ValueError('Clinical text embedding must be 768-dimensional')
        return v
    
    @validator('confidence_score', 'urgency_score')
    def validate_scores(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Scores must be between 0.0 and 1.0')
        return v

class ImageEmbedding(BaseModel):
    """Medical image embedding with anatomical context."""
    
    embedding_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    image_modality: ImageModality = Field(..., description="Type of medical imaging")
    embedding_vector: List[float] = Field(..., description="Image feature embedding")
    anatomical_region: str = Field(..., description="Body region imaged")
    view_position: Optional[str] = Field(default=None, description="Imaging view/position")
    detected_abnormalities: List[str] = Field(default_factory=list, description="Detected pathologies")
    radiological_features: Dict[str, float] = Field(default_factory=dict, description="Quantified features")
    image_quality_score: float = Field(..., description="Image quality assessment (0 to 1)")
    diagnostic_confidence: float = Field(..., description="Diagnostic confidence (0 to 1)")
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Imaging metadata
    pixel_spacing: Optional[Tuple[float, float]] = Field(default=None, description="Pixel spacing in mm")
    slice_thickness: Optional[float] = Field(default=None, description="Slice thickness in mm")
    contrast_used: Optional[bool] = Field(default=None, description="Whether contrast was used")
    
    @validator('image_quality_score', 'diagnostic_confidence')
    def validate_scores(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Scores must be between 0.0 and 1.0')
        return v

class AudioEmbedding(BaseModel):
    """Medical audio embedding with acoustic features."""
    
    embedding_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    audio_type: AudioType = Field(..., description="Type of medical audio")
    embedding_vector: List[float] = Field(..., description="Audio feature embedding")
    transcription: Optional[str] = Field(default=None, description="Speech transcription")
    acoustic_features: Dict[str, float] = Field(default_factory=dict, description="Extracted acoustic features")
    medical_terminology: List[str] = Field(default_factory=list, description="Detected medical terms")
    emotional_indicators: Dict[str, float] = Field(default_factory=dict, description="Emotional markers")
    speech_clarity_score: Optional[float] = Field(default=None, description="Speech clarity (0 to 1)")
    clinical_relevance_score: float = Field(..., description="Clinical relevance (0 to 1)")
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Audio metadata
    duration_seconds: float = Field(..., description="Audio duration in seconds")
    sample_rate: int = Field(..., description="Audio sample rate in Hz")
    channels: int = Field(default=1, description="Number of audio channels")
    
    @validator('speech_clarity_score', 'clinical_relevance_score')
    def validate_scores(cls, v):
        if v is not None and not 0.0 <= v <= 1.0:
            raise ValueError('Scores must be between 0.0 and 1.0')
        return v

class LabEmbedding(BaseModel):
    """Laboratory data embedding with reference ranges."""
    
    embedding_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    test_type: str = Field(..., description="Type of laboratory test")
    embedding_vector: List[float] = Field(..., description="Lab data feature embedding")
    test_results: Dict[str, float] = Field(..., description="Numerical test results")
    reference_ranges: Dict[str, Tuple[float, float]] = Field(..., description="Normal reference ranges")
    abnormal_flags: List[str] = Field(default_factory=list, description="Abnormal result indicators")
    critical_values: List[str] = Field(default_factory=list, description="Critical value alerts")
    trend_analysis: Dict[str, str] = Field(default_factory=dict, description="Trend compared to previous")
    clinical_significance: float = Field(..., description="Clinical significance score (0 to 1)")
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Lab metadata
    collection_timestamp: Optional[datetime] = Field(default=None, description="Sample collection time")
    lab_name: Optional[str] = Field(default=None, description="Laboratory name")
    test_method: Optional[str] = Field(default=None, description="Testing methodology")
    
    @validator('clinical_significance')
    def validate_significance(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Clinical significance must be between 0.0 and 1.0')
        return v

class OmicsEmbedding(BaseModel):
    """Genomic/omics data embedding with variant analysis."""
    
    embedding_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    omics_type: str = Field(..., description="Type of omics data (genomics, proteomics, etc.)")
    embedding_vector: List[float] = Field(..., description="Omics feature embedding")
    variant_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Genetic variants")
    pathogenic_variants: List[str] = Field(default_factory=list, description="Disease-associated variants")
    pharmacogenomic_markers: List[str] = Field(default_factory=list, description="Drug response markers")
    ancestry_inference: Dict[str, float] = Field(default_factory=dict, description="Genetic ancestry")
    polygenic_risk_scores: Dict[str, float] = Field(default_factory=dict, description="Disease risk scores")
    clinical_actionability: float = Field(..., description="Clinical actionability score (0 to 1)")
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Omics metadata
    sequencing_platform: Optional[str] = Field(default=None, description="Sequencing technology")
    coverage_depth: Optional[float] = Field(default=None, description="Average sequencing depth")
    quality_score: Optional[float] = Field(default=None, description="Overall data quality")
    
    @validator('clinical_actionability')
    def validate_actionability(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Clinical actionability must be between 0.0 and 1.0')
        return v

class AttentionWeights(BaseModel):
    """Attention weights for multimodal fusion."""
    
    modality_weights: Dict[ModalityType, float] = Field(..., description="Weight for each modality")
    cross_modal_attention: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Cross-modal attention")
    temporal_weights: Optional[List[float]] = Field(default=None, description="Temporal attention weights")
    spatial_weights: Optional[List[List[float]]] = Field(default=None, description="Spatial attention for images")
    feature_importance: Dict[str, float] = Field(default_factory=dict, description="Individual feature importance")
    
    @validator('modality_weights')
    def validate_modality_weights(cls, v):
        total_weight = sum(v.values())
        if not 0.9 <= total_weight <= 1.1:  # Allow small numerical errors
            raise ValueError('Modality weights should sum to approximately 1.0')
        return v

class FusedEmbedding(BaseModel):
    """Fused multimodal embedding with comprehensive metadata."""
    
    fusion_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    component_embeddings: List[Union[ClinicalTextEmbedding, ImageEmbedding, AudioEmbedding, LabEmbedding, OmicsEmbedding]] = Field(..., description="Source embeddings")
    fused_vector: List[float] = Field(..., description="Final fused embedding vector")
    fusion_method: FusionMethod = Field(..., description="Method used for fusion")
    attention_weights: AttentionWeights = Field(..., description="Attention weights applied")
    modality_contributions: Dict[ModalityType, float] = Field(..., description="Contribution of each modality")
    fusion_confidence: float = Field(..., description="Confidence in fusion quality (0 to 1)")
    complementarity_score: float = Field(..., description="How well modalities complement each other (0 to 1)")
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('fusion_confidence', 'complementarity_score')
    def validate_scores(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Scores must be between 0.0 and 1.0')
        return v

class UncertaintyMetrics(BaseModel):
    """Uncertainty quantification for predictions."""
    
    aleatoric_uncertainty: float = Field(..., description="Data/noise uncertainty")
    epistemic_uncertainty: float = Field(..., description="Model/knowledge uncertainty")
    total_uncertainty: float = Field(..., description="Combined uncertainty")
    confidence_interval: Tuple[float, float] = Field(..., description="95% confidence interval")
    prediction_entropy: float = Field(..., description="Shannon entropy of prediction")
    out_of_distribution_score: float = Field(..., description="OOD detection score (0 to 1)")
    
    @validator('aleatoric_uncertainty', 'epistemic_uncertainty', 'total_uncertainty', 'prediction_entropy', 'out_of_distribution_score')
    def validate_uncertainty_values(cls, v):
        if v < 0.0:
            raise ValueError('Uncertainty values must be non-negative')
        return v

class MultimodalPrediction(BaseModel):
    """Comprehensive multimodal prediction with explanations."""
    
    prediction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    fused_embedding: FusedEmbedding = Field(..., description="Source fused embedding")
    
    # Primary predictions
    diagnosis_predictions: Dict[str, float] = Field(..., description="Disease probability scores")
    risk_stratification: Dict[str, float] = Field(..., description="Risk category probabilities")
    treatment_recommendations: List[str] = Field(default_factory=list, description="Suggested treatments")
    urgency_score: float = Field(..., description="Clinical urgency (0 to 1)")
    
    # Uncertainty and confidence
    uncertainty_metrics: UncertaintyMetrics = Field(..., description="Prediction uncertainty")
    prediction_confidence: float = Field(..., description="Overall prediction confidence (0 to 1)")
    
    # Clinical context
    differential_diagnosis: List[str] = Field(default_factory=list, description="Differential diagnosis list")
    clinical_reasoning: str = Field(..., description="AI reasoning explanation")
    supporting_evidence: Dict[str, List[str]] = Field(default_factory=dict, description="Evidence for each prediction")
    
    # Quality metrics
    prediction_quality_score: float = Field(..., description="Overall prediction quality (0 to 1)")
    clinical_relevance_score: float = Field(..., description="Clinical relevance (0 to 1)")
    
    # Metadata
    model_version: str = Field(..., description="Model version used")
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)
    requires_human_review: bool = Field(default=False, description="Whether human review is needed")
    
    @validator('urgency_score', 'prediction_confidence', 'prediction_quality_score', 'clinical_relevance_score')
    def validate_scores(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Scores must be between 0.0 and 1.0')
        return v

class MultimodalQuery(BaseModel):
    """Query structure for multimodal similarity search."""
    
    query_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text_query: Optional[str] = Field(default=None, description="Clinical text query")
    image_query: Optional[bytes] = Field(default=None, description="Medical image query")
    audio_query: Optional[bytes] = Field(default=None, description="Audio query")
    lab_query: Optional[Dict[str, float]] = Field(default=None, description="Lab values query")
    
    # Search parameters
    similarity_threshold: float = Field(default=0.7, description="Minimum similarity score")
    max_results: int = Field(default=100, description="Maximum number of results")
    modality_weights: Optional[Dict[ModalityType, float]] = Field(default=None, description="Custom modality weights")
    
    # Filters
    time_range: Optional[Tuple[datetime, datetime]] = Field(default=None, description="Time range filter")
    demographic_filters: Optional[Dict[str, Any]] = Field(default=None, description="Patient demographic filters")
    clinical_filters: Optional[Dict[str, Any]] = Field(default=None, description="Clinical condition filters")
    
    @validator('similarity_threshold')
    def validate_threshold(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Similarity threshold must be between 0.0 and 1.0')
        return v

class ProcessingRequest(BaseModel):
    """Request for multimodal data processing."""
    
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str = Field(..., description="Anonymized patient identifier")
    
    # Input data
    clinical_text: Optional[str] = Field(default=None, description="Clinical notes or text")
    medical_images: Optional[List[bytes]] = Field(default=None, description="Medical images")
    audio_data: Optional[bytes] = Field(default=None, description="Medical audio")
    lab_data: Optional[Dict[str, float]] = Field(default=None, description="Laboratory results")
    genomic_data: Optional[Dict[str, Any]] = Field(default=None, description="Genomic/omics data")
    
    # Processing options
    fusion_method: FusionMethod = Field(default=FusionMethod.ATTENTION_FUSION, description="Fusion method to use")
    enable_uncertainty: bool = Field(default=True, description="Calculate uncertainty metrics")
    generate_explanations: bool = Field(default=True, description="Generate explanations")
    
    # Clinical context
    specialty: Optional[str] = Field(default=None, description="Medical specialty context")
    urgency_level: Optional[str] = Field(default=None, description="Clinical urgency level")
    
    @validator('medical_images')
    def validate_images(cls, v):
        if v is not None and len(v) > 20:  # Reasonable limit
            raise ValueError('Maximum 20 images per request')
        return v

class FusionConfig(BaseModel):
    """Configuration for multimodal fusion engine."""
    
    # Model configurations
    clinical_bert_model: str = Field(default="emilyalsentzer/Bio_ClinicalBERT", description="Clinical BERT model")
    vision_model: str = Field(default="microsoft/swin-base-patch4-window7-224", description="Vision transformer model")
    audio_model: str = Field(default="openai/whisper-base", description="Audio processing model")
    
    # Fusion parameters
    default_fusion_method: FusionMethod = Field(default=FusionMethod.ATTENTION_FUSION)
    attention_heads: int = Field(default=8, description="Number of attention heads")
    hidden_dim: int = Field(default=768, description="Hidden dimension size")
    dropout_rate: float = Field(default=0.1, description="Dropout rate")
    
    # Processing settings
    max_text_length: int = Field(default=512, description="Maximum text tokens")
    image_size: Tuple[int, int] = Field(default=(224, 224), description="Image input size")
    audio_duration: float = Field(default=30.0, description="Maximum audio duration in seconds")
    
    # Quality thresholds
    min_confidence_threshold: float = Field(default=0.6, description="Minimum confidence for predictions")
    uncertainty_threshold: float = Field(default=0.3, description="Threshold for high uncertainty")
    
    # Device settings
    device: str = Field(default="cpu", description="Processing device (cpu/cuda/mps)")
    batch_size: int = Field(default=16, description="Processing batch size")
    num_workers: int = Field(default=4, description="Number of data loading workers")
    
    @validator('dropout_rate')
    def validate_dropout(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Dropout rate must be between 0.0 and 1.0')
        return v