"""
Edge AI Schemas for Healthcare Platform V2.0

Pydantic schemas for Gemma 3n on-device AI processing, medical knowledge integration,
and edge computing optimization for healthcare applications.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid

class DeviceType(str, Enum):
    """Types of edge devices."""
    TABLET = "tablet"
    SMARTPHONE = "smartphone" 
    EMBEDDED = "embedded"
    WORKSTATION = "workstation"
    EDGE_SERVER = "edge_server"

class ProcessingMode(str, Enum):
    """Processing modes for edge AI."""
    OFFLINE = "offline"
    ONLINE = "online"
    HYBRID = "hybrid"
    EMERGENCY = "emergency"

class MedicalSpecialty(str, Enum):
    """Medical specialties for context-aware processing."""
    EMERGENCY_MEDICINE = "emergency_medicine"
    INTERNAL_MEDICINE = "internal_medicine"
    CARDIOLOGY = "cardiology"
    PULMONOLOGY = "pulmonology"
    ENDOCRINOLOGY = "endocrinology"
    NEUROLOGY = "neurology"
    PSYCHIATRY = "psychiatry"
    DERMATOLOGY = "dermatology"
    RADIOLOGY = "radiology"
    PATHOLOGY = "pathology"

class UrgencyLevel(str, Enum):
    """Clinical urgency levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class ValidationStatus(str, Enum):
    """Medical validation status."""
    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"
    REQUIRES_REVIEW = "requires_review"

