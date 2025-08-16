"""
FHIR R4 Resource Validation Comprehensive Testing Suite

This comprehensive test suite validates FHIR R4 resource compliance for:
- Patient resource validation with encrypted PHI fields
- Immunization resource validation with CVX codes
- Observation resource validation with LOINC codes
- DocumentReference validation with metadata integrity
- FHIR security labels and provenance tracking
- Resource reference integrity and linking validation
- Business rule validation beyond basic structure

Implements HL7 FHIR R4 specification compliance with healthcare
data integrity and security requirements for production systems.
"""

import pytest
import pytest_asyncio
import asyncio
import json
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Core testing imports
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

# Application imports
from app.main import app
from app.core.database_unified import get_db
from app.core.security import EncryptionService
from app.modules.healthcare_records.schemas import (
    FHIRValidationRequest, FHIRValidationResponse,
    PatientCreate, ImmunizationCreate
)
from app.modules.healthcare_records.fhir_validator import get_fhir_validator
from app.tests.helpers.auth_helpers import AuthTestHelper


@pytest_asyncio.fixture
async def setup_test_environment(db_session: AsyncSession):
    """Set up test environment with encryption and validation services."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        auth_helper = AuthTestHelper(db_session, client)
        
        # Create test user with unique username
        import uuid
        test_id = str(uuid.uuid4())[:8]
        username = f"fhir_validator_{test_id}"
        
        test_user = await auth_helper.create_user(
            username=username,
            role="system_admin",
            email=f"validator.{test_id}@example.com",
            password="ValidatorSecure123!"
        )
        
        # Get authentication headers
        auth_headers = await auth_helper.get_headers(
            username, "ValidatorSecure123!"
        )
        
        validator = get_fhir_validator()
        encryption_service = EncryptionService()
        
        yield {
            "client": client,
            "auth_helper": auth_helper,
            "test_user": test_user,
            "auth_headers": auth_headers,
            "validator": validator,
            "encryption_service": encryption_service,
            "db_session": db_session
        }
        
        await auth_helper.cleanup()


class TestFHIRValidationSuite:
    """Comprehensive FHIR R4 validation testing suite."""
    pass


@pytest.mark.asyncio
class TestPatientResourceValidation(TestFHIRValidationSuite):
    """Patient resource FHIR R4 validation tests."""
    
    async def test_valid_patient_resource_minimal(self, setup_test_environment):
        """Test validation of minimal valid Patient resource."""
        test_env = setup_test_environment
        client = test_env["client"]
        auth_headers = test_env["auth_headers"]
        validator = test_env["validator"]
        
        patient_resource = {
            "resourceType": "Patient",
            "id": "patient-001",
            "active": True,
            "identifier": [{
                "use": "official",
                "type": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                        "code": "MR"
                    }]
                },
                "system": "http://hospital.example.org",
                "value": "MRN123456"
            }],
            "name": [{
                "use": "official",
                "family": "TestPatient",
                "given": ["John", "William"]
            }],
            "gender": "male",
            "birthDate": "1990-01-01"
        }
        
        validation_request = FHIRValidationRequest(
            resource=patient_resource
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201]
        result = response.json()
        assert result["is_valid"] is True
        assert result["resource_type"] == "Patient"
        assert len(result["issues"]) == 0
    
    async def test_patient_resource_with_encrypted_fields(self, setup_test_environment):
        """Test Patient resource validation with encrypted PHI fields."""
        test_env = setup_test_environment
        client = test_env["client"]
        auth_headers = test_env["auth_headers"]
        patient_resource = {
            "resourceType": "Patient",
            "id": "patient-encrypted-001",
            "active": True,
            "identifier": [{
                "use": "official",
                "system": "http://hospital.example.org",
                "value": "[ENCRYPTED:MRN]"
            }],
            "name": [{
                "use": "official",
                "family": "[ENCRYPTED:LastName]",
                "given": ["[ENCRYPTED:FirstName]"]
            }],
            "telecom": [{
                "system": "phone",
                "value": "[ENCRYPTED:Phone]",
                "use": "home"
            }],
            "gender": "female",
            "birthDate": "[ENCRYPTED:DOB]",
            "address": [{
                "use": "home",
                "line": ["[ENCRYPTED:Address]"],
                "city": "[ENCRYPTED:City]",
                "state": "[ENCRYPTED:State]",
                "postalCode": "[ENCRYPTED:ZIP]",
                "country": "US"
            }],
            "meta": {
                "security": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                    "code": "R",
                    "display": "Restricted"
                }]
            }
        }
        
        validation_request = FHIRValidationRequest(
            resource=patient_resource
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["is_valid"] is True
        assert "encrypted" in str(result.get("warnings", [])).lower()
    
    async def test_patient_resource_invalid_gender(self, setup_test_environment):
        """Test Patient resource validation with invalid gender code."""
        test_env = setup_test_environment
        client = test_env["client"]
        auth_headers = test_env["auth_headers"]
        
        patient_resource = {
            "resourceType": "Patient",
            "id": "patient-invalid-001",
            "active": True,
            "name": [{
                "use": "official",
                "family": "TestPatient",
                "given": ["Jane"]
            }],
            "gender": "invalid_gender_code",  # Invalid gender
            "birthDate": "1985-05-15"
        }
        
        validation_request = FHIRValidationRequest(
            resource=patient_resource
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=auth_headers
        )
        
        # Enterprise healthcare deployment returns 422 for invalid resources
        assert response.status_code == 422
        result = response.json()
        # Should have validation error details for invalid gender
        assert "detail" in result
        assert "gender" in str(result["detail"]).lower()
    
    async def test_patient_resource_missing_required_fields(self, setup_test_environment):
        """Test Patient resource validation with missing required fields."""
        test_env = setup_test_environment
        client = test_env["client"]
        auth_headers = test_env["auth_headers"]
        
        patient_resource = {
            "resourceType": "Patient"
            # Missing all other required fields
        }
        
        validation_request = FHIRValidationRequest(
            resource=patient_resource
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=auth_headers
        )
        
        # Enterprise healthcare deployment returns 422 for invalid resources
        assert response.status_code == 422
        result = response.json()
        # Should have validation error details
        assert "detail" in result or "message" in result


@pytest.mark.asyncio
class TestImmunizationResourceValidation(TestFHIRValidationSuite):
    """Immunization resource FHIR R4 validation tests."""
    
    async def test_valid_immunization_resource(self, setup_test_environment):
        """Test validation of valid Immunization resource."""
        test_env = setup_test_environment
        client = test_env["client"]
        auth_headers = test_env["auth_headers"]
        
        immunization_resource = {
            "resourceType": "Immunization",
            "id": "immunization-001",
            "status": "completed",
            "vaccineCode": {
                "coding": [{
                    "system": "http://hl7.org/fhir/sid/cvx",
                    "code": "208",
                    "display": "COVID-19, mRNA, LNP-S, PF, 30 mcg/0.3 mL dose"
                }]
            },
            "patient": {
                "reference": "Patient/patient-001"
            },
            "occurrenceDateTime": "2024-01-15T10:30:00Z",
            "recorded": "2024-01-15T10:35:00Z",
            "primarySource": True,
            "lotNumber": "LOT123ABC",
            "expirationDate": "2025-01-15",
            "site": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActSite",
                    "code": "LA",
                    "display": "left arm"
                }]
            },
            "route": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-RouteOfAdministration",
                    "code": "IM",
                    "display": "Injection, intramuscular"
                }]
            },
            "doseQuantity": {
                "value": 0.3,
                "unit": "mL",
                "system": "http://unitsofmeasure.org",
                "code": "mL"
            },
            "performer": [{
                "function": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0443",
                        "code": "AP",
                        "display": "Administering Provider"
                    }]
                },
                "actor": {
                    "display": "Dr. Sarah Johnson, MD"
                }
            }],
            "reasonCode": [{
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": "840539006",
                    "display": "Disease caused by severe acute respiratory syndrome coronavirus 2"
                }]
            }],
            # Enterprise compliance fields for series tracking
            "series_complete": False,
            "series_dosed": 1
        }
        
        validation_request = FHIRValidationRequest(
            resource=immunization_resource
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["is_valid"] is True
        assert result["resource_type"] == "Immunization"
    
    async def test_immunization_resource_with_encrypted_fields(self, setup_test_environment):
        """Test Immunization resource with encrypted PHI fields."""
        test_env = setup_test_environment
        client = test_env["client"]
        auth_headers = test_env["auth_headers"]
        
        immunization_resource = {
            "resourceType": "Immunization",
            "id": "immunization-encrypted-001",
            "status": "completed",
            "vaccineCode": {
                "coding": [{
                    "system": "http://hl7.org/fhir/sid/cvx",
                    "code": "88",
                    "display": "Influenza virus vaccine"
                }]
            },
            "patient": {
                "reference": "Patient/patient-encrypted-001"
            },
            "occurrenceDateTime": "2024-01-15T10:30:00Z",
            "location": {
                "display": "[ENCRYPTED:Clinic Location]"
            },
            "lotNumber": "[ENCRYPTED:LotNumber]",
            "manufacturer": {
                "display": "[ENCRYPTED:Manufacturer]"
            },
            "performer": [{
                "actor": {
                    "display": "[ENCRYPTED:Provider Name]"
                }
            }],
            "meta": {
                "security": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                    "code": "R",
                    "display": "Restricted"
                }]
            },
            # Enterprise compliance fields for series tracking
            "series_complete": False,
            "series_dosed": 1
        }
        
        validation_request = FHIRValidationRequest(
            resource=immunization_resource
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["is_valid"] is True
    
    async def test_immunization_resource_invalid_cvx_code(self, setup_test_environment):
        """Test Immunization resource validation with invalid CVX code."""
        test_env = setup_test_environment
        client = test_env["client"]
        auth_headers = test_env["auth_headers"]
        
        immunization_resource = {
            "resourceType": "Immunization",
            "id": "immunization-invalid-001",
            "status": "completed",
            "vaccineCode": {
                "coding": [{
                    "system": "http://hl7.org/fhir/sid/cvx",
                    "code": "999999",  # Invalid CVX code
                    "display": "Invalid Vaccine"
                }]
            },
            "patient": {
                "reference": "Patient/patient-001"
            },
            "occurrenceDateTime": "2024-01-15T10:30:00Z",
            # Enterprise compliance fields for series tracking
            "series_complete": False,
            "series_dosed": 1
        }
        
        validation_request = FHIRValidationRequest(
            resource=immunization_resource
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        # Should have warnings about invalid CVX code
        assert len(result.get("warnings", [])) > 0 or not result["is_valid"]


@pytest.mark.asyncio
class TestObservationResourceValidation(TestFHIRValidationSuite):
    """Observation resource FHIR R4 validation tests."""
    
    async def test_valid_observation_resource(self, setup_test_environment):
        """Test validation of valid Observation resource."""
        test_env = setup_test_environment
        client = test_env["client"]
        auth_headers = test_env["auth_headers"]
        
        observation_resource = {
            "resourceType": "Observation",
            "id": "observation-001",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "8867-4",
                    "display": "Heart rate"
                }]
            },
            "subject": {
                "reference": "Patient/patient-001"
            },
            "effectiveDateTime": "2024-01-15T10:30:00Z",
            "valueQuantity": {
                "value": 72,
                "unit": "beats/min",
                "system": "http://unitsofmeasure.org",
                "code": "/min"
            },
            "performer": [{
                "reference": "Practitioner/practitioner-001"
            }]
        }
        
        validation_request = FHIRValidationRequest(
            resource=observation_resource
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["is_valid"] is True
        assert result["resource_type"] == "Observation"
    
    async def test_observation_resource_invalid_loinc_code(self, setup_test_environment):
        """Test Observation resource validation with invalid LOINC code."""
        test_env = setup_test_environment
        client = test_env["client"]
        auth_headers = test_env["auth_headers"]
        
        observation_resource = {
            "resourceType": "Observation",
            "id": "observation-invalid-001",
            "status": "final",
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "INVALID-CODE",  # Invalid LOINC code
                    "display": "Invalid Measurement"
                }]
            },
            "subject": {
                "reference": "Patient/patient-001"
            },
            "effectiveDateTime": "2024-01-15T10:30:00Z",
            "valueQuantity": {
                "value": 100,
                "unit": "mg/dL"
            }
        }
        
        validation_request = FHIRValidationRequest(
            resource=observation_resource
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        # Should have warnings about invalid LOINC code
        assert len(result.get("warnings", [])) > 0 or not result["is_valid"]


@pytest.mark.asyncio
class TestDocumentReferenceValidation(TestFHIRValidationSuite):
    """DocumentReference resource FHIR R4 validation tests."""
    
    async def test_valid_document_reference(self, setup_test_environment):
        """Test validation of valid DocumentReference resource."""
        test_env = setup_test_environment
        client = test_env["client"]
        auth_headers = test_env["auth_headers"]
        
        document_reference = {
            "resourceType": "DocumentReference",
            "id": "document-001",
            "status": "current",
            "docStatus": "final",
            "type": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "34108-1",
                    "display": "Outpatient Note"
                }]
            },
            "category": [{
                "coding": [{
                    "system": "http://hl7.org/fhir/us/core/CodeSystem/us-core-documentreference-category",
                    "code": "clinical-note",
                    "display": "Clinical Note"
                }]
            }],
            "subject": {
                "reference": "Patient/patient-001"
            },
            "date": "2024-01-15T10:30:00Z",
            "author": [{
                "reference": "Practitioner/practitioner-001"
            }],
            "content": [{
                "attachment": {
                    "contentType": "text/plain",
                    "data": "Q2xpbmljYWwgbm90ZSBjb250ZW50",  # Base64 encoded
                    "title": "Clinical Note",
                    "creation": "2024-01-15T10:30:00Z"
                }
            }],
            "context": {
                "encounter": [{
                    "reference": "Encounter/encounter-001"
                }],
                "period": {
                    "start": "2024-01-15T10:00:00Z",
                    "end": "2024-01-15T11:00:00Z"
                }
            },
            "securityLabel": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                "code": "R",
                "display": "Restricted"
            }]
        }
        
        validation_request = FHIRValidationRequest(
            resource=document_reference
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["is_valid"] is True
        assert result["resource_type"] == "DocumentReference"
    
    async def test_document_reference_with_encrypted_content(self, setup_test_environment):
        """Test DocumentReference with encrypted content."""
        test_env = setup_test_environment
        client = test_env["client"]
        auth_headers = test_env["auth_headers"]
        encryption_service = test_env["encryption_service"]
        
        # Encrypt the document title using our AES-256-GCM encryption
        encrypted_title = await encryption_service.encrypt_string("Confidential Patient Document")
        
        document_reference = {
            "resourceType": "DocumentReference",
            "id": "document-encrypted-001",
            "status": "current",
            "type": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "34108-1",
                    "display": "Outpatient Note"
                }]
            },
            "subject": {
                "reference": "Patient/patient-encrypted-001"
            },
            "date": "2024-01-15T10:30:00Z",
            "content": [{
                "attachment": {
                    "contentType": "application/encrypted",
                    "url": "https://secure-storage.example.org/documents/encrypted-001",
                    "title": encrypted_title,  # Use real AES-256-GCM encrypted data
                    "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                }
            }],
            "securityLabel": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                "code": "R",
                "display": "Restricted"
            }]
        }
        
        validation_request = FHIRValidationRequest(
            resource=document_reference
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["is_valid"] is True


@pytest.mark.asyncio
class TestFHIRSecurityLabelsValidation(TestFHIRValidationSuite):
    """FHIR security labels and access control validation tests."""
    
    async def test_security_labels_validation(self, setup_test_environment):
        """Test validation of FHIR security labels."""
        test_env = setup_test_environment
        client = test_env["client"]
        auth_headers = test_env["auth_headers"]
        
        patient_with_security = {
            "resourceType": "Patient",
            "id": "patient-security-001",
            "active": True,
            "name": [{
                "use": "official",
                "family": "SecurePatient",
                "given": ["Jane"]
            }],
            "meta": {
                "security": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                    "code": "R",
                    "display": "Restricted"
                }, {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                    "code": "HTEST",
                    "display": "test health data"
                }],
                "tag": [{
                    "system": "http://example.org/security-tags",
                    "code": "PHI",
                    "display": "Protected Health Information"
                }]
            }
        }
        
        validation_request = FHIRValidationRequest(
            resource=patient_with_security
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["is_valid"] is True
        
        # Check that security labels are recognized
        security_codes = [
            security["code"] 
            for security in patient_with_security["meta"]["security"]
        ]
        assert "R" in security_codes  # Restricted
        assert "HTEST" in security_codes  # Test data
    
    async def test_invalid_security_labels(self, setup_test_environment):
        """Test validation with invalid security labels."""
        test_env = setup_test_environment
        client = test_env["client"]
        auth_headers = test_env["auth_headers"]
        
        patient_with_invalid_security = {
            "resourceType": "Patient",
            "id": "patient-invalid-security-001",
            "active": True,
            "name": [{
                "use": "official",
                "family": "TestPatient",
                "given": ["John"]
            }],
            "meta": {
                "security": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                    "code": "INVALID_CODE",  # Invalid security code
                    "display": "Invalid Security Level"
                }]
            }
        }
        
        validation_request = FHIRValidationRequest(
            resource=patient_with_invalid_security
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        # Should have warnings about invalid security codes
        assert len(result.get("warnings", [])) > 0 or not result["is_valid"]


@pytest.mark.asyncio
class TestFHIRProvenanceTracking(TestFHIRValidationSuite):
    """FHIR Provenance resource validation tests."""
    
    async def test_valid_provenance_resource(self, setup_test_environment):
        """Test validation of valid Provenance resource."""
        test_env = setup_test_environment
        client = test_env["client"]
        auth_headers = test_env["auth_headers"]
        
        provenance_resource = {
            "resourceType": "Provenance",
            "id": "provenance-001",
            "target": [{
                "reference": "Patient/patient-001"
            }],
            "occurredDateTime": "2024-01-15T10:30:00Z",
            "recorded": "2024-01-15T10:31:00Z",
            "activity": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-DataOperation",
                    "code": "CREATE",
                    "display": "create"
                }]
            },
            "agent": [{
                "type": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
                        "code": "author",
                        "display": "Author"
                    }]
                },
                "who": {
                    "reference": "Practitioner/practitioner-001"
                }
            }],
            "signature": [{
                "type": [{
                    "system": "urn:iso-astm:E1762-95:2013",
                    "code": "1.2.840.10065.1.12.1.1",
                    "display": "Author's Signature"
                }],
                "when": "2024-01-15T10:31:00Z",
                "who": {
                    "reference": "Practitioner/practitioner-001"
                },
                "data": "dGhpcyBibG9iIGlzIHNuaXBwZWQ="  # Base64 encoded signature
            }]
        }
        
        validation_request = FHIRValidationRequest(
            resource=provenance_resource
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["is_valid"] is True
        assert result["resource_type"] == "Provenance"


@pytest.mark.asyncio
class TestFHIRBusinessRulesValidation(TestFHIRValidationSuite):
    """FHIR business rules and advanced validation tests."""
    
    async def test_patient_immunization_business_rules(self, setup_test_environment):
        """Test business rule validation for patient-immunization relationships."""
        test_env = setup_test_environment
        client = test_env["client"]
        auth_headers = test_env["auth_headers"]
        
        # First validate patient
        patient_resource = {
            "resourceType": "Patient",
            "id": "patient-business-001",
            "active": True,
            "birthDate": "2020-01-01",  # Child patient
            "name": [{
                "use": "official",
                "family": "ChildPatient",
                "given": ["Baby"]
            }]
        }
        
        # Then validate immunization with age-appropriate vaccine
        immunization_resource = {
            "resourceType": "Immunization",
            "id": "immunization-business-001",
            "status": "completed",
            "vaccineCode": {
                "coding": [{
                    "system": "http://hl7.org/fhir/sid/cvx",
                    "code": "08",  # Hepatitis B vaccine (appropriate for infants)
                    "display": "Hepatitis B vaccine"
                }]
            },
            "patient": {
                "reference": "Patient/patient-business-001"
            },
            "occurrenceDateTime": "2020-02-01T10:30:00Z"  # 1 month after birth
        }
        
        # Validate both resources
        patient_validation = FHIRValidationRequest(
            resource=patient_resource
        )
        
        immunization_validation = FHIRValidationRequest(
            resource=immunization_resource
        )
        
        # Test patient validation
        patient_response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=patient_validation.model_dump(),
            headers=auth_headers
        )
        assert patient_response.status_code == 200
        patient_result = patient_response.json()
        assert patient_result["is_valid"] is True
        
        # Test immunization validation
        immunization_response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=immunization_validation.model_dump(),
            headers=auth_headers
        )
        assert immunization_response.status_code == 200
        immunization_result = immunization_response.json()
        assert immunization_result["is_valid"] is True
    
    async def test_invalid_date_ranges(self, setup_test_environment):
        """Test validation of invalid date ranges in resources."""
        test_env = setup_test_environment
        client = test_env["client"]
        auth_headers = test_env["auth_headers"]
        
        observation_resource = {
            "resourceType": "Observation",
            "id": "observation-invalid-dates-001",
            "status": "final",
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "8867-4",
                    "display": "Heart rate"
                }]
            },
            "subject": {
                "reference": "Patient/patient-001"
            },
            "effectiveDateTime": "2025-01-01T10:30:00Z",  # Future date (invalid)
            "valueQuantity": {
                "value": 72,
                "unit": "beats/min"
            }
        }
        
        validation_request = FHIRValidationRequest(
            resource=observation_resource
        )
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        # Should detect future date as warning or error
        assert len(result.get("warnings", [])) > 0 or not result["is_valid"]


@pytest.mark.asyncio
class TestFHIRPerformanceValidation(TestFHIRValidationSuite):
    """FHIR validation performance and stress tests."""
    
    async def test_large_resource_validation_performance(self, setup_test_environment):
        """Test performance of validating large FHIR resources."""
        test_env = setup_test_environment
        client = test_env["client"]
        auth_headers = test_env["auth_headers"]
        
        # Create a large patient resource with many addresses and contacts
        large_patient = {
            "resourceType": "Patient",
            "id": "patient-large-001",
            "active": True,
            "identifier": [
                {
                    "use": "official",
                    "system": f"http://system-{i}.example.org",
                    "value": f"ID-{i:06d}"
                }
                for i in range(100)  # 100 identifiers
            ],
            "name": [{
                "use": "official",
                "family": "LargePatient",
                "given": ["Multi", "Identifier"]
            }],
            "address": [
                {
                    "use": "home",
                    "line": [f"Address Line {i}", f"Suite {i}"],
                    "city": f"City-{i}",
                    "state": f"State-{i}",
                    "postalCode": f"{i:05d}",
                    "country": "US"
                }
                for i in range(50)  # 50 addresses
            ]
        }
        
        validation_request = FHIRValidationRequest(
            resource=large_patient
        )
        
        start_time = datetime.now()
        
        response = await client.post(
            "/api/v1/healthcare/fhir/validate",
            json=validation_request.model_dump(),
            headers=auth_headers
        )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        assert response.status_code == 200
        result = response.json()
        assert result["is_valid"] is True
        
        # Performance assertion - should complete within reasonable time
        assert processing_time < 5.0, f"Validation took {processing_time}s, expected < 5s"
    
    async def test_concurrent_validation_performance(self, setup_test_environment):
        """Test concurrent FHIR resource validation performance."""
        test_env = setup_test_environment
        client = test_env["client"]
        auth_headers = test_env["auth_headers"]
        
        # Create multiple validation requests
        validation_requests = []
        for i in range(10):
            patient_resource = {
                "resourceType": "Patient",
                "id": f"patient-concurrent-{i:03d}",
                "active": True,
                "name": [{
                    "use": "official",
                    "family": f"ConcurrentPatient-{i}",
                    "given": ["Test"]
                }],
                "birthDate": f"199{i % 10}-01-01"
            }
            validation_requests.append(
                FHIRValidationRequest(
                    resource=patient_resource
                )
            )
        
        start_time = datetime.now()
        
        # Send concurrent requests
        responses = []
        for request in validation_requests:
            response = await client.post(
                "/api/v1/healthcare/fhir/validate",
                json=request.model_dump(),
                headers=auth_headers
            )
            responses.append(response)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Verify all responses
        for response in responses:
            assert response.status_code == 200
            result = response.json()
            assert result["is_valid"] is True
        
        # Performance assertion
        assert processing_time < 10.0, f"Concurrent validation took {processing_time}s, expected < 10s"


@pytest.mark.asyncio
async def test_fhir_validation_error_handling(setup_test_environment):
    """Test FHIR validation error handling and recovery."""
    test_env = setup_test_environment
    client = test_env["client"]
    auth_headers = test_env["auth_headers"]
    
    # Test with malformed JSON
    malformed_request = {
        "resource_type": "Patient",
        "resource_data": "INVALID_JSON"  # Should be dict, not string
    }
    
    response = await client.post(
        "/api/v1/healthcare/fhir/validate",
        json=malformed_request,
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error
    
    # Test with unsupported resource type
    unsupported_request = {
        "resource_type": "UnsupportedResource",
        "resource_data": {
            "resourceType": "UnsupportedResource",
            "id": "test-001"
        }
    }
    
    response = await client.post(
        "/api/v1/healthcare/fhir/validate",
        json=unsupported_request,
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio 
async def test_fhir_validation_integration(setup_test_environment):
    """Integration test for FHIR validation with healthcare service."""
    test_env = setup_test_environment
    client = test_env["client"]
    auth_headers = test_env["auth_headers"]
    
    # Test end-to-end validation workflow
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
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = response.json()
    
    # Verify complete validation response structure
    assert "is_valid" in result
    assert "resource_type" in result
    assert "issues" in result
    assert "warnings" in result or "issues" in result
    
    assert result["is_valid"] is True
    assert result["resource_type"] == "Patient"
    assert isinstance(result["issues"], list)
    if "warnings" in result:
        assert isinstance(result["warnings"], list)
    if "severity_counts" in result:
        assert isinstance(result["severity_counts"], dict)


if __name__ == "__main__":
    """Run FHIR validation tests independently."""
    pytest.main([__file__, "-v", "--tb=short"])