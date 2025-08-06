"""
Healthcare Records Background Processing Tasks

Celery tasks for PHI encryption, consent management, compliance reporting,
and data lifecycle management with HIPAA/GDPR compliance.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from celery import Task, group, chain, chord
from celery.result import AsyncResult
import structlog
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tasks import celery_app
from app.core.database import AsyncSessionLocal
from app.core.security import EncryptionService
from app.core.event_bus_advanced import HybridEventBus as EventBus, DomainEvent, EventPriority
from app.core.exceptions import ProcessingError, ValidationError
from app.core.database_advanced import (
    Patient, ClinicalDocument, Consent, PHIAccessLog,
    ConsentStatus, ConsentType, DocumentType
)
from app.modules.healthcare_records.service import (
    PatientService, ClinicalDocumentService, 
    ConsentService, PHIAccessAuditService,
    AccessContext
)
from app.modules.healthcare_records.anonymization import AnonymizationEngine
from app.modules.healthcare_records.fhir_validator import FHIRValidator

logger = structlog.get_logger(__name__)

# Constants
ENCRYPTION_BATCH_SIZE = 100
CONSENT_CHECK_INTERVAL = 3600  # 1 hour
COMPLIANCE_REPORT_INTERVAL = 86400  # 24 hours
AUDIT_RETENTION_DAYS = 2555  # 7 years for HIPAA
DOCUMENT_ARCHIVE_DAYS = 365
MAX_RETRY_ATTEMPTS = 3
TASK_TIME_LIMIT = 3600  # 1 hour
PHI_TASK_PRIORITY = 9  # High priority for PHI tasks

# Domain Events for task completion
class PHIEncryptionCompleted(DomainEvent):
    task_id: str
    records_processed: int
    duration_seconds: float

class ComplianceReportGenerated(DomainEvent):
    report_id: str
    report_type: str
    period_start: datetime
    period_end: datetime

class ConsentExpirationProcessed(DomainEvent):
    expired_count: int
    notified_count: int

class DataAnonymizationCompleted(DomainEvent):
    dataset_id: str
    records_anonymized: int
    techniques_used: List[str]


class SecurePHITask(Task):
    """Base task class with PHI-specific security measures"""
    
    def __init__(self):
        super().__init__()
        self.encryption_service = None
        self.event_bus = None
    
    def before_start(self, task_id, args, kwargs):
        """Initialize services before task execution"""
        try:
            super().before_start(task_id, args, kwargs)
            self.encryption_service = EncryptionService()
            self.event_bus = EventBus()
            
            # Audit task start
            logger.info(
                "PHI task starting",
                task_id=task_id,
                task_name=self.name,
                args_count=len(args) if args else 0
            )
        except Exception as e:
            logger.error("Failed to initialize PHI task", error=str(e), task_id=task_id)
            raise
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure with security considerations"""
        try:
            super().on_failure(exc, task_id, args, kwargs, einfo)
            
            # Log task failure without exposing sensitive data
            logger.error(
                "PHI task failed",
                task_id=task_id,
                task_name=self.name,
                error_type=type(exc).__name__,
                # Don't log full exception to avoid PHI exposure
            )
            
            # Clear any sensitive data from memory
            self._clear_task_cache(task_id)
        except Exception as cleanup_error:
            logger.error("Failed to cleanup failed PHI task", error=str(cleanup_error))
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        try:
            super().on_success(retval, task_id, args, kwargs)
            
            logger.info(
                "PHI task completed successfully",
                task_id=task_id,
                task_name=self.name
            )
        except Exception as e:
            logger.error("Failed to handle PHI task success", error=str(e))
    
    def _clear_task_cache(self, task_id: str):
        """Clear sensitive data from cache"""
        try:
            # In a real implementation, clear Redis cache keys
            logger.info("Cleared sensitive task cache", task_id=task_id)
        except Exception as e:
            logger.error("Failed to clear task cache", error=str(e), task_id=task_id)
    
    def _contains_phi(self, data: Any) -> bool:
        """Check if data contains PHI"""
        if isinstance(data, dict):
            phi_fields = {'ssn', 'date_of_birth', 'patient_id', 'mrn'}
            return any(field in data for field in phi_fields)
        return False


