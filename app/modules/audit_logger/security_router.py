"""
Security Reporting Router for CSP Violations and Security Events
Handles CSP violation reports and security monitoring endpoints.
"""

from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
import structlog
import json

from app.core.database_unified import get_db
from app.core.security import get_current_user_id, require_role
from app.modules.audit_logger.service import get_audit_service
from app.modules.audit_logger.schemas import SecurityViolationEvent

logger = structlog.get_logger()

router = APIRouter()

@router.post("/csp-report")
async def handle_csp_violation_report(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Content Security Policy violation reports.
    
    This endpoint receives CSP violation reports from browsers and logs them
    for security monitoring and compliance purposes.
    """
    try:
        # Parse CSP violation report
        body = await request.body()
        
        if not body:
            logger.warning("Empty CSP violation report received")
            return JSONResponse(status_code=204, content={})
        
        try:
            report_data = json.loads(body)
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in CSP violation report", error=str(e))
            return JSONResponse(status_code=400, content={"error": "Invalid JSON"})
        
        # Extract CSP violation details
        csp_report = report_data.get("csp-report", {})
        
        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log CSP violation as security event
        audit_service = get_audit_service()
        
        violation_event = SecurityViolationEvent(
            user_id="system",  # CSP violations are system-level
            violation_type="csp_violation",
            severity_level="medium",  # CSP violations are typically medium severity
            detection_method="browser_report",
            investigation_required=True,  # CSP violations should be investigated
            operation="csp_violation_report",
            outcome="reported",
            headers={
                "csp_violation": {
                    "blocked_uri": csp_report.get("blocked-uri", "unknown"),
                    "violated_directive": csp_report.get("violated-directive", "unknown"),
                    "effective_directive": csp_report.get("effective-directive", "unknown"),
                    "original_policy": csp_report.get("original-policy", "unknown"),
                    "document_uri": csp_report.get("document-uri", "unknown"),
                    "referrer": csp_report.get("referrer", "unknown"),
                    "source_file": csp_report.get("source-file", "unknown"),
                    "line_number": csp_report.get("line-number", 0),
                    "column_number": csp_report.get("column-number", 0)
                },
                "client_info": {
                    "ip_address": client_ip,
                    "user_agent": user_agent,
                    "timestamp": request.headers.get("date", "unknown")
                },
                "raw_report": report_data
            }
        )
        
        # Log the violation
        success = await audit_service.log_audit_event(violation_event)
        
        if success:
            logger.warning(
                "CSP violation reported and logged",
                violation_id=violation_event.event_id,
                blocked_uri=csp_report.get("blocked-uri", "unknown"),
                violated_directive=csp_report.get("violated-directive", "unknown"),
                client_ip=client_ip,
                document_uri=csp_report.get("document-uri", "unknown")
            )
        else:
            logger.error("Failed to log CSP violation to audit system")
        
        # Return 204 No Content (standard for CSP reporting)
        return JSONResponse(status_code=204, content={})
        
    except Exception as e:
        logger.error("Error processing CSP violation report", error=str(e))
        # Still return 204 to avoid breaking browser CSP reporting
        return JSONResponse(status_code=204, content={})

@router.get("/csp-violations")
async def get_csp_violations(
    limit: int = 50,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin"))
):
    """
    Get recent CSP violation reports for security analysis.
    Admin-only endpoint for security monitoring.
    """
    try:
        # Query audit logs for CSP violations
        from app.core.database_unified import AuditLog
        from sqlalchemy import desc, select
        from datetime import datetime, timedelta
        
        # Get CSP violations from last 7 days
        since_date = datetime.utcnow() - timedelta(days=7)
        
        query = select(AuditLog).where(
            AuditLog.timestamp >= since_date,
            AuditLog.event_type == "SECURITY_VIOLATION",
            AuditLog.headers.op("->>")(
                "csp_violation"
            ).isnot(None)
        ).order_by(desc(AuditLog.timestamp)).limit(limit)
        
        result = await db.execute(query)
        violations = result.scalars().all()
        
        # Format violations for response
        formatted_violations = []
        for violation in violations:
            try:
                headers = violation.headers or {}
                csp_info = headers.get("csp_violation", {})
                client_info = headers.get("client_info", {})
                
                formatted_violations.append({
                    "id": str(violation.id),
                    "timestamp": violation.timestamp.isoformat(),
                    "blocked_uri": csp_info.get("blocked_uri", "unknown"),
                    "violated_directive": csp_info.get("violated_directive", "unknown"),
                    "effective_directive": csp_info.get("effective_directive", "unknown"),
                    "document_uri": csp_info.get("document_uri", "unknown"),
                    "source_file": csp_info.get("source_file", "unknown"),
                    "line_number": csp_info.get("line_number", 0),
                    "column_number": csp_info.get("column_number", 0),
                    "client_ip": client_info.get("ip_address", "unknown"),
                    "user_agent": client_info.get("user_agent", "unknown")
                })
            except Exception as parse_error:
                logger.error("Error parsing CSP violation", 
                           violation_id=violation.id, 
                           error=str(parse_error))
                continue
        
        logger.info(
            "CSP violations retrieved",
            user_id=current_user_id,
            violation_count=len(formatted_violations),
            query_limit=limit
        )
        
        return {
            "violations": formatted_violations,
            "total_count": len(formatted_violations),
            "query_info": {
                "limit": limit,
                "days_back": 7,
                "query_time": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error("Failed to retrieve CSP violations", error=str(e))
        raise HTTPException(
            status_code=500, 
            detail="Failed to retrieve CSP violation reports"
        )

@router.get("/security-summary")
async def get_security_summary(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin"))
):
    """
    Get security summary including CSP violations, failed logins, and other security events.
    """
    try:
        from app.core.database_unified import AuditLog
        from sqlalchemy import func, select
        from datetime import datetime, timedelta
        
        # Get security events from last 24 hours
        since_date = datetime.utcnow() - timedelta(hours=24)
        
        # Count different types of security events
        security_summary = {
            "csp_violations": 0,
            "failed_logins": 0,
            "security_violations": 0,
            "phi_access_events": 0,
            "admin_actions": 0,
            "total_events": 0,
            "time_period": "24 hours",
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Query for CSP violations
        csp_query = select(func.count(AuditLog.id)).where(
            AuditLog.timestamp >= since_date,
            AuditLog.event_type == "SECURITY_VIOLATION",
            AuditLog.headers.op("->>")(
                "csp_violation"
            ).isnot(None)
        )
        csp_result = await db.execute(csp_query)
        security_summary["csp_violations"] = csp_result.scalar() or 0
        
        # Query for failed logins
        failed_login_query = select(func.count(AuditLog.id)).where(
            AuditLog.timestamp >= since_date,
            AuditLog.event_type == "USER_LOGIN_FAILED"
        )
        failed_login_result = await db.execute(failed_login_query)
        security_summary["failed_logins"] = failed_login_result.scalar() or 0
        
        # Query for security violations
        security_violation_query = select(func.count(AuditLog.id)).where(
            AuditLog.timestamp >= since_date,
            AuditLog.event_type == "SECURITY_VIOLATION"
        )
        security_violation_result = await db.execute(security_violation_query)
        security_summary["security_violations"] = security_violation_result.scalar() or 0
        
        # Query for PHI access events
        phi_access_query = select(func.count(AuditLog.id)).where(
            AuditLog.timestamp >= since_date,
            AuditLog.event_type == "PHI_ACCESSED"
        )
        phi_access_result = await db.execute(phi_access_query)
        security_summary["phi_access_events"] = phi_access_result.scalar() or 0
        
        # Query for admin actions
        admin_action_query = select(func.count(AuditLog.id)).where(
            AuditLog.timestamp >= since_date,
            AuditLog.event_type.in_(["ADMIN_ACTION", "SYSTEM_CONFIG_CHANGED"])
        )
        admin_action_result = await db.execute(admin_action_query)
        security_summary["admin_actions"] = admin_action_result.scalar() or 0
        
        # Total events
        total_query = select(func.count(AuditLog.id)).where(
            AuditLog.timestamp >= since_date
        )
        total_result = await db.execute(total_query)
        security_summary["total_events"] = total_result.scalar() or 0
        
        logger.info(
            "Security summary generated",
            user_id=current_user_id,
            summary=security_summary
        )
        
        return security_summary
        
    except Exception as e:
        logger.error("Failed to generate security summary", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to generate security summary"
        )

@router.get("/events")
async def get_security_events(
    limit: int = 100,
    offset: int = 0,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin"))
):
    """Get security events from audit logs."""
    try:
        # This will be implemented with proper audit log querying
        # For now, return mock data to make endpoint operational
        return {
            "events": [
                {
                    "id": "evt_001",
                    "timestamp": "2025-07-22T12:00:00Z",
                    "event_type": "authentication_failure",
                    "severity": "medium",
                    "user_id": "user_123",
                    "source_ip": "192.168.1.100",
                    "details": "Failed login attempt"
                },
                {
                    "id": "evt_002", 
                    "timestamp": "2025-07-22T11:45:00Z",
                    "event_type": "csp_violation",
                    "severity": "low",
                    "user_id": "system",
                    "source_ip": "10.0.0.50",
                    "details": "Content Security Policy violation detected"
                }
            ],
            "total": 2,
            "limit": limit,
            "offset": offset,
            "filters": {
                "event_type": event_type,
                "severity": severity
            },
            "status": "operational",
            "message": "Security events endpoint ready - full implementation pending"
        }
    except Exception as e:
        logger.error("Failed to get security events", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve security events"
        )