"""
Cross-Module Event Handlers for Healthcare System

This module implements event handlers that provide cross-module integration
through domain events. Each handler responds to specific events and coordinates
actions across different bounded contexts while maintaining loose coupling.

Key handlers include:
- Audit logging for all security and compliance events
- Analytics recalculation triggers  
- Dashboard data refresh
- Compliance monitoring and alerting
- Cross-module data synchronization
- Security incident response
- IRIS API integration monitoring
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import structlog

from app.core.event_bus_advanced import BaseEvent, EventHandler, TypedEventHandler
from app.core.events.definitions import (
    EventCategory,
    # Patient events
    PatientCreated, PatientUpdated, PatientDeactivated, PatientMerged,
    # Immunization events
    ImmunizationRecorded, ImmunizationUpdated, ImmunizationDeleted,
    # Document events
    DocumentUploaded, DocumentClassified, DocumentProcessed, DocumentVersionCreated,
    # Workflow events
    WorkflowInstanceCreated, WorkflowStepCompleted, WorkflowInstanceCompleted,
    # Security events
    SecurityViolationDetected, UnauthorizedAccessAttempt, PHIAccessLogged,
    # Audit events
    AuditLogCreated, ComplianceViolationDetected,
    # IRIS events
    IRISConnectionEstablished, IRISDataSynchronized, IRISAPIError,
    # Analytics events
    AnalyticsCalculationCompleted, ReportGenerated,
    # Consent events
    ConsentProvided, ConsentRevoked
)

logger = structlog.get_logger()


# ============================================
# AUDIT LOGGING HANDLERS
# ============================================

class AuditLoggingHandler(TypedEventHandler):
    """Handler for comprehensive audit logging of security-sensitive events."""
    
    def __init__(self):
        # Subscribe to all security, PHI access, and compliance events
        event_types = [
            SecurityViolationDetected,
            UnauthorizedAccessAttempt,
            PHIAccessLogged,
            ComplianceViolationDetected,
            PatientCreated,
            PatientUpdated,
            PatientDeactivated,
            ConsentProvided,
            ConsentRevoked,
            ImmunizationRecorded,
            DocumentUploaded
        ]
        super().__init__("audit_logger", event_types)
        self.logger = logger.bind(handler="audit_logger")
    
    async def handle(self, event: BaseEvent) -> bool:
        """Process audit-required events."""
        try:
            audit_data = await self._prepare_audit_data(event)
            
            # Route to appropriate audit logger based on event type
            if isinstance(event, (SecurityViolationDetected, UnauthorizedAccessAttempt)):
                await self._log_security_event(event, audit_data)
            elif isinstance(event, PHIAccessLogged):
                await self._log_phi_access(event, audit_data)
            elif isinstance(event, (ConsentProvided, ConsentRevoked)):
                await self._log_consent_event(event, audit_data)
            elif isinstance(event, (PatientCreated, PatientUpdated, PatientDeactivated)):
                await self._log_patient_event(event, audit_data)
            else:
                await self._log_general_event(event, audit_data)
            
            self.logger.info("Audit log created", 
                           event_type=event.event_type,
                           event_id=event.event_id)
            return True
            
        except Exception as e:
            self.logger.error("Audit logging failed", 
                            event_type=event.event_type,
                            error=str(e))
            return False
    
    async def _prepare_audit_data(self, event: BaseEvent) -> Dict[str, Any]:
        """Prepare standardized audit data."""
        return {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "aggregate_id": event.aggregate_id,
            "aggregate_type": event.aggregate_type,
            "timestamp": event.timestamp,
            "correlation_id": event.correlation_id,
            "publisher": event.publisher,
            "event_data": event.dict(),
            "audit_timestamp": datetime.utcnow(),
            "audit_source": "event_handler"
        }
    
    async def _log_security_event(self, event: BaseEvent, audit_data: Dict[str, Any]):
        """Log security-related events with high priority."""
        # This would integrate with your existing audit logger service
        self.logger.critical("Security event audit",
                           violation_type=getattr(event, 'violation_type', 'unknown'),
                           severity=getattr(event, 'severity', 'high'),
                           **audit_data)
    
    async def _log_phi_access(self, event: PHIAccessLogged, audit_data: Dict[str, Any]):
        """Log PHI access with HIPAA compliance details."""
        self.logger.info("PHI access audit",
                        user_id=event.user_id,
                        patient_id=event.patient_id,
                        fields_accessed=event.phi_fields_accessed,
                        legal_basis=event.legal_basis,
                        consent_verified=event.consent_verified,
                        **audit_data)
    
    async def _log_consent_event(self, event: BaseEvent, audit_data: Dict[str, Any]):
        """Log consent-related events for GDPR compliance."""
        self.logger.info("Consent event audit",
                        patient_id=getattr(event, 'patient_id', None),
                        consent_type=getattr(event, 'consent_type', None),
                        **audit_data)
    
    async def _log_patient_event(self, event: BaseEvent, audit_data: Dict[str, Any]):
        """Log patient lifecycle events."""
        self.logger.info("Patient event audit",
                        patient_id=getattr(event, 'patient_id', None),
                        **audit_data)
    
    async def _log_general_event(self, event: BaseEvent, audit_data: Dict[str, Any]):
        """Log general audit-required events."""
        self.logger.info("General event audit", **audit_data)


# ============================================
# ANALYTICS RECALCULATION HANDLER
# ============================================

class AnalyticsRecalculationHandler(TypedEventHandler):
    """Handler for triggering analytics recalculation based on data changes."""
    
    def __init__(self):
        # Subscribe to events that affect analytics
        event_types = [
            PatientCreated, PatientUpdated, PatientDeactivated,
            ImmunizationRecorded, ImmunizationUpdated, ImmunizationDeleted,
            DocumentUploaded, DocumentClassified,
            WorkflowInstanceCompleted,
            IRISDataSynchronized
        ]
        super().__init__("analytics_recalculator", event_types)
        self.logger = logger.bind(handler="analytics_recalculator")
        self._pending_recalculations: Set[str] = set()
        self._batch_delay_seconds = 30  # Batch recalculations
    
    async def handle(self, event: BaseEvent) -> bool:
        """Handle events that require analytics recalculation."""
        try:
            recalc_types = await self._determine_recalculation_types(event)
            
            for recalc_type in recalc_types:
                self._pending_recalculations.add(recalc_type)
                self.logger.info("Analytics recalculation queued",
                               recalc_type=recalc_type,
                               trigger_event=event.event_type)
            
            # Schedule batch processing
            asyncio.create_task(self._process_pending_recalculations())
            
            return True
            
        except Exception as e:
            self.logger.error("Analytics recalculation handler error", 
                            event_type=event.event_type,
                            error=str(e))
            return False
    
    async def _determine_recalculation_types(self, event: BaseEvent) -> List[str]:
        """Determine which analytics need recalculation based on event."""
        recalc_types = []
        
        if isinstance(event, (PatientCreated, PatientUpdated, PatientDeactivated)):
            recalc_types.extend(["patient_demographics", "population_statistics"])
            
        if isinstance(event, (ImmunizationRecorded, ImmunizationUpdated, ImmunizationDeleted)):
            recalc_types.extend(["immunization_coverage", "vaccine_effectiveness"])
            
        if isinstance(event, PatientCreated) and getattr(event, 'birth_year', None):
            recalc_types.append("age_distribution")
            
        if isinstance(event, DocumentUploaded):
            recalc_types.append("document_statistics")
            
        if isinstance(event, WorkflowInstanceCompleted):
            recalc_types.extend(["workflow_efficiency", "quality_metrics"])
            
        if isinstance(event, IRISDataSynchronized):
            recalc_types.extend(["data_quality", "sync_performance"])
        
        return recalc_types
    
    async def _process_pending_recalculations(self):
        """Process pending recalculations in batches."""
        await asyncio.sleep(self._batch_delay_seconds)
        
        if not self._pending_recalculations:
            return
        
        recalc_batch = list(self._pending_recalculations)
        self._pending_recalculations.clear()
        
        self.logger.info("Processing analytics recalculation batch",
                        recalc_types=recalc_batch)
        
        for recalc_type in recalc_batch:
            try:
                await self._execute_recalculation(recalc_type)
                self.logger.info("Analytics recalculation completed",
                               recalc_type=recalc_type)
            except Exception as e:
                self.logger.error("Analytics recalculation failed",
                                recalc_type=recalc_type,
                                error=str(e))
    
    async def _execute_recalculation(self, recalc_type: str):
        """Execute specific analytics recalculation."""
        # This would integrate with your analytics service
        # For now, we'll simulate the recalculation
        await asyncio.sleep(0.1)  # Simulate calculation time
        
        # You would call your analytics service here, e.g.:
        # from app.modules.analytics.service import analytics_service
        # await analytics_service.recalculate(recalc_type)


# ============================================
# DASHBOARD REFRESH HANDLER
# ============================================

class DashboardRefreshHandler(TypedEventHandler):
    """Handler for triggering dashboard data refresh."""
    
    def __init__(self):
        # Subscribe to events that affect dashboard displays
        event_types = [
            PatientCreated, PatientUpdated,
            ImmunizationRecorded,
            WorkflowStepCompleted, WorkflowInstanceCompleted,
            SecurityViolationDetected,
            IRISDataSynchronized,
            AnalyticsCalculationCompleted
        ]
        super().__init__("dashboard_refresher", event_types)
        self.logger = logger.bind(handler="dashboard_refresher")
    
    async def handle(self, event: BaseEvent) -> bool:
        """Handle events that require dashboard refresh."""
        try:
            dashboard_sections = self._determine_dashboard_sections(event)
            
            for section in dashboard_sections:
                await self._refresh_dashboard_section(section, event)
                self.logger.debug("Dashboard section refreshed",
                                section=section,
                                trigger_event=event.event_type)
            
            return True
            
        except Exception as e:
            self.logger.error("Dashboard refresh handler error",
                            event_type=event.event_type,
                            error=str(e))
            return False
    
    def _determine_dashboard_sections(self, event: BaseEvent) -> List[str]:
        """Determine which dashboard sections need refresh."""
        sections = []
        
        if isinstance(event, (PatientCreated, PatientUpdated)):
            sections.extend(["patient_summary", "recent_activity"])
            
        if isinstance(event, ImmunizationRecorded):
            sections.extend(["immunization_summary", "recent_activity"])
            
        if isinstance(event, (WorkflowStepCompleted, WorkflowInstanceCompleted)):
            sections.extend(["workflow_status", "recent_activity"])
            
        if isinstance(event, SecurityViolationDetected):
            sections.extend(["security_alerts", "incident_summary"])
            
        if isinstance(event, IRISDataSynchronized):
            sections.append("integration_status")
            
        if isinstance(event, AnalyticsCalculationCompleted):
            sections.extend(["analytics_summary", "reports"])
        
        return sections
    
    async def _refresh_dashboard_section(self, section: str, event: BaseEvent):
        """Refresh specific dashboard section."""
        # This would integrate with your dashboard service
        # You might use WebSocket connections to push updates to connected clients
        
        refresh_data = {
            "section": section,
            "timestamp": datetime.utcnow(),
            "trigger_event": event.event_type,
            "trigger_id": event.event_id
        }
        
        # Simulate dashboard refresh
        self.logger.debug("Dashboard refresh executed", **refresh_data)


# ============================================
# COMPLIANCE MONITORING HANDLER
# ============================================

class ComplianceMonitoringHandler(TypedEventHandler):
    """Handler for monitoring compliance violations and triggering alerts."""
    
    def __init__(self):
        # Subscribe to events that may indicate compliance issues
        event_types = [
            SecurityViolationDetected,
            UnauthorizedAccessAttempt,
            PHIAccessLogged,
            ConsentRevoked,
            PatientDeactivated,
            DocumentUploaded,
            IRISAPIError
        ]
        super().__init__("compliance_monitor", event_types)
        self.logger = logger.bind(handler="compliance_monitor")
        self._violation_thresholds = {
            "unauthorized_access": 5,  # per hour
            "phi_access_without_consent": 1,  # immediate alert
            "data_breach_indicators": 1  # immediate alert
        }
    
    async def handle(self, event: BaseEvent) -> bool:
        """Monitor events for compliance violations."""
        try:
            compliance_checks = await self._perform_compliance_checks(event)
            
            for check_result in compliance_checks:
                if check_result["violation_detected"]:
                    await self._handle_compliance_violation(check_result, event)
                
            return True
            
        except Exception as e:
            self.logger.error("Compliance monitoring error",
                            event_type=event.event_type,
                            error=str(e))
            return False
    
    async def _perform_compliance_checks(self, event: BaseEvent) -> List[Dict[str, Any]]:
        """Perform compliance checks based on event type."""
        checks = []
        
        if isinstance(event, UnauthorizedAccessAttempt):
            checks.append(await self._check_unauthorized_access_threshold(event))
            
        if isinstance(event, PHIAccessLogged):
            checks.append(await self._check_phi_access_compliance(event))
            
        if isinstance(event, ConsentRevoked):
            checks.append(await self._check_consent_revocation_compliance(event))
            
        if isinstance(event, SecurityViolationDetected):
            checks.append(await self._check_security_violation_severity(event))
        
        return checks
    
    async def _check_unauthorized_access_threshold(self, event: UnauthorizedAccessAttempt) -> Dict[str, Any]:
        """Check if unauthorized access attempts exceed threshold."""
        # This would query your audit logs to count recent attempts
        recent_attempts = 3  # Simulate counting recent attempts
        threshold = self._violation_thresholds["unauthorized_access"]
        
        return {
            "check_type": "unauthorized_access_threshold",
            "violation_detected": recent_attempts >= threshold,
            "severity": "high" if recent_attempts >= threshold else "low",
            "details": f"Recent attempts: {recent_attempts}, threshold: {threshold}"
        }
    
    async def _check_phi_access_compliance(self, event: PHIAccessLogged) -> Dict[str, Any]:
        """Check PHI access compliance."""
        violation_detected = not event.consent_verified or not event.legal_basis
        
        return {
            "check_type": "phi_access_compliance",
            "violation_detected": violation_detected,
            "severity": "critical" if violation_detected else "low",
            "details": f"Consent: {event.consent_verified}, Legal basis: {event.legal_basis}"
        }
    
    async def _check_consent_revocation_compliance(self, event: ConsentRevoked) -> Dict[str, Any]:
        """Check consent revocation compliance."""
        # Check if data processing should be halted
        violation_detected = (
            event.data_processing_halt_required and 
            not event.effective_immediately
        )
        
        return {
            "check_type": "consent_revocation_compliance",
            "violation_detected": violation_detected,
            "severity": "high" if violation_detected else "low",
            "details": f"Halt required: {event.data_processing_halt_required}"
        }
    
    async def _check_security_violation_severity(self, event: SecurityViolationDetected) -> Dict[str, Any]:
        """Check security violation severity."""
        critical_violations = ["data_breach", "unauthorized_system_access", "malware_detected"]
        violation_detected = event.severity == "critical" or event.violation_type in critical_violations
        
        return {
            "check_type": "security_violation_severity",
            "violation_detected": violation_detected,
            "severity": event.severity,
            "details": f"Violation type: {event.violation_type}"
        }
    
    async def _handle_compliance_violation(self, check_result: Dict[str, Any], event: BaseEvent):
        """Handle detected compliance violation."""
        self.logger.critical("Compliance violation detected",
                           check_type=check_result["check_type"],
                           severity=check_result["severity"],
                           trigger_event=event.event_type,
                           details=check_result["details"])
        
        # This would trigger compliance violation event
        # await event_bus.publish_compliance_violation(...)


# ============================================
# IRIS INTEGRATION MONITORING HANDLER
# ============================================

class IRISIntegrationMonitorHandler(TypedEventHandler):
    """Handler for monitoring IRIS API integration health."""
    
    def __init__(self):
        event_types = [
            IRISConnectionEstablished,
            IRISDataSynchronized,
            IRISAPIError
        ]
        super().__init__("iris_integration_monitor", event_types)
        self.logger = logger.bind(handler="iris_integration_monitor")
    
    async def handle(self, event: BaseEvent) -> bool:
        """Monitor IRIS integration events."""
        try:
            if isinstance(event, IRISConnectionEstablished):
                await self._handle_connection_established(event)
            elif isinstance(event, IRISDataSynchronized):
                await self._handle_data_synchronized(event)
            elif isinstance(event, IRISAPIError):
                await self._handle_api_error(event)
            
            return True
            
        except Exception as e:
            self.logger.error("IRIS monitoring error",
                            event_type=event.event_type,
                            error=str(e))
            return False
    
    async def _handle_connection_established(self, event: IRISConnectionEstablished):
        """Handle successful IRIS connection."""
        self.logger.info("IRIS connection established",
                        endpoint_id=event.endpoint_id,
                        latency_ms=event.connection_latency_ms)
    
    async def _handle_data_synchronized(self, event: IRISDataSynchronized):
        """Handle IRIS data synchronization."""
        success_rate = event.records_successful / event.records_processed if event.records_processed > 0 else 0
        
        if success_rate < 0.95:  # Less than 95% success rate
            self.logger.warning("IRIS sync low success rate",
                              sync_id=event.sync_id,
                              success_rate=success_rate,
                              failed_records=event.records_failed)
        else:
            self.logger.info("IRIS sync completed successfully",
                           sync_id=event.sync_id,
                           success_rate=success_rate)
    
    async def _handle_api_error(self, event: IRISAPIError):
        """Handle IRIS API errors."""
        self.logger.error("IRIS API error detected",
                         endpoint_id=event.endpoint_id,
                         error_code=event.error_code,
                         error_message=event.error_message,
                         retry_count=event.retry_count)
        
        # Check if circuit breaker should be triggered
        if event.circuit_breaker_triggered:
            self.logger.critical("IRIS circuit breaker triggered",
                               endpoint_id=event.endpoint_id)


# ============================================
# SECURITY INCIDENT RESPONSE HANDLER
# ============================================

class SecurityIncidentResponseHandler(TypedEventHandler):
    """Handler for automated security incident response."""
    
    def __init__(self):
        event_types = [
            SecurityViolationDetected,
            UnauthorizedAccessAttempt
        ]
        super().__init__("security_incident_response", event_types)
        self.logger = logger.bind(handler="security_incident_response")
    
    async def handle(self, event: BaseEvent) -> bool:
        """Handle security incidents with automated response."""
        try:
            if isinstance(event, SecurityViolationDetected):
                await self._handle_security_violation(event)
            elif isinstance(event, UnauthorizedAccessAttempt):
                await self._handle_unauthorized_access(event)
            
            return True
            
        except Exception as e:
            self.logger.error("Security incident response error",
                            event_type=event.event_type,
                            error=str(e))
            return False
    
    async def _handle_security_violation(self, event: SecurityViolationDetected):
        """Handle security violations with appropriate response."""
        if event.severity == "critical":
            await self._trigger_critical_incident_response(event)
        elif event.severity == "high":
            await self._trigger_high_severity_response(event)
        else:
            await self._log_security_incident(event)
    
    async def _handle_unauthorized_access(self, event: UnauthorizedAccessAttempt):
        """Handle unauthorized access attempts."""
        # Rate limiting and user blocking logic would go here
        self.logger.warning("Unauthorized access attempt detected",
                          user_id=event.user_id,
                          resource_type=event.resource_type,
                          source_ip=event.source_ip)
    
    async def _trigger_critical_incident_response(self, event: SecurityViolationDetected):
        """Trigger critical incident response procedures."""
        self.logger.critical("Critical security incident - triggering response",
                           violation_id=event.violation_id,
                           violation_type=event.violation_type)
        
        # This would trigger:
        # - Immediate notification to security team
        # - Automated containment measures
        # - Incident tracking system creation
    
    async def _trigger_high_severity_response(self, event: SecurityViolationDetected):
        """Trigger high severity incident response."""
        self.logger.error("High severity security incident",
                         violation_id=event.violation_id,
                         violation_type=event.violation_type)
    
    async def _log_security_incident(self, event: SecurityViolationDetected):
        """Log security incident for review."""
        self.logger.warning("Security incident logged for review",
                          violation_id=event.violation_id,
                          violation_type=event.violation_type)


# ============================================
# HANDLER REGISTRY
# ============================================

def get_default_handlers() -> List[EventHandler]:
    """Get the default set of event handlers."""
    return [
        AuditLoggingHandler(),
        AnalyticsRecalculationHandler(),
        DashboardRefreshHandler(),
        ComplianceMonitoringHandler(),
        IRISIntegrationMonitorHandler(),
        SecurityIncidentResponseHandler()
    ]


def register_handlers(event_bus) -> None:
    """Register all default handlers with the event bus."""
    handlers = get_default_handlers()
    
    for handler in handlers:
        event_bus.hybrid_bus.subscribe(handler)
        logger.info("Event handler registered", handler=handler.handler_name)
    
    logger.info("All default event handlers registered", count=len(handlers))


# ============================================
# UTILITY CLASSES
# ============================================

class ConditionalHandler(EventHandler):
    """Base class for handlers with conditional processing."""
    
    def __init__(self, handler_name: str, condition_func: callable):
        super().__init__(handler_name)
        self.condition_func = condition_func
    
    async def can_handle(self, event: BaseEvent) -> bool:
        """Check if event meets condition for processing."""
        try:
            return await self.condition_func(event)
        except Exception as e:
            logger.error("Condition check failed",
                        handler=self.handler_name,
                        error=str(e))
            return False


class BatchingHandler(EventHandler):
    """Base class for handlers that batch process events."""
    
    def __init__(self, handler_name: str, batch_size: int = 10, batch_timeout: int = 60):
        super().__init__(handler_name)
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.event_batch: List[BaseEvent] = []
        self.last_batch_time = datetime.utcnow()
    
    async def handle(self, event: BaseEvent) -> bool:
        """Add event to batch and process if batch is full or timeout reached."""
        self.event_batch.append(event)
        
        should_process = (
            len(self.event_batch) >= self.batch_size or
            (datetime.utcnow() - self.last_batch_time).seconds >= self.batch_timeout
        )
        
        if should_process:
            return await self.process_batch()
        
        return True
    
    async def process_batch(self) -> bool:
        """Process the current batch of events."""
        if not self.event_batch:
            return True
        
        try:
            await self.handle_batch(self.event_batch)
            self.event_batch.clear()
            self.last_batch_time = datetime.utcnow()
            return True
        except Exception as e:
            logger.error("Batch processing failed",
                        handler=self.handler_name,
                        batch_size=len(self.event_batch),
                        error=str(e))
            return False
    
    async def handle_batch(self, events: List[BaseEvent]) -> None:
        """Override this method to implement batch processing logic."""
        raise NotImplementedError