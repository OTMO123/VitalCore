"""
SOC2 Type II Compliance Event Handlers

Enterprise event handlers for SOC2 Type II, HIPAA, and GDPR compliance.
Processes authentication, authorization, and data access events for immutable audit trails.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import structlog

from app.core.event_bus import Event, EventType, EventHandler as SimpleEventHandler
from app.core.event_bus_advanced import BaseEvent, HybridEventBus, EventHandler
from app.modules.audit_logger.service import get_audit_service
from app.core.audit_logger import AuditEventType, AuditSeverity

logger = structlog.get_logger(__name__)


class SimpleEventBridgeHandler(SimpleEventHandler):
    """Bridge handler for simple event bus events to SOC2 compliance handlers."""
    
    def __init__(self):
        self.audit_service = None
        self.handler_name = "simple_event_bridge"
    
    async def __call__(self, event: Event):
        """Handle simple event bus events."""
        try:
            # Initialize audit service if needed
            if self.audit_service is None:
                try:
                    self.audit_service = get_audit_service()
                except RuntimeError:
                    logger.warning("Audit service not available for simple event bridge")
                    return await self._log_to_structured_only(event)
            
            # Map simple event types to audit processing
            await self._process_simple_event(event)
            
        except Exception as e:
            logger.error(
                "Simple event bridge processing error",
                event_type=event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type),
                error=str(e)
            )
    
    async def _process_simple_event(self, event: Event):
        """Process simple event for SOC2 compliance."""
        event_type_str = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
        
        # Map event types to audit event types
        event_type_mapping = {
            "user.login.success": AuditEventType.USER_LOGIN,
            "user.login.failure": AuditEventType.USER_LOGIN,
            "user.logout": AuditEventType.USER_LOGOUT,
            "token.created": AuditEventType.TOKEN_ISSUED,
            "token.expired": AuditEventType.TOKEN_EXPIRED,
            "access.granted": AuditEventType.AUTHORIZATION_SUCCESS,
            "access.denied": AuditEventType.AUTHORIZATION_FAILURE,
            "security.violation": AuditEventType.SECURITY_VIOLATION,
            "error.occurred": AuditEventType.SYSTEM_ERROR
        }
        
        audit_event_type = event_type_mapping.get(event_type_str)
        if not audit_event_type:
            logger.debug("No audit mapping for simple event type", event_type=event_type_str)
            return
        
        # Determine severity based on outcome
        outcome = getattr(event, 'outcome', 'success')
        if event_type_str.endswith('.failure') or event_type_str.endswith('.denied') or event_type_str.endswith('.violation'):
            severity = AuditSeverity.HIGH
        elif event_type_str.endswith('.error'):
            severity = AuditSeverity.CRITICAL
        else:
            severity = AuditSeverity.LOW
        
        # Extract event data
        event_data = {}
        if hasattr(event, 'data') and event.data:
            event_data.update(event.data)
        if hasattr(event, 'metadata') and event.metadata:
            event_data.update(event.metadata)
        
        # Create audit log entry
        await self.audit_service.log_event(
            event_type=audit_event_type,
            user_id=event.user_id,
            resource_type="authentication" if "login" in event_type_str or "token" in event_type_str else "system",
            resource_id=event.event_id,
            action=event_type_str,
            outcome=outcome,
            severity=severity,
            details=event_data,
            ip_address=event.ip_address,
            user_agent=event.user_agent
        )
        
        logger.info(
            "SOC2 simple event processed",
            event_type=event_type_str,
            event_id=event.event_id,
            user_id=event.user_id,
            outcome=outcome,
            compliance="SOC2_TYPE_II"
        )
    
    async def _log_to_structured_only(self, event: Event):
        """Fallback to structured logging when audit service unavailable."""
        try:
            event_type_str = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
            logger.info(
                "SOC2 simple event (structured log fallback)",
                event_type=event_type_str,
                event_id=event.event_id,
                user_id=event.user_id,
                outcome=getattr(event, 'outcome', 'success'),
                timestamp=event.timestamp.isoformat() if hasattr(event, 'timestamp') else datetime.now(timezone.utc).isoformat(),
                compliance="SOC2_TYPE_II_FALLBACK",
                data=getattr(event, 'data', {})
            )
        except Exception as e:
            logger.error("Failed to log simple event to structured log", error=str(e))


class SOC2AuthenticationHandler(EventHandler):
    """SOC2 Type II compliant authentication event handler."""
    
    def __init__(self):
        super().__init__("soc2_authentication_handler")
        self.audit_service = None
    
    def get_subscription_patterns(self) -> list[str]:
        """Subscribe to authentication-related events."""
        return [
            "user.login.success",
            "user.login.failure", 
            "user.logout",
            "token.created",
            "token.expired"
        ]
    
    async def can_handle(self, event: BaseEvent) -> bool:
        """Check if this handler can process the event."""
        return event.event_type in self.get_subscription_patterns()
    
    async def handle(self, event: BaseEvent) -> bool:
        """Handle authentication events for SOC2 compliance."""
        try:
            # Initialize audit service if needed
            if self.audit_service is None:
                try:
                    self.audit_service = get_audit_service()
                except RuntimeError:
                    logger.warning("Audit service not available, logging to structured log only")
                    return await self._log_to_structured_only(event)
            
            # Map event types to audit event types
            event_type_mapping = {
                "user.login.success": AuditEventType.USER_LOGIN,
                "user.login.failure": AuditEventType.USER_LOGIN,
                "user.logout": AuditEventType.USER_LOGOUT,
                "token.created": AuditEventType.TOKEN_ISSUED,
                "token.expired": AuditEventType.TOKEN_EXPIRED
            }
            
            audit_event_type = event_type_mapping.get(event.event_type)
            if not audit_event_type:
                logger.warning("Unknown event type for audit", event_type=event.event_type)
                return False
            
            # Determine severity based on outcome
            outcome = getattr(event, 'outcome', 'success')
            severity = AuditSeverity.LOW if outcome == 'success' else AuditSeverity.HIGH
            
            # Extract user information
            user_id = getattr(event, 'user_id', None)
            if hasattr(event, 'headers'):
                user_id = event.headers.get('user_id', user_id)
            
            # Extract event data
            event_data = {}
            if hasattr(event, 'headers'):
                event_data.update(event.headers)
            if hasattr(event, 'data'):
                event_data.update(getattr(event, 'data', {}))
            
            # Create audit log entry
            await self.audit_service.log_event(
                event_type=audit_event_type,
                user_id=user_id,
                resource_type="authentication",
                resource_id=getattr(event, 'event_id', None),
                action=event.event_type,
                outcome=outcome,
                severity=severity,
                details=event_data,
                ip_address=getattr(event, 'ip_address', None),
                user_agent=getattr(event, 'user_agent', None)
            )
            
            logger.info(
                "SOC2 authentication event processed",
                event_type=event.event_type,
                event_id=getattr(event, 'event_id', None),
                user_id=user_id,
                outcome=outcome,
                compliance="SOC2_TYPE_II"
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to process authentication event",
                event_type=event.event_type,
                event_id=getattr(event, 'event_id', None),
                error=str(e),
                handler=self.handler_name
            )
            return False
    
    async def _log_to_structured_only(self, event: BaseEvent) -> bool:
        """Fallback to structured logging when audit service unavailable."""
        try:
            logger.info(
                "SOC2 authentication event (structured log fallback)",
                event_type=event.event_type,
                event_id=getattr(event, 'event_id', None),
                user_id=getattr(event, 'user_id', None),
                outcome=getattr(event, 'outcome', 'success'),
                timestamp=getattr(event, 'timestamp', datetime.now(timezone.utc)).isoformat(),
                compliance="SOC2_TYPE_II_FALLBACK",
                data=getattr(event, 'headers', {})
            )
            return True
        except Exception as e:
            logger.error("Failed to log authentication event to structured log", error=str(e))
            return False


class SOC2PHIAccessHandler(EventHandler):
    """SOC2 Type II and HIPAA compliant PHI access event handler."""
    
    def __init__(self):
        super().__init__("soc2_phi_access_handler")
        self.audit_service = None
    
    def get_subscription_patterns(self) -> list[str]:
        """Subscribe to PHI access events."""
        return [
            "phi.accessed",
            "patient.created",
            "patient.updated",
            "patient.deleted",
            "data.accessed",
            "data.created",
            "data.updated",
            "data.deleted"
        ]
    
    async def can_handle(self, event: BaseEvent) -> bool:
        """Check if this handler can process PHI-related events."""
        return event.event_type in self.get_subscription_patterns()
    
    async def handle(self, event: BaseEvent) -> bool:
        """Handle PHI access events for HIPAA compliance."""
        try:
            # Initialize audit service if needed
            if self.audit_service is None:
                try:
                    self.audit_service = get_audit_service()
                except RuntimeError:
                    logger.warning("Audit service not available, logging to structured log only")
                    return await self._log_phi_to_structured_only(event)
            
            # All PHI access is high severity for HIPAA compliance
            severity = AuditSeverity.HIGH
            
            # Extract PHI information
            user_id = getattr(event, 'user_id', None)
            if hasattr(event, 'headers'):
                user_id = event.headers.get('user_id', user_id)
            
            resource_type = getattr(event, 'aggregate_type', 'unknown')
            resource_id = getattr(event, 'aggregate_id', None)
            
            # Extract event data
            event_data = {
                "phi_access": True,
                "compliance_flags": ["HIPAA", "SOC2_TYPE_II"]
            }
            if hasattr(event, 'headers'):
                event_data.update(event.headers)
            if hasattr(event, 'data'):
                event_data.update(getattr(event, 'data', {}))
            
            # Create audit log entry
            await self.audit_service.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=event.event_type,
                outcome=getattr(event, 'outcome', 'success'),
                severity=severity,
                details=event_data,
                ip_address=getattr(event, 'ip_address', None),
                user_agent=getattr(event, 'user_agent', None)
            )
            
            logger.info(
                "SOC2 PHI access event processed",
                event_type=event.event_type,
                event_id=getattr(event, 'event_id', None),
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                compliance="HIPAA_SOC2_TYPE_II"
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to process PHI access event",
                event_type=event.event_type,
                event_id=getattr(event, 'event_id', None),
                error=str(e),
                handler=self.handler_name
            )
            return False
    
    async def _log_phi_to_structured_only(self, event: BaseEvent) -> bool:
        """Fallback to structured logging for PHI access when audit service unavailable."""
        try:
            logger.info(
                "SOC2 PHI access event (structured log fallback)",
                event_type=event.event_type,
                event_id=getattr(event, 'event_id', None),
                user_id=getattr(event, 'user_id', None),
                resource_type=getattr(event, 'aggregate_type', 'unknown'),
                resource_id=getattr(event, 'aggregate_id', None),
                timestamp=getattr(event, 'timestamp', datetime.now(timezone.utc)).isoformat(),
                compliance="HIPAA_SOC2_TYPE_II_FALLBACK",
                phi_access=True,
                data=getattr(event, 'headers', {})
            )
            return True
        except Exception as e:
            logger.error("Failed to log PHI access event to structured log", error=str(e))
            return False


class SOC2SystemSecurityHandler(EventHandler):
    """SOC2 Type II compliant system security event handler."""
    
    def __init__(self):
        super().__init__("soc2_system_security_handler")
        self.audit_service = None
    
    def get_subscription_patterns(self) -> list[str]:
        """Subscribe to system security events."""
        return [
            "access.granted",
            "access.denied",
            "permission.check",
            "security.violation",
            "error.occurred",
            "system.startup",
            "system.shutdown"
        ]
    
    async def can_handle(self, event: BaseEvent) -> bool:
        """Check if this handler can process security events."""
        return event.event_type in self.get_subscription_patterns()
    
    async def handle(self, event: BaseEvent) -> bool:
        """Handle system security events for SOC2 compliance."""
        try:
            # Initialize audit service if needed
            if self.audit_service is None:
                try:
                    self.audit_service = get_audit_service()
                except RuntimeError:
                    logger.warning("Audit service not available, logging to structured log only")
                    return await self._log_security_to_structured_only(event)
            
            # Map event types to audit event types
            event_type_mapping = {
                "access.granted": AuditEventType.AUTHORIZATION_SUCCESS,
                "access.denied": AuditEventType.AUTHORIZATION_FAILURE,
                "permission.check": AuditEventType.PERMISSION_CHECK,
                "security.violation": AuditEventType.SECURITY_VIOLATION,
                "error.occurred": AuditEventType.SYSTEM_ERROR,
                "system.startup": AuditEventType.SYSTEM_STARTUP,
                "system.shutdown": AuditEventType.SYSTEM_SHUTDOWN
            }
            
            audit_event_type = event_type_mapping.get(event.event_type, AuditEventType.SYSTEM_ERROR)
            
            # Determine severity
            outcome = getattr(event, 'outcome', 'success')
            if event.event_type in ["security.violation", "access.denied"]:
                severity = AuditSeverity.CRITICAL
            elif outcome == 'error':
                severity = AuditSeverity.HIGH
            else:
                severity = AuditSeverity.MEDIUM
            
            # Extract event information
            user_id = getattr(event, 'user_id', None)
            if hasattr(event, 'headers'):
                user_id = event.headers.get('user_id', user_id)
            
            resource_type = getattr(event, 'aggregate_type', 'system')
            resource_id = getattr(event, 'aggregate_id', None)
            
            # Extract event data
            event_data = {}
            if hasattr(event, 'headers'):
                event_data.update(event.headers)
            if hasattr(event, 'data'):
                event_data.update(getattr(event, 'data', {}))
            
            # Create audit log entry
            await self.audit_service.log_event(
                event_type=audit_event_type,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=event.event_type,
                outcome=outcome,
                severity=severity,
                details=event_data,
                ip_address=getattr(event, 'ip_address', None),
                user_agent=getattr(event, 'user_agent', None)
            )
            
            logger.info(
                "SOC2 system security event processed",
                event_type=event.event_type,
                event_id=getattr(event, 'event_id', None),
                user_id=user_id,
                outcome=outcome,
                severity=severity.value,
                compliance="SOC2_TYPE_II"
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to process system security event",
                event_type=event.event_type,
                event_id=getattr(event, 'event_id', None),
                error=str(e),
                handler=self.handler_name
            )
            return False
    
    async def _log_security_to_structured_only(self, event: BaseEvent) -> bool:
        """Fallback to structured logging for security events when audit service unavailable."""
        try:
            logger.info(
                "SOC2 system security event (structured log fallback)",
                event_type=event.event_type,
                event_id=getattr(event, 'event_id', None),
                user_id=getattr(event, 'user_id', None),
                outcome=getattr(event, 'outcome', 'success'),
                timestamp=getattr(event, 'timestamp', datetime.now(timezone.utc)).isoformat(),
                compliance="SOC2_TYPE_II_FALLBACK",
                data=getattr(event, 'headers', {})
            )
            return True
        except Exception as e:
            logger.error("Failed to log security event to structured log", error=str(e))
            return False


# Global handler instances
_authentication_handler: Optional[SOC2AuthenticationHandler] = None
_phi_access_handler: Optional[SOC2PHIAccessHandler] = None
_system_security_handler: Optional[SOC2SystemSecurityHandler] = None


def get_soc2_authentication_handler() -> SOC2AuthenticationHandler:
    """Get singleton SOC2 authentication handler."""
    global _authentication_handler
    if _authentication_handler is None:
        _authentication_handler = SOC2AuthenticationHandler()
    return _authentication_handler


def get_soc2_phi_access_handler() -> SOC2PHIAccessHandler:
    """Get singleton SOC2 PHI access handler."""
    global _phi_access_handler
    if _phi_access_handler is None:
        _phi_access_handler = SOC2PHIAccessHandler()
    return _phi_access_handler


def get_soc2_system_security_handler() -> SOC2SystemSecurityHandler:
    """Get singleton SOC2 system security handler."""
    global _system_security_handler
    if _system_security_handler is None:
        _system_security_handler = SOC2SystemSecurityHandler()
    return _system_security_handler


async def register_soc2_event_handlers(event_bus) -> None:
    """Register all SOC2 compliance event handlers with the event bus."""
    try:
        # Register authentication handler
        auth_handler = get_soc2_authentication_handler()
        event_bus.subscribe(auth_handler)
        
        # Register PHI access handler
        phi_handler = get_soc2_phi_access_handler()
        event_bus.subscribe(phi_handler)
        
        # Register system security handler
        security_handler = get_soc2_system_security_handler()
        event_bus.subscribe(security_handler)
        
        logger.info(
            "SOC2 compliance event handlers registered",
            handlers=[
                auth_handler.handler_name,
                phi_handler.handler_name, 
                security_handler.handler_name
            ],
            compliance="SOC2_TYPE_II_HIPAA_GDPR"
        )
        
    except Exception as e:
        logger.error("Failed to register SOC2 event handlers", error=str(e))
        raise


async def register_simple_event_bridge() -> None:
    """Register bridge handler for simple event bus events."""
    try:
        from app.core.event_bus import event_bus, EventType
        
        # Create bridge handler
        bridge_handler = SimpleEventBridgeHandler()
        
        # Subscribe to authentication and security events
        event_bus.subscribe(EventType.USER_LOGIN_SUCCESS, bridge_handler)
        event_bus.subscribe(EventType.USER_LOGIN_FAILURE, bridge_handler)
        event_bus.subscribe(EventType.USER_LOGOUT, bridge_handler)
        event_bus.subscribe(EventType.TOKEN_CREATED, bridge_handler)
        event_bus.subscribe(EventType.TOKEN_EXPIRED, bridge_handler)
        event_bus.subscribe(EventType.ACCESS_GRANTED, bridge_handler)
        event_bus.subscribe(EventType.ACCESS_DENIED, bridge_handler)
        event_bus.subscribe(EventType.SECURITY_VIOLATION, bridge_handler)
        event_bus.subscribe(EventType.ERROR_OCCURRED, bridge_handler)
        
        logger.info(
            "Simple event bridge handler registered",
            handler="simple_event_bridge",
            event_types=[
                "user.login.success", "user.login.failure", "user.logout",
                "token.created", "token.expired", "access.granted", 
                "access.denied", "security.violation", "error.occurred"
            ],
            compliance="SOC2_TYPE_II_BRIDGE"
        )
        
    except Exception as e:
        logger.error("Failed to register simple event bridge handler", error=str(e))
        raise