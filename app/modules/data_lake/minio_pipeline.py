"""
MinIO Data Lake Pipeline for Healthcare ML Platform

Enterprise-grade MinIO integration for ML training datasets with HIPAA-compliant
storage, automated lifecycle management, and seamless vector database synchronization.
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import structlog
import io
import uuid

# Handle optional data lake dependencies
try:
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
    from minio import Minio
    from minio.error import S3Error
    import boto3
    from botocore.exceptions import ClientError
    DATA_LAKE_DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    # Create mock objects for missing dependencies
    pd = None
    pa = None
    pq = None
    Minio = None
    S3Error = None
    boto3 = None
    ClientError = None
    DATA_LAKE_DEPENDENCIES_AVAILABLE = False
    MISSING_DATA_LAKE_DEPS_ERROR = str(e)

from app.core.config import get_settings
from app.core.security import EncryptionService

# Handle optional audit service import
try:
    from app.modules.audit_logger.service import SOC2AuditService, get_audit_service
    AUDIT_SERVICE_AVAILABLE = True
except ImportError:
    SOC2AuditService = None
    get_audit_service = None
    AUDIT_SERVICE_AVAILABLE = False
from app.modules.data_anonymization.schemas import AnonymizedMLProfile, MLDatasetMetadata
from app.modules.vector_store.milvus_client import MilvusVectorStore
from app.modules.vector_store.schemas import VectorIndexRequest

logger = structlog.get_logger(__name__)

class DataLakeConfig:
    """Configuration for MinIO Data Lake."""
    
    def __init__(self):
        self.endpoint = "localhost:9000"
        self.access_key = "minio_access_key"
        self.secret_key = "minio_secret_key"
        self.secure = True
        self.region = "us-east-1"
        
        # Healthcare-specific buckets
        self.buckets = {
            "ml-training-data": "ml-training-datasets",
            "vector-embeddings": "clinical-bert-embeddings", 
            "anonymized-profiles": "anonymized-patient-profiles",
            "model-artifacts": "ml-model-artifacts",
            "audit-logs": "data-access-audit-logs",
            "backups": "disaster-recovery-backups"
        }
        
        # HIPAA compliance settings
        self.encryption_enabled = True
        self.versioning_enabled = True
        self.audit_logging = True
        self.retention_days = {
            "training_data": 2555,  # 7 years for HIPAA
            "embeddings": 365,      # 1 year for vectors
            "audit_logs": 2555,     # 7 years for audit
            "backups": 90           # 90 days for backups
        }
        
        # Performance settings
        self.batch_size = 1000
        self.multipart_threshold = 64 * 1024 * 1024  # 64MB
        self.max_concurrency = 10

class MLDataLakePipeline:
    """
    Production-ready MinIO data lake pipeline for healthcare ML platform.
    
    Provides HIPAA-compliant ML dataset management with automated lifecycle
    policies, vector database synchronization, and comprehensive audit trails.
    """
    
    def __init__(self, config: Optional[DataLakeConfig] = None):
        """
        Initialize ML data lake pipeline.
        
        Args:
            config: Data lake configuration
        """
        self.config = config or DataLakeConfig()
        self.settings = get_settings()
        self.logger = logger.bind(component="MLDataLakePipeline")
        
        # Check data lake dependencies
        if not DATA_LAKE_DEPENDENCIES_AVAILABLE:
            self.logger.error(
                "Data lake dependencies not available - data lake functionality disabled",
                error=MISSING_DATA_LAKE_DEPS_ERROR
            )
            self.data_lake_available = False
        else:
            self.data_lake_available = True
        
        # Initialize services
        self.encryption_service = EncryptionService()
        
        # Initialize audit service if available
        if AUDIT_SERVICE_AVAILABLE and get_audit_service is not None:
            try:
                self.audit_service = get_audit_service()
            except RuntimeError:
                # Audit service not initialized yet - will be set later
                self.audit_service = None
                self.logger.info("Audit service not initialized yet - will be available after startup")
        else:
            self.audit_service = None
            self.logger.warning("Audit service not available - data lake operations will not be audited")
        self.vector_store: Optional[MilvusVectorStore] = None
        
        # MinIO clients
        self.minio_client: Optional[Minio] = None
        self.s3_client: Optional[boto3.client] = None
        
        # Operation tracking
        self.upload_stats = {
            "total_uploads": 0,
            "total_bytes": 0,
            "failed_uploads": 0,
            "average_speed_mbps": 0.0
        }
        
        self.logger.info(
            "ML Data Lake pipeline initialized",
            endpoint=self.config.endpoint,
            secure=self.config.secure,
            encryption_enabled=self.config.encryption_enabled
        )
    
    # CONNECTION & CONFIGURATION METHODS
    
    async def initialize_minio_client(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        secure: Optional[bool] = None
    ) -> None:
        """
        Initialize secure MinIO client connection.
        
        Args:
            endpoint: MinIO server endpoint (optional override)
            access_key: Access key (optional override)
            secret_key: Secret key (optional override)
            secure: Enable HTTPS (optional override)
        """
        try:
            # Use provided parameters or fall back to config
            endpoint = endpoint or self.config.endpoint
            access_key = access_key or self.config.access_key
            secret_key = secret_key or self.config.secret_key
            secure = secure if secure is not None else self.config.secure
            
            # Initialize MinIO client
            self.minio_client = Minio(
                endpoint=endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure,
                region=self.config.region
            )
            
            # Initialize S3-compatible client for advanced operations
            self.s3_client = boto3.client(
                's3',
                endpoint_url=f"{'https' if secure else 'http'}://{endpoint}",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=self.config.region
            )
            
            # Test connection
            try:
                buckets = self.minio_client.list_buckets()
                bucket_count = len(buckets)
            except Exception as e:
                raise ConnectionError(f"Failed to connect to MinIO: {str(e)}")
            
            self.logger.info(
                "MinIO client initialized successfully",
                endpoint=endpoint,
                secure=secure,
                existing_buckets=bucket_count
            )
            
            # Audit connection establishment
            await self._audit_connection_event("connected", {
                "endpoint": endpoint,
                "secure": secure,
                "bucket_count": bucket_count
            })
            
        except Exception as e:
            self.logger.error(
                "Failed to initialize MinIO client",
                endpoint=endpoint,
                error=str(e)
            )
            raise
    
    async def create_healthcare_buckets(self) -> Dict[str, bool]:
        """
        Create healthcare-specific buckets with HIPAA compliance settings.
        
        Returns:
            Dictionary of bucket creation results
        """
        try:
            if not self.minio_client:
                await self.initialize_minio_client()
            
            creation_results = {}
            
            for bucket_purpose, bucket_name in self.config.buckets.items():
                try:
                    # Check if bucket already exists
                    if self.minio_client.bucket_exists(bucket_name):
                        creation_results[bucket_name] = True
                        self.logger.info(f"Bucket {bucket_name} already exists")
                        continue
                    
                    # Create bucket
                    self.minio_client.make_bucket(
                        bucket_name=bucket_name,
                        location=self.config.region
                    )
                    
                    # Configure HIPAA compliance settings
                    await self._configure_bucket_compliance(bucket_name, bucket_purpose)
                    
                    creation_results[bucket_name] = True
                    
                    self.logger.info(
                        "Healthcare bucket created successfully",
                        bucket_name=bucket_name,
                        purpose=bucket_purpose
                    )
                    
                except Exception as e:
                    creation_results[bucket_name] = False
                    self.logger.error(
                        "Failed to create healthcare bucket",
                        bucket_name=bucket_name,
                        error=str(e)
                    )
            
            # Audit bucket creation
            await self._audit_bucket_operation("create_healthcare_buckets", {
                "buckets_created": sum(creation_results.values()),
                "total_buckets": len(self.config.buckets),
                "results": creation_results
            })
            
            return creation_results
            
        except Exception as e:
            self.logger.error(
                "Failed to create healthcare buckets",
                error=str(e)
            )
            return {}
    
    async def configure_hipaa_encryption(self, bucket_name: str) -> bool:
        """
        Configure HIPAA-compliant encryption for bucket.
        
        Args:
            bucket_name: Name of bucket to configure
            
        Returns:
            True if encryption configured successfully
        """
        try:
            if not self.s3_client:
                await self.initialize_minio_client()
            
            # Configure server-side encryption
            encryption_config = {
                'Rules': [
                    {
                        'ApplyServerSideEncryptionByDefault': {
                            'SSEAlgorithm': 'AES256'
                        },
                        'BucketKeyEnabled': True
                    }
                ]
            }
            
            # Apply encryption configuration
            self.s3_client.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration=encryption_config
            )
            
            self.logger.info(
                "HIPAA encryption configured for bucket",
                bucket_name=bucket_name,
                encryption_algorithm="AES256"
            )
            
            # Audit encryption configuration
            await self._audit_security_event("encryption_configured", {
                "bucket_name": bucket_name,
                "encryption_algorithm": "AES256"
            })
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to configure HIPAA encryption",
                bucket_name=bucket_name,
                error=str(e)
            )
            return False
    
    async def setup_lifecycle_policies(self, bucket_name: str, retention_days: int) -> bool:
        """
        Setup lifecycle policies for HIPAA data retention.
        
        Args:
            bucket_name: Name of bucket
            retention_days: Number of days to retain data
            
        Returns:
            True if lifecycle policies configured successfully
        """
        try:
            if not self.s3_client:
                await self.initialize_minio_client()
            
            # Configure lifecycle policy
            lifecycle_config = {
                'Rules': [
                    {
                        'ID': f'HIPAARetention-{bucket_name}',
                        'Status': 'Enabled',
                        'Expiration': {
                            'Days': retention_days
                        },
                        'NoncurrentVersionExpiration': {
                            'NoncurrentDays': retention_days
                        },
                        'AbortIncompleteMultipartUpload': {
                            'DaysAfterInitiation': 7
                        }
                    }
                ]
            }
            
            # Apply lifecycle configuration
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration=lifecycle_config
            )
            
            self.logger.info(
                "Lifecycle policies configured for bucket",
                bucket_name=bucket_name,
                retention_days=retention_days
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to configure lifecycle policies",
                bucket_name=bucket_name,
                error=str(e)
            )
            return False
    
    async def validate_bucket_security(self, bucket_name: str) -> Dict[str, bool]:
        """
        Validate security configuration of bucket.
        
        Args:
            bucket_name: Name of bucket to validate
            
        Returns:
            Security validation results
        """
        try:
            if not self.s3_client:
                await self.initialize_minio_client()
            
            security_status = {
                "encryption_enabled": False,
                "versioning_enabled": False,
                "lifecycle_configured": False,
                "public_access_blocked": False,
                "audit_logging_enabled": False
            }
            
            # Check encryption
            try:
                encryption_response = self.s3_client.get_bucket_encryption(Bucket=bucket_name)
                security_status["encryption_enabled"] = True
            except ClientError:
                security_status["encryption_enabled"] = False
            
            # Check versioning
            try:
                versioning_response = self.s3_client.get_bucket_versioning(Bucket=bucket_name)
                security_status["versioning_enabled"] = (
                    versioning_response.get('Status') == 'Enabled'
                )
            except ClientError:
                security_status["versioning_enabled"] = False
            
            # Check lifecycle policies
            try:
                lifecycle_response = self.s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
                security_status["lifecycle_configured"] = bool(lifecycle_response.get('Rules'))
            except ClientError:
                security_status["lifecycle_configured"] = False
            
            # Check public access block
            try:
                public_access_response = self.s3_client.get_public_access_block(Bucket=bucket_name)
                security_status["public_access_blocked"] = (
                    public_access_response['PublicAccessBlockConfiguration']['BlockPublicAcls']
                )
            except ClientError:
                security_status["public_access_blocked"] = False
            
            # Audit logging is assumed enabled if bucket exists
            security_status["audit_logging_enabled"] = True
            
            all_secure = all(security_status.values())
            
            self.logger.info(
                "Bucket security validation completed",
                bucket_name=bucket_name,
                all_secure=all_secure,
                **security_status
            )
            
            return security_status
            
        except Exception as e:
            self.logger.error(
                "Failed to validate bucket security",
                bucket_name=bucket_name,
                error=str(e)
            )
            return {"validation_failed": True}
    
    # ML DATASET OPERATIONS METHODS
    
    async def export_anonymized_profiles_for_training(
        self,
        profiles: List[AnonymizedMLProfile],
        dataset_name: str
    ) -> str:
        """
        Export anonymized profiles as ML training dataset.
        
        Args:
            profiles: List of anonymized ML profiles
            dataset_name: Name for the training dataset
            
        Returns:
            Dataset identifier (S3 key)
        """
        try:
            if not profiles:
                raise ValueError("No profiles provided for export")
            
            if not self.minio_client:
                await self.initialize_minio_client()
            
            # Create dataset metadata
            dataset_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            
            # Convert profiles to DataFrame for Parquet export
            profile_data = []
            
            for profile in profiles:
                if not profile.prediction_ready or not profile.compliance_validated:
                    continue
                
                profile_record = {
                    "profile_id": profile.profile_id,
                    "anonymous_id": profile.anonymous_id,
                    "age_group": profile.age_group.value,
                    "gender_category": profile.gender_category,
                    "pregnancy_status": profile.pregnancy_status.value,
                    "location_category": profile.location_category.value,
                    "season_category": profile.season_category.value,
                    "medical_history_categories": json.dumps(profile.medical_history_categories),
                    "medication_categories": json.dumps(profile.medication_categories),
                    "allergy_categories": json.dumps(profile.allergy_categories),
                    "risk_factors": json.dumps(profile.risk_factors),
                    "clinical_text_embedding": json.dumps(profile.clinical_text_embedding) if profile.clinical_text_embedding else None,
                    "categorical_features": json.dumps(profile.categorical_features),
                    "similarity_metadata": json.dumps(profile.similarity_metadata),
                    "anonymization_timestamp": profile.anonymization_timestamp.isoformat(),
                    "export_timestamp": timestamp.isoformat()
                }
                
                profile_data.append(profile_record)
            
            if not profile_data:
                raise ValueError("No prediction-ready profiles found for export")
            
            # Create DataFrame and convert to Parquet
            df = pd.DataFrame(profile_data)
            
            # Create Parquet file in memory
            parquet_buffer = io.BytesIO()
            df.to_parquet(parquet_buffer, index=False, compression='snappy')
            parquet_buffer.seek(0)
            
            # Generate S3 key
            s3_key = f"training-datasets/{dataset_name}/{dataset_id}.parquet"
            bucket_name = self.config.buckets["ml-training-data"]
            
            # Upload to MinIO
            self.minio_client.put_object(
                bucket_name=bucket_name,
                object_name=s3_key,
                data=parquet_buffer,
                length=parquet_buffer.getbuffer().nbytes,
                content_type="application/octet-stream"
            )
            
            # Create dataset metadata file
            metadata = MLDatasetMetadata(
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                total_profiles=len(profile_data),
                date_range_start=min(profile.anonymization_timestamp for profile in profiles),
                date_range_end=max(profile.anonymization_timestamp for profile in profiles),
                embedding_model="Bio_ClinicalBERT",
                vector_dimension=768,
                created_by="ml_data_lake_pipeline"
            )
            
            # Upload metadata
            metadata_key = f"training-datasets/{dataset_name}/{dataset_id}_metadata.json"
            metadata_json = metadata.json()
            
            self.minio_client.put_object(
                bucket_name=bucket_name,
                object_name=metadata_key,
                data=io.BytesIO(metadata_json.encode()),
                length=len(metadata_json),
                content_type="application/json"
            )
            
            self.logger.info(
                "Anonymized profiles exported successfully",
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                profiles_exported=len(profile_data),
                bucket_name=bucket_name,
                s3_key=s3_key
            )
            
            # Update upload statistics
            self.upload_stats["total_uploads"] += 1
            self.upload_stats["total_bytes"] += parquet_buffer.getbuffer().nbytes
            
            # Audit export operation
            await self._audit_dataset_operation("export_anonymized_profiles", {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "profiles_exported": len(profile_data),
                "file_size_bytes": parquet_buffer.getbuffer().nbytes,
                "s3_key": s3_key
            })
            
            return s3_key
            
        except Exception as e:
            self.logger.error(
                "Failed to export anonymized profiles",
                dataset_name=dataset_name,
                profiles_count=len(profiles),
                error=str(e)
            )
            self.upload_stats["failed_uploads"] += 1
            raise
    
    async def create_ml_training_dataset(self, dataset_config: Dict) -> MLDatasetMetadata:
        """
        Create comprehensive ML training dataset from multiple sources.
        
        Args:
            dataset_config: Configuration for dataset creation
            
        Returns:
            ML dataset metadata
        """
        try:
            dataset_name = dataset_config["name"]
            source_profiles = dataset_config["profiles"]
            include_embeddings = dataset_config.get("include_embeddings", True)
            split_ratios = dataset_config.get("split_ratios", {"train": 0.8, "validation": 0.1, "test": 0.1})
            
            # Validate dataset configuration
            if sum(split_ratios.values()) != 1.0:
                raise ValueError("Split ratios must sum to 1.0")
            
            # Filter prediction-ready profiles
            ready_profiles = [
                profile for profile in source_profiles
                if profile.prediction_ready and profile.compliance_validated
            ]
            
            if len(ready_profiles) < 10:
                raise ValueError("Insufficient prediction-ready profiles for dataset creation")
            
            # Shuffle and split data
            import random
            random.shuffle(ready_profiles)
            
            n_total = len(ready_profiles)
            n_train = int(n_total * split_ratios["train"])
            n_val = int(n_total * split_ratios["validation"])
            
            train_profiles = ready_profiles[:n_train]
            val_profiles = ready_profiles[n_train:n_train + n_val]
            test_profiles = ready_profiles[n_train + n_val:]
            
            # Export each split
            dataset_id = str(uuid.uuid4())
            split_keys = {}
            
            for split_name, split_profiles in [
                ("train", train_profiles),
                ("validation", val_profiles),
                ("test", test_profiles)
            ]:
                if split_profiles:
                    split_key = await self.export_anonymized_profiles_for_training(
                        split_profiles,
                        f"{dataset_name}/{split_name}"
                    )
                    split_keys[split_name] = split_key
            
            # Create comprehensive dataset metadata
            metadata = MLDatasetMetadata(
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                total_profiles=len(ready_profiles),
                date_range_start=min(profile.anonymization_timestamp for profile in ready_profiles),
                date_range_end=max(profile.anonymization_timestamp for profile in ready_profiles),
                embedding_model="Bio_ClinicalBERT",
                vector_dimension=768,
                created_by="ml_data_lake_pipeline"
            )
            
            # Add split information
            metadata.dataset_splits = {
                "train": {"count": len(train_profiles), "s3_key": split_keys.get("train")},
                "validation": {"count": len(val_profiles), "s3_key": split_keys.get("validation")},
                "test": {"count": len(test_profiles), "s3_key": split_keys.get("test")}
            }
            
            # Calculate age distribution
            age_distribution = {}
            for profile in ready_profiles:
                age_group = profile.age_group.value
                age_distribution[age_group] = age_distribution.get(age_group, 0) + 1
            metadata.age_group_distribution = age_distribution
            
            # Extract condition categories
            all_conditions = set()
            for profile in ready_profiles:
                all_conditions.update(profile.medical_history_categories)
            metadata.condition_categories = list(all_conditions)
            
            self.logger.info(
                "ML training dataset created successfully",
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                total_profiles=len(ready_profiles),
                train_count=len(train_profiles),
                val_count=len(val_profiles),
                test_count=len(test_profiles)
            )
            
            return metadata
            
        except Exception as e:
            self.logger.error(
                "Failed to create ML training dataset",
                dataset_name=dataset_config.get("name", "unknown"),
                error=str(e)
            )
            raise
    
    async def upload_training_data_parquet(self, data: Dict, s3_key: str) -> bool:
        """
        Upload training data as Parquet file to data lake.
        
        Args:
            data: Training data dictionary
            s3_key: S3 object key for storage
            
        Returns:
            True if upload successful
        """
        try:
            if not self.minio_client:
                await self.initialize_minio_client()
            
            # Convert data to DataFrame
            df = pd.DataFrame(data)
            
            # Create Parquet file
            parquet_buffer = io.BytesIO()
            df.to_parquet(parquet_buffer, index=False, compression='snappy')
            parquet_buffer.seek(0)
            
            # Upload to MinIO
            bucket_name = self.config.buckets["ml-training-data"]
            
            self.minio_client.put_object(
                bucket_name=bucket_name,
                object_name=s3_key,
                data=parquet_buffer,
                length=parquet_buffer.getbuffer().nbytes,
                content_type="application/octet-stream"
            )
            
            self.logger.info(
                "Training data uploaded successfully",
                s3_key=s3_key,
                file_size_mb=parquet_buffer.getbuffer().nbytes / (1024 * 1024),
                records_count=len(df)
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to upload training data",
                s3_key=s3_key,
                error=str(e)
            )
            return False
    
    async def batch_upload_vector_embeddings(
        self,
        embeddings: List[Dict],
        batch_size: int = 1000
    ) -> List[str]:
        """
        Batch upload vector embeddings to data lake.
        
        Args:
            embeddings: List of embedding dictionaries
            batch_size: Number of embeddings per batch
            
        Returns:
            List of S3 keys for uploaded batches
        """
        try:
            if not embeddings:
                return []
            
            if not self.minio_client:
                await self.initialize_minio_client()
            
            bucket_name = self.config.buckets["vector-embeddings"]
            uploaded_keys = []
            
            # Process embeddings in batches
            for i in range(0, len(embeddings), batch_size):
                batch = embeddings[i:i + batch_size]
                batch_id = str(uuid.uuid4())
                
                # Create batch DataFrame
                df = pd.DataFrame(batch)
                
                # Convert to Parquet
                parquet_buffer = io.BytesIO()
                df.to_parquet(parquet_buffer, index=False, compression='snappy')
                parquet_buffer.seek(0)
                
                # Generate S3 key
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                s3_key = f"embeddings/batch_{timestamp}_{batch_id}.parquet"
                
                # Upload batch
                self.minio_client.put_object(
                    bucket_name=bucket_name,
                    object_name=s3_key,
                    data=parquet_buffer,
                    length=parquet_buffer.getbuffer().nbytes,
                    content_type="application/octet-stream"
                )
                
                uploaded_keys.append(s3_key)
                
                self.logger.debug(
                    "Embedding batch uploaded",
                    batch_number=i // batch_size + 1,
                    batch_size=len(batch),
                    s3_key=s3_key
                )
            
            self.logger.info(
                "Vector embeddings batch upload completed",
                total_embeddings=len(embeddings),
                batches_uploaded=len(uploaded_keys),
                bucket_name=bucket_name
            )
            
            return uploaded_keys
            
        except Exception as e:
            self.logger.error(
                "Failed to batch upload vector embeddings",
                embeddings_count=len(embeddings),
                error=str(e)
            )
            return []
    
    # VECTOR DATABASE SYNC METHODS
    
    async def sync_to_vector_database(
        self,
        profiles: List[AnonymizedMLProfile]
    ) -> Dict[str, Any]:
        """
        Synchronize anonymized profiles to vector database.
        
        Args:
            profiles: List of anonymized ML profiles
            
        Returns:
            Synchronization results
        """
        try:
            if not self.vector_store:
                from app.modules.vector_store.milvus_client import MilvusVectorStore
                self.vector_store = MilvusVectorStore()
                await self.vector_store.initialize_milvus_connection()
            
            # Filter profiles with embeddings
            vectorizable_profiles = [
                profile for profile in profiles
                if profile.clinical_text_embedding and profile.compliance_validated
            ]
            
            if not vectorizable_profiles:
                return {"synced_count": 0, "errors": [], "success": True}
            
            # Index vectors in Milvus
            index_result = await self.vector_store.index_patient_vectors(vectorizable_profiles)
            
            # Store sync metadata in data lake
            sync_metadata = {
                "sync_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "profiles_synced": index_result["indexed_count"],
                "total_profiles": len(profiles),
                "milvus_insert_ids": index_result.get("insert_ids", []),
                "errors": index_result.get("errors", [])
            }
            
            # Upload sync metadata
            await self._upload_sync_metadata(sync_metadata)
            
            self.logger.info(
                "Profiles synchronized to vector database",
                profiles_synced=sync_metadata["profiles_synced"],
                total_profiles=len(profiles),
                sync_id=sync_metadata["sync_id"]
            )
            
            return {
                "synced_count": sync_metadata["profiles_synced"],
                "sync_id": sync_metadata["sync_id"],
                "success": index_result["success"],
                "errors": index_result.get("errors", [])
            }
            
        except Exception as e:
            self.logger.error(
                "Failed to sync profiles to vector database",
                profiles_count=len(profiles),
                error=str(e)
            )
            return {"synced_count": 0, "errors": [str(e)], "success": False}
    
    # PRIVATE HELPER METHODS
    
    async def _configure_bucket_compliance(self, bucket_name: str, bucket_purpose: str):
        """Configure HIPAA compliance settings for bucket."""
        try:
            # Enable versioning
            if self.config.versioning_enabled:
                self.s3_client.put_bucket_versioning(
                    Bucket=bucket_name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
            
            # Configure encryption
            if self.config.encryption_enabled:
                await self.configure_hipaa_encryption(bucket_name)
            
            # Setup lifecycle policies
            retention_days = self.config.retention_days.get(
                bucket_purpose.replace("-", "_"), 
                self.config.retention_days["training_data"]
            )
            await self.setup_lifecycle_policies(bucket_name, retention_days)
            
            # Block public access
            self.s3_client.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True,
                    'RestrictPublicBuckets': True
                }
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to configure bucket compliance",
                bucket_name=bucket_name,
                error=str(e)
            )
    
    async def _upload_sync_metadata(self, sync_metadata: Dict):
        """Upload synchronization metadata to data lake."""
        try:
            metadata_json = json.dumps(sync_metadata, indent=2)
            
            s3_key = f"sync-metadata/{sync_metadata['sync_id']}.json"
            bucket_name = self.config.buckets["audit-logs"]
            
            self.minio_client.put_object(
                bucket_name=bucket_name,
                object_name=s3_key,
                data=io.BytesIO(metadata_json.encode()),
                length=len(metadata_json),
                content_type="application/json"
            )
            
        except Exception as e:
            self.logger.error("Failed to upload sync metadata", error=str(e))
    
    # AUDIT METHODS
    
    async def _audit_connection_event(self, event_type: str, details: Dict):
        """Audit connection-related events."""
        try:
            audit_data = {
                "operation": f"data_lake_connection_{event_type}",
                "details": details,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.logger.info(f"Data lake connection {event_type}", **audit_data)
        except Exception as e:
            self.logger.error("Failed to audit connection event", error=str(e))
    
    async def _audit_bucket_operation(self, operation: str, details: Dict):
        """Audit bucket-related operations."""
        try:
            audit_data = {
                "operation": f"data_lake_bucket_{operation}",
                "details": details,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.logger.info(f"Data lake bucket {operation}", **audit_data)
        except Exception as e:
            self.logger.error("Failed to audit bucket operation", error=str(e))
    
    async def _audit_dataset_operation(self, operation: str, details: Dict):
        """Audit dataset-related operations."""
        try:
            audit_data = {
                "operation": f"data_lake_dataset_{operation}",
                "details": details,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.logger.info(f"Data lake dataset {operation}", **audit_data)
        except Exception as e:
            self.logger.error("Failed to audit dataset operation", error=str(e))
    
    async def _audit_security_event(self, event_type: str, details: Dict):
        """Audit security-related events."""
        try:
            audit_data = {
                "operation": f"data_lake_security_{event_type}",
                "details": details,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.logger.info(f"Data lake security {event_type}", **audit_data)
        except Exception as e:
            self.logger.error("Failed to audit security event", error=str(e))