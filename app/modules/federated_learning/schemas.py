"""
Federated Learning Schemas for Healthcare Platform V2.0

Pydantic schemas for federated learning orchestration, secure aggregation,
and privacy-preserving multi-institutional healthcare AI training.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid

class FLStatus(str, Enum):
    """Federated learning status."""
    INITIALIZING = "initializing"
    RECRUITING = "recruiting"
    TRAINING = "training"
    AGGREGATING = "aggregating"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AggregationMethod(str, Enum):
    """Model aggregation methods."""
    FEDAVG = "fedavg"
    FEDPROX = "fedprox"
    FEDOPT = "fedopt"
    SCAFFOLD = "scaffold"
    SECURE_AGGREGATION = "secure_aggregation"

class PrivacyLevel(str, Enum):
    """Privacy levels for federated learning."""
    BASIC = "basic"
    STANDARD = "standard"
    HIGH = "high"
    MAXIMUM = "maximum"

class ParticipantType(str, Enum):
    """Types of federated learning participants."""
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    RESEARCH_INSTITUTION = "research_institution"
    GOVERNMENT_AGENCY = "government_agency"

class FLConfig(BaseModel):
    """Configuration for federated learning orchestrator."""
    
    # Basic FL settings
    coordinator_id: str = Field(..., description="FL coordinator identifier")
    min_participants: int = Field(default=3, description="Minimum number of participants")
    max_participants: int = Field(default=50, description="Maximum number of participants")
    
    # Round settings
    max_rounds: int = Field(default=100, description="Maximum training rounds")
    min_rounds: int = Field(default=5, description="Minimum training rounds")
    round_timeout_minutes: int = Field(default=60, description="Round timeout in minutes")
    
    # Aggregation settings
    default_aggregation_method: AggregationMethod = Field(default=AggregationMethod.FEDAVG)
    consensus_threshold: float = Field(default=0.8, description="Consensus threshold for decisions")
    minimum_success_rate: float = Field(default=0.7, description="Minimum success rate for operations")
    
    # Privacy settings
    privacy_level: PrivacyLevel = Field(default=PrivacyLevel.HIGH)
    enable_differential_privacy: bool = Field(default=True)
    privacy_epsilon: float = Field(default=1.0, description="Differential privacy epsilon")
    privacy_delta: float = Field(default=1e-5, description="Differential privacy delta")
    
    # Security settings
    enable_secure_aggregation: bool = Field(default=True)
    enable_homomorphic_encryption: bool = Field(default=True)
    require_participant_certificates: bool = Field(default=True)
    
    # Performance settings
    max_concurrent_rounds: int = Field(default=3)
    collection_timeout_minutes: int = Field(default=30)
    collection_poll_interval_seconds: int = Field(default=10)
    minimum_participation_rate: float = Field(default=0.6)
    
    # Convergence settings
    convergence_threshold: float = Field(default=0.001, description="Model convergence threshold")
    accuracy_threshold: float = Field(default=0.01, description="Accuracy improvement threshold")
    target_accuracy: float = Field(default=0.85, description="Target model accuracy")
    
    # Data requirements
    min_data_size_per_participant: int = Field(default=100, description="Minimum data samples per participant")
    
    @validator('privacy_epsilon')
    def validate_epsilon(cls, v):
        if v <= 0:
            raise ValueError('Privacy epsilon must be positive')
        return v
    
    @validator('consensus_threshold', 'minimum_success_rate', 'minimum_participation_rate')
    def validate_rates(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Rate values must be between 0.0 and 1.0')
        return v

class ModelUpdate(BaseModel):
    """Model update from a federated learning participant."""
    
    update_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    participant_id: str = Field(..., description="Participant identifier")
    round_number: int = Field(..., description="Training round number")
    
    # Model data
    model_weights: Dict[str, Any] = Field(..., description="Updated model weights")
    model_version: str = Field(default="1.0", description="Model version")
    
    # Training metrics
    training_samples: int = Field(..., description="Number of training samples used")
    training_loss: float = Field(..., description="Training loss achieved")
    validation_accuracy: float = Field(..., description="Validation accuracy")
    training_time_minutes: float = Field(default=0.0, description="Training time in minutes")
    
    # Privacy metrics
    privacy_epsilon: Optional[float] = Field(default=None, description="Differential privacy epsilon used")
    privacy_delta: Optional[float] = Field(default=None, description="Differential privacy delta used")
    noise_scale: Optional[float] = Field(default=None, description="Noise scale applied")
    
    # Security and integrity
    checksum: str = Field(..., description="Update checksum for integrity")
    digital_signature: Optional[str] = Field(default=None, description="Digital signature")
    
    # Metadata
    update_timestamp: datetime = Field(default_factory=datetime.utcnow)
    participant_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('training_samples')
    def validate_training_samples(cls, v):
        if v <= 0:
            raise ValueError('Training samples must be positive')
        return v
    
    @validator('validation_accuracy')
    def validate_accuracy(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Validation accuracy must be between 0.0 and 1.0')
        return v

class GlobalModel(BaseModel):
    """Global model after federated aggregation."""
    
    model_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    model_weights: Dict[str, Any] = Field(..., description="Aggregated model weights")
    model_version: str = Field(default="1.0", description="Model version")
    
    # Aggregation metadata
    aggregation_method: str = Field(..., description="Aggregation method used")
    participant_count: int = Field(..., description="Number of participants in aggregation")
    round_number: int = Field(..., description="Training round number")
    
    # Performance metrics
    global_accuracy: float = Field(..., description="Estimated global accuracy")
    global_loss: Optional[float] = Field(default=None, description="Estimated global loss")
    convergence_metrics: Dict[str, float] = Field(default_factory=dict)
    
    # Privacy and security
    privacy_budget_consumed: float = Field(default=0.0, description="Total privacy budget consumed")
    model_checksum: str = Field(..., description="Model checksum for integrity")
    
    # Timestamps
    aggregation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('global_accuracy')
    def validate_accuracy(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Global accuracy must be between 0.0 and 1.0')
        return v

class FLNetwork(BaseModel):
    """Federated learning network configuration."""
    
    network_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    network_name: str = Field(..., description="Network name")
    
    # Participants
    participants: List[Any] = Field(..., description="List of participating institutions")  # Hospital objects
    coordinator_id: str = Field(..., description="Network coordinator")
    
    # Network settings
    aggregation_method: AggregationMethod = Field(..., description="Default aggregation method")
    privacy_level: PrivacyLevel = Field(..., description="Network privacy level")
    encryption_enabled: bool = Field(default=True)
    
    # Training parameters
    consensus_threshold: float = Field(..., description="Consensus threshold")
    max_rounds: int = Field(..., description="Maximum training rounds")
    target_accuracy: float = Field(..., description="Target accuracy")
    
    # Network status
    status: str = Field(default="active", description="Network status")
    created_timestamp: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)

class FLRound(BaseModel):
    """Federated learning round information."""
    
    round_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    network_id: str = Field(..., description="Network identifier")
    round_number: int = Field(..., description="Round number")
    
    # Round settings
    round_start_time: datetime = Field(default_factory=datetime.utcnow)
    round_end_time: Optional[datetime] = Field(default=None)
    timeout_minutes: int = Field(default=60)
    
    # Participants
    invited_participants: List[str] = Field(..., description="Invited participant IDs")
    active_participants: List[str] = Field(default_factory=list, description="Active participant IDs")
    completed_participants: List[str] = Field(default_factory=list, description="Completed participant IDs")
    
    # Round status
    status: FLStatus = Field(default=FLStatus.INITIALIZING)
    global_model_id: Optional[str] = Field(default=None, description="Resulting global model ID")
    
    # Performance metrics
    round_accuracy: Optional[float] = Field(default=None)
    participation_rate: Optional[float] = Field(default=None)
    aggregation_time_seconds: Optional[float] = Field(default=None)

class ConvergenceMetrics(BaseModel):
    """Convergence metrics for federated learning."""
    
    round_number: int = Field(..., description="Round number")
    global_accuracy: float = Field(..., description="Global model accuracy")
    
    # Convergence indicators
    weight_difference: float = Field(..., description="Weight difference from previous round")
    accuracy_improvement: float = Field(..., description="Accuracy improvement")
    loss_improvement: float = Field(..., description="Loss improvement")
    
    # Convergence status
    converged: bool = Field(..., description="Whether model has converged")
    convergence_score: float = Field(..., description="Convergence score (0-1)")
    
    # Predictions
    rounds_since_improvement: int = Field(default=0)
    estimated_rounds_to_convergence: Optional[int] = Field(default=None)
    
    # Timestamp
    measurement_timestamp: datetime = Field(default_factory=datetime.utcnow)

class EncryptionKey(BaseModel):
    """Encryption key information for federated learning."""
    
    key_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    master_key: bytes = Field(..., description="Master encryption key")
    participant_keys: Dict[str, bytes] = Field(..., description="Participant-specific keys")
    
    # Key metadata
    algorithm: str = Field(default="AES-256-GCM", description="Encryption algorithm")
    key_size: int = Field(default=256, description="Key size in bits")
    
    # Key lifecycle
    created_timestamp: datetime = Field(default_factory=datetime.utcnow)
    expiry_timestamp: Optional[datetime] = Field(default=None)
    rotation_count: int = Field(default=0, description="Number of key rotations")

class EncryptedUpdate(BaseModel):
    """Encrypted model update."""
    
    encrypted_update_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    participant_id: str = Field(..., description="Participant identifier")
    
    # Encrypted data
    encrypted_weights: bytes = Field(..., description="Encrypted model weights")
    encryption_metadata: Dict[str, Any] = Field(..., description="Encryption metadata")
    
    # Security
    initialization_vector: bytes = Field(..., description="Encryption IV")
    authentication_tag: bytes = Field(..., description="Authentication tag")
    key_id: str = Field(..., description="Encryption key identifier")
    
    # Timestamps
    encryption_timestamp: datetime = Field(default_factory=datetime.utcnow)

class SecurityAudit(BaseModel):
    """Security audit record for federated learning."""
    
    audit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    network_id: str = Field(..., description="Network identifier")
    round_id: Optional[str] = Field(default=None, description="Round identifier")
    
    # Audit details
    audit_type: str = Field(..., description="Type of security audit")
    security_events: List[str] = Field(default_factory=list, description="Security events detected")
    threat_level: str = Field(default="low", description="Assessed threat level")
    
    # Audit results
    security_score: float = Field(..., description="Security score (0-1)")
    vulnerabilities: List[str] = Field(default_factory=list, description="Identified vulnerabilities")
    recommendations: List[str] = Field(default_factory=list, description="Security recommendations")
    
    # Compliance
    compliance_status: Dict[str, bool] = Field(default_factory=dict, description="Compliance status")
    
    # Timestamps
    audit_timestamp: datetime = Field(default_factory=datetime.utcnow)

class PrivacyBudget(BaseModel):
    """Privacy budget tracking for differential privacy."""
    
    budget_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    network_id: str = Field(..., description="Network identifier")
    participant_id: Optional[str] = Field(default=None, description="Participant identifier")
    
    # Privacy parameters
    total_epsilon: float = Field(..., description="Total privacy budget (epsilon)")
    total_delta: float = Field(..., description="Total privacy budget (delta)")
    consumed_epsilon: float = Field(default=0.0, description="Consumed epsilon")
    consumed_delta: float = Field(default=0.0, description="Consumed delta")
    
    # Budget allocation
    round_epsilon_allocation: float = Field(..., description="Epsilon allocation per round")
    remaining_rounds: int = Field(..., description="Estimated remaining rounds")
    
    # Budget tracking
    budget_usage_history: List[Dict[str, float]] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('total_epsilon', 'total_delta', 'consumed_epsilon', 'consumed_delta')
    def validate_privacy_params(cls, v):
        if v < 0:
            raise ValueError('Privacy parameters must be non-negative')
        return v

class PrivateData(BaseModel):
    """Privately processed data for federated learning."""
    
    data_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    participant_id: str = Field(..., description="Participant identifier")
    
    # Privacy mechanisms applied
    privacy_mechanisms: List[str] = Field(default_factory=list, description="Applied privacy mechanisms")
    epsilon_used: float = Field(default=0.0, description="Epsilon consumed")
    delta_used: float = Field(default=0.0, description="Delta consumed")
    
    # Data characteristics
    original_data_size: int = Field(..., description="Original data size")
    private_data_size: int = Field(..., description="Private data size")
    utility_score: float = Field(..., description="Data utility score (0-1)")
    
    # Processing metadata
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)
    privacy_guarantees: Dict[str, Any] = Field(default_factory=dict)

class FLHistory(BaseModel):
    """Historical record of federated learning activities."""
    
    history_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    network_id: str = Field(..., description="Network identifier")
    
    # Training history
    total_rounds: int = Field(..., description="Total rounds completed")
    total_participants: int = Field(..., description="Total unique participants")
    training_duration: timedelta = Field(..., description="Total training duration")
    
    # Performance history
    accuracy_progression: List[float] = Field(default_factory=list, description="Accuracy over rounds")
    loss_progression: List[float] = Field(default_factory=list, description="Loss over rounds")
    convergence_round: Optional[int] = Field(default=None, description="Round where convergence achieved")
    
    # Privacy history
    total_privacy_budget_consumed: float = Field(default=0.0, description="Total epsilon consumed")
    privacy_violations: List[str] = Field(default_factory=list, description="Privacy violations detected")
    
    # Participant history
    participant_contributions: Dict[str, float] = Field(default_factory=dict)
    participant_reliability: Dict[str, float] = Field(default_factory=dict)
    
    # Timestamps
    training_start: datetime = Field(..., description="Training start time")
    training_end: Optional[datetime] = Field(default=None, description="Training end time")

class PrivacyAuditReport(BaseModel):
    """Privacy audit report for federated learning."""
    
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    network_id: str = Field(..., description="Network identifier")
    audit_period_start: datetime = Field(..., description="Audit period start")
    audit_period_end: datetime = Field(..., description="Audit period end")
    
    # Privacy analysis
    privacy_budget_analysis: Dict[str, float] = Field(default_factory=dict)
    privacy_violations: List[str] = Field(default_factory=list)
    privacy_risks: List[str] = Field(default_factory=list)
    
    # Compliance assessment
    dp_compliance: bool = Field(..., description="Differential privacy compliance")
    k_anonymity_compliance: bool = Field(..., description="K-anonymity compliance")
    gdpr_compliance: bool = Field(..., description="GDPR compliance")
    hipaa_compliance: bool = Field(..., description="HIPAA compliance")
    
    # Recommendations
    privacy_recommendations: List[str] = Field(default_factory=list)
    risk_mitigation_steps: List[str] = Field(default_factory=list)
    
    # Report metadata
    auditor_id: str = Field(..., description="Auditor identifier")
    report_generation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    report_version: str = Field(default="1.0")