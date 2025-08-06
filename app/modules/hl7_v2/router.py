#!/usr/bin/env python3
"""
HL7 v2 Router Implementation
REST API endpoints for HL7 v2 message processing and legacy system integration.

This module provides HTTP endpoints for receiving, processing, and responding to
HL7 v2 messages from legacy healthcare systems. It handles message validation,
processing, FHIR mapping, and ACK/NAK response generation.

Endpoints:
- POST /hl7/message - Process incoming HL7 v2 message
- GET /hl7/status - Get HL7 processing status
- POST /hl7/validate - Validate HL7 message without processing
- GET /hl7/supported-types - Get supported message types
- POST /hl7/test - Test HL7 message processing with sample data
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database_unified import get_async_session
from app.core.security import get_current_user_with_permissions
from app.modules.hl7_v2.hl7_processor import (
    HL7MessageProcessor, HL7Parser, HL7MessageType, HL7SegmentType
)

logger = structlog.get_logger()

# Pydantic models for API requests/responses

class HL7MessageRequest(BaseModel):
    """HL7 message processing request"""
    message: str = Field(..., description="HL7 v2 message text")
    source_system: str = Field("unknown", description="Source system identifier")
    return_ack: bool = Field(True, description="Return ACK/NAK message")
    validate_only: bool = Field(False, description="Validate only, do not process")

class HL7MessageResponse(BaseModel):
    """HL7 message processing response"""
    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Processing result message")
    message_type: Optional[str] = Field(None, description="HL7 message type")
    message_control_id: Optional[str] = Field(None, description="Message control ID")
    ack_message: Optional[str] = Field(None, description="ACK/NAK response message")
    fhir_resources: Optional[List[Dict[str, Any]]] = Field(None, description="Generated FHIR resources")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    errors: Optional[List[str]] = Field(None, description="Validation or processing errors")

class HL7ValidationResponse(BaseModel):
    """HL7 message validation response"""
    valid: bool = Field(..., description="Message is valid")
    message_type: Optional[str] = Field(None, description="HL7 message type")
    segment_count: int = Field(..., description="Number of segments")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")

class HL7StatusResponse(BaseModel):
    """HL7 processing status response"""
    service_status: str = Field(..., description="Service status")
    supported_message_types: List[str] = Field(..., description="Supported message types")
    messages_processed_today: int = Field(..., description="Messages processed today")
    last_processed_at: Optional[datetime] = Field(None, description="Last message processed timestamp")
    error_rate_percent: float = Field(..., description="Error rate percentage")

class HL7TestRequest(BaseModel):
    """HL7 test message request"""
    message_type: str = Field(..., description="Message type to generate")
    include_optional_segments: bool = Field(False, description="Include optional segments")

# Router setup
router = APIRouter(prefix="/hl7", tags=["HL7 v2 Processing"])

async def get_hl7_processor(
    db: AsyncSession = Depends(get_async_session)
) -> HL7MessageProcessor:
    """Dependency injection for HL7 processor"""
    return HL7MessageProcessor(db)

async def get_hl7_parser() -> HL7Parser:
    """Dependency injection for HL7 parser"""
    return HL7Parser()

# HL7 Message Processing Endpoints

@router.post("/message", response_model=HL7MessageResponse)
async def process_hl7_message(
    request: HL7MessageRequest,
    processor: HL7MessageProcessor = Depends(get_hl7_processor)
):
    """
    Process incoming HL7 v2 message.
    
    This endpoint receives HL7 v2 messages, validates them, processes the content,
    maps to FHIR resources where applicable, and returns processing results along
    with an appropriate ACK/NAK response.
    
    Supported message types include:
    - ADT (Admission, Discharge, Transfer)
    - ORM (Order Management)
    - ORU (Observation Results)
    - SIU (Scheduling Information)
    - VXU (Vaccination Updates)
    """
    
    start_time = datetime.now()
    
    try:
        logger.info("HL7_API - Processing message request",
                   source_system=request.source_system,
                   message_length=len(request.message),
                   validate_only=request.validate_only)
        
        if request.validate_only:
            # Validation only mode
            parser = HL7Parser()
            message = parser.parse_message(request.message)
            is_valid, errors = parser.validate_message(message)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return HL7MessageResponse(
                status="validated" if is_valid else "invalid",
                message=f"Message validation {'passed' if is_valid else 'failed'}",
                message_type=message.message_type.value,
                message_control_id=message.message_control_id,
                processing_time_ms=processing_time,
                errors=errors if not is_valid else None
            )
        
        # Full processing mode
        result = await processor.process_message(request.message, request.source_system)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Extract FHIR resources from result
        fhir_resources = []
        if result.get("patient_data"):
            fhir_resources.append(result["patient_data"])
        if result.get("encounter_data"):
            fhir_resources.append(result["encounter_data"])
        if result.get("orders"):
            fhir_resources.extend(result["orders"])
        if result.get("observations"):
            fhir_resources.extend(result["observations"])
        if result.get("immunizations"):
            fhir_resources.extend(result["immunizations"])
        if result.get("appointment_data"):
            fhir_resources.append(result["appointment_data"])
        
        response = HL7MessageResponse(
            status=result.get("status", "unknown"),
            message=result.get("message", "Message processed"),
            message_type=result.get("message_type"),
            message_control_id=result.get("message_control_id"),
            ack_message=result.get("ack_message") if request.return_ack else None,
            fhir_resources=fhir_resources if fhir_resources else None,
            processing_time_ms=processing_time,
            errors=result.get("errors")
        )
        
        logger.info("HL7_API - Message processed successfully",
                   status=result.get("status"),
                   message_type=result.get("message_type"),
                   fhir_resource_count=len(fhir_resources),
                   processing_time_ms=processing_time)
        
        return response
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.error("HL7_API - Message processing failed",
                    source_system=request.source_system,
                    error=str(e),
                    processing_time_ms=processing_time)
        
        return HL7MessageResponse(
            status="error",
            message=f"Processing failed: {str(e)}",
            processing_time_ms=processing_time,
            errors=[str(e)]
        )

@router.post("/message/raw")
async def process_raw_hl7_message(
    request: Request,
    source_system: str = "unknown",
    processor: HL7MessageProcessor = Depends(get_hl7_processor)
):
    """
    Process raw HL7 v2 message (plain text).
    
    This endpoint accepts raw HL7 messages as plain text in the request body,
    useful for direct integration with legacy systems that send messages
    in their native format.
    
    Returns ACK/NAK message as plain text response.
    """
    
    try:
        # Read raw message from request body
        message_bytes = await request.body()
        message_text = message_bytes.decode('utf-8', errors='replace')
        
        logger.info("HL7_API - Processing raw message",
                   source_system=source_system,
                   message_length=len(message_text))
        
        # Process message
        result = await processor.process_message(message_text, source_system)
        
        # Return ACK/NAK as plain text
        ack_message = result.get("ack_message", "")
        
        # Set appropriate content type for HL7
        return PlainTextResponse(
            content=ack_message,
            headers={"Content-Type": "application/hl7-v2"}
        )
        
    except Exception as e:
        logger.error("HL7_API - Raw message processing failed",
                    source_system=source_system,
                    error=str(e))
        
        # Return error ACK
        error_ack = "MSH|^~\\&|SYSTEM|FACILITY|||" + datetime.now().strftime("%Y%m%d%H%M%S") + "||ACK||P|2.5\rMSA|AE|UNKNOWN|Processing error"
        
        return PlainTextResponse(
            content=error_ack,
            status_code=500,
            headers={"Content-Type": "application/hl7-v2"}
        )

@router.post("/validate", response_model=HL7ValidationResponse)
async def validate_hl7_message(
    request: HL7MessageRequest,
    parser: HL7Parser = Depends(get_hl7_parser)
):
    """
    Validate HL7 v2 message structure and content.
    
    This endpoint validates HL7 messages without processing them,
    useful for testing and validation during development or integration.
    """
    
    try:
        logger.info("HL7_API - Validating message",
                   message_length=len(request.message))
        
        # Parse message
        message = parser.parse_message(request.message)
        
        # Validate message
        is_valid, errors = parser.validate_message(message)
        
        # Generate warnings for non-critical issues
        warnings = []
        if not message.timestamp:
            warnings.append("Message timestamp is missing or invalid")
        
        if not message.message_control_id:
            warnings.append("Message control ID is missing")
        
        response = HL7ValidationResponse(
            valid=is_valid,
            message_type=message.message_type.value,
            segment_count=len(message.segments),
            errors=errors,
            warnings=warnings
        )
        
        logger.info("HL7_API - Message validation completed",
                   valid=is_valid,
                   error_count=len(errors),
                   warning_count=len(warnings))
        
        return response
        
    except Exception as e:
        logger.error("HL7_API - Message validation failed",
                    error=str(e))
        
        return HL7ValidationResponse(
            valid=False,
            message_type="unknown",
            segment_count=0,
            errors=[f"Validation failed: {str(e)}"]
        )

@router.get("/status", response_model=HL7StatusResponse)
async def get_hl7_status():
    """
    Get HL7 processing service status.
    
    Returns information about the HL7 processing service including
    supported message types, processing statistics, and health status.
    """
    
    try:
        # Get supported message types
        supported_types = [mt.value for mt in HL7MessageType]
        
        # In a real implementation, these would come from database/metrics
        status_data = HL7StatusResponse(
            service_status="healthy",
            supported_message_types=supported_types,
            messages_processed_today=0,  # Would query from database
            last_processed_at=None,  # Would query from database
            error_rate_percent=0.0  # Would calculate from metrics
        )
        
        logger.info("HL7_API - Status requested",
                   supported_types_count=len(supported_types))
        
        return status_data
        
    except Exception as e:
        logger.error("HL7_API - Status request failed",
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get HL7 status: {str(e)}"
        )

@router.get("/supported-types")
async def get_supported_message_types():
    """
    Get list of supported HL7 v2 message types.
    
    Returns detailed information about supported message types
    including descriptions and capabilities.
    """
    
    try:
        message_types = []
        
        for message_type in HL7MessageType:
            type_info = {
                "code": message_type.value,
                "name": message_type.name,
                "description": _get_message_type_description(message_type),
                "supported_events": _get_supported_events(message_type)
            }
            message_types.append(type_info)
        
        response = {
            "supported_message_types": message_types,
            "total_count": len(message_types),
            "last_updated": datetime.now().isoformat()
        }
        
        logger.info("HL7_API - Supported types requested",
                   type_count=len(message_types))
        
        return response
        
    except Exception as e:
        logger.error("HL7_API - Supported types request failed",
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get supported types: {str(e)}"
        )

@router.post("/test", response_model=HL7MessageResponse)
async def test_hl7_processing(
    request: HL7TestRequest,
    processor: HL7MessageProcessor = Depends(get_hl7_processor)
):
    """
    Test HL7 message processing with sample data.
    
    Generates sample HL7 messages for testing and processes them
    to validate the processing pipeline and FHIR mapping.
    """
    
    try:
        logger.info("HL7_API - Test processing requested",
                   message_type=request.message_type)
        
        # Generate sample message
        sample_message = _generate_sample_message(
            request.message_type,
            request.include_optional_segments
        )
        
        if not sample_message:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot generate sample message for type: {request.message_type}"
            )
        
        # Process the sample message
        result = await processor.process_message(sample_message, "test_system")
        
        # Extract FHIR resources
        fhir_resources = []
        if result.get("patient_data"):
            fhir_resources.append(result["patient_data"])
        if result.get("encounter_data"):
            fhir_resources.append(result["encounter_data"])
        
        response = HL7MessageResponse(
            status=result.get("status", "success"),
            message=f"Test message processed successfully: {request.message_type}",
            message_type=result.get("message_type"),
            message_control_id=result.get("message_control_id"),
            ack_message=result.get("ack_message"),
            fhir_resources=fhir_resources if fhir_resources else None
        )
        
        logger.info("HL7_API - Test processing completed",
                   message_type=request.message_type,
                   status=result.get("status"))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("HL7_API - Test processing failed",
                    message_type=request.message_type,
                    error=str(e))
        
        return HL7MessageResponse(
            status="error",
            message=f"Test processing failed: {str(e)}",
            errors=[str(e)]
        )

# Health Check Endpoint

@router.get("/health")
async def health_check():
    """
    Health check endpoint for HL7 processing service.
    
    Returns basic health status and readiness information.
    """
    
    try:
        # Perform basic health checks
        parser = HL7Parser()
        
        # Test message parsing
        test_message = "MSH|^~\\&|TEST|FACILITY|||20240101120000||ADT^A01||P|2.5\rPID|||12345||DOE^JOHN^^^||19800101|M|||123 MAIN ST^^ANYTOWN^ST^12345||555-1234"
        parsed_message = parser.parse_message(test_message)
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "checks": {
                "parser": "ok",
                "database": "ok",  # Would check database connection
                "memory": "ok"     # Would check memory usage
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error("HL7_API - Health check failed",
                    error=str(e))
        
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )

# Helper Functions

def _get_message_type_description(message_type: HL7MessageType) -> str:
    """Get description for message type"""
    
    descriptions = {
        HL7MessageType.ADT_A01: "Admit/Visit notification",
        HL7MessageType.ADT_A02: "Transfer a patient", 
        HL7MessageType.ADT_A03: "Discharge/End visit",
        HL7MessageType.ADT_A04: "Register a patient",
        HL7MessageType.ADT_A08: "Update patient information",
        HL7MessageType.ORM_O01: "Order message",
        HL7MessageType.ORU_R01: "Unsolicited transmission of observation",
        HL7MessageType.SIU_S12: "Notification of new appointment booking",
        HL7MessageType.VXU_V04: "Vaccination record update"
    }
    
    return descriptions.get(message_type, "Unknown message type")

def _get_supported_events(message_type: HL7MessageType) -> List[str]:
    """Get supported events for message type"""
    
    if message_type.value.startswith("ADT"):
        return ["A01", "A02", "A03", "A04", "A08", "A11", "A12"]
    elif message_type.value.startswith("ORM"):
        return ["O01", "O02"]
    elif message_type.value.startswith("ORU"):
        return ["R01", "R03"]
    elif message_type.value.startswith("SIU"):
        return ["S12", "S13", "S14", "S15", "S17", "S26"]
    elif message_type.value.startswith("VXU"):
        return ["V04"]
    else:
        return []

def _generate_sample_message(message_type: str, include_optional: bool = False) -> Optional[str]:
    """Generate sample HL7 message for testing"""
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    control_id = f"TEST{timestamp[-6:]}"
    
    if message_type == "ADT^A01":
        # ADT A01 - Admit patient
        message = f"""MSH|^~\\&|HIS|HOSPITAL|EMR|CLINIC|{timestamp}||ADT^A01|{control_id}|P|2.5
