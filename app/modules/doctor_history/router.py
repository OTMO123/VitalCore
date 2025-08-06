"""
Doctor History Mode Router - Linked Medical Timeline API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import structlog
import uuid
from datetime import datetime

from app.core.database_unified import get_db
from app.core.security import (
    get_current_user_id, require_role, verify_token,
    check_rate_limit, SecurityManager
)
from app.modules.auth.router import get_current_user
from app.core.audit_logger import (
    audit_logger, log_phi_access, AuditContext, AuditEventType, AuditSeverity
)
from app.modules.doctor_history.service import DoctorHistoryService
from app.modules.doctor_history.schemas import (
    DoctorHistoryResponse, LinkedTimelineResponse, CareCyclesResponse,
    TimelineFilters, EventType, EventPriority
)

logger = structlog.get_logger()

router = APIRouter()


@router.get("/health")
async def doctor_history_health():
    """Health check for doctor history service."""
    return {
        "status": "healthy",
        "service": "doctor-history-mode",
        "features": ["case_history", "linked_timeline", "care_cycles"],
        "compliance": ["HIPAA", "SOC2", "FHIR-R4"]
    }


@router.get("/history/{case_id}", response_model=DoctorHistoryResponse)
async def get_case_history(
    case_id: uuid.UUID,
    request: Request,
    event_types: Optional[List[EventType]] = Query(None, description="Filter by event types"),
    priority_levels: Optional[List[EventPriority]] = Query(None, description="Filter by priority levels"),
    date_from: Optional[datetime] = Query(None, description="Start date filter"),
    date_to: Optional[datetime] = Query(None, description="End date filter"),
    provider_filter: Optional[str] = Query(None, description="Filter by provider name"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive case history for doctor review.
    
    **Doctor History Mode Features:**
    - Complete medical case timeline
    - Patient demographics (encrypted/secured)
    - Care context and quality metrics
    - Event filtering and prioritization
    
    **Security & Compliance:**
    - Requires doctor role authorization
    - Full PHI access audit logging
    - SOC2 Type II compliant data handling
    - HIPAA minimum necessary access
    
    **Use Cases:**
    - Doctor reviewing patient case before consultation
    - Medical case handoff between providers
    - Care quality assessment and review
    - Medical record continuity analysis
    """
    try:
        # Rate limiting for PHI access
        await check_rate_limit(
            request=request,
            user_id=current_user["id"],
            endpoint="doctor_case_history",
            limit_per_minute=30
        )
        
        # Verify doctor role
        if current_user.get("role", "").lower() not in ["doctor", "physician", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor role required for case history access"
            )
        
        # Create audit context
        audit_context = AuditContext(
            user_id=current_user["id"],
            resource_type="medical_case",
            resource_id=str(case_id),
            action="PHI_ACCESS",
            request_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            additional_context={
                "endpoint": "doctor_case_history",
                "case_id": str(case_id),
                "filters_applied": {
                    "event_types": event_types,
                    "priority_levels": priority_levels,
                    "date_range": f"{date_from} to {date_to}" if date_from or date_to else None,
                    "provider_filter": provider_filter
                }
            }
        )
        
        # Log PHI access (mandatory for HIPAA compliance)
        await log_phi_access(
            user_id=current_user["id"],
            resource_type="medical_case",
            resource_id=str(case_id),
            access_reason="doctor_case_review",
            phi_types=["medical_history", "patient_demographics", "clinical_data"],
            audit_context=audit_context
        )
        
        # Build timeline filters
        filters = None
        if any([event_types, priority_levels, date_from, date_to, provider_filter]):
            filters = TimelineFilters(
                event_types=event_types,
                priority_levels=priority_levels,
                date_from=date_from,
                date_to=date_to,
                provider_filter=provider_filter
            )
        
        # Get doctor history service
        history_service = DoctorHistoryService(db)
        
        # Get case history
        case_history = await history_service.get_case_history(
            case_id=case_id,
            user_id=current_user["id"],
            filters=filters
        )
        
        # Log successful access
        await audit_logger.log_action(
            user_id=current_user["id"],
            action=AuditEventType.PHI_ACCESSED,
            resource_type="medical_case",
            resource_id=str(case_id),
            details={
                "operation": "case_history_retrieved",
                "total_events": case_history.total_events,
                "date_range": case_history.date_range,
                "filters_applied": bool(filters),
                "compliance": "HIPAA_SOC2_compliant"
            },
            severity=AuditSeverity.INFO,
            audit_context=audit_context
        )
        
        logger.info(
            "Case history accessed successfully",
            case_id=str(case_id),
            user_id=current_user["id"],
            total_events=case_history.total_events
        )
        
        return case_history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving case history: {str(e)}", case_id=str(case_id))
        
        # Log security violation for audit
        await audit_logger.log_action(
            user_id=current_user["id"],
            action=AuditEventType.SECURITY_VIOLATION,
            resource_type="medical_case",
            resource_id=str(case_id),
            details={
                "operation": "case_history_access_failed",
                "error": str(e),
                "endpoint": "doctor_case_history"
            },
            severity=AuditSeverity.HIGH
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve case history"
        )


