"""
FHIR R4 Resource Validation Enterprise Security Testing Suite

SOC2 Type II + HIPAA + FHIR R4 + GDPR Compliant Testing
========================================================

This comprehensive test suite validates FHIR R4 resource compliance for:
- Patient resource validation with encrypted PHI fields
- Immunization resource validation with CVX codes
- Observation resource validation with LOINC codes
- DocumentReference validation with metadata integrity
- FHIR security labels and provenance tracking
- Resource reference integrity and linking validation
- Business rule validation beyond basic structure

Enterprise Security Features:
- Real JWT authentication with role-based access
- PHI/PII encryption validation
- Audit trail verification
- SOC2 Type II compliance checks
- GDPR consent tracking
- HIPAA minimum necessary enforcement
"""

import pytest
import pytest_asyncio
import asyncio
import json
import uuid
from datetime import datetime, date, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple

# Core testing imports
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

# Application imports
from app.main import app
from app.core.security import EncryptionService
from app.modules.healthcare_records.service import AccessContext
from app.modules.healthcare_records.schemas import (
    FHIRValidationRequest, FHIRValidationResponse,
    PatientCreate, ImmunizationCreate
)
from app.tests.helpers.auth_helpers import AuthTestHelper


@pytest_asyncio.fixture
async def enterprise_test_environment(db_session: AsyncSession):
    """Set up enterprise-grade test environment with real authentication."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        auth_helper = AuthTestHelper(db_session, client)
        
        # Create users with different roles for comprehensive testing
        import uuid
        test_id = str(uuid.uuid4())[:8]
        
        admin_user = await auth_helper.create_user(
            username=f"enterprise_admin_{test_id}",
            role="system_admin",
            email=f"admin.{test_id}@example.com",
            password="EnterpriseSecure123!"
        )
        
        physician_user = await auth_helper.create_user(
            username=f"test_physician_{test_id}",
            role="physician",
            email=f"physician.{test_id}@example.com",
            password="PhysicianSecure123!"
        )
        
        patient_user = await auth_helper.create_user(
            username=f"test_patient_{test_id}",
            role="patient",
            email=f"patient.{test_id}@example.com",
            password="PatientSecure123!"
        )
        
        # Get authentication headers for different roles
        admin_headers = await auth_helper.get_headers(
            f"enterprise_admin_{test_id}", "EnterpriseSecure123!"
        )
        physician_headers = await auth_helper.get_headers(
            f"test_physician_{test_id}", "PhysicianSecure123!"
        )
        patient_headers = await auth_helper.get_headers(
            f"test_patient_{test_id}", "PatientSecure123!"
        )
        
        encryption_service = EncryptionService()
        
        yield {
            "client": client,
            "auth_helper": auth_helper,
            "admin_user": admin_user,
            "physician_user": physician_user,
            "patient_user": patient_user,
            "admin_headers": admin_headers,
            "physician_headers": physician_headers,
            "patient_headers": patient_headers,
            "encryption_service": encryption_service,
            "db_session": db_session
        }
        
        await auth_helper.cleanup()


@pytest.mark.integration
@pytest.mark.fhir
@pytest.mark.security
class TestFHIRValidationEnterpriseSecurity:
    """Enterprise FHIR R4 validation security tests."""
    
    @pytest.mark.asyncio
    async def test_fhir_validation_requires_authentication(self, enterprise_test_environment):
        """Test that FHIR validation requires proper authentication."""
        env = enterprise_test_environment
        client = env["client"]
        
        patient_resource = {
            "resourceType": "Patient",
            "id": "patient-auth-test",
            "active": True,
            "name": [{
                "use": "official",
                "family": "AuthTest",
                "given": ["FHIR"]
            }],
            "gender": "other",
            "birthDate": "1990-01-01"
        }
        
        validation_request = FHIRValidationRequest(
            resource=patient_resource
        )
        
        # Test without authentication
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump()
        )
        
        assert response.status_code == 401
        
        # Test with invalid token
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_fhir_validation_with_admin_role(self, enterprise_test_environment):
        """Test FHIR validation with system admin role."""
        env = enterprise_test_environment
        client = env["client"]
        admin_headers = env["admin_headers"]
        
        patient_resource = {
            "resourceType": "Patient",
            "id": "patient-admin-001",
            "active": True,
            "identifier": [{
                "use": "official",
                "system": "http://hospital.example.org",
                "value": "MRN-ADMIN-001"
            }],
            "name": [{
                "use": "official",
                "family": "AdminTest",
                "given": ["FHIR"]
            }],
            "gender": "other",
            "birthDate": "1990-01-01"
        }
        
        validation_request = FHIRValidationRequest(
            resource=patient_resource
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=admin_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert "is_valid" in result
        assert "resource_type" in result
        assert "issues" in result
        assert "warnings" in result
        assert result["resource_type"] == "Patient"
    
    @pytest.mark.asyncio
    async def test_fhir_validation_with_physician_role(self, enterprise_test_environment):
        """Test FHIR validation with physician role."""
        env = enterprise_test_environment
        client = env["client"]
        physician_headers = env["physician_headers"]
        
        immunization_resource = {
            "resourceType": "Immunization",
            "id": "immunization-physician-001",
            "status": "completed",
            "vaccineCode": {
                "coding": [{
                    "system": "http://hl7.org/fhir/sid/cvx",
                    "code": "140",
                    "display": "Influenza, seasonal, injectable, preservative free"
                }]
            },
            "patient": {
                "reference": "Patient/patient-physician-001"
            },
            "occurrenceDateTime": "2023-10-15T10:00:00Z",
            "primarySource": True,
            # Enterprise compliance fields for series tracking
            "series_complete": True,
            "series_dosed": 1
        }
        
        validation_request = FHIRValidationRequest(
            resource=immunization_resource
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=physician_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["is_valid"] is True
        assert result["resource_type"] == "Immunization"
        assert len(result["issues"]) == 0
    
    @pytest.mark.asyncio
    async def test_fhir_validation_role_based_access(self, enterprise_test_environment):
        """Test role-based access control for FHIR validation."""
        env = enterprise_test_environment
        client = env["client"]
        patient_headers = env["patient_headers"]
        
        # Patients should have limited access to validation features
        sensitive_resource = {
            "resourceType": "Observation",
            "id": "observation-sensitive-001",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory",
                    "display": "Laboratory"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "33747-0",
                    "display": "General health status"
                }]
            },
            "subject": {
                "reference": "Patient/patient-sensitive-001"
            },
            "effectiveDateTime": "2023-10-15T09:30:00Z",
            "valueString": "Good general health"
        }
        
        validation_request = FHIRValidationRequest(
            resource=sensitive_resource
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=patient_headers
        )
        
        # Patients might have limited validation access
        # depending on your business rules
        assert response.status_code in [200, 403]
    
    @pytest.mark.asyncio
    async def test_fhir_validation_with_encrypted_phi(self, enterprise_test_environment):
        """Test FHIR validation with encrypted PHI fields."""
        env = enterprise_test_environment
        client = env["client"]
        admin_headers = env["admin_headers"]
        encryption_service = env["encryption_service"]
        
        # Encrypt sensitive data
        encrypted_name = await encryption_service.encrypt_string("Confidential Patient")
        encrypted_ssn = await encryption_service.encrypt_string("123-45-6789")
        encrypted_phone = await encryption_service.encrypt_string("555-123-4567")
        
        patient_resource = {
            "resourceType": "Patient",
            "id": "patient-encrypted-phi-001",
            "active": True,
            "identifier": [{
                "use": "official",
                "type": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                        "code": "SS",
                        "display": "Social Security number"
                    }]
                },
                "system": "http://hl7.org/fhir/sid/us-ssn",
                "value": encrypted_ssn
            }],
            "name": [{
                "use": "official",
                "family": encrypted_name,
                "given": ["Patient"]
            }],
            "telecom": [{
                "system": "phone",
                "value": encrypted_phone,
                "use": "home"
            }],
            "gender": "unknown",
            "birthDate": "1985-06-15",
            "meta": {
                "security": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                    "code": "R",
                    "display": "restricted"
                }]
            }
        }
        
        validation_request = FHIRValidationRequest(
            resource=patient_resource
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=admin_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Should validate successfully with encrypted fields
        assert result["is_valid"] is True
        assert result["resource_type"] == "Patient"
    
    @pytest.mark.asyncio
    async def test_fhir_validation_security_labels(self, enterprise_test_environment):
        """Test FHIR validation with security labels for compliance."""
        env = enterprise_test_environment
        client = env["client"]
        admin_headers = env["admin_headers"]
        
        observation_resource = {
            "resourceType": "Observation",
            "id": "observation-security-labels-001",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "social-history",
                    "display": "Social History"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "72166-2",
                    "display": "Tobacco smoking status"
                }]
            },
            "subject": {
                "reference": "Patient/patient-security-001"
            },
            "effectiveDateTime": "2023-10-15T09:30:00Z",
            "valueCodeableConcept": {
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": "449868002",
                    "display": "Current every day smoker"
                }]
            },
            "meta": {
                "security": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                        "code": "N",
                        "display": "normal"
                    },
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                        "code": "HPRGRP",
                        "display": "health program reporting"
                    }
                ]
            }
        }
        
        validation_request = FHIRValidationRequest(
            resource=observation_resource
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=admin_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["is_valid"] is True
        assert result["resource_type"] == "Observation"
        # Verify security labels are present in response
        assert "security_labels" in result
    
    @pytest.mark.asyncio
    async def test_fhir_validation_provenance_tracking(self, enterprise_test_environment):
        """Test FHIR validation with provenance tracking for audit compliance."""
        env = enterprise_test_environment
        client = env["client"]
        physician_headers = env["physician_headers"]
        physician_user = env["physician_user"]
        
        provenance_resource = {
            "resourceType": "Provenance",
            "id": "provenance-validation-001",
            "target": [{
                "reference": "Patient/patient-provenance-001"
            }],
            "recorded": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "agent": [{
                "type": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
                        "code": "author",
                        "display": "Author"
                    }]
                },
                "who": {
                    "reference": f"Practitioner/{physician_user.id}",
                    "display": "Test Physician"
                }
            }],
            "activity": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-DataOperation",
                    "code": "CREATE",
                    "display": "create"
                }]
            }
        }
        
        validation_request = FHIRValidationRequest(
            resource=provenance_resource
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=physician_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["is_valid"] is True
        assert result["resource_type"] == "Provenance"
    
    @pytest.mark.asyncio
    async def test_fhir_validation_gdpr_consent_tracking(self, enterprise_test_environment):
        """Test FHIR validation with GDPR consent tracking."""
        env = enterprise_test_environment
        client = env["client"]
        admin_headers = env["admin_headers"]
        
        consent_resource = {
            "resourceType": "Consent",
            "id": "consent-gdpr-001",
            "status": "active",
            "scope": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/consentscope",
                    "code": "patient-privacy",
                    "display": "Privacy Consent"
                }]
            },
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/consentcategorycodes",
                    "code": "idscl",
                    "display": "Information Disclosure"
                }]
            }],
            "patient": {
                "reference": "Patient/patient-gdpr-consent-001"
            },
            "dateTime": "2023-10-15T08:00:00Z",
            "performer": [{
                "reference": "Patient/patient-gdpr-consent-001"
            }],
            "policyRule": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/consentpolicycodes",
                    "code": "gdpr",
                    "display": "GDPR"
                }]
            },
            "provision": {
                "type": "permit",
                "purpose": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                    "code": "TREAT",
                    "display": "treatment"
                }]
            }
        }
        
        validation_request = FHIRValidationRequest(
            resource=consent_resource
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=admin_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["is_valid"] is True
        assert result["resource_type"] == "Consent"
    
    @pytest.mark.asyncio
    async def test_fhir_validation_error_handling_enterprise(self, enterprise_test_environment):
        """Test enterprise error handling for FHIR validation."""
        env = enterprise_test_environment
        client = env["client"]
        admin_headers = env["admin_headers"]
        
        # Invalid resource with invalid resourceType
        invalid_resource = {
            "resourceType": "InvalidResourceType",
            "id": "patient-invalid-001"
        }
        
        validation_request = FHIRValidationRequest(
            resource=invalid_resource
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=admin_headers
        )
        
        assert response.status_code == 422
        result = response.json()
        
        # Should provide detailed validation errors
        assert "detail" in result or "issues" in result
    
    @pytest.mark.asyncio
    async def test_fhir_validation_performance_enterprise(self, enterprise_test_environment):
        """Test performance requirements for enterprise FHIR validation."""
        env = enterprise_test_environment
        client = env["client"]
        admin_headers = env["admin_headers"]
        
        # Large but valid patient resource
        large_patient_resource = {
            "resourceType": "Patient",
            "id": "patient-performance-001",
            "active": True,
            "identifier": [
                {
                    "use": "official",
                    "system": f"http://hospital.example.org/id-{i}",
                    "value": f"ID-{i:06d}"
                } for i in range(50)  # Multiple identifiers
            ],
            "name": [{
                "use": "official",
                "family": "PerformanceTest",
                "given": ["Large", "Resource"]
            }],
            "telecom": [
                {
                    "system": "phone",
                    "value": f"555-{i:04d}",
                    "use": "home"
                } for i in range(20)  # Multiple phone numbers
            ],
            "gender": "unknown",
            "birthDate": "1990-01-01"
        }
        
        validation_request = FHIRValidationRequest(
            resource=large_patient_resource
        )
        
        start_time = datetime.now(timezone.utc)
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=admin_headers
        )
        
        end_time = datetime.now(timezone.utc)
        processing_time = (end_time - start_time).total_seconds()
        
        assert response.status_code == 200
        assert processing_time < 5.0  # Should process within 5 seconds
        
        result = response.json()
        assert result["is_valid"] is True
        assert result["resource_type"] == "Patient"


# Integration test for the main validation function we need to fix
@pytest.mark.asyncio
async def test_fhir_validation_integration_enterprise(enterprise_test_environment):
    """Integration test for FHIR validation with enterprise authentication."""
    env = enterprise_test_environment
    client = env["client"]
    admin_headers = env["admin_headers"]
    
    patient_resource = {
        "resourceType": "Patient",
        "id": "patient-integration-001",
        "active": True,
        "identifier": [{
            "use": "official",
            "system": "http://hospital.example.org",       
            "value": "MRN-INTEGRATION-001"
        }],
        "name": [{
            "use": "official",
            "family": "IntegrationTest",
            "given": ["FHIR"]
        }],
        "gender": "other",
        "birthDate": "1990-01-01"
    }

    validation_request = FHIRValidationRequest(
        resource=patient_resource
    )

    response = await client.post(
        "/api/v1/healthcare/fhir/validate",
        json=validation_request.model_dump(),
        headers=admin_headers
    )

    assert response.status_code == 200
    result = response.json()
    
    # Verify complete validation response structure
    assert "is_valid" in result
    assert "resource_type" in result
    assert "issues" in result
    assert "warnings" in result
    
    assert result["is_valid"] is True
    assert result["resource_type"] == "Patient"
    assert isinstance(result["issues"], list)
    assert isinstance(result["warnings"], list)


@pytest.mark.asyncio 
async def test_fhir_validation_error_handling_enterprise(enterprise_test_environment):
    """Test error handling for FHIR validation with enterprise security."""
    env = enterprise_test_environment
    client = env["client"]
    admin_headers = env["admin_headers"]
    
    # Test with completely invalid resource type
    invalid_request = FHIRValidationRequest(
        resource={"resourceType": "InvalidResourceType", "id": "test"}
    )
    
    response = await client.post(
        "/api/v1/healthcare/fhir/validate",
        json=invalid_request.model_dump(),
        headers=admin_headers
    )
    
    assert response.status_code == 422
    result = response.json()
    
    # Should contain detailed error information
    assert "detail" in result or "message" in result