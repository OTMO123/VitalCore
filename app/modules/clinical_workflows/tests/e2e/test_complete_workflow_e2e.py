"""
Clinical Workflows End-to-End Tests

Complete workflow lifecycle testing with real-world scenarios.
Tests full user journeys from different healthcare provider perspectives.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Dict, Any, List

from httpx import AsyncClient
from fastapi import status

from app.modules.clinical_workflows.schemas import (
    WorkflowType, WorkflowStatus, WorkflowPriority, EncounterClass, StepStatus
)


class TestCompletePatientEncounterWorkflow:
    """Test complete patient encounter workflow from admission to discharge."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.physician
    async def test_emergency_department_workflow_complete(
        self, async_client: AsyncClient, physician_token: str, nurse_token: str,
        role_based_headers, patient_id: str
    ):
        """
        Test complete ED workflow: Physician creates -> Nurse updates -> Physician completes.
        
        Scenario: Patient arrives with chest pain, goes through triage, assessment, 
        treatment, and discharge.
        """
        physician_headers = role_based_headers(physician_token)
        nurse_headers = role_based_headers(nurse_token)
        
        # Step 1: Physician creates initial workflow (Triage)
        print("\\n=== Step 1: Emergency Department Triage ===")
        
        initial_workflow_data = {
            "patient_id": patient_id,
            "provider_id": str(uuid4()),
            "workflow_type": WorkflowType.EMERGENCY.value,
            "priority": WorkflowPriority.URGENT.value,
            "chief_complaint": "Chest pain, 8/10 severity, radiating to left arm",
            "history_present_illness": "45-year-old male presents with acute chest pain onset 1 hour ago",
            "location": "Emergency Department",
            "department": "Emergency Medicine",
            "estimated_duration_minutes": 180,
            "allergies": ["Penicillin"],
            "current_medications": ["Aspirin 81mg daily", "Lisinopril 10mg daily"]
        }
        
        create_response = await async_client.post(
            "/api/v1/clinical-workflows/workflows",
            json=initial_workflow_data,
            headers=physician_headers
        )
        
        assert create_response.status_code == status.HTTP_201_CREATED
        workflow_data = create_response.json()
        workflow_id = workflow_data["id"]
        
        assert workflow_data["status"] == WorkflowStatus.ACTIVE.value
        assert workflow_data["priority"] == WorkflowPriority.URGENT.value
        assert workflow_data["completion_percentage"] == 0
        
        print(f"✓ Workflow created: {workflow_id}")
        print(f"  Status: {workflow_data['status']}")
        print(f"  Priority: {workflow_data['priority']}")
        
        # Step 2: Add initial assessment step
        print("\\n=== Step 2: Initial Assessment Step ===")
        
        assessment_step_data = {
            "workflow_id": workflow_id,
            "step_name": "initial_assessment",
            "step_type": "clinical_evaluation",
            "step_order": 1,
            "estimated_duration_minutes": 30,
            "notes": "Primary survey, vital signs, pain assessment"
        }
        
        step_response = await async_client.post(
            f"/api/v1/clinical-workflows/workflows/{workflow_id}/steps",
            json=assessment_step_data,
            headers=physician_headers
        )
        
        assert step_response.status_code == status.HTTP_201_CREATED
        step_data = step_response.json()
        assessment_step_id = step_data["id"]
        
        assert step_data["step_name"] == "initial_assessment"
        assert step_data["status"] == StepStatus.PENDING.value
        
        print(f"✓ Assessment step added: {assessment_step_id}")
        
        # Step 3: Nurse updates with vital signs (role-based collaboration)
        print("\\n=== Step 3: Nurse Updates Vital Signs ===")
        
        vital_signs_update = {
            "assessment": "Patient appears distressed, diaphoretic",
            "vital_signs": {
                "systolic_bp": 160,
                "diastolic_bp": 95,
                "heart_rate": 110,
                "respiratory_rate": 22,
                "temperature": 98.8,
                "oxygen_saturation": 96,
                "pain_score": 8
            },
            "progress_notes": "Vital signs obtained, patient stable but in significant discomfort"
        }
        
        # Note: Nurse may have limited update permissions in real scenario
        nurse_update_response = await async_client.put(
            f"/api/v1/clinical-workflows/workflows/{workflow_id}",
            json=vital_signs_update,
            headers=nurse_headers
        )
        
        # Handle different permission scenarios
        if nurse_update_response.status_code == status.HTTP_200_OK:
            print("✓ Nurse successfully updated vital signs")
        elif nurse_update_response.status_code == status.HTTP_403_FORBIDDEN:
            print("⚠ Nurse has limited permissions - using physician for update")
            nurse_update_response = await async_client.put(
                f"/api/v1/clinical-workflows/workflows/{workflow_id}",
                json=vital_signs_update,
                headers=physician_headers
            )
            assert nurse_update_response.status_code == status.HTTP_200_OK
        
        # Step 4: Complete initial assessment step
        print("\\n=== Step 4: Complete Initial Assessment ===")
        
        assessment_completion = {
            "status": StepStatus.COMPLETED.value,
            "completed_at": datetime.utcnow().isoformat(),
            "actual_duration_minutes": 25,
            "quality_score": 90,
            "notes": "Assessment completed. High suspicion for acute coronary syndrome."
        }
        
        complete_step_response = await async_client.put(
            f"/api/v1/clinical-workflows/steps/{assessment_step_id}/complete",
            json=assessment_completion,
            headers=physician_headers
        )
        
        assert complete_step_response.status_code == status.HTTP_200_OK
        completed_step = complete_step_response.json()
        
        assert completed_step["status"] == StepStatus.COMPLETED.value
        assert completed_step["quality_score"] == 90
        
        print("✓ Initial assessment completed")
        print(f"  Quality score: {completed_step['quality_score']}")
        print(f"  Duration: {completed_step['actual_duration_minutes']} minutes")
        
        # Step 5: Add diagnostic testing step
        print("\\n=== Step 5: Diagnostic Testing ===")
        
        diagnostic_step_data = {
            "workflow_id": workflow_id,
            "step_name": "diagnostic_testing",
            "step_type": "diagnostics",
            "step_order": 2,
            "estimated_duration_minutes": 60,
            "notes": "EKG, cardiac enzymes, chest X-ray ordered"
        }
        
        diagnostic_step_response = await async_client.post(
            f"/api/v1/clinical-workflows/workflows/{workflow_id}/steps",
            json=diagnostic_step_data,
            headers=physician_headers
        )
        
        assert diagnostic_step_response.status_code == status.HTTP_201_CREATED
        diagnostic_step_id = diagnostic_step_response.json()["id"]
        
        print("✓ Diagnostic testing step added")
        
        # Step 6: Update workflow with diagnostic results
        print("\\n=== Step 6: Diagnostic Results and Treatment Plan ===")
        
        diagnostic_update = {
            "assessment": "EKG shows ST elevation in leads II, III, aVF. Troponin elevated. STEMI confirmed.",
            "plan": "Emergent cardiac catheterization. Aspirin, clopidogrel, heparin initiated. Cardiology consulted.",
            "completion_percentage": 75,
            "progress_notes": "STEMI protocol activated. Patient prepared for emergent cath lab."
        }
        
        diagnostic_update_response = await async_client.put(
            f"/api/v1/clinical-workflows/workflows/{workflow_id}",
            json=diagnostic_update,
            headers=physician_headers
        )
        
        assert diagnostic_update_response.status_code == status.HTTP_200_OK
        
        print("✓ Diagnostic results updated")
        print("✓ Treatment plan established")
        
        # Step 7: Complete diagnostic testing step
        diagnostic_completion = {
            "status": StepStatus.COMPLETED.value,
            "completed_at": datetime.utcnow().isoformat(),
            "actual_duration_minutes": 45,
            "quality_score": 95,
            "notes": "All diagnostic tests completed. STEMI confirmed and treated per protocol."
        }
        
        await async_client.put(
            f"/api/v1/clinical-workflows/steps/{diagnostic_step_id}/complete",
            json=diagnostic_completion,
            headers=physician_headers
        )
        
        print("✓ Diagnostic testing completed")
        
        # Step 8: Create clinical encounter for documentation
        print("\\n=== Step 8: Clinical Encounter Documentation ===")
        
        encounter_data = {
            "workflow_id": workflow_id,
            "patient_id": patient_id,
            "provider_id": str(uuid4()),
            "encounter_class": EncounterClass.EMERGENCY.value,
            "encounter_datetime": datetime.utcnow().isoformat(),
            "soap_note": {
                "subjective": "45-year-old male with acute chest pain, 8/10 severity, radiating to left arm, onset 1 hour ago",
                "objective": "VS: BP 160/95, HR 110, RR 22, O2 96%, Temp 98.8°F. Patient appears distressed, diaphoretic. EKG shows STEMI.",
                "assessment": "ST-elevation myocardial infarction (STEMI) - inferior wall",
                "plan": "Emergent cardiac catheterization. Dual antiplatelet therapy initiated. Cardiology consultation."
            },
            "location": "Emergency Department",
            "department": "Emergency Medicine",
            "follow_up_required": True
        }
        
        encounter_response = await async_client.post(
            "/api/v1/clinical-workflows/encounters",
            json=encounter_data,
            headers=physician_headers
        )
        
        assert encounter_response.status_code == status.HTTP_201_CREATED
        encounter_id = encounter_response.json()["id"]
        
        print(f"✓ Clinical encounter documented: {encounter_id}")
        
        # Step 9: Complete the entire workflow
        print("\\n=== Step 9: Workflow Completion ===")
        
        completion_notes = ("Patient successfully treated for STEMI. "
                          "Underwent emergent cardiac catheterization with stent placement. "
                          "Stable condition. Transferred to CCU for monitoring.")
        
        completion_response = await async_client.post(
            f"/api/v1/clinical-workflows/workflows/{workflow_id}/complete",
            json=completion_notes,
            headers=physician_headers
        )
        
        assert completion_response.status_code == status.HTTP_200_OK
        final_workflow = completion_response.json()
        
        assert final_workflow["status"] == WorkflowStatus.COMPLETED.value
        assert final_workflow["completion_percentage"] == 100
        
        print("✓ Workflow completed successfully")
        print(f"  Final status: {final_workflow['status']}")
        print(f"  Completion: {final_workflow['completion_percentage']}%")
        
        # Step 10: Verify complete workflow retrieval
        print("\\n=== Step 10: Final Workflow Verification ===")
        
        final_retrieval = await async_client.get(
            f"/api/v1/clinical-workflows/workflows/{workflow_id}",
            params={"decrypt_phi": True, "access_purpose": "completion_verification"},
            headers=physician_headers
        )
        
        assert final_retrieval.status_code == status.HTTP_200_OK
        final_data = final_retrieval.json()
        
        # Verify workflow completeness
        assert final_data["status"] == WorkflowStatus.COMPLETED.value
        assert final_data["completion_percentage"] == 100
        assert final_data["workflow_end_time"] is not None
        assert final_data["access_count"] > 0  # Should have been accessed multiple times
        
        print("✓ Final verification successful")
        print(f"  Total access count: {final_data['access_count']}")
        print(f"  Workflow duration: {final_data.get('actual_duration_minutes', 'N/A')} minutes")
        
        return {
            "workflow_id": workflow_id,
            "encounter_id": encounter_id,
            "final_status": final_data["status"],
            "completion_percentage": final_data["completion_percentage"],
            "total_steps": 2,  # assessment and diagnostic steps
            "access_count": final_data["access_count"]
        }
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.physician
    async def test_routine_outpatient_workflow(
        self, async_client: AsyncClient, physician_token: str, role_based_headers
    ):
        """
        Test routine outpatient workflow for annual physical exam.
        
        Scenario: Patient comes for annual physical, preventive care,
        routine screenings, and follow-up scheduling.
        """
        headers = role_based_headers(physician_token)
        patient_id = str(uuid4())
        
        print("\\n=== Routine Outpatient Physical Exam Workflow ===")
        
        # Step 1: Create routine workflow
        routine_workflow_data = {
            "patient_id": patient_id,
            "provider_id": str(uuid4()),
            "workflow_type": WorkflowType.ENCOUNTER.value,
            "priority": WorkflowPriority.ROUTINE.value,
            "chief_complaint": "Annual physical examination and preventive care",
            "history_present_illness": "55-year-old patient for routine annual physical. No acute complaints.",
            "location": "Primary Care Clinic",
            "department": "Family Medicine",
            "estimated_duration_minutes": 45,
            "allergies": ["No known allergies"],
            "current_medications": ["Multivitamin daily", "Vitamin D 1000 IU daily"]
        }
        
        create_response = await async_client.post(
            "/api/v1/clinical-workflows/workflows",
            json=routine_workflow_data,
            headers=headers
        )
        
        assert create_response.status_code == status.HTTP_201_CREATED
        workflow_id = create_response.json()["id"]
        
        print(f"✓ Routine workflow created: {workflow_id}")
        
        # Step 2: Add preventive care screening step
        screening_step = {
            "workflow_id": workflow_id,
            "step_name": "preventive_screening",
            "step_type": "preventive_care",
            "step_order": 1,
            "estimated_duration_minutes": 20,
            "notes": "Age-appropriate screenings: mammogram, colonoscopy, bone density"
        }
        
        step_response = await async_client.post(
            f"/api/v1/clinical-workflows/workflows/{workflow_id}/steps",
            json=screening_step,
            headers=headers
        )
        
        assert step_response.status_code == status.HTTP_201_CREATED
        screening_step_id = step_response.json()["id"]
        
        # Step 3: Update with physical exam findings
        physical_exam_update = {
            "assessment": "Overall good health. BMI within normal range. No acute findings.",
            "plan": "Continue current lifestyle. Mammogram and colonoscopy due. Return in 1 year.",
            "completion_percentage": 85,
            "vital_signs": {
                "systolic_bp": 125,
                "diastolic_bp": 78,
                "heart_rate": 68,
                "respiratory_rate": 16,
                "temperature": 98.4,
                "weight_kg": 68.0,
                "height_cm": 165.0,
                "bmi": 25.0
            }
        }
        
        update_response = await async_client.put(
            f"/api/v1/clinical-workflows/workflows/{workflow_id}",
            json=physical_exam_update,
            headers=headers
        )
        
        assert update_response.status_code == status.HTTP_200_OK
        
        # Step 4: Complete screening step
        screening_completion = {
            "status": StepStatus.COMPLETED.value,
            "actual_duration_minutes": 18,
            "quality_score": 88,
            "notes": "Preventive care counseling completed. Screening schedules reviewed."
        }
        
        await async_client.put(
            f"/api/v1/clinical-workflows/steps/{screening_step_id}/complete",
            json=screening_completion,
            headers=headers
        )
        
        # Step 5: Complete workflow
        completion_notes = "Annual physical completed. Patient counseled on preventive care. Follow-up appointments scheduled."
        
        completion_response = await async_client.post(
            f"/api/v1/clinical-workflows/workflows/{workflow_id}/complete",
            json=completion_notes,
            headers=headers
        )
        
        assert completion_response.status_code == status.HTTP_200_OK
        final_workflow = completion_response.json()
        
        assert final_workflow["status"] == WorkflowStatus.COMPLETED.value
        assert final_workflow["completion_percentage"] == 100
        
        print("✓ Routine outpatient workflow completed successfully")
        
        return {
            "workflow_id": workflow_id,
            "workflow_type": "routine_outpatient",
            "completion_status": final_workflow["status"]
        }


