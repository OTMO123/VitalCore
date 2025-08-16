"""
Clinical Workflows Schemas Validation Tests

Comprehensive testing of Pydantic schemas, validation rules,
FHIR R4 compliance, and data transformation.
"""

import pytest
from datetime import datetime, date
from typing import List, Dict
from uuid import uuid4
from pydantic import ValidationError

from app.modules.clinical_workflows.schemas import (
    # Enums
    WorkflowType, WorkflowStatus, WorkflowPriority, EncounterClass, 
    EncounterStatus, StepStatus, DocumentationQuality,
    
    # Core schemas
    ClinicalWorkflowCreate, ClinicalWorkflowUpdate, ClinicalWorkflowResponse,
    ClinicalWorkflowStepCreate, ClinicalWorkflowStepUpdate, ClinicalWorkflowStepResponse,
    ClinicalEncounterCreate, ClinicalEncounterResponse,
    
    # Supporting schemas
    SOAPNote, VitalSigns, ClinicalCode,
    ClinicalWorkflowSearchFilters, WorkflowAnalytics, WorkflowAuditEvent
)


class TestClinicalWorkflowSchemas:
    """Test clinical workflow Pydantic schemas."""
    
    @pytest.fixture
    def valid_workflow_data(self):
        """Valid workflow creation data."""
        return {
            "patient_id": uuid4(),
            "provider_id": uuid4(),
            "workflow_type": WorkflowType.ENCOUNTER,
            "priority": WorkflowPriority.ROUTINE,
            "chief_complaint": "Chest pain and shortness of breath",
            "history_present_illness": "Patient reports chest pain starting 2 hours ago",
            "location": "Emergency Department",
            "department": "Emergency Medicine",
            "estimated_duration_minutes": 90
        }
    
    @pytest.fixture
    def valid_vital_signs(self):
        """Valid vital signs data."""
        return {
            "systolic_bp": 140,
            "diastolic_bp": 90,
            "heart_rate": 95,
            "respiratory_rate": 18,
            "temperature": 98.6,
            "oxygen_saturation": 98,
            "weight_kg": 75.0,
            "height_cm": 175.0,
            "pain_score": 7
        }
    
    @pytest.fixture
    def valid_clinical_codes(self):
        """Valid clinical codes."""
        return [
            {
                "code": "R06.02",
                "display": "Shortness of breath",
                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                "version": "2024"
            },
            {
                "code": "R50.9",
                "display": "Fever, unspecified",
                "system": "http://hl7.org/fhir/sid/icd-10-cm"
            }
        ]
    
    def test_clinical_workflow_create_valid(self, valid_workflow_data):
        """Test valid clinical workflow creation."""
        workflow = ClinicalWorkflowCreate(**valid_workflow_data)
        
        assert workflow.patient_id == valid_workflow_data["patient_id"]
        assert workflow.workflow_type == WorkflowType.ENCOUNTER
        assert workflow.priority == WorkflowPriority.ROUTINE
        assert workflow.chief_complaint == valid_workflow_data["chief_complaint"]
        assert workflow.estimated_duration_minutes == 90
    
    def test_clinical_workflow_create_required_fields(self):
        """Test required field validation."""
        # Missing required fields should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            ClinicalWorkflowCreate(
                workflow_type=WorkflowType.ENCOUNTER
                # Missing patient_id
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("patient_id",) for error in errors)
    
    def test_clinical_workflow_create_enum_validation(self, valid_workflow_data):
        """Test enum field validation."""
        # Valid enum values should work
        workflow_data = valid_workflow_data.copy()
        workflow_data["workflow_type"] = WorkflowType.CARE_PLAN
        workflow_data["priority"] = WorkflowPriority.URGENT
        
        workflow = ClinicalWorkflowCreate(**workflow_data)
        assert workflow.workflow_type == WorkflowType.CARE_PLAN
        assert workflow.priority == WorkflowPriority.URGENT
        
        # Invalid enum values should fail
        invalid_data = valid_workflow_data.copy()
        invalid_data["workflow_type"] = "invalid_type"
        
        with pytest.raises(ValidationError):
            ClinicalWorkflowCreate(**invalid_data)
    
    def test_clinical_workflow_create_with_structured_data(self, valid_workflow_data, valid_vital_signs, valid_clinical_codes):
        """Test workflow creation with structured clinical data."""
        workflow_data = valid_workflow_data.copy()
        workflow_data.update({
            "vital_signs": valid_vital_signs,
            "allergies": ["Penicillin", "Latex"],
            "current_medications": ["Lisinopril 10mg daily", "Metformin 500mg BID"],
            "diagnosis_codes": valid_clinical_codes,
            "clinical_alerts": ["Drug allergy alert", "Hypertension monitoring"],
            "consent_id": uuid4()
        })
        
        workflow = ClinicalWorkflowCreate(**workflow_data)
        
        assert workflow.vital_signs.systolic_bp == 140
        assert "Penicillin" in workflow.allergies
        assert len(workflow.diagnosis_codes) == 2
        assert workflow.diagnosis_codes[0].code == "R06.02"
        assert workflow.consent_id is not None
    
    def test_clinical_workflow_update_partial(self):
        """Test partial workflow updates."""
        update_data = {
            "status": WorkflowStatus.COMPLETED,
            "completion_percentage": 100,
            "documentation_quality": DocumentationQuality.EXCELLENT,
            "workflow_end_time": datetime.utcnow(),
            "actual_duration_minutes": 85
        }
        
        update = ClinicalWorkflowUpdate(**update_data)
        
        assert update.status == WorkflowStatus.COMPLETED
        assert update.completion_percentage == 100
        assert update.documentation_quality == DocumentationQuality.EXCELLENT
        assert update.actual_duration_minutes == 85
    
    def test_clinical_workflow_update_validation(self):
        """Test update validation rules."""
        # Invalid completion percentage
        with pytest.raises(ValidationError):
            ClinicalWorkflowUpdate(completion_percentage=150)  # > 100
        
        with pytest.raises(ValidationError):
            ClinicalWorkflowUpdate(completion_percentage=-10)  # < 0
        
        # Invalid duration
        with pytest.raises(ValidationError):
            ClinicalWorkflowUpdate(actual_duration_minutes=0)  # < 1


class TestVitalSignsValidation:
    """Test vital signs validation and business rules."""
    
    def test_vital_signs_valid_ranges(self):
        """Test vital signs within valid clinical ranges."""
        valid_vitals = VitalSigns(
            systolic_bp=120,
            diastolic_bp=80,
            heart_rate=70,
            respiratory_rate=16,
            temperature=98.6,
            oxygen_saturation=99,
            weight_kg=70.0,
            height_cm=170.0,
            pain_score=3
        )
        
        assert valid_vitals.systolic_bp == 120
        assert valid_vitals.diastolic_bp == 80
        assert valid_vitals.bmi is not None  # Should be auto-calculated
    
    def test_vital_signs_range_validation(self):
        """Test vital signs range validation."""
        # Blood pressure too high
        with pytest.raises(ValidationError):
            VitalSigns(systolic_bp=350)  # > 300
        
        # Heart rate too low
        with pytest.raises(ValidationError):
            VitalSigns(heart_rate=15)  # < 20
        
        # Oxygen saturation invalid
        with pytest.raises(ValidationError):
            VitalSigns(oxygen_saturation=110)  # > 100
        
        # Pain score out of range
        with pytest.raises(ValidationError):
            VitalSigns(pain_score=15)  # > 10
    
    def test_blood_pressure_relationship_validation(self):
        """Test blood pressure systolic > diastolic validation."""
        # Valid BP relationship
        valid_bp = VitalSigns(
            systolic_bp=120,
            diastolic_bp=80
        )
        assert valid_bp.systolic_bp > valid_bp.diastolic_bp
        
        # Invalid BP relationship (systolic <= diastolic)
        with pytest.raises(ValidationError):
            VitalSigns(
                systolic_bp=80,
                diastolic_bp=120  # Diastolic higher than systolic
            )
    
    def test_bmi_auto_calculation(self):
        """Test automatic BMI calculation."""
        vitals = VitalSigns(
            weight_kg=70.0,
            height_cm=175.0
        )
        
        # BMI should be auto-calculated: 70 / (1.75^2) = 22.9
        expected_bmi = round(70.0 / (1.75 ** 2), 1)
        assert vitals.bmi == expected_bmi
    
    def test_bmi_override_validation(self):
        """Test BMI override validation."""
        # Provided BMI should match calculated BMI (within tolerance)
        vitals = VitalSigns(
            weight_kg=70.0,
            height_cm=175.0,
            bmi=22.9  # Correct BMI
        )
        assert vitals.bmi == 22.9
        
        # Significantly different BMI should fail validation
        with pytest.raises(ValidationError):
            VitalSigns(
                weight_kg=70.0,
                height_cm=175.0,
                bmi=30.0  # Incorrect BMI
            )


class TestClinicalCodeValidation:
    """Test clinical code validation (ICD-10, CPT, SNOMED)."""
    
    def test_clinical_code_valid(self):
        """Test valid clinical code creation."""
        code = ClinicalCode(
            code="R06.02",
            display="Shortness of breath",
            system="http://hl7.org/fhir/sid/icd-10-cm",
            version="2024"
        )
        
        assert code.code == "R06.02"
        assert code.display == "Shortness of breath"
        assert "icd-10" in code.system.lower()
    
    def test_clinical_code_required_fields(self):
        """Test required fields for clinical codes."""
        # Missing required fields
        with pytest.raises(ValidationError):
            ClinicalCode(
                code="R06.02"
                # Missing display and system
            )
    
    def test_clinical_codes_list_validation(self):
        """Test validation of clinical codes list."""
        codes_data = [
            {
                "code": "R06.02",
                "display": "Shortness of breath", 
                "system": "http://hl7.org/fhir/sid/icd-10-cm"
            },
            {
                "code": "99213",
                "display": "Office visit, established patient",
                "system": "http://www.ama-assn.org/go/cpt"
            }
        ]
        
        # Should validate successfully
        codes = [ClinicalCode(**code_data) for code_data in codes_data]
        assert len(codes) == 2
        assert codes[0].code == "R06.02"
        assert codes[1].code == "99213"


class TestSOAPNoteValidation:
    """Test SOAP note structure validation."""
    
    def test_soap_note_complete(self):
        """Test complete SOAP note."""
        soap = SOAPNote(
            subjective="Patient reports chest pain, 7/10 severity, radiating to left arm",
            objective="BP 140/90, HR 95, RR 18, O2 98%. Chest clear to auscultation",
            assessment="Chest pain, rule out acute coronary syndrome",
            plan="EKG, cardiac enzymes, chest X-ray. Monitor in ED"
        )
        
        assert "chest pain" in soap.subjective.lower()
        assert "bp 140/90" in soap.objective.lower()
        assert "acute coronary syndrome" in soap.assessment.lower()
        assert "ekg" in soap.plan.lower()
    
    def test_soap_note_partial(self):
        """Test partial SOAP note (all fields optional)."""
        soap = SOAPNote(
            subjective="Patient reports headache"
            # Other fields optional
        )
        
        assert soap.subjective is not None
        assert soap.objective is None
        assert soap.assessment is None
        assert soap.plan is None


class TestWorkflowStepSchemas:
    """Test workflow step schemas."""
    
    def test_workflow_step_create(self):
        """Test workflow step creation."""
        step_data = {
            "workflow_id": uuid4(),
            "step_name": "patient_assessment",
            "step_type": "clinical_evaluation",
            "step_order": 1,
            "notes": "Initial patient assessment completed",
            "estimated_duration_minutes": 15
        }
        
        step = ClinicalWorkflowStepCreate(**step_data)
        
        assert step.step_name == "patient_assessment"
        assert step.step_order == 1
        assert step.estimated_duration_minutes == 15
    
    def test_workflow_step_create_validation(self):
        """Test workflow step validation rules."""
        base_data = {
            "workflow_id": uuid4(),
            "step_name": "test_step",
            "step_type": "test",
            "step_order": 1
        }
        
        # Valid step
        step = ClinicalWorkflowStepCreate(**base_data)
        assert step.step_order == 1
        
        # Invalid step order (< 1)
        invalid_data = base_data.copy()
        invalid_data["step_order"] = 0
        
        with pytest.raises(ValidationError):
            ClinicalWorkflowStepCreate(**invalid_data)
    
    def test_workflow_step_update(self):
        """Test workflow step updates."""
        update_data = {
            "status": StepStatus.COMPLETED,
            "completed_at": datetime.utcnow(),
            "actual_duration_minutes": 20,
            "quality_score": 95,
            "completion_quality": DocumentationQuality.EXCELLENT,
            "notes": "Step completed successfully"
        }
        
        update = ClinicalWorkflowStepUpdate(**update_data)
        
        assert update.status == StepStatus.COMPLETED
        assert update.quality_score == 95
        assert update.completion_quality == DocumentationQuality.EXCELLENT
    
    def test_workflow_step_update_validation(self):
        """Test step update validation."""
        # Invalid quality score
        with pytest.raises(ValidationError):
            ClinicalWorkflowStepUpdate(quality_score=150)  # > 100
        
        # Invalid duration
        with pytest.raises(ValidationError):
            ClinicalWorkflowStepUpdate(actual_duration_minutes=0)  # < 1


class TestEncounterSchemas:
    """Test clinical encounter schemas."""
    
    def test_encounter_create_minimal(self):
        """Test minimal encounter creation."""
        encounter_data = {
            "patient_id": uuid4(),
            "provider_id": uuid4(),
            "encounter_class": EncounterClass.AMBULATORY,
            "encounter_datetime": datetime.utcnow()
        }
        
        encounter = ClinicalEncounterCreate(**encounter_data)
        
        assert encounter.encounter_class == EncounterClass.AMBULATORY
        assert encounter.encounter_datetime is not None
        assert encounter.follow_up_required is False  # Default value
    
    def test_encounter_create_complete(self, valid_vital_signs, valid_clinical_codes):
        """Test complete encounter creation with all data."""
        soap_note = {
            "subjective": "Patient reports fatigue and weakness",
            "objective": "Patient appears tired, vital signs stable",
            "assessment": "Possible viral syndrome vs. anxiety",
            "plan": "Symptomatic care, follow up in 1 week"
        }
        
        encounter_data = {
            "patient_id": uuid4(),
            "provider_id": uuid4(),
            "encounter_class": EncounterClass.AMBULATORY,
            "encounter_type_code": "185349003",
            "encounter_type_display": "Encounter for check up",
            "soap_note": soap_note,
            "vital_signs": valid_vital_signs,
            "diagnosis_codes": valid_clinical_codes,
            "encounter_datetime": datetime.utcnow(),
            "location": "Primary Care Clinic",
            "department": "Family Medicine",
            "disposition": "home",
            "outcome": "improved",
            "follow_up_required": True,
            "consent_id": uuid4()
        }
        
        encounter = ClinicalEncounterCreate(**encounter_data)
        
        assert encounter.soap_note.subjective == soap_note["subjective"]
        assert encounter.vital_signs.heart_rate == valid_vital_signs["heart_rate"]
        assert len(encounter.diagnosis_codes) == 2
        assert encounter.follow_up_required is True
    
    def test_encounter_enum_validation(self):
        """Test encounter enum validation."""
        base_data = {
            "patient_id": uuid4(),
            "provider_id": uuid4(),
            "encounter_datetime": datetime.utcnow()
        }
        
        # Valid encounter class
        valid_data = base_data.copy()
        valid_data["encounter_class"] = EncounterClass.EMERGENCY
        
        encounter = ClinicalEncounterCreate(**valid_data)
        assert encounter.encounter_class == EncounterClass.EMERGENCY
        
        # Invalid encounter class
        invalid_data = base_data.copy()
        invalid_data["encounter_class"] = "INVALID_CLASS"
        
        with pytest.raises(ValidationError):
            ClinicalEncounterCreate(**invalid_data)


class TestSearchAndAnalyticsSchemas:
    """Test search filters and analytics schemas."""
    
    def test_workflow_search_filters(self):
        """Test workflow search filters."""
        filters = ClinicalWorkflowSearchFilters(
            patient_id=uuid4(),
            workflow_type=WorkflowType.ENCOUNTER,
            status=[WorkflowStatus.ACTIVE, WorkflowStatus.COMPLETED],
            priority=[WorkflowPriority.URGENT, WorkflowPriority.EMERGENCY],
            date_from=date(2025, 1, 1),
            date_to=date(2025, 12, 31),
            search_text="chest pain",
            page=2,
            page_size=50,
            sort_by="created_at",
            sort_direction="desc"
        )
        
        assert filters.workflow_type == WorkflowType.ENCOUNTER
        assert WorkflowStatus.ACTIVE in filters.status
        assert filters.page == 2
        assert filters.sort_by == "created_at"
    
    def test_search_filters_validation(self):
        """Test search filter validation."""
        # Valid page and page_size
        filters = ClinicalWorkflowSearchFilters(page=1, page_size=20)
        assert filters.page == 1
        assert filters.page_size == 20
        
        # Invalid page (< 1)
        with pytest.raises(ValidationError):
            ClinicalWorkflowSearchFilters(page=0)
        
        # Invalid page_size (> 100)
        with pytest.raises(ValidationError):
            ClinicalWorkflowSearchFilters(page_size=150)
        
        # Invalid sort field
        with pytest.raises(ValidationError):
            ClinicalWorkflowSearchFilters(sort_by="invalid_field")
    
    def test_workflow_analytics(self):
        """Test workflow analytics schema."""
        analytics = WorkflowAnalytics(
            total_workflows=1000,
            completed_workflows=850,
            average_duration_minutes=75.5,
            completion_rate=0.85,
            quality_score_average=87.3,
            workflows_by_type={
                "encounter": 600,
                "care_plan": 200,
                "consultation": 200
            },
            workflows_by_status={
                "completed": 850,
                "active": 100,
                "cancelled": 50
            },
            workflows_by_priority={
                "routine": 700,
                "urgent": 250,
                "emergency": 50
            },
            average_time_to_completion=72.8,
            documentation_quality_distribution={
                "excellent": 300,
                "good": 400,
                "fair": 200,
                "poor": 100
            },
            period_start=date(2025, 1, 1),
            period_end=date(2025, 3, 31)
        )
        
        assert analytics.total_workflows == 1000
        assert analytics.completion_rate == 0.85
        assert analytics.workflows_by_type["encounter"] == 600
    
    def test_audit_event_schema(self):
        """Test audit event schema."""
        audit_event = WorkflowAuditEvent(
            id=uuid4(),
            workflow_id=uuid4(),
            event_type="workflow_completed",
            action="complete",
            user_id=uuid4(),
            timestamp=datetime.utcnow(),
            ip_address="192.168.1.100",
            session_id="session_123",
            phi_accessed=True,
            phi_fields_accessed=["assessment", "plan"],
            access_purpose="clinical_documentation",
            risk_level="medium",
            anomaly_score=25
        )
        
        assert audit_event.event_type == "workflow_completed"
        assert audit_event.phi_accessed is True
        assert "assessment" in audit_event.phi_fields_accessed
        assert audit_event.risk_level == "medium"


class TestSchemaCompatibility:
    """Test schema compatibility and data transformation."""
    
    def test_create_to_response_transformation(self, valid_workflow_data):
        """Test transformation from create to response schema."""
        # Create workflow
        create_data = valid_workflow_data.copy()
        create_workflow = ClinicalWorkflowCreate(**create_data)
        
        # Transform to response (simulating service layer processing)
        response_data = create_data.copy()
        response_data.update({
            "id": uuid4(),
            "status": WorkflowStatus.ACTIVE,
            "workflow_start_time": datetime.utcnow(),
            "completion_percentage": 0,
            "created_at": datetime.utcnow(),
            "access_count": 0,
            "version": 1
        })
        
        response_workflow = ClinicalWorkflowResponse(**response_data)
        
        assert response_workflow.id is not None
        assert response_workflow.patient_id == create_workflow.patient_id
        assert response_workflow.workflow_type == create_workflow.workflow_type
        assert response_workflow.status == WorkflowStatus.ACTIVE
    
    def test_update_to_response_merge(self):
        """Test merging update data with existing response."""
        # Original response
        original_data = {
            "id": uuid4(),
            "patient_id": uuid4(),
            "provider_id": uuid4(),
            "workflow_type": WorkflowType.ENCOUNTER,
            "status": WorkflowStatus.ACTIVE,
            "priority": WorkflowPriority.ROUTINE,
            "workflow_start_time": datetime.utcnow(),
            "completion_percentage": 25,
            "created_at": datetime.utcnow(),
            "access_count": 5,
            "version": 1
        }
        
        # Update data
        update_data = {
            "status": WorkflowStatus.COMPLETED,
            "completion_percentage": 100,
            "workflow_end_time": datetime.utcnow()
        }
        
        # Merge update into response (simulating service layer)
        updated_data = original_data.copy()
        updated_data.update(update_data)
        
        updated_response = ClinicalWorkflowResponse(**updated_data)
        
        assert updated_response.status == WorkflowStatus.COMPLETED
        assert updated_response.completion_percentage == 100
        assert updated_response.workflow_end_time is not None


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])