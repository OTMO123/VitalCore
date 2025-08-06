"""
Data Anonymization Router for ML/AI Healthcare Platform

API endpoints for ML-ready data anonymization, compliance validation,
and dataset preparation for healthcare prediction algorithms.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog

from app.core.security import verify_token, get_current_user_id
from app.core.database_unified import get_db
from app.core.exceptions import ValidationError, UnauthorizedAccess

from .ml_anonymizer import MLAnonymizationEngine
from .schemas import (
    AnonymizedMLProfile, ComplianceValidationResult, MLDatasetMetadata,
    AnonymizationAuditTrail
)

logger = structlog.get_logger(__name__)
security = HTTPBearer()

# Create router with ML anonymization prefix
router = APIRouter(
    prefix="/api/v1/ml-anonymization",
    tags=["ML Data Anonymization"],
    dependencies=[Depends(security)]
)

# Initialize ML anonymization engine
ml_anonymizer = MLAnonymizationEngine()

@router.post(
    "/anonymize-patient",
    response_model=AnonymizedMLProfile,
    summary="Create ML-ready anonymized patient profile",
    description="Anonymize patient data for ML/AI disease prediction while maintaining HIPAA/GDPR compliance"
)
async def anonymize_patient_for_ml(
    patient_data: Dict[str, Any],
    clinical_text: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Create ML-ready anonymized patient profile.
    
    This endpoint transforms patient data into an anonymized profile
    optimized for Clinical BERT embeddings and disease prediction algorithms.
    """
    try:
        # User is authenticated via get_current_user_id
        # Additional user validation can be added here if needed
        
        # Create ML anonymized profile
        ml_profile = await ml_anonymizer.create_ml_profile(
            patient_data=patient_data,
            clinical_text=clinical_text
        )
        
        logger.info(
            "ML patient anonymization completed",
            user_id=current_user_id,
            profile_id=ml_profile.profile_id,
            prediction_ready=ml_profile.prediction_ready
        )
        
        return ml_profile
        
    except ValidationError as e:
        logger.error(
            "ML anonymization validation failed",
            user_id=current_user_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Anonymization validation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(
            "ML anonymization failed",
            user_id=current_user_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create ML anonymized profile"
        )

@router.post(
    "/batch-anonymize",
    response_model=List[AnonymizedMLProfile],
    summary="Batch anonymize patients for ML training",
    description="Efficiently anonymize multiple patients for ML dataset creation"
)
async def batch_anonymize_patients(
    patient_list: List[Dict[str, Any]],
    clinical_texts: Optional[List[str]] = None,
    current_user_id: str = Depends(get_current_user_id),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db=Depends(get_db)
):
    """
    Batch anonymize multiple patients for ML training datasets.
    
    Processes multiple patient records efficiently while maintaining
    the same anonymization quality as single-patient processing.
    """
    try:
        if len(patient_list) > 1000:  # Reasonable batch size limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size too large. Maximum 1000 patients per batch."
            )
        
        if clinical_texts and len(clinical_texts) != len(patient_list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Clinical texts list must match patient list length"
            )
        
        # Process batch anonymization
        ml_profiles = await ml_anonymizer.batch_create_ml_profiles(
            patient_list=patient_list,
            clinical_texts=clinical_texts
        )
        
        logger.info(
            "Batch ML anonymization completed",
            user_id=current_user_id,
            total_patients=len(patient_list),
            successful_profiles=len(ml_profiles),
            prediction_ready_count=sum(
                1 for profile in ml_profiles if profile.prediction_ready
            )
        )
        
        return ml_profiles
        
    except Exception as e:
        logger.error(
            "Batch ML anonymization failed",
            user_id=current_user_id,
            patient_count=len(patient_list),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to batch anonymize patients"
        )