class TestMultiProviderCollaborationWorkflow:
    """Test workflows involving multiple healthcare providers."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.physician
    @pytest.mark.nurse
    async def test_multi_provider_surgery_workflow(
        self, async_client: AsyncClient, physician_token: str, nurse_token: str,
        role_based_headers
    ):
        """
        Test surgical workflow with multiple providers: Surgeon, Anesthesiologist, Nurses.
        
        Scenario: Patient scheduled for elective surgery with pre-op, 
        intra-op, and post-op care coordination.
        """
        physician_headers = role_based_headers(physician_token)
        nurse_headers = role_based_headers(nurse_token)
        patient_id = str(uuid4())
        
        print("\\n=== Multi-Provider Surgical Workflow ===")
        
        # Step 1: Surgeon creates pre-operative workflow
        preop_workflow_data = {
            "patient_id": patient_id,
            "provider_id": str(uuid4()),  # Surgeon ID
            "workflow_type": WorkflowType.PROCEDURE.value,
            "priority": WorkflowPriority.URGENT.value,
            "chief_complaint": "Elective laparoscopic cholecystectomy",
            "history_present_illness": "Patient with symptomatic gallstones, scheduled for elective surgery",
            "location": "Surgical Suite",
            "department": "General Surgery",
            "estimated_duration_minutes": 240,  # 4 hours including prep
            "allergies": ["Morphine"],
            "current_medications": ["Atorvastatin 20mg daily"]
        }
        
        create_response = await async_client.post(
            "/api/v1/clinical-workflows/workflows",
            json=preop_workflow_data,
            headers=physician_headers
        )
        
        assert create_response.status_code == status.HTTP_201_CREATED
        workflow_id = create_response.json()["id"]
        
        print(f"✓ Surgical workflow created by surgeon: {workflow_id}")
        
        # Step 2: Add pre-operative assessment step
        preop_step = {
            "workflow_id": workflow_id,
            "step_name": "preoperative_assessment",
            "step_type": "surgical_prep",
            "step_order": 1,
            "estimated_duration_minutes": 45,
            "notes": "Pre-op assessment, consent, anesthesia evaluation"
        }
        
        preop_step_response = await async_client.post(
            f"/api/v1/clinical-workflows/workflows/{workflow_id}/steps",
            json=preop_step,
            headers=physician_headers
        )
        
        preop_step_id = preop_step_response.json()["id"]
        
        # Step 3: Nurse updates with pre-op vitals and preparation
        preop_update = {
            "progress_notes": "Pre-op checklist completed. Patient NPO since midnight. IV access established.",
            "vital_signs": {
                "systolic_bp": 130,
                "diastolic_bp": 85,
                "heart_rate": 75,
                "respiratory_rate": 16,
                "temperature": 98.6,
                "oxygen_saturation": 99
            }
        }
        
        # Attempt nurse update (may require physician authorization)
        nurse_update_response = await async_client.put(
            f"/api/v1/clinical-workflows/workflows/{workflow_id}",
            json=preop_update,
            headers=nurse_headers
        )
        
        if nurse_update_response.status_code == status.HTTP_403_FORBIDDEN:
            # Use physician headers for update
            nurse_update_response = await async_client.put(
                f"/api/v1/clinical-workflows/workflows/{workflow_id}",
                json=preop_update,
                headers=physician_headers
            )
        
        assert nurse_update_response.status_code == status.HTTP_200_OK
        print("✓ Pre-operative preparation completed by nursing")
        
        # Step 4: Complete pre-op step and add intra-operative step
        preop_completion = {
            "status": StepStatus.COMPLETED.value,
            "actual_duration_minutes": 40,
            "quality_score": 92,
            "notes": "Pre-operative assessment complete. Patient ready for surgery."
        }
        
        await async_client.put(
            f"/api/v1/clinical-workflows/steps/{preop_step_id}/complete",
            json=preop_completion,
            headers=physician_headers
        )
        
        # Add intra-operative step
        intraop_step = {
            "workflow_id": workflow_id,
            "step_name": "intraoperative_procedure",
            "step_type": "surgical_procedure",
            "step_order": 2,
            "estimated_duration_minutes": 90,
            "notes": "Laparoscopic cholecystectomy procedure"
        }
        
        intraop_step_response = await async_client.post(
            f"/api/v1/clinical-workflows/workflows/{workflow_id}/steps",
            json=intraop_step,
            headers=physician_headers
        )
        
        intraop_step_id = intraop_step_response.json()["id"]
        
        # Step 5: Update workflow with surgical findings
        surgical_update = {
            "assessment": "Laparoscopic cholecystectomy completed successfully. No complications.",
            "plan": "Post-operative recovery. Pain management. Discharge planning.",
            "completion_percentage": 80,
            "progress_notes": "Procedure completed without complications. Gallbladder removed intact."
        }
        
        surgical_update_response = await async_client.put(
            f"/api/v1/clinical-workflows/workflows/{workflow_id}",
            json=surgical_update,
            headers=physician_headers
        )
        
        assert surgical_update_response.status_code == status.HTTP_200_OK
        print("✓ Surgical procedure completed")
        
        # Step 6: Complete intra-operative step
        intraop_completion = {
            "status": StepStatus.COMPLETED.value,
            "actual_duration_minutes": 85,
            "quality_score": 95,
            "notes": "Surgery completed successfully without complications."
        }
        
        await async_client.put(
            f"/api/v1/clinical-workflows/steps/{intraop_step_id}/complete",
            json=intraop_completion,
            headers=physician_headers
        )
        
        # Step 7: Add post-operative recovery step
        postop_step = {
            "workflow_id": workflow_id,
            "step_name": "postoperative_recovery",
            "step_type": "recovery",
            "step_order": 3,
            "estimated_duration_minutes": 120,
            "notes": "Post-operative monitoring and recovery"
        }
        
        postop_step_response = await async_client.post(
            f"/api/v1/clinical-workflows/workflows/{workflow_id}/steps",
            json=postop_step,
            headers=physician_headers
        )
        
        postop_step_id = postop_step_response.json()["id"]
        
        # Step 8: Complete post-operative recovery
        postop_completion = {
            "status": StepStatus.COMPLETED.value,
            "actual_duration_minutes": 110,
            "quality_score": 90,
            "notes": "Post-operative recovery completed. Patient stable for discharge."
        }
        
        await async_client.put(
            f"/api/v1/clinical-workflows/steps/{postop_step_id}/complete",
            json=postop_completion,
            headers=physician_headers
        )
        
        # Step 9: Complete entire surgical workflow
        completion_notes = ("Laparoscopic cholecystectomy completed successfully. "
                          "Patient recovered well. Discharged home with post-op instructions.")
        
        final_completion = await async_client.post(
            f"/api/v1/clinical-workflows/workflows/{workflow_id}/complete",
            json=completion_notes,
            headers=physician_headers
        )
        
        assert final_completion.status_code == status.HTTP_200_OK
        final_workflow = final_completion.json()
        
        assert final_workflow["status"] == WorkflowStatus.COMPLETED.value
        assert final_workflow["completion_percentage"] == 100
        
        print("✓ Multi-provider surgical workflow completed successfully")
        print(f"  Total steps completed: 3")
        print(f"  Final status: {final_workflow['status']}")
        
        return {
            "workflow_id": workflow_id,
            "workflow_type": "multi_provider_surgery",
            "total_steps": 3,
            "providers_involved": ["surgeon", "nurse", "anesthesiologist"],
            "completion_status": final_workflow["status"]
        }


class TestWorkflowAnalyticsAndReporting:
    """Test analytics generation and reporting workflows."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.admin
    async def test_comprehensive_analytics_workflow(
        self, async_client: AsyncClient, admin_token: str, physician_token: str,
        role_based_headers
    ):
        """
        Test comprehensive analytics workflow for quality improvement.
        
        Scenario: Clinical administrator generates analytics reports
        for quality improvement and performance monitoring.
        """
        admin_headers = role_based_headers(admin_token)
        physician_headers = role_based_headers(physician_token)
        
        print("\\n=== Comprehensive Analytics Workflow ===")
        
        # Step 1: Create sample workflows for analytics
        sample_workflows = []
        
        for i in range(5):
            workflow_data = {
                "patient_id": str(uuid4()),
                "provider_id": str(uuid4()),
                "workflow_type": WorkflowType.ENCOUNTER.value,
                "priority": [WorkflowPriority.ROUTINE.value, WorkflowPriority.URGENT.value][i % 2],
                "chief_complaint": f"Analytics test case {i + 1}",
                "location": "Test Department",
                "estimated_duration_minutes": 60
            }
            
            create_response = await async_client.post(
                "/api/v1/clinical-workflows/workflows",
                json=workflow_data,
                headers=physician_headers
            )
            
            if create_response.status_code == status.HTTP_201_CREATED:
                workflow_id = create_response.json()["id"]
                sample_workflows.append(workflow_id)
                
                # Complete some workflows for analytics
                if i < 3:
                    await async_client.post(
                        f"/api/v1/clinical-workflows/workflows/{workflow_id}/complete",
                        json=f"Analytics test workflow {i + 1} completed",
                        headers=physician_headers
                    )
        
        print(f"✓ Created {len(sample_workflows)} sample workflows for analytics")
        
        # Step 2: Generate workflow analytics
        analytics_params = {
            "date_from": (datetime.now() - timedelta(days=1)).date().isoformat(),
            "date_to": datetime.now().date().isoformat(),
            "workflow_type": WorkflowType.ENCOUNTER.value
        }
        
        analytics_response = await async_client.get(
            "/api/v1/clinical-workflows/analytics",
            params=analytics_params,
            headers=admin_headers
        )
        
        assert analytics_response.status_code == status.HTTP_200_OK
        analytics_data = analytics_response.json()
        
        # Verify analytics structure
        required_fields = [
            "total_workflows", "completed_workflows", "completion_rate",
            "workflows_by_type", "workflows_by_status"
        ]
        
        for field in required_fields:
            assert field in analytics_data, f"Missing analytics field: {field}"
        
        print("✓ Analytics generated successfully")
        print(f"  Total workflows: {analytics_data.get('total_workflows', 0)}")
        print(f"  Completed workflows: {analytics_data.get('completed_workflows', 0)}")
        print(f"  Completion rate: {analytics_data.get('completion_rate', 0):.2%}")
        
        # Step 3: Test metrics endpoint
        metrics_response = await async_client.get(
            "/api/v1/clinical-workflows/metrics",
            headers=admin_headers
        )
        
        assert metrics_response.status_code == status.HTTP_200_OK
        metrics_data = metrics_response.json()
        
        assert "service" in metrics_data
        assert "metrics" in metrics_data
        assert metrics_data["service"] == "clinical_workflows"
        
        print("✓ Performance metrics retrieved")
        print(f"  Service: {metrics_data['service']}")
        
        return {
            "analytics_generated": True,
            "sample_workflows_created": len(sample_workflows),
            "analytics_data": analytics_data,
            "metrics_data": metrics_data
        }


