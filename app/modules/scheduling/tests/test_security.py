"""
Security-focused tests for appointment scheduling module
Following TDD principles and SOC2 Type II compliance
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import SecurityManager
from app.core.audit_logger import AuditContext
from app.modules.scheduling.schemas import AppointmentCreate, AppointmentUpdate
from app.modules.scheduling.models import Appointment, AppointmentAuditLog
from app.modules.scheduling.security import SchedulingSecurityManager


class TestSchedulingSecurityManager:
    """Test security controls for appointment scheduling"""

    @pytest.fixture
    def security_manager(self):
        return SchedulingSecurityManager()

    @pytest.fixture
    def sample_appointment_data(self):
        return {
            "patient_id": str(uuid.uuid4()),
            "practitioner_id": str(uuid.uuid4()),
            "start_time": datetime.utcnow() + timedelta(days=1),
            "end_time": datetime.utcnow() + timedelta(days=1, hours=1),
            "appointment_type": "consultation",
            "status": "scheduled",
            "notes": "Patient consultation for diabetes management",
            "location": "Room 101"
        }

    @pytest.mark.asyncio
    async def test_encrypt_appointment_phi(self, security_manager, sample_appointment_data):
        """Test that PHI in appointments is properly encrypted"""
        # Test encryption of sensitive fields
        encrypted_notes = await security_manager.encrypt_phi_field(
            sample_appointment_data["notes"]
        )
        encrypted_location = await security_manager.encrypt_phi_field(
            sample_appointment_data["location"]
        )
        
        # Verify encryption occurred
        assert encrypted_notes != sample_appointment_data["notes"]
        assert encrypted_location != sample_appointment_data["location"]
        
        # Verify decryption works
        decrypted_notes = await security_manager.decrypt_phi_field(encrypted_notes)
        decrypted_location = await security_manager.decrypt_phi_field(encrypted_location)
        
        assert decrypted_notes == sample_appointment_data["notes"]
        assert decrypted_location == sample_appointment_data["location"]

    @pytest.mark.asyncio
    async def test_appointment_access_audit_logging(self, security_manager, sample_appointment_data):
        """Test that all appointment access is audited per HIPAA requirements"""
        user_id = str(uuid.uuid4())
        appointment_id = str(uuid.uuid4())
        
        # Test audit log creation for appointment access
        audit_entry = await security_manager.log_appointment_access(
            appointment_id=appointment_id,
            user_id=user_id,
            action="view",
            ip_address="192.168.1.100",
            user_agent="test-agent",
            access_purpose="patient_care"
        )
        
        # Verify audit entry contains required HIPAA fields
        assert audit_entry["appointment_id"] == appointment_id
        assert audit_entry["user_id"] == user_id
        assert audit_entry["action"] == "view"
        assert audit_entry["timestamp"] is not None
        assert audit_entry["ip_address"] == "192.168.1.100"
        assert audit_entry["access_purpose"] == "patient_care"
        
        # Verify audit entry is immutable (contains cryptographic hash)
        assert "integrity_hash" in audit_entry
        assert len(audit_entry["integrity_hash"]) == 64  # SHA-256 hash

    @pytest.mark.asyncio
    async def test_role_based_appointment_access(self, security_manager):
        """Test role-based access control for appointments"""
        # Test admin access (should have full access)
        admin_permissions = await security_manager.get_user_permissions(
            user_role="admin",
            resource_type="appointment"
        )
        assert "create" in admin_permissions
        assert "read" in admin_permissions
        assert "update" in admin_permissions
        assert "delete" in admin_permissions
        
        # Test operator access (limited access)
        operator_permissions = await security_manager.get_user_permissions(
            user_role="operator",
            resource_type="appointment"
        )
        assert "create" in operator_permissions
        assert "read" in operator_permissions
        assert "update" in operator_permissions
        assert "delete" not in operator_permissions
        
        # Test user access (read-only for own appointments)
        user_permissions = await security_manager.get_user_permissions(
            user_role="user",
            resource_type="appointment"
        )
        assert "read" in user_permissions
        assert "create" not in user_permissions
        assert "update" not in user_permissions
        assert "delete" not in user_permissions

    @pytest.mark.asyncio
    async def test_appointment_data_validation(self, security_manager, sample_appointment_data):
        """Test security validation of appointment data"""
        # Test valid appointment data
        is_valid, errors = await security_manager.validate_appointment_data(
            sample_appointment_data
        )
        assert is_valid
        assert len(errors) == 0
        
        # Test appointment with invalid patient_id
        invalid_data = sample_appointment_data.copy()
        invalid_data["patient_id"] = "invalid-uuid"
        
        is_valid, errors = await security_manager.validate_appointment_data(invalid_data)
        assert not is_valid
        assert "patient_id" in str(errors)
        
        # Test appointment with SQL injection attempt
        malicious_data = sample_appointment_data.copy()
        malicious_data["notes"] = "'; DROP TABLE appointments; --"
        
        is_valid, errors = await security_manager.validate_appointment_data(malicious_data)
        assert not is_valid
        assert "security_violation" in str(errors)

    @pytest.mark.asyncio
    async def test_appointment_time_slot_security(self, security_manager):
        """Test security controls for appointment time slot management"""
        practitioner_id = str(uuid.uuid4())
        base_time = datetime.utcnow() + timedelta(days=1)
        
        # Test double booking prevention
        slot1 = {
            "practitioner_id": practitioner_id,
            "start_time": base_time,
            "end_time": base_time + timedelta(hours=1)
        }
        
        slot2 = {
            "practitioner_id": practitioner_id,
            "start_time": base_time + timedelta(minutes=30),
            "end_time": base_time + timedelta(hours=1, minutes=30)
        }
        
        # First slot should be valid
        is_valid = await security_manager.validate_time_slot_availability(slot1, [])
        assert is_valid
        
        # Second slot should conflict
        is_valid = await security_manager.validate_time_slot_availability(slot2, [slot1])
        assert not is_valid

    @pytest.mark.asyncio
    async def test_phi_field_masking(self, security_manager, sample_appointment_data):
        """Test PHI field masking for non-authorized users"""
        # Test full data for authorized user
        authorized_data = await security_manager.mask_phi_fields(
            sample_appointment_data,
            user_role="admin",
            access_purpose="patient_care"
        )
        assert authorized_data["notes"] == sample_appointment_data["notes"]
        assert authorized_data["location"] == sample_appointment_data["location"]
        
        # Test masked data for unauthorized user
        masked_data = await security_manager.mask_phi_fields(
            sample_appointment_data,
            user_role="guest",
            access_purpose="research"
        )
        assert masked_data["notes"] == "[REDACTED]"
        assert masked_data["location"] == "[REDACTED]"
        assert masked_data["patient_id"] != sample_appointment_data["patient_id"]  # Should be anonymized


class TestComplianceValidation:
    """Test SOC2 Type II and HIPAA compliance for appointment scheduling"""

    @pytest.mark.asyncio
    async def test_soc2_audit_trail_integrity(self):
        """Test SOC2 CC7.2 - Audit trail integrity and completeness"""
        security_manager = SchedulingSecurityManager()
        
        # Create multiple audit entries
        entries = []
        for i in range(5):
            entry = await security_manager.log_appointment_access(
                appointment_id=str(uuid.uuid4()),
                user_id=str(uuid.uuid4()),
                action=f"action_{i}",
                ip_address="192.168.1.100",
                user_agent="test-agent",
                access_purpose="patient_care"
            )
            entries.append(entry)
        
        # Verify audit trail chain integrity
        is_valid = await security_manager.verify_audit_chain_integrity(entries)
        assert is_valid
        
        # Test tampered audit entry detection
        entries[2]["action"] = "tampered_action"
        is_valid = await security_manager.verify_audit_chain_integrity(entries)
        assert not is_valid

    @pytest.mark.asyncio
    async def test_hipaa_minimum_necessary_standard(self):
        """Test HIPAA minimum necessary standard implementation"""
        security_manager = SchedulingSecurityManager()
        
        appointment_data = {
            "patient_id": str(uuid.uuid4()),
            "practitioner_id": str(uuid.uuid4()),
            "start_time": datetime.utcnow() + timedelta(days=1),
            "appointment_type": "consultation",
            "notes": "Sensitive medical information",
            "insurance_info": "Policy #12345",
            "emergency_contact": "John Doe - 555-1234"
        }
        
        # Test billing staff access (should see insurance info)
        billing_view = await security_manager.apply_minimum_necessary_filter(
            appointment_data,
            user_role="billing",
            access_purpose="billing"
        )
        assert "insurance_info" in billing_view
        assert "notes" not in billing_view
        
        # Test scheduling staff access (should see basic info only)
        scheduling_view = await security_manager.apply_minimum_necessary_filter(
            appointment_data,
            user_role="scheduler",
            access_purpose="scheduling"
        )
        assert "start_time" in scheduling_view
        assert "notes" not in scheduling_view
        assert "insurance_info" not in scheduling_view

    @pytest.mark.asyncio
    async def test_data_retention_compliance(self):
        """Test automated data retention and purging compliance"""
        security_manager = SchedulingSecurityManager()
        
        # Test appointment eligibility for purging
        old_appointment = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.utcnow() - timedelta(days=2555),  # ~7 years old
            "status": "completed",
            "last_accessed": datetime.utcnow() - timedelta(days=365)
        }
        
        new_appointment = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.utcnow() - timedelta(days=30),
            "status": "scheduled",
            "last_accessed": datetime.utcnow() - timedelta(days=1)
        }
        
        # Old completed appointment should be eligible for purging
        is_eligible = await security_manager.is_eligible_for_purging(old_appointment)
        assert is_eligible
        
        # New appointment should not be eligible
        is_eligible = await security_manager.is_eligible_for_purging(new_appointment)
        assert not is_eligible

    @pytest.mark.asyncio
    async def test_breach_detection_and_alerting(self):
        """Test security breach detection and automated alerting"""
        security_manager = SchedulingSecurityManager()
        
        # Simulate suspicious access pattern
        suspicious_events = [
            {
                "user_id": "user123",
                "action": "bulk_export",
                "appointment_count": 1000,
                "timestamp": datetime.utcnow(),
                "ip_address": "192.168.1.100"
            },
            {
                "user_id": "user123",
                "action": "access_after_hours",
                "timestamp": datetime.utcnow().replace(hour=2),  # 2 AM
                "ip_address": "10.0.0.1"  # Different IP
            }
        ]
        
        # Test breach detection
        alerts = await security_manager.analyze_security_events(suspicious_events)
        
        assert len(alerts) > 0
        assert any("bulk_access" in alert["type"] for alert in alerts)
        assert any("unusual_access_time" in alert["type"] for alert in alerts)
        assert any("ip_address_change" in alert["type"] for alert in alerts)


class TestFHIRCompliance:
    """Test FHIR R4 compliance for appointment scheduling"""

    @pytest.mark.asyncio
    async def test_fhir_appointment_resource_structure(self):
        """Test FHIR R4 Appointment resource compliance"""
        from app.modules.scheduling.fhir import FHIRAppointmentConverter
        
        converter = FHIRAppointmentConverter()
        
        appointment_data = {
            "id": str(uuid.uuid4()),
            "patient_id": str(uuid.uuid4()),
            "practitioner_id": str(uuid.uuid4()),
            "start_time": datetime.utcnow() + timedelta(days=1),
            "end_time": datetime.utcnow() + timedelta(days=1, hours=1),
            "status": "booked",
            "appointment_type": "consultation",
            "location": "Room 101"
        }
        
        # Convert to FHIR format
        fhir_resource = await converter.to_fhir_appointment(appointment_data)
        
        # Verify FHIR R4 structure
        assert fhir_resource["resourceType"] == "Appointment"
        assert "id" in fhir_resource
        assert "status" in fhir_resource
        assert "start" in fhir_resource
        assert "end" in fhir_resource
        assert "participant" in fhir_resource
        
        # Verify participant structure
        participants = fhir_resource["participant"]
        assert len(participants) >= 2  # Patient and practitioner
        
        patient_participant = next(
            p for p in participants 
            if p["actor"]["reference"].startswith("Patient/")
        )
        assert patient_participant["status"] == "accepted"
        
    @pytest.mark.asyncio
    async def test_fhir_interoperability_validation(self):
        """Test FHIR interoperability and validation"""
        from app.modules.scheduling.fhir import FHIRValidator
        
        validator = FHIRValidator()
        
        valid_fhir_appointment = {
            "resourceType": "Appointment",
            "id": "example-appointment",
            "status": "booked",
            "start": "2024-12-25T10:00:00Z",
            "end": "2024-12-25T11:00:00Z",
            "participant": [
                {
                    "actor": {"reference": "Patient/123"},
                    "status": "accepted"
                },
                {
                    "actor": {"reference": "Practitioner/456"},
                    "status": "accepted"
                }
            ]
        }
        
        # Test valid FHIR resource
        is_valid, errors = await validator.validate_fhir_appointment(valid_fhir_appointment)
        assert is_valid
        assert len(errors) == 0
        
        # Test invalid FHIR resource
        invalid_fhir_appointment = valid_fhir_appointment.copy()
        del invalid_fhir_appointment["status"]  # Required field
        
        is_valid, errors = await validator.validate_fhir_appointment(invalid_fhir_appointment)
        assert not is_valid
        assert "status" in str(errors)