@router.post(
    "/validate-compliance",
    response_model=ComplianceValidationResult,
    summary="Validate anonymization compliance",
    description="Comprehensive compliance validation against HIPAA, GDPR, and SOC2 standards"
)
async def validate_anonymization_compliance(
    profile: AnonymizedMLProfile,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Validate anonymized profile compliance with healthcare regulations.
    
    Performs comprehensive validation against HIPAA Safe Harbor,
    GDPR Article 26, and SOC2 Type II requirements.
    """
    try:
        # Perform comprehensive compliance validation
        compliance_result = await ml_anonymizer.compliance_validator.comprehensive_compliance_check(
            profile
        )
        
        logger.info(
            "Compliance validation completed",
            user_id=current_user_id,
            profile_id=profile.profile_id,
            overall_compliant=compliance_result.overall_compliance_score >= 0.9,
            compliance_score=compliance_result.overall_compliance_score
        )
        
        return compliance_result
        
    except Exception as e:
        logger.error(
            "Compliance validation failed",
            user_id=current_user_id,
            profile_id=profile.profile_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate compliance"
        )

@router.post(
    "/export-ml-dataset",
    response_model=Dict[str, str],
    summary="Export ML training dataset",
    description="Export anonymized profiles as ML training dataset with compliance certification"
)
async def export_ml_training_dataset(
    profiles: List[AnonymizedMLProfile],
    dataset_name: str,
    current_user_id: str = Depends(get_current_user_id),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db=Depends(get_db)
):
    """
    Export anonymized profiles for ML training.
    
    Creates a compliance-certified ML training dataset from
    validated anonymized patient profiles.
    """
    try:
        if not dataset_name or len(dataset_name) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset name must be at least 3 characters long"
            )
        
        if not profiles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No profiles provided for dataset export"
            )
        
        # Export dataset
        dataset_id = await ml_anonymizer.export_for_ml_training(
            profiles=profiles,
            dataset_name=dataset_name
        )
        
        logger.info(
            "ML training dataset exported",
            user_id=current_user_id,
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            profile_count=len(profiles)
        )
        
        return {
            "dataset_id": dataset_id,
            "dataset_name": dataset_name,
            "status": "exported",
            "profile_count": str(len(profiles))
        }
        
    except Exception as e:
        logger.error(
            "ML dataset export failed",
            user_id=current_user_id,
            dataset_name=dataset_name,
            profile_count=len(profiles),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export ML training dataset"
        )

@router.post(
    "/apply-k-anonymity",
    response_model=List[AnonymizedMLProfile],
    summary="Apply k-anonymity to ML profiles",
    description="Apply k-anonymity privacy technique to anonymized ML profiles"
)
async def apply_k_anonymity_to_profiles(
    profiles: List[AnonymizedMLProfile],
    k: int,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Apply k-anonymity to ML profiles.
    
    Ensures that each profile is indistinguishable from at least k-1
    other profiles in the dataset for enhanced privacy protection.
    """
    try:
        if k < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="k value must be at least 2 for k-anonymity"
            )
        
        if k > len(profiles):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="k value cannot be larger than the number of profiles"
            )
        
        # Apply k-anonymity
        k_anonymous_profiles = await ml_anonymizer.apply_k_anonymity_ml(
            profiles=profiles,
            k=k
        )
        
        logger.info(
            "K-anonymity applied to ML profiles",
            user_id=current_user_id,
            profile_count=len(profiles),
            k_value=k
        )
        
        return k_anonymous_profiles
        
    except Exception as e:
        logger.error(
            "K-anonymity application failed",
            user_id=current_user_id,
            profile_count=len(profiles),
            k_value=k,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply k-anonymity"
        )

