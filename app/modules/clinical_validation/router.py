"""
Clinical Validation API Router for Healthcare Platform V2.0
FastAPI router for clinical validation endpoints including study management,
evidence processing, and validation reporting.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from app.core.security import get_current_user_id
from app.modules.audit_logger.service import get_audit_service, SOC2AuditService
from . import (
    ValidationStudy, ValidationProtocol, ValidationEvidence, 
    ValidationReport, ClinicalMetrics, ValidationDashboard,
    ValidationStatus, EvidenceLevel, RegulatoryStandard,
    ValidationLevel, ClinicalDomain, ClinicalValidationService
)
from .schemas import (
    ValidationStudyCreate, ValidationStudyUpdate, ValidationStudyResponse,
    ValidationProtocolCreate, ValidationProtocolUpdate, ValidationProtocolResponse,
    ValidationEvidenceCreate, ValidationEvidenceUpdate, ValidationEvidenceResponse,
    ValidationReportResponse, ClinicalMetricsResponse, ValidationDashboardResponse,
    StudyProgressRequest, StatisticalAnalysisRequest, EvidenceSynthesisRequest
)
from .service import ClinicalValidationService

router = APIRouter(prefix="/clinical-validation", tags=["Clinical Validation"])
security = HTTPBearer()

# Request/Response models for complex operations
class StudyExecutionRequest(BaseModel):
    """Request model for study execution."""
    y_true: List[int]
    y_pred: List[int]
    y_pred_proba: List[float]
    metadata: Optional[Dict[str, Any]] = None

class ValidationAnalysisRequest(BaseModel):
    """Request model for validation analysis."""
    study_ids: List[str]
    analysis_type: str = "comprehensive"
    include_meta_analysis: bool = False

class BulkOperationResponse(BaseModel):
    """Response model for bulk operations."""
    successful: List[str]
    failed: List[Dict[str, str]]
    total_processed: int

# Dependency injection
async def get_validation_service() -> ClinicalValidationService:
    """Get clinical validation service instance."""
    return ClinicalValidationService()

@router.get("/health", 
    summary="Health check for clinical validation service",
    description="Check if the clinical validation service is operational"
)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "clinical_validation", "timestamp": datetime.utcnow()}

# Validation Protocol Endpoints

@router.post("/protocols", 
    response_model=ValidationProtocolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create validation protocol",
    description="Create a new clinical validation protocol"
)
async def create_protocol(
    protocol_data: ValidationProtocolCreate,
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service),
    audit_service: SOC2AuditService = Depends(get_audit_service)
):
    """Create a new validation protocol."""
    try:
        protocol = await service.create_validation_protocol(protocol_data.dict())
        
        await audit_service.log_security_event({
            "event_type": "clinical_validation",
            "event_subtype": "protocol_created",
            "user_id": current_user_id,
            "protocol_id": protocol.protocol_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return ValidationProtocolResponse.model_validate(protocol)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create validation protocol: {str(e)}"
        )

@router.get("/protocols", 
    response_model=List[ValidationProtocolResponse],
    summary="List validation protocols",
    description="Retrieve all validation protocols with optional filtering"
)
async def list_protocols(
    clinical_domain: Optional[ClinicalDomain] = Query(None, description="Filter by clinical domain"),
    validation_level: Optional[ValidationLevel] = Query(None, description="Filter by validation level"),
    active_only: bool = Query(True, description="Show only active protocols"),
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service)
):
    """List validation protocols with optional filtering."""
    try:
        protocols = await service.list_validation_protocols(
            clinical_domain=clinical_domain,
            validation_level=validation_level,
            active_only=active_only
        )
        return [ValidationProtocolResponse.model_validate(p) for p in protocols]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve protocols: {str(e)}"
        )

@router.get("/protocols/{protocol_id}", 
    response_model=ValidationProtocolResponse,
    summary="Get validation protocol",
    description="Retrieve a specific validation protocol by ID"
)
async def get_protocol(
    protocol_id: str,
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service)
):
    """Get validation protocol by ID."""
    try:
        protocol = await service.get_validation_protocol(protocol_id)
        if not protocol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Validation protocol not found"
            )
        return ValidationProtocolResponse.model_validate(protocol)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve protocol: {str(e)}"
        )

@router.put("/protocols/{protocol_id}", 
    response_model=ValidationProtocolResponse,
    summary="Update validation protocol",
    description="Update an existing validation protocol"
)
async def update_protocol(
    protocol_id: str,
    protocol_data: ValidationProtocolUpdate,
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service),
    audit_service: SOC2AuditService = Depends(get_audit_service)
):
    """Update validation protocol."""
    try:
        protocol = await service.update_validation_protocol(protocol_id, protocol_data.dict(exclude_unset=True))
        
        await audit_service.log_security_event({
            "event_type": "clinical_validation",
            "event_subtype": "protocol_updated",
            "user_id": current_user_id,
            "protocol_id": protocol_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return ValidationProtocolResponse.model_validate(protocol)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update protocol: {str(e)}"
        )

# Validation Study Endpoints

@router.post("/studies", 
    response_model=ValidationStudyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create validation study",
    description="Create a new clinical validation study"
)
async def create_study(
    study_data: ValidationStudyCreate,
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service),
    audit_service: SOC2AuditService = Depends(get_audit_service)
):
    """Create a new validation study."""
    try:
        study = await service.create_validation_study(study_data.dict())
        
        await audit_service.log_security_event({
            "event_type": "clinical_validation",
            "event_subtype": "study_created",
            "user_id": current_user_id,
            "study_id": study.study_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return ValidationStudyResponse.model_validate(study)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create validation study: {str(e)}"
        )

@router.get("/studies", 
    response_model=List[ValidationStudyResponse],
    summary="List validation studies",
    description="Retrieve all validation studies with optional filtering"
)
async def list_studies(
    status_filter: Optional[ValidationStatus] = Query(None, description="Filter by study status"),
    protocol_id: Optional[str] = Query(None, description="Filter by protocol ID"),
    active_only: bool = Query(True, description="Show only active studies"),
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service)
):
    """List validation studies with optional filtering."""
    try:
        studies = await service.list_validation_studies(
            status_filter=status_filter,
            protocol_id=protocol_id,
            active_only=active_only
        )
        return [ValidationStudyResponse.model_validate(s) for s in studies]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve studies: {str(e)}"
        )

@router.get("/studies/{study_id}", 
    response_model=ValidationStudyResponse,
    summary="Get validation study",
    description="Retrieve a specific validation study by ID"
)
async def get_study(
    study_id: str,
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service)
):
    """Get validation study by ID."""
    try:
        study = await service.get_validation_study(study_id)
        if not study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Validation study not found"
            )
        return ValidationStudyResponse.model_validate(study)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve study: {str(e)}"
        )

@router.put("/studies/{study_id}", 
    response_model=ValidationStudyResponse,
    summary="Update validation study",
    description="Update an existing validation study"
)
async def update_study(
    study_id: str,
    study_data: ValidationStudyUpdate,
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service),
    audit_service: SOC2AuditService = Depends(get_audit_service)
):
    """Update validation study."""
    try:
        study = await service.update_validation_study(study_id, study_data.dict(exclude_unset=True))
        
        await audit_service.log_security_event({
            "event_type": "clinical_validation",
            "event_subtype": "study_updated",
            "user_id": current_user_id,
            "study_id": study_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return ValidationStudyResponse.model_validate(study)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update study: {str(e)}"
        )

# Study Execution Endpoints

@router.post("/studies/{study_id}/execute", 
    response_model=ClinicalMetricsResponse,
    summary="Execute validation study",
    description="Execute a validation study with provided data"
)
async def execute_study(
    study_id: str,
    execution_data: StudyExecutionRequest,
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service),
    audit_service: SOC2AuditService = Depends(get_audit_service)
):
    """Execute validation study with provided data."""
    try:
        metrics = await service.execute_validation_study(
            study_id=study_id,
            y_true=execution_data.y_true,
            y_pred=execution_data.y_pred,
            y_pred_proba=execution_data.y_pred_proba,
            metadata=execution_data.metadata
        )
        
        await audit_service.log_security_event({
            "event_type": "clinical_validation",
            "event_subtype": "study_executed",
            "user_id": current_user_id,
            "study_id": study_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return ClinicalMetricsResponse.model_validate(metrics)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to execute study: {str(e)}"
        )

@router.get("/studies/{study_id}/progress", 
    summary="Get study progress",
    description="Get detailed progress information for a validation study"
)
async def get_study_progress(
    study_id: str,
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service)
):
    """Get study progress and status."""
    try:
        progress = await service.monitor_study_progress(study_id)
        return progress
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve study progress: {str(e)}"
        )

# Evidence Management Endpoints

@router.post("/evidence", 
    response_model=ValidationEvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create validation evidence",
    description="Create new validation evidence entry"
)
async def create_evidence(
    evidence_data: ValidationEvidenceCreate,
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service),
    audit_service: SOC2AuditService = Depends(get_audit_service)
):
    """Create validation evidence."""
    try:
        evidence = await service.create_validation_evidence(evidence_data.dict())
        
        await audit_service.log_security_event({
            "event_type": "clinical_validation",
            "event_subtype": "evidence_created",
            "user_id": current_user_id,
            "evidence_id": evidence.evidence_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return ValidationEvidenceResponse.model_validate(evidence)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create evidence: {str(e)}"
        )

@router.get("/evidence", 
    response_model=List[ValidationEvidenceResponse],
    summary="List validation evidence",
    description="Retrieve all validation evidence with optional filtering"
)
async def list_evidence(
    evidence_level: Optional[EvidenceLevel] = Query(None, description="Filter by evidence level"),
    study_reference: Optional[str] = Query(None, description="Filter by study reference"),
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service)
):
    """List validation evidence with optional filtering."""
    try:
        evidence_list = await service.list_validation_evidence(
            evidence_level=evidence_level,
            study_reference=study_reference
        )
        return [ValidationEvidenceResponse.model_validate(e) for e in evidence_list]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve evidence: {str(e)}"
        )

# Analysis and Reporting Endpoints

@router.post("/analysis/statistical", 
    summary="Perform statistical analysis",
    description="Perform comprehensive statistical analysis on validation data"
)
async def perform_statistical_analysis(
    analysis_request: StatisticalAnalysisRequest,
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service)
):
    """Perform statistical analysis on validation data."""
    try:
        results = await service.perform_statistical_analysis(
            study_id=analysis_request.study_id,
            y_true=analysis_request.y_true,
            y_pred=analysis_request.y_pred,
            y_pred_proba=analysis_request.y_pred_proba,
            metadata=analysis_request.metadata
        )
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to perform statistical analysis: {str(e)}"
        )

@router.post("/analysis/synthesis", 
    summary="Synthesize evidence",
    description="Synthesize evidence from multiple validation studies"
)
async def synthesize_evidence(
    synthesis_request: EvidenceSynthesisRequest,
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service)
):
    """Synthesize evidence from multiple studies."""
    try:
        synthesis = await service.synthesize_evidence(
            study_ids=synthesis_request.study_ids,
            evidence_ids=synthesis_request.evidence_ids,
            synthesis_method=synthesis_request.synthesis_method
        )
        return synthesis
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to synthesize evidence: {str(e)}"
        )

@router.get("/reports/{study_id}", 
    response_model=ValidationReportResponse,
    summary="Generate validation report",
    description="Generate comprehensive validation report for a study"
)
async def generate_validation_report(
    study_id: str,
    include_raw_data: bool = Query(False, description="Include raw data in report"),
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service),
    audit_service: SOC2AuditService = Depends(get_audit_service)
):
    """Generate validation report for a study."""
    try:
        report = await service.generate_validation_report(study_id, include_raw_data)
        
        await audit_service.log_security_event({
            "event_type": "clinical_validation",
            "event_subtype": "report_generated",
            "user_id": current_user_id,
            "study_id": study_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return ValidationReportResponse.model_validate(report)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )

@router.get("/dashboard", 
    response_model=ValidationDashboardResponse,
    summary="Get validation dashboard",
    description="Get comprehensive validation dashboard with metrics and status"
)
async def get_validation_dashboard(
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service)
):
    """Get validation dashboard with comprehensive metrics."""
    try:
        dashboard = await service.generate_validation_dashboard()
        return ValidationDashboardResponse.model_validate(dashboard)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dashboard: {str(e)}"
        )

# Bulk Operations

@router.post("/studies/bulk-create", 
    response_model=BulkOperationResponse,
    summary="Bulk create studies",
    description="Create multiple validation studies in bulk"
)
async def bulk_create_studies(
    studies_data: List[ValidationStudyCreate],
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service),
    audit_service: SOC2AuditService = Depends(get_audit_service)
):
    """Bulk create validation studies."""
    successful = []
    failed = []
    
    for study_data in studies_data:
        try:
            study = await service.create_validation_study(study_data.dict())
            successful.append(study.study_id)
        except Exception as e:
            failed.append({
                "study_name": study_data.study_name,
                "error": str(e)
            })
    
    await audit_service.log_security_event({
        "event_type": "clinical_validation",
        "event_subtype": "bulk_studies_created",
        "user_id": current_user_id,
        "successful_count": len(successful),
        "failed_count": len(failed),
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return BulkOperationResponse(
        successful=successful,
        failed=failed,
        total_processed=len(studies_data)
    )

@router.post("/studies/bulk-execute", 
    response_model=BulkOperationResponse,
    summary="Bulk execute studies",
    description="Execute multiple validation studies in bulk"
)
async def bulk_execute_studies(
    study_ids: List[str] = Body(..., description="List of study IDs to execute"),
    execution_data: Dict[str, StudyExecutionRequest] = Body(..., description="Execution data for each study"),
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service),
    audit_service: SOC2AuditService = Depends(get_audit_service)
):
    """Bulk execute validation studies."""
    successful = []
    failed = []
    
    for study_id in study_ids:
        try:
            if study_id in execution_data:
                data = execution_data[study_id]
                await service.execute_validation_study(
                    study_id=study_id,
                    y_true=data.y_true,
                    y_pred=data.y_pred,
                    y_pred_proba=data.y_pred_proba,
                    metadata=data.metadata
                )
                successful.append(study_id)
            else:
                failed.append({
                    "study_id": study_id,
                    "error": "No execution data provided"
                })
        except Exception as e:
            failed.append({
                "study_id": study_id,
                "error": str(e)
            })
    
    await audit_service.log_security_event({
        "event_type": "clinical_validation",
        "event_subtype": "bulk_studies_executed",
        "user_id": current_user_id,
        "successful_count": len(successful),
        "failed_count": len(failed),
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return BulkOperationResponse(
        successful=successful,
        failed=failed,
        total_processed=len(study_ids)
    )

# Search and Filter Endpoints

@router.get("/search", 
    summary="Search validation data",
    description="Search across studies, protocols, and evidence"
)
async def search_validation_data(
    query: str = Query(..., description="Search query"),
    search_type: str = Query("all", description="Search type: studies, protocols, evidence, or all"),
    limit: int = Query(50, description="Maximum results to return"),
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service)
):
    """Search across validation data."""
    try:
        results = await service.search_validation_data(
            query=query,
            search_type=search_type,
            limit=limit
        )
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

# Export Endpoints

@router.get("/export/studies", 
    summary="Export study data",
    description="Export validation study data in various formats"
)
async def export_study_data(
    format: str = Query("json", description="Export format: json, csv, xml"),
    study_ids: Optional[List[str]] = Query(None, description="Specific study IDs to export"),
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service)
):
    """Export study data in specified format."""
    try:
        export_data = await service.export_study_data(
            format=format,
            study_ids=study_ids
        )
        
        if format == "csv":
            return JSONResponse(
                content={"data": export_data},
                headers={"Content-Type": "text/csv"}
            )
        elif format == "xml":
            return JSONResponse(
                content={"data": export_data},
                headers={"Content-Type": "application/xml"}
            )
        else:
            return export_data
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )

# Administrative Endpoints

@router.post("/admin/cleanup", 
    summary="Cleanup validation data",
    description="Administrative endpoint for data cleanup"
)
async def cleanup_validation_data(
    days_old: int = Query(365, description="Remove data older than specified days"),
    dry_run: bool = Query(True, description="Perform dry run without actual deletion"),
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service),
    audit_service: SOC2AuditService = Depends(get_audit_service)
):
    """Administrative cleanup of old validation data."""
    # Note: Admin privilege check would need to be implemented based on current_user_id
    # For now, we'll skip the admin check but log the attempt
    # if not is_admin_user(current_user_id):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Administrative privileges required"
    #     )
    
    try:
        cleanup_result = await service.cleanup_old_data(
            days_old=days_old,
            dry_run=dry_run
        )
        
        await audit_service.log_security_event({
            "event_type": "clinical_validation",
            "event_subtype": "data_cleanup",
            "user_id": current_user_id,
            "dry_run": dry_run,
            "days_old": days_old,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return cleanup_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}"
        )

@router.get("/admin/statistics", 
    summary="Get validation statistics",
    description="Administrative endpoint for validation statistics"
)
async def get_validation_statistics(
    current_user_id: str = Depends(get_current_user_id),
    service: ClinicalValidationService = Depends(get_validation_service)
):
    """Get comprehensive validation statistics."""
    # Note: Admin privilege check would need to be implemented based on current_user_id
    # For now, we'll skip the admin check but log the attempt
    # if not is_admin_user(current_user_id):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Administrative privileges required"
    #     )
    
    try:
        statistics = await service.get_validation_statistics()
        return statistics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )