"""
Prefect ETL Orchestrator for Healthcare ML Platform

Enterprise-grade Prefect integration for ML data processing pipelines with
healthcare-specific workflows, HIPAA compliance, and production monitoring.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
import structlog
from prefect import flow, task, get_run_logger
from prefect.client.orchestration import PrefectClient
from prefect.deployments import Deployment
from prefect.server.schemas.states import StateType
from prefect.blocks.system import Secret
from prefect.infrastructure import DockerContainer
from prefect.task_runners import SequentialTaskRunner, ConcurrentTaskRunner
import pandas as pd

from app.core.config import get_settings
from app.core.security import EncryptionService
from app.modules.audit_logger.service import AuditLogService
from app.modules.data_anonymization.ml_anonymizer import MLAnonymizationEngine
from app.modules.data_anonymization.schemas import AnonymizedMLProfile, ComplianceValidationResult
from app.modules.ml_prediction.clinical_bert import ClinicalBERTService
from app.modules.vector_store.milvus_client import MilvusVectorStore
from app.modules.data_lake.minio_pipeline import MLDataLakePipeline

logger = structlog.get_logger(__name__)

class PrefectConfig:
    """Configuration for Prefect ML orchestrator."""
    
    def __init__(self):
        self.api_url = "http://localhost:4200/api"
        self.deployment_name = "healthcare-ml-pipeline"
        self.work_pool_name = "healthcare-ml-pool"
        
        # Healthcare-specific settings
        self.max_concurrent_tasks = 5
        self.task_timeout_minutes = 30
        self.retry_attempts = 3
        self.pipeline_timeout_hours = 6
        
        # HIPAA compliance
        self.audit_all_operations = True
        self.encrypt_intermediate_data = True
        self.enable_data_lineage = True
        
        # Performance settings
        self.batch_size = 1000
        self.prefetch_factor = 2
        self.memory_limit_gb = 8

class PrefectMLOrchestrator:
    """
    Production-ready Prefect orchestrator for healthcare ML pipelines.
    
    Provides enterprise-grade ETL orchestration with healthcare-specific workflows,
    HIPAA compliance monitoring, and comprehensive error handling.
    """
    
    def __init__(self, config: Optional[PrefectConfig] = None):
        """
        Initialize Prefect ML orchestrator.
        
        Args:
            config: Prefect configuration
        """
        self.config = config or PrefectConfig()
        self.settings = get_settings()
        self.logger = logger.bind(component="PrefectMLOrchestrator")
        
        # Initialize services
        self.encryption_service = EncryptionService()
        self.audit_service = AuditLogService()
        
        # ML services
        self.ml_anonymizer = MLAnonymizationEngine()
        self.clinical_bert = ClinicalBERTService()
        self.vector_store = MilvusVectorStore()
        self.data_lake = MLDataLakePipeline()
        
        # Prefect client
        self.client: Optional[PrefectClient] = None
        
        # Pipeline state tracking
        self.active_flows = {}
        self.pipeline_metrics = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "average_duration_minutes": 0.0
        }
        
        self.logger.info(
            "Prefect ML orchestrator initialized",
            api_url=self.config.api_url,
            max_concurrent_tasks=self.config.max_concurrent_tasks,
            audit_enabled=self.config.audit_all_operations
        )
    
    # PIPELINE CONFIGURATION METHODS
    
    async def initialize_prefect_client(self, api_url: Optional[str] = None) -> None:
        """
        Initialize Prefect client connection.
        
        Args:
            api_url: Prefect API URL (optional override)
        """
        try:
            api_url = api_url or self.config.api_url
            
            self.client = PrefectClient(api=api_url)
            
            # Test connection
            server_version = await self.client.hello()
            
            self.logger.info(
                "Prefect client initialized successfully",
                api_url=api_url,
                server_version=server_version
            )
            
            # Audit client initialization
            await self._audit_pipeline_event("client_initialized", {
                "api_url": api_url,
                "server_version": server_version
            })
            
        except Exception as e:
            self.logger.error(
                "Failed to initialize Prefect client",
                api_url=api_url,
                error=str(e)
            )
            raise
    
    async def create_ml_deployment_pool(self) -> str:
        """
        Create ML deployment pool for healthcare workflows.
        
        Returns:
            Deployment pool identifier
        """
        try:
            if not self.client:
                await self.initialize_prefect_client()
            
            # Create work pool for healthcare ML tasks
            work_pool_config = {
                "name": self.config.work_pool_name,
                "type": "docker",
                "description": "Healthcare ML pipeline work pool",
                "concurrency_limit": self.config.max_concurrent_tasks
            }
            
            # Register work pool
            work_pool = await self.client.create_work_pool(**work_pool_config)
            
            self.logger.info(
                "ML deployment pool created",
                pool_name=self.config.work_pool_name,
                pool_id=work_pool.id,
                concurrency_limit=self.config.max_concurrent_tasks
            )
            
            return str(work_pool.id)
            
        except Exception as e:
            self.logger.error(
                "Failed to create ML deployment pool",
                pool_name=self.config.work_pool_name,
                error=str(e)
            )
            raise
    
    async def register_healthcare_flows(self) -> Dict[str, str]:
        """
        Register healthcare-specific Prefect flows.
        
        Returns:
            Dictionary of flow names to deployment IDs
        """
        try:
            registered_flows = {}
            
            # Define healthcare flows
            healthcare_flows = [
                {
                    "name": "ml-anonymization-pipeline",
                    "flow": self._create_anonymization_flow(),
                    "description": "ML-ready patient data anonymization pipeline"
                },
                {
                    "name": "clinical-bert-embedding-pipeline", 
                    "flow": self._create_embedding_flow(),
                    "description": "Clinical BERT embedding generation pipeline"
                },
                {
                    "name": "vector-database-sync-pipeline",
                    "flow": self._create_vector_sync_flow(),
                    "description": "Vector database synchronization pipeline"
                },
                {
                    "name": "ml-training-dataset-pipeline",
                    "flow": self._create_dataset_preparation_flow(),
                    "description": "ML training dataset preparation pipeline"
                },
                {
                    "name": "compliance-validation-pipeline",
                    "flow": self._create_compliance_flow(),
                    "description": "HIPAA/GDPR compliance validation pipeline"
                }
            ]
            
            # Register each flow
            for flow_config in healthcare_flows:
                deployment = Deployment.build_from_flow(
                    flow=flow_config["flow"],
                    name=flow_config["name"],
                    work_pool_name=self.config.work_pool_name,
                    description=flow_config["description"],
                    tags=["healthcare", "ml", "hipaa"]
                )
                
                deployment_id = await deployment.apply()
                registered_flows[flow_config["name"]] = str(deployment_id)
                
                self.logger.info(
                    "Healthcare flow registered",
                    flow_name=flow_config["name"],
                    deployment_id=deployment_id
                )
            
            # Audit flow registration
            await self._audit_pipeline_event("flows_registered", {
                "flows_count": len(registered_flows),
                "flow_names": list(registered_flows.keys())
            })
            
            return registered_flows
            
        except Exception as e:
            self.logger.error(
                "Failed to register healthcare flows",
                error=str(e)
            )
            raise
    
    async def configure_secure_storage(self) -> bool:
        """
        Configure secure storage for pipeline secrets and data.
        
        Returns:
            True if storage configured successfully
        """
        try:
            # Create encrypted storage blocks for sensitive data
            storage_blocks = [
                {
                    "name": "milvus-credentials",
                    "type": "secret",
                    "value": {
                        "host": self.vector_store.config.host,
                        "username": self.vector_store.config.username,
                        "password": self.vector_store.config.password
                    }
                },
                {
                    "name": "minio-credentials",
                    "type": "secret", 
                    "value": {
                        "endpoint": self.data_lake.config.endpoint,
                        "access_key": self.data_lake.config.access_key,
                        "secret_key": self.data_lake.config.secret_key
                    }
                }
            ]
            
            # Register storage blocks
            for block_config in storage_blocks:
                secret_block = Secret(value=block_config["value"])
                await secret_block.save(name=block_config["name"])
            
            self.logger.info(
                "Secure storage configured",
                blocks_created=len(storage_blocks)
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to configure secure storage",
                error=str(e)
            )
            return False
    
    async def setup_flow_monitoring(self) -> Dict[str, Any]:
        """
        Setup monitoring for pipeline flows.
        
        Returns:
            Monitoring configuration
        """
        try:
            monitoring_config = {
                "enable_metrics": True,
                "enable_logging": True,
                "enable_alerts": True,
                "metrics_retention_days": 90,
                "log_level": "INFO",
                "alert_thresholds": {
                    "failure_rate": 0.05,  # 5% failure rate threshold
                    "average_duration_minutes": 60,  # 1 hour duration threshold
                    "memory_usage_gb": self.config.memory_limit_gb * 0.8
                }
            }
            
            self.logger.info(
                "Flow monitoring configured",
                **monitoring_config
            )
            
            return monitoring_config
            
        except Exception as e:
            self.logger.error(
                "Failed to setup flow monitoring",
                error=str(e)
            )
            return {}
    
    # ML DATA PIPELINE METHODS
    
    async def run_anonymization_pipeline(self, patient_ids: List[str]) -> Dict[str, Any]:
        """
        Execute ML-ready patient data anonymization pipeline.
        
        Args:
            patient_ids: List of patient IDs to anonymize
            
        Returns:
            Pipeline execution results
        """
        try:
            flow_run_id = str(uuid.uuid4())
            start_time = datetime.utcnow()
            
            self.logger.info(
                "Starting anonymization pipeline",
                flow_run_id=flow_run_id,
                patient_count=len(patient_ids)
            )
            
            # Execute anonymization flow
            anonymization_flow = self._create_anonymization_flow()
            
            flow_result = await anonymization_flow(
                patient_ids=patient_ids,
                flow_run_id=flow_run_id
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update pipeline metrics
            self.pipeline_metrics["total_runs"] += 1
            if flow_result["success"]:
                self.pipeline_metrics["successful_runs"] += 1
            else:
                self.pipeline_metrics["failed_runs"] += 1
            
            # Update average duration
            self.pipeline_metrics["average_duration_minutes"] = (
                (self.pipeline_metrics["average_duration_minutes"] * (self.pipeline_metrics["total_runs"] - 1) + 
                 processing_time / 60) / self.pipeline_metrics["total_runs"]
            )
            
            result = {
                "flow_run_id": flow_run_id,
                "success": flow_result["success"],
                "anonymized_profiles": flow_result.get("anonymized_profiles", []),
                "processing_time_seconds": processing_time,
                "pipeline_metrics": self.pipeline_metrics
            }
            
            self.logger.info(
                "Anonymization pipeline completed",
                flow_run_id=flow_run_id,
                success=result["success"],
                profiles_created=len(result["anonymized_profiles"]),
                processing_time_seconds=processing_time
            )
            
            # Audit pipeline execution
            await self._audit_pipeline_execution("anonymization", flow_run_id, result)
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Anonymization pipeline failed",
                patient_count=len(patient_ids),
                error=str(e)
            )
            self.pipeline_metrics["failed_runs"] += 1
            return {
                "flow_run_id": flow_run_id if 'flow_run_id' in locals() else None,
                "success": False,
                "error": str(e)
            }
    
    async def execute_vector_embedding_pipeline(
        self,
        profiles: List[AnonymizedMLProfile]
    ) -> Dict[str, Any]:
        """
        Execute Clinical BERT embedding generation pipeline.
        
        Args:
            profiles: List of anonymized ML profiles
            
        Returns:
            Embedding pipeline results
        """
        try:
            flow_run_id = str(uuid.uuid4())
            start_time = datetime.utcnow()
            
            self.logger.info(
                "Starting vector embedding pipeline",
                flow_run_id=flow_run_id,
                profiles_count=len(profiles)
            )
            
            # Execute embedding flow
            embedding_flow = self._create_embedding_flow()
            
            flow_result = await embedding_flow(
                profiles=profiles,
                flow_run_id=flow_run_id
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = {
                "flow_run_id": flow_run_id,
                "success": flow_result["success"],
                "embedded_profiles": flow_result.get("embedded_profiles", []),
                "processing_time_seconds": processing_time
            }
            
            self.logger.info(
                "Vector embedding pipeline completed",
                flow_run_id=flow_run_id,
                success=result["success"],
                embedded_count=len(result["embedded_profiles"]),
                processing_time_seconds=processing_time
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Vector embedding pipeline failed",
                profiles_count=len(profiles),
                error=str(e)
            )
            return {
                "flow_run_id": flow_run_id if 'flow_run_id' in locals() else None,
                "success": False,
                "error": str(e)
            }
    
    async def run_ml_training_data_preparation(self, dataset_config: Dict) -> MLDatasetMetadata:
        """
        Execute ML training data preparation pipeline.
        
        Args:
            dataset_config: Configuration for dataset creation
            
        Returns:
            ML dataset metadata
        """
        try:
            flow_run_id = str(uuid.uuid4())
            
            self.logger.info(
                "Starting ML training data preparation pipeline",
                flow_run_id=flow_run_id,
                dataset_name=dataset_config.get("name", "unnamed")
            )
            
            # Execute dataset preparation flow
            dataset_flow = self._create_dataset_preparation_flow()
            
            dataset_metadata = await dataset_flow(
                dataset_config=dataset_config,
                flow_run_id=flow_run_id
            )
            
            self.logger.info(
                "ML training data preparation completed",
                flow_run_id=flow_run_id,
                dataset_id=dataset_metadata.dataset_id,
                total_profiles=dataset_metadata.total_profiles
            )
            
            return dataset_metadata
            
        except Exception as e:
            self.logger.error(
                "ML training data preparation failed",
                dataset_name=dataset_config.get("name", "unnamed"),
                error=str(e)
            )
            raise
    
    # FLOW CREATION METHODS (Private)
    
    def _create_anonymization_flow(self):
        """Create anonymization pipeline flow."""
        
        @task(name="load-patient-data", retries=self.config.retry_attempts)
        async def load_patient_data(patient_ids: List[str]) -> List[Dict[str, Any]]:
            """Load patient data for anonymization."""
            # In production, this would load from the healthcare database
            # For now, return mock data structure
            patient_data = []
            for patient_id in patient_ids:
                patient_data.append({
                    "id": patient_id,
                    "age": 35,
                    "gender": "female",
                    "medical_history": ["asthma", "hypertension"],
                    "location": "Boston, MA"
                })
            return patient_data
        
        @task(name="anonymize-profiles", retries=self.config.retry_attempts)
        async def anonymize_profiles(patient_data: List[Dict[str, Any]]) -> List[AnonymizedMLProfile]:
            """Anonymize patient data for ML use."""
            profiles = []
            for data in patient_data:
                profile = await self.ml_anonymizer.create_ml_profile(data)
                if profile and profile.compliance_validated:
                    profiles.append(profile)
            return profiles
        
        @task(name="validate-compliance", retries=self.config.retry_attempts)
        async def validate_compliance(profiles: List[AnonymizedMLProfile]) -> List[AnonymizedMLProfile]:
            """Validate HIPAA compliance of anonymized profiles."""
            validated_profiles = []
            for profile in profiles:
                validation_result = await self.ml_anonymizer.compliance_validator.comprehensive_compliance_check(profile)
                if validation_result.overall_compliance_score >= 0.9:
                    validated_profiles.append(profile)
            return validated_profiles
        
        @flow(
            name="ml-anonymization-pipeline",
            description="ML-ready patient data anonymization with HIPAA compliance",
            task_runner=ConcurrentTaskRunner()
        )
        async def anonymization_pipeline(patient_ids: List[str], flow_run_id: str) -> Dict[str, Any]:
            """Main anonymization pipeline flow."""
            run_logger = get_run_logger()
            run_logger.info(f"Starting anonymization pipeline: {flow_run_id}")
            
            try:
                # Load patient data
                patient_data = await load_patient_data(patient_ids)
                
                # Anonymize profiles
                anonymized_profiles = await anonymize_profiles(patient_data)
                
                # Validate compliance
                validated_profiles = await validate_compliance(anonymized_profiles)
                
                run_logger.info(
                    f"Anonymization pipeline completed successfully: {flow_run_id}",
                    extra={
                        "patients_processed": len(patient_data),
                        "profiles_created": len(validated_profiles)
                    }
                )
                
                return {
                    "success": True,
                    "anonymized_profiles": validated_profiles
                }
                
            except Exception as e:
                run_logger.error(f"Anonymization pipeline failed: {flow_run_id}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e)
                }
        
        return anonymization_pipeline
    
    def _create_embedding_flow(self):
        """Create Clinical BERT embedding pipeline flow."""
        
        @task(name="initialize-clinical-bert", retries=self.config.retry_attempts)
        async def initialize_clinical_bert() -> bool:
            """Initialize Clinical BERT model."""
            return await self.clinical_bert.initialize_model()
        
        @task(name="generate-embeddings", retries=self.config.retry_attempts)
        async def generate_embeddings(profiles: List[AnonymizedMLProfile]) -> List[AnonymizedMLProfile]:
            """Generate Clinical BERT embeddings for profiles."""
            embedded_profiles = []
            
            # Process in batches for efficiency
            batch_size = self.config.batch_size
            for i in range(0, len(profiles), batch_size):
                batch = profiles[i:i + batch_size]
                
                for profile in batch:
                    # Mock clinical text for embedding
                    clinical_text = f"Patient with {', '.join(profile.medical_history_categories)}"
                    
                    # Update profile with embedding
                    updated_profile = await self.clinical_bert.update_ml_profile_with_embedding(
                        profile, clinical_text
                    )
                    embedded_profiles.append(updated_profile)
            
            return embedded_profiles
        
        @flow(
            name="clinical-bert-embedding-pipeline",
            description="Clinical BERT embedding generation for ML profiles",
            task_runner=ConcurrentTaskRunner()
        )
        async def embedding_pipeline(profiles: List[AnonymizedMLProfile], flow_run_id: str) -> Dict[str, Any]:
            """Main embedding pipeline flow."""
            run_logger = get_run_logger()
            run_logger.info(f"Starting embedding pipeline: {flow_run_id}")
            
            try:
                # Initialize Clinical BERT
                bert_initialized = await initialize_clinical_bert()
                if not bert_initialized:
                    raise RuntimeError("Failed to initialize Clinical BERT model")
                
                # Generate embeddings
                embedded_profiles = await generate_embeddings(profiles)
                
                run_logger.info(
                    f"Embedding pipeline completed successfully: {flow_run_id}",
                    extra={
                        "profiles_processed": len(profiles),
                        "embeddings_generated": len(embedded_profiles)
                    }
                )
                
                return {
                    "success": True,
                    "embedded_profiles": embedded_profiles
                }
                
            except Exception as e:
                run_logger.error(f"Embedding pipeline failed: {flow_run_id}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e)
                }
        
        return embedding_pipeline
    
    def _create_vector_sync_flow(self):
        """Create vector database synchronization flow."""
        
        @task(name="sync-to-milvus", retries=self.config.retry_attempts)
        async def sync_to_milvus(profiles: List[AnonymizedMLProfile]) -> Dict[str, Any]:
            """Synchronize profiles to Milvus vector database."""
            return await self.data_lake.sync_to_vector_database(profiles)
        
        @flow(
            name="vector-database-sync-pipeline",
            description="Synchronize ML profiles to vector database",
            task_runner=SequentialTaskRunner()
        )
        async def vector_sync_pipeline(profiles: List[AnonymizedMLProfile], flow_run_id: str) -> Dict[str, Any]:
            """Main vector synchronization pipeline flow."""
            run_logger = get_run_logger()
            run_logger.info(f"Starting vector sync pipeline: {flow_run_id}")
            
            try:
                sync_result = await sync_to_milvus(profiles)
                
                run_logger.info(
                    f"Vector sync pipeline completed: {flow_run_id}",
                    extra=sync_result
                )
                
                return sync_result
                
            except Exception as e:
                run_logger.error(f"Vector sync pipeline failed: {flow_run_id}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e)
                }
        
        return vector_sync_pipeline
    
    def _create_dataset_preparation_flow(self):
        """Create ML dataset preparation flow."""
        
        @task(name="prepare-training-dataset", retries=self.config.retry_attempts)
        async def prepare_training_dataset(dataset_config: Dict) -> MLDatasetMetadata:
            """Prepare ML training dataset."""
            return await self.data_lake.create_ml_training_dataset(dataset_config)
        
        @flow(
            name="ml-training-dataset-pipeline",
            description="Prepare ML training datasets with compliance validation",
            task_runner=SequentialTaskRunner()
        )
        async def dataset_preparation_pipeline(dataset_config: Dict, flow_run_id: str) -> MLDatasetMetadata:
            """Main dataset preparation pipeline flow."""
            run_logger = get_run_logger()
            run_logger.info(f"Starting dataset preparation pipeline: {flow_run_id}")
            
            try:
                dataset_metadata = await prepare_training_dataset(dataset_config)
                
                run_logger.info(
                    f"Dataset preparation completed: {flow_run_id}",
                    extra={
                        "dataset_id": dataset_metadata.dataset_id,
                        "total_profiles": dataset_metadata.total_profiles
                    }
                )
                
                return dataset_metadata
                
            except Exception as e:
                run_logger.error(f"Dataset preparation failed: {flow_run_id}", exc_info=True)
                raise
        
        return dataset_preparation_pipeline
    
    def _create_compliance_flow(self):
        """Create compliance validation flow."""
        
        @task(name="validate-hipaa-compliance", retries=self.config.retry_attempts)
        async def validate_hipaa_compliance(profiles: List[AnonymizedMLProfile]) -> List[ComplianceValidationResult]:
            """Validate HIPAA compliance for profiles."""
            results = []
            for profile in profiles:
                result = await self.ml_anonymizer.compliance_validator.comprehensive_compliance_check(profile)
                results.append(result)
            return results
        
        @flow(
            name="compliance-validation-pipeline",
            description="HIPAA/GDPR compliance validation for ML data",
            task_runner=ConcurrentTaskRunner()
        )
        async def compliance_pipeline(profiles: List[AnonymizedMLProfile], flow_run_id: str) -> Dict[str, Any]:
            """Main compliance validation pipeline flow."""
            run_logger = get_run_logger()
            run_logger.info(f"Starting compliance validation pipeline: {flow_run_id}")
            
            try:
                validation_results = await validate_hipaa_compliance(profiles)
                
                compliant_count = sum(1 for result in validation_results if result.overall_compliance_score >= 0.9)
                
                run_logger.info(
                    f"Compliance validation completed: {flow_run_id}",
                    extra={
                        "profiles_validated": len(validation_results),
                        "compliant_profiles": compliant_count
                    }
                )
                
                return {
                    "success": True,
                    "validation_results": validation_results,
                    "compliance_rate": compliant_count / len(validation_results) if validation_results else 0.0
                }
                
            except Exception as e:
                run_logger.error(f"Compliance validation failed: {flow_run_id}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e)
                }
        
        return compliance_pipeline
    
    # AUDIT METHODS
    
    async def _audit_pipeline_event(self, event_type: str, details: Dict):
        """Audit pipeline-related events."""
        try:
            audit_data = {
                "operation": f"prefect_pipeline_{event_type}",
                "details": details,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.logger.info(f"Pipeline {event_type}", **audit_data)
        except Exception as e:
            self.logger.error("Failed to audit pipeline event", error=str(e))
    
    async def _audit_pipeline_execution(self, pipeline_type: str, flow_run_id: str, result: Dict):
        """Audit pipeline execution."""
        try:
            audit_data = {
                "operation": f"pipeline_execution_{pipeline_type}",
                "flow_run_id": flow_run_id,
                "success": result.get("success", False),
                "processing_time_seconds": result.get("processing_time_seconds", 0),
                "timestamp": datetime.utcnow().isoformat()
            }
            self.logger.info(f"Pipeline execution {pipeline_type}", **audit_data)
        except Exception as e:
            self.logger.error("Failed to audit pipeline execution", error=str(e))