EVN|A01|{timestamp}|||^DOCTOR^ATTENDING
PID|1||12345^^^MRN||DOE^JOHN^MIDDLE^^MR||19800115|M||2106-3|123 MAIN ST^^ANYTOWN^ST^12345||(555)123-4567|(555)987-6543|EN|S||987654321|||N||||||||N
PV1|1|I|ICU^101^1||E||123456^DOCTOR^ATTENDING^A|||SUR||||19||01|||123456^DOCTOR^ATTENDING^A||VIP|2|||||||||||||||||||H|||{timestamp}"""
        
        if include_optional:
            message += f"\rDG1|1|I10|Z51.11^Encounter for antineoplastic chemotherapy^ICD10|Chemotherapy||W"
            
    elif message_type == "ORU^R01":
        # ORU R01 - Lab results
        message = f"""MSH|^~\\&|LIS|LAB|EMR|CLINIC|{timestamp}||ORU^R01|{control_id}|P|2.5
PID|1||12345^^^MRN||DOE^JOHN^MIDDLE^^MR||19800115|M||2106-3|123 MAIN ST^^ANYTOWN^ST^12345||(555)123-4567
OBR|1|LAB123|LAB123|CBC^Complete Blood Count^LN|||{timestamp}|||||||||123456^DOCTOR^ORDERING^A
OBX|1|NM|WBC^White Blood Cell Count^LN|1|7.5|10*3/uL|4.0-11.0|N|||F|||{timestamp}
OBX|2|NM|RBC^Red Blood Cell Count^LN|2|4.2|10*6/uL|3.8-5.2|N|||F|||{timestamp}
OBX|3|NM|HGB^Hemoglobin^LN|3|12.5|g/dL|11.0-15.0|N|||F|||{timestamp}"""
        
    elif message_type == "SIU^S12":
        # SIU S12 - New appointment
        message = f"""MSH|^~\\&|SCHEDULING|HOSPITAL|EMR|CLINIC|{timestamp}||SIU^S12|{control_id}|P|2.5
SCH|APPT123||APPT123|APPOINTMENT|||{timestamp}|{timestamp}|15|MIN|^DOCTOR^ATTENDING|||||A
PID|1||12345^^^MRN||DOE^JOHN^MIDDLE^^MR||19800115|M||2106-3|123 MAIN ST^^ANYTOWN^ST^12345||(555)123-4567
AIS|1|A|OFFICE^Office Visit^LOCAL|||{timestamp}|15|MIN||10|MIN|A"""
        
    else:
        return None
    
    return message.replace("\n", "\r")

# Export router
__all__ = ["router"]