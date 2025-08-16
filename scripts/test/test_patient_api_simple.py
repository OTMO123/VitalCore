#!/usr/bin/env python3
"""
Simple Patient API test to verify core functionality works.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from datetime import datetime


@pytest.mark.asyncio
async def test_patient_create_schema():
    """Test patient creation schema validation."""
    from app.modules.healthcare_records.schemas import PatientCreate
    
    # Valid patient data
    patient_data = {
        "resourceType": "Patient",
        "identifier": [
            {
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "MR",
                            "display": "Medical Record Number"
                        }
                    ]
                },
                "system": "http://example.org/patient-ids",
                "value": "123456",
                "use": "usual"
            }
        ],
        "name": [
            {
                "family": "Doe",
                "given": ["John", "Q"],
                "use": "official"
            }
        ],
        "gender": "male",
        "birthDate": "1990-01-01",
        "telecom": [
            {
                "system": "email",
                "value": "john.doe@example.com",
                "use": "home"
            }
        ],
        "organization_id": str(uuid.uuid4())
    }
    
    # Should create successfully
    patient = PatientCreate(**patient_data)
    
    # Check the fields that exist
    assert patient.name[0].family == "Doe"
    assert patient.name[0].given == ["John", "Q"]
    assert patient.gender == "male"
    assert patient.organization_id is not None
    assert patient.active is True


@pytest.mark.asyncio
async def test_patient_response_schema():
    """Test patient response schema."""
    from app.modules.healthcare_records.schemas import PatientResponse
    
    # Mock response data  
    response_data = {
        "id": str(uuid.uuid4()),
        "identifier": [
            {
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "MR",
                            "display": "Medical Record Number"
                        }
                    ]
                },
                "system": "http://example.org/patient-ids",
                "value": "123456",
                "use": "usual"
            }
        ],
        "active": True,
        "name": [
            {
                "family": "Doe",
                "given": ["John"],
                "use": "official"
            }
        ],
        "gender": "male",
        "birthDate": "1990-01-01",
        "consent_status": "pending",
        "consent_types": [],
        "organization_id": str(uuid.uuid4()),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    # Should create successfully
    response = PatientResponse(**response_data)
    assert response.name[0].family == "Doe"
    assert response.active is True


@pytest.mark.asyncio
async def test_fhir_validation_request():
    """Test FHIR validation request schema."""
    from app.modules.healthcare_records.schemas import FHIRValidationRequest
    
    validation_data = {
        "resource_type": "Patient",
        "resource_data": {
            "resourceType": "Patient",
            "name": [{"family": "Doe", "given": ["John"]}],
            "gender": "male"
        }
    }
    
    request = FHIRValidationRequest(**validation_data)
    assert request.resource_type == "Patient"
    assert request.resource_data["resourceType"] == "Patient"


@pytest.mark.asyncio 
async def test_healthcare_service_initialization():
    """Test healthcare service can be initialized with mocked dependencies."""
    from app.modules.healthcare_records.service import HealthcareRecordsService
    
    # Mock dependencies
    mock_session = AsyncMock()
    mock_event_bus = AsyncMock()
    mock_encryption = AsyncMock()
    
    # Should initialize without errors
    service = HealthcareRecordsService(
        session=mock_session,
        event_bus=mock_event_bus,
        encryption=mock_encryption
    )
    
    assert service.session == mock_session
    assert service.event_bus == mock_event_bus


@pytest.mark.asyncio
async def test_access_context():
    """Test access context creation."""
    from app.modules.healthcare_records.service import AccessContext
    
    context = AccessContext(
        user_id="user123",
        purpose="treatment",
        role="physician",
        ip_address="192.168.1.1",
        session_id="session123"
    )
    
    assert context.user_id == "user123"
    assert context.purpose == "treatment"
    assert context.role == "physician"


@pytest.mark.asyncio
async def test_patient_api_endpoint_structure():
    """Test that patient API endpoints are properly structured."""
    from app.modules.healthcare_records.router import router
    
    # Check that router has routes
    assert len(router.routes) > 0
    
    # Find patient routes
    patient_routes = [route for route in router.routes if hasattr(route, 'path') and 'patients' in route.path]
    assert len(patient_routes) > 0
    
    print(f"✓ Found {len(patient_routes)} patient API endpoints")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])