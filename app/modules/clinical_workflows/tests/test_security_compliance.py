"""
Clinical Workflows Security & Compliance Tests

Comprehensive testing of security features, PHI protection, FHIR compliance,
and SOC2/HIPAA requirements for the clinical workflows module.
"""

import pytest
import json
import re
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from app.modules.clinical_workflows.security import (
    ClinicalWorkflowSecurity, ClinicalSecurityError, ConsentVerificationError,
    FHIRValidationError, ProviderAuthorizationError, PHIEncryptionError
)
from app.modules.clinical_workflows.schemas import (
    WorkflowType, EncounterClass, VitalSigns, ClinicalCode
)
from app.core.database_unified import DataClassification


class TestPHIEncryptionSecurity:
    """Test PHI encryption and decryption security."""
    
    @pytest.fixture
    def mock_encryption_service(self):
        """Mock encryption service."""
        service = AsyncMock()
        service.encrypt.return_value = "encrypted_data_hash"
        service.decrypt.return_value = "decrypted_plain_text"
        return service
    
    @pytest.fixture
    def mock_audit_service(self):
        """Mock audit service."""
        service = AsyncMock()
        service.log_phi_access = AsyncMock()
        service.log_event = AsyncMock()
        return service
    
    @pytest.fixture
    def security_manager(self, mock_encryption_service, mock_audit_service):
        """Create security manager with mocked dependencies."""
        return ClinicalWorkflowSecurity(mock_encryption_service, mock_audit_service)
    
    @pytest.mark.asyncio
    async def test_encrypt_clinical_field_success(self, security_manager, mock_encryption_service, mock_audit_service):
        """Test successful PHI field encryption."""
        field_data = "Patient has chest pain and shortness of breath"
        patient_id = str(uuid4())
        workflow_id = str(uuid4())
        
        result = await security_manager.encrypt_clinical_field(
            data=field_data,
            field_name="chief_complaint",
            patient_id=patient_id,
            workflow_id=workflow_id
        )
        
        # Verify encryption service called with correct context
        mock_encryption_service.encrypt.assert_called_once()
        call_args = mock_encryption_service.encrypt.call_args
        assert call_args[0][0] == field_data  # Data to encrypt
        
        context = call_args[1]["context"]
        assert context["field"] == "clinical_chief_complaint"
        assert context["patient_id"] == patient_id
        assert context["data_type"] == "PHI"
        assert context["workflow_id"] == workflow_id
        
        # Verify audit logging
        mock_audit_service.log_phi_access.assert_called_once_with(
            action="encrypt_clinical_field",
            field_type="chief_complaint",
            patient_id=patient_id,
            additional_data={"workflow_id": workflow_id}
        )
        
        assert result == "encrypted_data_hash"
    
    @pytest.mark.asyncio
    async def test_encrypt_clinical_field_json_data(self, security_manager, mock_encryption_service):
        """Test encryption of JSON data structures."""
        field_data = {
            "vital_signs": {
                "blood_pressure": "140/90",
                "heart_rate": 95,
                "temperature": 98.6
            },
            "allergies": ["Penicillin", "Latex"]
        }
        
        await security_manager.encrypt_clinical_field(
            data=field_data,
            field_name="vital_signs",
            patient_id=str(uuid4())
        )
        
        # Verify JSON serialization
        call_args = mock_encryption_service.encrypt.call_args
        encrypted_data = call_args[0][0]
        
        # Should be JSON string
        parsed_data = json.loads(encrypted_data)
        assert parsed_data["vital_signs"]["heart_rate"] == 95
        assert "Penicillin" in parsed_data["allergies"]
    
    @pytest.mark.asyncio
    async def test_decrypt_clinical_field_success(self, security_manager, mock_encryption_service, mock_audit_service):
        """Test successful PHI field decryption."""
        encrypted_data = "encrypted_field_data"
        patient_id = str(uuid4())
        user_id = str(uuid4())
        workflow_id = str(uuid4())
        
        # Mock decryption to return JSON
        mock_encryption_service.decrypt.return_value = '{"test": "data"}'
        
        result = await security_manager.decrypt_clinical_field(
            encrypted_data=encrypted_data,
            field_name="assessment",
            patient_id=patient_id,
            user_id=user_id,
            access_purpose="clinical_review",
            workflow_id=workflow_id
        )
        
        # Verify decryption service called
        mock_encryption_service.decrypt.assert_called_once()
        call_args = mock_encryption_service.decrypt.call_args
        assert call_args[0][0] == encrypted_data
        
        context = call_args[1]["context"]
        assert context["field"] == "clinical_assessment"
        assert context["patient_id"] == patient_id
        
        # Verify audit logging
        mock_audit_service.log_phi_access.assert_called_once_with(
            action="decrypt_clinical_field",
            field_type="assessment",
            patient_id=patient_id,
            user_id=user_id,
            access_purpose="clinical_review",
            additional_data={"workflow_id": workflow_id}
        )
        
        # Should return parsed JSON
        assert result == {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_decrypt_clinical_field_plain_text(self, security_manager, mock_encryption_service):
        """Test decryption of plain text (non-JSON) data."""
        mock_encryption_service.decrypt.return_value = "Plain text clinical note"
        
        result = await security_manager.decrypt_clinical_field(
            encrypted_data="encrypted_data",
            field_name="notes",
            patient_id=str(uuid4()),
            user_id=str(uuid4()),
            access_purpose="review"
        )
        
        # Should return plain string
        assert result == "Plain text clinical note"
    
    @pytest.mark.asyncio
    async def test_encryption_error_handling(self, security_manager, mock_encryption_service):
        """Test encryption error handling."""
        # Mock encryption failure
        mock_encryption_service.encrypt.side_effect = Exception("Encryption failed")
        
        with pytest.raises(ClinicalSecurityError) as exc_info:
            await security_manager.encrypt_clinical_field(
                data="test data",
                field_name="test_field",
                patient_id=str(uuid4())
            )
        
        assert "Failed to encrypt clinical field test_field" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_decryption_error_handling(self, security_manager, mock_encryption_service):
        """Test decryption error handling."""
        # Mock decryption failure
        mock_encryption_service.decrypt.side_effect = Exception("Decryption failed")
        
        with pytest.raises(ClinicalSecurityError) as exc_info:
            await security_manager.decrypt_clinical_field(
                encrypted_data="encrypted_data",
                field_name="test_field",
                patient_id=str(uuid4()),
                user_id=str(uuid4()),
                access_purpose="test"
            )
        
        assert "Failed to decrypt clinical field test_field" in str(exc_info.value)


class TestProviderPermissions:
    """Test provider permission validation."""
    
    @pytest.fixture
    def security_manager(self):
        mock_encryption = AsyncMock()
        mock_audit = AsyncMock()
        return ClinicalWorkflowSecurity(mock_encryption, mock_audit)
    
    @pytest.mark.asyncio
    async def test_validate_provider_permissions_success(self, security_manager):
        """Test successful provider permission validation."""
        provider_id = str(uuid4())
        patient_id = str(uuid4())
        
        result = await security_manager.validate_provider_permissions(
            provider_id=provider_id,
            patient_id=patient_id,
            action="create_workflow",
            workflow_type=WorkflowType.ENCOUNTER
        )
        
        assert result is True
        
        # Verify audit logging
        security_manager.audit_service.log_event.assert_called_once_with(
            event_type="PROVIDER_PERMISSION_CHECK",
            user_id=provider_id,
            additional_data={
                "patient_id": patient_id,
                "action": "create_workflow",
                "workflow_type": WorkflowType.ENCOUNTER.value,
                "result": "granted"
            }
        )
    
    @pytest.mark.asyncio
    async def test_validate_provider_permissions_missing_ids(self, security_manager):
        """Test permission validation with missing IDs."""
        # Missing provider ID
        result = await security_manager.validate_provider_permissions(
            provider_id="",
            patient_id=str(uuid4()),
            action="test_action"
        )
        assert result is False
        
        # Missing patient ID
        result = await security_manager.validate_provider_permissions(
            provider_id=str(uuid4()),
            patient_id="",
            action="test_action"
        )
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_provider_permissions_error_handling(self, security_manager):
        """Test permission validation error handling."""
        # Mock audit service failure
        security_manager.audit_service.log_event.side_effect = Exception("Audit failed")
        
        result = await security_manager.validate_provider_permissions(
            provider_id=str(uuid4()),
            patient_id=str(uuid4()),
            action="test_action"
        )
        
        # Should return False on error
        assert result is False


class TestConsentVerification:
    """Test patient consent verification."""
    
    @pytest.fixture
    def security_manager(self):
        mock_encryption = AsyncMock()
        mock_audit = AsyncMock()
        return ClinicalWorkflowSecurity(mock_encryption, mock_audit)
    
    @pytest.mark.asyncio
    async def test_verify_clinical_consent_success(self, security_manager):
        """Test successful consent verification."""
        patient_id = str(uuid4())
        user_id = str(uuid4())
        
        consent_verified, consent_id = await security_manager.verify_clinical_consent(
            patient_id=patient_id,
            workflow_type=WorkflowType.ENCOUNTER,
            user_id=user_id
        )
        
        assert consent_verified is True
        assert consent_id is not None
        assert consent_id.startswith(f"consent_{patient_id}")
        
        # Verify audit logging
        security_manager.audit_service.log_event.assert_called_once_with(
            event_type="CONSENT_VERIFICATION",
            user_id=user_id,
            additional_data={
                "patient_id": patient_id,
                "workflow_type": WorkflowType.ENCOUNTER.value,
                "required_consent": "treatment",
                "result": "verified"
            }
        )
    
    @pytest.mark.asyncio
    async def test_verify_emergency_consent(self, security_manager):
        """Test emergency consent verification."""
        patient_id = str(uuid4())
        user_id = str(uuid4())
        
        consent_verified, consent_id = await security_manager.verify_clinical_consent(
            patient_id=patient_id,
            workflow_type=WorkflowType.EMERGENCY,
            user_id=user_id
        )
        
        assert consent_verified is True
        
        # Verify emergency access consent type
        call_args = security_manager.audit_service.log_event.call_args
        additional_data = call_args[1]["additional_data"]
        assert additional_data["required_consent"] == "emergency_access"
    
    @pytest.mark.asyncio
    async def test_consent_verification_error_handling(self, security_manager):
        """Test consent verification error handling."""
        # Mock audit service failure
        security_manager.audit_service.log_event.side_effect = Exception("Audit failed")
        
        consent_verified, consent_id = await security_manager.verify_clinical_consent(
            patient_id=str(uuid4()),
            workflow_type=WorkflowType.ENCOUNTER,
            user_id=str(uuid4())
        )
        
        assert consent_verified is False
        assert consent_id is None


class TestFHIRValidation:
    """Test FHIR R4 compliance validation."""
    
    @pytest.fixture
    def security_manager(self):
        mock_encryption = AsyncMock()
        mock_audit = AsyncMock()
        return ClinicalWorkflowSecurity(mock_encryption, mock_audit)
    
    def test_validate_fhir_encounter_success(self, security_manager):
        """Test successful FHIR encounter validation."""
        valid_encounter = {
            "encounter_class": "AMB",
            "encounter_status": "finished",
            "encounter_datetime": datetime.utcnow().isoformat(),
            "patient_id": str(uuid4()),
            "provider_id": str(uuid4())
        }
        
        is_valid, errors = security_manager.validate_fhir_encounter(valid_encounter)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_fhir_encounter_missing_fields(self, security_manager):
        """Test FHIR validation with missing required fields."""
        incomplete_encounter = {
            "encounter_status": "finished"
            # Missing encounter_class and other required fields
        }
        
        is_valid, errors = security_manager.validate_fhir_encounter(incomplete_encounter)
        
        assert is_valid is False
        assert any("encounter_class is required" in error for error in errors)
    
    def test_validate_fhir_encounter_invalid_class(self, security_manager):
        """Test FHIR validation with invalid encounter class."""
        invalid_encounter = {
            "encounter_class": "INVALID_CLASS",
            "encounter_status": "finished",
            "encounter_datetime": datetime.utcnow().isoformat(),
            "patient_id": str(uuid4()),
            "provider_id": str(uuid4())
        }
        
        is_valid, errors = security_manager.validate_fhir_encounter(invalid_encounter)
        
        assert is_valid is False
        assert any("Invalid encounter_class" in error for error in errors)
    
    def test_validate_fhir_encounter_invalid_datetime(self, security_manager):
        """Test FHIR validation with invalid datetime format."""
        invalid_encounter = {
            "encounter_class": "AMB",
            "encounter_status": "finished",
            "encounter_datetime": "invalid-datetime-format",
            "patient_id": str(uuid4()),
            "provider_id": str(uuid4())
        }
        
        is_valid, errors = security_manager.validate_fhir_encounter(invalid_encounter)
        
        assert is_valid is False
        assert any("Invalid encounter_datetime format" in error for error in errors)
    
    def test_validate_fhir_encounter_invalid_uuid(self, security_manager):
        """Test FHIR validation with invalid UUID format."""
        invalid_encounter = {
            "encounter_class": "AMB",
            "encounter_status": "finished",
            "encounter_datetime": datetime.utcnow().isoformat(),
            "patient_id": "invalid-uuid",
            "provider_id": str(uuid4())
        }
        
        is_valid, errors = security_manager.validate_fhir_encounter(invalid_encounter)
        
        assert is_valid is False
        assert any("Invalid patient_id format" in error for error in errors)


class TestClinicalCodeValidation:
    """Test clinical code validation (ICD-10, CPT, SNOMED)."""
    
    @pytest.fixture
    def security_manager(self):
        mock_encryption = AsyncMock()
        mock_audit = AsyncMock()
        return ClinicalWorkflowSecurity(mock_encryption, mock_audit)
    
    def test_validate_icd10_codes_success(self, security_manager):
        """Test successful ICD-10 code validation."""
        valid_codes = [
            ClinicalCode(
                code="R06.02",
                display="Shortness of breath",
                system="http://hl7.org/fhir/sid/icd-10-cm"
            ),
            ClinicalCode(
                code="I10",
                display="Essential hypertension",
                system="http://hl7.org/fhir/sid/icd-10-cm"
            )
        ]
        
        is_valid, errors = security_manager.validate_clinical_codes(valid_codes)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_cpt_codes_success(self, security_manager):
        """Test successful CPT code validation."""
        valid_codes = [
            ClinicalCode(
                code="99213",
                display="Office visit, established patient",
                system="http://www.ama-assn.org/go/cpt"
            ),
            ClinicalCode(
                code="93000",
                display="Electrocardiogram",
                system="http://www.ama-assn.org/go/cpt"
            )
        ]
        
        is_valid, errors = security_manager.validate_clinical_codes(valid_codes)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_snomed_codes_success(self, security_manager):
        """Test successful SNOMED code validation."""
        valid_codes = [
            ClinicalCode(
                code="185349003",
                display="Encounter for check up",
                system="http://snomed.info/sct"
            )
        ]
        
        is_valid, errors = security_manager.validate_clinical_codes(valid_codes)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_invalid_icd10_codes(self, security_manager):
        """Test invalid ICD-10 code validation."""
        invalid_codes = [
            ClinicalCode(
                code="INVALID",
                display="Invalid code",
                system="http://hl7.org/fhir/sid/icd-10-cm"
            ),
            ClinicalCode(
                code="123",
                display="Another invalid code",
                system="http://hl7.org/fhir/sid/icd-10-cm"
            )
        ]
        
        is_valid, errors = security_manager.validate_clinical_codes(invalid_codes)
        
        assert is_valid is False
        assert any("Invalid ICD-10 code format" in error for error in errors)
    
    def test_validate_missing_required_fields(self, security_manager):
        """Test validation with missing required fields."""
        incomplete_codes = [
            ClinicalCode(
                code="R06.02",
                display="",  # Missing display
                system="http://hl7.org/fhir/sid/icd-10-cm"
            )
        ]
        
        is_valid, errors = security_manager.validate_clinical_codes(incomplete_codes)
        
        assert is_valid is False
        assert any("Missing required fields" in error for error in errors)


class TestVitalSignsValidation:
    """Test vital signs validation."""
    
    @pytest.fixture
    def security_manager(self):
        mock_encryption = AsyncMock()
        mock_audit = AsyncMock()
        return ClinicalWorkflowSecurity(mock_encryption, mock_audit)
    
    def test_validate_vital_signs_success(self, security_manager):
        """Test successful vital signs validation."""
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
        
        is_valid, errors = security_manager.validate_vital_signs(valid_vitals)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_vital_signs_out_of_range(self, security_manager):
        """Test vital signs validation with out-of-range values."""
        invalid_vitals = VitalSigns(
            systolic_bp=350,  # Too high
            diastolic_bp=80,
            heart_rate=15,    # Too low
            oxygen_saturation=110,  # Invalid (> 100)
            pain_score=15     # Too high
        )
        
        is_valid, errors = security_manager.validate_vital_signs(invalid_vitals)
        
        assert is_valid is False
        assert any("systolic_bp value 350 is outside normal range" in error for error in errors)
        assert any("heart_rate value 15 is outside normal range" in error for error in errors)
        assert any("oxygen_saturation value 110 is outside normal range" in error for error in errors)
        assert any("pain_score value 15 is outside normal range" in error for error in errors)
    
    def test_validate_blood_pressure_relationship(self, security_manager):
        """Test blood pressure relationship validation."""
        invalid_vitals = VitalSigns(
            systolic_bp=80,   # Lower than diastolic
            diastolic_bp=120  # Higher than systolic
        )
        
        is_valid, errors = security_manager.validate_vital_signs(invalid_vitals)
        
        assert is_valid is False
        assert any("Systolic BP must be greater than diastolic BP" in error for error in errors)
    
    def test_validate_bmi_calculation(self, security_manager):
        """Test BMI calculation validation."""
        # Correct BMI
        valid_vitals = VitalSigns(
            weight_kg=70.0,
            height_cm=175.0,
            bmi=22.9  # Correct BMI
        )
        
        is_valid, errors = security_manager.validate_vital_signs(valid_vitals)
        assert is_valid is True
        
        # Incorrect BMI
        invalid_vitals = VitalSigns(
            weight_kg=70.0,
            height_cm=175.0,
            bmi=30.0  # Incorrect BMI (should be ~22.9)
        )
        
        is_valid, errors = security_manager.validate_vital_signs(invalid_vitals)
        assert is_valid is False
        assert any("BMI calculation mismatch" in error for error in errors)


class TestPHIDetection:
    """Test PHI detection in clinical text."""
    
    @pytest.fixture
    def security_manager(self):
        mock_encryption = AsyncMock()
        mock_audit = AsyncMock()
        return ClinicalWorkflowSecurity(mock_encryption, mock_audit)
    
    def test_detect_phi_ssn(self, security_manager):
        """Test SSN detection in clinical text."""
        text_with_ssn = "Patient SSN is 123-45-6789 for insurance verification"
        
        phi_detected = security_manager.detect_phi_in_text(text_with_ssn)
        
        assert len(phi_detected) == 1
        assert phi_detected[0]["type"] == "SSN"
        assert phi_detected[0]["value"] == "123-45-6789"
        assert phi_detected[0]["risk_level"] == "high"
    
    def test_detect_phi_phone(self, security_manager):
        """Test phone number detection."""
        text_with_phone = "Contact patient at 555-123-4567 for follow-up"
        
        phi_detected = security_manager.detect_phi_in_text(text_with_phone)
        
        assert len(phi_detected) == 1
        assert phi_detected[0]["type"] == "phone"
        assert phi_detected[0]["value"] == "555-123-4567"
        assert phi_detected[0]["risk_level"] == "medium"
    
    def test_detect_phi_email(self, security_manager):
        """Test email detection."""
        text_with_email = "Patient email: john.doe@example.com for communications"
        
        phi_detected = security_manager.detect_phi_in_text(text_with_email)
        
        assert len(phi_detected) == 1
        assert phi_detected[0]["type"] == "email"
        assert phi_detected[0]["value"] == "john.doe@example.com"
        assert phi_detected[0]["risk_level"] == "medium"
    
    def test_detect_multiple_phi_types(self, security_manager):
        """Test detection of multiple PHI types."""
        text_with_multiple_phi = """
        Patient: John Doe
        SSN: 123-45-6789
        Phone: 555-123-4567
        Email: john.doe@example.com
        """
        
        phi_detected = security_manager.detect_phi_in_text(text_with_multiple_phi)
        
        assert len(phi_detected) == 3
        phi_types = [item["type"] for item in phi_detected]
        assert "SSN" in phi_types
        assert "phone" in phi_types
        assert "email" in phi_types
    
    def test_sanitize_clinical_text(self, security_manager):
        """Test clinical text sanitization."""
        text_with_phi = """
        Patient SSN: 123-45-6789
        Contact: 555-123-4567
        Email: patient@example.com
        Chief complaint: Chest pain
        """
        
        sanitized = security_manager.sanitize_clinical_text(text_with_phi)
        
        assert "XXX-XX-XXXX" in sanitized
        assert "XXX-XXX-XXXX" in sanitized
        assert "[EMAIL_REDACTED]" in sanitized
        assert "Chest pain" in sanitized  # Clinical content preserved
        
        # Verify PHI is removed
        assert "123-45-6789" not in sanitized
        assert "555-123-4567" not in sanitized
        assert "patient@example.com" not in sanitized


class TestWorkflowTransitionValidation:
    """Test workflow status transition validation."""
    
    @pytest.fixture
    def security_manager(self):
        mock_encryption = AsyncMock()
        mock_audit = AsyncMock()
        return ClinicalWorkflowSecurity(mock_encryption, mock_audit)
    
    @pytest.mark.asyncio
    async def test_valid_workflow_transitions(self, security_manager):
        """Test valid workflow status transitions."""
        from app.modules.clinical_workflows.schemas import WorkflowStatus
        
        user_id = str(uuid4())
        workflow_id = str(uuid4())
        
        # Valid transitions
        valid_transitions = [
            (WorkflowStatus.ACTIVE, WorkflowStatus.COMPLETED),
            (WorkflowStatus.ACTIVE, WorkflowStatus.CANCELLED),
            (WorkflowStatus.ACTIVE, WorkflowStatus.SUSPENDED),
            (WorkflowStatus.SUSPENDED, WorkflowStatus.ACTIVE),
            (WorkflowStatus.SUSPENDED, WorkflowStatus.CANCELLED)
        ]
        
        for current_status, new_status in valid_transitions:
            is_valid, error_msg = await security_manager.validate_workflow_transition(
                current_status=current_status,
                new_status=new_status,
                user_id=user_id,
                workflow_id=workflow_id
            )
            
            assert is_valid is True
            assert error_msg is None
    
    @pytest.mark.asyncio
    async def test_invalid_workflow_transitions(self, security_manager):
        """Test invalid workflow status transitions."""
        from app.modules.clinical_workflows.schemas import WorkflowStatus
        
        user_id = str(uuid4())
        workflow_id = str(uuid4())
        
        # Invalid transitions (from final states)
        invalid_transitions = [
            (WorkflowStatus.COMPLETED, WorkflowStatus.ACTIVE),
            (WorkflowStatus.CANCELLED, WorkflowStatus.ACTIVE),
            (WorkflowStatus.COMPLETED, WorkflowStatus.SUSPENDED)
        ]
        
        for current_status, new_status in invalid_transitions:
            is_valid, error_msg = await security_manager.validate_workflow_transition(
                current_status=current_status,
                new_status=new_status,
                user_id=user_id,
                workflow_id=workflow_id
            )
            
            assert is_valid is False
            assert error_msg is not None
            assert "Invalid transition" in error_msg
            
            # Verify audit logging of invalid transition
            security_manager.audit_service.log_event.assert_called_with(
                event_type="INVALID_WORKFLOW_TRANSITION",
                user_id=user_id,
                additional_data={
                    "workflow_id": workflow_id,
                    "current_status": current_status.value,
                    "attempted_status": new_status.value,
                    "error": error_msg
                }
            )


class TestRiskScoring:
    """Test clinical workflow risk scoring."""
    
    @pytest.fixture
    def security_manager(self):
        mock_encryption = AsyncMock()
        mock_audit = AsyncMock()
        return ClinicalWorkflowSecurity(mock_encryption, mock_audit)
    
    def test_calculate_risk_score_routine(self, security_manager):
        """Test risk score calculation for routine workflow."""
        workflow_data = {
            "priority": "routine",
            "workflow_type": "encounter"
        }
        
        risk_score = security_manager.calculate_risk_score(workflow_data)
        
        # Routine encounter should have low risk score
        assert 0 <= risk_score <= 30
    
    def test_calculate_risk_score_emergency(self, security_manager):
        """Test risk score calculation for emergency workflow."""
        workflow_data = {
            "priority": "emergency",
            "workflow_type": "emergency"
        }
        
        risk_score = security_manager.calculate_risk_score(workflow_data)
        
        # Emergency workflow should have high risk score
        assert 80 <= risk_score <= 100
    
    def test_calculate_risk_score_procedure(self, security_manager):
        """Test risk score calculation for procedure workflow."""
        workflow_data = {
            "priority": "urgent",
            "workflow_type": "procedure"
        }
        
        risk_score = security_manager.calculate_risk_score(workflow_data)
        
        # Urgent procedure should have medium-high risk score
        assert 40 <= risk_score <= 70
    
    def test_calculate_risk_score_capped_at_100(self, security_manager):
        """Test that risk score is capped at 100."""
        workflow_data = {
            "priority": "stat",      # 90 points
            "workflow_type": "emergency"  # 80 points
        }
        
        risk_score = security_manager.calculate_risk_score(workflow_data)
        
        # Should be capped at 100, not 170
        assert risk_score == 100
    
    def test_calculate_risk_score_error_handling(self, security_manager):
        """Test risk score calculation error handling."""
        # Invalid workflow data
        workflow_data = {}
        
        risk_score = security_manager.calculate_risk_score(workflow_data)
        
        # Should return default medium risk on error
        assert risk_score == 50


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])