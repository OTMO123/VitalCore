"""
FHIR Security API Router for Healthcare Platform V2.0

RESTful API endpoints for enhanced FHIR security labels, consent management,
access control, and provenance tracking with SOC2/HIPAA compliance.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Dict, List, Any, Optional, Union
import uuid
from datetime import datetime, timedelta

from .schemas import (
    SecurityLabel, SecurityLabelRequest, ConsentPolicy, ConsentRequest, ConsentContext,
    ProvenanceRecord, AccessRequest, AccessDecision, ComplianceResult,
    FHIRSecurityConfig, SecurityReport, BreachNotification, SecurityAuditEvent
)
from .fhir_secure_handler import FHIRSecureHandler
from .security_labels import SecurityLabelManager, LabelingContext
from .consent_manager import ConsentManager
from .provenance_tracker import ProvenanceTracker
from ..auth.service import get_current_user_id, require_role
from ...core.audit_logger import audit_log
from ...core.config import get_settings

router = APIRouter(prefix="/api/v1/fhir-security", tags=["FHIR Security"])
settings = get_settings()

# Initialize FHIR security components
security_config = FHIRSecurityConfig()
fhir_handler = FHIRSecureHandler(security_config)
label_manager = SecurityLabelManager(security_config)
consent_manager = ConsentManager(security_config)
provenance_tracker = ProvenanceTracker(security_config)

@router.post("/security-labels/apply", response_model=Dict[str, Any])
@audit_log("apply_security_labels")
async def apply_security_labels(
    request: SecurityLabelRequest,
    current_user: str = Depends(require_role("doctor"))
) -> Dict[str, Any]:
    """
    Apply security labels to a FHIR resource.
    
    Args:
        request: Security labeling request
        
    Returns:
        Applied security labels information
    """
    try:
        # Create labeling context
        labeling_context = LabelingContext(
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            data_elements=[],  # Would be populated from actual resource
            clinical_context={},
            patient_demographics={},
            organizational_policy={},
            regulatory_requirements=["HIPAA", "FHIR_R4"]
        )
        
        # Mock resource for demonstration
        mock_resource = type('MockResource', (), {
            'resource_type': request.resource_type,
            'id': request.resource_id,
            'meta': None
        })()
        
        # Classify sensitivity
        classification, applied_rules = await label_manager.classify_resource_sensitivity(
            mock_resource, labeling_context
        )
        
        # Apply security labels
        applied_labels = await label_manager.apply_security_labels(
            mock_resource, classification, request.handling_instructions
        )
        
        # Validate compliance
        compliance_result = await label_manager.validate_label_compliance(
            mock_resource, ["HIPAA", "FHIR_R4", "SOC2"]
        )
        
        return {
            "resource_type": request.resource_type,
            "resource_id": request.resource_id,
            "classification": classification.value,
            "applied_labels": [
                {
                    "system": label.system,
                    "code": label.code,
                    "display": label.display,
                    "category": label.category.value
                }
                for label in applied_labels
            ],
            "applied_rules": applied_rules,
            "compliance_result": compliance_result,
            "labeling_timestamp": datetime.utcnow().isoformat(),
            "labeled_by": current_user
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply security labels: {str(e)}"
        )

@router.post("/consent/create", response_model=ConsentContext)
@audit_log("create_consent_record")
async def create_consent_record(
    patient_id: str,
    consent_policies: List[str],
    granular_permissions: Optional[Dict[str, Any]] = None,
    consent_method: str = "digital_signature",
    current_user: str = Depends(require_role("doctor"))
) -> ConsentContext:
    """
    Create a new consent record for a patient.
    
    Args:
        patient_id: Patient identifier
        consent_policies: List of consent policy IDs
        granular_permissions: Specific permissions and restrictions
        consent_method: Method of consent capture
        
    Returns:
        Created consent context
    """
    try:
        consent_context = await consent_manager.create_consent_record(
            patient_id=patient_id,
            consent_policies=consent_policies,
            granular_permissions=granular_permissions,
            consent_method=consent_method,
            witness_info={"created_by": current_user}
        )
        
        return consent_context
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create consent record: {str(e)}"
        )

@router.post("/consent/validate", response_model=Dict[str, Any])
@audit_log("validate_consent_access")
async def validate_consent_for_access(
    request: ConsentRequest,
    current_user: str = Depends(require_role("technician"))
) -> Dict[str, Any]:
    """
    Validate consent for specific data access request.
    
    Args:
        request: Consent validation request
        
    Returns:
        Validation result with permission details
    """
    try:
        validation_result = await consent_manager.validate_consent_for_access(
            patient_id=request.patient_id,
            access_purpose=request.purpose,
            data_categories=request.data_categories,
            requesting_user=current_user,
            access_context={
                "urgency_level": request.urgency_level,
                "duration_hours": request.access_duration_hours,
                "justification": request.clinical_justification
            }
        )
        
        return validation_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate consent: {str(e)}"
        )

@router.put("/consent/{patient_id}/withdraw", response_model=Dict[str, Any])
@audit_log("withdraw_consent")
async def withdraw_consent(
    patient_id: str,
    withdrawal_scope: str = "all",
    withdrawal_reason: Optional[str] = None,
    current_user: str = Depends(require_role("patient"))
) -> Dict[str, Any]:
    """
    Process consent withdrawal request.
    
    Args:
        patient_id: Patient identifier
        withdrawal_scope: Scope of withdrawal
        withdrawal_reason: Reason for withdrawal
        
    Returns:
        Withdrawal processing result
    """
    try:
        withdrawal_result = await consent_manager.withdraw_consent(
            patient_id=patient_id,
            withdrawal_scope=withdrawal_scope,
            withdrawal_reason=withdrawal_reason
        )
        
        return withdrawal_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process consent withdrawal: {str(e)}"
        )

@router.get("/consent/{patient_id}/status", response_model=Dict[str, Any])
async def get_consent_status(
    patient_id: str,
    current_user: str = Depends(require_role("doctor"))
) -> Dict[str, Any]:
    """
    Get comprehensive consent status for a patient.
    
    Args:
        patient_id: Patient identifier
        
    Returns:
        Comprehensive consent status
    """
    try:
        consent_status = await consent_manager.get_consent_status(patient_id)
        return consent_status
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get consent status: {str(e)}"
        )

@router.post("/provenance/create", response_model=ProvenanceRecord)
@audit_log("create_provenance_record")
async def create_provenance_record(
    resource_type: str,
    resource_id: str,
    action: str,
    agent_info: Dict[str, Any],
    activity_details: Optional[Dict[str, Any]] = None,
    current_user: str = Depends(require_role("system"))
) -> ProvenanceRecord:
    """
    Create a new provenance record for resource activity.
    
    Args:
        resource_type: Type of FHIR resource
        resource_id: Resource identifier
        action: Action performed
        agent_info: Information about the agent
        activity_details: Additional activity details
        
    Returns:
        Created provenance record
    """
    try:
        from .schemas import ProvenanceAction
        
        # Validate and convert action
        try:
            provenance_action = ProvenanceAction(action.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {action}"
            )
        
        # Add current user to agent info if not provided
        if "id" not in agent_info:
            agent_info["id"] = current_user
        
        provenance_record = await provenance_tracker.create_provenance_record(
            resource_type=resource_type,
            resource_id=resource_id,
            action=provenance_action,
            agent_info=agent_info,
            activity_details=activity_details
        )
        
        return provenance_record
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create provenance record: {str(e)}"
        )

@router.post("/provenance/lineage", response_model=ProvenanceRecord)
@audit_log("track_data_lineage")
async def track_data_lineage(
    source_resource_id: str,
    derived_resource_id: str,
    transformation_details: Dict[str, Any],
    agent_info: Dict[str, Any],
    current_user: str = Depends(require_role("system"))
) -> ProvenanceRecord:
    """
    Track data lineage between source and derived resources.
    
    Args:
        source_resource_id: Source resource identifier
        derived_resource_id: Derived resource identifier
        transformation_details: Details about the transformation
        agent_info: Agent performing transformation
        
    Returns:
        Lineage provenance record
    """
    try:
        # Add current user to agent info if not provided
        if "id" not in agent_info:
            agent_info["id"] = current_user
        
        lineage_record = await provenance_tracker.track_data_lineage(
            source_resource_id=source_resource_id,
            derived_resource_id=derived_resource_id,
            transformation_details=transformation_details,
            agent_info=agent_info
        )
        
        return lineage_record
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track data lineage: {str(e)}"
        )

@router.get("/provenance/{resource_type}/{resource_id}/integrity", response_model=Dict[str, Any])
async def verify_provenance_integrity(
    resource_type: str,
    resource_id: str,
    current_user: str = Depends(require_role("auditor"))
) -> Dict[str, Any]:
    """
    Verify the integrity of provenance chain for a resource.
    
    Args:
        resource_type: Type of FHIR resource
        resource_id: Resource identifier
        
    Returns:
        Integrity verification result
    """
    try:
        verification_result = await provenance_tracker.verify_provenance_integrity(
            resource_type=resource_type,
            resource_id=resource_id
        )
        
        return verification_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify provenance integrity: {str(e)}"
        )

@router.get("/provenance/{resource_type}/{resource_id}/history", response_model=Dict[str, Any])
async def get_provenance_history(
    resource_type: str,
    resource_id: str,
    include_lineage: bool = True,
    current_user: str = Depends(require_role("doctor"))
) -> Dict[str, Any]:
    """
    Get complete provenance history for a resource.
    
    Args:
        resource_type: Type of FHIR resource
        resource_id: Resource identifier
        include_lineage: Whether to include data lineage
        
    Returns:
        Complete provenance history
    """
    try:
        history = await provenance_tracker.get_resource_provenance_history(
            resource_type=resource_type,
            resource_id=resource_id,
            include_lineage=include_lineage
        )
        
        return history
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get provenance history: {str(e)}"
        )

@router.post("/access-control/evaluate", response_model=AccessDecision)
@audit_log("evaluate_access_control")
async def evaluate_access_control(
    request: AccessRequest,
    current_user: str = Depends(require_role("system"))
) -> AccessDecision:
    """
    Evaluate access control for FHIR resource request.
    
    Args:
        request: Access control request
        
    Returns:
        Access control decision
    """
    try:
        resource_request = {
            "resource_type": request.resource_type,
            "resource_id": request.resource_id,
            "access_type": request.access_type.value,
            "purpose": request.purpose,
            "emergency_access": request.emergency_access
        }
        
        user_permissions = {
            "user_id": request.user_context.user_id,
            "user_role": request.user_context.user_role,
            "organization_id": request.user_context.organization_id,
            "security_clearance": request.user_context.security_clearance.value,
            "access_scopes": request.user_context.access_scopes
        }
        
        access_decision = await fhir_handler.manage_fhir_access_control(
            resource_request=resource_request,
            user_permissions=user_permissions
        )
        
        return access_decision
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate access control: {str(e)}"
        )

@router.post("/compliance/validate", response_model=ComplianceResult)
@audit_log("validate_security_compliance")
async def validate_security_compliance(
    resource_type: str,
    resource_id: str,
    compliance_standards: List[str] = ["HIPAA", "FHIR_R4", "SOC2"],
    current_user: str = Depends(require_role("compliance_officer"))
) -> ComplianceResult:
    """
    Validate security compliance for a FHIR resource.
    
    Args:
        resource_type: Type of FHIR resource
        resource_id: Resource identifier
        compliance_standards: Required compliance standards
        
    Returns:
        Compliance validation result
    """
    try:
        # Mock resource for validation
        mock_resource = type('MockResource', (), {
            'resource_type': resource_type,
            'id': resource_id,
            'meta': None
        })()
        
        policy = {
            "require_security_labels": True,
            "require_consent": True,
            "require_encryption": True,
            "require_audit": True,
            "compliance_standards": compliance_standards
        }
        
        compliance_result = await fhir_handler.validate_fhir_security_compliance(
            resource=mock_resource,
            policy=policy
        )
        
        # Convert to response format
        return ComplianceResult(
            resource_id=resource_id,
            resource_type=resource_type,
            compliant=compliance_result.compliant,
            compliance_score=compliance_result.compliance_score,
            violations=compliance_result.violations,
            recommendations=compliance_result.recommendations,
            compliance_standards=compliance_result.compliance_standards,
            validator_id=current_user,
            policy_version="1.0",
            compliance_level="full" if compliance_result.compliant else "partial"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate security compliance: {str(e)}"
        )

@router.get("/reports/security", response_model=SecurityReport)
async def generate_security_report(
    start_date: datetime,
    end_date: datetime,
    report_type: str = "compliance",
    current_user: str = Depends(require_role("security_officer"))
) -> SecurityReport:
    """
    Generate comprehensive security report.
    
    Args:
        start_date: Report period start
        end_date: Report period end
        report_type: Type of report to generate
        
    Returns:
        Security report
    """
    try:
        # Generate provenance report
        provenance_report = await provenance_tracker.generate_provenance_report(
            start_date=start_date,
            end_date=end_date
        )
        
        # Generate basic security report
        report = SecurityReport(
            report_type=report_type,
            report_period_start=start_date,
            report_period_end=end_date,
            generated_by=current_user,
            total_access_events=provenance_report["summary_statistics"]["total_provenance_records"],
            compliant_access_events=int(provenance_report["summary_statistics"]["total_provenance_records"] * 0.95),  # Mock
            non_compliant_access_events=int(provenance_report["summary_statistics"]["total_provenance_records"] * 0.05),  # Mock
            overall_compliance_score=0.95,  # Mock
            hipaa_compliance_score=0.97,    # Mock
            gdpr_compliance_score=0.93,     # Mock
            soc2_compliance_score=0.96,     # Mock
            security_recommendations=[
                "Continue monitoring after-hours access",
                "Review emergency access procedures",
                "Update consent management policies"
            ]
        )
        
        return report
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate security report: {str(e)}"
        )

@router.post("/breach/notify", response_model=Dict[str, str])
@audit_log("security_breach_notification")
async def notify_security_breach(
    breach: BreachNotification,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(require_role("security_officer"))
) -> Dict[str, str]:
    """
    Report and process security breach notification.
    
    Args:
        breach: Security breach details
        background_tasks: Background task queue
        
    Returns:
        Breach notification confirmation
    """
    try:
        # Store breach notification
        breach.discovered_by = current_user
        breach.investigation_lead = current_user
        
        # Schedule background processing
        background_tasks.add_task(
            _process_breach_notification,
            breach
        )
        
        return {
            "breach_id": breach.breach_id,
            "status": "reported",
            "investigation_started": "true",
            "notification_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process breach notification: {str(e)}"
        )

@router.get("/config", response_model=FHIRSecurityConfig)
async def get_security_configuration(
    current_user: str = Depends(require_role("admin"))
) -> FHIRSecurityConfig:
    """
    Get current FHIR security configuration.
    
    Returns:
        Current security configuration
    """
    return security_config

@router.put("/config", response_model=Dict[str, str])
@audit_log("update_security_configuration")
async def update_security_configuration(
    config: FHIRSecurityConfig,
    current_user: str = Depends(require_role("admin"))
) -> Dict[str, str]:
    """
    Update FHIR security configuration.
    
    Args:
        config: New security configuration
        
    Returns:
        Update confirmation
    """
    try:
        # Validate configuration
        if not config.enable_security_labels and config.require_consent_validation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot require consent validation without security labels"
            )
        
        # Update global configuration
        global security_config
        security_config = config
        
        return {
            "status": "updated",
            "updated_by": current_user,
            "update_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update security configuration: {str(e)}"
        )

@router.get("/health", response_model=Dict[str, Any])
async def fhir_security_health_check() -> Dict[str, Any]:
    """
    FHIR security service health check.
    
    Returns:
        Service health status
    """
    try:
        # Check consent expiry
        expiry_check = await consent_manager.check_consent_expiry()
        
        return {
            "status": "healthy",
            "security_labels_enabled": security_config.enable_security_labels,
            "consent_management_enabled": security_config.require_consent_validation,
            "encryption_enabled": security_config.enable_encryption,
            "digital_signatures_enabled": security_config.enable_digital_signatures,
            "active_consents": len(consent_manager.active_consents),
            "expiring_consents": len(expiry_check["expiring_soon"]),
            "provenance_chains": len(provenance_tracker.provenance_chains),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Background task functions

async def _process_breach_notification(breach: BreachNotification):
    """Process security breach notification in background."""
    try:
        # Log critical security event
        audit_event = SecurityAuditEvent(
            event_type="security_breach",
            severity="critical",
            event_details={
                "breach_id": breach.breach_id,
                "breach_type": breach.breach_type,
                "affected_resources": breach.affected_resources,
                "affected_patients": breach.affected_patients,
                "severity": breach.severity
            },
            outcome="failure"
        )
        
        # In production, would:
        # 1. Notify security team
        # 2. Initiate incident response
        # 3. Update affected patient records
        # 4. Generate regulatory notifications
        # 5. Implement containment measures
        
        logger.info(f"Security breach {breach.breach_id} processed")
        
    except Exception as e:
        logger.error(f"Failed to process breach notification: {str(e)}")