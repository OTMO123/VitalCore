"""
Privacy Computing API Router for Healthcare Platform V2.0

RESTful API endpoints for advanced privacy-preserving computation including
homomorphic encryption, secure multiparty computation, and differential privacy.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Dict, List, Any, Optional
import torch
import numpy as np
from datetime import datetime, timedelta

from .privacy_engine import AdvancedPrivacyEngine
from .schemas import (
    PrivacyConfig, HEContext, EncryptedData, EncryptedResult,
    SecretShare, MPCComputation, DifferentialPrivacyParams,
    PrivacyValidationResult, PrivacyLevel
)
from ..auth.service import get_current_user_id, require_role
from ...core.audit_logger import audit_log
from ...core.config import get_settings

router = APIRouter(prefix="/api/v1/privacy", tags=["Privacy Computing"])
settings = get_settings()

# Initialize privacy engine
privacy_config = PrivacyConfig()
privacy_engine = AdvancedPrivacyEngine(privacy_config)

@router.post("/differential-privacy/global", response_model=Dict[str, Any])
@audit_log("apply_global_differential_privacy")
async def apply_global_differential_privacy(
    data: List[float],
    epsilon: float,
    delta: Optional[float] = 1e-5,
    current_user: str = Depends(require_role("researcher"))
) -> Dict[str, Any]:
    """
    Apply global differential privacy to dataset.
    
    Args:
        data: Input dataset as list of floats
        epsilon: Privacy budget parameter (0.001 to 10.0)
        delta: Privacy parameter (default 1e-5)
        
    Returns:
        Differentially private dataset with metadata
    """
    try:
        # Validate parameters
        if not 0.001 <= epsilon <= 10.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Epsilon must be between 0.001 and 10.0"
            )
        
        if not 1e-10 <= delta <= 1e-3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Delta must be between 1e-10 and 1e-3"
            )
        
        # Convert to tensor
        dataset = torch.tensor(data, dtype=torch.float32)
        
        # Apply differential privacy
        private_dataset = await privacy_engine.apply_global_differential_privacy(
            dataset, epsilon
        )
        
        # Calculate utility metrics
        accuracy_loss = await privacy_engine._calculate_accuracy_loss(dataset, private_dataset)
        utility_score = await privacy_engine._calculate_utility_score(dataset, private_dataset)
        
        return {
            "private_data": private_dataset.tolist(),
            "privacy_parameters": {
                "epsilon": epsilon,
                "delta": delta,
                "mechanism": "gaussian"
            },
            "utility_metrics": {
                "accuracy_loss_percentage": accuracy_loss,
                "utility_score": utility_score
            },
            "metadata": {
                "original_size": len(data),
                "processing_timestamp": datetime.utcnow().isoformat(),
                "user_id": current_user
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply differential privacy: {str(e)}"
        )

@router.post("/differential-privacy/local", response_model=Dict[str, Any])
@audit_log("apply_local_differential_privacy")
async def apply_local_differential_privacy(
    record: List[float],
    epsilon: float,
    current_user: str = Depends(require_role("researcher"))
) -> Dict[str, Any]:
    """
    Apply local differential privacy to individual record.
    
    Args:
        record: Individual data record
        epsilon: Local privacy budget
        
    Returns:
        Locally differentially private record
    """
    try:
        # Convert to tensor
        record_tensor = torch.tensor(record, dtype=torch.float32)
        
        # Apply local differential privacy
        private_record = await privacy_engine.implement_local_differential_privacy(
            record_tensor, epsilon
        )
        
        return {
            "private_record": private_record.tolist(),
            "privacy_parameters": {
                "epsilon": epsilon,
                "mechanism": "laplace",
                "privacy_type": "local"
            },
            "metadata": {
                "original_length": len(record),
                "processing_timestamp": datetime.utcnow().isoformat(),
                "user_id": current_user
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply local differential privacy: {str(e)}"
        )

@router.post("/homomorphic-encryption/initialize", response_model=HEContext)
@audit_log("initialize_homomorphic_encryption")
async def initialize_homomorphic_encryption(
    key_size: int = 8192,
    scheme: str = "ckks",
    current_user: str = Depends(require_role("admin"))
) -> HEContext:
    """
    Initialize homomorphic encryption context.
    
    Args:
        key_size: Polynomial modulus degree (1024, 2048, 4096, 8192, 16384)
        scheme: Encryption scheme ("ckks", "bfv", "bgv")
        
    Returns:
        Homomorphic encryption context
    """
    try:
        he_context = await privacy_engine.initialize_homomorphic_encryption(
            key_size, scheme
        )
        
        return he_context
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize homomorphic encryption: {str(e)}"
        )

@router.post("/homomorphic-encryption/encrypt", response_model=EncryptedData)
@audit_log("encrypt_patient_data")
async def encrypt_patient_data(
    data: List[float],
    context_id: str,
    current_user: str = Depends(require_role("doctor"))
) -> EncryptedData:
    """
    Encrypt patient data using homomorphic encryption.
    
    Args:
        data: Patient data to encrypt
        context_id: HE context identifier
        
    Returns:
        Encrypted data container
    """
    try:
        # Convert to tensor
        data_tensor = torch.tensor(data, dtype=torch.float32)
        
        # Encrypt data
        encrypted_data = await privacy_engine.encrypt_patient_data(
            data_tensor, context_id
        )
        
        return encrypted_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to encrypt patient data: {str(e)}"
        )

@router.post("/homomorphic-encryption/compute", response_model=EncryptedResult)
@audit_log("perform_encrypted_computation")
async def perform_encrypted_computation(
    encrypted_data_id: str,
    operation: str,
    current_user: str = Depends(require_role("researcher"))
) -> EncryptedResult:
    """
    Perform computation on encrypted data without decryption.
    
    Args:
        encrypted_data_id: ID of encrypted data
        operation: Operation to perform ("square", "add_constant", "multiply_constant", "polynomial")
        
    Returns:
        Encrypted computation result
    """
    try:
        # Get encrypted data from cache
        if encrypted_data_id not in privacy_engine.encrypted_data_cache:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Encrypted data not found"
            )
        
        encrypted_data = privacy_engine.encrypted_data_cache[encrypted_data_id]
        
        # Perform computation
        encrypted_result = await privacy_engine.perform_encrypted_computation(
            encrypted_data, operation
        )
        
        return encrypted_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform encrypted computation: {str(e)}"
        )

@router.post("/secure-multiparty/initialize", response_model=MPCComputation)
@audit_log("initialize_mpc_protocol")
async def initialize_mpc_protocol(
    parties: List[str],
    threshold: int,
    current_user: str = Depends(require_role("admin"))
) -> MPCComputation:
    """
    Initialize secure multiparty computation protocol.
    
    Args:
        parties: List of participating party identifiers
        threshold: Minimum parties needed for reconstruction
        
    Returns:
        MPC computation context
    """
    try:
        mpc_computation = await privacy_engine.initialize_mpc_protocol(
            parties, threshold
        )
        
        return mpc_computation
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize MPC protocol: {str(e)}"
        )

@router.post("/secure-multiparty/secret-share", response_model=List[SecretShare])
@audit_log("create_secret_shares")
async def create_secret_shares(
    data: List[float],
    num_parties: int,
    current_user: str = Depends(require_role("researcher"))
) -> List[SecretShare]:
    """
    Create secret shares of data using Shamir's secret sharing.
    
    Args:
        data: Data to be secret shared
        num_parties: Number of parties to create shares for
        
    Returns:
        List of secret shares
    """
    try:
        # Convert to tensor
        data_tensor = torch.tensor(data, dtype=torch.float32)
        
        # Create secret shares
        secret_shares = await privacy_engine.secret_share_data(
            data_tensor, num_parties
        )
        
        return secret_shares
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create secret shares: {str(e)}"
        )

@router.post("/secure-multiparty/aggregate", response_model=Dict[str, Any])
@audit_log("perform_secure_aggregation")
async def perform_secure_aggregation(
    shares_data: List[Dict[str, Any]],
    current_user: str = Depends(require_role("researcher"))
) -> Dict[str, Any]:
    """
    Perform secure aggregation of secret shares.
    
    Args:
        shares_data: List of secret share dictionaries
        
    Returns:
        Aggregated result
    """
    try:
        # Convert dictionaries to SecretShare objects
        secret_shares = [SecretShare(**share_data) for share_data in shares_data]
        
        # Perform secure aggregation
        aggregated_result = await privacy_engine.perform_secure_aggregation(
            secret_shares
        )
        
        return {
            "aggregated_result": aggregated_result.tolist(),
            "metadata": {
                "input_shares": len(secret_shares),
                "aggregation_timestamp": datetime.utcnow().isoformat(),
                "user_id": current_user
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform secure aggregation: {str(e)}"
        )

@router.post("/privacy/validate", response_model=PrivacyValidationResult)
@audit_log("validate_privacy_guarantees")
async def validate_privacy_guarantees(
    operation_config: Dict[str, Any],
    current_user: str = Depends(require_role("admin"))
) -> PrivacyValidationResult:
    """
    Validate that privacy guarantees are met for given operation.
    
    Args:
        operation_config: Configuration of privacy operation
        
    Returns:
        Privacy validation result
    """
    try:
        validation_result = await privacy_engine.validate_privacy_guarantees(
            operation_config
        )
        
        return validation_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate privacy guarantees: {str(e)}"
        )

@router.get("/privacy/report", response_model=Dict[str, Any])
@audit_log("generate_privacy_report")
async def generate_privacy_report(
    days_back: int = 30,
    current_user: str = Depends(require_role("admin"))
) -> Dict[str, Any]:
    """
    Generate comprehensive privacy operations report.
    
    Args:
        days_back: Number of days to include in report
        
    Returns:
        Privacy report with metrics and compliance status
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        privacy_report = await privacy_engine.generate_privacy_report(
            start_date, end_date
        )
        
        return privacy_report
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate privacy report: {str(e)}"
        )

