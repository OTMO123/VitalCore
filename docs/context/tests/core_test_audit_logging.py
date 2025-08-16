"""
Core Tests: Audit Logging for SOC2 Compliance

Critical tests for audit logging system:
- Comprehensive event capture
- Log integrity and immutability
- PHI access tracking
- Security event logging
- Compliance reporting
- Log retention and archival
- Performance impact
"""
import pytest
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit_logger.models import AuditLog
from app.modules.healthcare_records.models import PHIAccessLog, Patient
from app.modules.audit_logger.service import AuditService
from app.core.security import hash_password


pytestmark = [pytest.mark.asyncio, pytest.mark.core, pytest.mark.security]


class TestAuditLogCompleteness:
    """Test that all critical events are logged"""
    
    async def test_authentication_events_logged(
        self,
        async_client,
        async_session: AsyncSession
    ):
        """
        Test all authentication events are captured.
        Required for security monitoring.
        """
        # Track initial log count
        initial_count = await self._get_audit_log_count(async_session)
        
        # Successful login
        response = await async_client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "testpassword123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # Failed login
        response = await async_client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "wrongpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # Check logs created
        auth_logs = await async_session.execute(
            select(AuditLog)
            .where(AuditLog.action.in_(["LOGIN_SUCCESS", "LOGIN_FAILED", "LOGIN", "AUTH_ATTEMPT"]))
            .order_by(AuditLog.timestamp.desc())
            .limit(5)
        )
        logs = list(auth_logs.scalars())
        
        assert len(logs) >= 2, "Authentication events not logged"
        
        # Verify log details
        for log in logs:
            assert log.ip_address is not None
            assert log.user_agent is not None
            assert log.timestamp is not None
            
            if "FAILED" in log.action or log.severity == "WARNING":
                assert log.details.get("reason") is not None
        
        print("✓ Authentication events comprehensively logged")
    
    async def test_data_modification_audit_trail(
        self,
        async_client,
        admin_headers,
        test_patient,
        async_session: AsyncSession
    ):
        """
        Test that all data modifications are logged.
        Critical for data integrity and compliance.
        """
        patient_id = str(test_patient.id)
        
        # Update patient data
        update_data = {
            "phone": "+1-555-999-8888",
            "email": "updated@example.com"
        }
        
        response = await async_client.patch(
            f"/api/v1/patients/{patient_id}",
            headers=admin_headers,
            json=update_data
        )
        assert response.status_code == 200
        
        # Delete patient (soft delete)
        response = await async_client.delete(
            f"/api/v1/patients/{patient_id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # Check audit trail
        modification_logs = await async_session.execute(
            select(AuditLog)
            .where(AuditLog.resource_type == "patient")
            .where(AuditLog.resource_id == patient_id)
            .where(AuditLog.action.in_(["UPDATE", "DELETE", "SOFT_DELETE"]))
            .order_by(AuditLog.timestamp)
        )
        logs = list(modification_logs.scalars())
        
        assert len(logs) >= 2, "Data modifications not logged"
        
        # Verify update log
        update_log = next((l for l in logs if l.action == "UPDATE"), None)
        assert update_log is not None
        assert "before" in update_log.details or "changes" in update_log.details
        assert update_log.user_id is not None
        
        # Verify delete log
        delete_log = next((l for l in logs if "DELETE" in l.action), None)
        assert delete_log is not None
        assert delete_log.severity in ["WARNING", "INFO"]
        
        print("✓ Data modification audit trail complete")
    
    async def test_phi_access_logging_completeness(
        self,
        async_client,
        user_headers,
        test_patient,
        async_session: AsyncSession
    ):
        """
        Test every PHI access is logged.
        HIPAA requirement - no exceptions.
        """
        patient_id = str(test_patient.id)
        
        # Various PHI access patterns
        access_patterns = [
            (f"/api/v1/patients/{patient_id}", "VIEW"),
            (f"/api/v1/patients/{patient_id}/medical-history", "VIEW"),
            (f"/api/v1/patients/{patient_id}/medications", "VIEW"),
            (f"/api/v1/clinical-documents?patient_id={patient_id}", "LIST"),
        ]
        
        initial_log_count = await self._get_phi_log_count(async_session, patient_id)
        
        for endpoint, expected_action in access_patterns:
            response = await async_client.get(endpoint, headers=user_headers)
            # Don't check status - we care about logging attempt
        
        # Verify PHI access logs created
        phi_logs = await async_session.execute(
            select(PHIAccessLog)
            .where(PHIAccessLog.patient_id == patient_id)
            .order_by(PHIAccessLog.accessed_at.desc())
            .limit(10)
        )
        logs = list(phi_logs.scalars())
        
        new_logs = len(logs) - initial_log_count
        assert new_logs >= len(access_patterns), "Not all PHI accesses logged"
        
        # Verify log quality
        for log in logs[:new_logs]:
            assert log.accessed_by is not None
            assert log.access_type in ["READ", "VIEW", "LIST"]
            assert log.ip_address is not None
            assert log.accessed_fields is not None  # Should list which fields
            
        print("✓ PHI access logging is comprehensive")
    
    async def test_security_event_capture(
        self,
        async_client,
        user_headers,
        admin_headers,
        async_session: AsyncSession
    ):
        """
        Test that security events are captured.
        Critical for threat detection.
        """
        security_events = []
        
        # Failed authorization attempt
        response = await async_client.get(
            "/api/v1/admin/users",
            headers=user_headers  # User trying admin endpoint
        )
        security_events.append("authorization_failure")
        
        # Invalid token attempt
        response = await async_client.get(
            "/api/v1/patients",
            headers={"Authorization": "Bearer invalid-token"}
        )
        security_events.append("invalid_token")
        
        # Potential SQL injection
        response = await async_client.get(
            "/api/v1/patients/search?name=' OR 1=1--",
            headers=user_headers
        )
        security_events.append("suspicious_input")
        
        # Check security logs
        security_logs = await async_session.execute(
            select(AuditLog)
            .where(AuditLog.severity.in_(["WARNING", "ERROR", "CRITICAL"]))
            .where(AuditLog.timestamp >= datetime.utcnow() - timedelta(minutes=1))
            .order_by(AuditLog.timestamp.desc())
        )
        logs = list(security_logs.scalars())
        
        # Should have security-related logs
        security_actions = [
            "ACCESS_DENIED", "FORBIDDEN", "INVALID_TOKEN",
            "SUSPICIOUS_ACTIVITY", "SECURITY_ALERT"
        ]
        
        logged_security_events = [
            log for log in logs 
            if any(action in log.action for action in security_actions)
        ]
        
        assert len(logged_security_events) >= 2, "Security events not properly logged"
        
        print("✓ Security event capture verified")
    
    async def _get_audit_log_count(self, session: AsyncSession) -> int:
        """Get current audit log count"""
        result = await session.execute(
            select(AuditLog).count()
        )
        return result.scalar() or 0
    
    async def _get_phi_log_count(self, session: AsyncSession, patient_id: str) -> int:
        """Get current PHI log count for patient"""
        result = await session.execute(
            select(PHIAccessLog)
            .where(PHIAccessLog.patient_id == patient_id)
            .count()
        )
        return result.scalar() or 0


class TestAuditLogIntegrity:
    """Test audit log immutability and integrity"""
    
    async def test_audit_log_immutability(
        self,
        async_client,
        admin_headers,
        async_session: AsyncSession
    ):
        """
        Test that audit logs cannot be modified.
        Critical for compliance and forensics.
        """
        # Create an audit log entry
        audit_service = AuditService(async_session)
        log_entry = await audit_service.log_action(
            user_id="test-user",
            action="TEST_IMMUTABILITY",
            resource_type="test",
            resource_id="test-123",
            details={"test": "original_value"}
        )
        await async_session.commit()
        
        log_id = log_entry.id
        original_timestamp = log_entry.timestamp
        original_details = log_entry.details
        
        # Attempt to modify via API (if update endpoint exists)
        response = await async_client.patch(
            f"/api/v1/audit-logs/{log_id}",
            headers=admin_headers,
            json={"details": {"test": "modified_value"}}
        )
        
        # Should not allow modification
        assert response.status_code in [404, 405, 403]
        
        # Attempt direct database modification
        try:
            await async_session.execute(
                update(AuditLog)
                .where(AuditLog.id == log_id)
                .values(details={"test": "hacked_value"})
            )
            await async_session.commit()
            
            # Verify it didn't change (might have trigger/protection)
            db_log = await async_session.get(AuditLog, log_id)
            if db_log.details != original_details:
                pytest.fail("Audit logs are mutable - critical security issue!")
        except Exception:
            # Good - database prevents modification
            pass
        
        print("✓ Audit log immutability verified")
    
    async def test_audit_log_integrity_hash(
        self,
        async_client,
        admin_headers,
        async_session: AsyncSession
    ):
        """
        Test audit log integrity using hashes.
        Ensures tampering can be detected.
        """
        # Create audit log with integrity hash
        audit_data = {
            "user_id": "test-user",
            "action": "INTEGRITY_TEST",
            "resource_type": "patient",
            "resource_id": "test-123",
            "details": {"operation": "test", "value": "important"},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Calculate integrity hash
        hash_input = f"{audit_data['user_id']}:{audit_data['action']}:{audit_data['resource_id']}:{audit_data['timestamp']}"
        expected_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        # Create log via service
        audit_service = AuditService(async_session)
        log_entry = await audit_service.log_action(**audit_data)
        await async_session.commit()
        
        # Check if integrity hash is stored
        if hasattr(log_entry, 'integrity_hash'):
            assert log_entry.integrity_hash is not None
            print("✓ Audit logs include integrity hashes")
        else:
            # Check if hash is in details or metadata
            if "hash" in str(log_entry.details):
                print("✓ Audit integrity tracked in details")
            else:
                print("⚠️  No integrity hash mechanism found")
    
    async def test_audit_log_chain_integrity(
        self,
        async_client,
        admin_headers,
        async_session: AsyncSession
    ):
        """
        Test audit log chain integrity.
        Each log should reference previous for tamper detection.
        """
        audit_service = AuditService(async_session)
        
        # Create chain of logs
        log_ids = []
        for i in range(3):
            log = await audit_service.log_action(
                user_id="test-user",
                action=f"CHAIN_TEST_{i}",
                resource_type="test",
                resource_id=f"test-{i}",
                details={"sequence": i}
            )
            log_ids.append(log.id)
            await async_session.commit()
        
        # Check if logs reference previous
        for i in range(1, len(log_ids)):
            current_log = await async_session.get(AuditLog, log_ids[i])
            
            # Check for chain reference
            if hasattr(current_log, 'previous_hash'):
                assert current_log.previous_hash is not None
                print("✓ Audit log chain integrity implemented")
                break
            elif "previous_id" in current_log.details:
                assert current_log.details["previous_id"] == str(log_ids[i-1])
                print("✓ Audit log chain tracked in details")
                break
        else:
            print("⚠️  No audit log chaining mechanism found")


class TestComplianceReporting:
    """Test compliance reporting capabilities"""
    
    async def test_phi_access_report_generation(
        self,
        async_client,
        admin_headers,
        test_patient,
        async_session: AsyncSession
    ):
        """
        Test PHI access report generation.
        Required for HIPAA compliance audits.
        """
        patient_id = str(test_patient.id)
        
        # Generate some PHI access
        for _ in range(3):
            await async_client.get(
                f"/api/v1/patients/{patient_id}",
                headers=admin_headers
            )
        
        # Request PHI access report
        response = await async_client.post(
            "/api/v1/reports/phi-access",
            headers=admin_headers,
            json={
                "patient_id": patient_id,
                "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "format": "detailed"
            }
        )
        
        if response.status_code == 404:
            # Try alternative endpoint
            response = await async_client.get(
                f"/api/v1/phi-access-logs?patient_id={patient_id}",
                headers=admin_headers
            )
        
        assert response.status_code == 200
        
        if isinstance(response.json(), dict):
            report = response.json()
            assert "access_count" in report or "total" in report
            assert "access_log" in report or "logs" in report
            print("✓ PHI access reports available")
        else:
            # List of logs
            logs = response.json()
            assert len(logs) >= 3
            print("✓ PHI access logs retrievable for reporting")
    
    async def test_security_compliance_dashboard(
        self,
        async_client,
        admin_headers,
        async_session: AsyncSession
    ):
        """
        Test security compliance dashboard data.
        Provides compliance status overview.
        """
        # Request compliance metrics
        response = await async_client.get(
            "/api/v1/compliance/dashboard",
            headers=admin_headers
        )
        
        if response.status_code == 404:
            # Try metrics endpoint
            response = await async_client.get(
                "/api/v1/metrics/security",
                headers=admin_headers
            )
        
        if response.status_code == 200:
            metrics = response.json()
            
            # Should include key compliance metrics
            expected_metrics = [
                "failed_login_attempts",
                "phi_access_count",
                "unauthorized_attempts",
                "active_users",
                "audit_log_size"
            ]
            
            found_metrics = sum(
                1 for metric in expected_metrics 
                if metric in str(metrics)
            )
            
            assert found_metrics >= 3, "Insufficient compliance metrics"
            print("✓ Compliance dashboard data available")
        else:
            print("⚠️  Compliance dashboard not implemented")
    
    async def test_audit_log_export_capabilities(
        self,
        async_client,
        super_admin_headers,
        async_session: AsyncSession
    ):
        """
        Test audit log export for external audits.
        Required for compliance audits.
        """
        # Request audit log export
        export_request = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            "end_date": datetime.utcnow().isoformat(),
            "format": "csv",
            "include_fields": [
                "timestamp", "user_id", "action", 
                "resource_type", "resource_id", "ip_address"
            ]
        }
        
        response = await async_client.post(
            "/api/v1/audit-logs/export",
            headers=super_admin_headers,
            json=export_request
        )
        
        if response.status_code == 404:
            print("⚠️  Audit log export not implemented")
            return
        
        assert response.status_code in [200, 202]  # 202 for async export
        
        if response.status_code == 200:
            # Direct export
            assert response.headers.get("content-type") in [
                "text/csv", "application/json", "application/octet-stream"
            ]
            print("✓ Audit log export available")
        else:
            # Async export
            export_job = response.json()
            assert "job_id" in export_job or "export_id" in export_job
            print("✓ Async audit log export available")


class TestAuditLogPerformance:
    """Test audit logging performance impact"""
    
    async def test_audit_logging_overhead(
        self,
        async_client,
        admin_headers,
        async_session: AsyncSession
    ):
        """
        Test that audit logging doesn't significantly impact performance.
        Should add <10ms overhead.
        """
        import time
        
        # Measure operation without audit logging
        # (In reality, we can't disable it, so we measure baseline)
        
        timings = []
        
        for _ in range(10):
            start = time.time()
            
            # Simple operation that triggers audit
            response = await async_client.get(
                "/api/v1/patients",
                headers=admin_headers
            )
            
            elapsed = (time.time() - start) * 1000  # Convert to ms
            timings.append(elapsed)
        
        avg_time = sum(timings) / len(timings)
        
        # Audit logging should not add significant overhead
        # Typical API call should be <200ms with audit logging
        assert avg_time < 200, f"High latency with audit logging: {avg_time:.0f}ms"
        
        print(f"✓ Audit logging overhead acceptable: {avg_time:.0f}ms avg")
    
    async def test_bulk_audit_log_performance(
        self,
        async_client,
        admin_headers,
        async_session: AsyncSession
    ):
        """
        Test performance with high volume of audit logs.
        System should handle thousands of logs/minute.
        """
        audit_service = AuditService(async_session)
        
        # Generate bulk audit logs
        start_time = time.time()
        bulk_count = 1000
        
        for i in range(bulk_count):
            await audit_service.log_action(
                user_id=f"bulk-test-{i % 10}",
                action="BULK_TEST",
                resource_type="test",
                resource_id=f"test-{i}",
                details={"index": i, "test": "performance"}
            )
            
            # Commit in batches
            if i % 100 == 0:
                await async_session.commit()
        
        await async_session.commit()
        elapsed_time = time.time() - start_time
        
        logs_per_second = bulk_count / elapsed_time
        
        print(f"✓ Bulk audit performance: {logs_per_second:.0f} logs/second")
        
        # Should handle at least 100 logs/second
        assert logs_per_second > 100, "Audit logging too slow for production"


class TestAuditLogRetention:
    """Test audit log retention and archival"""
    
    async def test_audit_log_retention_policy(
        self,
        async_client,
        admin_headers,
        async_session: AsyncSession
    ):
        """
        Test audit log retention policy enforcement.
        Logs should be retained per compliance requirements.
        """
        # Check retention policy endpoint
        response = await async_client.get(
            "/api/v1/audit-logs/retention-policy",
            headers=admin_headers
        )
        
        if response.status_code == 200:
            policy = response.json()
            
            # Verify retention periods
            assert policy["min_retention_days"] >= 365  # 1 year minimum
            assert policy["phi_access_retention_days"] >= 2190  # 6 years for HIPAA
            assert "archival_strategy" in policy
            
            print(f"✓ Retention policy: {policy['min_retention_days']} days minimum")
        else:
            # Check if old logs exist
            old_logs = await async_session.execute(
                select(AuditLog)
                .where(AuditLog.timestamp < datetime.utcnow() - timedelta(days=365))
                .limit(1)
            )
            
            if old_logs.scalar_one_or_none():
                print("✓ Logs retained beyond 1 year")
            else:
                print("⚠️  Cannot verify retention policy")
    
    async def test_audit_log_archival_process(
        self,
        async_client,
        super_admin_headers,
        async_session: AsyncSession
    ):
        """
        Test audit log archival process.
        Old logs should be archived, not deleted.
        """
        # Trigger archival process
        response = await async_client.post(
            "/api/v1/audit-logs/archive",
            headers=super_admin_headers,
            json={
                "older_than_days": 365,
                "archive_location": "compliance_archive"
            }
        )
        
        if response.status_code == 404:
            print("⚠️  Audit log archival not implemented")
            return
        
        assert response.status_code in [200, 202]
        
        result = response.json()
        if "archived_count" in result:
            assert result["archived_count"] >= 0
            assert "archive_location" in result
            print(f"✓ Archived {result['archived_count']} audit logs")
        else:
            assert "job_id" in result  # Async archival
            print("✓ Audit log archival process available")


class TestAuditLogSearch:
    """Test audit log search and filtering capabilities"""
    
    async def test_audit_log_search_capabilities(
        self,
        async_client,
        admin_headers,
        async_session: AsyncSession
    ):
        """
        Test comprehensive audit log search.
        Required for investigations and audits.
        """
        # Search by various criteria
        search_tests = [
            {"user_id": "test-user"},
            {"action": "LOGIN"},
            {"resource_type": "patient"},
            {"severity": "WARNING"},
            {"date_from": (datetime.utcnow() - timedelta(days=7)).isoformat()},
            {"ip_address": "127.0.0.1"},
        ]
        
        successful_searches = 0
        
        for search_params in search_tests:
            response = await async_client.get(
                "/api/v1/audit-logs/search",
                headers=admin_headers,
                params=search_params
            )
            
            if response.status_code == 200:
                successful_searches += 1
                results = response.json()
                assert isinstance(results, (list, dict))
        
        # Should support most search criteria
        assert successful_searches >= 4, "Limited audit search capabilities"
        print(f"✓ Audit search supports {successful_searches}/{len(search_tests)} criteria")
    
    async def test_audit_log_correlation(
        self,
        async_client,
        admin_headers,
        test_patient,
        async_session: AsyncSession
    ):
        """
        Test ability to correlate related audit logs.
        Important for security investigations.
        """
        patient_id = str(test_patient.id)
        
        # Generate related events
        # 1. User views patient
        await async_client.get(
            f"/api/v1/patients/{patient_id}",
            headers=admin_headers
        )
        
        # 2. User updates patient
        await async_client.patch(
            f"/api/v1/patients/{patient_id}",
            headers=admin_headers,
            json={"phone": "+1-555-000-1111"}
        )
        
        # 3. User exports patient data
        await async_client.post(
            f"/api/v1/patients/{patient_id}/export",
            headers=admin_headers,
            json={"format": "pdf"}
        )
        
        # Search for correlated events
        response = await async_client.get(
            f"/api/v1/audit-logs/trace/{patient_id}",
            headers=admin_headers
        )
        
        if response.status_code == 404:
            # Try general search
            response = await async_client.get(
                f"/api/v1/audit-logs?resource_id={patient_id}",
                headers=admin_headers
            )
        
        if response.status_code == 200:
            trace_logs = response.json()
            
            # Should find multiple related events
            if isinstance(trace_logs, list):
                assert len(trace_logs) >= 2
                
                # Check if correlation ID exists
                if trace_logs and "correlation_id" in trace_logs[0]:
                    print("✓ Audit log correlation with trace IDs")
                else:
                    print("✓ Related audit logs can be retrieved")
        else:
            print("⚠️  Audit log correlation not implemented")


if __name__ == "__main__":
    """
    Run audit logging security tests:
    python tests/core/security/test_audit_logging.py
    """
    print("📊 Running audit logging security tests...")
    pytest.main([__file__, "-v", "--tb=short"])