class GemmaConfig(BaseModel):
    """Configuration for Gemma 3n on-device engine."""
    
    model_path: str = Field(..., description="Path to Gemma model files")
    model_version: str = Field(default="gemma-3n-medical", description="Model version identifier")
    device: str = Field(default="cpu", description="Target device (cpu, cuda, mps)")
    device_type: DeviceType = Field(default=DeviceType.TABLET, description="Type of edge device")
    
    # Model parameters
    max_context_length: int = Field(default=2048, description="Maximum context length")
    max_response_tokens: int = Field(default=512, description="Maximum response tokens")
    temperature: float = Field(default=0.1, description="Generation temperature")
    top_p: float = Field(default=0.9, description="Top-p sampling parameter")
    
    # Memory management
    max_memory_gb: float = Field(default=4.0, description="Maximum memory usage in GB")
    cache_size_mb: float = Field(default=100.0, description="Cache size in MB")
    quantization_enabled: bool = Field(default=True, description="Enable model quantization")
    
    # Medical domain settings
    medical_vocabulary_path: Optional[str] = Field(default=None, description="Path to medical vocabulary")
    clinical_protocols_path: Optional[str] = Field(default=None, description="Path to clinical protocols")
    emergency_mode_enabled: bool = Field(default=True, description="Enable emergency processing mode")
    
    # Performance settings
    batch_size: int = Field(default=1, description="Processing batch size")
    num_threads: int = Field(default=4, description="Number of processing threads")
    enable_optimization: bool = Field(default=True, description="Enable inference optimizations")
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError('Temperature must be between 0.0 and 2.0')
        return v
    
    @validator('top_p')
    def validate_top_p(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Top-p must be between 0.0 and 1.0')
        return v

class MedicalClaim(BaseModel):
    """Individual medical claim for validation."""
    
    claim_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    claim_text: str = Field(..., description="Medical claim statement")
    claim_type: str = Field(..., description="Type of medical claim")
    confidence_score: float = Field(..., description="Confidence in claim (0 to 1)")
    source_context: str = Field(..., description="Original context of claim")
    medical_specialty: Optional[MedicalSpecialty] = Field(default=None, description="Relevant medical specialty")
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence score must be between 0.0 and 1.0')
        return v

class ClaimValidation(BaseModel):
    """Validation result for individual medical claim."""
    
    claim_id: str = Field(..., description="Reference to original claim")
    validation_status: ValidationStatus = Field(..., description="Validation result")
    accuracy_score: float = Field(..., description="Accuracy assessment (0 to 1)")
    evidence_strength: str = Field(..., description="Strength of supporting evidence")
    contradictions: List[str] = Field(default_factory=list, description="Identified contradictions")
    supporting_references: List[str] = Field(default_factory=list, description="Supporting medical references")
    confidence_interval: tuple[float, float] = Field(..., description="Confidence interval for accuracy")
    
    @validator('accuracy_score')
    def validate_accuracy(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Accuracy score must be between 0.0 and 1.0')
        return v

class ReasoningStep(BaseModel):
    """Individual step in clinical reasoning chain."""
    
    step_number: int = Field(..., description="Sequential step number")
    step_type: str = Field(..., description="Type of reasoning step")
    description: str = Field(..., description="Step description")
    clinical_evidence: List[str] = Field(default_factory=list, description="Supporting clinical evidence")
    confidence_level: float = Field(..., description="Confidence in reasoning step")
    medical_concepts: List[str] = Field(default_factory=list, description="Relevant medical concepts")
    decision_point: bool = Field(default=False, description="Whether this is a key decision point")
    
    @validator('confidence_level')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence level must be between 0.0 and 1.0')
        return v

class ReasoningChain(BaseModel):
    """Complete clinical reasoning chain."""
    
    reasoning_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reasoning_steps: List[ReasoningStep] = Field(..., description="Sequential reasoning steps")
    confidence_score: float = Field(..., description="Overall reasoning confidence")
    decision_points: List[int] = Field(default_factory=list, description="Key decision step numbers")
    medical_evidence: Dict[str, List[str]] = Field(default_factory=dict, description="Supporting evidence by category")
    uncertainty_areas: List[str] = Field(default_factory=list, description="Areas of high uncertainty")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next clinical steps")
    reasoning_quality: str = Field(..., description="Quality assessment of reasoning")
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence score must be between 0.0 and 1.0')
        return v

class MedicalEntityList(BaseModel):
    """Extracted medical entities from clinical text."""
    
    extraction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symptoms: List[str] = Field(default_factory=list, description="Identified symptoms")
    diagnoses: List[str] = Field(default_factory=list, description="Identified diagnoses")
    medications: List[str] = Field(default_factory=list, description="Identified medications")
    anatomy: List[str] = Field(default_factory=list, description="Anatomical references")
    laboratory_values: List[str] = Field(default_factory=list, description="Lab values and results")
    procedures: List[str] = Field(default_factory=list, description="Medical procedures")
    
    # Entity metadata
    snomed_mappings: Dict[str, str] = Field(default_factory=dict, description="SNOMED CT concept mappings")
    icd_mappings: Dict[str, str] = Field(default_factory=dict, description="ICD-10/11 code mappings")
    confidence_score: float = Field(..., description="Extraction confidence")
    extraction_method: str = Field(..., description="Method used for extraction")
    
    # Processing metadata
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_text_length: int = Field(..., description="Length of source text")
    entities_per_100_chars: float = Field(..., description="Entity density metric")
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence score must be between 0.0 and 1.0')
        return v

class ValidationResult(BaseModel):
    """Comprehensive medical validation result."""
    
    validation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    overall_accuracy: float = Field(..., description="Overall accuracy score (0 to 1)")
    validated_claims: List[ClaimValidation] = Field(..., description="Individual claim validations")
    contradictions: List[str] = Field(default_factory=list, description="Identified contradictions")
    uncertainty_areas: List[str] = Field(default_factory=list, description="High uncertainty areas")
    recommendations: List[str] = Field(default_factory=list, description="Validation recommendations")
    
    # Validation metadata
    knowledge_base_version: str = Field(..., description="Knowledge base version used")
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    validation_method: str = Field(default="knowledge_base", description="Validation methodology")
    human_review_required: bool = Field(default=False, description="Whether human review is needed")
    
    # Quality metrics
    evidence_quality: str = Field(default="moderate", description="Quality of supporting evidence")
    consensus_level: str = Field(default="partial", description="Level of medical consensus")
    
    @validator('overall_accuracy')
    def validate_accuracy(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Overall accuracy must be between 0.0 and 1.0')
        return v

class GemmaOutput(BaseModel):
    """Comprehensive output from Gemma 3n processing."""
    
    output_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    raw_response: str = Field(..., description="Raw model response")
    structured_output: Dict[str, Any] = Field(..., description="Structured interpretation of response")
    
    # Confidence and uncertainty
    confidence_score: float = Field(..., description="Overall confidence in output")
    uncertainty_metrics: Dict[str, float] = Field(..., description="Uncertainty quantification")
    
    # Validation results
    validation_result: ValidationResult = Field(..., description="Medical validation results")
    
    # Performance metrics
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")
    model_version: str = Field(..., description="Model version used")
    context_tokens: int = Field(..., description="Number of context tokens")
    response_tokens: int = Field(..., description="Number of response tokens")
    
    # Medical metadata
    medical_specialty: Optional[MedicalSpecialty] = Field(default=None, description="Relevant medical specialty")
    urgency_level: Optional[UrgencyLevel] = Field(default=None, description="Clinical urgency assessment")
    requires_human_review: bool = Field(default=False, description="Whether human review is recommended")
    
    # Processing metadata
    processing_mode: ProcessingMode = Field(default=ProcessingMode.ONLINE, description="Processing mode used")
    device_type: DeviceType = Field(default=DeviceType.TABLET, description="Device type used")
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence score must be between 0.0 and 1.0')
        return v

class EmergencyAssessment(BaseModel):
    """Emergency clinical assessment result."""
    
    assessment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    urgency_level: UrgencyLevel = Field(..., description="Assessed urgency level")
    triage_category: str = Field(..., description="Emergency triage category")
    time_to_treatment: Optional[int] = Field(default=None, description="Recommended time to treatment (minutes)")
    
    # Clinical indicators
    red_flags: List[str] = Field(default_factory=list, description="Critical warning signs")
    vital_sign_concerns: List[str] = Field(default_factory=list, description="Concerning vital signs")
    symptom_severity: Dict[str, str] = Field(default_factory=dict, description="Symptom severity assessment")
    
    # Recommendations
    immediate_actions: List[str] = Field(default_factory=list, description="Immediate medical actions")
    monitoring_requirements: List[str] = Field(default_factory=list, description="Required monitoring")
    specialist_consultation: List[str] = Field(default_factory=list, description="Recommended specialists")
    
    # Assessment metadata
    assessment_confidence: float = Field(..., description="Confidence in emergency assessment")
    assessment_timestamp: datetime = Field(default_factory=datetime.utcnow)
    assessment_method: str = Field(default="gemma_emergency", description="Assessment methodology")
    
    @validator('assessment_confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Assessment confidence must be between 0.0 and 1.0')
        return v

class OfflineCapability(BaseModel):
    """Offline processing capability assessment."""
    
    capability_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    offline_mode_available: bool = Field(..., description="Whether offline mode is available")
    supported_functions: List[str] = Field(..., description="Functions available offline")
    limitations: List[str] = Field(default_factory=list, description="Offline mode limitations")
    
    # Performance in offline mode
    offline_accuracy: float = Field(..., description="Expected accuracy in offline mode")
    offline_response_time: float = Field(..., description="Expected response time offline (ms)")
    storage_requirements_mb: float = Field(..., description="Storage requirements for offline mode")
    
    # Sync capabilities
    sync_required: bool = Field(default=True, description="Whether periodic sync is required")
    last_sync_timestamp: Optional[datetime] = Field(default=None, description="Last successful sync")
    pending_updates: int = Field(default=0, description="Number of pending updates")
    
    @validator('offline_accuracy')
    def validate_accuracy(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Offline accuracy must be between 0.0 and 1.0')
        return v

class EdgeDeploymentConfig(BaseModel):
    """Configuration for edge device deployment."""
    
    deployment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_device: DeviceType = Field(..., description="Target device type")
    deployment_environment: str = Field(..., description="Deployment environment")
    
    # Resource constraints
    max_memory_mb: float = Field(..., description="Maximum memory allocation")
    max_storage_mb: float = Field(..., description="Maximum storage allocation")
    max_cpu_usage: float = Field(default=80.0, description="Maximum CPU usage percentage")
    
    # Model optimization
    quantization_level: str = Field(default="int8", description="Model quantization level")
    pruning_ratio: float = Field(default=0.0, description="Model pruning ratio")
    optimization_target: str = Field(default="balanced", description="Optimization target (speed/size/accuracy)")
    
    # Connectivity settings
    requires_internet: bool = Field(default=False, description="Whether internet connection is required")
    sync_frequency_hours: int = Field(default=24, description="Sync frequency in hours")
    offline_duration_hours: int = Field(default=72, description="Maximum offline operation duration")
    
    # Security settings
    local_encryption_enabled: bool = Field(default=True, description="Enable local data encryption")
    secure_boot_required: bool = Field(default=True, description="Require secure boot")
    attestation_enabled: bool = Field(default=True, description="Enable device attestation")
    
    @validator('max_cpu_usage')
    def validate_cpu_usage(cls, v):
        if not 0.0 <= v <= 100.0:
            raise ValueError('CPU usage must be between 0.0 and 100.0')
        return v
    
    @validator('pruning_ratio')
    def validate_pruning(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Pruning ratio must be between 0.0 and 1.0')
        return v

class ModelUpdateRequest(BaseModel):
    """Request for model update via federated learning."""
    
    update_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_node: str = Field(..., description="Source node identifier")
    update_version: str = Field(..., description="Update version")
    
    # Update content
    weight_updates: Dict[str, Any] = Field(..., description="Model weight updates")
    metadata_updates: Dict[str, Any] = Field(default_factory=dict, description="Model metadata updates")
    
    # Update metadata
    training_samples: int = Field(..., description="Number of training samples used")
    training_accuracy: float = Field(..., description="Training accuracy achieved")
    validation_accuracy: float = Field(..., description="Validation accuracy")
    
    # Security and validation
    digital_signature: str = Field(..., description="Digital signature for update verification")
    checksum: str = Field(..., description="Update checksum")
    encryption_used: bool = Field(default=True, description="Whether update is encrypted")
    
    # Timing
    creation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    expiry_timestamp: datetime = Field(..., description="Update expiry time")
    priority_level: str = Field(default="normal", description="Update priority level")
    
    @validator('training_accuracy', 'validation_accuracy')
    def validate_accuracy(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Accuracy must be between 0.0 and 1.0')
        return v

class ClinicalProtocol(BaseModel):
    """Clinical protocol definition for edge AI."""
    
    protocol_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    protocol_name: str = Field(..., description="Name of clinical protocol")
    medical_specialty: MedicalSpecialty = Field(..., description="Relevant medical specialty")
    evidence_level: str = Field(..., description="Evidence level (A, B, C)")
    
    # Protocol content
    clinical_guidelines: List[str] = Field(..., description="Clinical guidelines")
    decision_criteria: Dict[str, Any] = Field(..., description="Decision criteria")
    contraindications: List[str] = Field(default_factory=list, description="Contraindications")
    monitoring_requirements: List[str] = Field(default_factory=list, description="Monitoring requirements")
    
    # Implementation details
    implementation_steps: List[str] = Field(..., description="Implementation steps")
    quality_metrics: List[str] = Field(default_factory=list, description="Quality metrics")
    audit_requirements: List[str] = Field(default_factory=list, description="Audit requirements")
    
    # Protocol metadata
    version: str = Field(..., description="Protocol version")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    review_date: Optional[datetime] = Field(default=None, description="Next review date")
    approval_status: str = Field(default="approved", description="Approval status")

class PerformanceBenchmark(BaseModel):
    """Performance benchmark results for edge AI."""
    
    benchmark_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_type: DeviceType = Field(..., description="Device type tested")
    model_configuration: str = Field(..., description="Model configuration")
    
    # Performance metrics
    inference_time_ms: float = Field(..., description="Average inference time")
    throughput_qps: float = Field(..., description="Queries per second")
    memory_usage_mb: float = Field(..., description="Memory usage")
    cpu_utilization: float = Field(..., description="CPU utilization percentage")
    gpu_utilization: Optional[float] = Field(default=None, description="GPU utilization percentage")
    
    # Accuracy metrics
    accuracy_score: float = Field(..., description="Model accuracy")
    precision: float = Field(..., description="Precision score")
    recall: float = Field(..., description="Recall score")
    f1_score: float = Field(..., description="F1 score")
    
    # Resource efficiency
    energy_consumption: Optional[float] = Field(default=None, description="Energy consumption (watts)")
    battery_life_hours: Optional[float] = Field(default=None, description="Battery life impact")
    thermal_impact: Optional[float] = Field(default=None, description="Thermal impact (celsius)")
    
    # Benchmark metadata
    test_dataset_size: int = Field(..., description="Test dataset size")
    benchmark_timestamp: datetime = Field(default_factory=datetime.utcnow)
    benchmark_duration_minutes: float = Field(..., description="Benchmark duration")
    
    @validator('accuracy_score', 'precision', 'recall', 'f1_score')
    def validate_metrics(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Metric must be between 0.0 and 1.0')
        return v
    
    @validator('cpu_utilization')
    def validate_cpu(cls, v):
        if not 0.0 <= v <= 100.0:
            raise ValueError('CPU utilization must be between 0.0 and 100.0')
        return v