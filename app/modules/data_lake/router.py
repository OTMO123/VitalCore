"""
Data Lake Router for Healthcare ML Platform

FastAPI endpoints for MinIO data lake operations with ML dataset management,
HIPAA-compliant storage, and vector database synchronization.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File
from fastapi.security import HTTPBearer
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
import json

from app.core.security import verify_token, get_current_user_id
from app.core.database_unified import get_db
from app.core.exceptions import ValidationError, UnauthorizedAccess

from .minio_pipeline import MLDataLakePipeline, DataLakeConfig
from app.modules.data_anonymization.schemas import AnonymizedMLProfile, MLDatasetMetadata

logger = structlog.get_logger(__name__)
security = HTTPBearer()

# Create router with data lake prefix
router = APIRouter(
    prefix="/api/v1/data-lake",
    tags=["ML Data Lake Operations"],
    dependencies=[Depends(security)]
)

# Initialize ML data lake pipeline
data_lake = MLDataLakePipeline()

@router.post(
    "/initialize",
    summary="Initialize MinIO data lake",
    description="Initialize MinIO connection and create healthcare buckets"
)
async def initialize_data_lake(
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Initialize MinIO data lake with healthcare-specific buckets.
    
    Sets up HIPAA-compliant object storage for ML training datasets,
    vector embeddings, and audit logs with proper encryption and lifecycle policies.
    """
    try:
        # Initialize MinIO client
        await data_lake.initialize_minio_client()
        
        # Create healthcare buckets
        bucket_results = await data_lake.create_healthcare_buckets()
        
        # Validate security configuration
        security_validations = {}
        for bucket_name in data_lake.config.buckets.values():
            if bucket_results.get(bucket_name, False):
                security_validations[bucket_name] = await data_lake.validate_bucket_security(bucket_name)
        
        successful_buckets = sum(bucket_results.values())
        total_buckets = len(data_lake.config.buckets)
        
        logger.info(
            "Data lake initialized successfully",
            user_id=current_user_id,
            buckets_created=successful_buckets,
            total_buckets=total_buckets,
            encryption_enabled=data_lake.config.encryption_enabled
        )
        
        return {
            "status": "initialized",
            "buckets_created": successful_buckets,
            "total_buckets": total_buckets,
            "bucket_results": bucket_results,
            "security_validations": security_validations,
            "encryption_enabled": data_lake.config.encryption_enabled,
            "initialized_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(
            "Data lake initialization failed",
            user_id=current_user_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize data lake"
        )

