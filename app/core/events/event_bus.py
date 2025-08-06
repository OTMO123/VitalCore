"""
Event Bus Service for Inter-Module Communication

This module provides a simplified, focused event bus service built on top of
the existing HybridEventBus infrastructure. It provides domain-specific
event handling for healthcare operations with:

- Type-safe event publishing and subscription
- Cross-module integration patterns
- Audit-compliant event handling
- Healthcare-specific event routing
- Integration with existing audit logging
- Support for event-driven analytics
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any, Type, Union
from functools import wraps
from contextlib import asynccontextmanager

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_bus_advanced import (
    HybridEventBus, 
    BaseEvent, 
    EventHandler, 
    TypedEventHandler,
    EventPriority,
    get_event_bus as get_hybrid_event_bus,
    initialize_event_bus as init_hybrid_event_bus
)
from app.core.events.definitions import (
    EVENT_TYPE_REGISTRY,
    EventCategory,
    get_event_class,
    validate_event_type,
    get_events_by_category,
    # Patient events
    PatientCreated, PatientUpdated, PatientDeactivated, PatientMerged,
    # Immunization events  
    ImmunizationRecorded, ImmunizationUpdated, ImmunizationDeleted,
    # Document events
    DocumentUploaded, DocumentClassified, DocumentProcessed, DocumentVersionCreated,
    # Clinical workflow events
    WorkflowInstanceCreated, WorkflowStepCompleted, WorkflowInstanceCompleted,
    # Security events
    SecurityViolationDetected, UnauthorizedAccessAttempt, PHIAccessLogged,
    # Audit events
    AuditLogCreated, ComplianceViolationDetected,
    # IRIS API events
    IRISConnectionEstablished, IRISDataSynchronized, IRISAPIError,
    # Analytics events
    AnalyticsCalculationCompleted, ReportGenerated,
    # Consent events
    ConsentProvided, ConsentRevoked
)
from app.core.database import get_db

logger = structlog.get_logger()


# ============================================
# EVENT BUS WRAPPER SERVICE
# ============================================

class HealthcareEventBus:
    """Healthcare-specific event bus service."""
    
    def __init__(self, hybrid_bus: HybridEventBus):
        self.hybrid_bus = hybrid_bus
        self.logger = logger.bind(component="healthcare_event_bus")
        self._handlers: Dict[str, List[Callable]] = {}
        self._middleware: List[Callable] = []
        
        # Event routing configuration
        self._routing_rules: Dict[str, List[str]] = {
            # Security events always go to audit
            "security.*": ["audit_logger", "security_monitor"],
            # PHI access events require special handling
            "security.phi_access": ["audit_logger", "compliance_monitor", "analytics"],
            # Patient events trigger analytics recalculation
            "patient.*": ["analytics", "reporting"],
            # Document events trigger classification workflows
            "document.*": ["document_processor", "compliance_monitor"],
            # IRIS events trigger monitoring and alerts
            "iris.*": ["integration_monitor", "alerting"],
            # Workflow events update dashboards
            "workflow.*": ["dashboard", "analytics"],
            # Consent events trigger data processing reviews
            "consent.*": ["compliance_monitor", "data_processor", "audit_logger"]
        }
    
    async def initialize(self):
        """Initialize the healthcare event bus."""
        self.logger.info("Initializing healthcare event bus")
        # The hybrid bus is already initialized, we just configure our layer
        
    async def shutdown(self):
        """Shutdown the healthcare event bus."""
        self.logger.info("Shutting down healthcare event bus")
        # Hybrid bus shutdown is handled at the application level
    
    # ============================================
    # EVENT PUBLISHING
    # ============================================
    
    async def publish_patient_created(
        self,
        patient_id: str,
        created_by_user_id: str,
        mrn: Optional[str] = None,
        fhir_id: Optional[str] = None,
        gender: Optional[str] = None,
        birth_year: Optional[int] = None,
        consent_obtained: bool = False,
        **kwargs
    ) -> bool:
        """Publish patient created event."""
        event = PatientCreated(
            aggregate_id=patient_id,
            publisher="healthcare_records",
            patient_id=patient_id,
            mrn=mrn,
            fhir_id=fhir_id,
            gender=gender,
            birth_year=birth_year,
            created_by_user_id=created_by_user_id,
            consent_obtained=consent_obtained,
            **kwargs
        )
        return await self._publish_event(event)
    
    async def publish_patient_updated(
        self,
        patient_id: str,
        updated_fields: List[str],
        updated_by_user_id: str,
        update_reason: Optional[str] = None,
        phi_fields_updated: bool = False,
        **kwargs
    ) -> bool:
        """Publish patient updated event."""
        event = PatientUpdated(
            aggregate_id=patient_id,
            publisher="healthcare_records",
            patient_id=patient_id,
            updated_fields=updated_fields,
            updated_by_user_id=updated_by_user_id,
            update_reason=update_reason,
            phi_fields_updated=phi_fields_updated,
            **kwargs
        )
        return await self._publish_event(event)
    
    async def publish_immunization_recorded(
        self,
        immunization_id: str,
        patient_id: str,
        vaccine_code: str,
        vaccine_name: str,
        administration_date: datetime,
        source_system: str = "manual",
        **kwargs
    ) -> bool:
        """Publish immunization recorded event."""
        event = ImmunizationRecorded(
            aggregate_id=immunization_id,
            publisher="healthcare_records",
            immunization_id=immunization_id,
            patient_id=patient_id,
            vaccine_code=vaccine_code,
            vaccine_name=vaccine_name,
            administration_date=administration_date,
            source_system=source_system,
            **kwargs
        )
        return await self._publish_event(event)
    
    async def publish_document_uploaded(
        self,
        document_id: str,
        filename: str,
        file_size: int,
        mime_type: str,
        document_type: str,
        uploaded_by_user_id: str,
        patient_id: Optional[str] = None,
        data_classification: str = "PHI",
        **kwargs
    ) -> bool:
        """Publish document uploaded event."""
        event = DocumentUploaded(
            aggregate_id=document_id,
            publisher="document_management",
            document_id=document_id,
            patient_id=patient_id,
            filename=filename,
            file_size=file_size,
            mime_type=mime_type,
            document_type=document_type,
            uploaded_by_user_id=uploaded_by_user_id,
            data_classification=data_classification,
            **kwargs
        )
        return await self._publish_event(event)
    
    async def publish_workflow_step_completed(
        self,
        workflow_instance_id: str,
        step_id: str,
        step_name: str,
        step_type: str,
        completed_by_user_id: str,
        outcome: str,
        **kwargs
    ) -> bool:
        """Publish workflow step completed event."""
        event = WorkflowStepCompleted(
            aggregate_id=workflow_instance_id,
            publisher="clinical_workflows",
            workflow_instance_id=workflow_instance_id,
            step_id=step_id,
            step_name=step_name,
            step_type=step_type,
            completed_by_user_id=completed_by_user_id,
            outcome=outcome,
            **kwargs
        )
        return await self._publish_event(event)
    
    async def publish_security_violation(
        self,
        violation_type: str,
        severity: str,
        violation_description: str,
        detection_method: str,
        resource_type: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Publish security violation event."""
        event = SecurityViolationDetected(
            aggregate_id=kwargs.get('violation_id', str(uuid.uuid4())),
            publisher="security_monitor",
            violation_type=violation_type,
            severity=severity,
            violation_description=violation_description,
            detection_method=detection_method,
            resource_type=resource_type,
            user_id=user_id,
            resource_id=resource_id,
            **kwargs
        )
        return await self._publish_event(event)
    
    async def publish_phi_access(
        self,
        user_id: str,
        patient_id: str,
        phi_fields_accessed: List[str],
        access_purpose: str,
        legal_basis: str,
        session_id: str,
        consent_verified: bool = True,
        **kwargs
    ) -> bool:
        """Publish PHI access event."""
        event = PHIAccessLogged(
            aggregate_id=f"phi_access_{user_id}_{patient_id}_{datetime.utcnow().timestamp()}",
            publisher="security_monitor",
            user_id=user_id,
            patient_id=patient_id,
            phi_fields_accessed=phi_fields_accessed,
            access_purpose=access_purpose,
            legal_basis=legal_basis,
            session_id=session_id,
            consent_verified=consent_verified,
            **kwargs
        )
        return await self._publish_event(event)
    
    async def publish_iris_data_synchronized(
        self,
        sync_id: str,
        endpoint_id: str,
        sync_type: str,
        records_processed: int,
        records_successful: int,
        sync_duration_ms: int,
        records_failed: int = 0,
        **kwargs
    ) -> bool:
        """Publish IRIS data synchronized event."""
        event = IRISDataSynchronized(
            aggregate_id=sync_id,
            publisher="iris_api",
            sync_id=sync_id,
            endpoint_id=endpoint_id,
            sync_type=sync_type,
            records_processed=records_processed,
            records_successful=records_successful,
            records_failed=records_failed,
            sync_duration_ms=sync_duration_ms,
            throughput_records_per_second=records_processed / (sync_duration_ms / 1000),
            **kwargs
        )
        return await self._publish_event(event)
    
    async def publish_consent_provided(
        self,
        consent_id: str,
        patient_id: str,
        consent_type: str,
        consent_scope: List[str],
        purposes: List[str],
        legal_basis: str,
        obtained_by_user_id: str,
        effective_date: datetime,
        **kwargs
    ) -> bool:
        """Publish consent provided event."""
        event = ConsentProvided(
            aggregate_id=consent_id,
            publisher="healthcare_records",
            consent_id=consent_id,
            patient_id=patient_id,
            consent_type=consent_type,
            consent_scope=consent_scope,
            purposes=purposes,
            legal_basis=legal_basis,
            obtained_by_user_id=obtained_by_user_id,
            effective_date=effective_date,
            **kwargs
        )
        return await self._publish_event(event)
    
    async def publish_consent_revoked(
        self,
        consent_id: str,
        patient_id: str,
        revocation_reason: str,
        revoked_by_user_id: Optional[str] = None,
        partial_revocation: bool = False,
        affected_data_categories: Optional[List[str]] = None,
        **kwargs
    ) -> bool:
        """Publish consent revoked event."""
        event = ConsentRevoked(
            aggregate_id=consent_id,
            publisher="healthcare_records",
            consent_id=consent_id,
            patient_id=patient_id,
            revocation_reason=revocation_reason,
            revoked_by_user_id=revoked_by_user_id,
            partial_revocation=partial_revocation,
            affected_data_categories=affected_data_categories or [],
            **kwargs
        )
        return await self._publish_event(event)
    
    # ============================================
    # GENERIC EVENT PUBLISHING
    # ============================================
    
    async def publish_event(
        self,
        event_type: str,
        aggregate_id: str,
        publisher: str,
        data: Dict[str, Any],
        priority: EventPriority = EventPriority.NORMAL,
        **kwargs
    ) -> bool:
        """Publish a generic event by type."""
        event_class = get_event_class(event_type)
        if not event_class:
            self.logger.error("Unknown event type", event_type=event_type)
            return False
        
        try:
            # Merge data with required fields
            event_data = {
                "aggregate_id": aggregate_id,
                "publisher": publisher,
                "priority": priority,
                **data,
                **kwargs
            }
            
            event = event_class(**event_data)
            return await self._publish_event(event)
            
        except Exception as e:
            self.logger.error("Failed to create event", 
                            event_type=event_type, error=str(e))
            return False
    
    async def _publish_event(self, event: BaseEvent) -> bool:
        """Internal method to publish events through the hybrid bus."""
        try:
            # Apply middleware
            for middleware in self._middleware:
                event = await middleware(event)
                if event is None:
                    self.logger.warning("Event filtered by middleware")
                    return False
            
            # Publish through hybrid bus
            success = await self.hybrid_bus.publish(event)
            
            if success:
                self.logger.info("Event published successfully",
                               event_type=event.event_type,
                               event_id=event.event_id,
                               aggregate_id=event.aggregate_id)
            else:
                self.logger.error("Failed to publish event",
                                event_type=event.event_type,
                                event_id=event.event_id)
            
            return success
            
        except Exception as e:
            self.logger.error("Event publishing error",
                            event_type=event.event_type,
                            error=str(e))
            return False
    
    # ============================================
    # EVENT SUBSCRIPTION
    # ============================================
    
    def subscribe(
        self,
        event_types: Union[str, List[str]],
        handler: Callable[[BaseEvent], bool],
        handler_name: Optional[str] = None
    ):
        """Subscribe to events with a handler function."""
        if isinstance(event_types, str):
            event_types = [event_types]
        
        handler_name = handler_name or f"handler_{uuid.uuid4().hex[:8]}"
        
        # Create wrapper handler
        class FunctionHandler(TypedEventHandler):
            def __init__(self, name: str, types: List[str], func: Callable):
                # Convert type names to classes for TypedEventHandler
                event_classes = [get_event_class(t) for t in types if get_event_class(t)]
                super().__init__(name, event_classes)
                self.func = func
            
            async def handle(self, event: BaseEvent) -> bool:
                try:
                    return await self.func(event)
                except Exception as e:
                    logger.error("Handler error", handler=self.handler_name, error=str(e))
                    return False
        
        wrapper = FunctionHandler(handler_name, event_types, handler)
        self.hybrid_bus.subscribe(wrapper, event_types)
        
        self.logger.info("Handler subscribed",
                        handler=handler_name,
                        event_types=event_types)
        
        return wrapper
    
    def subscribe_to_category(
        self,
        category: EventCategory,
        handler: Callable[[BaseEvent], bool],
        handler_name: Optional[str] = None
    ):
        """Subscribe to all events in a category."""
        event_classes = get_events_by_category(category)
        event_types = [cls.__fields__['event_type'].default for cls in event_classes]
        
        return self.subscribe(event_types, handler, handler_name)
    
    def unsubscribe(self, handler_name: str):
        """Unsubscribe a handler."""
        self.hybrid_bus.unsubscribe(handler_name)
        self.logger.info("Handler unsubscribed", handler=handler_name)
    
    # ============================================
    # MIDDLEWARE
    # ============================================
    
    def add_middleware(self, middleware: Callable[[BaseEvent], BaseEvent]):
        """Add middleware for event processing."""
        self._middleware.append(middleware)
        self.logger.info("Middleware added", middleware=middleware.__name__)
    
    def remove_middleware(self, middleware: Callable):
        """Remove middleware."""
        if middleware in self._middleware:
            self._middleware.remove(middleware)
            self.logger.info("Middleware removed", middleware=middleware.__name__)
    
    # ============================================
    # EVENT DECORATORS
    # ============================================
    
    def publishes(self, event_type: str, **event_kwargs):
        """Decorator to automatically publish events from method calls."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                result = await func(*args, **kwargs)
                
                # Extract aggregate_id and publisher from function context
                aggregate_id = event_kwargs.get('aggregate_id') or str(uuid.uuid4())
                publisher = event_kwargs.get('publisher', 'unknown')
                
                # Merge function result with event data
                event_data = {**event_kwargs}
                if isinstance(result, dict):
                    event_data.update(result)
                
                # Remove decorator-specific keys
                event_data.pop('aggregate_id', None)
                event_data.pop('publisher', None)
                
                await self.publish_event(
                    event_type=event_type,
                    aggregate_id=aggregate_id,
                    publisher=publisher,
                    data=event_data
                )
                
                return result
            return wrapper
        return decorator
    
    # ============================================
    # QUERY AND MONITORING
    # ============================================
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics."""
        return self.hybrid_bus.get_metrics()
    
    def get_subscription_info(self) -> Dict[str, Any]:
        """Get subscription information."""
        return {
            "handlers": list(self.hybrid_bus.handlers.keys()),
            "subscription_patterns": dict(self.hybrid_bus.subscription_patterns),
            "middleware_count": len(self._middleware)
        }
    
    async def replay_events(
        self,
        aggregate_id: str,
        from_version: int = 0,
        to_version: Optional[int] = None
    ) -> int:
        """Replay events for an aggregate."""
        return await self.hybrid_bus.replay_events(aggregate_id, from_version, to_version)

    async def publish(self, event: BaseEvent) -> bool:
        """Publish an event (compatibility method for external callers)."""
        return await self._publish_event(event)