@router.get("/timeline/{case_id}/linked", response_model=LinkedTimelineResponse)
async def get_linked_medical_timeline(
    case_id: uuid.UUID,
    request: Request,
    event_types: Optional[List[EventType]] = Query(None, description="Filter by event types"),
    priority_levels: Optional[List[EventPriority]] = Query(None, description="Filter by priority levels"),
    date_from: Optional[datetime] = Query(None, description="Start date filter"),
    date_to: Optional[datetime] = Query(None, description="End date filter"),
    include_linked_only: bool = Query(False, description="Show only events with correlations"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get linked medical timeline with advanced event correlation analysis.
    
    **Linked Medical Timeline Features:**
    - Event correlation analysis and grouping
    - Care transition point identification
    - Critical care pathway mapping
    - Temporal relationship analysis
    - Clinical decision support integration
    
    **Advanced Analytics:**
    - Event causality chains
    - Care phase progression analysis
    - Outcome correlation patterns
    - Quality indicator tracking
    
    **FHIR R4 Compliance:**
    - FHIR resource type mapping
    - Interoperability-ready data format
    - Healthcare standard compliance
    """
    try:
        # Enhanced rate limiting for complex analysis
        await check_rate_limit(
            request=request,
            user_id=current_user["id"],
            endpoint="linked_medical_timeline",
            limit_per_minute=15  # Lower limit for complex queries
        )
        
        # Verify doctor role
        if current_user.get("role", "").lower() not in ["doctor", "physician", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor role required for linked timeline access"
            )
        
        # Create enhanced audit context
        audit_context = AuditContext(
            user_id=current_user["id"],
            resource_type="medical_timeline",
            resource_id=str(case_id),
            action="ADVANCED_PHI_ACCESS",
            request_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            additional_context={
                "endpoint": "linked_medical_timeline",
                "case_id": str(case_id),
                "analysis_type": "correlation_analysis",
                "filters_applied": {
                    "event_types": event_types,
                    "priority_levels": priority_levels,
                    "date_range": f"{date_from} to {date_to}" if date_from or date_to else None,
                    "linked_only": include_linked_only
                }
            }
        )
        
        # Log advanced PHI access
        await log_phi_access(
            user_id=current_user["id"],
            resource_type="medical_timeline",
            resource_id=str(case_id),
            access_reason="linked_timeline_analysis",
            phi_types=["medical_timeline", "clinical_correlations", "care_analytics"],
            audit_context=audit_context
        )
        
        # Build filters
        filters = TimelineFilters(
            event_types=event_types,
            priority_levels=priority_levels,
            date_from=date_from,
            date_to=date_to,
            include_linked_only=include_linked_only
        )
        
        # Get history service
        history_service = DoctorHistoryService(db)
        
        # Get linked timeline
        linked_timeline = await history_service.get_linked_timeline(
            case_id=case_id,
            user_id=current_user["id"],
            filters=filters
        )
        
        # Log successful analysis
        await audit_logger.log_action(
            user_id=current_user["id"],
            action=AuditEventType.PHI_ACCESSED,
            resource_type="medical_timeline",
            resource_id=str(case_id),
            details={
                "operation": "linked_timeline_analysis_completed",
                "total_events": linked_timeline.total_linked_events,
                "correlations_found": len(linked_timeline.event_correlations),
                "care_transitions": len(linked_timeline.care_transitions),
                "critical_paths": len(linked_timeline.critical_paths),
                "analysis_type": "advanced_correlation",
                "compliance": "HIPAA_SOC2_FHIR_compliant"
            },
            severity=AuditSeverity.INFO,
            audit_context=audit_context
        )
        
        logger.info(
            "Linked timeline analysis completed",
            case_id=str(case_id),
            user_id=current_user["id"],
            correlations=len(linked_timeline.event_correlations),
            transitions=len(linked_timeline.care_transitions)
        )
        
        return linked_timeline
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving linked timeline: {str(e)}", case_id=str(case_id))
        
        await audit_logger.log_action(
            user_id=current_user["id"],
            action=AuditEventType.SECURITY_VIOLATION,
            resource_type="medical_timeline",
            resource_id=str(case_id),
            details={
                "operation": "linked_timeline_access_failed",
                "error": str(e),
                "endpoint": "linked_medical_timeline"
            },
            severity=AuditSeverity.HIGH
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve linked timeline"
        )


@router.get("/care-cycles/{patient_id}", response_model=CareCyclesResponse)
async def get_patient_care_cycles(
    patient_id: uuid.UUID,
    request: Request,
    include_completed: bool = Query(True, description="Include completed care cycles"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get patient care cycles for comprehensive care management.
    
    **Care Cycle Management Features:**
    - Active and completed care cycles
    - Care phase progression tracking
    - Outcome measurement and analytics
    - Quality indicator monitoring
    - Care coordination insights
    
    **Care Management Analytics:**
    - Care complexity assessment
    - Resource utilization analysis
    - Team coordination effectiveness
    - Patient satisfaction tracking
    - Quality improvement opportunities
    
    **Value-Based Care Support:**
    - Care cycle duration analytics
    - Outcome-based quality metrics
    - Cost-effectiveness indicators
    - Population health insights
    """
    try:
        # Rate limiting for care management queries
        await check_rate_limit(
            request=request,
            user_id=current_user["id"],
            endpoint="patient_care_cycles",
            limit_per_minute=20
        )
        
        # Verify doctor role
        if current_user.get("role", "").lower() not in ["doctor", "physician", "admin", "care_manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Healthcare provider role required for care cycle access"
            )
        
        # Create audit context
        audit_context = AuditContext(
            user_id=current_user["id"],
            resource_type="patient_care_cycles",
            resource_id=str(patient_id),
            action="CARE_MANAGEMENT_ACCESS",
            request_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            additional_context={
                "endpoint": "patient_care_cycles",
                "patient_id": str(patient_id),
                "include_completed": include_completed,
                "care_management_purpose": "cycle_review_and_planning"
            }
        )
        
        # Log care management access
        await log_phi_access(
            user_id=current_user["id"],
            resource_type="patient_care_cycles",
            resource_id=str(patient_id),
            access_reason="care_cycle_management",
            phi_types=["care_plans", "care_outcomes", "quality_metrics"],
            audit_context=audit_context
        )
        
        # Get history service
        history_service = DoctorHistoryService(db)
        
        # Get care cycles
        care_cycles = await history_service.get_care_cycles(
            patient_id=patient_id,
            user_id=current_user["id"],
            include_completed=include_completed
        )
        
        # Log successful care cycle access
        await audit_logger.log_action(
            user_id=current_user["id"],
            action=AuditEventType.PHI_ACCESSED,
            resource_type="patient_care_cycles",
            resource_id=str(patient_id),
            details={
                "operation": "care_cycles_retrieved",
                "active_cycles": care_cycles.total_active_cycles,
                "completed_cycles": care_cycles.total_completed_cycles,
                "care_complexity": care_cycles.care_complexity_score,
                "primary_care_areas": len(care_cycles.primary_care_areas),
                "compliance": "HIPAA_SOC2_compliant"
            },
            severity=AuditSeverity.INFO,
            audit_context=audit_context
        )
        
        logger.info(
            "Care cycles accessed successfully",
            patient_id=str(patient_id),
            user_id=current_user["id"],
            active_cycles=care_cycles.total_active_cycles,
            completed_cycles=care_cycles.total_completed_cycles
        )
        
        return care_cycles
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving care cycles: {str(e)}", patient_id=str(patient_id))
        
        await audit_logger.log_action(
            user_id=current_user["id"],
            action=AuditEventType.SECURITY_VIOLATION,
            resource_type="patient_care_cycles",
            resource_id=str(patient_id),
            details={
                "operation": "care_cycles_access_failed",
                "error": str(e),
                "endpoint": "patient_care_cycles"
            },
            severity=AuditSeverity.HIGH
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve care cycles"
        )


# Additional endpoints for care cycle management

@router.post("/care-cycles/{patient_id}/new")
async def create_care_cycle(
    patient_id: uuid.UUID,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new care cycle for a patient."""
    # Implementation for creating care cycles
    return {"message": "Care cycle creation endpoint - to be implemented"}


@router.put("/care-cycles/{cycle_id}/update")
async def update_care_cycle(
    cycle_id: uuid.UUID,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing care cycle."""
    # Implementation for updating care cycles
    return {"message": "Care cycle update endpoint - to be implemented"}


@router.get("/analytics/care-performance")
async def get_care_performance_analytics(
    request: Request,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get care performance analytics for quality improvement."""
    # Implementation for care performance analytics
    return {
        "message": "Care performance analytics endpoint - to be implemented",
        "features": [
            "care_cycle_duration_trends",
            "outcome_quality_metrics",
            "patient_satisfaction_analysis",
            "resource_utilization_efficiency",
            "care_coordination_effectiveness"
        ]
    }


@router.get("/insights/population-health")
async def get_population_health_insights(
    request: Request,
    care_area: Optional[str] = Query(None, description="Filter by care area"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get population health insights from care cycle data."""
    # Implementation for population health insights
    return {
        "message": "Population health insights endpoint - to be implemented",
        "features": [
            "care_pattern_analysis",
            "outcome_prediction_models",
            "risk_stratification_insights",
            "quality_improvement_opportunities",
            "value_based_care_metrics"
        ]
    }