@router.post("/privacy/optimize-utility", response_model=Dict[str, float])
@audit_log("optimize_privacy_utility_tradeoff")
async def optimize_privacy_utility_tradeoff(
    data: List[float],
    utility_metric: str = "accuracy",
    current_user: str = Depends(require_role("researcher"))
) -> Dict[str, float]:
    """
    Optimize privacy-utility tradeoff for given dataset.
    
    Args:
        data: Input dataset
        utility_metric: Utility metric to optimize ("accuracy", "f1", "auc")
        
    Returns:
        Optimal privacy parameters
    """
    try:
        # Convert to tensor
        dataset = torch.tensor(data, dtype=torch.float32)
        
        # Optimize privacy-utility tradeoff
        optimal_params = await privacy_engine.optimize_privacy_utility_tradeoff(
            dataset, utility_metric
        )
        
        return optimal_params
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize privacy-utility tradeoff: {str(e)}"
        )

@router.get("/privacy/contexts", response_model=List[HEContext])
async def list_he_contexts(
    current_user: str = Depends(require_role("admin"))
) -> List[HEContext]:
    """
    List all available homomorphic encryption contexts.
    
    Returns:
        List of HE contexts
    """
    try:
        return list(privacy_engine.he_contexts.values())
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list HE contexts: {str(e)}"
        )