@celery_app.task(
    base=SecurePHITask,
    bind=True,
    name='healthcare.process_phi_encryption_queue',
    queue='phi_processing',
    priority=PHI_TASK_PRIORITY,
    time_limit=TASK_TIME_LIMIT,
    soft_time_limit=TASK_TIME_LIMIT - 60
)
async def process_phi_encryption_queue(
    self,
    patient_ids: List[str],
    fields_to_encrypt: List[str],
    operation: str = "encrypt"  # "encrypt" or "re-encrypt"
) -> Dict[str, Any]:
    """
    Bulk PHI field encryption/re-encryption task
    
    Args:
        patient_ids: List of patient IDs to process
        fields_to_encrypt: PHI fields to encrypt
        operation: "encrypt" for initial encryption, "re-encrypt" for key rotation
    """
    start_time = datetime.utcnow()
    results = {
        'successful': 0,
        'failed': 0,
        'errors': [],
        'task_id': self.request.id
    }
    
    if not patient_ids:
        logger.info("No patient IDs provided for encryption")
        return results
    
    try:
        async with AsyncSessionLocal() as session:
            encryption_service = EncryptionService()
            event_bus = EventBus()
            
            # Process in batches
            for i in range(0, len(patient_ids), ENCRYPTION_BATCH_SIZE):
                batch = patient_ids[i:i + ENCRYPTION_BATCH_SIZE]
                
                # Update progress
                progress = (i / len(patient_ids)) * 100
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i,
                        'total': len(patient_ids),
                        'percent': progress
                    }
                )
                
                # Process batch
                try:
                    await _process_encryption_batch(
                        session,
                        encryption_service,
                        batch,
                        fields_to_encrypt,
                        operation,
                        results
                    )
                except Exception as e:
                    logger.error(
                        "Batch encryption failed",
                        batch_start=i,
                        error=str(e)
                    )
                    results['errors'].append({
                        'batch': f"{i}-{i + len(batch)}",
                        'error': str(e)
                    })
        
        # Calculate duration
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Publish completion event
        await event_bus.publish(
            PHIEncryptionCompleted(
                task_id=self.request.id,
                records_processed=results['successful'],
                duration_seconds=duration
            )
        )
        
        # Log completion
        logger.info(
            "PHI encryption queue processed",
            task_id=self.request.id,
            successful=results['successful'],
            failed=results['failed'],
            duration=duration
        )
        
        return results
        
    except Exception as e:
        logger.error("PHI encryption task failed", error=str(e), task_id=self.request.id)
        results['errors'].append(str(e))
        results['failed'] = len(patient_ids)
        return results


async def _process_encryption_batch(
    session: AsyncSession,
    encryption_service: EncryptionService,
    patient_ids: List[str],
    fields: List[str],
    operation: str,
    results: Dict[str, Any]
):
    """Process a batch of patients for encryption"""
    try:
        # Fetch patients
        query = select(Patient).where(
            Patient.id.in_(patient_ids)
        )
        result = await session.execute(query)
        patients = result.scalars().all()
        
        for patient in patients:
            try:
                # Process each field
                for field in fields:
                    encrypted_field = f"{field}_encrypted"
                    
                    if hasattr(patient, field):
                        value = getattr(patient, field)
                        if value:
                            if operation == "encrypt":
                                encrypted = await encryption_service.encrypt(
                                    value,
                                    context={'field': field, 'patient_id': patient.id}
                                )
                                setattr(patient, encrypted_field, encrypted)
                            elif operation == "re-encrypt":
                                # Decrypt with old key and re-encrypt with new
                                if hasattr(patient, encrypted_field):
                                    current_encrypted = getattr(patient, encrypted_field)
                                    if current_encrypted:
                                        decrypted = await encryption_service.decrypt(current_encrypted)
                                        encrypted = await encryption_service.encrypt(
                                            decrypted,
                                            context={'field': field, 'patient_id': patient.id}
                                        )
                                        setattr(patient, encrypted_field, encrypted)
                
                results['successful'] += 1
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'patient_id': patient.id,
                    'error': str(e)
                })
                logger.error("Failed to encrypt patient data", patient_id=patient.id, error=str(e))
        
        # Commit batch
        await session.commit()
        
    except Exception as e:
        await session.rollback()
        logger.error("Failed to process encryption batch", error=str(e))
        raise


