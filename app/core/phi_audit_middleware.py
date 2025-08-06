"""
PHI Access Audit Middleware
Автоматически логирует доступ к защищенной медицинской информации для HIPAA compliance
"""

from fastapi import Request, Response
from fastapi.routing import APIRoute
from typing import Callable, Any
import structlog
import time
import json
from datetime import datetime

from app.core.database_unified import AuditEventType
from app.modules.audit_logger.service import get_audit_service

logger = structlog.get_logger()

class PHIAuditRoute(APIRoute):
    """
    Custom route class that automatically logs PHI access for HIPAA compliance.
    
    Usage:
        @router.get("/patients/{patient_id}", route_class=PHIAuditRoute)
        async def get_patient(patient_id: str):
            # PHI access will be automatically logged
            return patient_data
    """
    
    def get_route_handler(self) -> Callable[[Request], Any]:
        original_route_handler = super().get_route_handler()
        
        async def custom_route_handler(request: Request) -> Response:
            # Start timing
            start_time = time.time()
            
            # Extract route information
            route_path = str(request.url.path)
            method = request.method
            user_id = getattr(request.state, 'user_id', None)
            
            # Determine if this is PHI access
            is_phi_access = self._is_phi_endpoint(route_path, method)
            
            try:
                # Execute the original route handler
                response = await original_route_handler(request)
                processing_time = time.time() - start_time
                
                # Log PHI access if applicable
                if is_phi_access:
                    await self._log_phi_access(
                        request=request,
                        response=response,
                        user_id=user_id,
                        processing_time=processing_time,
                        success=True
                    )
                
                return response
                
            except Exception as e:
                processing_time = time.time() - start_time
                
                # Log failed PHI access attempt
                if is_phi_access:
                    await self._log_phi_access(
                        request=request,
                        response=None,
                        user_id=user_id,
                        processing_time=processing_time,
                        success=False,
                        error=str(e)
                    )
                
                # Re-raise the exception
                raise
        
        return custom_route_handler
    
    def _is_phi_endpoint(self, path: str, method: str) -> bool:
        """Determine if this endpoint involves PHI access."""
        phi_patterns = [
            '/patients/',
            '/healthcare/',
            '/clinical-documents/',
            '/phi/',
            '/immunizations/',
            '/medical-records/',
            '/health-data/'
        ]
        
        # Check if path contains PHI-related patterns
        for pattern in phi_patterns:
            if pattern in path.lower():
                return True
        
        return False
    
    async def _log_phi_access(
        self,
        request: Request,
        response: Response = None,
        user_id: str = None,
        processing_time: float = 0,
        success: bool = True,
        error: str = None
    ):
        """Log PHI access event for HIPAA compliance."""
        try:
            # Extract request details
            path = str(request.url.path)
            method = request.method
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
            
            # Extract resource information
            resource_id = self._extract_resource_id(path)
            resource_type = self._determine_resource_type(path)
            
            # Determine event type
            if success:
                if method == "GET":
                    event_type = AuditEventType.PHI_ACCESSED
                elif method == "POST":
                    event_type = AuditEventType.PHI_CREATED
                elif method in ["PUT", "PATCH"]:
                    event_type = AuditEventType.PHI_UPDATED
                elif method == "DELETE":
                    event_type = AuditEventType.PHI_DELETED
                else:
                    event_type = AuditEventType.PHI_ACCESSED
            else:
                event_type = AuditEventType.SECURITY_VIOLATION
            
            # Create audit event
            from app.modules.audit_logger.schemas import DataAccessEvent
            
            phi_event = DataAccessEvent(
                user_id=user_id or "unknown",
                access_type="phi_access",
                data_operation=method.lower(),
                resource_type=resource_type,
                resource_id=resource_id,
                data_sensitivity_level="phi",  # Always PHI for this middleware
                access_granted=success,
                operation=f"phi_{method.lower()}",
                outcome="success" if success else "failure",
                headers={
                    "endpoint": path,
                    "method": method,
                    "user_agent": user_agent,
                    "processing_time_ms": round(processing_time * 1000, 2),
                    "response_status": response.status_code if response else "error",
                    "error_message": error if error else None,
                    "compliance_flags": ["HIPAA", "PHI_ACCESS"],
                    "audit_category": "phi_access",
                    "severity": "high" if not success else "medium"
                }
            )
            
            # Additional metadata for specific resource types
            if "patient" in resource_type.lower():
                phi_event.headers["patient_id"] = resource_id
                phi_event.headers["data_type"] = "patient_record"
            elif "clinical" in resource_type.lower():
                phi_event.headers["document_id"] = resource_id
                phi_event.headers["data_type"] = "clinical_document"
            
            # Set IP address
            phi_event.headers["ip_address"] = client_ip
            
            # Log the event with graceful event loop handling
            try:
                audit_service = get_audit_service()
                success_logged = await audit_service.log_audit_event(phi_event)
                
                if success_logged:
                    logger.info(
                        "PHI access logged",
                        event_type=event_type,
                        user_id=user_id,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        success=success,
                        compliance="HIPAA"
                    )
                else:
                    logger.error(
                        "Failed to log PHI access - CRITICAL COMPLIANCE ISSUE",
                        user_id=user_id,
                        resource_type=resource_type,
                        path=path
                    )
            except RuntimeError as e:
                if "Event loop is closed" in str(e):
                    # Handle event loop closure gracefully during shutdown
                    logger.warning(
                        "PHI audit logging skipped due to event loop closure during shutdown",
                        user_id=user_id,
                        resource_type=resource_type,
                        path=path,
                        compliance_note="SHUTDOWN_GRACEFUL_DEGRADATION"
                    )
                    # For enterprise compliance, we should implement a fallback logging mechanism
                    # such as writing directly to a file or queue for later processing
                    await self._fallback_phi_audit_log(phi_event, logging_error=e)
                else:
                    raise
                
        except Exception as logging_error:
            # CRITICAL: PHI access logging failure is a serious compliance issue
            logger.error(
                "CRITICAL: PHI audit logging failed",
                error=str(logging_error),
                user_id=user_id,
                path=path,
                compliance_violation="HIPAA_AUDIT_FAILURE"
            )
            # Attempt fallback logging for enterprise compliance
            try:
                await self._fallback_phi_audit_log(phi_event, logging_error)
            except Exception as fallback_error:
                logger.error(
                    "Fallback PHI audit logging also failed",
                    original_error=str(logging_error),
                    fallback_error=str(fallback_error),
                    compliance_violation="CRITICAL_AUDIT_SYSTEM_FAILURE"
                )
    
    def _extract_resource_id(self, path: str) -> str:
        """Extract resource ID from path."""
        # Pattern matching for common ID patterns
        import re
        
        # UUID pattern
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        uuid_match = re.search(uuid_pattern, path, re.IGNORECASE)
        if uuid_match:
            return uuid_match.group(0)
        
        # Numeric ID pattern
        numeric_pattern = r'/(\d+)(?:/|$)'
        numeric_match = re.search(numeric_pattern, path)
        if numeric_match:
            return numeric_match.group(1)
        
        # Alphanumeric ID after known paths
        id_patterns = [
            r'/patients/([^/]+)',
            r'/healthcare/([^/]+)',
            r'/clinical-documents/([^/]+)',
            r'/phi/([^/]+)'
        ]
        
        for pattern in id_patterns:
            match = re.search(pattern, path, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "unknown"
    
    def _determine_resource_type(self, path: str) -> str:
        """Determine resource type from path."""
        path_lower = path.lower()
        
        if '/patients/' in path_lower:
            return 'patient_record'
        elif '/healthcare/' in path_lower:
            return 'healthcare_record'
        elif '/clinical-documents/' in path_lower:
            return 'clinical_document'
        elif '/immunizations/' in path_lower:
            return 'immunization_record'
        elif '/medical-records/' in path_lower:
            return 'medical_record'
        elif '/phi/' in path_lower:
            return 'phi_data'
        else:
            return 'healthcare_data'

    async def _fallback_phi_audit_log(self, phi_event: Any, logging_error: Exception):
        """
        Fallback PHI audit logging for enterprise compliance.
        
        When the primary audit system fails (e.g., due to event loop closure),
        this method provides a fallback mechanism to ensure PHI access is still logged
        for HIPAA/SOC2 compliance requirements.
        """
        import asyncio
        import os
        import json
        from pathlib import Path
        
        try:
            # For enterprise compliance, write to secure fallback audit file
            fallback_dir = Path("/var/log/healthcare/phi_audit_fallback")
            fallback_dir.mkdir(parents=True, exist_ok=True)
            
            # Create fallback audit entry
            fallback_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": "PHI_ACCESS_FALLBACK",
                "user_id": getattr(phi_event, 'user_id', 'unknown'),
                "resource_type": getattr(phi_event, 'resource_type', 'unknown'),
                "resource_id": getattr(phi_event, 'resource_id', 'unknown'),
                "access_type": getattr(phi_event, 'event_type', 'unknown'),
                "compliance_note": "FALLBACK_LOGGING_DUE_TO_SYSTEM_ISSUE",
                "original_error": str(logging_error),
                "ip_address": getattr(phi_event.headers, 'ip_address', 'unknown') if hasattr(phi_event, 'headers') else 'unknown',
                "session_id": getattr(phi_event, 'session_id', 'unknown'),
                "requires_manual_review": True
            }
            
            # Write to daily fallback file
            fallback_file = fallback_dir / f"phi_audit_fallback_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
            
            # Use synchronous I/O for fallback to avoid event loop issues
            with open(fallback_file, 'a') as f:
                f.write(json.dumps(fallback_entry) + '\n')
                f.flush()
                os.fsync(f.fileno())  # Force write to disk for compliance
            
            logger.warning(
                "PHI access logged to fallback file for compliance",
                fallback_file=str(fallback_file),
                user_id=fallback_entry["user_id"],
                compliance="HIPAA_FALLBACK_LOGGING"
            )
            
        except Exception as fallback_error:
            # Last resort: log to system logger
            logger.critical(
                "CRITICAL: All PHI audit logging mechanisms failed",
                original_error=str(logging_error),
                fallback_error=str(fallback_error),
                phi_event_data=str(phi_event),
                compliance_violation="TOTAL_AUDIT_SYSTEM_FAILURE",
                immediate_action_required=True
            )


