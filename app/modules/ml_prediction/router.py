"""
ML Prediction Router for Healthcare Platform

FastAPI endpoints for Clinical BERT embeddings, similarity search,
and ML prediction services with HIPAA compliance.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog

from app.core.security import verify_token, get_current_user_id
from app.core.database_unified import get_db
from app.core.exceptions import ValidationError, UnauthorizedAccess

from .clinical_bert import ClinicalBERTService, ClinicalBERTConfig
from app.modules.data_anonymization.schemas import AnonymizedMLProfile

logger = structlog.get_logger(__name__)
security = HTTPBearer()

# Create router with ML prediction prefix
router = APIRouter(
    prefix="/api/v1/ml-prediction",
    tags=["ML Prediction Services"],
    dependencies=[Depends(security)]
)

# Initialize Clinical BERT service
clinical_bert_service = ClinicalBERTService()

@router.post(
    "/clinical-bert/embed",
    summary="Generate Clinical BERT embedding",
    description="Generate Bio_ClinicalBERT embedding for medical text with anonymization validation"
)
async def generate_clinical_embedding(
    clinical_text: str,
    anonymized_profile: Optional[AnonymizedMLProfile] = None,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Generate Clinical BERT embedding for medical text.
    
    This endpoint creates 768-dimensional embeddings using Bio_ClinicalBERT
    specifically trained on clinical text for disease prediction algorithms.
    """
    try:
        # User is authenticated, proceed with ML operations
        # Additional user validation can be added here if needed
        
        # Validate input
        if not clinical_text or len(clinical_text.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Clinical text must be at least 10 characters"
            )
        
        # Generate Clinical BERT embedding
        embedding_result = await clinical_bert_service.generate_clinical_embedding(
            clinical_text=clinical_text,
            profile=anonymized_profile
        )
        
        if not embedding_result:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to generate clinical embedding"
            )
        
        if not embedding_result.anonymization_validated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Clinical text failed anonymization validation"
            )
        
        logger.info(
            "Clinical BERT embedding generated successfully",
            user_id=current_user_id,
            embedding_dimension=embedding_result.embedding_dimension,
            confidence_score=embedding_result.confidence_score,
            clinical_categories=embedding_result.clinical_categories
        )
        
        return {
            "text_hash": embedding_result.text_hash,
            "embedding_vector": embedding_result.embedding_vector,
            "embedding_dimension": embedding_result.embedding_dimension,
            "model_version": embedding_result.model_version,
            "confidence_score": embedding_result.confidence_score,
            "clinical_categories": embedding_result.clinical_categories,
            "anonymization_validated": embedding_result.anonymization_validated,
            "processing_timestamp": embedding_result.processing_timestamp.isoformat()
        }
        
    except ValidationError as e:
        logger.error(
            "Clinical embedding validation failed",
            user_id=current_user_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Embedding validation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(
            "Clinical embedding generation failed",
            user_id=current_user_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate clinical embedding"
        )

@router.post(
    "/clinical-bert/batch-embed",
    summary="Batch generate Clinical BERT embeddings",
    description="Generate Clinical BERT embeddings for multiple texts efficiently"
)
async def batch_generate_clinical_embeddings(
    clinical_texts: List[str],
    anonymized_profiles: Optional[List[AnonymizedMLProfile]] = None,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Generate Clinical BERT embeddings for multiple texts efficiently.
    
    Processes multiple clinical texts in batches for optimal performance
    while maintaining the same quality and compliance standards.
    """
    try:
        if len(clinical_texts) > 100:  # Reasonable batch size limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size too large. Maximum 100 texts per batch."
            )
        
        if anonymized_profiles and len(anonymized_profiles) != len(clinical_texts):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profiles list must match clinical texts list length"
            )
        
        # Validate all texts
        for i, text in enumerate(clinical_texts):
            if not text or len(text.strip()) < 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Clinical text at index {i} must be at least 10 characters"
                )
        
        # Generate batch embeddings
        embedding_results = await clinical_bert_service.batch_generate_embeddings(
            clinical_texts=clinical_texts,
            profiles=anonymized_profiles
        )
        
        # Process results
        successful_embeddings = []
        failed_indices = []
        
        for i, result in enumerate(embedding_results):
            if result and result.anonymization_validated:
                successful_embeddings.append({
                    "index": i,
                    "text_hash": result.text_hash,
                    "embedding_vector": result.embedding_vector,
                    "embedding_dimension": result.embedding_dimension,
                    "confidence_score": result.confidence_score,
                    "clinical_categories": result.clinical_categories,
                    "processing_timestamp": result.processing_timestamp.isoformat()
                })
            else:
                failed_indices.append(i)
        
        logger.info(
            "Batch clinical embedding generation completed",
            user_id=current_user_id,
            total_texts=len(clinical_texts),
            successful_embeddings=len(successful_embeddings),
            failed_embeddings=len(failed_indices)
        )
        
        return {
            "total_texts": len(clinical_texts),
            "successful_embeddings": successful_embeddings,
            "failed_indices": failed_indices,
            "success_rate": len(successful_embeddings) / len(clinical_texts)
        }
        
    except Exception as e:
        logger.error(
            "Batch clinical embedding generation failed",
            user_id=current_user_id,
            text_count=len(clinical_texts),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate batch clinical embeddings"
        )

@router.post(
    "/similarity/calculate",
    summary="Calculate embedding similarity",
    description="Calculate cosine similarity between two Clinical BERT embeddings"
)
async def calculate_embedding_similarity(
    embedding1: List[float],
    embedding2: List[float],
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Calculate cosine similarity between two Clinical BERT embeddings.
    
    Used for disease prediction algorithms and patient similarity analysis
    for clinical decision support systems.
    """
    try:
        # Validate embeddings
        if not embedding1 or not embedding2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both embeddings must be provided"
            )
        
        if len(embedding1) != len(embedding2):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Embeddings must have the same dimension"
            )
        
        if len(embedding1) != 768:  # Bio_ClinicalBERT dimension
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Embeddings must be 768-dimensional Bio_ClinicalBERT vectors"
            )
        
        # Calculate similarity
        similarity_score = await clinical_bert_service.get_embedding_similarity(
            embedding1, embedding2
        )
        
        logger.info(
            "Embedding similarity calculated",
            user_id=current_user_id,
            similarity_score=similarity_score,
            embedding_dimension=len(embedding1)
        )
        
        return {
            "similarity_score": similarity_score,
            "embedding_dimension": len(embedding1),
            "similarity_level": (
                "high" if similarity_score >= 0.8 else
                "medium" if similarity_score >= 0.6 else
                "low"
            ),
            "calculated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(
            "Embedding similarity calculation failed",
            user_id=current_user_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate embedding similarity"
        )