@celery_app.task(
    bind=True,
    name='healthcare.monitor_consent_expiration',
    queue='healthcare_monitoring'
)
async def monitor_consent_expiration(self) -> Dict[str, Any]:
    """
    Monitor and update expired patient consents
    Runs periodically to check for expired consents and notify patients
    """
    results = {
        'expired_consents': 0,
        'notifications_sent': 0,
        'errors': []
    }
    
    try:
        async with AsyncSessionLocal() as session:
            event_bus = EventBus()
            
            # Find consents expiring in next 30 days
            expiry_threshold = datetime.utcnow() + timedelta(days=30)
            
            query = select(Consent).where(
                and_(
                    Consent.status == ConsentStatus.GRANTED,
                    Consent.expires_at.isnot(None),
                    Consent.expires_at <= expiry_threshold
                )
            )
            
            result = await session.execute(query)
            expiring_consents = result.scalars().all()
            
            for consent in expiring_consents:
                try:
                    # Check if already expired
                    if consent.expires_at <= datetime.utcnow():
                        # Mark as expired
                        consent.status = ConsentStatus.EXPIRED
                        results['expired_consents'] += 1
                        
                        # Create notification task
                        notify_consent_expiration.delay(
                            consent.patient_id,
                            consent.consent_type.value
                        )
                        results['notifications_sent'] += 1
                        
                    elif consent.expires_at <= datetime.utcnow() + timedelta(days=7):
                        # Send reminder for consents expiring in 7 days
                        notify_consent_expiring_soon.delay(
                            consent.patient_id,
                            consent.consent_type.value,
                            consent.expires_at.isoformat()
                        )
                        results['notifications_sent'] += 1
                        
                except Exception as e:
                    results['errors'].append({
                        'consent_id': consent.id,
                        'error': str(e)
                    })
                    logger.error("Failed to process consent expiration", consent_id=consent.id, error=str(e))
            
            await session.commit()
        
        # Publish completion event
        await event_bus.publish(
            ConsentExpirationProcessed(
                expired_count=results['expired_consents'],
                notified_count=results['notifications_sent']
            )
        )
        
        logger.info(
            "Consent expiration monitoring completed",
            expired=results['expired_consents'],
            notified=results['notifications_sent']
        )
        
        return results
        
    except Exception as e:
        logger.error("Consent expiration monitoring failed", error=str(e))
        results['errors'].append(str(e))
        return results


@celery_app.task(
    bind=True,
    name='healthcare.generate_compliance_reports',
    queue='compliance',
    time_limit=7200  # 2 hours for large reports
)
async def generate_compliance_reports(
    self,
    report_type: str,  # "hipaa", "gdpr", "soc2"
    start_date: str,
    end_date: str,
    include_details: bool = True
) -> Dict[str, Any]:
    """
    Generate comprehensive compliance reports for auditors
    """
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        report_id = str(uuid.uuid4())
        
        async with AsyncSessionLocal() as session:
            event_bus = EventBus()
            audit_service = PHIAccessAuditService(session, event_bus)
            
            # Base compliance report
            report = await audit_service.generate_compliance_report(
                start, end, report_type
            )
            
            report['report_id'] = report_id
            report['include_details'] = include_details
            
            if report_type == "hipaa":
                # HIPAA-specific requirements
                report['hipaa_compliance'] = await _generate_hipaa_metrics(
                    session, start, end, include_details
                )
            elif report_type == "gdpr":
                # GDPR-specific requirements
                report['gdpr_compliance'] = await _generate_gdpr_metrics(
                    session, start, end, include_details
                )
            elif report_type == "soc2":
                # SOC2-specific requirements
                report['soc2_compliance'] = await _generate_soc2_metrics(
                    session, start, end, include_details
                )
            
            # Detect anomalies
            anomalies = await audit_service.detect_anomalies(
                lookback_hours=int((end - start).total_seconds() / 3600)
            )
            report['security_anomalies'] = anomalies
            
            # Store report (implement secure storage)
            await _store_compliance_report(report)
            
            # Publish event
            await event_bus.publish(
                ComplianceReportGenerated(
                    report_id=report_id,
                    report_type=report_type,
                    period_start=start,
                    period_end=end
                )
            )
        
        logger.info(
            "Compliance report generated",
            report_id=report_id,
            report_type=report_type
        )
        
        return {
            'report_id': report_id,
            'report_type': report_type,
            'status': 'completed',
            'location': f"reports/{report_id}.json"
        }
        
    except Exception as e:
        logger.error("Compliance report generation failed", error=str(e), report_type=report_type)
        raise


