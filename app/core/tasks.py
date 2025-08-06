from celery import Celery
from celery.schedules import crontab
import structlog
import asyncio
import httpx
import json
import uuid
import redis
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from celery.utils.log import get_task_logger

from app.core.config import get_settings
from app.core.database_unified import AuditEventType

logger = structlog.get_logger()

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "iris_api_system",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.modules.iris_api.tasks",
        "app.modules.audit_logger.tasks", 
        "app.modules.purge_scheduler.tasks",
        "app.modules.auth.tasks",
        "app.modules.healthcare_records.tasks",
        "app.modules.edge_ai.tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "app.modules.iris_api.tasks.*": {"queue": "iris_api"},
        "app.modules.audit_logger.tasks.*": {"queue": "audit"},
        "app.modules.purge_scheduler.tasks.*": {"queue": "purge"},
        "app.modules.auth.tasks.*": {"queue": "auth"},
        "app.modules.healthcare_records.tasks.process_phi_encryption_queue": {"queue": "phi_processing"},
        "app.modules.healthcare_records.tasks.monitor_consent_expiration": {"queue": "healthcare_monitoring"},
        "app.modules.healthcare_records.tasks.generate_compliance_reports": {"queue": "compliance"},
        "app.modules.healthcare_records.tasks.anonymize_patient_data": {"queue": "research_processing"},
        "app.modules.healthcare_records.tasks.audit_phi_access_patterns": {"queue": "security_monitoring"},
        "app.modules.healthcare_records.tasks.cleanup_expired_access_tokens": {"queue": "maintenance"},
        "app.modules.healthcare_records.tasks.sync_patient_fhir_resources": {"queue": "fhir_processing"},
        "app.modules.healthcare_records.tasks.archive_old_clinical_documents": {"queue": "data_lifecycle"},
        "app.core.tasks.process_voice_transcription": {"queue": "voice_processing"},
        "app.core.tasks.process_clinical_decision_support": {"queue": "clinical_ai"},
        "app.core.tasks.extract_medical_entities": {"queue": "medical_ner"},
        "app.core.tasks.cleanup_expired_voice_files": {"queue": "maintenance"}
    },
    
    # Task execution settings
    task_always_eager=settings.DEBUG,  # Execute tasks synchronously in debug mode
    task_eager_propagates=settings.DEBUG,
    task_ignore_result=False,
    result_expires=3600,  # 1 hour
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=100,
    
    # Monitoring
    task_send_sent_event=True,
    worker_send_task_events=True,
)

