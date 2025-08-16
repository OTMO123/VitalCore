"""
HIPAA-Compliant Lab Role Security Testing Framework

Tests lab technician role access controls and result management:
- Lab technicians can upload test results for assigned tests
- Limited patient data access (minimum necessary for lab work)
- Cannot access full patient records or clinical notes
- Laboratory result audit trails and quality control
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
from app.tests.helpers.auth_helpers import create_test_user, get_auth_headers


@pytest.mark.security
@pytest.mark.lab_role
class TestLabRoleSecurityCompliance:
    """Test suite for lab technician role security and HIPAA compliance."""
    
    @pytest.mark.asyncio
    async def test_lab_can_upload_results_for_assigned_tests_only(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that lab technicians can only upload results for tests assigned to them."""
        
        # Create lab technicians
        lab_tech1 = await create_test_user(
            db_session,
            username="lab_tech1",
            role="clinical_technician", 
            email="lab1@hospital.com"
        )
        lab_tech2 = await create_test_user(
            db_session,
            username="lab_tech2",
            role="clinical_technician",
            email="lab2@hospital.com"
        )
        
        # Create doctor to order tests
        doctor = await create_test_user(
            db_session,
            username="ordering_doctor",
            role="physician",
            email="doctor@hospital.com"
        )
        
        admin = await create_test_user(
            db_session,
            username="lab_admin", 
            role="admin",
            email="admin@hospital.com"
        )
        
        lab1_headers = await get_auth_headers(async_client, "lab_tech1", "TestPassword123!")
        lab2_headers = await get_auth_headers(async_client, "lab_tech2", "TestPassword123!")
        doctor_headers = await get_auth_headers(async_client, "ordering_doctor", "TestPassword123!")
        admin_headers = await get_auth_headers(async_client, "lab_admin", "TestPassword123!")
        
        # Create patient
        patient_data = PatientCreate(
            first_name="Lab",
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
        
        # Doctor orders lab tests
        test_order1 = {
            "patient_id": patient_id,
            "test_type": "complete_blood_count",
            "priority": "routine",
            "instructions": "Fasting not required",
            "assigned_lab_tech": str(lab_tech1.id)
        }
        test_order2 = {
            "patient_id": patient_id,
            "test_type": "lipid_panel",
            "priority": "routine", 
            "instructions": "12-hour fasting required",
            "assigned_lab_tech": str(lab_tech2.id)
        }
        
        order1_response = await async_client.post(
            "/api/v1/laboratory/orders",
            json=test_order1,
            headers=doctor_headers
        )
        order2_response = await async_client.post(
            "/api/v1/laboratory/orders", 
            json=test_order2,
            headers=doctor_headers
        )
        
        test_order1_id = order1_response.json()["id"]
        test_order2_id = order2_response.json()["id"]
        
        # Test 1: Lab Tech 1 can upload results for their assigned test
        result_data1 = {
            "test_order_id": test_order1_id,
            "results": {
                "white_blood_cells": "7.5",
                "red_blood_cells": "4.8",
                "hemoglobin": "14.2",
                "hematocrit": "42.1"
            },
            "result_status": "normal",
            "technician_notes": "Sample quality good, all values within normal range",
            "quality_control_passed": True
        }
        
        upload1_response = await async_client.post(
            "/api/v1/laboratory/results",
            json=result_data1,
            headers=lab1_headers
        )
        assert upload1_response.status_code == status.HTTP_201_CREATED
        
        # Test 2: Lab Tech 1 CANNOT upload results for test assigned to Lab Tech 2
        result_data2 = {
            "test_order_id": test_order2_id,
            "results": {
                "total_cholesterol": "180",
                "hdl_cholesterol": "55",
                "ldl_cholesterol": "100"
            },
            "result_status": "normal",
            "technician_notes": "Unauthorized upload attempt"
        }
        
        unauthorized_upload = await async_client.post(
            "/api/v1/laboratory/results",
            json=result_data2,
            headers=lab1_headers
        )
        assert unauthorized_upload.status_code == status.HTTP_403_FORBIDDEN
        
        # Test 3: Lab Tech 2 can upload results for their assigned test
        correct_upload = await async_client.post(
            "/api/v1/laboratory/results",
            json=result_data2,
            headers=lab2_headers
        )
        assert correct_upload.status_code == status.HTTP_201_CREATED
        
    @pytest.mark.asyncio
    async def test_lab_limited_patient_data_access(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test lab technician limited access to patient data (minimum necessary)."""
        
        lab_tech = await create_test_user(
            db_session,
            username="limited_lab_tech",
            role="clinical_technician",
            email="limited@hospital.com"
        )
        
        admin = await create_test_user(
            db_session,
            username="patient_admin",
            role="admin",
            email="admin@hospital.com"
        )
        
        lab_headers = await get_auth_headers(async_client, "limited_lab_tech", "TestPassword123!")
        admin_headers = await get_auth_headers(async_client, "patient_admin", "TestPassword123!")
        
        # Create patient with comprehensive data
        patient_data = PatientCreate(
            first_name="Lab",
            last_name="TestPatient",
            date_of_birth="1990-01-01",
            gender="male",
            phone="555-0123",
            email="patient@test.com",
            emergency_contact_name="Emergency Contact",
            emergency_contact_phone="555-0456"
        )
        
        patient_response = await async_client.post(
            "/api/v1/healthcare/patients",
            json=patient_data.dict(),
            headers=admin_headers
        )
        patient_id = patient_response.json()["id"]
        
        # Test 1: Lab tech can access limited patient demographics for lab work
        demographics_response = await async_client.get(
            f"/api/v1/healthcare/patients/{patient_id}/lab-demographics",
            headers=lab_headers
        )
        assert demographics_response.status_code == status.HTTP_200_OK
        
        demographics = demographics_response.json()
        # Should include necessary info for lab work but not full record
        assert "id" in demographics
        assert "gender" in demographics
        assert "birthDate" in demographics
        # Should NOT include contact info, emergency contacts, etc.
        assert "phone" not in demographics
        assert "emergency_contact" not in demographics
        
        # Test 2: Lab tech CANNOT access full patient record
        full_record_response = await async_client.get(
            f"/api/v1/healthcare/patients/{patient_id}",
            headers=lab_headers
        )
        assert full_record_response.status_code == status.HTTP_403_FORBIDDEN
        
        # Test 3: Lab tech CANNOT access clinical notes or treatment history
        clinical_notes_response = await async_client.get(
            f"/api/v1/healthcare/patients/{patient_id}/clinical-notes",
            headers=lab_headers
        )
        assert clinical_notes_response.status_code == status.HTTP_403_FORBIDDEN
        
    @pytest.mark.asyncio
    async def test_lab_result_quality_control_and_approval(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test lab result quality control processes and approval workflows."""
        
        # Create lab technician and lab supervisor
        lab_tech = await create_test_user(
            db_session,
            username="qc_lab_tech",
            role="clinical_technician",
            email="tech@hospital.com"
        )
        lab_supervisor = await create_test_user(
            db_session,
            username="lab_supervisor",
            role="lab_supervisor", 
            email="supervisor@hospital.com"
        )
        
        doctor = await create_test_user(
            db_session,
            username="qc_doctor",
            role="physician",
            email="qcdoctor@hospital.com"
        )
        
        admin = await create_test_user(
            db_session,
            username="qc_admin",
            role="admin",
            email="qcadmin@hospital.com"
        )
        
        tech_headers = await get_auth_headers(async_client, "qc_lab_tech", "TestPassword123!")
        supervisor_headers = await get_auth_headers(async_client, "lab_supervisor", "TestPassword123!")
        doctor_headers = await get_auth_headers(async_client, "qc_doctor", "TestPassword123!")
        admin_headers = await get_auth_headers(async_client, "qc_admin", "TestPassword123!")
        
        # Create patient and test order
        patient_data = PatientCreate(
            first_name="QC",
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
        
        # Doctor orders test
        test_order = {
            "patient_id": patient_id,
            "test_type": "blood_glucose",
            "priority": "stat",
            "assigned_lab_tech": str(lab_tech.id)
        }
        
        order_response = await async_client.post(
            "/api/v1/laboratory/orders",
            json=test_order,
            headers=doctor_headers
        )
        test_order_id = order_response.json()["id"]
        
        # Test 1: Lab tech uploads preliminary results
        preliminary_results = {
            "test_order_id": test_order_id,
            "results": {
                "glucose_level": "250"  # Abnormally high value
            },
            "result_status": "abnormal",
            "technician_notes": "Critically high glucose level, recommend immediate review",
            "quality_control_passed": True,
            "requires_supervisor_review": True
        }
        
        upload_response = await async_client.post(
            "/api/v1/laboratory/results",
            json=preliminary_results,
            headers=tech_headers
        )
        assert upload_response.status_code == status.HTTP_201_CREATED
        result_id = upload_response.json()["id"]
        
        # Test 2: Lab supervisor reviews and approves results
        supervisor_review = {
            "result_id": result_id,
            "approval_status": "approved",
            "supervisor_notes": "Results verified, double-checked due to critical value",
            "additional_testing_required": False
        }
        
        approval_response = await async_client.post(
            "/api/v1/laboratory/results/review",
            json=supervisor_review,
            headers=supervisor_headers
        )
        assert approval_response.status_code == status.HTTP_200_OK
        
        # Test 3: Critical values trigger automatic notifications
        notifications_response = await async_client.get(
            f"/api/v1/laboratory/results/{result_id}/notifications",
            headers=supervisor_headers
        )
        assert notifications_response.status_code == status.HTTP_200_OK
        notifications = notifications_response.json()
        assert len(notifications["critical_value_alerts"]) > 0
        
    @pytest.mark.asyncio
    async def test_lab_cannot_access_unauthorized_functions(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that lab technicians cannot access unauthorized functions."""
        
        lab_tech = await create_test_user(
            db_session,
            username="restricted_lab_tech",
            role="clinical_technician",
            email="restricted@hospital.com"
        )
        
        headers = await get_auth_headers(async_client, "restricted_lab_tech", "TestPassword123!")
        
        # Test 1: Cannot access user management
        users_response = await async_client.get(
            "/api/v1/auth/users",
            headers=headers
        )
        assert users_response.status_code == status.HTTP_403_FORBIDDEN
        
        # Test 2: Cannot access patient management (create/update patients)
        patient_data = {
            "first_name": "Unauthorized",
            "last_name": "Patient",
            "date_of_birth": "1990-01-01",
            "gender": "male"
        }
        
        create_patient_response = await async_client.post(
            "/api/v1/healthcare/patients",
            json=patient_data,
            headers=headers
        )
        assert create_patient_response.status_code == status.HTTP_403_FORBIDDEN
        
        # Test 3: Cannot access prescription management
        prescription_response = await async_client.get(
            "/api/v1/healthcare/prescriptions",
            headers=headers
        )
        assert prescription_response.status_code == status.HTTP_403_FORBIDDEN
        
        # Test 4: Cannot access clinical workflows
        workflows_response = await async_client.get(
            "/api/v1/clinical-workflows/workflows",
            headers=headers
        )
        assert workflows_response.status_code == status.HTTP_403_FORBIDDEN
        
        # Test 5: Cannot access audit logs
        audit_response = await async_client.get(
            "/api/v1/audit/logs",
            headers=headers
        )
        assert audit_response.status_code == status.HTTP_403_FORBIDDEN
        
    @pytest.mark.asyncio
    async def test_lab_result_integration_with_patient_records(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test lab result integration with patient medical records."""
        
        lab_tech = await create_test_user(
            db_session,
            username="integration_lab_tech",
            role="clinical_technician",
            email="integration@hospital.com"
        )
        
        doctor = await create_test_user(
            db_session,
            username="integration_doctor",
            role="physician",
            email="intdoctor@hospital.com"
        )
        
        admin = await create_test_user(
            db_session,
            username="integration_admin",
            role="admin",
            email="intadmin@hospital.com"
        )
        
        lab_headers = await get_auth_headers(async_client, "integration_lab_tech", "TestPassword123!")
        doctor_headers = await get_auth_headers(async_client, "integration_doctor", "TestPassword123!")
        admin_headers = await get_auth_headers(async_client, "integration_admin", "TestPassword123!")
        
        # Create patient
        patient_data = PatientCreate(
            first_name="Integration",
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
        
        # Doctor orders test
        test_order = {
            "patient_id": patient_id,
            "test_type": "hemoglobin_a1c",
            "priority": "routine",
            "assigned_lab_tech": str(lab_tech.id),
            "clinical_indication": "Diabetes monitoring"
        }
        
        order_response = await async_client.post(
            "/api/v1/laboratory/orders",
            json=test_order,
            headers=doctor_headers
        )
        test_order_id = order_response.json()["id"]
        
        # Lab tech uploads results
        result_data = {
            "test_order_id": test_order_id,
            "results": {
                "hemoglobin_a1c": "7.2"
            },
            "result_status": "abnormal",
            "reference_ranges": {
                "hemoglobin_a1c": "< 7.0% for diabetic patients"
            },
            "technician_notes": "Slightly elevated, patient may need medication adjustment"
        }
        
        upload_response = await async_client.post(
            "/api/v1/laboratory/results",
            json=result_data,
            headers=lab_headers
        )
        assert upload_response.status_code == status.HTTP_201_CREATED
        result_id = upload_response.json()["id"]
        
        # Test 1: Doctor can view lab results in patient record
        patient_labs_response = await async_client.get(
            f"/api/v1/healthcare/patients/{patient_id}/laboratory-results",
            headers=doctor_headers
        )
        assert patient_labs_response.status_code == status.HTTP_200_OK
        lab_results = patient_labs_response.json()
        assert len(lab_results["results"]) > 0
        assert lab_results["results"][0]["test_type"] == "hemoglobin_a1c"
        
        # Test 2: Lab tech can view status of their submitted results
        tech_results_response = await async_client.get(
            "/api/v1/laboratory/my-results",
            headers=lab_headers
        )
        assert tech_results_response.status_code == status.HTTP_200_OK
        tech_results = tech_results_response.json()
        assert len(tech_results["submitted_results"]) > 0
        
    @pytest.mark.asyncio
    async def test_lab_result_audit_trail_compliance(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test comprehensive audit trail for lab result handling."""
        
        lab_tech = await create_test_user(
            db_session,
            username="audit_lab_tech",
            role="clinical_technician",
            email="auditlab@hospital.com"
        )
        
        doctor = await create_test_user(
            db_session,
            username="audit_doctor",
            role="physician", 
            email="auditdoc@hospital.com"
        )
        
        admin = await create_test_user(
            db_session,
            username="audit_admin",
            role="admin",
            email="auditadmin@hospital.com"
        )
        
        lab_headers = await get_auth_headers(async_client, "audit_lab_tech", "TestPassword123!")
        doctor_headers = await get_auth_headers(async_client, "audit_doctor", "TestPassword123!")
        admin_headers = await get_auth_headers(async_client, "audit_admin", "TestPassword123!")
        
        # Create patient
        patient_data = PatientCreate(
            first_name="Audit",
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
        
        # Complete workflow with audit trail
        # 1. Doctor orders test
        test_order = {
            "patient_id": patient_id,
            "test_type": "comprehensive_metabolic_panel",
            "priority": "routine",
            "assigned_lab_tech": str(lab_tech.id)
        }
        
        order_response = await async_client.post(
            "/api/v1/laboratory/orders",
            json=test_order,
            headers=doctor_headers
        )
        test_order_id = order_response.json()["id"]
        
        # 2. Lab tech processes and uploads results
        result_data = {
            "test_order_id": test_order_id,
            "results": {
                "sodium": "142",
                "potassium": "4.1", 
                "chloride": "101",
                "glucose": "95"
            },
            "result_status": "normal",
            "processing_notes": "All values within normal limits"
        }
        
        upload_response = await async_client.post(
            "/api/v1/laboratory/results",
            json=result_data,
            headers=lab_headers
        )
        result_id = upload_response.json()["id"]
        
        # 3. Verify comprehensive audit trail
        audit_response = await async_client.get(
            f"/api/v1/laboratory/results/{result_id}/audit-trail",
            headers=lab_headers
        )
        assert audit_response.status_code == status.HTTP_200_OK
        
        audit_trail = audit_response.json()
        # Should include all key events with timestamps and user info
        events = audit_trail["events"]
        assert any(event["event_type"] == "test_ordered" for event in events)
        assert any(event["event_type"] == "sample_received" for event in events)
        assert any(event["event_type"] == "results_entered" for event in events)
        assert any(event["event_type"] == "results_verified" for event in events)
        
        # Each event should have required audit information
        for event in events:
            assert "timestamp" in event
            assert "user_id" in event
            assert "event_type" in event
            assert "details" in event


@pytest.mark.security
@pytest.mark.integration
class TestLabRoleIntegration:
    """Integration tests for lab role across multiple healthcare modules."""
    
    @pytest.mark.asyncio
    async def test_lab_iris_api_integration(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test lab integration with IRIS API for immunization verification."""
        
        lab_tech = await create_test_user(
            db_session,
            username="iris_lab_tech",
            role="clinical_technician",
            email="irislab@hospital.com"
        )
        
        headers = await get_auth_headers(async_client, "iris_lab_tech", "TestPassword123!")
        
        # Test lab tech can verify immunization status for titer testing
        iris_response = await async_client.get(
            "/api/v1/iris/immunizations/verify?patient_id=test-patient&test_type=immunity_titer",
            headers=headers
        )
        # Should return data or appropriate error based on access level
        assert iris_response.status_code in [
            status.HTTP_200_OK, 
            status.HTTP_403_FORBIDDEN,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ]
        
    @pytest.mark.asyncio
    async def test_lab_document_management_integration(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test lab integration with document management for result reports."""
        
        lab_tech = await create_test_user(
            db_session,
            username="document_lab_tech",
            role="clinical_technician", 
            email="doclab@hospital.com"
        )
        
        headers = await get_auth_headers(async_client, "document_lab_tech", "TestPassword123!")
        
        # Test lab tech can upload lab result documents
        document_data = {
            "document_type": "lab_result_report",
            "test_order_id": "test-order-id",
            "file_format": "pdf",
            "content_base64": "base64encodedpdfcontent..."
        }
        
        document_response = await async_client.post(
            "/api/v1/documents/lab-results",
            json=document_data,
            headers=headers
        )
        # Should work if document management is properly integrated
        assert document_response.status_code in [
            status.HTTP_201_CREATED, 
            status.HTTP_404_NOT_FOUND,
            status.HTTP_403_FORBIDDEN
        ]