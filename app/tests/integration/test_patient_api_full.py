#!/usr/bin/env python3
"""
Comprehensive Patient API Integration Tests

Tests all CRUD operations, error cases, validation, and business logic
for the Patient API endpoints with real database interactions.
"""
import pytest
import uuid
from datetime import datetime, date
from typing import Dict, Any
from unittest.mock import AsyncMock, patch

from fastapi import status
from httpx import AsyncClient

from app.modules.healthcare_records.schemas import PatientCreate, PatientUpdate
from app.core.security import create_access_token


@pytest.mark.integration
@pytest.mark.asyncio
class TestPatientCRUDOperations:
    """Test Patient Create, Read, Update, Delete operations."""
    
    async def test_create_patient_success(self, async_test_client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test successful patient creation with all required fields."""
        patient_data = {
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
                    "value": f"MRN-{uuid.uuid4().hex[:8]}",
                    "use": "usual"
                }
            ],
            "active": True,
            "name": [
                {
                    "use": "official",
                    "family": "Johnson",
                    "given": ["Sarah", "Marie"],
                    "prefix": ["Ms."]
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
                    "value": "sarah.johnson@example.com",
                    "use": "home"
                }
            ],
            "gender": "female",
            "birthDate": "1985-06-15",
            "address": [
                {
                    "use": "home",
                    "type": "physical",
                    "line": ["123 Main Street", "Apt 4B"],
                    "city": "Springfield",
                    "state": "IL",
                    "postalCode": "62701",
                    "country": "US"
                }
            ],
            "organization_id": str(uuid.uuid4())
        }
        
        response = await async_test_client.post(
            "/api/v1/healthcare/patients",
            json=patient_data,
            headers=admin_auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        patient = response.json()
        
        # Verify response structure
        assert "id" in patient
        assert patient["name"][0]["family"] == "Johnson"
        assert patient["gender"] == "female"
        assert patient["active"] is True
        assert "created_at" in patient
        assert "updated_at" in patient
        
        # Store patient ID for other tests
        return patient["id"]
    
    @pytest.mark.asyncio
    async def test_create_patient_minimal_data(self, async_test_client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test patient creation with minimal required fields only."""
        minimal_patient = {
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
                    "system": "http://example.org/minimal",
                    "value": f"MIN-{uuid.uuid4().hex[:8]}",
                    "use": "usual"
                }
            ],
            "name": [
                {
                    "family": "Minimal",
                    "given": ["Test"],
                    "use": "official"
                }
            ],
            "gender": "unknown",
            "birthDate": "1990-01-01",
            "organization_id": str(uuid.uuid4())
        }
        
        response = await async_test_client.post(
            "/api/v1/healthcare/patients",
            json=minimal_patient,
            headers=admin_auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        patient = response.json()
        assert patient["name"][0]["family"] == "Minimal"
        assert patient["active"] is True  # Should default to True
    
    @pytest.mark.asyncio
    async def test_get_patient_by_id(self, async_test_client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test retrieving a patient by ID."""
        # First create a patient
        patient_id = await self.test_create_patient_success(async_test_client, admin_auth_headers)
        
        # Then retrieve it
        response = await async_test_client.get(
            f"/api/v1/healthcare/patients/{patient_id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        patient = response.json()
        assert patient["id"] == patient_id
        assert patient["name"][0]["family"] == "Johnson"
    
    @pytest.mark.asyncio
    async def test_list_patients_with_pagination(self, async_test_client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test listing patients with pagination parameters."""
        # Create multiple patients first
        for i in range(5):
            patient_data = {
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
                        "system": "http://example.org/test",
                        "value": f"TEST-{i}-{uuid.uuid4().hex[:6]}",
                        "use": "usual"
                    }
                ],
                "name": [
                    {
                        "family": f"TestFamily{i}",
                        "given": [f"TestGiven{i}"],
                        "use": "official"
                    }
                ],
                "gender": "unknown",
                "birthDate": "1990-01-01",
                "organization_id": str(uuid.uuid4())
            }
            
            await async_test_client.post(
                "/api/v1/healthcare/patients",
                json=patient_data,
                headers=admin_auth_headers
            )
        
        # Test listing with pagination
        response = await async_test_client.get(
            "/api/v1/healthcare/patients?limit=3&offset=0",
            headers=admin_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "patients" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert len(data["patients"]) <= 3
    
    @pytest.mark.asyncio
    async def test_update_patient(self, async_test_client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test updating patient information."""
        # Create a patient first
        patient_id = await self.test_create_patient_success(async_test_client, admin_auth_headers)
        
        # Update data
        update_data = {
            "active": False,
            "name": [
                {
                    "use": "official",
                    "family": "Johnson-Updated",
                    "given": ["Sarah", "Marie", "Updated"],
                }
            ],
            "telecom": [
                {
                    "system": "email",
                    "value": "sarah.updated@example.com",
                    "use": "work"
                }
            ]
        }
        
        response = await async_test_client.put(
            f"/api/v1/healthcare/patients/{patient_id}",
            json=update_data,
            headers=admin_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        updated_patient = response.json()
        assert updated_patient["name"][0]["family"] == "Johnson-Updated"
        assert updated_patient["active"] is False
        assert "Updated" in updated_patient["name"][0]["given"]
    
    @pytest.mark.asyncio
    async def test_soft_delete_patient(self, async_test_client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test soft deletion of patient (sets active=False)."""
        # Create a patient first
        patient_id = await self.test_create_patient_success(async_test_client, admin_auth_headers)
        
        # Soft delete
        response = await async_test_client.delete(
            f"/api/v1/healthcare/patients/{patient_id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify patient is marked inactive
        get_response = await async_test_client.get(
            f"/api/v1/healthcare/patients/{patient_id}",
            headers=admin_auth_headers
        )
        
        assert get_response.status_code == status.HTTP_200_OK
        patient = get_response.json()
        assert patient["active"] is False


@pytest.mark.integration
@pytest.mark.asyncio
class TestPatientAPIErrorHandling:
    """Test error cases and validation for Patient API."""
    
    async def test_create_patient_missing_required_fields(self, async_test_client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test creation fails with missing required fields."""
        invalid_data = {
            "name": [
                {
                    "family": "Incomplete",
                    "given": ["Test"]
                }
            ]
            # Missing identifier, gender, birthDate, organization_id
        }
        
        response = await async_test_client.post(
            "/api/v1/healthcare/patients",
            json=invalid_data,
            headers=admin_auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error = response.json()
        assert "detail" in error
    
    @pytest.mark.asyncio
    async def test_create_patient_invalid_gender(self, async_test_client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test creation fails with invalid gender value."""
        invalid_data = {
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
                    "system": "http://example.org/test",
                    "value": "TEST-INVALID",
                    "use": "usual"
                }
            ],
            "name": [
                {
                    "family": "Test",
                    "given": ["Invalid"],
                    "use": "official"
                }
            ],
            "gender": "invalid_gender",  # Invalid value
            "birthDate": "1990-01-01",
            "organization_id": str(uuid.uuid4())
        }
        
        response = await async_test_client.post(
            "/api/v1/healthcare/patients",
            json=invalid_data,
            headers=admin_auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_get_patient_not_found(self, async_test_client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test 404 error for non-existent patient."""
        fake_id = str(uuid.uuid4())
        
        response = await async_test_client.get(
            f"/api/v1/healthcare/patients/{fake_id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        error = response.json()
        assert "not found" in error["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_patient_invalid_uuid(self, async_test_client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test 422 error for invalid UUID format."""
        response = await async_test_client.get(
            "/api/v1/healthcare/patients/not-a-uuid",
            headers=admin_auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_update_patient_not_found(self, async_test_client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test 404 error when updating non-existent patient."""
        fake_id = str(uuid.uuid4())
        update_data = {
            "name": [
                {
                    "family": "NotFound",
                    "given": ["Test"],
                    "use": "official"
                }
            ]
        }
        
        response = await async_test_client.put(
            f"/api/v1/healthcare/patients/{fake_id}",
            json=update_data,
            headers=admin_auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.integration
@pytest.mark.asyncio
class TestPatientAPIAuthentication:
    """Test authentication and authorization for Patient API."""
    
    async def test_create_patient_requires_auth(self, async_test_client: AsyncClient):
        """Test that creating a patient requires authentication."""
        patient_data = {
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
                    "system": "http://example.org/test",
                    "value": "TEST-UNAUTH",
                    "use": "usual"
                }
            ],
            "name": [
                {
                    "family": "Unauthorized",
                    "given": ["Test"],
                    "use": "official"
                }
            ],
            "gender": "unknown",
            "birthDate": "1990-01-01",
            "organization_id": str(uuid.uuid4())
        }
        
        response = await async_test_client.post(
            "/api/v1/healthcare/patients",
            json=patient_data
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_regular_user_cannot_create_patient(self, async_test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test that regular users cannot create patients (requires operator role)."""
        patient_data = {
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
                    "system": "http://example.org/test",
                    "value": "TEST-FORBIDDEN",
                    "use": "usual"
                }
            ],
            "name": [
                {
                    "family": "Forbidden",
                    "given": ["Test"],
                    "use": "official"
                }
            ],
            "gender": "unknown",
            "birthDate": "1990-01-01",
            "organization_id": str(uuid.uuid4())
        }
        
        response = await async_test_client.post(
            "/api/v1/healthcare/patients",
            json=patient_data,
            headers=auth_headers  # Regular user headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.asyncio
    async def test_invalid_token_rejected(self, async_test_client: AsyncClient):
        """Test that invalid tokens are rejected."""
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        
        response = await async_test_client.get(
            "/api/v1/healthcare/patients",
            headers=invalid_headers
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.asyncio
class TestPatientAPIFiltering:
    """Test filtering and search functionality for Patient API."""
    
    async def test_filter_patients_by_name(self, async_test_client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test filtering patients by name."""
        # Create patients with specific names
        test_patients = [
            ("Smith", "John"),
            ("Smith", "Jane"), 
            ("Jones", "Bob"),
            ("Williams", "Alice")
        ]
        
        for family, given in test_patients:
            patient_data = {
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
                        "system": "http://example.org/filter-test",
                        "value": f"FILTER-{family}-{given}",
                        "use": "usual"
                    }
                ],
                "name": [
                    {
                        "family": family,
                        "given": [given],
                        "use": "official"
                    }
                ],
                "gender": "unknown",
                "birthDate": "1990-01-01",
                "organization_id": str(uuid.uuid4())
            }
            
            await async_test_client.post(
                "/api/v1/healthcare/patients",
                json=patient_data,
                headers=admin_auth_headers
            )
        
        # Filter by family name
        response = await async_test_client.get(
            "/api/v1/healthcare/patients?family_name=Smith",
            headers=admin_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["patients"]) == 2
        
        # Verify both Smith patients are returned
        family_names = [p["name"][0]["family"] for p in data["patients"]]
        assert all(name == "Smith" for name in family_names)
    
    @pytest.mark.asyncio
    async def test_filter_patients_by_gender(self, async_test_client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test filtering patients by gender."""
        # Create patients with different genders
        genders = ["male", "female", "other", "unknown"]
        
        for gender in genders:
            patient_data = {
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
                        "system": "http://example.org/gender-test",
                        "value": f"GENDER-{gender.upper()}",
                        "use": "usual"
                    }
                ],
                "name": [
                    {
                        "family": f"Test{gender.title()}",
                        "given": ["Gender"],
                        "use": "official"
                    }
                ],
                "gender": gender,
                "birthDate": "1990-01-01",
                "organization_id": str(uuid.uuid4())
            }
            
            await async_test_client.post(
                "/api/v1/healthcare/patients",
                json=patient_data,
                headers=admin_auth_headers
            )
        
        # Filter by gender
        response = await async_test_client.get(
            "/api/v1/healthcare/patients?gender=female",
            headers=admin_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["patients"]) == 1
        assert data["patients"][0]["gender"] == "female"
    
    @pytest.mark.asyncio
    async def test_filter_patients_by_active_status(self, async_test_client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test filtering patients by active status."""
        # Create active and inactive patients
        for i, active in enumerate([True, False, True, False]):
            patient_data = {
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
                        "system": "http://example.org/active-test",
                        "value": f"ACTIVE-{i}",
                        "use": "usual"
                    }
                ],
                "active": active,
                "name": [
                    {
                        "family": f"Active{i}",
                        "given": ["Test"],
                        "use": "official"
                    }
                ],
                "gender": "unknown",
                "birthDate": "1990-01-01",
                "organization_id": str(uuid.uuid4())
            }
            
            await async_test_client.post(
                "/api/v1/healthcare/patients",
                json=patient_data,
                headers=admin_auth_headers
            )
        
        # Filter by active status
        response = await async_test_client.get(
            "/api/v1/healthcare/patients?active=true",
            headers=admin_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["patients"]) == 2
        assert all(p["active"] is True for p in data["patients"])


@pytest.mark.integration
@pytest.mark.asyncio
class TestPatientAPIBusinessLogic:
    """Test business logic and PHI handling for Patient API."""
    
    @patch('app.core.audit_logger.audit_logger.log_event')
    async def test_patient_creation_logs_audit_event(self, mock_log_event, async_test_client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test that patient creation triggers audit logging."""
        patient_data = {
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
                    "system": "http://example.org/audit-test",
                    "value": "AUDIT-TEST",
                    "use": "usual"
                }
            ],
            "name": [
                {
                    "family": "AuditTest",
                    "given": ["Patient"],
                    "use": "official"
                }
            ],
            "gender": "unknown",
            "birthDate": "1990-01-01",
            "organization_id": str(uuid.uuid4())
        }
        
        response = await async_test_client.post(
            "/api/v1/healthcare/patients",
            json=patient_data,
            headers=admin_auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify audit event was logged
        mock_log_event.assert_called()
        call_args = mock_log_event.call_args
        assert "patient" in str(call_args).lower()
    
    @pytest.mark.asyncio
    async def test_patient_data_validation_birthdate(self, async_test_client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test birth date validation (future dates should be rejected)."""
        future_date = date.today().replace(year=date.today().year + 1)
        
        patient_data = {
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
                    "system": "http://example.org/date-test",
                    "value": "DATE-TEST",
                    "use": "usual"
                }
            ],
            "name": [
                {
                    "family": "FutureDate",
                    "given": ["Test"],
                    "use": "official"
                }
            ],
            "gender": "unknown",
            "birthDate": future_date.isoformat(),
            "organization_id": str(uuid.uuid4())
        }
        
        response = await async_test_client.post(
            "/api/v1/healthcare/patients",
            json=patient_data,
            headers=admin_auth_headers
        )
        
        # Should reject future birth dates
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_duplicate_identifier_handling(self, async_test_client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test handling of duplicate patient identifiers."""
        duplicate_identifier = f"DUP-{uuid.uuid4().hex[:8]}"
        
        # Create first patient
        patient_data_1 = {
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
                    "system": "http://example.org/dup-test",
                    "value": duplicate_identifier,
                    "use": "usual"
                }
            ],
            "name": [
                {
                    "family": "Duplicate",
                    "given": ["First"],
                    "use": "official"
                }
            ],
            "gender": "unknown",
            "birthDate": "1990-01-01",
            "organization_id": str(uuid.uuid4())
        }
        
        response_1 = await async_test_client.post(
            "/api/v1/healthcare/patients",
            json=patient_data_1,
            headers=admin_auth_headers
        )
        
        assert response_1.status_code == status.HTTP_201_CREATED
        
        # Try to create second patient with same identifier
        patient_data_2 = {
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
                    "system": "http://example.org/dup-test",
                    "value": duplicate_identifier,  # Same identifier
                    "use": "usual"
                }
            ],
            "name": [
                {
                    "family": "Duplicate",
                    "given": ["Second"],
                    "use": "official"
                }
            ],
            "gender": "unknown",
            "birthDate": "1990-01-01",
            "organization_id": str(uuid.uuid4())
        }
        
        response_2 = await async_test_client.post(
            "/api/v1/healthcare/patients",
            json=patient_data_2,
            headers=admin_auth_headers
        )
        
        # Should reject duplicate identifiers
        assert response_2.status_code == status.HTTP_409_CONFLICT


if __name__ == "__main__":
    """
    Run comprehensive patient API tests:
    python app/tests/integration/test_patient_api_full.py
    """
    import os
    os.chdir("/mnt/c/Users/aurik/Code_Projects/2_scraper")
    pytest.main([__file__, "-v", "--tb=short"])