@router.post(
    "/export-training-dataset",
    summary="Export ML training dataset",
    description="Export anonymized profiles as ML training dataset"
)
async def export_training_dataset(
    profiles: List[AnonymizedMLProfile],
    dataset_name: str,
    current_user_id: str = Depends(get_current_user_id),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db=Depends(get_db)
):
    """
    Export anonymized patient profiles as ML training dataset.
    
    Creates Parquet files with compliance-validated anonymized profiles
    optimized for ML training with proper data lineage and audit trails.
    """
    try:
        if not profiles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No profiles provided for export"
            )
        
        if not dataset_name or len(dataset_name) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset name must be at least 3 characters long"
            )
        
        if len(profiles) > 10000:  # Reasonable export limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Export size too large. Maximum 10,000 profiles per export."
            )
        
        # Validate all profiles are prediction-ready and compliant
        invalid_profiles = []
        for i, profile in enumerate(profiles):
            if not profile.prediction_ready:
                invalid_profiles.append(f"Profile {i}: not prediction ready")
            elif not profile.compliance_validated:
                invalid_profiles.append(f"Profile {i}: compliance not validated")
        
        if invalid_profiles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid profiles: {'; '.join(invalid_profiles[:5])}"
            )
        
        # Export dataset
        start_time = datetime.utcnow()
        s3_key = await data_lake.export_anonymized_profiles_for_training(
            profiles=profiles,
            dataset_name=dataset_name
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(
            "Training dataset exported successfully",
            user_id=current_user_id,
            dataset_name=dataset_name,
            profiles_exported=len(profiles),
            s3_key=s3_key,
            processing_time_seconds=processing_time
        )
        
        return {
            "status": "exported",
            "dataset_name": dataset_name,
            "s3_key": s3_key,
            "profiles_exported": len(profiles),
            "processing_time_seconds": processing_time,
            "exported_at": datetime.utcnow().isoformat()
        }
        
    except ValidationError as e:
        logger.error(
            "Dataset export validation failed",
            user_id=current_user_id,
            dataset_name=dataset_name,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export validation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(
            "Dataset export failed",
            user_id=current_user_id,
            dataset_name=dataset_name,
            profiles_count=len(profiles),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export training dataset"
        )

@router.post(
    "/create-ml-dataset",
    response_model=MLDatasetMetadata,
    summary="Create comprehensive ML dataset",
    description="Create ML training dataset with train/validation/test splits"
)
async def create_ml_training_dataset(
    dataset_config: Dict[str, Any],
    current_user_id: str = Depends(get_current_user_id),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db=Depends(get_db)
):
    """
    Create comprehensive ML training dataset with splits.
    
    Generates train/validation/test splits from anonymized profiles with
    proper stratification and compliance validation for each split.
    """
    try:
        # Validate dataset configuration
        required_fields = ["name", "profiles"]
        missing_fields = [field for field in required_fields if field not in dataset_config]
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required fields: {missing_fields}"
            )
        
        profiles = dataset_config["profiles"]
        if not isinstance(profiles, list) or len(profiles) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset must contain at least 10 profiles"
            )
        
        # Validate split ratios if provided
        split_ratios = dataset_config.get("split_ratios", {"train": 0.8, "validation": 0.1, "test": 0.1})
        if abs(sum(split_ratios.values()) - 1.0) > 0.001:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Split ratios must sum to 1.0"
            )
        
        # Create ML training dataset
        start_time = datetime.utcnow()
        dataset_metadata = await data_lake.create_ml_training_dataset(dataset_config)
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(
            "ML training dataset created successfully",
            user_id=current_user_id,
            dataset_id=dataset_metadata.dataset_id,
            dataset_name=dataset_metadata.dataset_name,
            total_profiles=dataset_metadata.total_profiles,
            processing_time_seconds=processing_time
        )
        
        return dataset_metadata
        
    except ValidationError as e:
        logger.error(
            "ML dataset creation validation failed",
            user_id=current_user_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dataset creation validation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(
            "ML dataset creation failed",
            user_id=current_user_id,
            dataset_name=dataset_config.get("name", "unknown"),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create ML training dataset"
        )

@router.post(
    "/sync-to-vector-db",
    summary="Sync profiles to vector database",
    description="Synchronize anonymized profiles to Milvus vector database"
)
async def sync_profiles_to_vector_database(
    profiles: List[AnonymizedMLProfile],
    current_user_id: str = Depends(get_current_user_id),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db=Depends(get_db)
):
    """
    Synchronize anonymized profiles to vector database.
    
    Indexes Clinical BERT embeddings in Milvus for similarity search
    while maintaining data consistency between data lake and vector store.
    """
    try:
        if not profiles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No profiles provided for synchronization"
            )
        
        # Validate profiles have embeddings
        vectorizable_profiles = [
            profile for profile in profiles
            if profile.clinical_text_embedding and profile.compliance_validated
        ]
        
        if not vectorizable_profiles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No profiles with valid embeddings for vector database sync"
            )
        
        # Synchronize to vector database
        start_time = datetime.utcnow()
        sync_result = await data_lake.sync_to_vector_database(vectorizable_profiles)
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(
            "Profiles synchronized to vector database",
            user_id=current_user_id,
            profiles_submitted=len(profiles),
            profiles_synced=sync_result["synced_count"],
            sync_id=sync_result.get("sync_id"),
            processing_time_seconds=processing_time
        )
        
        return {
            "status": "synchronized",
            "profiles_submitted": len(profiles),
            "profiles_synced": sync_result["synced_count"],
            "sync_id": sync_result.get("sync_id"),
            "success": sync_result["success"],
            "errors": sync_result.get("errors", []),
            "processing_time_seconds": processing_time,
            "synchronized_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(
            "Vector database sync failed",
            user_id=current_user_id,
            profiles_count=len(profiles),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to synchronize profiles to vector database"
        )

