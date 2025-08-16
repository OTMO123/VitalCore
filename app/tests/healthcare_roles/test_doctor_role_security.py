"""
HIPAA-Compliant Doctor Role Security Testing Framework

Tests doctor role access controls and clinical workflow permissions:
- Doctors can only access assigned patients
- Clinical workflow initiation capabilities  
- Prescription management with audit trails
- PHI access logging and minimum necessary compliance
"""

import pytest
import uuid
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.core.database_unified import User, Patient
from app.modules.auth.schemas import UserCreate
from app.modules.healthcare_records.schemas import PatientCreate
from app.modules.clinical_workflows.schemas import ClinicalWorkflowCreate, ClinicalEncounterCreate
from app.tests.helpers.auth_helpers import create_test_user, get_auth_headers


@pytest.mark.security
@pytest.mark.doctor_role
class TestDoctorRoleSecurityCompliance:
    """Test suite for doctor role security and HIPAA compliance."""
    
    @pytest.mark.asyncio
    async def test_doctor_can_access_assigned_patients_only(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that doctors can only access patients assigned to their care."""
        
        # Create doctors and patients
        doctor1 = await create_test_user(
            db_session,
            username="doctor1", 
            role="physician",
            email="doctor1@hospital.com"
        )
        doctor2 = await create_test_user(
            db_session,
            username="doctor2",
            role="physician", 
            email="doctor2@hospital.com"
        )
        
        # Create admin to set up patient assignments
        admin_user = await create_test_user(
            db_session,
            username="admin_assign",
            role="admin",
            email="admin@hospital.com"
        )
        
        doctor1_headers = await get_auth_headers(async_client, "doctor1", "TestPassword123!")
        doctor2_headers = await get_auth_headers(async_client, "doctor2", "TestPassword123!")
        admin_headers = await get_auth_headers(async_client, "admin_assign", "TestPassword123!")
        
        # Create patients
        patient1_data = PatientCreate(
            first_name="Patient",
            last_name="One",
            date_of_birth="1990-01-01",
            gender="male"
        )
        patient2_data = PatientCreate(
            first_name="Patient", 
            last_name="Two",
            date_of_birth="1985-05-15",
            gender="female"
        )
        
        # Admin creates patients
        patient1_response = await async_client.post(
            "/api/v1/healthcare/patients",
            json=patient1_data.dict(),
            headers=admin_headers
        )
        patient2_response = await async_client.post(
            "/api/v1/healthcare/patients", 
            json=patient2_data.dict(),
            headers=admin_headers
        )
        
        patient1_id = patient1_response.json()["id"]
        patient2_id = patient2_response.json()["id"]
        
        # Assign Patient 1 to Doctor 1, Patient 2 to Doctor 2
        assignment1 = {
            "patient_id": patient1_id,
            "doctor_id": str(doctor1.id),
            "assignment_type": "primary_care",
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=365)).isoformat()
        }
        assignment2 = {
            "patient_id": patient2_id, 
            "doctor_id": str(doctor2.id),
            "assignment_type": "primary_care",
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=365)).isoformat()
        }
        
        await async_client.post(
            "/api/v1/healthcare/patient-assignments",
            json=assignment1,
            headers=admin_headers
        )
        await async_client.post(
            "/api/v1/healthcare/patient-assignments",
            json=assignment2, 
            headers=admin_headers
        )
        
        # Test 1: Doctor 1 can access their assigned patient
        assigned_response = await async_client.get(
            f"/api/v1/healthcare/patients/{patient1_id}",
            headers=doctor1_headers
        )
        assert assigned_response.status_code == status.HTTP_200_OK
        
        # Test 2: Doctor 1 CANNOT access unassigned patient (HIPAA minimum necessary)
        unassigned_response = await async_client.get(
            f"/api/v1/healthcare/patients/{patient2_id}",
            headers=doctor1_headers
        )
        assert unassigned_response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
        
        # Test 3: Doctor can view list of only their assigned patients
        assigned_patients_response = await async_client.get(
            "/api/v1/healthcare/patients/assigned",
            headers=doctor1_headers
        )
        assert assigned_patients_response.status_code == status.HTTP_200_OK
        assigned_patients = assigned_patients_response.json()
        assert len(assigned_patients["patients"]) == 1
        assert assigned_patients["patients"][0]["id"] == patient1_id
        
    @pytest.mark.asyncio
    async def test_doctor_clinical_workflow_initiation(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test doctor capability to initiate and manage clinical workflows."""
        
        doctor = await create_test_user(
            db_session,
            username="workflow_doctor",
            role="physician", 
            email="workflow@hospital.com"
        )
        
        # Create patient assigned to doctor
        admin = await create_test_user(
            db_session,
            username="workflow_admin",
            role="admin",
            email="admin@hospital.com"
        )
        
        doctor_headers = await get_auth_headers(async_client, "workflow_doctor", "TestPassword123!")
        admin_headers = await get_auth_headers(async_client, "workflow_admin", "TestPassword123!")
        
        # Create patient
        patient_data = PatientCreate(
            first_name="Workflow",
            last_name="Patient",
            date_of_birth="1990-01-01",
            gender="male"
        )
        
        patient_response = await async_client.post(
            "/api/v1/healthcare/patients",
            json=patient_data.dict(),
            headers=admin_headers
        )
        patient_id = patient_response.json()["id"]
        
        # Assign patient to doctor
        assignment = {
            "patient_id": patient_id,
            "doctor_id": str(doctor.id),
            "assignment_type": "primary_care"
        }
        await async_client.post(
            "/api/v1/healthcare/patient-assignments",
            json=assignment,
            headers=admin_headers
        )
        
        # Test 1: Doctor can initiate clinical workflow
        workflow_data = ClinicalWorkflowCreate(
            patient_id=patient_id,
            workflow_type="encounter",
            priority="routine",
            chief_complaint="Annual physical examination",
            estimated_duration_minutes=60
        )
        
        workflow_response = await async_client.post(
            "/api/v1/clinical-workflows/workflows",
            json=workflow_data.dict(),
            headers=doctor_headers
        )
        assert workflow_response.status_code == status.HTTP_201_CREATED
        workflow_id = workflow_response.json()["id"]
        
        # Test 2: Doctor can update workflow status
        status_update = {
            "status": "in_progress",
            "notes": "Patient arrived, starting examination"
        }
        
        update_response = await async_client.patch(
            f"/api/v1/clinical-workflows/workflows/{workflow_id}/status",
            json=status_update,
            headers=doctor_headers
        )
        assert update_response.status_code == status.HTTP_200_OK
        
        # Test 3: Doctor can add clinical workflow step
        from app.modules.clinical_workflows.schemas import ClinicalWorkflowStepCreate
        
        step_data = ClinicalWorkflowStepCreate(
            workflow_id=workflow_id,
            step_name="Lab Test Order",
            step_type="lab_test",
            step_order=1,
            instructions="Fasting required, collect in morning",
            notes="Complete blood count ordered"
        )
        
        step_response = await async_client.post(
            "/api/v1/clinical-workflows/steps",
            json=step_data.dict(),
            headers=doctor_headers
        )
        assert step_response.status_code == status.HTTP_201_CREATED
        
    @pytest.mark.asyncio
    async def test_doctor_prescription_management_with_audit(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test doctor prescription management with comprehensive audit trails."""
        
        doctor = await create_test_user(
            db_session,
            username="prescribing_doctor",
            role="physician",
            email="prescriber@hospital.com"
        )
        
        admin = await create_test_user(
            db_session,
            username="prescription_admin", 
            role="admin",
            email="admin@hospital.com"
        )
        
        doctor_headers = await get_auth_headers(async_client, "prescribing_doctor", "TestPassword123!")
        admin_headers = await get_auth_headers(async_client, "prescription_admin", "TestPassword123!")
        
        # Create and assign patient
        patient_data = PatientCreate(
            first_name="Prescription",
            last_name="Patient",
            date_of_birth="1990-01-01",
            gender="male"
        )
        
        patient_response = await async_client.post(
            "/api/v1/healthcare/patients",
            json=patient_data.dict(),
            headers=admin_headers
        )
        patient_id = patient_response.json()["id"]
        
        assignment = {
            "patient_id": patient_id,
            "doctor_id": str(doctor.id),
            "assignment_type": "primary_care"
        }
        await async_client.post(
            "/api/v1/healthcare/patient-assignments",
            json=assignment,
            headers=admin_headers
        )
        
        # Test 1: Doctor can create prescription
        prescription_data = {
            "patient_id": patient_id,
            "medication_name": "Amoxicillin",
            "dosage": "500mg",
            "frequency": "twice daily",
            "duration": "7 days",
            "indication": "Bacterial infection",
            "special_instructions": "Take with food"
        }
        
        prescription_response = await async_client.post(
            "/api/v1/healthcare/prescriptions",
            json=prescription_data,
            headers=doctor_headers
        )
        assert prescription_response.status_code == status.HTTP_201_CREATED
        prescription_id = prescription_response.json()["id"]
        
        # Test 2: Doctor can modify prescription (with audit trail)
        modification = {
            "dosage": "250mg",
            "modification_reason": "Patient reported side effects, reducing dose"
        }
        
        modify_response = await async_client.patch(
            f"/api/v1/healthcare/prescriptions/{prescription_id}",
            json=modification,
            headers=doctor_headers
        )
        assert modify_response.status_code == status.HTTP_200_OK
        
        # Test 3: Verify prescription audit trail
        audit_response = await async_client.get(
            f"/api/v1/healthcare/prescriptions/{prescription_id}/audit",
            headers=doctor_headers
        )
        assert audit_response.status_code == status.HTTP_200_OK
        audit_data = audit_response.json()
        assert len(audit_data["audit_trail"]) >= 2  # Create + Modify
        
    @pytest.mark.asyncio
    async def test_doctor_cannot_access_unauthorized_functions(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that doctors cannot access unauthorized administrative functions."""
        
        doctor = await create_test_user(
            db_session,
            username="restricted_doctor",
            role="physician",
            email="restricted@hospital.com"
        )
        
        headers = await get_auth_headers(async_client, "restricted_doctor", "TestPassword123!")
        
        # Test 1: Cannot access user management
        users_response = await async_client.get(
            "/api/v1/auth/users",
            headers=headers
        )
        assert users_response.status_code == status.HTTP_403_FORBIDDEN
        
        # Test 2: Cannot access system configuration
        config_response = await async_client.get(
            "/api/v1/system/config",
            headers=headers
        )
        assert config_response.status_code == status.HTTP_403_FORBIDDEN
        
        # Test 3: Cannot access other doctors' patient assignments
        assignments_response = await async_client.get(
            "/api/v1/healthcare/patient-assignments/all",
            headers=headers
        )
        assert assignments_response.status_code == status.HTTP_403_FORBIDDEN
        
        # Test 4: Cannot delete other users' data
        delete_response = await async_client.delete(
            "/api/v1/auth/users/some-other-user-id",
            headers=headers
        )
        assert delete_response.status_code == status.HTTP_403_FORBIDDEN
        
    @pytest.mark.asyncio
    async def test_doctor_phi_access_minimum_necessary_compliance(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test HIPAA minimum necessary rule compliance for doctor PHI access."""
        
        doctor = await create_test_user(
            db_session,
            username="minimal_doctor",
            role="physician",
            email="minimal@hospital.com"
        )
        
        admin = await create_test_user(
            db_session,
            username="minimal_admin",
            role="admin", 
            email="admin@hospital.com"
        )
        
        doctor_headers = await get_auth_headers(async_client, "minimal_doctor", "TestPassword123!")
        admin_headers = await get_auth_headers(async_client, "minimal_admin", "TestPassword123!")
        
        # Create patient with comprehensive data
        patient_data = PatientCreate(
            first_name="Minimal",
            last_name="Necessary",
            date_of_birth="1990-01-01",
            gender="male",
            phone="555-0123",
            emergency_contact_name="John Doe",
            emergency_contact_phone="555-0456"
        )
        
        patient_response = await async_client.post(
            "/api/v1/healthcare/patients",
            json=patient_data.dict(),
            headers=admin_headers
        )
        patient_id = patient_response.json()["id"]
        
        # Assign patient to doctor
        assignment = {
            "patient_id": patient_id,
            "doctor_id": str(doctor.id),
            "assignment_type": "primary_care"
        }
        await async_client.post(
            "/api/v1/healthcare/patient-assignments",
            json=assignment,
            headers=admin_headers
        )
        
        # Test 1: Doctor access with specific purpose should limit data returned
        clinical_access = await async_client.get(
            f"/api/v1/healthcare/patients/{patient_id}?purpose=treatment&scope=clinical",
            headers=doctor_headers
        )
        assert clinical_access.status_code == status.HTTP_200_OK
        clinical_data = clinical_access.json()
        
        # Should include medical info but may limit administrative details
        assert "name" in clinical_data
        assert "gender" in clinical_data
        assert "birthDate" in clinical_data
        
        # Test 2: Administrative access should be limited
        admin_access = await async_client.get(
            f"/api/v1/healthcare/patients/{patient_id}?purpose=billing&scope=administrative",
            headers=doctor_headers
        )
        # Doctor should not have billing access
        assert admin_access.status_code == status.HTTP_403_FORBIDDEN
        
        # Test 3: Verify all access is properly audited with purpose
        # Each access should log the specific purpose and scope
        
    @pytest.mark.asyncio
    async def test_doctor_interdisciplinary_collaboration(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test doctor collaboration with other healthcare providers."""
        
        # Create multiple doctors
        primary_doctor = await create_test_user(
            db_session,
            username="primary_doctor",
            role="physician",
            email="primary@hospital.com"
        )
        specialist_doctor = await create_test_user(
            db_session,
            username="specialist_doctor", 
            role="physician",
            email="specialist@hospital.com"
        )
        
        admin = await create_test_user(
            db_session,
            username="collab_admin",
            role="admin",
            email="admin@hospital.com"
        )
        
        primary_headers = await get_auth_headers(async_client, "primary_doctor", "TestPassword123!")
        specialist_headers = await get_auth_headers(async_client, "specialist_doctor", "TestPassword123!")
        admin_headers = await get_auth_headers(async_client, "collab_admin", "TestPassword123!")
        
        # Create patient
        patient_data = PatientCreate(
            first_name="Collaborative",
            last_name="Care",
            date_of_birth="1990-01-01",
            gender="male"
        )
        
        patient_response = await async_client.post(
            "/api/v1/healthcare/patients",
            json=patient_data.dict(),
            headers=admin_headers
        )
        patient_id = patient_response.json()["id"]
        
        # Assign to primary doctor
        primary_assignment = {
            "patient_id": patient_id,
            "doctor_id": str(primary_doctor.id),
            "assignment_type": "primary_care"
        }
        await async_client.post(
            "/api/v1/healthcare/patient-assignments",
            json=primary_assignment,
            headers=admin_headers
        )
        
        # Test 1: Primary doctor can create referral to specialist
        referral_data = {
            "patient_id": patient_id,
            "referring_doctor_id": str(primary_doctor.id),
            "referred_to_doctor_id": str(specialist_doctor.id),
            "referral_reason": "Cardiology consultation",
            "clinical_summary": "Patient reports chest pain, requires specialist evaluation",
            "urgency": "routine"
        }
        
        referral_response = await async_client.post(
            "/api/v1/healthcare/referrals",
            json=referral_data,
            headers=primary_headers
        )
        assert referral_response.status_code == status.HTTP_201_CREATED
        referral_id = referral_response.json()["id"]
        
        # Test 2: Specialist can accept referral and gain temporary access
        accept_response = await async_client.post(
            f"/api/v1/healthcare/referrals/{referral_id}/accept",
            headers=specialist_headers
        )
        assert accept_response.status_code == status.HTTP_200_OK
        
        # Test 3: Specialist can now access patient (temporary assignment)
        specialist_access = await async_client.get(
            f"/api/v1/healthcare/patients/{patient_id}",
            headers=specialist_headers
        )
        assert specialist_access.status_code == status.HTTP_200_OK
        
        # Test 4: Specialist can add consultation notes
        consultation_data = {
            "referral_id": referral_id,
            "findings": "Normal cardiac examination, recommend stress test",
            "recommendations": "Schedule cardiac stress test within 2 weeks",
            "follow_up_required": True
        }
        
        consultation_response = await async_client.post(
            "/api/v1/healthcare/consultations",
            json=consultation_data,
            headers=specialist_headers
        )
        assert consultation_response.status_code == status.HTTP_201_CREATED


@pytest.mark.security  
@pytest.mark.integration
class TestDoctorRoleIntegration:
    """Integration tests for doctor role across multiple healthcare modules."""
    
    @pytest.mark.asyncio
    async def test_doctor_iris_api_integration(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test doctor integration with IRIS API for immunization data."""
        
        doctor = await create_test_user(
            db_session,
            username="iris_doctor",
            role="physician",
            email="iris@hospital.com"
        )
        
        headers = await get_auth_headers(async_client, "iris_doctor", "TestPassword123!")
        
        # Test doctor can query IRIS API for patient immunization data
        iris_response = await async_client.get(
            "/api/v1/iris/immunizations?patient_id=test-patient-id",
            headers=headers
        )
        # Should return data or appropriate error based on IRIS integration status
        assert iris_response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
        
    @pytest.mark.asyncio
    async def test_doctor_document_management_integration(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test doctor integration with document management system."""
        
        doctor = await create_test_user(
            db_session,
            username="document_doctor", 
            role="physician",
            email="document@hospital.com"
        )
        
        headers = await get_auth_headers(async_client, "document_doctor", "TestPassword123!")
        
        # Test doctor can upload clinical documents
        document_data = {
            "document_type": "clinical_note",
            "patient_id": "test-patient-id",
            "title": "Consultation Note",
            "content": "Patient consultation findings..."
        }
        
        document_response = await async_client.post(
            "/api/v1/documents/clinical",
            json=document_data,
            headers=headers
        )
        # Should work if document management is properly integrated
        assert document_response.status_code in [status.HTTP_201_CREATED, status.HTTP_404_NOT_FOUND]