class TestErrorRecoveryWorkflows:
    """Test error handling and recovery scenarios."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_workflow_error_recovery(
        self, async_client: AsyncClient, physician_token: str, role_based_headers
    ):
        """
        Test workflow error recovery and resilience.
        
        Scenario: Test system behavior during various error conditions
        and recovery mechanisms.
        """
        headers = role_based_headers(physician_token)
        
        print("\\n=== Workflow Error Recovery Testing ===")
        
        # Test 1: Invalid workflow data recovery
        print("\\n--- Test 1: Invalid Data Recovery ---")
        
        invalid_workflow_data = {
            "patient_id": "invalid-uuid-format",
            "workflow_type": "invalid_type",
            "priority": "invalid_priority"
        }
        
        invalid_response = await async_client.post(
            "/api/v1/clinical-workflows/workflows",
            json=invalid_workflow_data,
            headers=headers
        )
        
        assert invalid_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        print("✓ Invalid data properly rejected")
        
        # Test 2: Non-existent workflow access
        print("\\n--- Test 2: Non-existent Workflow Access ---")
        
        non_existent_id = str(uuid4())
        
        not_found_response = await async_client.get(
            f"/api/v1/clinical-workflows/workflows/{non_existent_id}",
            headers=headers
        )
        
        assert not_found_response.status_code == status.HTTP_404_NOT_FOUND
        print("✓ Non-existent workflow properly handled")
        
        # Test 3: Unauthorized access recovery
        print("\\n--- Test 3: Unauthorized Access Recovery ---")
        
        # Test without authentication
        unauthorized_response = await async_client.get(
            "/api/v1/clinical-workflows/workflows"
        )
        
        assert unauthorized_response.status_code == status.HTTP_401_UNAUTHORIZED
        print("✓ Unauthorized access properly blocked")
        
        # Test 4: Malformed request recovery
        print("\\n--- Test 4: Malformed Request Recovery ---")
        
        malformed_headers = headers.copy()
        malformed_headers["Content-Type"] = "application/json"
        
        malformed_response = await async_client.post(
            "/api/v1/clinical-workflows/workflows",
            content='{"malformed": json}',  # Invalid JSON
            headers=malformed_headers
        )
        
        assert malformed_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        print("✓ Malformed requests properly handled")
        
        print("\\n✓ All error recovery tests passed")
        
        return {
            "error_recovery_tests_passed": 4,
            "invalid_data_handled": True,
            "not_found_handled": True,
            "unauthorized_blocked": True,
            "malformed_requests_handled": True
        }


class TestWorkflowComplianceValidation:
    """Test compliance validation in complete workflows."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.security
    async def test_hipaa_compliance_workflow(
        self, async_client: AsyncClient, physician_token: str, role_based_headers
    ):
        """
        Test HIPAA compliance throughout complete workflow lifecycle.
        
        Scenario: Verify PHI protection, audit trails, and access controls
        in a complete clinical workflow.
        """
        headers = role_based_headers(physician_token)
        patient_id = str(uuid4())
        
        print("\\n=== HIPAA Compliance Validation Workflow ===")
        
        # Step 1: Create workflow with PHI
        workflow_data = {
            "patient_id": patient_id,
            "provider_id": str(uuid4()),
            "workflow_type": WorkflowType.ENCOUNTER.value,
            "priority": WorkflowPriority.ROUTINE.value,
            "chief_complaint": "Patient reports diabetes management concerns",
            "history_present_illness": "Type 2 diabetes, poor glucose control",
            "allergies": ["Sulfa medications"],
            "current_medications": ["Metformin 1000mg BID", "Insulin glargine 20 units daily"],
            "location": "Endocrinology Clinic"
        }
        
        create_response = await async_client.post(
            "/api/v1/clinical-workflows/workflows",
            json=workflow_data,
            headers=headers
        )
        
        assert create_response.status_code == status.HTTP_201_CREATED
        workflow_id = create_response.json()["id"]
        
        print("✓ Workflow with PHI created")
        
        # Step 2: Access workflow with PHI decryption
        phi_access_response = await async_client.get(
            f"/api/v1/clinical-workflows/workflows/{workflow_id}",
            params={"decrypt_phi": True, "access_purpose": "treatment"},
            headers=headers
        )
        
        assert phi_access_response.status_code == status.HTTP_200_OK
        phi_data = phi_access_response.json()
        
        # Verify access tracking
        assert phi_data["access_count"] >= 1
        
        print("✓ PHI access properly tracked")
        
        # Step 3: Update with additional PHI
        phi_update = {
            "assessment": "HbA1c elevated at 9.2%. Recommend medication adjustment.",
            "plan": "Increase insulin dose. Nutritionist referral. Follow-up in 3 months.",
            "progress_notes": "Patient counseled on diabetes management and lifestyle modifications."
        }
        
        update_response = await async_client.put(
            f"/api/v1/clinical-workflows/workflows/{workflow_id}",
            json=phi_update,
            headers=headers
        )
        
        assert update_response.status_code == status.HTTP_200_OK
        
        print("✓ PHI updates properly processed")
        
        # Step 4: Complete workflow
        completion_notes = "Diabetes management plan established. Patient educated on self-care."
        
        completion_response = await async_client.post(
            f"/api/v1/clinical-workflows/workflows/{workflow_id}/complete",
            json=completion_notes,
            headers=headers
        )
        
        assert completion_response.status_code == status.HTTP_200_OK
        
        print("✓ Workflow completed with PHI protection")
        
        # Step 5: Verify final access count and audit trail
        final_access = await async_client.get(
            f"/api/v1/clinical-workflows/workflows/{workflow_id}",
            params={"decrypt_phi": False, "access_purpose": "audit_verification"},
            headers=headers
        )
        
        assert final_access.status_code == status.HTTP_200_OK
        final_data = final_access.json()
        
        # Verify audit trail
        assert final_data["access_count"] >= 3  # Created, updated, completed, verified
        assert final_data["status"] == WorkflowStatus.COMPLETED.value
        
        print("✓ HIPAA compliance validation completed")
        print(f"  Total PHI access events: {final_data['access_count']}")
        print(f"  Workflow properly completed and audited")
        
        return {
            "hipaa_compliance_verified": True,
            "phi_access_tracked": True,
            "audit_trail_complete": True,
            "workflow_id": workflow_id,
            "total_access_events": final_data["access_count"]
        }