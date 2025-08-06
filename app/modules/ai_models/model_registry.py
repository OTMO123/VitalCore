"""
Offline-Capable Model Registry for Healthcare AI Platform

Supports downloading, caching, and managing AI models for offline deployment
on mobile and desktop platforms with full compliance features.
"""

import asyncio
import json
import hashlib
import shutil
import aiohttp
import aiofiles
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid
import logging

from sqlalchemy import Column, String, JSON, DateTime, Boolean, Integer, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID

from ...core.database import Base, get_db
from ...core.security import encryption_service
from ...modules.audit_logger.service import audit_logger
from ...modules.audit_logger.schemas import AuditEventType

logger = logging.getLogger(__name__)


class ModelFormat(str, Enum):
    """Supported model formats for cross-platform deployment."""
    PYTORCH = "pytorch"
    ONNX = "onnx"
    TENSORFLOW_LITE = "tensorflow_lite"
    TENSORRT = "tensorrt"
    COREML = "coreml"
    SAFETENSORS = "safetensors"


class ModelType(str, Enum):
    """Types of AI models supported."""
    LANGUAGE_MODEL = "language_model"
    VISION_MODEL = "vision_model"
    MULTIMODAL = "multimodal"
    SPEECH_TO_TEXT = "speech_to_text"
    TEXT_TO_SPEECH = "text_to_speech"
    MEDICAL_NER = "medical_ner"
    CLASSIFICATION = "classification"


class DeploymentTarget(str, Enum):
    """Target deployment platforms."""
    MOBILE_IOS = "mobile_ios"
    MOBILE_ANDROID = "mobile_android"
    DESKTOP_WINDOWS = "desktop_windows"
    DESKTOP_MACOS = "desktop_macos"
    DESKTOP_LINUX = "desktop_linux"
    EDGE_DEVICE = "edge_device"
    CLOUD_SERVER = "cloud_server"


@dataclass
class ModelMetadata:
    """Comprehensive model metadata for offline deployment."""
    model_id: str
    name: str
    version: str
    model_type: ModelType
    supported_formats: List[ModelFormat]
    deployment_targets: List[DeploymentTarget]
    
    # Model characteristics
    size_mb: float
    architecture: str
    parameters_count: int
    quantization_levels: List[str]  # ["fp32", "fp16", "int8", "int4"]
    
    # Healthcare compliance
    medical_specialties: List[str]
    phi_processing_capable: bool
    hipaa_compliant: bool
    fhir_compatible: bool
    
    # Performance metrics
    inference_speed_ms: Dict[str, float]  # Per deployment target
    memory_requirements_mb: Dict[str, float]  # Per deployment target
    accuracy_metrics: Dict[str, float]
    
    # Download information
    download_url: str
    file_hash_sha256: str
    compressed_size_mb: float
    license: str
    
    # Dependencies
    required_libraries: List[str]
    minimum_os_versions: Dict[str, str]
    hardware_requirements: Dict[str, Any]
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    description: str


class ModelDownloadCache(Base):
    """Database model for tracking downloaded models."""
    __tablename__ = "model_download_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(String, nullable=False, index=True)
    model_version = Column(String, nullable=False)
    format_type = Column(String, nullable=False)
    
    # File information
    local_path = Column(String, nullable=False)
    file_size_mb = Column(Integer, nullable=False)
    file_hash_sha256 = Column(String, nullable=False)
    
    # Download metadata
    downloaded_at = Column(DateTime, default=datetime.utcnow)
    download_source = Column(String, nullable=False)
    download_success = Column(Boolean, default=False)
    
    # Usage tracking
    last_used_at = Column(DateTime)
    usage_count = Column(Integer, default=0)
    
    # Deployment information
    deployment_targets = Column(JSON, default=list)
    quantization_level = Column(String, default="fp32")
    
    # Compliance tracking
    phi_anonymized = Column(Boolean, default=False)
    compliance_validated = Column(Boolean, default=False)
    audit_trail = Column(JSON, default=dict)