@router.post(
    "/profile/update-with-embedding",
    response_model=AnonymizedMLProfile,
    summary="Update ML profile with Clinical BERT embedding",
    description="Update anonymized ML profile with Clinical BERT embedding from clinical text"
)
async def update_profile_with_embedding(
    profile: AnonymizedMLProfile,
    clinical_text: str,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Update anonymized ML profile with Clinical BERT embedding.
    
    Enhances ML profiles with Clinical BERT embeddings for improved
    disease prediction accuracy while maintaining HIPAA compliance.
    """
    try:
        # Validate profile compliance
        if not profile.compliance_validated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile must be compliance validated before embedding update"
            )
        
        # Update profile with embedding
        updated_profile = await clinical_bert_service.update_ml_profile_with_embedding(
            profile=profile,
            clinical_text=clinical_text
        )
        
        logger.info(
            "ML profile updated with Clinical BERT embedding",
            user_id=current_user_id,
            profile_id=updated_profile.profile_id,
            embedding_added=updated_profile.clinical_text_embedding is not None,
            prediction_ready=updated_profile.prediction_ready
        )
        
        return updated_profile
        
    except Exception as e:
        logger.error(
            "Failed to update profile with embedding",
            user_id=current_user_id,
            profile_id=profile.profile_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile with Clinical BERT embedding"
        )

@router.get(
    "/clinical-bert/health",
    summary="Clinical BERT service health check",
    description="Check health status of Clinical BERT service and model"
)
async def clinical_bert_health_check():
    """
    Health check for Clinical BERT service.
    
    Verifies that Bio_ClinicalBERT model is loaded and functioning
    correctly for embedding generation.
    """
    try:
        health_status = await clinical_bert_service.get_service_health()
        
        # Determine HTTP status based on health
        if health_status["status"] == "healthy":
            status_code = status.HTTP_200_OK
        elif health_status["status"] == "unhealthy":
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        return health_status
        
    except Exception as e:
        logger.error("Clinical BERT health check failed", error=str(e))
        return {
            "service": "clinical_bert",
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.post(
    "/clinical-bert/initialize",
    summary="Initialize Clinical BERT model",
    description="Manually initialize Bio_ClinicalBERT model for embedding generation"
)
async def initialize_clinical_bert_model(
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Manually initialize Bio_ClinicalBERT model.
    
    Useful for pre-loading the model before processing large batches
    of clinical text for embedding generation.
    """
    try:
        # User is authenticated, proceed with model initialization
        # Additional user validation can be added here if needed
        
        # Initialize model
        initialization_successful = await clinical_bert_service.initialize_model()
        
        if not initialization_successful:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize Clinical BERT model"
            )
        
        logger.info(
            "Clinical BERT model initialized manually",
            user_id=current_user_id,
            model_name=clinical_bert_service.config.model_name
        )
        
        return {
            "status": "initialized",
            "model_name": clinical_bert_service.config.model_name,
            "device": str(clinical_bert_service.device),
            "initialized_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(
            "Clinical BERT model initialization failed",
            user_id=current_user_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize Clinical BERT model"
        )