#!/usr/bin/env python3
"""
FHIR Interoperability Validation Router
REST API endpoints for FHIR system validation and testing.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database_unified import get_async_session
from app.core.security import get_current_user_with_permissions
from app.modules.fhir_validation.interop_validator import (
    FHIRInteroperabilityValidator, FHIRSystemConfig, FHIRSystemType,
    ValidationResult, ValidationStatus,
    get_epic_sandbox_config, get_cerner_sandbox_config, get_hapi_test_config
)
from app.modules.healthcare_records.schemas import FHIRValidationRequest, FHIRValidationResponse
from app.modules.healthcare_records.fhir_validator import get_fhir_validator

logger = structlog.get_logger()

# Pydantic models for requests/responses

class ValidationRequest(BaseModel):
    """FHIR system validation request"""
    system_type: FHIRSystemType
    name: str
    base_url: HttpUrl
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    smart_enabled: bool = False
    auth_url: Optional[HttpUrl] = None
    token_url: Optional[HttpUrl] = None
    version: str = "R4"
    timeout_seconds: int = 30
    custom_headers: Optional[Dict[str, str]] = None

class ValidationResponse(BaseModel):
    """FHIR system validation response"""
    system: Dict[str, Any]
    summary: Dict[str, Any]
    test_results: List[Dict[str, Any]]
    recommendations: List[str]
    timestamp: str

class SystemConfigResponse(BaseModel):
    """System configuration response"""
    name: str
    system_type: str
    base_url: str
    smart_enabled: bool
    description: str

# Router setup
router = APIRouter(prefix="/fhir/validation", tags=["FHIR Interoperability Validation"])

async def get_validator(
    db: AsyncSession = Depends(get_async_session)
) -> FHIRInteroperabilityValidator:
    """Dependency injection for FHIR validator"""
    return FHIRInteroperabilityValidator(db)

# Validation Endpoints

@router.post("/validate-resource", response_model=FHIRValidationResponse)
async def validate_fhir_resource(
    request: FHIRValidationRequest,
    current_user = Depends(get_current_user_with_permissions)
):
    """
    Validate FHIR resource for compliance and correctness.
    
    Performs comprehensive FHIR R4 resource validation including structure,
    terminology, business rules, and security validation.
    """
    
    try:
        # Extract resource type from the resource data
        resource_type = request.resource.get("resourceType")
        if not resource_type:
            raise HTTPException(
                status_code=422, 
                detail="Resource must contain 'resourceType' field"
            )
        
        logger.info("FHIR_VALIDATION - Resource validation request",
                   user_id=current_user.id,
                   resource_type=resource_type)
        
        # Get FHIR validator
        validator = get_fhir_validator()
        
        # Perform validation with separate resource_type and resource_data
        start_time = datetime.now()
        validation_result = await validator.validate_resource(
            resource_type=resource_type,
            resource_data=request.resource,
            profile_url=request.profile
        )
        end_time = datetime.now()
        
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Update validation duration in the response
        validation_result.validation_duration_ms = duration_ms
        if request.profile:
            validation_result.profile_validated = request.profile
        
        logger.info("FHIR_VALIDATION - Resource validation completed",
                   user_id=current_user.id,
                   resource_type=resource_type,
                   valid=validation_result.valid,
                   duration_ms=duration_ms)
        
        return validation_result
        
    except Exception as e:
        logger.error("FHIR_VALIDATION - Resource validation failed",
                    user_id=current_user.id,
                    resource_type=request.resource.get("resourceType", "Unknown"),
                    error=str(e))
        
        raise HTTPException(
            status_code=500,
            detail=f"FHIR resource validation failed: {str(e)}"
        )

@router.post("/validate-system", response_model=ValidationResponse)
async def validate_fhir_system(
    request: ValidationRequest,
    background_tasks: BackgroundTasks,
    validator: FHIRInteroperabilityValidator = Depends(get_validator),
    current_user = Depends(get_current_user_with_permissions)
):
    """
    Validate external FHIR system interoperability.
    
    Performs comprehensive validation including connectivity, capability statement,
    SMART on FHIR authentication, resource operations, and system-specific features.
    """
    
    try:
        logger.info("FHIR_VALIDATION - System validation request",
                   user_id=current_user.id,
                   system_name=request.name,
                   system_type=request.system_type.value,
                   base_url=str(request.base_url))
        
        # Convert request to system config
        config = FHIRSystemConfig(
            system_type=request.system_type,
            name=request.name,
            base_url=str(request.base_url),
            client_id=request.client_id,
            client_secret=request.client_secret,
            smart_enabled=request.smart_enabled,
            auth_url=str(request.auth_url) if request.auth_url else None,
            token_url=str(request.token_url) if request.token_url else None,
            version=request.version,
            timeout_seconds=request.timeout_seconds,
            custom_headers=request.custom_headers
        )
        
        # Perform validation
        async with validator:
            result = await validator.validate_system(config)
        
        logger.info("FHIR_VALIDATION - System validation completed",
                   user_id=current_user.id,
                   system_name=request.name,
                   overall_status=result.get("summary", {}).get("overall_status"),
                   success_rate=result.get("summary", {}).get("success_rate_percent"))
        
        return ValidationResponse(**result)
        
    except Exception as e:
        logger.error("FHIR_VALIDATION - System validation failed",
                    user_id=current_user.id,
                    system_name=request.name,
                    error=str(e))
        
        raise HTTPException(
            status_code=500,
            detail=f"FHIR system validation failed: {str(e)}"
        )

@router.get("/system-configs")
async def get_predefined_system_configs(
    current_user = Depends(get_current_user_with_permissions)
) -> List[SystemConfigResponse]:
    """
    Get predefined FHIR system configurations.
    
    Returns a list of pre-configured FHIR systems that can be used
    for validation testing, including sandbox environments.
    """
    
    try:
        configs = [
            SystemConfigResponse(
                name="Epic FHIR Sandbox",
                system_type="epic",
                base_url="https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4",
                smart_enabled=True,
                description="Epic's public FHIR R4 sandbox for testing"
            ),
            SystemConfigResponse(
                name="Cerner FHIR Sandbox",
                system_type="cerner",
                base_url="https://fhir-open.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d",
                smart_enabled=True,
                description="Cerner's public FHIR R4 sandbox for testing"
            ),
            SystemConfigResponse(
                name="HAPI FHIR Test Server",
                system_type="hapi",
                base_url="http://hapi.fhir.org/baseR4",
                smart_enabled=False,
                description="HAPI FHIR open test server"
            )
        ]
        
        logger.info("FHIR_VALIDATION - System configs requested",
                   user_id=current_user.id,
                   config_count=len(configs))
        
        return configs
        
    except Exception as e:
        logger.error("FHIR_VALIDATION - Failed to get system configs",
                    user_id=current_user.id,
                    error=str(e))
        
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve system configurations"
        )

@router.post("/validate-epic-sandbox")
async def validate_epic_sandbox(
    background_tasks: BackgroundTasks,
    validator: FHIRInteroperabilityValidator = Depends(get_validator),
    current_user = Depends(get_current_user_with_permissions)
):
    """
    Validate Epic FHIR sandbox.
    
    Quick validation of Epic's public FHIR sandbox using predefined configuration.
    """
    
    try:
        config = get_epic_sandbox_config()
        
        async with validator:
            result = await validator.validate_system(config)
        
        logger.info("FHIR_VALIDATION - Epic sandbox validation completed",
                   user_id=current_user.id,
                   overall_status=result.get("summary", {}).get("overall_status"))
        
        return result
        
    except Exception as e:
        logger.error("FHIR_VALIDATION - Epic sandbox validation failed",
                    user_id=current_user.id,
                    error=str(e))
        
        raise HTTPException(
            status_code=500,
            detail=f"Epic sandbox validation failed: {str(e)}"
        )

@router.post("/validate-cerner-sandbox")
async def validate_cerner_sandbox(
    background_tasks: BackgroundTasks,
    validator: FHIRInteroperabilityValidator = Depends(get_validator),
    current_user = Depends(get_current_user_with_permissions)
):
    """
    Validate Cerner FHIR sandbox.
    
    Quick validation of Cerner's public FHIR sandbox using predefined configuration.
    """
    
    try:
        config = get_cerner_sandbox_config()
        
        async with validator:
            result = await validator.validate_system(config)
        
        logger.info("FHIR_VALIDATION - Cerner sandbox validation completed",
                   user_id=current_user.id,
                   overall_status=result.get("summary", {}).get("overall_status"))
        
        return result
        
    except Exception as e:
        logger.error("FHIR_VALIDATION - Cerner sandbox validation failed",
                    user_id=current_user.id,
                    error=str(e))
        
        raise HTTPException(
            status_code=500,
            detail=f"Cerner sandbox validation failed: {str(e)}"
        )

@router.post("/validate-hapi-test")
async def validate_hapi_test_server(
    background_tasks: BackgroundTasks,
    validator: FHIRInteroperabilityValidator = Depends(get_validator),
    current_user = Depends(get_current_user_with_permissions)
):
    """
    Validate HAPI FHIR test server.
    
    Quick validation of HAPI FHIR public test server using predefined configuration.
    """
    
    try:
        config = get_hapi_test_config()
        
        async with validator:
            result = await validator.validate_system(config)
        
        logger.info("FHIR_VALIDATION - HAPI test server validation completed",
                   user_id=current_user.id,
                   overall_status=result.get("summary", {}).get("overall_status"))
        
        return result
        
    except Exception as e:
        logger.error("FHIR_VALIDATION - HAPI test server validation failed",
                    user_id=current_user.id,
                    error=str(e))
        
        raise HTTPException(
            status_code=500,
            detail=f"HAPI test server validation failed: {str(e)}"
        )

@router.get("/validation-status")
async def get_validation_status(
    current_user = Depends(get_current_user_with_permissions)
):
    """
    Get FHIR validation service status.
    
    Returns current status and capabilities of the FHIR validation service.
    """
    
    try:
        status = {
            "service_status": "active",
            "supported_systems": [system_type.value for system_type in FHIRSystemType],
            "validation_capabilities": [
                "connectivity_testing",
                "capability_statement_validation", 
                "smart_on_fhir_authentication",
                "resource_operations_testing",
                "search_functionality_testing",
                "resource_validation",
                "system_specific_features"
            ],
            "predefined_configs": 3,
            "description": "FHIR R4 interoperability validation service"
        }
        
        logger.info("FHIR_VALIDATION - Status requested",
                   user_id=current_user.id)
        
        return status
        
    except Exception as e:
        logger.error("FHIR_VALIDATION - Failed to get status",
                    user_id=current_user.id,
                    error=str(e))
        
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve validation status"
        )

# Export router
__all__ = ["router"]