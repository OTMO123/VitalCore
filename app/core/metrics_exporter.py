"""
Prometheus Metrics Exporter for Healthcare Records Backend

Production-grade metrics collection and export for Prometheus monitoring:
- Healthcare-specific business metrics
- Performance and SLA monitoring
- HIPAA and SOC2 compliance metrics
- Security and audit trail metrics
- Database and cache performance metrics
- Custom healthcare KPIs and alerts

This module exposes all critical metrics needed for comprehensive
monitoring and alerting in a healthcare production environment.
"""

import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog

from prometheus_client import (
    Counter, Histogram, Gauge, Summary, Info, Enum,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
from fastapi import APIRouter, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func, select

from app.core.database_unified import get_db
from app.core.config import get_settings
from app.core.redis_caching import cache_manager
from app.core.audit_logging_optimized import optimized_audit_logger

logger = structlog.get_logger()

# Create custom registry for healthcare metrics
healthcare_registry = CollectorRegistry()

# =============================================================================
# CORE SYSTEM METRICS
# =============================================================================

# API Performance Metrics
http_requests_total = Counter(
    'healthcare_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=healthcare_registry
)

http_request_duration_seconds = Histogram(
    'healthcare_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=healthcare_registry
)

# Database Metrics
db_connections_active = Gauge(
    'healthcare_db_connections_active',
    'Number of active database connections',
    registry=healthcare_registry
)

db_connections_max = Gauge(
    'healthcare_db_connections_max',
    'Maximum database connections',
    registry=healthcare_registry
)

db_query_duration_seconds = Histogram(
    'healthcare_db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
    registry=healthcare_registry
)

db_queries_total = Counter(
    'healthcare_db_queries_total',
    'Total database queries',
    ['query_type', 'status'],
    registry=healthcare_registry
)

# =============================================================================
# HEALTHCARE BUSINESS METRICS
# =============================================================================

# Patient Management Metrics
patients_total = Gauge(
    'healthcare_patients_total',
    'Total number of patients in system',
    registry=healthcare_registry
)

patients_created_total = Counter(
    'healthcare_patients_created_total',
    'Total patients created',
    ['organization'],
    registry=healthcare_registry
)

patients_accessed_total = Counter(
    'healthcare_patients_accessed_total',
    'Total patient record access events',
    ['user_role', 'access_type'],
    registry=healthcare_registry
)

# Immunization Metrics
immunizations_total = Gauge(
    'healthcare_immunizations_total',
    'Total immunizations in system',
    registry=healthcare_registry
)

immunizations_recorded_total = Counter(
    'healthcare_immunizations_recorded_total',
    'Total immunizations recorded',
    ['vaccine_code', 'organization'],
    registry=healthcare_registry
)

immunization_adverse_events_total = Counter(
    'healthcare_immunization_adverse_events_total',
    'Total immunization adverse events',
    ['severity', 'vaccine_code'],
    registry=healthcare_registry
)

# Clinical Document Metrics
documents_total = Gauge(
    'healthcare_documents_total',
    'Total clinical documents in system',
    registry=healthcare_registry
)

documents_uploaded_total = Counter(
    'healthcare_documents_uploaded_total',
    'Total documents uploaded',
    ['document_type', 'organization'],
    registry=healthcare_registry
)

documents_accessed_total = Counter(
    'healthcare_documents_accessed_total',
    'Total document access events',
    ['document_type', 'user_role'],
    registry=healthcare_registry
)

# =============================================================================
# COMPLIANCE AND SECURITY METRICS
# =============================================================================

# PHI Access Metrics
phi_access_total = Counter(
    'healthcare_phi_access_total',
    'Total PHI access events',
    ['user_role', 'resource_type', 'outcome'],
    registry=healthcare_registry
)

phi_access_denied_total = Counter(
    'healthcare_phi_access_denied_total',
    'Total PHI access denied events',
    ['reason', 'user_role'],
    registry=healthcare_registry
)

phi_encryption_operations_total = Counter(
    'healthcare_phi_encryption_operations_total',
    'Total PHI encryption/decryption operations',
    ['operation', 'status'],
    registry=healthcare_registry
)

# Audit Trail Metrics
audit_events_total = Counter(
    'healthcare_audit_events_total',
    'Total audit events logged',
    ['event_type', 'log_level'],
    registry=healthcare_registry
)

audit_buffer_size = Gauge(
    'healthcare_audit_buffer_size',
    'Current audit log buffer size',
    registry=healthcare_registry
)

audit_events_processed_total = Counter(
    'healthcare_audit_events_processed_total',
    'Total audit events processed',
    ['batch_status'],
    registry=healthcare_registry
)

audit_processing_duration_seconds = Histogram(
    'healthcare_audit_processing_duration_seconds',
    'Audit batch processing duration',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    registry=healthcare_registry
)

# Authentication and Authorization Metrics
auth_attempts_total = Counter(
    'healthcare_auth_attempts_total',
    'Total authentication attempts',
    ['method', 'outcome'],
    registry=healthcare_registry
)

auth_failed_total = Counter(
    'healthcare_auth_failed_total',
    'Total failed authentication attempts',
    ['reason', 'method'],
    registry=healthcare_registry
)

jwt_tokens_issued_total = Counter(
    'healthcare_jwt_tokens_issued_total',
    'Total JWT tokens issued',
    ['token_type'],
    registry=healthcare_registry
)

jwt_invalid_total = Counter(
    'healthcare_jwt_invalid_total',
    'Total invalid JWT tokens',
    ['reason'],
    registry=healthcare_registry
)

# Consent Management Metrics
consent_grants_total = Counter(
    'healthcare_consent_grants_total',
    'Total consent grants',
    ['consent_type', 'method'],
    registry=healthcare_registry
)

consent_validations_total = Counter(
    'healthcare_consent_validations_total',
    'Total consent validations',
    ['outcome', 'consent_type'],
    registry=healthcare_registry
)

consent_validation_failed_total = Counter(
    'healthcare_consent_validation_failed_total',
    'Total failed consent validations',
    ['reason'],
    registry=healthcare_registry
)

# =============================================================================
# FHIR COMPLIANCE METRICS
# =============================================================================

fhir_validation_total = Counter(
    'healthcare_fhir_validation_total',
    'Total FHIR resource validations',
    ['resource_type', 'outcome'],
    registry=healthcare_registry
)

fhir_validation_success_total = Counter(
    'healthcare_fhir_validation_success_total',
    'Total successful FHIR validations',
    ['resource_type'],
    registry=healthcare_registry
)

fhir_validation_failed_total = Counter(
    'healthcare_fhir_validation_failed_total',
    'Total failed FHIR validations',
    ['resource_type', 'error_type'],
    registry=healthcare_registry
)

fhir_validation_duration_seconds = Histogram(
    'healthcare_fhir_validation_duration_seconds',
    'FHIR validation duration',
    ['resource_type'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=healthcare_registry
)

# =============================================================================
# CACHE AND PERFORMANCE METRICS
# =============================================================================

cache_requests_total = Counter(
    'healthcare_cache_requests_total',
    'Total cache requests',
    ['cache_type', 'operation'],
    registry=healthcare_registry
)

cache_hits_total = Counter(
    'healthcare_cache_hits_total',
    'Total cache hits',
    ['cache_type'],
    registry=healthcare_registry
)

cache_misses_total = Counter(
    'healthcare_cache_misses_total',
    'Total cache misses',
    ['cache_type'],
    registry=healthcare_registry
)

cache_hit_rate = Gauge(
    'healthcare_cache_hit_rate',
    'Cache hit rate percentage',
    ['cache_type'],
    registry=healthcare_registry
)

# Rate Limiting Metrics
rate_limit_requests_total = Counter(
    'healthcare_rate_limit_requests_total',
    'Total rate limit checks',
    ['endpoint', 'outcome'],
    registry=healthcare_registry
)

rate_limit_exceeded_total = Counter(
    'healthcare_rate_limit_exceeded_total',
    'Total rate limit violations',
    ['endpoint', 'client_type'],
    registry=healthcare_registry
)

# =============================================================================
# EXTERNAL INTEGRATION METRICS
# =============================================================================

iris_api_requests_total = Counter(
    'healthcare_iris_api_requests_total',
    'Total IRIS API requests',
    ['operation', 'status'],
    registry=healthcare_registry
)

iris_api_duration_seconds = Histogram(
    'healthcare_iris_api_duration_seconds',
    'IRIS API request duration',
    ['operation'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    registry=healthcare_registry
)

iris_sync_operations_total = Counter(
    'healthcare_iris_sync_operations_total',
    'Total IRIS sync operations',
    ['sync_type', 'outcome'],
    registry=healthcare_registry
)

# =============================================================================
# ERROR AND EXCEPTION METRICS
# =============================================================================

exceptions_total = Counter(
    'healthcare_exceptions_total',
    'Total exceptions caught',
    ['exception_type', 'module'],
    registry=healthcare_registry
)

encryption_failed_total = Counter(
    'healthcare_encryption_failed_total',
    'Total encryption failures',
    ['operation', 'error_type'],
    registry=healthcare_registry
)

data_validation_errors_total = Counter(
    'healthcare_data_validation_errors_total',
    'Total data validation errors',
    ['validation_type', 'field'],
    registry=healthcare_registry
)

# =============================================================================
# BUSINESS KPI METRICS
# =============================================================================

system_uptime_seconds = Gauge(
    'healthcare_system_uptime_seconds',
    'System uptime in seconds',
    registry=healthcare_registry
)

active_user_sessions = Gauge(
    'healthcare_active_user_sessions',
    'Number of active user sessions',
    registry=healthcare_registry
)

data_retention_violations_total = Counter(
    'healthcare_data_retention_violations_total',
    'Total data retention policy violations',
    ['data_type', 'violation_type'],
    registry=healthcare_registry
)


@dataclass
class MetricsCollector:
    """Collects and updates healthcare metrics from various sources."""
    
    def __init__(self):
        self.settings = get_settings()
        self.start_time = time.time()
        
    async def update_database_metrics(self, session: AsyncSession) -> None:
        """Update database-related metrics."""
        try:
            # Update patient count
            patient_count_result = await session.execute(
                text("SELECT COUNT(*) FROM patients WHERE active = true AND soft_deleted_at IS NULL")
            )
            patient_count = patient_count_result.scalar()
            patients_total.set(patient_count)
            
            # Update immunization count
            immunization_count_result = await session.execute(
                text("SELECT COUNT(*) FROM immunizations WHERE soft_deleted_at IS NULL")
            )
            immunization_count = immunization_count_result.scalar()
            immunizations_total.set(immunization_count)
            
            # Update document count
            document_count_result = await session.execute(
                text("SELECT COUNT(*) FROM clinical_documents WHERE soft_deleted_at IS NULL")
            )
            document_count = document_count_result.scalar()
            documents_total.set(document_count)
            
            # Update database connection metrics (if available)
            try:
                connection_stats = await session.execute(
                    text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
                )
                active_connections = connection_stats.scalar()
                db_connections_active.set(active_connections)
            except Exception:
                # Handle case where pg_stat_activity is not accessible
                pass
                
        except Exception as e:
            logger.error("Failed to update database metrics", error=str(e))
    
    async def update_cache_metrics(self) -> None:
        """Update cache performance metrics."""
        try:
            cache_stats = await cache_manager.get_performance_metrics()
            
            # Update cache hit rate
            cache_performance = cache_stats.get("cache_performance", {})
            hit_rate = cache_performance.get("hit_rate_percent", 0)
            cache_hit_rate.labels(cache_type="redis").set(hit_rate)
            
        except Exception as e:
            logger.error("Failed to update cache metrics", error=str(e))
    
    async def update_audit_metrics(self) -> None:
        """Update audit logging metrics."""
        try:
            audit_performance = await optimized_audit_logger.get_performance_metrics()
            
            # Update buffer size
            buffer_stats = audit_performance.get("buffer_statistics", {})
            current_buffer_size = buffer_stats.get("current_size", 0)
            audit_buffer_size.set(current_buffer_size)
            
        except Exception as e:
            logger.error("Failed to update audit metrics", error=str(e))
    
    def update_system_metrics(self) -> None:
        """Update system-level metrics."""
        try:
            # Update system uptime
            uptime = time.time() - self.start_time
            system_uptime_seconds.set(uptime)
            
        except Exception as e:
            logger.error("Failed to update system metrics", error=str(e))


# Global metrics collector
metrics_collector = MetricsCollector()

# =============================================================================
# METRICS ENDPOINT
# =============================================================================

metrics_router = APIRouter(prefix="/metrics", tags=["metrics"])

@metrics_router.get("/")
async def get_prometheus_metrics():
    """Endpoint for Prometheus to scrape metrics."""
    return Response(
        generate_latest(healthcare_registry),
        media_type=CONTENT_TYPE_LATEST
    )

@metrics_router.get("/healthcare")
async def get_healthcare_metrics(session: AsyncSession = Depends(get_db)):
    """Get comprehensive healthcare metrics."""
    
    # Update all metrics before returning
    await metrics_collector.update_database_metrics(session)
    await metrics_collector.update_cache_metrics()
    await metrics_collector.update_audit_metrics()
    metrics_collector.update_system_metrics()
    
    return Response(
        generate_latest(healthcare_registry),
        media_type=CONTENT_TYPE_LATEST
    )

@metrics_router.get("/health")
async def metrics_health_check():
    """Health check for metrics endpoint."""
    return {
        "status": "healthy",
        "metrics_registry": "healthcare_registry",
        "collectors_count": len(healthcare_registry._collector_to_names),
        "uptime_seconds": time.time() - metrics_collector.start_time
    }

# =============================================================================
# METRICS HELPER FUNCTIONS
# =============================================================================

class HealthcareMetrics:
    """Helper class for recording healthcare-specific metrics."""
    
    @staticmethod
    def record_phi_access(user_role: str, resource_type: str, outcome: str):
        """Record PHI access event."""
        phi_access_total.labels(
            user_role=user_role,
            resource_type=resource_type,
            outcome=outcome
        ).inc()
    
    @staticmethod
    def record_phi_access_denied(reason: str, user_role: str):
        """Record PHI access denial."""
        phi_access_denied_total.labels(
            reason=reason,
            user_role=user_role
        ).inc()
    
    @staticmethod
    def record_patient_created(organization: str = "default"):
        """Record patient creation."""
        patients_created_total.labels(organization=organization).inc()
    
    @staticmethod
    def record_immunization_recorded(vaccine_code: str, organization: str = "default"):
        """Record immunization."""
        immunizations_recorded_total.labels(
            vaccine_code=vaccine_code,
            organization=organization
        ).inc()
    
    @staticmethod
    def record_document_uploaded(document_type: str, organization: str = "default"):
        """Record document upload."""
        documents_uploaded_total.labels(
            document_type=document_type,
            organization=organization
        ).inc()
    
    @staticmethod
    def record_fhir_validation(resource_type: str, outcome: str):
        """Record FHIR validation."""
        fhir_validation_total.labels(
            resource_type=resource_type,
            outcome=outcome
        ).inc()
        
        if outcome == "success":
            fhir_validation_success_total.labels(resource_type=resource_type).inc()
        else:
            fhir_validation_failed_total.labels(
                resource_type=resource_type,
                error_type=outcome
            ).inc()
    
    @staticmethod
    def record_audit_event(event_type: str, log_level: str):
        """Record audit event."""
        audit_events_total.labels(
            event_type=event_type,
            log_level=log_level
        ).inc()
    
    @staticmethod
    def record_auth_attempt(method: str, outcome: str):
        """Record authentication attempt."""
        auth_attempts_total.labels(
            method=method,
            outcome=outcome
        ).inc()
        
        if outcome != "success":
            auth_failed_total.labels(
                reason=outcome,
                method=method
            ).inc()
    
    @staticmethod
    def record_consent_operation(operation: str, consent_type: str, outcome: str):
        """Record consent management operation."""
        if operation == "grant":
            consent_grants_total.labels(
                consent_type=consent_type,
                method="api"
            ).inc()
        elif operation == "validate":
            consent_validations_total.labels(
                outcome=outcome,
                consent_type=consent_type
            ).inc()
            
            if outcome != "success":
                consent_validation_failed_total.labels(reason=outcome).inc()
    
    @staticmethod
    def time_operation(metric_histogram, labels: dict = None):
        """Decorator to time operations."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    if labels:
                        metric_histogram.labels(**labels).observe(duration)
                    else:
                        metric_histogram.observe(duration)
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    if labels:
                        metric_histogram.labels(**labels).observe(duration)
                    else:
                        metric_histogram.observe(duration)
                    raise
            return wrapper
        return decorator


# Export metrics helper instance
healthcare_metrics = HealthcareMetrics()