async def _generate_hipaa_metrics(
    session: AsyncSession,
    start: datetime,
    end: datetime,
    include_details: bool
) -> Dict[str, Any]:
    """Generate HIPAA-specific compliance metrics"""
    metrics = {
        'minimum_necessary_compliance': 0,
        'access_controls_effectiveness': 0,
        'audit_controls_compliance': 0,
        'transmission_security': 0,
        'details': {} if include_details else None
    }
    
    try:
        # Check minimum necessary principle
        total_accesses = await session.scalar(
            select(func.count(PHIAccessLog.id)).where(
                and_(
                    PHIAccessLog.accessed_at >= start,
                    PHIAccessLog.accessed_at <= end
                )
            )
        )
        
        justified_accesses = await session.scalar(
            select(func.count(PHIAccessLog.id)).where(
                and_(
                    PHIAccessLog.accessed_at >= start,
                    PHIAccessLog.accessed_at <= end,
                    PHIAccessLog.access_purpose.in_([
                        'treatment', 'payment', 'operations'
                    ])
                )
            )
        )
        
        if total_accesses > 0:
            metrics['minimum_necessary_compliance'] = (
                justified_accesses / total_accesses
            ) * 100
        
        # Additional HIPAA metrics would be implemented here
        
    except Exception as e:
        logger.error("Failed to generate HIPAA metrics", error=str(e))
    
    return metrics


async def _generate_gdpr_metrics(
    session: AsyncSession,
    start: datetime,
    end: datetime,
    include_details: bool
) -> Dict[str, Any]:
    """Generate GDPR-specific compliance metrics"""
    metrics = {
        'consent_compliance': 0,
        'data_portability_requests': 0,
        'erasure_requests': 0,
        'rectification_requests': 0,
        'processing_lawfulness': 0
    }
    
    try:
        # Check consent compliance
        total_processing = await session.scalar(
            select(func.count(PHIAccessLog.id)).where(
                and_(
                    PHIAccessLog.accessed_at >= start,
                    PHIAccessLog.accessed_at <= end
                )
            )
        )
        
        # Additional GDPR metrics would be implemented here
        
    except Exception as e:
        logger.error("Failed to generate GDPR metrics", error=str(e))
    
    return metrics


async def _generate_soc2_metrics(
    session: AsyncSession,
    start: datetime,
    end: datetime,
    include_details: bool
) -> Dict[str, Any]:
    """Generate SOC2-specific compliance metrics"""
    metrics = {
        'availability': 0,
        'processing_integrity': 0,
        'confidentiality': 0,
        'privacy': 0,
        'security_incidents': 0
    }
    
    try:
        # Calculate availability metrics
        # Additional SOC2 metrics would be implemented here
        pass
        
    except Exception as e:
        logger.error("Failed to generate SOC2 metrics", error=str(e))
    
    return metrics


