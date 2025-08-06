"""
Data Anonymization Schemas for ML-Ready Healthcare Platform

Pydantic schemas for ML-ready anonymized patient profiles that preserve
clinical similarity while ensuring zero re-identification risk.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from uuid import uuid4

class AnonymizationMethod(str, Enum):
    """Anonymization techniques used."""
    K_ANONYMITY = "k_anonymity"
    DIFFERENTIAL_PRIVACY = "differential_privacy"
    PSEUDONYMIZATION = "pseudonymization"
    GENERALIZATION = "generalization"
    SUPPRESSION = "suppression"

class ComplianceStandard(str, Enum):
    """Compliance standards validated."""
    HIPAA = "hipaa"
    GDPR = "gdpr" 
    SOC2_TYPE_II = "soc2_type_ii"
    FHIR_R4 = "fhir_r4"

class AgeGroup(str, Enum):
    """Medical age categorization for risk assessment."""
    PEDIATRIC = "pediatric"           # < 18
    YOUNG_ADULT = "young_adult"       # 18-24
    REPRODUCTIVE_AGE = "reproductive_age"  # 25-34
    MIDDLE_AGE = "middle_age"         # 35-49
    OLDER_ADULT = "older_adult"       # 50-64
    ELDERLY = "elderly"               # 65+

class PregnancyStatus(str, Enum):
    """Pregnancy status for risk stratification."""
    NOT_PREGNANT = "not_pregnant"
    PREGNANT_TRIMESTER_1 = "pregnant_trimester_1"
    PREGNANT_TRIMESTER_2 = "pregnant_trimester_2" 
    PREGNANT_TRIMESTER_3 = "pregnant_trimester_3"
    POSTPARTUM = "postpartum"
    UNKNOWN = "unknown"

class LocationCategory(str, Enum):
    """Location categorization for disease exposure patterns."""
    URBAN_NORTHEAST = "urban_northeast"
    URBAN_SOUTHEAST = "urban_southeast"
    URBAN_MIDWEST = "urban_midwest"
    URBAN_WEST = "urban_west"
    RURAL_NORTHEAST = "rural_northeast"
    RURAL_SOUTHEAST = "rural_southeast"
    RURAL_MIDWEST = "rural_midwest"
    RURAL_WEST = "rural_west"
    INTERNATIONAL = "international"
    UNKNOWN = "unknown"

class SeasonCategory(str, Enum):
    """Seasonal categorization for disease pattern analysis."""
    WINTER = "winter"    # Respiratory illness peak
    SPRING = "spring"    # Allergy season
    SUMMER = "summer"    # Different disease patterns
    FALL = "fall"        # Flu season beginning

class ClinicalCategory(str, Enum):
    """Clinical history categorization for similarity matching."""
    RESPIRATORY_HISTORY = "respiratory_history"
    CARDIAC_HISTORY = "cardiac_history" 
    ALLERGIC_HISTORY = "allergic_history"
    DIABETIC_HISTORY = "diabetic_history"
    NEUROLOGICAL_HISTORY = "neurological_history"
    PSYCHIATRIC_HISTORY = "psychiatric_history"
    ONCOLOGICAL_HISTORY = "oncological_history"
    INFECTIOUS_DISEASE_HISTORY = "infectious_disease_history"
    AUTOIMMUNE_HISTORY = "autoimmune_history"
    SURGICAL_HISTORY = "surgical_history"

class AnonymizedMLProfile(BaseModel):
    """
    ML-ready anonymized patient profile for disease prediction.
    
    This profile preserves clinical similarity while ensuring zero
    re-identification risk for HIPAA/GDPR compliance.
    """
    # Core identifiers
    anonymous_id: str = Field(..., description="Consistent pseudonymous identifier")
    profile_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique profile identifier")
    
    # Demographic categories (medical risk-based)
    age_group: AgeGroup = Field(..., description="Medical age categorization")
    gender_category: str = Field(..., description="Gender category (male/female/other)")
    pregnancy_status: PregnancyStatus = Field(default=PregnancyStatus.NOT_PREGNANT)
    
    # Geographic and temporal categories
    location_category: LocationCategory = Field(..., description="Location for exposure patterns")
    season_category: SeasonCategory = Field(..., description="Season for disease patterns")
    
    # Clinical history categories
    medical_history_categories: List[ClinicalCategory] = Field(
        default_factory=list,
        description="Categorized medical history for similarity"
    )
    medication_categories: List[str] = Field(
        default_factory=list,
        description="Medication class categories"
    )
    allergy_categories: List[str] = Field(
        default_factory=list,
        description="Allergy type categories"
    )
    
    # Risk stratification
    risk_factors: List[str] = Field(
        default_factory=list,
        description="Quantified risk factor categories"
    )
    
    # ML-ready features
    clinical_text_embedding: Optional[List[float]] = Field(
        default=None,
        description="768-dimensional Clinical BERT embedding"
    )
    categorical_features: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured categorical features for ML"
    )
    
    # Similarity metadata for prediction algorithms
    similarity_metadata: Dict[str, float] = Field(
        default_factory=dict,
        description="Weights for similarity matching algorithms"
    )
    
    # Anonymization metadata
    anonymization_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When anonymization was performed"
    )
    anonymization_version: str = Field(
        default="v1.0",
        description="Anonymization algorithm version"
    )
    
    # Quality and compliance
    prediction_ready: bool = Field(
        default=False,
        description="Ready for ML prediction algorithms"
    )
    compliance_validated: bool = Field(
        default=False,
        description="Passed all compliance validations"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "anonymous_id": "anon_abc123def456",
                "age_group": "reproductive_age",
                "gender_category": "female",
                "pregnancy_status": "pregnant_trimester_3",
                "location_category": "urban_northeast",
                "season_category": "winter",
                "medical_history_categories": ["allergic_history", "respiratory_history"],
                "medication_categories": ["antihistamines", "beta_agonists"],
                "allergy_categories": ["environmental_allergies", "drug_allergies"],
                "risk_factors": ["pregnancy_immunosuppression", "seasonal_exposure"],
                "clinical_text_embedding": [0.23, -0.45, 0.67],  # Truncated for example
                "similarity_metadata": {
                    "medical_similarity_weight": 0.8,
                    "demographic_similarity_weight": 0.3,
                    "temporal_similarity_weight": 0.5
                },
                "prediction_ready": True,
                "compliance_validated": True
            }
        }
    }
    
    @field_validator('clinical_text_embedding')
    @classmethod
    def validate_embedding_dimension(cls, v):
        """Validate Clinical BERT embedding is 768-dimensional."""
        if v is not None and len(v) != 768:
            raise ValueError("Clinical BERT embedding must be 768-dimensional")
        return v
    
    @field_validator('similarity_metadata')
    @classmethod 
    def validate_similarity_weights(cls, v):
        """Validate similarity weights are between 0 and 1."""
        for weight_name, weight_value in v.items():
            if not 0 <= weight_value <= 1:
                raise ValueError(f"Similarity weight {weight_name} must be between 0 and 1")
        return v

class AnonymizationAuditTrail(BaseModel):
    """
    Comprehensive audit trail for anonymization process.
    
    Tracks all anonymization operations for SOC2/HIPAA compliance.
    """
    audit_id: str = Field(default_factory=lambda: str(uuid4()))
    original_patient_id: str = Field(..., description="Original patient identifier (hashed)")
    anonymous_id: str = Field(..., description="Generated anonymous identifier")
    
    # Anonymization process details
    anonymization_method: AnonymizationMethod = Field(..., description="Primary anonymization technique")
    additional_methods: List[AnonymizationMethod] = Field(
        default_factory=list,
        description="Additional anonymization techniques applied"
    )
    
    # Data transformation tracking
    pii_fields_removed: List[str] = Field(
        default_factory=list,
        description="PII fields that were removed"
    )
    fields_generalized: List[str] = Field(
        default_factory=list,
        description="Fields that were generalized"
    )
    fields_suppressed: List[str] = Field(
        default_factory=list,
        description="Fields that were suppressed"
    )
    
    # Quality metrics
    utility_score: float = Field(
        default=0.0,
        description="Data utility score after anonymization"
    )
    k_anonymity_level: Optional[int] = Field(
        default=None,
        description="K-anonymity level achieved"
    )
    epsilon_value: Optional[float] = Field(
        default=None,
        description="Differential privacy epsilon value"
    )
    
    # Compliance validation
    compliance_checks_passed: List[ComplianceStandard] = Field(
        default_factory=list,
        description="Compliance standards validated"
    )
    gdpr_article_26_compliant: bool = Field(
        default=False,
        description="GDPR Article 26 anonymization compliance"
    )
    hipaa_safe_harbor_compliant: bool = Field(
        default=False,
        description="HIPAA Safe Harbor rule compliance"
    )
    
    # Process metadata
    anonymization_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When anonymization was performed"
    )
    processing_duration_seconds: float = Field(
        default=0.0,
        description="Time taken for anonymization"
    )
    algorithm_version: str = Field(
        default="v1.0",
        description="Anonymization algorithm version"
    )
    
    # Auditing
    performed_by: str = Field(..., description="System/user that performed anonymization")
    audit_signature: str = Field(..., description="Cryptographic audit signature")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "original_patient_id": "hash_of_original_id_abc123",
                "anonymous_id": "anon_abc123def456",
                "anonymization_method": "pseudonymization",
                "additional_methods": ["generalization", "k_anonymity"],
                "pii_fields_removed": ["ssn", "full_name", "phone_number", "email"],
                "fields_generalized": ["age", "zipcode", "date_of_birth"],
                "utility_score": 0.92,
                "k_anonymity_level": 5,
                "compliance_checks_passed": ["hipaa", "gdpr", "soc2_type_ii"],
                "gdpr_article_26_compliant": True,
                "hipaa_safe_harbor_compliant": True,
                "processing_duration_seconds": 0.234,
                "performed_by": "ml_anonymization_engine",
                "audit_signature": "sha256_signature_here"
            }
        }
    }

class ComplianceValidationResult(BaseModel):
    """
    Results of compliance validation for anonymized data.
    """
    validation_id: str = Field(default_factory=lambda: str(uuid4()))
    profile_id: str = Field(..., description="Anonymized profile ID being validated")
    
    # Compliance test results
    hipaa_compliant: bool = Field(default=False)
    gdpr_compliant: bool = Field(default=False)
    soc2_compliant: bool = Field(default=False)
    fhir_compliant: bool = Field(default=False)
    
    # Detailed validation results
    pii_removal_validated: bool = Field(default=False, description="All PII successfully removed")
    re_identification_risk: float = Field(default=1.0, description="Risk of re-identification (0.0 = no risk)")
    utility_preservation: float = Field(default=0.0, description="Data utility preserved (0.0-1.0)")
    
    # Specific compliance details
    hipaa_safe_harbor_identifiers_removed: List[str] = Field(
        default_factory=list,
        description="HIPAA Safe Harbor identifiers that were removed"
    )
    gdpr_article_26_criteria_met: List[str] = Field(
        default_factory=list,
        description="GDPR Article 26 criteria satisfied"
    )
    
    # Validation metadata
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    validation_algorithm_version: str = Field(default="v1.0")
    overall_compliance_score: float = Field(default=0.0, description="Overall compliance score (0.0-1.0)")
    
    # Recommendations
    compliance_issues: List[str] = Field(
        default_factory=list,
        description="Identified compliance issues"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations for compliance improvement"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "profile_id": "profile_abc123",
                "hipaa_compliant": True,
                "gdpr_compliant": True,
                "soc2_compliant": True,
                "fhir_compliant": True,
                "pii_removal_validated": True,
                "re_identification_risk": 0.001,
                "utility_preservation": 0.92,
                "hipaa_safe_harbor_identifiers_removed": [
                    "names", "dates", "telephone_numbers", "ssn"
                ],
                "gdpr_article_26_criteria_met": [
                    "pseudonymization", "additional_safeguards", "separate_storage"
                ],
                "overall_compliance_score": 0.95,
                "compliance_issues": [],
                "recommendations": []
            }
        }
    }

class MLDatasetMetadata(BaseModel):
    """
    Metadata for ML training datasets created from anonymized profiles.
    """
    dataset_id: str = Field(default_factory=lambda: str(uuid4()))
    dataset_name: str = Field(..., description="Human-readable dataset name")
    
    # Dataset composition
    total_profiles: int = Field(..., description="Total number of anonymized profiles")
    date_range_start: datetime = Field(..., description="Earliest patient data timestamp")
    date_range_end: datetime = Field(..., description="Latest patient data timestamp")
    
    # Clinical characteristics
    age_group_distribution: Dict[AgeGroup, int] = Field(
        default_factory=dict,
        description="Distribution of age groups in dataset"
    )
    condition_categories: List[str] = Field(
        default_factory=list,
        description="Medical conditions represented in dataset"
    )
    
    # ML readiness
    embedding_model: str = Field(
        default="Bio_ClinicalBERT",
        description="Clinical BERT model used for embeddings"
    )
    vector_dimension: int = Field(default=768, description="Embedding vector dimension")
    
    # Quality metrics
    dataset_quality_score: float = Field(default=0.0, description="Overall dataset quality")
    anonymization_quality: float = Field(default=0.0, description="Anonymization quality score")
    clinical_utility: float = Field(default=0.0, description="Clinical utility preservation")
    
    # Compliance certification
    compliance_certified: bool = Field(default=False)
    certification_details: Dict[ComplianceStandard, bool] = Field(default_factory=dict)
    
    # Creation metadata
    created_timestamp: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="System/user that created dataset")
    anonymization_version: str = Field(default="v1.0")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "dataset_name": "winter_respiratory_predictions_2025",
                "total_profiles": 50000,
                "age_group_distribution": {
                    "reproductive_age": 15000,
                    "middle_age": 20000,
                    "older_adult": 15000
                },
                "condition_categories": ["respiratory_infections", "pneumonia", "allergic_reactions"],
                "dataset_quality_score": 0.94,
                "anonymization_quality": 0.97,
                "clinical_utility": 0.91,
                "compliance_certified": True,
                "certification_details": {
                    "hipaa": True,
                    "gdpr": True,
                    "soc2_type_ii": True
                }
            }
        }
    }