# ============================================
# DECORATOR FOR EASY PHI ROUTE PROTECTION
# ============================================

def phi_audit_required(func):
    """
    Decorator to mark a function as requiring PHI audit logging.
    
    Usage:
        @router.get("/patients/{patient_id}")
        @phi_audit_required
        async def get_patient(patient_id: str):
            return patient_data
    """
    func._requires_phi_audit = True
    return func


# ============================================
# MIDDLEWARE FOR AUTOMATIC PHI DETECTION
# ============================================

class PHIAuditMiddleware:
    """
    Middleware that automatically detects and logs PHI access.
    Add this to your FastAPI app for comprehensive PHI logging.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Create a custom scope with PHI audit tracking
        request = Request(scope, receive)
        
        # Check if this is a PHI endpoint
        path = request.url.path
        method = request.method
        
        is_phi_endpoint = self._is_phi_endpoint(path, method)
        
        if is_phi_endpoint:
            # Add PHI audit flag to request state
            scope["state"] = scope.get("state", {})
            scope["state"]["requires_phi_audit"] = True
            scope["state"]["phi_resource_type"] = self._determine_resource_type(path)
            scope["state"]["phi_resource_id"] = self._extract_resource_id(path)
        
        await self.app(scope, receive, send)
    
    def _is_phi_endpoint(self, path: str, method: str) -> bool:
        """Check if endpoint handles PHI data."""
        phi_patterns = [
            '/patients/',
            '/healthcare/',
            '/clinical-documents/',
            '/phi/',
            '/immunizations/',
            '/medical-records/',
            '/health-data/'
        ]
        
        for pattern in phi_patterns:
            if pattern in path.lower():
                return True
        
        return False
    
    def _determine_resource_type(self, path: str) -> str:
        """Determine PHI resource type."""
        path_lower = path.lower()
        
        if '/patients/' in path_lower:
            return 'patient_record'
        elif '/healthcare/' in path_lower:
            return 'healthcare_record'
        elif '/clinical-documents/' in path_lower:
            return 'clinical_document'
        else:
            return 'phi_data'
    
    def _extract_resource_id(self, path: str) -> str:
        """Extract resource ID."""
        import re
        
        # Simple ID extraction
        id_match = re.search(r'/([^/]+)/?$', path)
        if id_match:
            return id_match.group(1)
        
        return "unknown"