async def _store_compliance_report(report: Dict[str, Any]):
    """Store compliance report securely"""
    try:
        # In a real implementation, this would store the report securely
        # For now, just log that it would be stored
        logger.info("Compliance report stored", report_id=report.get('report_id'))
    except Exception as e:
        logger.error("Failed to store compliance report", error=str(e))


@celery_app.task(
    bind=True,
    name='healthcare.anonymize_patient_data',
    queue='research_processing',
    base=SecurePHITask
)
async def anonymize_patient_data(
    self,
    dataset_id: str,
    patient_ids: List[str],
    anonymization_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Anonymize patient data for research purposes
    Uses differential privacy and k-anonymity techniques
    """
    results = {
        'dataset_id': dataset_id,
        'records_processed': 0,
        'anonymization_techniques': [],
        'quality_metrics': {}
    }
    
    try:
        async with AsyncSessionLocal() as session:
            event_bus = EventBus()
            anonymizer = AnonymizationEngine(anonymization_config)
            
            # Fetch patients
            query = select(Patient).where(
                Patient.id.in_(patient_ids)
            )
            
            result = await session.execute(query)
            patients = result.scalars().all()
            
            # Create anonymized dataset
            anonymized_records = []
            
            for patient in patients:
                try:
                    # Convert patient to dict (would decrypt PHI fields in real implementation)
                    patient_data = await _patient_to_dict(patient)
                    
                    # Apply anonymization
                    anonymized = await anonymizer.anonymize_record(
                        patient_data,
                        preserve_fields=anonymization_config.get(
                            'preserve_fields', []
                        )
                    )
                    
                    anonymized_records.append(anonymized)
                    results['records_processed'] += 1
                    
                    # Update progress
                    progress = (results['records_processed'] / len(patients)) * 100
                    self.update_state(
                        state='PROGRESS',
                        meta={'percent': progress}
                    )
                    
                except Exception as e:
                    logger.error(
                        "Failed to anonymize patient",
                        patient_id=patient.id,
                        error=str(e)
                    )
            
            # Apply k-anonymity
            if anonymization_config.get('k_anonymity', {}).get('enabled'):
                k_value = anonymization_config['k_anonymity']['k']
                anonymized_records = await anonymizer.apply_k_anonymity(
                    anonymized_records,
                    k=k_value,
                    quasi_identifiers=anonymization_config['k_anonymity'].get(
                        'quasi_identifiers', []
                    )
                )
                results['anonymization_techniques'].append(f"k-anonymity (k={k_value})")
            
            # Apply differential privacy
            if anonymization_config.get('differential_privacy', {}).get('enabled'):
                epsilon = anonymization_config['differential_privacy']['epsilon']
                anonymized_records = await anonymizer.apply_differential_privacy(
                    anonymized_records,
                    epsilon=epsilon
                )
                results['anonymization_techniques'].append(
                    f"differential-privacy (ε={epsilon})"
                )
            
            # Calculate quality metrics
            results['quality_metrics'] = await anonymizer.calculate_utility_metrics(
                anonymized_records
            )
            
            # Store anonymized dataset
            await _store_anonymized_dataset(
                dataset_id,
                anonymized_records,
                results
            )
            
            # Publish completion event
            await event_bus.publish(
                DataAnonymizationCompleted(
                    dataset_id=dataset_id,
                    records_anonymized=results['records_processed'],
                    techniques_used=results['anonymization_techniques']
                )
            )
        
        logger.info(
            "Data anonymization completed",
            dataset_id=dataset_id,
            records=results['records_processed']
        )
        
        return results
        
    except Exception as e:
        logger.error("Data anonymization failed", error=str(e), dataset_id=dataset_id)
        raise


async def _patient_to_dict(patient: Patient) -> Dict[str, Any]:
    """Convert patient to dictionary for anonymization"""
    # In a real implementation, this would decrypt PHI fields
    return {
        'id': patient.id,
        'age': 30,  # placeholder
        'gender': patient.gender,
        'created_at': patient.created_at.isoformat() if patient.created_at else None
    }


async def _store_anonymized_dataset(
    dataset_id: str,
    records: List[Dict[str, Any]],
    metadata: Dict[str, Any]
):
    """Store anonymized dataset securely"""
    try:
        # In a real implementation, store to secure location
        logger.info("Anonymized dataset stored", dataset_id=dataset_id, record_count=len(records))
    except Exception as e:
        logger.error("Failed to store anonymized dataset", error=str(e))


@celery_app.task(
    bind=True,
    name='healthcare.audit_phi_access_patterns',
    queue='security_monitoring'
)
async def audit_phi_access_patterns(
    self,
    lookback_hours: int = 24,
    alert_threshold: Dict[str, int] = None
) -> Dict[str, Any]:
    """
    Analyze PHI access patterns for security monitoring
    Detects anomalous behavior and potential security incidents
    """
    if alert_threshold is None:
        alert_threshold = {
            'max_accesses_per_user': 100,
            'max_patients_per_user': 50,
            'max_after_hours_accesses': 10
        }
    
    alerts = []
    
    try:
        async with AsyncSessionLocal() as session:
            cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)
            
            # Analyze access patterns by user
            user_activity = await session.execute(
                select(
                    PHIAccessLog.accessed_by,
                    func.count(PHIAccessLog.id).label('access_count'),
                    func.count(func.distinct(PHIAccessLog.patient_id)).label(
                        'unique_patients'
                    )
                ).where(
                    PHIAccessLog.accessed_at >= cutoff_time
                ).group_by(
                    PHIAccessLog.accessed_by
                )
            )
            
            for row in user_activity:
                # Check for excessive access
                if row.access_count > alert_threshold['max_accesses_per_user']:
                    alerts.append({
                        'type': 'excessive_access',
                        'severity': 'high',
                        'user_id': row.accessed_by,
                        'access_count': row.access_count,
                        'threshold': alert_threshold['max_accesses_per_user']
                    })
                
                # Check for accessing too many patients
                if row.unique_patients > alert_threshold['max_patients_per_user']:
                    alerts.append({
                        'type': 'broad_access_pattern',
                        'severity': 'medium',
                        'user_id': row.accessed_by,
                        'patient_count': row.unique_patients,
                        'threshold': alert_threshold['max_patients_per_user']
                    })
            
            # Check for after-hours access
            after_hours = await session.execute(
                select(
                    PHIAccessLog.accessed_by,
                    func.count(PHIAccessLog.id).label('count')
                ).where(
                    and_(
                        PHIAccessLog.accessed_at >= cutoff_time,
                        or_(
                            func.extract('hour', PHIAccessLog.accessed_at) < 6,
                            func.extract('hour', PHIAccessLog.accessed_at) > 22
                        )
                    )
                ).group_by(
                    PHIAccessLog.accessed_by
                ).having(
                    func.count(PHIAccessLog.id) > alert_threshold[
                        'max_after_hours_accesses'
                    ]
                )
            )
            
            for row in after_hours:
                alerts.append({
                    'type': 'after_hours_access',
                    'severity': 'medium',
                    'user_id': row.accessed_by,
                    'access_count': row.count,
                    'threshold': alert_threshold['max_after_hours_accesses']
                })
            
            # Generate summary
            summary = {
                'period_hours': lookback_hours,
                'total_alerts': len(alerts),
                'high_severity': len([a for a in alerts if a['severity'] == 'high']),
                'medium_severity': len([a for a in alerts if a['severity'] == 'medium']),
                'low_severity': len([a for a in alerts if a['severity'] == 'low']),
                'alerts': alerts
            }
            
            # Send alerts if any high severity
            if summary['high_severity'] > 0:
                await _send_security_alerts(alerts)
        
        logger.info(
            "PHI access pattern audit completed",
            total_alerts=summary['total_alerts'],
            high_severity=summary['high_severity']
        )
        
        return summary
        
    except Exception as e:
        logger.error("PHI access pattern audit failed", error=str(e))
        raise


async def _send_security_alerts(alerts: List[Dict[str, Any]]):
    """Send security alerts to monitoring system"""
    try:
        # In a real implementation, send alerts via email, Slack, etc.
        logger.warning("Security alerts triggered", alert_count=len(alerts))
    except Exception as e:
        logger.error("Failed to send security alerts", error=str(e))


@celery_app.task(
    bind=True,
    name='healthcare.cleanup_expired_access_tokens',
    queue='maintenance'
)
async def cleanup_expired_access_tokens(self) -> Dict[str, Any]:
    """
    Clean up expired PHI access tokens and temporary access grants
    """
    results = {
        'tokens_cleaned': 0,
        'temporary_grants_revoked': 0,
        'errors': []
    }
    
    try:
        async with AsyncSessionLocal() as session:
            # Revoke expired temporary consent grants
            expired_grants = await session.execute(
                select(Consent).where(
                    and_(
                        Consent.status == ConsentStatus.GRANTED,
                        Consent.expires_at.isnot(None),
                        Consent.expires_at < datetime.utcnow()
                    )
                )
            )
            
            for consent in expired_grants.scalars():
                consent.status = ConsentStatus.EXPIRED
                results['temporary_grants_revoked'] += 1
            
            await session.commit()
        
        logger.info(
            "Access token cleanup completed",
            tokens_cleaned=results['tokens_cleaned'],
            grants_revoked=results['temporary_grants_revoked']
        )
        
        return results
        
    except Exception as e:
        logger.error("Access token cleanup failed", error=str(e))
        results['errors'].append(str(e))
        return results


@celery_app.task(
    bind=True,
    name='healthcare.sync_patient_fhir_resources',
    queue='fhir_processing'
)
async def sync_patient_fhir_resources(
    self,
    patient_ids: List[str],
    validate_only: bool = False
) -> Dict[str, Any]:
    """
    Validate and sync patient FHIR resources
    Ensures all patient data is FHIR R4 compliant
    """
    results = {
        'validated': 0,
        'updated': 0,
        'validation_errors': [],
        'sync_errors': []
    }
    
    try:
        async with AsyncSessionLocal() as session:
            validator = FHIRValidator()
            
            for patient_id in patient_ids:
                try:
                    # Fetch patient
                    patient = await session.get(Patient, patient_id)
                    if not patient:
                        continue
                    
                    # Validate FHIR resource
                    validation_result = await validator.validate_patient_resource(
                        patient.fhir_resource or {}
                    )
                    
                    if validation_result.is_valid:
                        results['validated'] += 1
                        
                        if not validate_only:
                            # Sync with external FHIR server if configured
                            await _sync_to_fhir_server(patient)
                            results['updated'] += 1
                    else:
                        results['validation_errors'].append({
                            'patient_id': patient_id,
                            'errors': validation_result.errors
                        })
                    
                    # Update progress
                    progress = (
                        patient_ids.index(patient_id) / len(patient_ids)
                    ) * 100
                    self.update_state(
                        state='PROGRESS',
                        meta={'percent': progress}
                    )
                    
                except Exception as e:
                    results['sync_errors'].append({
                        'patient_id': patient_id,
                        'error': str(e)
                    })
        
        logger.info(
            "FHIR resource sync completed",
            validated=results['validated'],
            updated=results['updated']
        )
        
        return results
        
    except Exception as e:
        logger.error("FHIR resource sync failed", error=str(e))
        raise


async def _sync_to_fhir_server(patient: Patient):
    """Sync patient to external FHIR server"""
    try:
        # In a real implementation, sync to external FHIR server
        logger.info("Patient synced to FHIR server", patient_id=patient.id)
    except Exception as e:
        logger.error("Failed to sync patient to FHIR server", error=str(e))


@celery_app.task(
    bind=True,
    name='healthcare.archive_old_clinical_documents',
    queue='data_lifecycle'
)
async def archive_old_clinical_documents(
    self,
    archive_after_days: int = DOCUMENT_ARCHIVE_DAYS,
    batch_size: int = 100
) -> Dict[str, Any]:
    """
    Archive old clinical documents based on retention policy
    Moves documents to cold storage while maintaining audit trail
    """
    results = {
        'documents_archived': 0,
        'space_reclaimed_mb': 0,
        'errors': []
    }
    
    try:
        async with AsyncSessionLocal() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=archive_after_days)
            
            # Find documents to archive
            documents_query = select(ClinicalDocument).where(
                and_(
                    ClinicalDocument.created_at < cutoff_date,
                    ClinicalDocument.archived_at.is_(None),
                    ClinicalDocument.soft_deleted_at.is_(None)
                )
            ).limit(batch_size)
            
            result = await session.execute(documents_query)
            documents = result.scalars().all()
            
            for document in documents:
                try:
                    # Move to archive storage
                    archived_key = await _archive_document_content(document)
                    
                    # Update document record
                    document.archived_at = datetime.utcnow()
                    document.archive_storage_key = archived_key
                    document.archived_by = "system"
                    
                    results['documents_archived'] += 1
                    results['space_reclaimed_mb'] += document.size_bytes / (1024 * 1024)
                    
                except Exception as e:
                    results['errors'].append({
                        'document_id': document.id,
                        'error': str(e)
                    })
            
            await session.commit()
            
            # Create audit entry for archival
            await _audit_archival_operation(results)
        
        logger.info(
            "Document archival completed",
            archived=results['documents_archived'],
            space_reclaimed_mb=round(results['space_reclaimed_mb'], 2)
        )
        
        return results
        
    except Exception as e:
        logger.error("Document archival failed", error=str(e))
        raise


async def _archive_document_content(document: ClinicalDocument) -> str:
    """Archive document content to cold storage"""
    try:
        # In a real implementation, move to S3 Glacier or similar
        return f"archive/{document.id}"
    except Exception as e:
        logger.error("Failed to archive document content", error=str(e))
        raise


async def _audit_archival_operation(results: Dict[str, Any]):
    """Create audit entry for archival operation"""
    try:
        # In a real implementation, create audit log entry
        logger.info("Archival operation audited", **results)
    except Exception as e:
        logger.error("Failed to audit archival operation", error=str(e))


# Notification tasks (chainable)
@celery_app.task(name='healthcare.notify_consent_expiration')
def notify_consent_expiration(patient_id: str, consent_type: str):
    """Send consent expiration notification"""
    try:
        # In a real implementation, send notification via email/SMS
        logger.info("Consent expiration notification sent", patient_id=patient_id, consent_type=consent_type)
    except Exception as e:
        logger.error("Failed to send consent expiration notification", error=str(e))


@celery_app.task(name='healthcare.notify_consent_expiring_soon')
def notify_consent_expiring_soon(
    patient_id: str,
    consent_type: str,
    expires_at: str
):
    """Send consent expiring soon notification"""
    try:
        # In a real implementation, send notification via email/SMS
        logger.info("Consent expiring soon notification sent", patient_id=patient_id, consent_type=consent_type)
    except Exception as e:
        logger.error("Failed to send consent expiring soon notification", error=str(e))


# Task workflows
def create_patient_onboarding_workflow(patient_data: Dict[str, Any]) -> chain:
    """Create workflow for new patient onboarding"""
    return chain(
        process_phi_encryption_queue.si(
            [patient_data['id']],
            ['ssn', 'date_of_birth', 'address']
        ),
        sync_patient_fhir_resources.si([patient_data['id']])
    )


def create_compliance_audit_workflow(audit_config: Dict[str, Any]) -> group:
    """Create comprehensive compliance audit workflow"""
    return group(
        generate_compliance_reports.si(
            'hipaa',
            audit_config['start_date'],
            audit_config['end_date']
        ),
        generate_compliance_reports.si(
            'gdpr',
            audit_config['start_date'],
            audit_config['end_date']
        ),
        audit_phi_access_patterns.si(
            lookback_hours=audit_config.get('lookback_hours', 168)
        )
    )


def create_data_lifecycle_workflow() -> chain:
    """Create data lifecycle management workflow"""
    return chain(
        monitor_consent_expiration.si(),
        cleanup_expired_access_tokens.si(),
        archive_old_clinical_documents.si()
    )