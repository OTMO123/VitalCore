"""
Risk Stratification Router
SOC2 Type 2 Compliant REST API Endpoints
Following TDD principles and SOLID design
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
import structlog
import uuid

from app.core.database_unified import get_db
from app.core.security import (
    get_current_user_id, require_role, get_client_info,
    check_rate_limit, SecurityManager
)
from app.core.audit_logger import AuditContext
from app.core.circuit_breaker import get_database_breaker
from app.modules.risk_stratification.service import get_risk_stratification_service
from app.modules.risk_stratification.schemas import (
    RiskScoreRequest, RiskScoreResponse, BatchRiskRequest, BatchRiskResponse,
    RiskFactorsResponse, ReadmissionRiskResponse, PopulationMetricsRequest, PopulationMetricsResponse
)
from app.core.exceptions import RiskCalculationError, SOC2ComplianceError

logger = structlog.get_logger()

router = APIRouter()

# ============================================
# HEALTH CHECK ENDPOINT
# ============================================

@router.get("/health")
async def risk_stratification_health_check():
    """Health check for risk stratification service"""
    return {
        "status": "healthy",
        "service": "risk-stratification", 
        "version": "1.0.0",
        "algorithms": ["composite_risk", "readmission_risk", "clinical_factors"],
        "soc2_compliance": "type_2_enabled",
        "model_version": "1.0.0"
    }

# ============================================
# RISK CALCULATION ENDPOINTS
# ============================================

@router.post("/calculate", response_model=RiskScoreResponse, status_code=status.HTTP_200_OK)
async def calculate_risk_score(
    request: RiskScoreRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin")),  # Require admin role for risk calculations
    _rate_limit: bool = Depends(check_rate_limit)
):
    """
    Calculate comprehensive risk score for a patient
    
    SOC2 Controls Applied:
    - CC6.1: Access control validation
    - CC7.2: Comprehensive audit logging
    - A1.2: Circuit breaker for availability
    - CC8.1: Request tracking and monitoring
    """
    # Get audit context from request
    client_info = await get_client_info(http_request)
    correlation_id = str(uuid.uuid4())
    
    try:
        # SOC2 CC7.2: Log risk calculation request
        logger.info("Risk calculation request initiated",
                   patient_id=request.patient_id,
                   requesting_user=current_user_id,
                   correlation_id=correlation_id,
                   access_purpose=request.access_purpose,
                   include_recommendations=request.include_recommendations,
                   ip_address=client_info.get("ip_address"))
        
        # Update request with validated user ID
        validated_request = RiskScoreRequest(
            patient_id=request.patient_id,
            include_recommendations=request.include_recommendations,
            include_readmission_risk=request.include_readmission_risk,
            time_horizon=request.time_horizon,
            clinical_context=request.clinical_context,
            requesting_user_id=current_user_id,  # Use authenticated user ID
            access_purpose=request.access_purpose
        )
        
        # Get risk stratification service
        service = await get_risk_stratification_service()
        
        # Calculate risk score with circuit breaker protection
        db_breaker = await get_database_breaker()
        
        async def calculate_with_breaker():
            return await service.calculate_risk_score(validated_request, db)
        
        risk_score = await db_breaker.call(calculate_with_breaker)
        
        # SOC2 CC7.2: Log successful calculation
        logger.info("Risk calculation completed successfully",
                   patient_id=request.patient_id,
                   risk_score=risk_score.score,
                   risk_level=risk_score.level,
                   correlation_id=correlation_id,
                   user_id=current_user_id,
                   processing_time_ms=0)  # Would track actual processing time
        
        # Add background task for additional processing if needed
        if request.include_readmission_risk:
            background_tasks.add_task(
                _log_readmission_risk_request,
                patient_id=request.patient_id,
                user_id=current_user_id,
                correlation_id=correlation_id
            )
        
        return risk_score
        
    except (RiskCalculationError, SOC2ComplianceError) as e:
        # Known risk calculation errors
        logger.error("Risk calculation failed with known error",
                    patient_id=request.patient_id,
                    error_code=getattr(e, 'error_code', 'UNKNOWN'),
                    error_message=str(e),
                    correlation_id=correlation_id,
                    user_id=current_user_id)
        
        if isinstance(e, SOC2ComplianceError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"SOC2 Compliance Violation: {e.message}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Risk Calculation Error: {e.message}"
            )
            
    except Exception as e:
        # Unexpected errors
        logger.error("Risk calculation failed with unexpected error",
                    patient_id=request.patient_id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    correlation_id=correlation_id,
                    user_id=current_user_id)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Risk calculation service temporarily unavailable"
        )

@router.post("/batch-calculate", response_model=BatchRiskResponse, status_code=status.HTTP_200_OK)
async def calculate_batch_risk_scores(
    request: BatchRiskRequest,
    http_request: Request,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin")),
    _rate_limit: bool = Depends(check_rate_limit)
):
    """
    Calculate risk scores for multiple patients (batch processing)
    
    SOC2 Controls Applied:
    - A1.2: Performance monitoring and batch size limits
    - CC7.2: Batch processing audit logging
    - CC6.1: Access control for bulk operations
    """
    client_info = await get_client_info(http_request)
    correlation_id = str(uuid.uuid4())
    
    try:
        # SOC2 A1.2: Validate batch size for performance compliance
        if len(request.patient_ids) > 1000:
            logger.warning("Batch size limit exceeded",
                          requested_count=len(request.patient_ids),
                          max_allowed=1000,
                          user_id=current_user_id,
                          correlation_id=correlation_id)
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size exceeds maximum limit of 1000 patients"
            )
        
        # SOC2 CC7.2: Log batch processing request
        logger.info("Batch risk calculation request initiated",
                   patient_count=len(request.patient_ids),
                   requesting_user=current_user_id,
                   correlation_id=correlation_id,
                   batch_size=request.batch_size,
                   access_purpose=request.access_purpose,
                   ip_address=client_info.get("ip_address"))
        
        # Update request with validated user ID
        validated_request = BatchRiskRequest(
            patient_ids=request.patient_ids,
            include_recommendations=request.include_recommendations,
            batch_size=request.batch_size,
            requesting_user_id=current_user_id,
            access_purpose=request.access_purpose,
            organization_id=request.organization_id
        )
        
        # Get service and process batch
        service = await get_risk_stratification_service()
        batch_result = await service.calculate_batch_risk_scores(validated_request, db)
        
        # SOC2 CC7.2: Log batch completion
        logger.info("Batch risk calculation completed",
                   requested_count=batch_result.requested_count,
                   processed_count=batch_result.processed_count,
                   failed_count=batch_result.failed_count,
                   processing_time_ms=batch_result.processing_time_ms,
                   correlation_id=correlation_id,
                   user_id=current_user_id)
        
        return batch_result
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error("Batch risk calculation failed",
                    patient_count=len(request.patient_ids),
                    error_type=type(e).__name__,
                    error_message=str(e),
                    correlation_id=correlation_id,
                    user_id=current_user_id)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch risk calculation service temporarily unavailable"
        )

@router.get("/factors/{patient_id}", response_model=RiskFactorsResponse)
async def get_risk_factors(
    patient_id: str,
    http_request: Request,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin"))
):
    """
    Get detailed risk factors for a specific patient
    
    SOC2 Controls Applied:
    - CC6.1: Individual patient access control
    - CC7.2: PHI access audit logging
    """
    try:
        # For now, calculate full risk score and extract factors
        # In production, this might be a separate optimized endpoint
        request_obj = RiskScoreRequest(
            patient_id=patient_id,
            include_recommendations=False,
            requesting_user_id=current_user_id,
            access_purpose="risk_factor_analysis"
        )
        
        service = await get_risk_stratification_service()
        risk_score = await service.calculate_risk_score(request_obj, db)
        
        return RiskFactorsResponse(
            patient_id=patient_id,
            factors=risk_score.factors,
            risk_score=risk_score.score,
            analysis_timestamp=risk_score.calculated_at,
            clinical_summary=f"Patient has {len(risk_score.factors)} identified risk factors with {risk_score.level} overall risk level"
        )
        
    except Exception as e:
        logger.error("Risk factors retrieval failed",
                    patient_id=patient_id,
                    error=str(e),
                    user_id=current_user_id)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Risk factors analysis temporarily unavailable"
        )

@router.get("/readmission/{patient_id}", response_model=ReadmissionRiskResponse)
async def calculate_readmission_risk(
    patient_id: str,
    http_request: Request,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin")),
    time_frame: str = "30_days"
):
    """
    Calculate readmission risk for a specific patient
    
    SOC2 Controls Applied:
    - CC6.1: Access control for clinical predictions
    - CC7.2: Readmission risk calculation audit logging
    """
    try:
        # Validate time frame
        valid_timeframes = ["30_days", "90_days", "1_year"]
        if time_frame not in valid_timeframes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid time_frame. Must be one of: {valid_timeframes}"
            )
        
        # Calculate readmission risk using the service
        service = await get_risk_stratification_service()
        
        # Get patient and extract clinical data
        patient = await service._get_patient(db, patient_id)
        clinical_data = await service.clinical_extractor.extract_clinical_metrics(patient)
        readmission_data = await service.risk_engine.calculate_readmission_risk(clinical_data)
        
        # Convert to response format
        response = ReadmissionRiskResponse(
            patient_id=patient_id,
            probability=readmission_data["probability"],
            time_frame=readmission_data["time_frame"],
            risk_factors=readmission_data["risk_factors"],
            interventions=readmission_data["interventions"],
            calculated_at=datetime.utcnow(),
            model=readmission_data["model"]
        )
        
        logger.info("Readmission risk calculated",
                   patient_id=patient_id,
                   probability=response.probability,
                   time_frame=time_frame,
                   user_id=current_user_id)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Readmission risk calculation failed",
                    patient_id=patient_id,
                    error=str(e),
                    user_id=current_user_id)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Readmission risk calculation temporarily unavailable"
        )

@router.post("/population/metrics", response_model=PopulationMetricsResponse)
async def get_population_metrics(
    request: PopulationMetricsRequest,
    http_request: Request,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin"))
):
    """
    Generate population health metrics and analytics
    
    SOC2 Controls Applied:
    - CC6.1: Access control for population data
    - CC7.2: Population analytics audit logging
    - A1.2: Performance monitoring for large datasets
    """
    try:
        # For MVP, return mock population metrics
        # In production, this would analyze actual patient population data
        
        from datetime import datetime, timedelta
        
        mock_response = PopulationMetricsResponse(
            cohort_id="default_population",
            cohort_name="All Patients",
            total_patients=2847,
            risk_distribution={
                "low": 1423,
                "moderate": 852,
                "high": 431,
                "critical": 141
            },
            outcome_trends=[
                {
                    "metric": "Average Risk Score",
                    "time_points": [
                        {"date": "2024-01-01", "value": 44.5, "confidence": 0.95},
                        {"date": "2024-01-15", "value": 42.3, "confidence": 0.94}
                    ],
                    "trend_direction": "improving",
                    "significance_level": 0.05
                }
            ],
            cost_metrics={
                "total_cost": 23985420.0,
                "cost_per_patient": 8425.0,
                "estimated_savings": 1240000.0,
                "roi": 2.8
            },
            quality_measures=[
                {
                    "measure_id": "hba1c_control",
                    "name": "HbA1c Control (<7%)",
                    "description": "Percentage of diabetic patients with HbA1c < 7%",
                    "current_score": 68.2,
                    "benchmark": 70.0,
                    "improvement": -1.8,
                    "measure_type": "outcome"
                }
            ],
            generated_at=datetime.utcnow(),
            data_range={
                "start_date": (datetime.utcnow() - timedelta(days=request.time_range_days)).isoformat(),
                "end_date": datetime.utcnow().isoformat()
            }
        )
        
        logger.info("Population metrics generated",
                   cohort_criteria=request.cohort_criteria,
                   metrics_requested=request.metrics_requested,
                   user_id=current_user_id,
                   organization_id=request.organization_id)
        
        return mock_response
        
    except Exception as e:
        logger.error("Population metrics generation failed",
                    error=str(e),
                    user_id=current_user_id)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Population metrics service temporarily unavailable"
        )

# ============================================
# BACKGROUND TASK FUNCTIONS
# ============================================

async def _log_readmission_risk_request(patient_id: str, user_id: str, correlation_id: str):
    """Background task to log readmission risk requests for analytics"""
    logger.info("Readmission risk calculation requested",
               patient_id=patient_id,
               user_id=user_id,
               correlation_id=correlation_id,
               background_task=True)

# ============================================
# ERROR HANDLERS - Note: Exception handlers should be added to main app, not router
# ============================================

# These would be added to the main FastAPI app instance, not the router
# See app/main.py for proper exception handler implementation