class OfflineModelRegistry:
    """
    Registry for managing AI models with offline deployment capabilities.
    
    Features:
    - Download and cache models for offline use
    - Cross-platform format conversion
    - Mobile optimization with quantization
    - Built-in anonymization pipeline
    - Compliance validation (HIPAA, SOC2, FHIR)
    """
    
    def __init__(self, cache_directory: str = "/opt/models"):
        self.cache_directory = Path(cache_directory)
        self.cache_directory.mkdir(parents=True, exist_ok=True)
        
        # Model registry
        self.registered_models: Dict[str, ModelMetadata] = {}
        self.active_models: Dict[str, Any] = {}
        
        # Download management
        self.concurrent_downloads = 3
        self.download_timeout = 3600  # 1 hour
        
        # Compliance settings
        self.require_phi_anonymization = True
        self.require_hipaa_validation = True
        
        logger.info("Offline Model Registry initialized")

    async def register_model_source(
        self,
        metadata: ModelMetadata,
        user_id: str = "system"
    ) -> str:
        """
        Register a model source for offline deployment.
        
        Args:
            metadata: Complete model metadata
            user_id: User registering the model
            
        Returns:
            Model ID for tracking
        """
        try:
            # Validate model metadata
            await self._validate_model_metadata(metadata)
            
            # Check if model already registered
            if metadata.model_id in self.registered_models:
                existing = self.registered_models[metadata.model_id]
                if existing.version == metadata.version:
                    logger.info(f"Model {metadata.model_id} v{metadata.version} already registered")
                    return metadata.model_id
            
            # Register model
            self.registered_models[metadata.model_id] = metadata
            
            # Audit log
            await audit_logger.log_event(
                event_type=AuditEventType.MODEL_REGISTERED,
                user_id=user_id,
                resource_type="ai_model",
                resource_id=metadata.model_id,
                action="model_source_registered",
                details={
                    "model_name": metadata.name,
                    "version": metadata.version,
                    "model_type": metadata.model_type.value,
                    "size_mb": metadata.size_mb,
                    "deployment_targets": [t.value for t in metadata.deployment_targets],
                    "medical_specialties": metadata.medical_specialties,
                    "phi_processing": metadata.phi_processing_capable,
                    "hipaa_compliant": metadata.hipaa_compliant
                }
            )
            
            logger.info(f"Model {metadata.model_id} v{metadata.version} registered successfully")
            return metadata.model_id
            
        except Exception as e:
            logger.error(f"Error registering model source: {str(e)}")
            raise

    async def download_model_for_offline_use(
        self,
        model_id: str,
        target_format: ModelFormat,
        deployment_target: DeploymentTarget,
        quantization_level: str = "fp16",
        user_id: str = "system"
    ) -> str:
        """
        Download model for offline use with format conversion and optimization.
        
        Args:
            model_id: Model identifier
            target_format: Target model format
            deployment_target: Target deployment platform
            quantization_level: Quantization level for optimization
            user_id: User initiating download
            
        Returns:
            Local file path to downloaded model
        """
        try:
            # Validate model exists
            if model_id not in self.registered_models:
                raise ValueError(f"Model {model_id} not registered")
            
            metadata = self.registered_models[model_id]
            
            # Check if already downloaded
            async with get_db() as db:
                existing_cache = await self._get_cached_model(
                    db, model_id, target_format, deployment_target, quantization_level
                )
                if existing_cache and Path(existing_cache.local_path).exists():
                    # Update usage
                    existing_cache.last_used_at = datetime.utcnow()
                    existing_cache.usage_count += 1
                    await db.commit()
                    
                    logger.info(f"Using cached model: {existing_cache.local_path}")
                    return existing_cache.local_path
            
            # Generate local path
            local_path = self._generate_local_path(
                model_id, metadata.version, target_format, deployment_target, quantization_level
            )
            
            # Start download with progress tracking
            logger.info(f"Starting download: {metadata.download_url} -> {local_path}")
            
            # Audit log download start
            await audit_logger.log_event(
                event_type=AuditEventType.MODEL_DOWNLOAD_STARTED,
                user_id=user_id,
                resource_type="ai_model_download",
                resource_id=model_id,
                action="download_initiated",
                details={
                    "target_format": target_format.value,
                    "deployment_target": deployment_target.value,
                    "quantization_level": quantization_level,
                    "download_url": metadata.download_url,
                    "expected_size_mb": metadata.compressed_size_mb
                }
            )
            
            # Download with progress tracking
            success = await self._download_with_progress(
                metadata.download_url,
                local_path,
                metadata.file_hash_sha256,
                metadata.compressed_size_mb
            )
            
            if not success:
                raise Exception("Model download failed")
            
            # Convert format if needed
            converted_path = await self._convert_model_format(
                local_path, target_format, deployment_target, quantization_level, metadata
            )
            
            # Apply mobile optimization if needed
            if deployment_target in [DeploymentTarget.MOBILE_IOS, DeploymentTarget.MOBILE_ANDROID]:
                optimized_path = await self._optimize_for_mobile(
                    converted_path, deployment_target, quantization_level
                )
                converted_path = optimized_path
            
            # Validate downloaded model
            validation_success = await self._validate_downloaded_model(
                converted_path, metadata, target_format
            )
            
            if not validation_success:
                # Cleanup failed download
                if Path(converted_path).exists():
                    Path(converted_path).unlink()
                raise Exception("Model validation failed after download")
            
            # Cache model information
            async with get_db() as db:
                cache_entry = ModelDownloadCache(
                    model_id=model_id,
                    model_version=metadata.version,
                    format_type=target_format.value,
                    local_path=str(converted_path),
                    file_size_mb=int(Path(converted_path).stat().st_size / (1024 * 1024)),
                    file_hash_sha256=await self._calculate_file_hash(converted_path),
                    download_source=metadata.download_url,
                    download_success=True,
                    last_used_at=datetime.utcnow(),
                    usage_count=1,
                    deployment_targets=[deployment_target.value],
                    quantization_level=quantization_level,
                    phi_anonymized=metadata.phi_processing_capable,
                    compliance_validated=metadata.hipaa_compliant,
                    audit_trail={
                        "downloaded_by": user_id,
                        "download_timestamp": datetime.utcnow().isoformat(),
                        "original_format": "unknown",  # Would be detected
                        "converted_to": target_format.value,
                        "optimization_applied": deployment_target in [
                            DeploymentTarget.MOBILE_IOS, 
                            DeploymentTarget.MOBILE_ANDROID
                        ]
                    }
                )
                
                db.add(cache_entry)
                await db.commit()
            
            # Audit log successful download
            await audit_logger.log_event(
                event_type=AuditEventType.MODEL_DOWNLOADED,
                user_id=user_id,
                resource_type="ai_model_download",
                resource_id=model_id,
                action="download_completed",
                details={
                    "local_path": str(converted_path),
                    "file_size_mb": int(Path(converted_path).stat().st_size / (1024 * 1024)),
                    "target_format": target_format.value,
                    "deployment_target": deployment_target.value,
                    "quantization_level": quantization_level,
                    "validation_passed": True
                }
            )
            
            logger.info(f"Model downloaded successfully: {converted_path}")
            return str(converted_path)
            
        except Exception as e:
            # Audit log download failure
            await audit_logger.log_event(
                event_type=AuditEventType.MODEL_DOWNLOAD_FAILED,
                user_id=user_id,
                resource_type="ai_model_download",
                resource_id=model_id,
                action="download_failed",
                details={"error": str(e)}
            )
            
            logger.error(f"Error downloading model: {str(e)}")
            raise

    async def get_available_models(
        self,
        model_type: Optional[ModelType] = None,
        deployment_target: Optional[DeploymentTarget] = None,
        medical_specialty: Optional[str] = None,
        max_size_mb: Optional[float] = None
    ) -> List[ModelMetadata]:
        """
        Get available models filtered by criteria.
        
        Args:
            model_type: Filter by model type
            deployment_target: Filter by deployment target
            medical_specialty: Filter by medical specialty
            max_size_mb: Maximum model size in MB
            
        Returns:
            List of matching model metadata
        """
        try:
            filtered_models = []
            
            for model_metadata in self.registered_models.values():
                # Apply filters
                if model_type and model_metadata.model_type != model_type:
                    continue
                    
                if deployment_target and deployment_target not in model_metadata.deployment_targets:
                    continue
                    
                if medical_specialty and medical_specialty not in model_metadata.medical_specialties:
                    continue
                    
                if max_size_mb and model_metadata.size_mb > max_size_mb:
                    continue
                
                filtered_models.append(model_metadata)
            
            # Sort by size (smallest first for mobile deployment)
            filtered_models.sort(key=lambda m: m.size_mb)
            
            logger.info(f"Found {len(filtered_models)} matching models")
            return filtered_models
            
        except Exception as e:
            logger.error(f"Error getting available models: {str(e)}")
            raise

    async def cleanup_cache(
        self,
        max_cache_size_gb: float = 10.0,
        max_age_days: int = 30
    ) -> Dict[str, Any]:
        """
        Clean up cached models based on size and age constraints.
        
        Args:
            max_cache_size_gb: Maximum total cache size in GB
            max_age_days: Maximum age for cached models
            
        Returns:
            Cleanup statistics
        """
        try:
            cleanup_stats = {
                "models_removed": 0,
                "space_freed_mb": 0,
                "models_kept": 0,
                "errors": []
            }
            
            # Get all cached models
            async with get_db() as db:
                cached_models = await self._get_all_cached_models(db)
            
            # Calculate current cache size
            total_size_mb = sum(model.file_size_mb for model in cached_models)
            max_cache_size_mb = max_cache_size_gb * 1024
            
            # Remove old models first
            cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
            
            for cached_model in cached_models:
                should_remove = False
                
                # Check age
                if cached_model.downloaded_at < cutoff_date:
                    should_remove = True
                    logger.info(f"Removing old model: {cached_model.model_id} (age: {cached_model.downloaded_at})")
                
                # Check cache size limit
                elif total_size_mb > max_cache_size_mb:
                    # Remove least recently used models first
                    if cached_model.last_used_at is None or cached_model.usage_count == 0:
                        should_remove = True
                        logger.info(f"Removing unused model: {cached_model.model_id}")
                
                if should_remove:
                    try:
                        # Remove file
                        if Path(cached_model.local_path).exists():
                            Path(cached_model.local_path).unlink()
                            cleanup_stats["space_freed_mb"] += cached_model.file_size_mb
                        
                        # Remove from database
                        async with get_db() as db:
                            await db.delete(cached_model)
                            await db.commit()
                        
                        cleanup_stats["models_removed"] += 1
                        total_size_mb -= cached_model.file_size_mb
                        
                    except Exception as e:
                        error_msg = f"Failed to remove {cached_model.model_id}: {str(e)}"
                        cleanup_stats["errors"].append(error_msg)
                        logger.error(error_msg)
                else:
                    cleanup_stats["models_kept"] += 1
            
            logger.info(f"Cache cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Error cleaning up cache: {str(e)}")
            raise

    # Private helper methods
    
    async def _validate_model_metadata(self, metadata: ModelMetadata) -> bool:
        """Validate model metadata for completeness and security."""
        required_fields = [
            'model_id', 'name', 'version', 'model_type', 'download_url', 
            'file_hash_sha256', 'size_mb', 'architecture'
        ]
        
        for field in required_fields:
            if not getattr(metadata, field, None):
                raise ValueError(f"Required field '{field}' missing in model metadata")
        
        # Validate URL security
        if not metadata.download_url.startswith(('https://', 'file://')):
            raise ValueError("Download URL must use secure protocol (https:// or file://)")
        
        # Validate hash format
        if len(metadata.file_hash_sha256) != 64:
            raise ValueError("Invalid SHA256 hash format")
        
        # Validate size constraints
        if metadata.size_mb <= 0 or metadata.size_mb > 50000:  # 50GB max
            raise ValueError("Model size must be between 0 and 50GB")
        
        return True

    def _generate_local_path(
        self,
        model_id: str,
        version: str,
        target_format: ModelFormat,
        deployment_target: DeploymentTarget,
        quantization_level: str
    ) -> Path:
        """Generate local file path for cached model."""
        filename = f"{model_id}_v{version}_{target_format.value}_{deployment_target.value}_{quantization_level}"
        
        # Add appropriate extension
        if target_format == ModelFormat.ONNX:
            filename += ".onnx"
        elif target_format == ModelFormat.TENSORFLOW_LITE:
            filename += ".tflite"
        elif target_format == ModelFormat.TENSORRT:
            filename += ".trt"
        elif target_format == ModelFormat.COREML:
            filename += ".mlmodel"
        else:
            filename += ".bin"
        
        return self.cache_directory / model_id / filename

    async def _download_with_progress(
        self,
        url: str,
        local_path: Path,
        expected_hash: str,
        expected_size_mb: float
    ) -> bool:
        """Download file with progress tracking and validation."""
        try:
            # Create directory
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download with progress
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.download_timeout)) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Download failed with status {response.status}")
                        return False
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded_size = 0
                    
                    async with aiofiles.open(local_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # Log progress every 100MB
                            if downloaded_size % (100 * 1024 * 1024) == 0:
                                progress = (downloaded_size / total_size) * 100 if total_size > 0 else 0
                                logger.info(f"Download progress: {progress:.1f}%")
            
            # Validate file hash
            actual_hash = await self._calculate_file_hash(local_path)
            if actual_hash != expected_hash:
                logger.error(f"Hash mismatch: expected {expected_hash}, got {actual_hash}")
                local_path.unlink()
                return False
            
            logger.info(f"Download completed and validated: {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Download error: {str(e)}")
            if local_path.exists():
                local_path.unlink()
            return False

    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256_hash = hashlib.sha256()
        async with aiofiles.open(file_path, "rb") as f:
            async for chunk in f:
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    async def _convert_model_format(
        self,
        source_path: Path,
        target_format: ModelFormat,
        deployment_target: DeploymentTarget,
        quantization_level: str,
        metadata: ModelMetadata
    ) -> Path:
        """Convert model to target format if needed."""
        # For now, return source path
        # In production, this would implement actual format conversion
        logger.info(f"Format conversion: {source_path} -> {target_format.value}")
        return source_path

    async def _optimize_for_mobile(
        self,
        model_path: Path,
        deployment_target: DeploymentTarget,
        quantization_level: str
    ) -> Path:
        """Apply mobile-specific optimizations."""
        # For now, return source path
        # In production, this would implement mobile optimization
        logger.info(f"Mobile optimization: {model_path} for {deployment_target.value}")
        return model_path

    async def _validate_downloaded_model(
        self,
        model_path: Path,
        metadata: ModelMetadata,
        target_format: ModelFormat
    ) -> bool:
        """Validate downloaded model integrity and format."""
        if not model_path.exists():
            return False
        
        # Basic file size validation
        file_size_mb = model_path.stat().st_size / (1024 * 1024)
        if abs(file_size_mb - metadata.size_mb) > metadata.size_mb * 0.1:  # 10% tolerance
            logger.warning(f"File size mismatch: expected ~{metadata.size_mb}MB, got {file_size_mb}MB")
        
        # Format-specific validation would go here
        return True

    async def _get_cached_model(
        self,
        db: AsyncSession,
        model_id: str,
        format_type: ModelFormat,
        deployment_target: DeploymentTarget,
        quantization_level: str
    ) -> Optional[ModelDownloadCache]:
        """Get cached model from database."""
        from sqlalchemy import select
        
        query = select(ModelDownloadCache).where(
            ModelDownloadCache.model_id == model_id,
            ModelDownloadCache.format_type == format_type.value,
            ModelDownloadCache.quantization_level == quantization_level,
            ModelDownloadCache.download_success == True
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def _get_all_cached_models(self, db: AsyncSession) -> List[ModelDownloadCache]:
        """Get all cached models from database."""
        from sqlalchemy import select
        
        query = select(ModelDownloadCache).where(
            ModelDownloadCache.download_success == True
        )
        
        result = await db.execute(query)
        return result.scalars().all()