@router.get("/privacy/config", response_model=PrivacyConfig)
async def get_privacy_config(
    current_user: str = Depends(require_role("admin"))
) -> PrivacyConfig:
    """
    Get current privacy engine configuration.
    
    Returns:
        Privacy configuration
    """
    return privacy_engine.config

@router.put("/privacy/config", response_model=Dict[str, str])
@audit_log("update_privacy_config")
async def update_privacy_config(
    config: PrivacyConfig,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(require_role("admin"))
) -> Dict[str, str]:
    """
    Update privacy engine configuration.
    
    Args:
        config: New privacy configuration
        
    Returns:
        Update status
    """
    try:
        # Validate configuration
        if config.epsilon <= 0 or config.epsilon > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid epsilon value"
            )
        
        # Update configuration
        privacy_engine.config = config
        
        # Schedule reinitialization in background
        background_tasks.add_task(
            _reinitialize_privacy_engine, config
        )
        
        return {
            "status": "success",
            "message": "Privacy configuration updated",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update privacy configuration: {str(e)}"
        )

async def _reinitialize_privacy_engine(config: PrivacyConfig) -> None:
    """Reinitialize privacy engine with new configuration."""
    try:
        global privacy_engine
        privacy_engine = AdvancedPrivacyEngine(config)
        
    except Exception as e:
        logger.error(f"Failed to reinitialize privacy engine: {str(e)}")

# Health check endpoint
@router.get("/health", response_model=Dict[str, Any])
async def privacy_health_check() -> Dict[str, Any]:
    """
    Privacy computing service health check.
    
    Returns:
        Service health status
    """
    try:
        return {
            "status": "healthy",
            "privacy_level": privacy_engine.config.privacy_level.value,
            "active_contexts": len(privacy_engine.he_contexts),
            "active_computations": len(privacy_engine.active_computations),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }