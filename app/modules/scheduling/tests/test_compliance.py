"""
HIPAA and SOC2 compliance tests for appointment scheduling module
Validates regulatory requirements and audit controls
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.scheduling.models import Appointment, AppointmentAuditLog
from app.modules.scheduling.service import AppointmentService
from app.core.audit_logger import AuditContext


class TestHIPAACompliance:
    """Test HIPAA Privacy and Security Rule compliance"""

    @pytest.fixture
    def appointment_service(self):
        return AppointmentService()

    @pytest.fixture
    def mock_db(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def hipaa_audit_context(self):
        return AuditContext(
            user_id=str(uuid.uuid4()),
            ip_address="192.168.1.100",
            user_agent="Healthcare-App/1.0",
            request_id=str(uuid.uuid4()),
            action="appointment_access",
            resource_type="appointment",
            compliance_context="hipaa"
        )

    @pytest.mark.asyncio
    async def test_hipaa_164_308_information_access_management(
        self, appointment_service, mock_db, hipaa_audit_context
    ):
        """
        Test HIPAA 164.308(a)(4) - Information Access Management
        Verify user access controls and authorization
        """
        appointment_id = str(uuid.uuid4())
        
        # Test authorized access (healthcare provider)
        authorized_user = {
            "user_id": str(uuid.uuid4()),
            "role": "practitioner",
            "organization_id": "org123",
            "clearance_level": "phi_access"
        }
        
        access_granted = await appointment_service.verify_hipaa_access_authorization(
            user=authorized_user,
            appointment_id=appointment_id,
            access_purpose="treatment",
            audit_context=hipaa_audit_context
        )
        assert access_granted
        
        # Test unauthorized access (billing staff accessing clinical notes)
        unauthorized_user = {
            "user_id": str(uuid.uuid4()),
            "role": "billing",
            "organization_id": "org123",
            "clearance_level": "limited_phi"
        }
        
        access_granted = await appointment_service.verify_hipaa_access_authorization(
            user=unauthorized_user,
            appointment_id=appointment_id,
            access_purpose="clinical_review",  # Outside billing scope
            audit_context=hipaa_audit_context
        )
        assert not access_granted

    @pytest.mark.asyncio
    async def test_hipaa_164_312_audit_controls(
        self, appointment_service, mock_db, hipaa_audit_context
    ):
        """
        Test HIPAA 164.312(b) - Audit Controls
        Verify comprehensive audit logging for all PHI access
        """
        appointment_id = str(uuid.uuid4())
        patient_id = str(uuid.uuid4())
        
        # Test audit log creation for appointment access
        audit_log = await appointment_service.create_hipaa_audit_log(
            appointment_id=appointment_id,
            patient_id=patient_id,
            action="view_appointment",
            user_id=hipaa_audit_context.user_id,
            access_purpose="patient_care",
            phi_fields_accessed=["start_time", "practitioner_id", "notes"],
            context=hipaa_audit_context
        )
        
        # Verify required HIPAA audit fields
        assert audit_log["appointment_id"] == appointment_id
        assert audit_log["patient_id"] == patient_id
        assert audit_log["user_id"] == hipaa_audit_context.user_id
        assert audit_log["timestamp"] is not None
        assert audit_log["action"] == "view_appointment"
        assert audit_log["access_purpose"] == "patient_care"
        assert audit_log["phi_fields_accessed"] == ["start_time", "practitioner_id", "notes"]
        assert audit_log["ip_address"] == hipaa_audit_context.ip_address
        assert audit_log["user_agent"] == hipaa_audit_context.user_agent
        
        # Verify audit log immutability (cryptographic integrity)
        assert "integrity_hash" in audit_log
        assert "digital_signature" in audit_log
        assert len(audit_log["integrity_hash"]) == 64  # SHA-256

    @pytest.mark.asyncio
    async def test_hipaa_164_308_contingency_plan(
        self, appointment_service, mock_db
    ):
        """
        Test HIPAA 164.308(a)(7) - Contingency Plan
        Verify data backup and recovery procedures
        """
        # Test data backup verification
        backup_status = await appointment_service.verify_appointment_data_backup()
        
        assert backup_status["backup_enabled"] is True
        assert backup_status["last_backup"] is not None
        assert backup_status["backup_encryption"] == "AES-256-GCM"
        assert backup_status["backup_location"] == "encrypted_cloud_storage"
        assert backup_status["recovery_time_objective"] <= 4  # Hours
        assert backup_status["recovery_point_objective"] <= 1  # Hour

        # Test disaster recovery plan validation
        dr_plan = await appointment_service.validate_disaster_recovery_plan()
        
        assert dr_plan["plan_exists"] is True
        assert dr_plan["last_tested"] is not None
        assert dr_plan["test_frequency"] == "quarterly"
        assert dr_plan["data_integrity_verification"] is True

    @pytest.mark.asyncio
    async def test_hipaa_164_314_business_associate_controls(
        self, appointment_service, mock_db
    ):
        """
        Test HIPAA 164.314 - Business Associate Agreement compliance
        Verify third-party integration security controls
        """
        # Test business associate validation for external scheduling systems
        ba_integration = {
            "partner_id": "external_scheduling_system",
            "baa_signed": True,
            "baa_expiry": datetime.utcnow() + timedelta(days=365),
            "security_assessment_date": datetime.utcnow() - timedelta(days=30),
            "data_sharing_scope": ["appointment_times", "practitioner_ids"],
            "phi_sharing_approved": True
        }
        
        is_compliant = await appointment_service.validate_business_associate_compliance(
            ba_integration
        )
        assert is_compliant
        
        # Test non-compliant business associate
        non_compliant_ba = ba_integration.copy()
        non_compliant_ba["baa_signed"] = False
        
        is_compliant = await appointment_service.validate_business_associate_compliance(
            non_compliant_ba
        )
        assert not is_compliant


class TestSOC2Type2Compliance:
    """Test SOC2 Type 2 compliance controls"""

    @pytest.fixture
    def appointment_service(self):
        return AppointmentService()

    @pytest.mark.asyncio
    async def test_soc2_cc6_1_logical_access_controls(self, appointment_service):
        """
        Test SOC2 CC6.1 - Logical and Physical Access Controls
        Verify user authentication and authorization
        """
        # Test multi-factor authentication requirement
        user_session = {
            "user_id": str(uuid.uuid4()),
            "role": "admin",
            "mfa_verified": True,
            "session_start": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "ip_address": "192.168.1.100"
        }
        
        access_control_result = await appointment_service.validate_soc2_access_controls(
            user_session=user_session,
            requested_action="create_appointment",
            resource_sensitivity="high"
        )
        
        assert access_control_result["access_granted"] is True
        assert access_control_result["mfa_required"] is True
        assert access_control_result["mfa_verified"] is True
        
        # Test access denial for non-MFA session
        non_mfa_session = user_session.copy()
        non_mfa_session["mfa_verified"] = False
        
        access_control_result = await appointment_service.validate_soc2_access_controls(
            user_session=non_mfa_session,
            requested_action="create_appointment",
            resource_sensitivity="high"
        )
        
        assert access_control_result["access_granted"] is False
        assert "mfa_required" in access_control_result["denial_reason"]

    @pytest.mark.asyncio
    async def test_soc2_cc7_2_system_monitoring(self, appointment_service):
        """
        Test SOC2 CC7.2 - System Monitoring
        Verify continuous monitoring and logging
        """
        # Test system monitoring dashboard
        monitoring_data = await appointment_service.get_soc2_monitoring_metrics()
        
        # Verify required monitoring metrics
        assert "active_user_sessions" in monitoring_data
        assert "failed_login_attempts_last_hour" in monitoring_data
        assert "appointment_access_rate" in monitoring_data
        assert "system_resource_utilization" in monitoring_data
        assert "security_alert_count" in monitoring_data
        
        # Test anomaly detection
        anomaly_detection = await appointment_service.detect_soc2_anomalies()
        
        assert "unusual_access_patterns" in anomaly_detection
        assert "performance_degradation" in anomaly_detection
        assert "security_violations" in anomaly_detection
        assert "data_integrity_issues" in anomaly_detection

    @pytest.mark.asyncio
    async def test_soc2_cc8_1_change_management(self, appointment_service):
        """
        Test SOC2 CC8.1 - Change Management
        Verify controlled changes to system and data
        """
        # Test change request approval process
        change_request = {
            "change_id": str(uuid.uuid4()),
            "change_type": "appointment_schema_update",
            "requested_by": str(uuid.uuid4()),
            "business_justification": "Add FHIR R4 compliance fields",
            "impact_assessment": "low_risk",
            "rollback_plan": "revert_to_previous_schema",
            "testing_plan": "comprehensive_test_suite"
        }
        
        approval_status = await appointment_service.process_soc2_change_request(
            change_request
        )
        
        assert approval_status["change_approved"] is True
        assert approval_status["approval_timestamp"] is not None
        assert approval_status["approved_by"] is not None
        assert approval_status["change_window_scheduled"] is True
        
        # Test unauthorized change detection
        unauthorized_change = {
            "table_name": "appointments",
            "change_type": "schema_modification",
            "changed_by": "unknown_user",
            "change_timestamp": datetime.utcnow(),
            "approval_id": None
        }
        
        is_authorized = await appointment_service.validate_soc2_change_authorization(
            unauthorized_change
        )
        assert not is_authorized

    @pytest.mark.asyncio
    async def test_soc2_a1_2_performance_monitoring(self, appointment_service):
        """
        Test SOC2 A1.2 - Performance Monitoring
        Verify system availability and performance
        """
        # Test performance metrics collection
        performance_metrics = await appointment_service.collect_soc2_performance_metrics()
        
        assert "appointment_api_response_time" in performance_metrics
        assert "database_query_performance" in performance_metrics
        assert "system_uptime_percentage" in performance_metrics
        assert "concurrent_user_capacity" in performance_metrics
        
        # Verify SLA compliance
        sla_compliance = performance_metrics["sla_compliance"]
        assert sla_compliance["availability_target"] == 99.9  # 99.9% uptime
        assert sla_compliance["response_time_target"] <= 2.0  # 2 seconds max
        assert sla_compliance["current_availability"] >= 99.9
        
        # Test performance alerting
        performance_alerts = await appointment_service.check_soc2_performance_alerts()
        
        # Should have no critical alerts in healthy system
        critical_alerts = [
            alert for alert in performance_alerts 
            if alert["severity"] == "critical"
        ]
        assert len(critical_alerts) == 0


class TestDataRetentionCompliance:
    """Test data retention and purging compliance"""

    @pytest.fixture
    def appointment_service(self):
        return AppointmentService()

    @pytest.mark.asyncio
    async def test_appointment_data_retention_policy(self, appointment_service):
        """Test automated data retention policy enforcement"""
        # Test retention policy configuration
        retention_policy = await appointment_service.get_data_retention_policy()
        
        assert retention_policy["appointment_retention_years"] == 7  # HIPAA requirement
        assert retention_policy["audit_log_retention_years"] == 6
        assert retention_policy["automated_purging"] is True
        assert retention_policy["data_anonymization_enabled"] is True
        
        # Test appointment eligibility for retention actions
        old_completed_appointment = {
            "id": str(uuid.uuid4()),
            "status": "completed",
            "end_time": datetime.utcnow() - timedelta(days=2555),  # ~7 years
            "last_accessed": datetime.utcnow() - timedelta(days=365),
            "patient_deceased": False
        }
        
        retention_action = await appointment_service.determine_retention_action(
            old_completed_appointment
        )
        
        assert retention_action["action"] == "anonymize"
        assert retention_action["eligible_for_purging"] is True
        assert retention_action["legal_hold"] is False

    @pytest.mark.asyncio
    async def test_data_anonymization_process(self, appointment_service):
        """Test PHI anonymization for expired appointments"""
        appointment_data = {
            "id": str(uuid.uuid4()),
            "patient_id": str(uuid.uuid4()),
            "practitioner_id": str(uuid.uuid4()),
            "notes": "Patient John Doe discussed treatment options",
            "location": "Room 101, Main Hospital",
            "contact_info": "john.doe@email.com, 555-1234"
        }
        
        # Test anonymization process
        anonymized_data = await appointment_service.anonymize_appointment_data(
            appointment_data
        )
        
        # Verify PHI removal
        assert anonymized_data["patient_id"] != appointment_data["patient_id"]
        assert "John Doe" not in anonymized_data["notes"]
        assert "email.com" not in anonymized_data.get("contact_info", "")
        assert "555-1234" not in anonymized_data.get("contact_info", "")
        
        # Verify research value preservation
        assert anonymized_data["id"] == appointment_data["id"]  # Research linkage
        assert anonymized_data["appointment_type"] == appointment_data.get("appointment_type")
        assert anonymized_data["duration_minutes"] == appointment_data.get("duration_minutes")

    @pytest.mark.asyncio
    async def test_secure_data_purging(self, appointment_service):
        """Test secure data purging procedures"""
        purge_request = {
            "appointment_ids": [str(uuid.uuid4()) for _ in range(5)],
            "purge_reason": "retention_policy_expired",
            "authorized_by": str(uuid.uuid4()),
            "legal_verification": True
        }
        
        # Test purging process
        purge_result = await appointment_service.execute_secure_data_purge(
            purge_request
        )
        
        assert purge_result["purge_successful"] is True
        assert purge_result["records_purged"] == 5
        assert purge_result["purge_method"] == "cryptographic_erasure"
        assert purge_result["verification_audit_id"] is not None
        
        # Verify purge audit trail
        purge_audit = purge_result["audit_trail"]
        assert purge_audit["authorized_by"] == purge_request["authorized_by"]
        assert purge_audit["legal_verification"] is True
        assert purge_audit["cryptographic_verification"] is True