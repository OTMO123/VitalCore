"""
Privacy Computing Schemas for Healthcare Platform V2.0

Data models and schemas for advanced privacy-preserving computation including
homomorphic encryption, secure multiparty computation, and differential privacy.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class PrivacyLevel(str, Enum):
    """Privacy levels for data processing."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"


class EncryptionScheme(str, Enum):
    """Homomorphic encryption schemes."""
    CKKS = "ckks"  # Approximate numbers
    BFV = "bfv"    # Exact integers
    BGV = "bgv"    # Exact integers
    TFHE = "tfhe"  # Boolean operations


class MPCProtocol(str, Enum):
    """Secure multiparty computation protocols."""
    SHAMIR = "shamir"
    BGW = "bgw"
    GMW = "gmw"
    SPDZ = "spdz"


class PrivacyMechanism(str, Enum):
    """Differential privacy mechanisms."""
    GAUSSIAN = "gaussian"
    LAPLACE = "laplace"
    EXPONENTIAL = "exponential"
    SPARSE_VECTOR = "sparse_vector"


class PrivacyConfig(BaseModel):
    """Configuration for privacy-preserving operations."""
    
    privacy_level: PrivacyLevel = PrivacyLevel.HIGH
    enable_homomorphic_encryption: bool = True
    enable_secure_multiparty_computation: bool = True
    enable_differential_privacy: bool = True
    
    # Differential privacy parameters
    epsilon: float = Field(default=1.0, ge=0.001, le=10.0)
    delta: float = Field(default=1e-5, ge=1e-10, le=1e-3)
    sensitivity: float = Field(default=1.0, ge=0.1, le=10.0)
    
    # Homomorphic encryption parameters
    encryption_scheme: EncryptionScheme = EncryptionScheme.CKKS
    poly_modulus_degree: int = Field(default=8192, ge=1024, le=32768)
    coeff_modulus_bits: List[int] = Field(default=[60, 40, 40, 60])
    scale: float = Field(default=2**40, ge=2**20, le=2**60)
    
    # MPC parameters
    mpc_protocol: MPCProtocol = MPCProtocol.SHAMIR
    threshold: int = Field(default=2, ge=2, le=10)
    num_parties: int = Field(default=3, ge=3, le=20)
    
    # Performance settings
    batch_size: int = Field(default=1000, ge=1, le=10000)
    parallel_processing: bool = True
    cache_intermediate_results: bool = True


class HEContext(BaseModel):
    """Homomorphic encryption context."""
    
    context_id: str
    encryption_scheme: EncryptionScheme
    poly_modulus_degree: int
    coeff_modulus_bits: List[int]
    scale: float
    public_key: Optional[str] = None
    secret_key: Optional[str] = None
    relin_keys: Optional[str] = None
    galois_keys: Optional[str] = None
    created_timestamp: datetime
    is_ready: bool = False


class EncryptedData(BaseModel):
    """Encrypted data container for homomorphic operations."""
    
    data_id: str
    encrypted_values: str  # Base64 encoded ciphertext
    encryption_scheme: EncryptionScheme
    context_id: str
    data_type: str  # "vector", "matrix", "scalar"
    dimensions: List[int]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    encryption_timestamp: datetime
    checksum: str


class EncryptedResult(BaseModel):
    """Result of homomorphic computation."""
    
    result_id: str
    encrypted_result: str  # Base64 encoded result
    computation_type: str
    input_data_ids: List[str]
    context_id: str
    computation_metadata: Dict[str, Any] = Field(default_factory=dict)
    computation_timestamp: datetime
    verification_hash: str


class SecretShare(BaseModel):
    """Secret share for secure multiparty computation."""
    
    share_id: str
    party_id: str
    share_value: str  # Encoded share
    share_index: int
    protocol: MPCProtocol
    threshold: int
    total_parties: int
    data_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_timestamp: datetime


class MPCComputation(BaseModel):
    """Secure multiparty computation definition."""
    
    computation_id: str
    protocol: MPCProtocol
    participating_parties: List[str]
    computation_function: str
    input_shares: Dict[str, List[SecretShare]]
    threshold: int
    privacy_level: PrivacyLevel
    computation_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_timestamp: datetime
    status: str = "pending"