@router.post(
    "/apply-differential-privacy",
    response_model=List[AnonymizedMLProfile],
    summary="Apply differential privacy to ML profiles",
    description="Apply differential privacy noise to anonymized ML profiles"
)
async def apply_differential_privacy_to_profiles(
    profiles: List[AnonymizedMLProfile],
    epsilon: float,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Apply differential privacy to ML profiles.
    
    Adds carefully calibrated noise to profiles to provide
    formal privacy guarantees while preserving data utility.
    """
    try:
        if epsilon <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Epsilon must be positive for differential privacy"
            )
        
        if epsilon > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Epsilon too large (max 10) - would provide insufficient privacy"
            )
        
        # Apply differential privacy
        dp_profiles = await ml_anonymizer.apply_differential_privacy_ml(
            profiles=profiles,
            epsilon=epsilon
        )
        
        logger.info(
            "Differential privacy applied to ML profiles",
            user_id=current_user_id,
            profile_count=len(profiles),
            epsilon=epsilon
        )
        
        return dp_profiles
        
    except Exception as e:
        logger.error(
            "Differential privacy application failed",
            user_id=current_user_id,
            profile_count=len(profiles),
            epsilon=epsilon,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply differential privacy"
        )

@router.get(
    "/utility-metrics/{profile_id}",
    response_model=Dict[str, float],
    summary="Get data utility metrics",
    description="Calculate utility preservation metrics for anonymized profile"
)
async def get_utility_metrics(
    profile_id: str,
    original_data: Dict[str, Any],
    anonymized_profile: AnonymizedMLProfile,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Calculate data utility metrics for anonymized profile.
    
    Compares original patient data with anonymized profile to
    measure how much clinical utility has been preserved.
    """
    try:
        # Calculate utility metrics
        utility_metrics = await ml_anonymizer.generate_utility_metrics(
            original=original_data,
            anonymized=anonymized_profile
        )
        
        logger.info(
            "Utility metrics calculated",
            user_id=current_user_id,
            profile_id=profile_id,
            overall_utility=utility_metrics["overall_utility"]
        )
        
        return utility_metrics
        
    except Exception as e:
        logger.error(
            "Utility metrics calculation failed",
            user_id=current_user_id,
            profile_id=profile_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate utility metrics"
        )

@router.get(
    "/re-identification-risk/{profile_id}",
    response_model=Dict[str, float],
    summary="Calculate re-identification risk",
    description="Assess re-identification risk for anonymized profile"
)
async def calculate_reidentification_risk(
    profile_id: str,
    profile: AnonymizedMLProfile,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Calculate re-identification risk for anonymized profile.
    
    Assesses the risk that an anonymized profile could be
    linked back to the original patient identity.
    """
    try:
        # Calculate re-identification risk
        risk_score = await ml_anonymizer.calculate_re_identification_risk(profile)
        
        logger.info(
            "Re-identification risk calculated",
            user_id=current_user_id,
            profile_id=profile_id,
            risk_score=risk_score
        )
        
        return {
            "profile_id": profile_id,
            "re_identification_risk": risk_score,
            "risk_level": (
                "low" if risk_score < 0.1 else
                "medium" if risk_score < 0.3 else
                "high"
            ),
            "calculated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(
            "Re-identification risk calculation failed",
            user_id=current_user_id,
            profile_id=profile_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate re-identification risk"
        )

@router.get(
    "/health",
    summary="ML Anonymization service health check",
    description="Check health status of ML anonymization components"
)
async def health_check():
    """
    Health check for ML anonymization service.
    
    Verifies that all ML anonymization components are
    functioning correctly and ready for processing.
    """
    try:
        # Test basic ML anonymizer functionality
        test_patient = {
            "id": "test_patient_123",
            "age": 30,
            "gender": "female",
            "medical_history": ["asthma"],
            "location": "Boston, MA"
        }
        
        # Create test ML profile
        test_profile = await ml_anonymizer.create_ml_profile(test_patient)
        
        health_status = {
            "status": "healthy",
            "ml_anonymizer": "operational",
            "clinical_extractor": "operational",
            "pseudonym_generator": "operational",
            "compliance_validator": "operational",
            "test_profile_created": test_profile.prediction_ready,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return health_status
        
    except Exception as e:
        logger.error("ML anonymization health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }