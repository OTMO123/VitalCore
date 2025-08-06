from celery import current_app as celery_app
from typing import List, Optional, Dict, Any
import asyncio
import structlog
from datetime import datetime, timedelta

from app.core.database_unified import get_db_session, APIEndpoint, Patient
from sqlalchemy import select
from app.modules.iris_api.service import iris_service
from app.modules.iris_api.schemas import SyncRequest, SyncStatus

logger = structlog.get_logger()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def health_check(self):
    """Check IRIS API health status for all active endpoints."""
    try:
        # Run async operation in sync context
        result = asyncio.run(_perform_health_checks())
        logger.info("IRIS API health check completed", 
                   endpoints_checked=len(result.get("results", [])))
        return result
        
    except Exception as exc:
        logger.error("IRIS API health check failed", error=str(exc))
        raise self.retry(exc=exc)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def sync_immunization_data(self, endpoint_id: str, patient_ids: Optional[List[str]] = None):
    """Sync immunization data from IRIS API."""
    try:
        result = asyncio.run(_perform_immunization_sync(endpoint_id, patient_ids))
        logger.info("Immunization data sync completed", 
                   endpoint_id=endpoint_id, 
                   patients_synced=result.get("synced_count", 0))
        return result
        
    except Exception as exc:
        logger.error("Immunization data sync failed", 
                    endpoint_id=endpoint_id, error=str(exc))
        raise self.retry(exc=exc)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300) 
def bulk_patient_sync(self, endpoint_id: str, batch_size: int = 100):
    """Perform bulk patient data synchronization."""
    try:
        result = asyncio.run(_perform_bulk_sync(endpoint_id, batch_size))
        logger.info("Bulk patient sync completed",
                   endpoint_id=endpoint_id,
                   total_processed=result.get("processed_count", 0))
        return result
        
    except Exception as exc:
        logger.error("Bulk patient sync failed",
                    endpoint_id=endpoint_id, error=str(exc))
        raise self.retry(exc=exc)

# Async helper functions

async def _perform_health_checks():
    """Perform health checks on all active endpoints."""
    db = await get_db_session()
    try:
        # Get all active API endpoints
        result = await db.execute(
            select(APIEndpoint).where(APIEndpoint.status == "active")
        )
        endpoints = result.scalars().all()
        
        results = []
        for endpoint in endpoints:
            try:
                health_status = await iris_service.health_check(str(endpoint.id), db)
                results.append({
                    "endpoint_id": str(endpoint.id),
                    "status": health_status.get("status", "unknown"),
                    "response_time": health_status.get("response_time", 0),
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error("Endpoint health check failed", 
                           endpoint_id=str(endpoint.id), error=str(e))
                results.append({
                    "endpoint_id": str(endpoint.id),
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return {"results": results, "timestamp": datetime.utcnow().isoformat()}
        
    finally:
        await db.close()

async def _perform_immunization_sync(endpoint_id: str, patient_ids: Optional[List[str]] = None):
    """Perform immunization data synchronization."""
    db = await get_db_session()
    try:
        # Implement immunization sync logic
        synced_count = 0
        errors = []
        
        # Get endpoint
        result = await db.execute(
            select(APIEndpoint).where(APIEndpoint.id == endpoint_id)
        )
        endpoint = result.scalar_one_or_none()
        
        if not endpoint:
            raise ValueError(f"Endpoint {endpoint_id} not found")
        
        # Get patients to sync
        if patient_ids:
            query = select(Patient).where(Patient.id.in_(patient_ids))
        else:
            query = select(Patient).where(Patient.is_active == True).limit(100)
            
        result = await db.execute(query)
        patients = result.scalars().all()
        
        # Sync each patient's immunization data
        for patient in patients:
            try:
                sync_result = await iris_service.sync_patient_immunizations(
                    str(endpoint.id), str(patient.id), db
                )
                if sync_result.get("success"):
                    synced_count += 1
                else:
                    errors.append(f"Patient {patient.id}: {sync_result.get('error')}")
                    
            except Exception as e:
                errors.append(f"Patient {patient.id}: {str(e)}")
        
        return {
            "synced_count": synced_count,
            "total_patients": len(patients),
            "errors": errors,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    finally:
        await db.close()

async def _perform_bulk_sync(endpoint_id: str, batch_size: int = 100):
    """Perform bulk patient data synchronization."""
    db = await get_db_session()
    try:
        processed_count = 0
        errors = []
        
        # Get endpoint
        result = await db.execute(
            select(APIEndpoint).where(APIEndpoint.id == endpoint_id)
        )
        endpoint = result.scalar_one_or_none()
        
        if not endpoint:
            raise ValueError(f"Endpoint {endpoint_id} not found")
        
        # Process in batches
        offset = 0
        while True:
            # Get batch of patients
            result = await db.execute(
                select(Patient)
                .where(Patient.is_active == True)
                .offset(offset)
                .limit(batch_size)
            )
            patients = result.scalars().all()
            
            if not patients:
                break
            
            # Sync batch
            for patient in patients:
                try:
                    sync_result = await iris_service.sync_patient_data(
                        str(endpoint.id), str(patient.id), db
                    )
                    if sync_result.get("success"):
                        processed_count += 1
                    else:
                        errors.append(f"Patient {patient.id}: {sync_result.get('error')}")
                        
                except Exception as e:
                    errors.append(f"Patient {patient.id}: {str(e)}")
            
            offset += batch_size
            
            # Break if batch was not full (last batch)
            if len(patients) < batch_size:
                break
        
        return {
            "processed_count": processed_count,
            "errors": errors,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    finally:
        await db.close()