# ============================================
# GLOBAL EVENT BUS INSTANCE
# ============================================

_healthcare_event_bus: Optional[HealthcareEventBus] = None


def get_event_bus() -> HealthcareEventBus:
    """Get the global healthcare event bus instance."""
    global _healthcare_event_bus
    if _healthcare_event_bus is None:
        raise RuntimeError("Healthcare event bus not initialized. Call initialize_event_bus() first.")
    return _healthcare_event_bus


async def initialize_event_bus(db_session_factory) -> HealthcareEventBus:
    """Initialize the global healthcare event bus."""
    global _healthcare_event_bus
    
    # Initialize the hybrid event bus first
    hybrid_bus = await init_hybrid_event_bus(db_session_factory)
    
    # Create healthcare event bus wrapper
    _healthcare_event_bus = HealthcareEventBus(hybrid_bus)
    await _healthcare_event_bus.initialize()
    
    logger.info("Healthcare event bus initialized successfully")
    return _healthcare_event_bus


async def shutdown_event_bus():
    """Shutdown the global healthcare event bus."""
    global _healthcare_event_bus
    if _healthcare_event_bus:
        await _healthcare_event_bus.shutdown()
        _healthcare_event_bus = None
    
    # Shutdown hybrid bus
    from app.core.event_bus_advanced import shutdown_event_bus as shutdown_hybrid
    await shutdown_hybrid()


