"""
Vector Store Schemas for Healthcare ML Platform

Pydantic schemas for Milvus vector database operations with healthcare-specific
data structures and HIPAA compliance validation.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import uuid

class VectorStatus(str, Enum):
    """Vector indexing status."""
    PENDING = "pending"
    INDEXED = "indexed"
    FAILED = "failed"
    DELETED = "deleted"

class SimilarityMetric(str, Enum):
    """Similarity calculation metrics."""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean" 
    IP = "inner_product"

class MedicalCategory(str, Enum):
    """Medical condition categories for filtering."""
    CARDIOVASCULAR = "cardiovascular"
    RESPIRATORY = "respiratory"
    ENDOCRINE = "endocrine"
    NEUROLOGICAL = "neurological"
    GASTROENTEROLOGICAL = "gastroenterological"
    MUSCULOSKELETAL = "musculoskeletal"
    DERMATOLOGICAL = "dermatological"
    INFECTIOUS = "infectious"
    PSYCHIATRIC = "psychiatric"
    ONCOLOGICAL = "oncological"

class SimilarCase(BaseModel):
    """
    Similar case result from vector similarity search.
    
    Represents a similar patient case found through Clinical BERT
    embedding similarity with anonymized clinical metadata.
    """
    
    case_id: str = Field(..., description="Anonymized case identifier")
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    distance: float = Field(..., description="Vector distance metric")
    
    # Anonymized clinical metadata
    age_group: str = Field(..., description="Medical age categorization")
    gender_category: str = Field(..., description="Gender category")
    pregnancy_status: str = Field(..., description="Pregnancy status category")
    location_category: str = Field(..., description="Geographic exposure category")
    season_category: str = Field(..., description="Seasonal disease pattern category")
    
    # Medical features
    medical_categories: List[MedicalCategory] = Field(default_factory=list, description="Primary medical conditions")
    risk_factors: List[str] = Field(default_factory=list, description="Associated risk factors")
    severity_indicators: Dict[str, float] = Field(default_factory=dict, description="Clinical severity metrics")
    
    # Metadata
    indexed_timestamp: datetime = Field(..., description="When case was indexed")
    last_updated: datetime = Field(..., description="Last metadata update")
    confidence_score: float = Field(..., description="Clinical data confidence (0.0 to 1.0)")
    
    @field_validator('similarity_score', 'confidence_score')
    @classmethod
    def validate_scores(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Scores must be between 0.0 and 1.0')
        return v

class VectorSearchRequest(BaseModel):
    """Request for vector similarity search."""
    
    query_vector: List[float] = Field(..., description="768-dimensional Clinical BERT embedding")
    top_k: int = Field(default=100, description="Number of similar cases to return")
    similarity_threshold: float = Field(default=0.6, description="Minimum similarity score")
    
    # Search filters
    age_groups: Optional[List[str]] = Field(default=None, description="Filter by age groups")
    gender_categories: Optional[List[str]] = Field(default=None, description="Filter by gender")
    medical_categories: Optional[List[MedicalCategory]] = Field(default=None, description="Filter by conditions")
    location_categories: Optional[List[str]] = Field(default=None, description="Filter by location")
    season_categories: Optional[List[str]] = Field(default=None, description="Filter by season")
    
    # Time range filters
    indexed_after: Optional[datetime] = Field(default=None, description="Cases indexed after date")
    indexed_before: Optional[datetime] = Field(default=None, description="Cases indexed before date")
    
    @field_validator('query_vector')
    @classmethod
    def validate_embedding_dimension(cls, v):
        if len(v) != 768:
            raise ValueError('Query vector must be 768-dimensional (Clinical BERT)')
        return v
    
    @field_validator('top_k')
    @classmethod
    def validate_top_k(cls, v):
        if not 1 <= v <= 1000:
            raise ValueError('top_k must be between 1 and 1000')
        return v

class VectorIndexRequest(BaseModel):
    """Request to index a new vector in Milvus."""
    
    profile_id: str = Field(..., description="Anonymized ML profile identifier")
    vector_embedding: List[float] = Field(..., description="768-dimensional Clinical BERT embedding")
    
    # Anonymized metadata for filtering
    age_group: str = Field(..., description="Medical age group")
    gender_category: str = Field(..., description="Gender category")
    pregnancy_status: str = Field(..., description="Pregnancy status")
    location_category: str = Field(..., description="Location category")
    season_category: str = Field(..., description="Season category")
    
    # Clinical metadata
    medical_categories: List[MedicalCategory] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    severity_indicators: Dict[str, float] = Field(default_factory=dict)
    
    # Quality metrics
    confidence_score: float = Field(..., description="Clinical data confidence")
    compliance_validated: bool = Field(..., description="HIPAA compliance validated")
    
    @field_validator('vector_embedding')
    @classmethod
    def validate_embedding_dimension(cls, v):
        if len(v) != 768:
            raise ValueError('Vector embedding must be 768-dimensional')
        return v

class VectorCollection(BaseModel):
    """Milvus collection configuration for healthcare vectors."""
    
    collection_name: str = Field(..., description="Collection name")
    vector_dimension: int = Field(default=768, description="Vector dimensionality")
    index_type: str = Field(default="IVF_FLAT", description="Milvus index type")
    metric_type: SimilarityMetric = Field(default=SimilarityMetric.COSINE, description="Similarity metric")
    
    # HIPAA security settings
    encryption_enabled: bool = Field(default=True, description="Enable data encryption")
    access_controlled: bool = Field(default=True, description="Enable access controls")
    audit_logging: bool = Field(default=True, description="Enable audit logging")
    
    # Performance settings
    nlist: int = Field(default=1024, description="Number of cluster units")
    nprobe: int = Field(default=16, description="Number of units to query")
    
    created_timestamp: datetime = Field(default_factory=datetime.utcnow)
    last_optimized: Optional[datetime] = Field(default=None)
    
    @field_validator('vector_dimension')
    @classmethod
    def validate_dimension(cls, v):
        if v != 768:
            raise ValueError('Healthcare collections must use 768-dimensional vectors')
        return v

class MilvusConfig(BaseModel):
    """Configuration for Milvus vector database connection."""
    
    host: str = Field(default="localhost", description="Milvus server host")
    port: int = Field(default=19530, description="Milvus server port")
    secure: bool = Field(default=True, description="Enable TLS encryption")
    
    # Authentication
    username: Optional[str] = Field(default=None, description="Milvus username")
    password: Optional[str] = Field(default=None, description="Milvus password")
    
    # Connection settings
    connection_timeout: int = Field(default=30, description="Connection timeout seconds")
    keep_alive: bool = Field(default=True, description="Keep connection alive")
    retry_attempts: int = Field(default=3, description="Connection retry attempts")
    
    # Healthcare-specific settings
    default_collection: str = Field(default="healthcare_vectors", description="Default collection name")
    enable_encryption: bool = Field(default=True, description="Enable vector encryption")
    audit_operations: bool = Field(default=True, description="Audit all operations")
    
    # Performance tuning
    batch_size: int = Field(default=1000, description="Batch size for bulk operations")
    search_timeout: int = Field(default=60, description="Search timeout seconds")
    cache_size: int = Field(default=1000, description="Query result cache size")

class VectorOperationResult(BaseModel):
    """Result of vector database operation."""
    
    operation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Operation identifier")
    operation_type: str = Field(..., description="Type of operation performed")
    success: bool = Field(..., description="Operation success status")
    
    # Metrics
    affected_count: int = Field(default=0, description="Number of vectors affected")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    
    # Results
    vector_ids: List[str] = Field(default_factory=list, description="IDs of affected vectors")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    
    # Audit trail
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = Field(default=None, description="User who performed operation")

class VectorCollectionStats(BaseModel):
    """Statistics for a Milvus collection."""
    
    collection_name: str = Field(..., description="Collection name")
    total_vectors: int = Field(..., description="Total number of vectors")
    indexed_vectors: int = Field(..., description="Number of indexed vectors")
    
    # Storage metrics
    total_size_mb: float = Field(..., description="Total collection size in MB")
    index_size_mb: float = Field(..., description="Index size in MB")
    
    # Performance metrics
    average_search_latency_ms: float = Field(..., description="Average search latency")
    queries_per_second: float = Field(..., description="Queries per second capability")
    
    # Health indicators
    last_compaction: Optional[datetime] = Field(default=None, description="Last compaction time")
    index_health: str = Field(..., description="Index health status")
    
    # HIPAA compliance
    encryption_status: str = Field(..., description="Encryption status")
    audit_coverage: float = Field(..., description="Percentage of operations audited")
    
    updated_timestamp: datetime = Field(default_factory=datetime.utcnow)

class EmergencySearchRequest(BaseModel):
    """Emergency case similarity search request."""
    
    symptoms: List[str] = Field(..., description="List of symptoms")
    demographics: Dict[str, Any] = Field(..., description="Patient demographics")
    severity_level: str = Field(..., description="Emergency severity level")
    
    # Search parameters
    top_k: int = Field(default=50, description="Number of similar emergency cases")
    time_sensitivity: bool = Field(default=True, description="Prioritize recent cases")
    location_proximity: bool = Field(default=True, description="Consider geographic proximity")
    
    @field_validator('symptoms')
    @classmethod
    def validate_symptoms(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one symptom must be provided')
        return v

class PopulationHealthQuery(BaseModel):
    """Population health analytics query."""
    
    location_category: str = Field(..., description="Geographic area of interest")
    time_range_start: datetime = Field(..., description="Query start date")
    time_range_end: datetime = Field(..., description="Query end date")
    
    # Analysis parameters
    condition_focus: Optional[List[MedicalCategory]] = Field(default=None, description="Focus conditions")
    age_groups: Optional[List[str]] = Field(default=None, description="Target age groups")
    aggregation_level: str = Field(default="weekly", description="Temporal aggregation")
    
    # Risk stratification
    risk_threshold: float = Field(default=0.7, description="Risk score threshold")
    include_trends: bool = Field(default=True, description="Include trend analysis")

class VectorBackupMetadata(BaseModel):
    """Metadata for vector database backups."""
    
    backup_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    collection_name: str = Field(..., description="Backed up collection")
    backup_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Backup details
    vector_count: int = Field(..., description="Number of vectors backed up")
    backup_size_mb: float = Field(..., description="Backup size in MB")
    backup_location: str = Field(..., description="Backup storage location")
    
    # Integrity verification
    checksum: str = Field(..., description="Backup integrity checksum")
    compression_ratio: float = Field(..., description="Compression ratio achieved")
    encryption_applied: bool = Field(..., description="Whether backup is encrypted")
    
    # Restore information
    restore_tested: bool = Field(default=False, description="Whether restore was tested")
    retention_until: datetime = Field(..., description="Backup retention expiry date")