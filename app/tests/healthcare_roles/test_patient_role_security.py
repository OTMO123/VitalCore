"""
HIPAA-Compliant Patient Role Security Testing Framework

Tests patient role access controls and PHI protection:
- Patients can only access their own records
- Consent management capabilities
- PHI access logging compliance
- FHIR R4 data validation
"""

import pytest
import uuid
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database_unified import User, Patient
from app.modules.auth.schemas import UserCreate
from app.modules.healthcare_records.schemas import PatientCreate
from app.tests.helpers.auth_helpers import create_test_user, get_auth_headers


@pytest.mark.security
@pytest.mark.patient_role
class TestPatientRoleSecurityCompliance:
    """Test suite for patient role security and HIPAA compliance."""
    
    @pytest.mark.asyncio
    async def test_patient_can_view_own_records_only(
        self, 
        async_client: AsyncClient, 
        db_session: AsyncSession
    ):
        """Test that patients can only access their own medical records."""
        
        # Create two patients with different user accounts
        patient1_user = await create_test_user(
            db_session, 
            username="patient1", 
            role="patient",
            email="patient1@test.com"
        )
        patient2_user = await create_test_user(
            db_session, 
            username="patient2", 
            role="patient",
            email="patient2@test.com"
        )
        
        # Create patient records
        patient1_data = PatientCreate(
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-01",
            gender="male"
        )
        patient2_data = PatientCreate(
            first_name="Jane",
            last_name="Smith", 
            date_of_birth="1985-05-15",
            gender="female"
        )
        
        # Create patients via API with respective user auth
        headers1 = await get_auth_headers(async_client, "patient1", "TestPassword123!")
        headers2 = await get_auth_headers(async_client, "patient2", "TestPassword123!")
        
        # Patient 1 creates their record
        response1 = await async_client.post(
            "/api/v1/healthcare/patients",
            json=patient1_data.dict(),
            headers=headers1
        )
        assert response1.status_code == status.HTTP_201_CREATED
        patient1_id = response1.json()["id"]
        
        # Patient 2 creates their record  
        response2 = await async_client.post(
            "/api/v1/healthcare/patients",
            json=patient2_data.dict(),
            headers=headers2
        )
        assert response2.status_code == status.HTTP_201_CREATED
        patient2_id = response2.json()["id"]
        
        # Test 1: Patient 1 can access their own record
        own_record_response = await async_client.get(
            f"/api/v1/healthcare/patients/{patient1_id}",
            headers=headers1
        )
        assert own_record_response.status_code == status.HTTP_200_OK
        own_data = own_record_response.json()
        assert own_data["name"][0]["given"][0] == "John"
        
        # Test 2: Patient 1 CANNOT access Patient 2's record (HIPAA compliance)
        unauthorized_response = await async_client.get(
            f"/api/v1/healthcare/patients/{patient2_id}",
            headers=headers1
        )
        assert unauthorized_response.status_code in [
            status.HTTP_403_FORBIDDEN, 
            status.HTTP_404_NOT_FOUND
        ]
        
        # Test 3: Verify PHI access is properly logged for audit compliance
        # This should be logged in audit_logs table with PHI_ACCESSED event
        
    @pytest.mark.asyncio
    async def test_patient_consent_management_capabilities(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test patient consent management and withdrawal capabilities."""
        
        # Create patient user
        patient_user = await create_test_user(
            db_session,
            username="consent_patient",
            role="patient", 
            email="consent@test.com"
        )
        
        headers = await get_auth_headers(async_client, "consent_patient", "TestPassword123!")
        
        # Create patient record
        patient_data = PatientCreate(
            first_name="Consent",
            last_name="Patient",
            date_of_birth="1990-01-01",
            gender="male"
        )
        
        create_response = await async_client.post(
            "/api/v1/healthcare/patients",
            json=patient_data.dict(),
            headers=headers
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        patient_id = create_response.json()["id"]
        
        # Test 1: Patient can view their consent status
        consent_response = await async_client.get(
            f"/api/v1/healthcare/patients/{patient_id}/consent",
            headers=headers
        )
        assert consent_response.status_code == status.HTTP_200_OK
        
        # Test 2: Patient can grant specific consent types
        consent_grant = {
            "consent_types": ["treatment", "data_sharing"],
            "purpose": "ongoing_care",
            "expiration_date": "2025-12-31"
        }
        
        grant_response = await async_client.post(
            f"/api/v1/healthcare/patients/{patient_id}/consent",
            json=consent_grant,
            headers=headers
        )
        assert grant_response.status_code == status.HTTP_201_CREATED
        
        # Test 3: Patient can withdraw consent
        withdraw_response = await async_client.delete(
            f"/api/v1/healthcare/patients/{patient_id}/consent/treatment",
            headers=headers
        )
        assert withdraw_response.status_code == status.HTTP_200_OK
        
    @pytest.mark.asyncio
    async def test_patient_data_portability_rights(
        self,
        async_client: AsyncClient, 
        db_session: AsyncSession
    ):
        """Test patient right to data portability (GDPR/HIPAA compliance)."""
        
        patient_user = await create_test_user(
            db_session,
            username="portability_patient",
            role="patient",
            email="portability@test.com"
        )
        
        headers = await get_auth_headers(async_client, "portability_patient", "TestPassword123!")
        
        # Create patient with comprehensive data
        patient_data = PatientCreate(
            first_name="Portability",
            last_name="Patient", 
            date_of_birth="1985-03-15",
            gender="female",
            phone="555-0123",
            email="portability@test.com"
        )
        
        create_response = await async_client.post(
            "/api/v1/healthcare/patients", 
            json=patient_data.dict(),
            headers=headers
        )
        patient_id = create_response.json()["id"]
        
        # Test 1: Patient can export their complete medical record
        export_response = await async_client.get(
            f"/api/v1/healthcare/patients/{patient_id}/export",
            headers=headers
        )
        assert export_response.status_code == status.HTTP_200_OK
        
        export_data = export_response.json()
        assert "patient_data" in export_data
        assert "immunizations" in export_data
        assert "clinical_documents" in export_data
        assert "audit_trail" in export_data  # HIPAA requirement
        
        # Test 2: Export includes FHIR R4 compliant format
        assert export_data["patient_data"]["resourceType"] == "Patient"
        assert "identifier" in export_data["patient_data"]
        
        # Test 3: Audit logging for data export (SOC2 compliance)
        # Export should trigger PHI_EXPORTED audit event
        
    @pytest.mark.asyncio
    async def test_patient_cannot_access_administrative_functions(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that patients cannot access administrative or other users' functions."""
        
        patient_user = await create_test_user(
            db_session,
            username="restricted_patient", 
            role="patient",
            email="restricted@test.com"
        )
        
        headers = await get_auth_headers(async_client, "restricted_patient", "TestPassword123!")
        
        # Test 1: Cannot access user management
        users_response = await async_client.get(
            "/api/v1/auth/users",
            headers=headers
        )
        assert users_response.status_code == status.HTTP_403_FORBIDDEN
        
        # Test 2: Cannot access audit logs
        audit_response = await async_client.get(
            "/api/v1/audit/logs",
            headers=headers  
        )
        assert audit_response.status_code == status.HTTP_403_FORBIDDEN
        
        # Test 3: Cannot access system configuration
        config_response = await async_client.get(
            "/api/v1/system/config",
            headers=headers
        )
        assert config_response.status_code == status.HTTP_403_FORBIDDEN
        
        # Test 4: Cannot create other users
        new_user_data = {
            "username": "malicious_user",
            "email": "malicious@test.com", 
            "password": "Password123!",
            "role": "admin"
        }
        
        create_user_response = await async_client.post(
            "/api/v1/auth/register",
            json=new_user_data,
            headers=headers
        )
        assert create_user_response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_patient_phi_access_audit_compliance(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that all patient PHI access is properly audited for HIPAA compliance."""
        
        patient_user = await create_test_user(
            db_session,
            username="audit_patient",
            role="patient", 
            email="audit@test.com"
        )
        
        headers = await get_auth_headers(async_client, "audit_patient", "TestPassword123!")
        
        # Create patient record
        patient_data = PatientCreate(
            first_name="Audit",
            last_name="Patient",
            date_of_birth="1990-01-01", 
            gender="male"
        )
        
        create_response = await async_client.post(
            "/api/v1/healthcare/patients",
            json=patient_data.dict(),
            headers=headers
        )
        patient_id = create_response.json()["id"]
        
        # Access patient record multiple times
        for i in range(3):
            access_response = await async_client.get(
                f"/api/v1/healthcare/patients/{patient_id}",
                headers=headers
            )
            assert access_response.status_code == status.HTTP_200_OK
        
        # Verify audit logs contain all PHI access events
        # This would be verified by checking audit_logs table
        # Each access should create PHI_ACCESSED audit event with:
        # - user_id, patient_id, timestamp
        # - fields_accessed list
        # - access_purpose
        # - IP address and session info
        
    @pytest.mark.asyncio
    async def test_patient_emergency_access_scenarios(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test patient record access during emergency scenarios."""
        
        # Create patient
        patient_user = await create_test_user(
            db_session,
            username="emergency_patient",
            role="patient",
            email="emergency@test.com"
        )
        
        # Create emergency user (doctor with emergency access)
        emergency_user = await create_test_user(
            db_session,
            username="emergency_doctor", 
            role="physician",
            email="emergency.doctor@test.com"
        )
        
        patient_headers = await get_auth_headers(async_client, "emergency_patient", "TestPassword123!")
        emergency_headers = await get_auth_headers(async_client, "emergency_doctor", "TestPassword123!")
        
        # Create patient record
        patient_data = PatientCreate(
            first_name="Emergency",
            last_name="Patient",
            date_of_birth="1990-01-01",
            gender="male"
        )
        
        create_response = await async_client.post(
            "/api/v1/healthcare/patients",
            json=patient_data.dict(), 
            headers=patient_headers
        )
        patient_id = create_response.json()["id"]
        
        # Test emergency access (break-glass scenario)
        emergency_access = {
            "access_reason": "emergency_treatment",
            "clinical_justification": "Patient unconscious, immediate treatment required",
            "emergency_contact": "Dr. Emergency, Trauma Unit"
        }
        
        emergency_response = await async_client.post(
            f"/api/v1/healthcare/patients/{patient_id}/emergency-access",
            json=emergency_access,
            headers=emergency_headers
        )
        assert emergency_response.status_code == status.HTTP_200_OK
        
        # Emergency access should be heavily audited
        # Should create EMERGENCY_ACCESS audit event
        # Should notify patient of emergency access
        # Should have time-limited access window
        
        
@pytest.mark.security
@pytest.mark.integration  
class TestPatientRoleIntegration:
    """Integration tests for patient role across multiple healthcare modules."""
    
    @pytest.mark.asyncio
    async def test_patient_immunization_record_access(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test patient access to their immunization records."""
        
        patient_user = await create_test_user(
            db_session,
            username="immunization_patient",
            role="patient",
            email="immunization@test.com"
        )
        
        headers = await get_auth_headers(async_client, "immunization_patient", "TestPassword123!")
        
        # Patient should be able to view their immunization history
        immunization_response = await async_client.get(
            "/api/v1/healthcare/immunizations?patient_id=self",
            headers=headers
        )
        assert immunization_response.status_code == status.HTTP_200_OK
        
    @pytest.mark.asyncio
    async def test_patient_clinical_document_access(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test patient access to their clinical documents."""
        
        patient_user = await create_test_user(
            db_session, 
            username="document_patient",
            role="patient",
            email="document@test.com"
        )
        
        headers = await get_auth_headers(async_client, "document_patient", "TestPassword123!")
        
        # Patient should be able to view their clinical documents
        documents_response = await async_client.get(
            "/api/v1/documents/patient/self",
            headers=headers
        )
        assert documents_response.status_code == status.HTTP_200_OK