# ============================================
# UTILITY FUNCTIONS
# ============================================

async def with_event_publishing(
    operation: Callable,
    event_type: str,
    aggregate_id: str,
    publisher: str,
    **event_data
):
    """Execute operation and publish event on success."""
    event_bus = get_event_bus()
    
    try:
        result = await operation()
        
        # Publish success event
        await event_bus.publish_event(
            event_type=event_type,
            aggregate_id=aggregate_id,
            publisher=publisher,
            data=event_data
        )
        
        return result
        
    except Exception as e:
        # Could publish failure event here
        logger.error("Operation failed, event not published",
                    event_type=event_type,
                    aggregate_id=aggregate_id,
                    error=str(e))
        raise


def event_transaction(event_type: str, publisher: str):
    """Decorator for transactional event publishing."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract aggregate_id from function args/kwargs
            aggregate_id = kwargs.get('id') or args[0] if args else str(uuid.uuid4())
            
            return await with_event_publishing(
                operation=lambda: func(*args, **kwargs),
                event_type=event_type,
                aggregate_id=str(aggregate_id),
                publisher=publisher,
                function_args=args,
                function_kwargs=kwargs
            )
        return wrapper
    return decorator


# ============================================
# CONTEXT MANAGERS
# ============================================

@asynccontextmanager
async def event_context(aggregate_id: str, publisher: str):
    """Context manager for event publishing within a transaction."""
    event_bus = get_event_bus()
    events_to_publish = []
    
    class EventCollector:
        def publish(self, event_type: str, **data):
            events_to_publish.append((event_type, data))
    
    collector = EventCollector()
    
    try:
        yield collector
        
        # Publish all collected events
        for event_type, data in events_to_publish:
            await event_bus.publish_event(
                event_type=event_type,
                aggregate_id=aggregate_id,
                publisher=publisher,
                data=data
            )
            
    except Exception as e:
        logger.error("Event context error", 
                    aggregate_id=aggregate_id,
                    events_count=len(events_to_publish),
                    error=str(e))
        raise