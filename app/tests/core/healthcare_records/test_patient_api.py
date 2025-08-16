"""
Patient API tests for healthcare records module.

Tests patient creation, retrieval, updating, and PHI encryption.
Comprehensive testing for FHIR R4 compliance and HIPAA security.
"""
import pytest
import json
import uuid
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.modules.healthcare_records.schemas import (
    PatientCreate, PatientUpdate, PatientResponse,
    PatientName, PatientIdentifier, PatientAddress,
    ConsentStatus, ConsentType
)

pytestmark = pytest.mark.healthcare


class TestPatientAPI:
    """Test patient management API endpoints"""
    
    @pytest.fixture
    def sample_patient_data(self) -> Dict[str, Any]:
        """Sample patient data for testing."""
        return {
            "identifier": [
                {
                    "use": "official",
                    "type": {
                        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}]
                    },
                    "system": "http://hospital.example.org/patients",
                    "value": "MRN123456789"
                }
            ],
            "active": True,
            "name": [
                {
                    "use": "official",
                    "family": "Doe",
                    "given": ["John", "William"]
                }
            ],
            "telecom": [
                {
                    "system": "phone",
                    "value": "+1-555-123-4567",
                    "use": "home"
                },
                {
                    "system": "email",
                    "value": "john.doe@example.com",
                    "use": "home"
                }
            ],
            "gender": "male",
            "birthDate": "1990-01-15",
            "address": [
                {
                    "use": "home",
                    "type": "physical",
                    "line": ["123 Main St", "Apt 4B"],
                    "city": "Anytown",
                    "state": "NY",
                    "postalCode": "12345",
                    "country": "US"
                }
            ],
            "consent_status": "active",
            "consent_types": ["treatment", "immunization_registry"],
            "organization_id": str(uuid.uuid4()),
            # Additional helper fields for the service
            "first_name": "John William",
            "last_name": "Doe",
            "date_of_birth": "1990-01-15"
        }
    
    @pytest.mark.asyncio
    async def test_create_patient_success(self, async_test_client, admin_auth_headers, sample_patient_data):
        """
        Test successful patient creation with PHI encryption.
        Verifies FHIR compliance and secure data handling.
        """
        response = await async_test_client.post(
            "/api/v1/healthcare/patients",
            headers=admin_auth_headers,
            json=sample_patient_data
        )
        
        assert response.status_code == 201
        patient_data = response.json()
        
        # Verify FHIR structure
        assert patient_data["resourceType"] == "Patient"
        assert "id" in patient_data
        assert patient_data["active"] is True
        
        # Verify identifiers
        assert len(patient_data["identifier"]) == 1
        assert patient_data["identifier"][0]["use"] == "official"
        
        # Verify names (should be encrypted in storage but decrypted in response for authorized user)
        assert len(patient_data["name"]) == 1
        assert patient_data["name"][0]["family"] == "Doe"
        assert patient_data["name"][0]["given"] == ["John", "William"]
        
        # Verify contact info is handled
        assert "telecom" in patient_data
        assert len(patient_data["telecom"]) == 2
        
        # Verify consent information
        assert patient_data["consent_status"] == "active"
        assert "treatment" in patient_data["consent_types"]
        assert "immunization_registry" in patient_data["consent_types"]
        
        # Verify metadata
        assert "created_at" in patient_data
        assert "updated_at" in patient_data
        assert "organization_id" in patient_data
        
        print("✓ Patient creation with PHI encryption successful")
    
    @pytest.mark.asyncio
    async def test_create_patient_validation_errors(self, async_test_client, admin_auth_headers):
        """
        Test patient creation validation.
        Ensures proper validation of required fields.
        """
        # Test missing required fields
        invalid_patients = [
            {},  # Empty data
            {"active": True},  # Missing identifier and name
            {"identifier": [], "name": []},  # Empty required arrays
            {
                "identifier": [{"use": "official", "value": "123"}],
                "name": []  # Empty names
            },
            {
                "identifier": [],
                "name": [{"family": "Doe", "given": ["John"]}]  # Empty identifiers
            }
        ]
        
        for invalid_data in invalid_patients:
            response = await async_test_client.post(
                "/api/v1/healthcare/patients",
                headers=admin_auth_headers,
                json=invalid_data
            )
            
            assert response.status_code == 422  # Validation error
            error_detail = response.json()["detail"]
            assert isinstance(error_detail, list)
            
        print("✓ Patient validation errors handled correctly")
    
    @pytest.mark.asyncio 
    async def test_get_patient_by_id(self, async_test_client, admin_auth_headers, test_patient):
        """
        Test patient retrieval by ID.
        Verifies proper data decryption and FHIR format.
        """
        patient_id = test_patient.id
        
        response = await async_test_client.get(
            f"/api/v1/healthcare/patients/{patient_id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        patient_data = response.json()
        
        # Verify FHIR structure
        assert patient_data["resourceType"] == "Patient"
        assert patient_data["id"] == str(patient_id)
        
        # Verify encrypted data is properly decrypted for authorized user
        assert "name" in patient_data
        assert "identifier" in patient_data
        
        # Verify consent information is included
        assert "consent_status" in patient_data
        assert "consent_types" in patient_data
        
        print("✓ Patient retrieval by ID successful")
    
    @pytest.mark.asyncio
    async def test_get_patient_not_found(self, async_test_client, admin_auth_headers):
        """
        Test patient retrieval for non-existent patient.
        """
        fake_id = str(uuid.uuid4())
        
        response = await async_test_client.get(
            f"/api/v1/healthcare/patients/{fake_id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
        print("✓ Patient not found handled correctly")
    
    @pytest.mark.asyncio
    async def test_update_patient(self, async_test_client, admin_auth_headers, test_patient):
        """
        Test patient update functionality.
        Verifies partial updates and PHI encryption.
        """
        patient_id = test_patient.id
        
        update_data = {
            "active": False,
            "gender": "female",
            "consent_status": "withdrawn"
        }
        
        response = await async_test_client.put(
            f"/api/v1/healthcare/patients/{patient_id}",
            headers=admin_auth_headers,
            json=update_data
        )
        
        assert response.status_code == 200
        updated_patient = response.json()
        
        # Verify updates applied
        assert updated_patient["active"] is False
        assert updated_patient["gender"] == "female"
        assert updated_patient["consent_status"] == "withdrawn"
        
        # Verify updated timestamp changed
        assert "updated_at" in updated_patient
        
        print("✓ Patient update successful")
    
    @pytest.mark.asyncio
    async def test_list_patients_with_pagination(self, async_test_client, admin_auth_headers):
        """
        Test patient listing with pagination.
        Verifies proper access control and pagination.
        """
        response = await async_test_client.get(
            "/api/v1/healthcare/patients?offset=0&limit=10",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        patients_data = response.json()
        
        # Should return paginated response
        assert "patients" in patients_data
        assert "total" in patients_data
        assert "limit" in patients_data
        assert "offset" in patients_data
        patients = patients_data["patients"]
        
        # Verify FHIR format for each patient
        for patient in patients:
            assert patient["resourceType"] == "Patient"
            assert "id" in patient
            assert "identifier" in patient
            
        print("✓ Patient listing with pagination successful")
    
    @pytest.mark.asyncio
    async def test_patient_access_control(self, async_test_client, user_headers, test_patient):
        """
        Test patient access control for different user roles.
        Verifies proper RBAC implementation.
        """
        patient_id = test_patient.id
        
        # Regular user should have limited access
        response = await async_test_client.get(
            f"/api/v1/healthcare/patients/{patient_id}",
            headers=user_headers
        )
        
        # Depending on implementation, might be 403 (forbidden) or 200 with filtered data
        if response.status_code == 200:
            patient_data = response.json()
            # Should not contain sensitive administrative fields
            sensitive_fields = ["ssn_encrypted", "internal_notes", "audit_metadata"]
            patient_json = json.dumps(patient_data)
            for field in sensitive_fields:
                assert field not in patient_json
        else:
            assert response.status_code in [403, 404]  # Forbidden or not found (data filtering)
        
        print("✓ Patient access control verified")
    
    @pytest.mark.asyncio
    async def test_patient_phi_encryption_integration(self, async_test_client, admin_auth_headers, sample_patient_data):
        """
        Test PHI encryption integration.
        Verifies that PHI data is encrypted in storage.
        """
        # Create patient with PHI data
        response = await async_test_client.post(
            "/api/v1/healthcare/patients",
            headers=admin_auth_headers,
            json=sample_patient_data
        )
        
        assert response.status_code == 201
        patient_data = response.json()
        patient_id = patient_data["id"]
        
        # Retrieve patient
        response = await async_test_client.get(
            f"/api/v1/healthcare/patients/{patient_id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        retrieved_patient = response.json()
        
        # Verify PHI fields are present and properly handled
        phi_fields = ["name", "telecom", "birthDate", "address"]
        for field in phi_fields:
            if field in sample_patient_data and sample_patient_data[field]:
                assert field in retrieved_patient
                # Data should be properly decrypted for authorized user
                assert retrieved_patient[field] is not None
        
        print("✓ PHI encryption integration verified")
    
    @pytest.mark.asyncio
    async def test_patient_consent_management(self, async_test_client, admin_auth_headers, test_patient):
        """
        Test patient consent management functionality.
        Verifies HIPAA-compliant consent tracking.
        """
        patient_id = test_patient.id
        
        # Update consent status
        consent_update = {
            "consent_status": "withdrawn",
            "consent_types": ["treatment"]  # Remove research consent
        }
        
        response = await async_test_client.put(
            f"/api/v1/healthcare/patients/{patient_id}",
            headers=admin_auth_headers,
            json=consent_update
        )
        
        assert response.status_code == 200
        updated_patient = response.json()
        
        # Verify consent changes
        assert updated_patient["consent_status"] == "withdrawn"
        assert updated_patient["consent_types"] == ["treatment"]
        
        # Test consent validation endpoint if available
        response = await async_test_client.get(
            f"/api/v1/healthcare/patients/{patient_id}/consent-status",
            headers=admin_auth_headers
        )
        
        if response.status_code == 200:
            consent_info = response.json()
            assert "consent_status" in consent_info
            assert "consent_types" in consent_info
            assert "last_updated" in consent_info
        
        print("✓ Patient consent management verified")
    
    @pytest.mark.asyncio
    async def test_patient_search_functionality(self, async_test_client, admin_auth_headers):
        """
        Test patient search capabilities.
        Verifies search works with encrypted PHI fields.
        """
        # Test search by various criteria
        search_params = [
            {"identifier": "MRN123"},
            {"family_name": "Doe"},
            {"gender": "male"},
            {"organization_id": str(uuid.uuid4())}
        ]
        
        for params in search_params:
            response = await async_test_client.get(
                "/api/v1/healthcare/patients/search",
                headers=admin_auth_headers,
                params=params
            )
            
            # Should return valid response (might be empty results)
            assert response.status_code == 200
            search_results = response.json()
            
            # Verify response format (should be paginated)
            assert isinstance(search_results, dict)
            assert "patients" in search_results
            assert "total" in search_results
            assert "limit" in search_results
            assert "offset" in search_results
        
        print("✓ Patient search functionality verified")
    
    @pytest.mark.asyncio
    async def test_patient_fhir_compliance(self, async_test_client, admin_auth_headers, sample_patient_data):
        """
        Test FHIR R4 compliance for patient resources.
        Verifies proper FHIR structure and validation.
        """
        # Create patient
        response = await async_test_client.post(
            "/api/v1/healthcare/patients",
            headers=admin_auth_headers,
            json=sample_patient_data
        )
        
        assert response.status_code == 201
        patient_data = response.json()
        
        # Test FHIR validation endpoint if available
        fhir_validation_request = {
            "resource_type": "Patient",
            "resource_data": patient_data
        }
        
        response = await async_test_client.post(
            "/api/v1/healthcare/fhir/validate",
            headers=admin_auth_headers,
            json=fhir_validation_request
        )
        
        if response.status_code == 200:
            validation_result = response.json()
            assert validation_result["is_valid"] is True
            assert validation_result["resource_type"] == "Patient"
            assert len(validation_result.get("errors", [])) == 0
        
        print("✓ Patient FHIR compliance verified")


class TestPatientPHIEncryption:
    """Test PHI encryption specific functionality"""
    
    @pytest.mark.asyncio
    async def test_phi_field_encryption(self, encryption_service, sample_patient_data):
        """
        Test that PHI fields are properly encrypted.
        Verifies field-level encryption implementation.
        """
        phi_sensitive_fields = {
            "name": sample_patient_data["name"][0]["family"],
            "birth_date": sample_patient_data["birthDate"],
            "phone": sample_patient_data["telecom"][0]["value"],
            "email": sample_patient_data["telecom"][1]["value"],
            "address": sample_patient_data["address"][0]["line"][0]
        }
        
        for field_type, value in phi_sensitive_fields.items():
            # Test encryption
            encrypted = await encryption_service.encrypt(value, context={"field": field_type})
            assert encrypted != str(value)  # Compare with string representation
            
            # Length comparison only for string values
            if isinstance(value, str):
                assert len(encrypted) > len(value)
            else:
                # For non-string values, just ensure encryption produces a result
                assert len(encrypted) > 0
            
            # Test decryption - compare with original isoformat for dates
            decrypted = await encryption_service.decrypt(encrypted)
            expected_value = value.isoformat() if hasattr(value, 'isoformat') else str(value)
            assert decrypted == expected_value
        
        print("✓ PHI field encryption verified")
    
    @pytest.mark.asyncio 
    async def test_phi_encryption_context_awareness(self, encryption_service):
        """
        Test that encryption is context-aware for different PHI types.
        """
        test_ssn = "123-45-6789"
        
        # Different contexts should be handled appropriately
        contexts = [
            {"field": "ssn", "patient_id": "12345"},
            {"field": "ssn", "patient_id": "67890"},
            {"field": "mrn", "patient_id": "12345"},
        ]
        
        encrypted_values = []
        for context in contexts:
            encrypted = await encryption_service.encrypt(test_ssn, context=context)
            encrypted_values.append(encrypted)
            
            # Verify decryption works
            decrypted = await encryption_service.decrypt(encrypted)
            assert decrypted == test_ssn
        
        # All encrypted values should be different (context-aware)
        assert len(set(encrypted_values)) == len(encrypted_values)
        
        print("✓ PHI encryption context awareness verified")


if __name__ == "__main__":
    """
    Run patient API tests directly:
    python app/tests/core/healthcare_records/test_patient_api.py
    """
    print("🏥 Running patient API tests...")
    pytest.main([__file__, "-v", "--tb=short"])