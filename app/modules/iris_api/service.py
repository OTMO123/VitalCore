import asyncio
import json
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
import structlog

from app.core.config import get_settings
from app.core.database import get_db
from app.core.database_advanced import APIEndpoint, APICredential, APIRequest
from app.core.database_unified import Patient
from app.modules.healthcare_records.models import Immunization
from app.core.security import security_manager
from app.core.events.event_bus import get_event_bus, HealthcareEventBus
from app.core.events.definitions import (
    IRISConnectionEstablished,
    IRISDataSynchronized,
    IRISAPIError as IRISAPIErrorEvent
)
from app.modules.iris_api.client import IRISAPIClient, IRISAPIError, CircuitBreakerError
from app.modules.iris_api.schemas import (
    APIEndpointCreate, APIEndpointResponse, SyncRequest, SyncResult, 
    SyncStatus, HealthCheckResponse, HealthStatus
)

logger = structlog.get_logger()

class IRISIntegrationService:
    """Service for managing IRIS API integration."""
    
    def __init__(self, event_bus: Optional[HealthcareEventBus] = None):
        self.settings = get_settings()
        self._clients: Dict[str, IRISAPIClient] = {}
        self.event_bus = event_bus
    
    def _get_event_bus(self) -> HealthcareEventBus:
        """Get event bus, initializing if needed."""
        if self.event_bus is None:
            try:
                self.event_bus = get_event_bus()
            except RuntimeError:
                # Event bus not initialized yet, return None and handle gracefully
                return None
        return self.event_bus
    
    async def get_client(self, endpoint_id: str, db: AsyncSession) -> IRISAPIClient:
        """Get or create IRIS API client for endpoint."""
        if endpoint_id in self._clients:
            return self._clients[endpoint_id]
        
        # Load endpoint configuration
        result = await db.execute(
            select(APIEndpoint).where(APIEndpoint.id == endpoint_id)
        )
        endpoint = result.scalar_one_or_none()
        
        if not endpoint:
            raise ValueError(f"API endpoint {endpoint_id} not found")
        
        # Load credentials
        result = await db.execute(
            select(APICredential).where(
                and_(
                    APICredential.api_endpoint_id == endpoint.id,
                    APICredential.is_active == True
                )
            )
        )
        credentials = {cred.credential_name: cred.encrypted_value for cred in result.scalars()}
        
        # Decrypt credentials
        client_id = security_manager.decrypt_data(credentials.get("client_id", ""))
        client_secret = security_manager.decrypt_data(credentials.get("client_secret", ""))
        
        # Create and cache client
        client = IRISAPIClient(
            base_url=endpoint.base_url,
            client_id=client_id,
            client_secret=client_secret,
            auth_type=endpoint.auth_type
        )
        
        self._clients[endpoint_id] = client
        return client
    
    async def create_api_endpoint(self, endpoint_data: APIEndpointCreate, db: AsyncSession) -> APIEndpointResponse:
        """Create new API endpoint configuration."""
        try:
            endpoint = APIEndpoint(
                name=endpoint_data.name,
                base_url=endpoint_data.base_url,
                api_version=endpoint_data.api_version,
                auth_type=endpoint_data.auth_type,
                timeout_seconds=endpoint_data.timeout_seconds,
                retry_attempts=endpoint_data.retry_attempts,
                metadata=endpoint_data.metadata
            )
            
            db.add(endpoint)
            await db.commit()
            await db.refresh(endpoint)
            
            # Publish IRIS connection established event
            event_bus = self._get_event_bus()
            if event_bus:
                await event_bus.publish_event(
                    event_type="iris.connection_established",
                aggregate_id=str(endpoint.id),
                publisher="iris_api",
                data={
                    "endpoint_id": str(endpoint.id),
                    "endpoint_url": endpoint.base_url,
                    "connection_id": str(endpoint.id),
                    "authentication_method": endpoint.auth_type,
                    "api_version": endpoint.api_version,
                    "health_check_passed": True,
                    "capabilities_verified": False
                }
            )
            
            logger.info("API endpoint created", endpoint_id=endpoint.id, name=endpoint.name)
            
            return APIEndpointResponse(
                id=str(endpoint.id),
                name=endpoint.name,
                base_url=endpoint.base_url,
                api_version=endpoint.api_version,
                status=endpoint.status.value,
                auth_type=endpoint.auth_type,
                timeout_seconds=endpoint.timeout_seconds,
                retry_attempts=endpoint.retry_attempts,
                last_health_check_at=endpoint.last_health_check_at,
                last_health_check_status=endpoint.last_health_check_status,
                metadata=endpoint.metadata,
                created_at=endpoint.created_at
            )
            
        except Exception as e:
            await db.rollback()
            logger.error("Failed to create API endpoint", error=str(e))
            raise
    
    async def add_api_credentials(
        self, 
        endpoint_id: str, 
        credential_name: str, 
        credential_value: str, 
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """Add encrypted credentials for API endpoint."""
        try:
            # Encrypt the credential value
            encrypted_value = security_manager.encrypt_data(credential_value)
            
            credential = APICredential(
                api_endpoint_id=endpoint_id,
                credential_name=credential_name,
                encrypted_value=encrypted_value,
                created_by=user_id
            )
            
            db.add(credential)
            await db.commit()
            
            # Clear cached client to force recreation with new credentials
            if endpoint_id in self._clients:
                del self._clients[endpoint_id]
            
            await publish_data_event(
                EventType.DATA_CREATED,
                resource_type="api_credential",
                resource_id=str(credential.id),
                data={"endpoint_id": endpoint_id, "credential_name": credential_name}
            )
            
            logger.info("API credentials added", endpoint_id=endpoint_id, credential_name=credential_name)
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error("Failed to add API credentials", error=str(e))
            return False
    
    async def health_check(self, endpoint_id: Optional[str], db: AsyncSession) -> List[HealthCheckResponse]:
        """Perform health check on IRIS API endpoints."""
        results = []
        
        # Query endpoints to check
        if endpoint_id:
            result = await db.execute(
                select(APIEndpoint).where(APIEndpoint.id == endpoint_id)
            )
            endpoints = [result.scalar_one_or_none()]
            if not endpoints[0]:
                raise ValueError(f"Endpoint {endpoint_id} not found")
        else:
            result = await db.execute(
                select(APIEndpoint).where(APIEndpoint.status == "active")
            )
            endpoints = result.scalars().all()
        
        # Check each endpoint
        for endpoint in endpoints:
            try:
                client = await self.get_client(str(endpoint.id), db)
                
                start_time = datetime.utcnow()
                health_result = await client.health_check()
                check_duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Update endpoint health status
                await db.execute(
                    update(APIEndpoint)
                    .where(APIEndpoint.id == endpoint.id)
                    .values(
                        last_health_check_at=start_time,
                        last_health_check_status=health_result["status"] == HealthStatus.HEALTHY
                    )
                )
                
                results.append(HealthCheckResponse(
                    endpoint_id=str(endpoint.id),
                    endpoint_name=endpoint.name,
                    status=health_result["status"],
                    response_time_ms=health_result.get("response_time_ms", int(check_duration)),
                    last_check_at=start_time,
                    error_message=health_result.get("error"),
                    metadata=health_result.get("data", {})
                ))
                
                # Log health check success
                logger.info(
                    "IRIS health check successful",
                    endpoint_id=str(endpoint.id),
                    status=health_result["status"].value,
                    response_time_ms=int(check_duration)
                )
                
            except (IRISAPIError, CircuitBreakerError) as e:
                # API-specific errors
                results.append(HealthCheckResponse(
                    endpoint_id=str(endpoint.id),
                    endpoint_name=endpoint.name,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=None,
                    last_check_at=datetime.utcnow(),
                    error_message=str(e),
                    metadata={}
                ))
                
                # Publish IRIS API error event
                event_bus = self._get_event_bus()
                if event_bus:
                    await event_bus.publish_event(
                    event_type="iris.api_error",
                    aggregate_id=str(endpoint.id),
                    publisher="iris_api",
                    data={
                        "endpoint_id": str(endpoint.id),
                        "operation": "health_check",
                        "error_code": "HEALTH_CHECK_FAILED",
                        "error_message": str(e),
                        "error_type": type(e).__name__,
                        "response_status": 503,
                        "retry_count": 0,
                        "circuit_breaker_triggered": isinstance(e, CircuitBreakerError),
                        "service_degraded": True
                    }
                )
                
            except Exception as e:
                # Unexpected errors
                logger.error("Health check failed", endpoint_id=endpoint.id, error=str(e))
                results.append(HealthCheckResponse(
                    endpoint_id=str(endpoint.id),
                    endpoint_name=endpoint.name,
                    status=HealthStatus.UNKNOWN,
                    response_time_ms=None,
                    last_check_at=datetime.utcnow(),
                    error_message=f"Health check failed: {str(e)}",
                    metadata={}
                ))
        
        await db.commit()
        return results
    
    async def sync_patient_data(self, sync_request: SyncRequest, endpoint_id: str, db: AsyncSession) -> SyncResult:
        """Synchronize patient data from IRIS API."""
        sync_id = secrets.token_hex(8)
        start_time = datetime.utcnow()
        
        try:
            client = await self.get_client(endpoint_id, db)
            
            patients_processed = 0
            patients_updated = 0
            patients_failed = 0
            immunizations_processed = 0
            immunizations_updated = 0
            errors = []
            
            # Determine which patients to sync
            if sync_request.patient_ids:
                patient_ids_to_sync = sync_request.patient_ids
            else:
                # Get all patients that need syncing
                if sync_request.sync_type == "full" or sync_request.force_full_sync:
                    result = await db.execute(select(Patient))
                    patients = result.scalars().all()
                    patient_ids_to_sync = [p.external_id for p in patients if p.external_id]
                else:
                    # Incremental sync - patients updated in last 24 hours
                    cutoff_time = datetime.utcnow() - timedelta(hours=24)
                    result = await db.execute(
                        select(Patient).where(Patient.iris_last_sync_at < cutoff_time)
                    )
                    patients = result.scalars().all()
                    patient_ids_to_sync = [p.external_id for p in patients if p.external_id]
            
            # Sync each patient
            for patient_id in patient_ids_to_sync:
                try:
                    patients_processed += 1
                    
                    # Get patient data from IRIS
                    iris_patient = await client.get_patient(patient_id)
                    
                    # Update or create patient record
                    updated = await self._update_patient_record(iris_patient, db)
                    if updated:
                        patients_updated += 1
                    
                    # Sync immunizations if requested
                    if sync_request.sync_type != "patient_specific":
                        iris_immunizations = await client.get_patient_immunizations(patient_id)
                        for iris_imm in iris_immunizations:
                            immunizations_processed += 1
                            updated = await self._update_immunization_record(iris_imm, db)
                            if updated:
                                immunizations_updated += 1
                    
                    # Update sync timestamp
                    await db.execute(
                        update(Patient)
                        .where(Patient.external_id == patient_id)
                        .values(
                            iris_last_sync_at=datetime.utcnow(),
                            iris_sync_status="success"
                        )
                    )
                    
                except IRISAPIError as e:
                    patients_failed += 1
                    error_msg = f"Patient {patient_id}: {str(e)}"
                    errors.append(error_msg)
                    logger.error("Patient sync failed", patient_id=patient_id, error=str(e))
                    
                    # Update sync status
                    await db.execute(
                        update(Patient)
                        .where(Patient.external_id == patient_id)
                        .values(iris_sync_status="failed")
                    )
                
                except Exception as e:
                    patients_failed += 1
                    error_msg = f"Patient {patient_id}: Unexpected error - {str(e)}"
                    errors.append(error_msg)
                    logger.error("Unexpected sync error", patient_id=patient_id, error=str(e))
            
            await db.commit()
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Determine overall status
            if patients_failed == 0:
                status = SyncStatus.SUCCESS
            elif patients_updated > 0:
                status = SyncStatus.PARTIAL
            else:
                status = SyncStatus.FAILED
            
            result = SyncResult(
                sync_id=sync_id,
                status=status,
                patients_processed=patients_processed,
                patients_updated=patients_updated,
                patients_failed=patients_failed,
                immunizations_processed=immunizations_processed,
                immunizations_updated=immunizations_updated,
                errors=errors,
                started_at=start_time,
                completed_at=end_time,
                duration_seconds=int(duration)
            )
            
            # Publish IRIS data synchronized event
            event_bus = self._get_event_bus()
            if event_bus:
                await event_bus.publish_iris_data_synchronized(
                sync_id=sync_id,
                endpoint_id=endpoint_id,
                sync_type=sync_request.sync_type,
                records_processed=patients_processed + immunizations_processed,
                records_successful=patients_updated + immunizations_updated,
                sync_duration_ms=int(duration * 1000),
                records_failed=patients_failed,
                data_quality_score=0.95 if patients_failed == 0 else max(0.5, 1.0 - (patients_failed / max(patients_processed, 1))),
                validation_errors=errors[:10]  # Include first 10 errors
            )
            
            logger.info("Patient data sync completed", 
                       sync_id=sync_id, status=status.value, 
                       patients_processed=patients_processed,
                       patients_updated=patients_updated,
                       patients_failed=patients_failed)
            
            return result
            
        except Exception as e:
            await db.rollback()
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.error("Patient sync failed", sync_id=sync_id, error=str(e))
            
            return SyncResult(
                sync_id=sync_id,
                status=SyncStatus.FAILED,
                patients_processed=0,
                patients_updated=0,
                patients_failed=0,
                immunizations_processed=0,
                immunizations_updated=0,
                errors=[str(e)],
                started_at=start_time,
                completed_at=end_time,
                duration_seconds=int(duration)
            )
    
    async def _update_patient_record(self, iris_patient, db: AsyncSession) -> bool:
        """Update or create patient record from IRIS data with complete FHIR processing."""
        try:
            # Check if patient exists by external_id
            result = await db.execute(
                select(Patient).where(Patient.external_id == iris_patient.patient_id)
            )
            patient = result.scalar_one_or_none()
            
            if patient:
                # Update existing patient - compare data version to avoid unnecessary updates
                current_version = patient.data_version or ""
                new_version = iris_patient.data_version or ""
                
                if new_version and new_version != current_version:
                    # Update patient with new data
                    if iris_patient.mrn:
                        patient.mrn = security_manager.encrypt_data(iris_patient.mrn)
                    
                    if iris_patient.demographics:
                        if iris_patient.demographics.get("first_name"):
                            patient.first_name_encrypted = security_manager.encrypt_data(
                                iris_patient.demographics["first_name"]
                            )
                        if iris_patient.demographics.get("last_name"):
                            patient.last_name_encrypted = security_manager.encrypt_data(
                                iris_patient.demographics["last_name"]
                            )
                        if iris_patient.demographics.get("date_of_birth"):
                            patient.date_of_birth_encrypted = security_manager.encrypt_data(
                                iris_patient.demographics["date_of_birth"]
                            )
                        if iris_patient.demographics.get("gender"):
                            patient.gender_encrypted = security_manager.encrypt_data(
                                iris_patient.demographics["gender"]
                            )
                        if iris_patient.demographics.get("phone"):
                            patient.phone_encrypted = security_manager.encrypt_data(
                                iris_patient.demographics["phone"]
                            )
                        if iris_patient.demographics.get("email"):
                            patient.email_encrypted = security_manager.encrypt_data(
                                iris_patient.demographics["email"]
                            )
                        if iris_patient.demographics.get("address"):
                            patient.address_encrypted = security_manager.encrypt_data(
                                json.dumps(iris_patient.demographics["address"])
                            )
                    
                    patient.data_version = new_version
                    patient.iris_last_sync_at = datetime.utcnow()
                    patient.iris_sync_status = "success"
                    patient.last_updated = iris_patient.last_updated
                    
                    logger.info("Updated existing patient", patient_id=iris_patient.patient_id, 
                              old_version=current_version, new_version=new_version)
                    return True
                else:
                    # No update needed, just update sync timestamp
                    patient.iris_last_sync_at = datetime.utcnow()
                    return False
            else:
                # Create new patient with complete FHIR data
                new_patient = Patient(
                    external_id=iris_patient.patient_id,
                    mrn=security_manager.encrypt_data(iris_patient.mrn or ""),
                    first_name_encrypted=security_manager.encrypt_data(
                        iris_patient.demographics.get("first_name", "") if iris_patient.demographics else ""
                    ),
                    last_name_encrypted=security_manager.encrypt_data(
                        iris_patient.demographics.get("last_name", "") if iris_patient.demographics else ""
                    ),
                    date_of_birth_encrypted=security_manager.encrypt_data(
                        iris_patient.demographics.get("date_of_birth", "") if iris_patient.demographics else ""
                    ),
                    gender_encrypted=security_manager.encrypt_data(
                        iris_patient.demographics.get("gender", "") if iris_patient.demographics else ""
                    ),
                    phone_encrypted=security_manager.encrypt_data(
                        iris_patient.demographics.get("phone", "") if iris_patient.demographics else ""
                    ),
                    email_encrypted=security_manager.encrypt_data(
                        iris_patient.demographics.get("email", "") if iris_patient.demographics else ""
                    ),
                    address_encrypted=security_manager.encrypt_data(
                        json.dumps(iris_patient.demographics.get("address", {})) if iris_patient.demographics else "{}"
                    ),
                    data_version=iris_patient.data_version,
                    iris_last_sync_at=datetime.utcnow(),
                    iris_sync_status="success",
                    last_updated=iris_patient.last_updated,
                    created_at=datetime.utcnow()
                )
                
                db.add(new_patient)
                logger.info("Created new patient", patient_id=iris_patient.patient_id)
                return True
                
        except Exception as e:
            logger.error("Failed to update patient record", 
                        patient_id=iris_patient.patient_id, error=str(e))
            # Update sync status to failed
            if patient:
                patient.iris_sync_status = "failed"
            return False
    
    async def _update_immunization_record(self, iris_immunization, db: AsyncSession) -> bool:
        """Update or create immunization record from IRIS data with enhanced validation."""
        try:
            # Check if immunization exists by IRIS record ID
            result = await db.execute(
                select(Immunization).where(Immunization.iris_record_id == iris_immunization.immunization_id)
            )
            immunization = result.scalar_one_or_none()
            
            if immunization:
                # Update existing record with new data - map IRIS fields to FHIR model
                immunization.vaccine_code = iris_immunization.vaccine_code
                immunization.vaccine_display = iris_immunization.vaccine_name
                immunization.occurrence_datetime = iris_immunization.administration_date
                # Encrypt PHI fields according to HIPAA requirements
                from app.core.security import encryption_service
                immunization.lot_number_encrypted = await encryption_service.encrypt(str(iris_immunization.lot_number)) if iris_immunization.lot_number else None
                immunization.manufacturer_encrypted = await encryption_service.encrypt(str(iris_immunization.manufacturer)) if iris_immunization.manufacturer else None
                immunization.performer_name_encrypted = await encryption_service.encrypt(str(iris_immunization.administered_by)) if iris_immunization.administered_by else None
                immunization.site_display = iris_immunization.administration_site
                immunization.route_display = iris_immunization.route
                immunization.last_updated = datetime.utcnow()
                
                logger.info("Updated existing immunization", 
                          immunization_id=iris_immunization.immunization_id,
                          patient_id=iris_immunization.patient_id)
                return True
            else:
                # Find patient by external_id
                result = await db.execute(
                    select(Patient).where(Patient.external_id == iris_immunization.patient_id)
                )
                patient = result.scalar_one_or_none()
                
                if patient:
                    # Create new immunization record - map IRIS fields to FHIR model
                    # Encrypt PHI fields according to HIPAA requirements
                    from app.core.security import encryption_service
                    new_immunization = Immunization(
                        patient_id=patient.id,
                        vaccine_code=iris_immunization.vaccine_code,
                        vaccine_display=iris_immunization.vaccine_name,
                        occurrence_datetime=iris_immunization.administration_date,
                        lot_number_encrypted=await encryption_service.encrypt(str(iris_immunization.lot_number)) if iris_immunization.lot_number else None,
                        manufacturer_encrypted=await encryption_service.encrypt(str(iris_immunization.manufacturer)) if iris_immunization.manufacturer else None,
                        performer_name_encrypted=await encryption_service.encrypt(str(iris_immunization.administered_by)) if iris_immunization.administered_by else None,
                        site_display=iris_immunization.administration_site,
                        route_display=iris_immunization.route,
                        iris_record_id=iris_immunization.immunization_id,
                        data_source="IRIS",
                        created_at=datetime.utcnow(),
                        last_updated=datetime.utcnow()
                    )
                    
                    db.add(new_immunization)
                    logger.info("Created new immunization record", 
                              immunization_id=iris_immunization.immunization_id,
                              patient_id=iris_immunization.patient_id)
                    return True
                else:
                    logger.warning("Patient not found for immunization", 
                                 patient_id=iris_immunization.patient_id,
                                 immunization_id=iris_immunization.immunization_id)
                    return False
        
        except Exception as e:
            logger.error("Failed to update immunization record", 
                        immunization_id=iris_immunization.immunization_id,
                        patient_id=iris_immunization.patient_id, 
                        error=str(e))
            return False

    # ============================================
    # NEW EXTERNAL INTEGRATION METHODS
    # ============================================

    async def sync_with_external_registry(self, endpoint_id: str, registry_type: str, 
                                        params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Sync with external immunization registries (state, national)."""
        try:
            client = await self.get_client(endpoint_id, db)
            
            # Call IRIS registry sync endpoint
            sync_result = await client.sync_immunization_registry({
                "registry_type": registry_type,
                "parameters": params,
                "include_demographics": True,
                "include_immunization_history": True
            })
            
            logger.info("External registry sync completed", 
                       endpoint_id=endpoint_id, registry_type=registry_type)
            
            return {
                "status": "success",
                "registry_type": registry_type,
                "records_found": sync_result.get("total_records", 0),
                "last_sync": datetime.utcnow().isoformat(),
                "details": sync_result
            }
            
        except Exception as e:
            logger.error("External registry sync failed", 
                        endpoint_id=endpoint_id, registry_type=registry_type, error=str(e))
            return {
                "status": "failed",
                "registry_type": registry_type,
                "error": str(e),
                "last_attempt": datetime.utcnow().isoformat()
            }

    async def submit_immunization_to_registry(self, endpoint_id: str, immunization_data: Dict[str, Any], 
                                            db: AsyncSession) -> Dict[str, Any]:
        """Submit immunization record to external registry via IRIS."""
        try:
            client = await self.get_client(endpoint_id, db)
            
            # Convert internal immunization data to FHIR R4 format
            fhir_immunization = self._convert_to_fhir_immunization(immunization_data)
            
            # Submit to IRIS for registry submission
            submission_result = await client.submit_immunization_record(fhir_immunization)
            
            # Update local record with submission status
            if immunization_data.get("id"):
                await db.execute(
                    update(Immunization)
                    .where(Immunization.id == immunization_data["id"])
                    .values(
                        registry_submission_status="submitted",
                        registry_submission_id=submission_result.get("id"),
                        registry_submission_date=datetime.utcnow()
                    )
                )
                await db.commit()
            
            logger.info("Immunization submitted to registry", 
                       immunization_id=immunization_data.get("id"),
                       submission_id=submission_result.get("id"))
            
            return {
                "status": "submitted",
                "submission_id": submission_result.get("id"),
                "registry_response": submission_result
            }
            
        except Exception as e:
            logger.error("Failed to submit immunization to registry", 
                        immunization_id=immunization_data.get("id"), error=str(e))
            return {
                "status": "failed",
                "error": str(e)
            }

    async def get_provider_directory(self, endpoint_id: str, search_params: Dict[str, str], 
                                   db: AsyncSession) -> List[Dict[str, Any]]:
        """Get healthcare provider directory from IRIS."""
        try:
            client = await self.get_client(endpoint_id, db)
            
            # Get provider directory from IRIS
            provider_bundle = await client.get_provider_directory(search_params)
            
            providers = []
            if provider_bundle.get("resourceType") == "Bundle":
                for entry in provider_bundle.get("entry", []):
                    if entry.get("resource", {}).get("resourceType") == "Practitioner":
                        provider = self._process_fhir_practitioner(entry["resource"])
                        providers.append(provider)
            
            logger.info("Retrieved provider directory", 
                       endpoint_id=endpoint_id, provider_count=len(providers))
            
            return providers
            
        except Exception as e:
            logger.error("Failed to get provider directory", 
                        endpoint_id=endpoint_id, error=str(e))
            return []

    async def get_vaccine_inventory(self, endpoint_id: str, location_id: Optional[str], 
                                  db: AsyncSession) -> Dict[str, Any]:
        """Get current vaccine inventory from IRIS."""
        try:
            client = await self.get_client(endpoint_id, db)
            
            # Get vaccine inventory
            inventory_data = await client.get_vaccine_inventory(location_id)
            
            logger.info("Retrieved vaccine inventory", 
                       endpoint_id=endpoint_id, location_id=location_id)
            
            return {
                "status": "success",
                "location_id": location_id,
                "inventory": inventory_data,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to get vaccine inventory", 
                        endpoint_id=endpoint_id, location_id=location_id, error=str(e))
            return {
                "status": "failed",
                "error": str(e),
                "last_attempt": datetime.utcnow().isoformat()
            }

    def _convert_to_fhir_immunization(self, immunization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert internal immunization data to FHIR R4 format."""
        fhir_immunization = {
            "resourceType": "Immunization",
            "status": "completed",
            "vaccineCode": {
                "coding": [{
                    "system": "http://hl7.org/fhir/sid/cvx",
                    "code": immunization_data.get("vaccine_code", ""),
                    "display": immunization_data.get("vaccine_name", "")
                }]
            },
            "patient": {
                "reference": f"Patient/{immunization_data.get('patient_external_id', '')}"
            },
            "occurrenceDateTime": immunization_data.get("administration_date", ""),
            "recorded": datetime.utcnow().isoformat(),
            "primarySource": True
        }
        
        # Add optional fields
        if immunization_data.get("lot_number"):
            fhir_immunization["lotNumber"] = immunization_data["lot_number"]
            
        if immunization_data.get("manufacturer"):
            fhir_immunization["manufacturer"] = {
                "display": immunization_data["manufacturer"]
            }
            
        if immunization_data.get("administered_by"):
            fhir_immunization["performer"] = [{
                "actor": {
                    "display": immunization_data["administered_by"]
                }
            }]
            
        if immunization_data.get("administration_site"):
            fhir_immunization["site"] = {
                "coding": [{
                    "display": immunization_data["administration_site"]
                }]
            }
            
        if immunization_data.get("route"):
            fhir_immunization["route"] = {
                "coding": [{
                    "display": immunization_data["route"]
                }]
            }
            
        if immunization_data.get("dose_number"):
            fhir_immunization["protocolApplied"] = [{
                "doseNumberPositiveInt": immunization_data["dose_number"],
                "seriesDosesPositiveInt": immunization_data.get("series_doses", 1)
            }]
        
        return fhir_immunization

    def _process_fhir_practitioner(self, fhir_practitioner: Dict[str, Any]) -> Dict[str, Any]:
        """Process FHIR R4 Practitioner resource."""
        practitioner = {
            "id": fhir_practitioner.get("id", ""),
            "name": "",
            "specialty": [],
            "contact": {},
            "address": {},
            "active": fhir_practitioner.get("active", True)
        }
        
        # Extract name
        if fhir_practitioner.get("name"):
            name = fhir_practitioner["name"][0]
            given_names = " ".join(name.get("given", []))
            family_name = name.get("family", "")
            practitioner["name"] = f"{given_names} {family_name}".strip()
        
        # Extract specialty
        for qualification in fhir_practitioner.get("qualification", []):
            if qualification.get("code", {}).get("coding"):
                coding = qualification["code"]["coding"][0]
                practitioner["specialty"].append({
                    "code": coding.get("code"),
                    "display": coding.get("display")
                })
        
        # Extract contact information
        for telecom in fhir_practitioner.get("telecom", []):
            if telecom.get("system") == "phone":
                practitioner["contact"]["phone"] = telecom.get("value")
            elif telecom.get("system") == "email":
                practitioner["contact"]["email"] = telecom.get("value")
        
        # Extract address
        if fhir_practitioner.get("address"):
            address = fhir_practitioner["address"][0]
            practitioner["address"] = {
                "line": address.get("line", []),
                "city": address.get("city"),
                "state": address.get("state"),
                "postal_code": address.get("postalCode")
            }
        
        return practitioner

# Global service instance
iris_service = IRISIntegrationService()