# Periodic tasks schedule
celery_app.conf.beat_schedule = {
    # Purge scheduler - runs every hour
    "purge-data-check": {
        "task": "app.modules.purge_scheduler.tasks.check_purge_schedules",
        "schedule": crontab(minute=0),  # Every hour
    },
    
    # Audit log maintenance - runs daily at 2 AM
    "audit-log-maintenance": {
        "task": "app.modules.audit_logger.tasks.maintain_audit_logs",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    
    # IRIS API health check - runs every 5 minutes
    "iris-api-health-check": {
        "task": "app.modules.iris_api.tasks.health_check",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
    
    # System metrics collection - runs every 15 minutes
    "collect-system-metrics": {
        "task": "app.core.tasks.collect_metrics",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    
    # Auth module tasks
    # Session cleanup - runs every 30 minutes
    "auth-session-cleanup": {
        "task": "app.modules.auth.tasks.cleanup_expired_sessions",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
    },
    
    # Failed login monitoring - runs every 10 minutes
    "auth-failed-login-monitor": {
        "task": "app.modules.auth.tasks.monitor_failed_login_attempts",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
    },
    
    # Token cleanup - runs every hour
    "auth-token-cleanup": {
        "task": "app.modules.auth.tasks.cleanup_expired_tokens",
        "schedule": crontab(minute=0),  # Every hour
    },
    
    # Security event processing - runs every 15 minutes
    "auth-security-events": {
        "task": "app.modules.auth.tasks.process_security_events",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    
    # Account unlock - runs every 5 minutes
    "auth-unlock-accounts": {
        "task": "app.modules.auth.tasks.unlock_user_accounts",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
    
    # Security report - runs daily at 3 AM
    "auth-security-report": {
        "task": "app.modules.auth.tasks.generate_security_report",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    
    # Permission sync - runs daily at 4 AM
    "auth-permission-sync": {
        "task": "app.modules.auth.tasks.sync_user_permissions",
        "schedule": crontab(hour=4, minute=0),  # Daily at 4 AM
    },
    
    # Authentication audit - runs daily at 1 AM
    "auth-audit-events": {
        "task": "app.modules.auth.tasks.audit_authentication_events",
        "schedule": crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    
    # Inactive user cleanup - runs weekly on Sunday at 5 AM
    "auth-inactive-user-cleanup": {
        "task": "app.modules.auth.tasks.cleanup_inactive_users",
        "schedule": crontab(hour=5, minute=0, day_of_week=0),  # Weekly on Sunday
    },
    
    # Healthcare Records Tasks
    
    # PHI encryption monitoring - runs every 6 hours
    "healthcare-phi-encryption-check": {
        "task": "app.modules.healthcare_records.tasks.process_phi_encryption_queue",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
        "kwargs": {"patient_ids": [], "fields_to_encrypt": [], "operation": "check"},
        "options": {"queue": "phi_processing"}
    },
    
    # Consent expiration monitoring - runs every hour
    "healthcare-consent-expiration": {
        "task": "app.modules.healthcare_records.tasks.monitor_consent_expiration",
        "schedule": crontab(minute=0),  # Every hour
        "options": {"queue": "healthcare_monitoring"}
    },
    
    # Daily HIPAA compliance report - runs daily at 2 AM
    "healthcare-hipaa-compliance-report": {
        "task": "app.modules.healthcare_records.tasks.generate_compliance_reports",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        "args": ["hipaa", (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(), datetime.now(timezone.utc).isoformat()],
        "options": {"queue": "compliance"}
    },
    
    # PHI access pattern auditing - runs every 30 minutes
    "healthcare-phi-access-audit": {
        "task": "app.modules.healthcare_records.tasks.audit_phi_access_patterns",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
        "args": [24],  # 24 hour lookback
        "options": {"queue": "security_monitoring"}
    },
    
    # Expired token cleanup - runs daily at 3 AM
    "healthcare-token-cleanup": {
        "task": "app.modules.healthcare_records.tasks.cleanup_expired_access_tokens",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
        "options": {"queue": "maintenance"}
    },
    
    # Document archival - runs weekly on Sunday at 1 AM
    "healthcare-document-archival": {
        "task": "app.modules.healthcare_records.tasks.archive_old_clinical_documents",
        "schedule": crontab(hour=1, minute=0, day_of_week=0),  # Weekly on Sunday
        "options": {"queue": "data_lifecycle"}
    },
    
    # Edge AI Tasks
    
    # Voice file cleanup - runs every hour
    "voice-file-cleanup": {
        "task": "app.core.tasks.cleanup_expired_voice_files",
        "schedule": crontab(minute=0),  # Every hour
        "options": {"queue": "maintenance"}
    },
}

@celery_app.task
def collect_metrics():
    """Collect system metrics for monitoring and alerting."""
    try:
        # Placeholder for metrics collection
        # In production, this would collect:
        # - Database connection pool status
        # - API response times
        # - Queue lengths
        # - Error rates
        # - Memory usage
        # - Disk space
        
        logger.info("System metrics collected successfully")
        return {"status": "success", "timestamp": "now"}
        
    except Exception as e:
        logger.error("Failed to collect system metrics", error=str(e))
        raise

@celery_app.task
def send_alert(alert_type: str, message: str, severity: str = "info"):
    """Send system alerts (email, Slack, etc.)."""
    try:
        # Placeholder for alert sending
        # In production, this would send alerts via:
        # - Email
        # - Slack
        # - PagerDuty
        # - SMS
        
        logger.info("Alert sent", alert_type=alert_type, message=message, severity=severity)
        return {"status": "sent", "alert_type": alert_type}
        
    except Exception as e:
        logger.error("Failed to send alert", error=str(e), alert_type=alert_type)
        raise

# Edge AI Processing Tasks

@celery_app.task(bind=True, max_retries=3)
def process_voice_transcription(self, audio_data: dict):
    """Process voice transcription using Whisper service."""
    task_logger = get_task_logger(__name__)
    
    try:
        task_logger.info(f"Starting voice transcription for audio: {audio_data.get('filename')}")
        
        # Run async transcription in event loop
        result = asyncio.run(_process_voice_transcription_async(audio_data))
        
        task_logger.info(f"Voice transcription completed: {result['transcription_id']}")
        return result
        
    except Exception as exc:
        task_logger.error(f"Voice transcription failed: {exc}")
        if self.request.retries < self.max_retries:
            task_logger.info(f"Retrying transcription (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60, exc=exc)
        else:
            # Log final failure
            asyncio.run(_log_transcription_failure(audio_data, str(exc)))
            raise exc

@celery_app.task(bind=True, max_retries=3)
def process_clinical_decision_support(self, clinical_data: dict):
    """Process clinical decision support using Gemma 3N engine."""
    task_logger = get_task_logger(__name__)
    
    try:
        task_logger.info(f"Starting clinical decision support for case: {clinical_data.get('case_id')}")
        
        # Run async processing in event loop
        result = asyncio.run(_process_clinical_decision_async(clinical_data))
        
        task_logger.info(f"Clinical decision support completed: {result['output_id']}")
        return result
        
    except Exception as exc:
        task_logger.error(f"Clinical decision support failed: {exc}")
        if self.request.retries < self.max_retries:
            task_logger.info(f"Retrying clinical processing (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60, exc=exc)
        else:
            # Log final failure
            asyncio.run(_log_clinical_processing_failure(clinical_data, str(exc)))
            raise exc

@celery_app.task(bind=True, max_retries=2)
def extract_medical_entities(self, text_data: dict):
    """Extract medical entities using Medical NER service."""
    task_logger = get_task_logger(__name__)
    
    try:
        task_logger.info(f"Starting medical NER for text: {len(text_data['text'])} characters")
        
        # Run async NER processing in event loop
        result = asyncio.run(_extract_medical_entities_async(text_data))
        
        task_logger.info(f"Medical NER completed: {result['entity_count']} entities")
        return result
        
    except Exception as exc:
        task_logger.error(f"Medical NER failed: {exc}")
        if self.request.retries < self.max_retries:
            task_logger.info(f"Retrying NER (attempt {self.request.retries + 1})")
            raise self.retry(countdown=30, exc=exc)
        else:
            # Log final failure
            asyncio.run(_log_ner_failure(text_data, str(exc)))
            raise exc

@celery_app.task
def cleanup_expired_voice_files():
    """Clean up expired voice recording files and cache entries."""
    task_logger = get_task_logger(__name__)
    
    try:
        task_logger.info("Starting voice file cleanup")
        
        # Run async cleanup in event loop
        result = asyncio.run(_cleanup_expired_voice_files_async())
        
        task_logger.info(f"Voice file cleanup completed: {result}")
        return result
        
    except Exception as exc:
        task_logger.error(f"Voice file cleanup failed: {exc}")
        raise exc

# Async helper functions for Edge AI tasks

async def _process_voice_transcription_async(audio_data: dict) -> dict:
    """Async voice transcription processing."""
    
    # Prepare request to Whisper service
    transcription_request = {
        "patient_id": audio_data.get("patient_id"),
        "medical_specialty": audio_data.get("medical_specialty"),
        "language": audio_data.get("language", "en"),
        "encrypt_result": audio_data.get("encrypt_result", True),
        "extract_medical_entities": audio_data.get("extract_entities", True)
    }
    
    # Send audio file to Whisper service
    files = {"audio_file": (audio_data["filename"], audio_data["file_content"], audio_data["content_type"])}
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"http://whisper-service:8002/transcribe",
                files=files,
                data=transcription_request
            )
            response.raise_for_status()
            result = response.json()
        
        # Store result with audit trail
        await _store_transcription_result(result, audio_data)
        
        return result
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error calling Whisper service: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing transcription: {e}")
        raise

async def _process_clinical_decision_async(clinical_data: dict) -> dict:
    """Async clinical decision processing."""
    
    # Prepare request to Gemma service
    gemma_request = {
        "text": clinical_data["clinical_text"],
        "max_tokens": clinical_data.get("max_tokens", 512),
        "temperature": clinical_data.get("temperature", 0.1),
        "medical_specialty": clinical_data.get("medical_specialty"),
        "urgency_level": clinical_data.get("urgency_level", "moderate"),
        "require_validation": clinical_data.get("require_validation", True)
    }
    
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"http://gemma-engine:8001/process",
                json=gemma_request
            )
            response.raise_for_status()
            result = response.json()
        
        # Store clinical decision result with audit trail
        await _store_clinical_decision_result(result, clinical_data)
        
        return result
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error calling Gemma service: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing clinical decision: {e}")
        raise

async def _extract_medical_entities_async(text_data: dict) -> dict:
    """Async medical entity extraction."""
    
    # Prepare request to Medical NER service
    ner_request = {
        "text": text_data["text"],
        "extract_snomed": text_data.get("extract_snomed", True),
        "extract_icd": text_data.get("extract_icd", True),
        "confidence_threshold": text_data.get("confidence_threshold", 0.7),
        "max_entities": text_data.get("max_entities", 100)
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"http://medical-ner:8003/extract",
                json=ner_request
            )
            response.raise_for_status()
            result = response.json()
        
        # Store NER result with audit trail
        await _store_ner_result(result, text_data)
        
        return result
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error calling Medical NER service: {e}")
        raise
    except Exception as e:
        logger.error(f"Error extracting medical entities: {e}")
        raise

async def _cleanup_expired_voice_files_async() -> dict:
    """Async voice file cleanup."""
    cleaned_files = 0
    cleaned_cache_entries = 0
    
    try:
        # Initialize Redis client
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Clean expired Redis cache entries
        pattern = "whisper:transcription:*"
        async for key in redis_client.scan_iter(match=pattern):
            ttl = await redis_client.ttl(key)
            if ttl == -1:  # Key without expiration
                await redis_client.expire(key, 86400)  # Set 24-hour expiration
            elif ttl == -2:  # Expired key
                await redis_client.delete(key)
                cleaned_cache_entries += 1
        
        await redis_client.close()
        
        return {
            "cleaned_files": cleaned_files,
            "cleaned_cache_entries": cleaned_cache_entries,
            "cleanup_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during voice file cleanup: {e}")
        raise

# Audit logging helpers

async def _store_transcription_result(result: dict, audio_data: dict):
    """Store transcription result with audit trail."""
    try:
        # Import audit logger here to avoid circular imports
        from app.modules.audit_logger.service import audit_logger
        
        await audit_logger.log_event(
            event_type=AuditEventType.PHI_ACCESS,
            user_id=audio_data.get("user_id", "system"),
            resource_type="voice_transcription",
            resource_id=result.get("transcription_id"),
            action="voice_transcription_completed",
            details={
                "patient_id": audio_data.get("patient_id"),
                "duration_seconds": result.get("audio_duration_seconds"),
                "word_count": result.get("word_count"),
                "encrypted": result.get("encrypted", False)
            }
        )
        
        logger.info(f"Transcription audit logged: {result.get('transcription_id')}")
        
    except Exception as e:
        logger.error(f"Failed to store transcription result: {e}")

async def _store_clinical_decision_result(result: dict, clinical_data: dict):
    """Store clinical decision result with audit trail."""
    try:
        from app.modules.audit_logger.service import audit_logger
        
        await audit_logger.log_event(
            event_type=AuditEventType.CLINICAL_DECISION,
            user_id=clinical_data.get("user_id", "system"),
            resource_type="clinical_decision_support",
            resource_id=result.get("output_id"),
            action="clinical_decision_completed",
            details={
                "case_id": clinical_data.get("case_id"),
                "medical_specialty": clinical_data.get("medical_specialty"),
                "urgency_level": clinical_data.get("urgency_level"),
                "requires_human_review": result.get("requires_human_review", False)
            }
        )
        
        logger.info(f"Clinical decision audit logged: {result.get('output_id')}")
        
    except Exception as e:
        logger.error(f"Failed to store clinical decision result: {e}")

async def _store_ner_result(result: dict, text_data: dict):
    """Store NER result with audit trail."""
    try:
        from app.modules.audit_logger.service import audit_logger
        
        await audit_logger.log_event(
            event_type=AuditEventType.DATA_PROCESSING,
            user_id=text_data.get("user_id", "system"),
            resource_type="medical_ner",
            resource_id=result.get("request_id"),
            action="medical_ner_completed",
            details={
                "text_length": result.get("text_length"),
                "entity_count": result.get("entity_count"),
                "processing_time_ms": result.get("processing_time_ms")
            }
        )
        
        logger.info(f"Medical NER audit logged: {result.get('request_id')}")
        
    except Exception as e:
        logger.error(f"Failed to store NER result: {e}")

async def _log_transcription_failure(audio_data: dict, error: str):
    """Log transcription failure for audit."""
    try:
        from app.modules.audit_logger.service import audit_logger
        
        await audit_logger.log_event(
            event_type=AuditEventType.SYSTEM_ERROR,
            user_id=audio_data.get("user_id", "system"),
            resource_type="voice_transcription",
            resource_id="failed",
            action="transcription_failed",
            details={
                "filename": audio_data.get("filename"),
                "error": error
            }
        )
    except Exception as e:
        logger.error(f"Failed to log transcription failure: {e}")

async def _log_clinical_processing_failure(clinical_data: dict, error: str):
    """Log clinical processing failure for audit."""
    try:
        from app.modules.audit_logger.service import audit_logger
        
        await audit_logger.log_event(
            event_type=AuditEventType.SYSTEM_ERROR,
            user_id=clinical_data.get("user_id", "system"),
            resource_type="clinical_decision_support",
            resource_id="failed",
            action="clinical_processing_failed",
            details={
                "case_id": clinical_data.get("case_id"),
                "error": error
            }
        )
    except Exception as e:
        logger.error(f"Failed to log clinical processing failure: {e}")

async def _log_ner_failure(text_data: dict, error: str):
    """Log NER failure for audit."""
    try:
        from app.modules.audit_logger.service import audit_logger
        
        await audit_logger.log_event(
            event_type=AuditEventType.SYSTEM_ERROR,
            user_id=text_data.get("user_id", "system"),
            resource_type="medical_ner",
            resource_id="failed",
            action="ner_processing_failed",
            details={
                "text_length": len(text_data.get("text", "")),
                "error": error
            }
        )
    except Exception as e:
        logger.error(f"Failed to log NER failure: {e}")

if __name__ == "__main__":
    celery_app.start()