class MPCResult(BaseModel):
    """Result of secure multiparty computation."""
    
    result_id: str
    computation_id: str
    result_shares: List[SecretShare]
    reconstructed_result: Optional[Any] = None
    participating_parties: List[str]
    computation_time_seconds: float
    verification_status: str
    result_metadata: Dict[str, Any] = Field(default_factory=dict)
    completion_timestamp: datetime


class DifferentialPrivacyParams(BaseModel):
    """Differential privacy parameters."""
    
    epsilon: float = Field(ge=0.001, le=10.0)
    delta: float = Field(ge=1e-10, le=1e-3)
    sensitivity: float = Field(ge=0.1, le=10.0)
    mechanism: PrivacyMechanism
    clipping_bound: Optional[float] = None
    noise_multiplier: Optional[float] = None
    composition_method: str = "basic"  # "basic", "advanced", "rdp"


class PrivatizedData(BaseModel):
    """Data processed with differential privacy."""
    
    data_id: str
    original_data_hash: str
    privatized_values: Union[List[float], Dict[str, float]]
    privacy_params: DifferentialPrivacyParams
    noise_added: float
    privacy_cost: float  # Epsilon consumed
    data_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    privatization_timestamp: datetime


class PrivacyBudget(BaseModel):
    """Privacy budget tracking for differential privacy."""
    
    budget_id: str
    user_id: Optional[str] = None
    dataset_id: str
    total_epsilon: float
    consumed_epsilon: float
    remaining_epsilon: float
    total_delta: float
    consumed_delta: float
    remaining_delta: float
    queries_executed: int
    budget_start_date: datetime
    budget_end_date: datetime
    is_active: bool = True


class PrivacyAuditEvent(BaseModel):
    """Privacy operation audit event."""
    
    event_id: str
    event_type: str  # "he_operation", "mpc_computation", "dp_query"
    user_id: Optional[str] = None
    operation_id: str
    privacy_level: PrivacyLevel
    data_accessed: List[str]
    privacy_cost: Dict[str, float]  # epsilon, delta consumed
    computation_details: Dict[str, Any]
    result_hash: Optional[str] = None
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class PrivacyValidationResult(BaseModel):
    """Result of privacy validation check."""
    
    validation_id: str
    operation_type: str
    is_valid: bool
    privacy_level_achieved: PrivacyLevel
    epsilon_consumed: float
    delta_consumed: float
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    validation_timestamp: datetime


class FederatedPrivacyConfig(BaseModel):
    """Configuration for federated privacy operations."""
    
    federation_id: str
    participating_institutions: List[str]
    privacy_level: PrivacyLevel
    local_dp_params: DifferentialPrivacyParams
    secure_aggregation_enabled: bool = True
    homomorphic_encryption_enabled: bool = True
    minimum_participants: int = Field(default=3, ge=2, le=20)
    privacy_budget_per_institution: PrivacyBudget
    communication_encryption: bool = True
    audit_all_operations: bool = True


class PrivacyMetrics(BaseModel):
    """Privacy operation performance metrics."""
    
    metrics_id: str
    operation_type: str
    privacy_level: PrivacyLevel
    data_size_bytes: int
    processing_time_seconds: float
    memory_usage_mb: float
    privacy_cost: Dict[str, float]
    accuracy_loss_percentage: Optional[float] = None
    utility_score: Optional[float] = None
    encryption_overhead: Optional[float] = None
    communication_overhead: Optional[float] = None
    timestamp: datetime


class PrivacyReport(BaseModel):
    """Comprehensive privacy operations report."""
    
    report_id: str
    report_period_start: datetime
    report_period_end: datetime
    total_operations: int
    operations_by_type: Dict[str, int]
    privacy_budget_utilization: Dict[str, float]
    security_incidents: List[PrivacyAuditEvent]
    performance_metrics: PrivacyMetrics
    compliance_status: Dict[str, bool]
    recommendations: List[str]
    generated_timestamp: datetime