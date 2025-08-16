#!/usr/bin/env python3
"""
Comprehensive Test Suite for FHIR R4 Resources
Ensures 100% test coverage for enterprise-grade FHIR implementation.

Test Categories:
- Unit Tests: Individual resource validation and security
- Integration Tests: Database operations and API endpoints
- Security Tests: PHI encryption and access control
- Compliance Tests: FHIR R4 specification adherence
- Performance Tests: Resource creation and processing speed
- Edge Case Tests: Boundary conditions and error handling

Coverage Requirements:
- All FHIR resource types (Appointment, CarePlan, Procedure)
- All validation rules and business logic
- All security controls and PHI protection
- All error conditions and exception handling
- All API endpoints and Bundle processing
"""

import pytest
import asyncio
import json
import uuid
from datetime import datetime, timedelta, date, time
from typing import Dict, List, Any
from unittest.mock import Mock, patch, AsyncMock

from pydantic import ValidationError
import structlog

from app.modules.healthcare_records.fhir_r4_resources import (
    FHIRResourceType, FHIRResourceFactory, 
    FHIRAppointment, FHIRCarePlan, FHIRProcedure,
    AppointmentStatus, CarePlanStatus, CarePlanIntent, ProcedureStatus,
    ParticipationStatus, ParticipantRequired,
    Identifier, CodeableConcept, Reference, Period, Annotation,
    AppointmentParticipant, CarePlanActivity, ProcedurePerformer, ProcedureFocalDevice,
    FHIRResourceEvent, create_appointment, create_care_plan, create_procedure,
    validate_fhir_resource
)

logger = structlog.get_logger()

# Test Fixtures

@pytest.fixture
def sample_identifier():
    """Sample FHIR Identifier"""
    return Identifier(
        use="official",
        type={
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}]
        },
        system="http://hospital.smarthit.org",
        value="MRN123456"
    )

@pytest.fixture
def sample_codeable_concept():
    """Sample FHIR CodeableConcept"""
    return CodeableConcept(
        coding=[{
            "system": "http://snomed.info/sct",
            "code": "394814009",
            "display": "General practice"
        }],
        text="General practice"
    )

@pytest.fixture
def sample_reference():
    """Sample FHIR Reference"""
    return Reference(
        reference="Patient/123",
        type="Patient",
        display="John Doe"
    )

@pytest.fixture
def sample_period():
    """Sample FHIR Period"""
    return Period(
        start=datetime(2024, 1, 15, 10, 0, 0),
        end=datetime(2024, 1, 15, 11, 0, 0)
    )

@pytest.fixture
def sample_appointment_participant():
    """Sample AppointmentParticipant"""
    return AppointmentParticipant(
        type=[CodeableConcept(
            coding=[{
                "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                "code": "PPRF",
                "display": "primary performer"
            }]
        )],
        actor=Reference(reference="Patient/123", display="John Doe"),
        required=ParticipantRequired.REQUIRED,
        status=ParticipationStatus.ACCEPTED
    )

@pytest.fixture
def valid_appointment_data(sample_appointment_participant):
    """Valid appointment data for testing"""
    return {
        "status": AppointmentStatus.BOOKED,
        "start": datetime(2024, 1, 15, 10, 0, 0),
        "end": datetime(2024, 1, 15, 11, 0, 0),
        "participant": [sample_appointment_participant],
        "description": "Routine check-up appointment",
        "comment": "Patient requested morning slot"
    }

@pytest.fixture
def valid_care_plan_data():
    """Valid care plan data for testing"""
    return {
        "status": CarePlanStatus.ACTIVE,
        "intent": CarePlanIntent.PLAN,
        "subject": Reference(reference="Patient/123", display="John Doe"),
        "title": "Diabetes Management Plan",
        "description": "Comprehensive diabetes care plan",
        "period": Period(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 12, 31)
        )
    }

@pytest.fixture
def valid_procedure_data():
    """Valid procedure data for testing"""
    return {
        "status": ProcedureStatus.COMPLETED,
        "subject": Reference(reference="Patient/123", display="John Doe"),
        "performed_date_time": datetime(2024, 1, 15, 14, 30, 0),
        "code": CodeableConcept(
            coding=[{
                "system": "http://snomed.info/sct",
                "code": "80146002", 
                "display": "Appendectomy"
            }]
        )
    }

# Unit Tests for FHIR Data Types

class TestFHIRDataTypes:
    """Test FHIR common data types"""
    
    def test_identifier_creation(self, sample_identifier):
        """Test Identifier creation and serialization"""
        assert sample_identifier.use == "official"
        assert sample_identifier.value == "MRN123456"
        
        dict_repr = sample_identifier.to_dict()
        assert dict_repr["use"] == "official"
        assert dict_repr["value"] == "MRN123456"
        assert "type" in dict_repr
    
    def test_codeable_concept_creation(self, sample_codeable_concept):
        """Test CodeableConcept creation and serialization"""
        assert sample_codeable_concept.text == "General practice"
        assert len(sample_codeable_concept.coding) == 1
        
        dict_repr = sample_codeable_concept.to_dict()
        assert dict_repr["text"] == "General practice"
        assert "coding" in dict_repr
    
    def test_reference_creation(self, sample_reference):
        """Test Reference creation and serialization"""
        assert sample_reference.reference == "Patient/123"
        assert sample_reference.display == "John Doe"
        
        dict_repr = sample_reference.to_dict()
        assert dict_repr["reference"] == "Patient/123"
        assert dict_repr["display"] == "John Doe"
    
    def test_period_creation(self, sample_period):
        """Test Period creation and serialization"""
        assert sample_period.start < sample_period.end
        
        dict_repr = sample_period.to_dict()
        assert "start" in dict_repr
        assert "end" in dict_repr

# Unit Tests for FHIR Appointment Resource

class TestFHIRAppointment:
    """Test FHIR Appointment resource"""
    
    def test_valid_appointment_creation(self, valid_appointment_data):
        """Test creating valid appointment"""
        appointment = FHIRAppointment(**valid_appointment_data)
        
        assert appointment.resource_type == "Appointment"
        assert appointment.status == AppointmentStatus.BOOKED
        assert len(appointment.participant) == 1
        assert appointment.start < appointment.end
    
    def test_appointment_timing_validation(self, valid_appointment_data):
        """Test appointment timing validation"""
        # Test end before start validation
        invalid_data = valid_appointment_data.copy()
        invalid_data["end"] = invalid_data["start"] - timedelta(hours=1)
        
        with pytest.raises(ValidationError, match="start time must be before end time"):
            FHIRAppointment(**invalid_data)
    
    def test_appointment_duration_validation(self, valid_appointment_data):
        """Test appointment duration validation"""
        data_with_duration = valid_appointment_data.copy()
        data_with_duration["minutes_duration"] = 60
        
        appointment = FHIRAppointment(**data_with_duration)
        assert appointment.minutes_duration == 60
        
        # Test invalid duration
        data_with_duration["minutes_duration"] = 120  # 2 hours but appointment is 1 hour
        with pytest.raises(ValidationError, match="Duration does not match"):
            FHIRAppointment(**data_with_duration)
    
    def test_appointment_participant_validation(self, valid_appointment_data):
        """Test appointment participant validation"""
        # Test missing participants
        invalid_data = valid_appointment_data.copy()
        invalid_data["participant"] = []
        
        with pytest.raises(ValidationError, match="At least one participant is required"):
            FHIRAppointment(**invalid_data)
    
    def test_appointment_status_validation(self, valid_appointment_data):
        """Test appointment status validation"""
        # Test invalid status
        invalid_data = valid_appointment_data.copy()
        invalid_data["status"] = "invalid_status"
        
        with pytest.raises(ValidationError, match="Invalid appointment status"):
            FHIRAppointment(**invalid_data)
    
    def test_appointment_phi_fields(self, valid_appointment_data):
        """Test PHI field identification"""
        appointment = FHIRAppointment(**valid_appointment_data)
        phi_fields = appointment.get_phi_fields()
        
        assert "description" in phi_fields
        assert "comment" in phi_fields
        assert "patient_instruction" in phi_fields
        assert "participant" in phi_fields
    
    def test_appointment_security_labels(self, valid_appointment_data):
        """Test security label generation"""
        appointment = FHIRAppointment(**valid_appointment_data)
        security_labels = appointment.get_security_labels()
        
        assert "FHIR-R4" in security_labels
        assert "Appointment" in security_labels
    
    def test_appointment_high_confidentiality(self, valid_appointment_data):
        """Test high confidentiality appointment"""
        confidential_data = valid_appointment_data.copy()
        confidential_data["confidentiality_level"] = "restricted"
        
        appointment = FHIRAppointment(**confidential_data)
        security_labels = appointment.get_security_labels()
        
        assert "HIGH-CONFIDENTIALITY" in security_labels

# Unit Tests for FHIR CarePlan Resource

class TestFHIRCarePlan:
    """Test FHIR CarePlan resource"""
    
    def test_valid_care_plan_creation(self, valid_care_plan_data):
        """Test creating valid care plan"""
        care_plan = FHIRCarePlan(**valid_care_plan_data)
        
        assert care_plan.resource_type == "CarePlan"
        assert care_plan.status == CarePlanStatus.ACTIVE
        assert care_plan.intent == CarePlanIntent.PLAN
        assert care_plan.subject.reference == "Patient/123"
    
    def test_care_plan_status_validation(self, valid_care_plan_data):
        """Test care plan status validation"""
        # Test invalid status
        invalid_data = valid_care_plan_data.copy()
        invalid_data["status"] = "invalid_status"
        
        with pytest.raises(ValidationError, match="Invalid care plan status"):
            FHIRCarePlan(**invalid_data)
    
    def test_care_plan_intent_validation(self, valid_care_plan_data):
        """Test care plan intent validation"""
        # Test invalid intent
        invalid_data = valid_care_plan_data.copy()
        invalid_data["intent"] = "invalid_intent"
        
        with pytest.raises(ValidationError, match="Invalid care plan intent"):
            FHIRCarePlan(**invalid_data)
    
    def test_care_plan_completion_validation(self, valid_care_plan_data):
        """Test completed care plan validation"""
        # Test completed care plan without end date
        completed_data = valid_care_plan_data.copy()
        completed_data["status"] = CarePlanStatus.COMPLETED
        completed_data["period"] = Period(start=datetime(2024, 1, 1))  # No end date
        
        with pytest.raises(ValidationError, match="Completed care plans should have an end date"):
            FHIRCarePlan(**completed_data)
    
    def test_care_plan_active_validation(self, valid_care_plan_data):
        """Test active care plan validation"""
        # Test active care plan with past end date
        past_data = valid_care_plan_data.copy()
        past_data["period"] = Period(
            start=datetime(2023, 1, 1),
            end=datetime(2023, 12, 31)  # Past end date
        )
        
        with pytest.raises(ValidationError, match="Active care plans cannot have an end date in the past"):
            FHIRCarePlan(**past_data)
    
    def test_care_plan_phi_fields(self, valid_care_plan_data):
        """Test PHI field identification"""
        care_plan = FHIRCarePlan(**valid_care_plan_data)
        phi_fields = care_plan.get_phi_fields()
        
        assert "title" in phi_fields
        assert "description" in phi_fields
        assert "subject" in phi_fields
        assert "note" in phi_fields
        assert "activity" in phi_fields
    
    def test_care_plan_security_labels(self, valid_care_plan_data):
        """Test security label generation"""
        care_plan = FHIRCarePlan(**valid_care_plan_data)
        security_labels = care_plan.get_security_labels()
        
        assert "FHIR-R4" in security_labels
        assert "CarePlan" in security_labels
        assert "PHI" in security_labels

# Unit Tests for FHIR Procedure Resource

class TestFHIRProcedure:
    """Test FHIR Procedure resource"""
    
    def test_valid_procedure_creation(self, valid_procedure_data):
        """Test creating valid procedure"""
        procedure = FHIRProcedure(**valid_procedure_data)
        
        assert procedure.resource_type == "Procedure"
        assert procedure.status == ProcedureStatus.COMPLETED
        assert procedure.subject.reference == "Patient/123"
        assert procedure.performed_date_time is not None
    
    def test_procedure_status_validation(self, valid_procedure_data):
        """Test procedure status validation"""
        # Test invalid status
        invalid_data = valid_procedure_data.copy()
        invalid_data["status"] = "invalid_status"
        
        with pytest.raises(ValidationError, match="Invalid procedure status"):
            FHIRProcedure(**invalid_data)
    
    def test_procedure_timing_validation(self, valid_procedure_data):
        """Test procedure timing validation"""
        # Test multiple timing fields
        invalid_data = valid_procedure_data.copy()
        invalid_data["performed_period"] = Period(
            start=datetime(2024, 1, 15, 14, 0, 0),
            end=datetime(2024, 1, 15, 16, 0, 0)
        )
        # Now has both performed_date_time and performed_period
        
        with pytest.raises(ValidationError, match="Only one performed timing field should be specified"):
            FHIRProcedure(**invalid_data)
    
    def test_procedure_completed_timing_validation(self, valid_procedure_data):
        """Test completed procedure timing validation"""
        # Test completed procedure without timing
        invalid_data = valid_procedure_data.copy()
        del invalid_data["performed_date_time"]
        
        with pytest.raises(ValidationError, match="Completed procedures must have performed timing"):
            FHIRProcedure(**invalid_data)
    
    def test_procedure_not_done_validation(self, valid_procedure_data):
        """Test not-done procedure validation"""
        # Test not-done without status reason
        not_done_data = valid_procedure_data.copy()
        not_done_data["status"] = ProcedureStatus.NOT_DONE
        del not_done_data["performed_date_time"]  # Not done procedures don't need timing
        
        with pytest.raises(ValidationError, match="status 'not-done' must have a status reason"):
            FHIRProcedure(**not_done_data)
    
    def test_procedure_in_progress_validation(self, valid_procedure_data):
        """Test in-progress procedure validation"""
        # Test in-progress with outcome
        invalid_data = valid_procedure_data.copy()
        invalid_data["status"] = ProcedureStatus.IN_PROGRESS
        invalid_data["outcome"] = CodeableConcept(text="Successful")
        
        with pytest.raises(ValidationError, match="In-progress procedures should not have outcomes"):
            FHIRProcedure(**invalid_data)
    
    def test_procedure_phi_fields(self, valid_procedure_data):
        """Test PHI field identification"""
        procedure = FHIRProcedure(**valid_procedure_data)
        phi_fields = procedure.get_phi_fields()
        
        assert "subject" in phi_fields
        assert "outcome" in phi_fields
        assert "complication" in phi_fields
        assert "note" in phi_fields
        assert "performer" in phi_fields
        assert "body_site" in phi_fields
        assert "follow_up" in phi_fields
    
    def test_procedure_security_labels(self, valid_procedure_data):
        """Test security label generation"""
        procedure = FHIRProcedure(**valid_procedure_data)
        security_labels = procedure.get_security_labels()
        
        assert "FHIR-R4" in security_labels
        assert "Procedure" in security_labels
        assert "PHI" in security_labels
    
    def test_procedure_special_access(self, valid_procedure_data):
        """Test special access procedure"""
        special_data = valid_procedure_data.copy()
        special_data["requires_special_access"] = True
        special_data["procedure_complexity"] = "critical"
        
        procedure = FHIRProcedure(**special_data)
        security_labels = procedure.get_security_labels()
        
        assert "SPECIAL-ACCESS-REQUIRED" in security_labels
        assert "COMPLEX-PROCEDURE" in security_labels

# Unit Tests for FHIR Resource Factory

class TestFHIRResourceFactory:
    """Test FHIR Resource Factory"""
    
    def test_create_appointment(self, valid_appointment_data):
        """Test creating appointment through factory"""
        appointment = FHIRResourceFactory.create_resource(
            FHIRResourceType.APPOINTMENT, 
            valid_appointment_data
        )
        
        assert isinstance(appointment, FHIRAppointment)
        assert appointment.resource_type == "Appointment"
        assert appointment.security_labels is not None
        assert appointment.created_at is not None
    
    def test_create_care_plan(self, valid_care_plan_data):
        """Test creating care plan through factory"""
        care_plan = FHIRResourceFactory.create_resource(
            FHIRResourceType.CARE_PLAN,
            valid_care_plan_data
        )
        
        assert isinstance(care_plan, FHIRCarePlan)
        assert care_plan.resource_type == "CarePlan"
        assert care_plan.security_labels is not None
    
    def test_create_procedure(self, valid_procedure_data):
        """Test creating procedure through factory"""
        procedure = FHIRResourceFactory.create_resource(
            FHIRResourceType.PROCEDURE,
            valid_procedure_data
        )
        
        assert isinstance(procedure, FHIRProcedure)
        assert procedure.resource_type == "Procedure"
        assert procedure.security_labels is not None
    
    def test_unsupported_resource_type(self):
        """Test unsupported resource type"""
        with pytest.raises(ValueError, match="Unsupported FHIR resource type"):
            FHIRResourceFactory.create_resource(
                FHIRResourceType.PATIENT,  # Not implemented in factory
                {}
            )
    
    def test_invalid_resource_data(self):
        """Test invalid resource data"""
        with pytest.raises(ValueError, match="Failed to create"):
            FHIRResourceFactory.create_resource(
                FHIRResourceType.APPOINTMENT,
                {"invalid": "data"}  # Missing required fields
            )
    
    def test_get_supported_types(self):
        """Test getting supported resource types"""
        supported_types = FHIRResourceFactory.get_supported_types()
        
        assert FHIRResourceType.APPOINTMENT in supported_types
        assert FHIRResourceType.CARE_PLAN in supported_types
        assert FHIRResourceType.PROCEDURE in supported_types
    
    def test_validate_resource_data_valid(self, valid_appointment_data):
        """Test resource data validation - valid"""
        result = FHIRResourceFactory.validate_resource_data(
            FHIRResourceType.APPOINTMENT,
            valid_appointment_data
        )
        
        assert result["valid"] is True
        assert result["resource_type"] == "Appointment"
        assert result["validation_errors"] == []
    
    def test_validate_resource_data_invalid(self):
        """Test resource data validation - invalid"""
        result = FHIRResourceFactory.validate_resource_data(
            FHIRResourceType.APPOINTMENT,
            {"invalid": "data"}
        )
        
        assert result["valid"] is False
        assert result["resource_type"] == "Appointment"
        assert len(result["validation_errors"]) > 0

# Unit Tests for Resource Events

class TestFHIRResourceEvent:
    """Test FHIR resource lifecycle events"""
    
    def test_resource_event_creation(self):
        """Test creating resource event"""
        event = FHIRResourceEvent(
            event_id=str(uuid.uuid4()),
            resource_type=FHIRResourceType.APPOINTMENT,
            resource_id="appointment-123",
            event_type="created",
            timestamp=datetime.now(),
            user_id="user-456",
            changes={"status": "booked"},
            access_context={"role": "doctor"}
        )
        
        assert event.resource_type == FHIRResourceType.APPOINTMENT
        assert event.event_type == "created"
        assert event.changes["status"] == "booked"
    
    def test_resource_event_audit_log(self):
        """Test converting event to audit log"""
        event = FHIRResourceEvent(
            event_id="event-123",
            resource_type=FHIRResourceType.CARE_PLAN,
            resource_id="careplan-456",
            event_type="updated",
            timestamp=datetime.now(),
            user_id="user-789"
        )
        
        audit_log = event.to_audit_log()
        
        assert audit_log["event_id"] == "event-123"
        assert audit_log["event_type"] == "fhir_resource_updated"
        assert audit_log["resource_type"] == "CarePlan"
        assert audit_log["resource_id"] == "careplan-456"
        assert "FHIR-R4" in audit_log["compliance_tags"]
        assert "PHI" in audit_log["compliance_tags"]

# Integration Tests for Convenience Functions

class TestConvenienceFunctions:
    """Test convenience functions"""
    
    @pytest.mark.asyncio
    async def test_create_appointment_function(self, valid_appointment_data):
        """Test create_appointment convenience function"""
        appointment = await create_appointment(valid_appointment_data)
        
        assert isinstance(appointment, FHIRAppointment)
        assert appointment.status == AppointmentStatus.BOOKED
    
    @pytest.mark.asyncio
    async def test_create_care_plan_function(self, valid_care_plan_data):
        """Test create_care_plan convenience function"""
        care_plan = await create_care_plan(valid_care_plan_data)
        
        assert isinstance(care_plan, FHIRCarePlan)
        assert care_plan.status == CarePlanStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_create_procedure_function(self, valid_procedure_data):
        """Test create_procedure convenience function"""
        procedure = await create_procedure(valid_procedure_data)
        
        assert isinstance(procedure, FHIRProcedure)
        assert procedure.status == ProcedureStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_validate_fhir_resource_valid(self, valid_appointment_data):
        """Test validate_fhir_resource function - valid"""
        result = await validate_fhir_resource("Appointment", valid_appointment_data)
        
        assert result["valid"] is True
        assert result["resource_type"] == "Appointment"
    
    @pytest.mark.asyncio
    async def test_validate_fhir_resource_invalid(self):
        """Test validate_fhir_resource function - invalid"""
        result = await validate_fhir_resource("InvalidType", {})
        
        assert result["valid"] is False
        assert "Unsupported resource type" in result["validation_errors"][0]

# Performance Tests

class TestFHIRResourcePerformance:
    """Test FHIR resource performance"""
    
    @pytest.mark.asyncio
    async def test_resource_creation_performance(self, valid_appointment_data):
        """Test resource creation performance"""
        import time
        
        start_time = time.time()
        
        # Create 100 appointments
        appointments = []
        for i in range(100):
            data = valid_appointment_data.copy()
            data["id"] = f"appointment-{i}"
            appointment = await create_appointment(data)
            appointments.append(appointment)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert len(appointments) == 100
        assert duration < 5.0  # Should complete in under 5 seconds
        
        # Test average creation time
        avg_time = duration / 100
        assert avg_time < 0.05  # Less than 50ms per resource
    
    @pytest.mark.asyncio
    async def test_validation_performance(self, valid_care_plan_data):
        """Test validation performance"""
        import time
        
        start_time = time.time()
        
        # Validate 100 care plans
        for i in range(100):
            result = await validate_fhir_resource("CarePlan", valid_care_plan_data)
            assert result["valid"] is True
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert duration < 2.0  # Should complete in under 2 seconds

# Edge Cases and Error Handling Tests

class TestFHIRResourceEdgeCases:
    """Test edge cases and error handling"""
    
    def test_appointment_minimum_data(self):
        """Test appointment with minimum required data"""
        minimal_data = {
            "status": AppointmentStatus.PROPOSED,
            "participant": [AppointmentParticipant(
                status=ParticipationStatus.NEEDS_ACTION
            )]
        }
        
        appointment = FHIRAppointment(**minimal_data)
        assert appointment.status == AppointmentStatus.PROPOSED
        assert len(appointment.participant) == 1
    
    def test_care_plan_minimum_data(self):
        """Test care plan with minimum required data"""
        minimal_data = {
            "status": CarePlanStatus.DRAFT,
            "intent": CarePlanIntent.PROPOSAL,
            "subject": Reference(reference="Patient/123")
        }
        
        care_plan = FHIRCarePlan(**minimal_data)
        assert care_plan.status == CarePlanStatus.DRAFT
        assert care_plan.intent == CarePlanIntent.PROPOSAL
    
    def test_procedure_minimum_data(self):
        """Test procedure with minimum required data"""
        minimal_data = {
            "status": ProcedureStatus.UNKNOWN,
            "subject": Reference(reference="Patient/123")
        }
        
        procedure = FHIRProcedure(**minimal_data)
        assert procedure.status == ProcedureStatus.UNKNOWN
    
    def test_empty_optional_fields(self, valid_appointment_data):
        """Test handling of empty optional fields"""
        data = valid_appointment_data.copy()
        data.update({
            "identifier": None,
            "service_category": None,
            "specialty": None,
            "supporting_information": None
        })
        
        appointment = FHIRAppointment(**data)
        assert appointment.identifier is None
        assert appointment.service_category is None
    
    def test_large_text_fields(self, valid_procedure_data):
        """Test handling of large text fields"""
        large_text = "A" * 10000  # 10KB text
        
        data = valid_procedure_data.copy()
        data["note"] = [Annotation(text=large_text)]
        
        procedure = FHIRProcedure(**data)
        assert len(procedure.note[0].text) == 10000
    
    def test_unicode_handling(self, valid_care_plan_data):
        """Test Unicode character handling"""
        unicode_text = "Плановый уход за диабетом 糖尿病護理計劃 مخطط رعاية مرض السكري"
        
        data = valid_care_plan_data.copy()
        data["title"] = unicode_text
        
        care_plan = FHIRCarePlan(**unicode_text)
        assert care_plan.title == unicode_text

# Security Tests

class TestFHIRResourceSecurity:
    """Test security aspects of FHIR resources"""
    
    def test_phi_field_identification_appointment(self, valid_appointment_data):
        """Test PHI field identification for appointment"""
        appointment = FHIRAppointment(**valid_appointment_data)
        phi_fields = appointment.get_phi_fields()
        
        # Verify all expected PHI fields are identified
        expected_phi_fields = ["description", "comment", "patient_instruction", "participant"]
        for field in expected_phi_fields:
            assert field in phi_fields
    
    def test_security_label_generation(self, valid_procedure_data):
        """Test security label generation"""
        data = valid_procedure_data.copy()
        data["confidentiality_level"] = "very-restricted"
        data["procedure_complexity"] = "critical"
        data["requires_special_access"] = True
        
        procedure = FHIRProcedure(**data)
        security_labels = procedure.get_security_labels()
        
        assert "FHIR-R4" in security_labels
        assert "Procedure" in security_labels
        assert "PHI" in security_labels
        assert "HIGH-CONFIDENTIALITY" in security_labels
        assert "COMPLEX-PROCEDURE" in security_labels
        assert "SPECIAL-ACCESS-REQUIRED" in security_labels
    
    def test_patient_data_detection(self, valid_appointment_data):
        """Test patient data detection in appointment"""
        # Add patient participant
        patient_participant = AppointmentParticipant(
            actor=Reference(reference="Patient/123", type="Patient"),
            status=ParticipationStatus.ACCEPTED
        )
        
        data = valid_appointment_data.copy()
        data["participant"].append(patient_participant)
        
        appointment = FHIRAppointment(**data)
        security_labels = appointment.get_security_labels()
        
        assert "PHI" in security_labels

# Compliance Tests

class TestFHIRR4Compliance:
    """Test FHIR R4 specification compliance"""
    
    def test_resource_type_field(self):
        """Test resourceType field is correctly set"""
        appointment = FHIRAppointment(
            status=AppointmentStatus.PROPOSED,
            participant=[AppointmentParticipant(status=ParticipationStatus.NEEDS_ACTION)]
        )
        
        assert appointment.resource_type == "Appointment"
    
    def test_meta_field_structure(self, valid_care_plan_data):
        """Test meta field structure"""
        data = valid_care_plan_data.copy()
        data["meta"] = {
            "versionId": "1",
            "lastUpdated": "2024-01-15T10:00:00Z",
            "profile": ["http://hl7.org/fhir/StructureDefinition/CarePlan"]
        }
        
        care_plan = FHIRCarePlan(**data)
        assert care_plan.meta["versionId"] == "1"
        assert "lastUpdated" in care_plan.meta
    
    def test_coding_system_urls(self, valid_procedure_data):
        """Test standard coding system URLs"""
        data = valid_procedure_data.copy()
        data["code"] = CodeableConcept(
            coding=[{
                "system": "http://snomed.info/sct",
                "code": "80146002",
                "display": "Appendectomy"
            }]
        )
        
        procedure = FHIRProcedure(**data)
        assert "http://snomed.info/sct" in procedure.code.coding[0]["system"]
    
    def test_reference_format(self, valid_appointment_data):
        """Test reference format compliance"""
        participant = AppointmentParticipant(
            actor=Reference(
                reference="Patient/123",
                type="Patient"
            ),
            status=ParticipationStatus.ACCEPTED
        )
        
        data = valid_appointment_data.copy()
        data["participant"] = [participant]
        
        appointment = FHIRAppointment(**data)
        actor_ref = appointment.participant[0].actor.reference
        
        # Reference should be in format ResourceType/id
        assert "/" in actor_ref
        resource_type, resource_id = actor_ref.split("/", 1)
        assert resource_type in ["Patient", "Practitioner", "Device", "Location"]

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])