@router.post(
    "/upload-embeddings",
    summary="Upload vector embeddings",
    description="Batch upload vector embeddings to data lake storage"
)
async def upload_vector_embeddings(
    embeddings: List[Dict[str, Any]],
    batch_size: int = 1000,
    current_user_id: str = Depends(get_current_user_id),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db=Depends(get_db)
):
    """
    Batch upload vector embeddings to data lake.
    
    Efficiently stores Clinical BERT embeddings in Parquet format
    with proper partitioning and compression for ML workflows.
    """
    try:
        if not embeddings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No embeddings provided for upload"
            )
        
        if len(embeddings) > 50000:  # Reasonable upload limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Upload size too large. Maximum 50,000 embeddings per upload."
            )
        
        if not 100 <= batch_size <= 5000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size must be between 100 and 5000"
            )
        
        # Validate embedding structure
        for i, embedding in enumerate(embeddings[:5]):  # Check first 5
            if not isinstance(embedding, dict):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Embedding {i} must be a dictionary"
                )
            if "vector" not in embedding:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Embedding {i} missing 'vector' field"
                )
        
        # Upload embeddings in batches
        start_time = datetime.utcnow()
        uploaded_keys = await data_lake.batch_upload_vector_embeddings(
            embeddings=embeddings,
            batch_size=batch_size
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(
            "Vector embeddings uploaded successfully",
            user_id=current_user_id,
            embeddings_count=len(embeddings),
            batches_created=len(uploaded_keys),
            batch_size=batch_size,
            processing_time_seconds=processing_time
        )
        
        return {
            "status": "uploaded",
            "embeddings_count": len(embeddings),
            "batches_created": len(uploaded_keys),
            "batch_size": batch_size,
            "s3_keys": uploaded_keys,
            "processing_time_seconds": processing_time,
            "uploaded_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(
            "Vector embeddings upload failed",
            user_id=current_user_id,
            embeddings_count=len(embeddings),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload vector embeddings"
        )

@router.get(
    "/bucket-security/{bucket_name}",
    summary="Validate bucket security",
    description="Validate HIPAA security configuration for specific bucket"
)
async def validate_bucket_security(
    bucket_name: str,
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Validate HIPAA security configuration for data lake bucket.
    
    Checks encryption, access controls, lifecycle policies, and audit
    logging configuration for healthcare compliance requirements.
    """
    try:
        # Validate bucket name
        valid_buckets = list(data_lake.config.buckets.values())
        if bucket_name not in valid_buckets:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bucket not found. Valid buckets: {valid_buckets}"
            )
        
        # Validate bucket security
        security_status = await data_lake.validate_bucket_security(bucket_name)
        
        # Calculate overall security score
        security_checks = [
            security_status.get("encryption_enabled", False),
            security_status.get("versioning_enabled", False),
            security_status.get("lifecycle_configured", False),
            security_status.get("public_access_blocked", False),
            security_status.get("audit_logging_enabled", False)
        ]
        
        security_score = sum(security_checks) / len(security_checks)
        compliance_level = "compliant" if security_score >= 0.8 else "non_compliant"
        
        logger.info(
            "Bucket security validation completed",
            user_id=current_user_id,
            bucket_name=bucket_name,
            security_score=security_score,
            compliance_level=compliance_level
        )
        
        return {
            "bucket_name": bucket_name,
            "security_status": security_status,
            "security_score": security_score,
            "compliance_level": compliance_level,
            "validation_timestamp": datetime.utcnow().isoformat(),
            "recommendations": [
                "Enable encryption" if not security_status.get("encryption_enabled") else None,
                "Enable versioning" if not security_status.get("versioning_enabled") else None,
                "Configure lifecycle policies" if not security_status.get("lifecycle_configured") else None,
                "Block public access" if not security_status.get("public_access_blocked") else None,
                "Enable audit logging" if not security_status.get("audit_logging_enabled") else None
            ]
        }
        
    except Exception as e:
        logger.error(
            "Bucket security validation failed",
            user_id=current_user_id,
            bucket_name=bucket_name,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate bucket security"
        )

@router.get(
    "/upload-statistics",
    summary="Get upload statistics",
    description="Get upload performance and usage statistics"
)
async def get_upload_statistics(
    current_user_id: str = Depends(get_current_user_id),
    db=Depends(get_db)
):
    """
    Get data lake upload statistics and performance metrics.
    
    Provides insights into upload patterns, performance, and storage
    utilization for capacity planning and optimization.
    """
    try:
        # Get upload statistics
        upload_stats = data_lake.upload_stats.copy()
        
        # Calculate additional metrics
        if upload_stats["total_uploads"] > 0:
            success_rate = (
                (upload_stats["total_uploads"] - upload_stats["failed_uploads"]) / 
                upload_stats["total_uploads"]
            )
            average_size_mb = upload_stats["total_bytes"] / (1024 * 1024 * upload_stats["total_uploads"])
        else:
            success_rate = 0.0
            average_size_mb = 0.0
        
        statistics = {
            "upload_statistics": upload_stats,
            "performance_metrics": {
                "success_rate": success_rate,
                "average_upload_size_mb": average_size_mb,
                "total_storage_gb": upload_stats["total_bytes"] / (1024 * 1024 * 1024)
            },
            "bucket_configuration": {
                "total_buckets": len(data_lake.config.buckets),
                "encryption_enabled": data_lake.config.encryption_enabled,
                "versioning_enabled": data_lake.config.versioning_enabled,
                "audit_logging": data_lake.config.audit_logging
            },
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
        logger.info(
            "Upload statistics retrieved",
            user_id=current_user_id,
            total_uploads=upload_stats["total_uploads"],
            success_rate=success_rate
        )
        
        return statistics
        
    except Exception as e:
        logger.error(
            "Failed to get upload statistics",
            user_id=current_user_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve upload statistics"
        )

@router.get(
    "/health",
    summary="Data lake health check",
    description="Check health status of MinIO data lake"
)
async def data_lake_health_check():
    """
    Health check for MinIO data lake infrastructure.
    
    Verifies connection status, bucket health, security configuration,
    and storage capacity for production monitoring.
    """
    try:
        # Check MinIO client status
        client_status = "connected" if data_lake.minio_client else "disconnected"
        
        # Get bucket status
        bucket_status = {}
        if data_lake.minio_client:
            try:
                buckets = data_lake.minio_client.list_buckets()
                bucket_status = {bucket.name: "healthy" for bucket in buckets}
            except Exception:
                bucket_status = {"error": "failed_to_list_buckets"}
        
        # Get upload statistics
        upload_stats = data_lake.upload_stats
        
        health_status = {
            "service": "minio_data_lake",
            "status": "healthy" if client_status == "connected" else "unhealthy",
            "client_status": client_status,
            "bucket_status": bucket_status,
            "upload_statistics": upload_stats,
            "configuration": {
                "encryption_enabled": data_lake.config.encryption_enabled,
                "versioning_enabled": data_lake.config.versioning_enabled,
                "audit_logging": data_lake.config.audit_logging,
                "secure_transport": data_lake.config.secure
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return health_status
        
    except Exception as e:
        logger.error("Data lake health check failed", error=str(e))
        return {
            "service": "minio_data_lake",
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }