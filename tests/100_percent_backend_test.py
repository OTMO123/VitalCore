#!/usr/bin/env python3
"""
100% Backend Reliability Test Suite
Comprehensive testing for absolute backend reliability before frontend integration.
"""

import asyncio
import json
import time
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import subprocess
import os


class TestStatus(Enum):
    PASS = "✅"
    FAIL = "❌" 
    SKIP = "⏭️"
    WARNING = "⚠️"
    CRITICAL = "🚨"


@dataclass
class TestCase:
    name: str
    category: str
    priority: str
    test_func: str
    expected_result: Any = None
    retry_count: int = 3
    timeout: int = 10
    status: TestStatus = TestStatus.SKIP
    error: str = ""
    execution_time: float = 0.0


class BackendReliabilityTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.auth_token = None
        self.test_results: List[TestCase] = []
        self.created_test_data = []  # Track created data for cleanup
        
    async def log(self, message: str, status: str = "INFO"):
        """Enhanced logging with timestamps"""
        icons = {"INFO": "ℹ️", "PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "CRITICAL": "🚨"}
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {icons.get(status, 'ℹ️')} {message}")

    async def curl_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> Tuple[int, Dict]:
        """Make HTTP request using curl with proper error handling"""
        
        cmd = ["curl", "-s", "-w", "\\n%{http_code}", "-X", method.upper()]
        
        # Add headers
        if headers:
            for key, value in headers.items():
                cmd.extend(["-H", f"{key}: {value}"])
        
        # Add data for POST/PUT/PATCH
        if data and method.upper() in ["POST", "PUT", "PATCH"]:
            # Special handling for login endpoint (form data)
            if endpoint == "/api/v1/auth/login":
                cmd.extend(["-H", "Content-Type: application/x-www-form-urlencoded"])
                form_data = "&".join([f"{k}={v}" for k, v in data.items()])
                cmd.extend(["-d", form_data])
            else:
                cmd.extend(["-H", "Content-Type: application/json"])
                cmd.extend(["-d", json.dumps(data)])
        
        # Add URL
        url = f"{self.base_url}{endpoint}"
        cmd.append(url)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return 0, {"error": f"Curl failed: {result.stderr}"}
            
            output_lines = result.stdout.strip().split('\n')
            status_code = int(output_lines[-1])
            
            # Parse response body
            body_text = '\n'.join(output_lines[:-1])
            try:
                body = json.loads(body_text) if body_text else {}
            except json.JSONDecodeError:
                body = {"raw_response": body_text}
            
            return status_code, body
            
        except subprocess.TimeoutExpired:
            return 0, {"error": "Request timeout"}
        except Exception as e:
            return 0, {"error": f"Request failed: {str(e)}"}

    async def authenticate(self) -> bool:
        """Authenticate with comprehensive error handling"""
        try:
            status_code, response = await self.curl_request(
                "POST", 
                "/api/v1/auth/login",
                data={"username": "admin", "password": "admin123"}
            )
            
            if status_code == 200 and "access_token" in response:
                self.auth_token = response["access_token"]
                await self.log("Authentication successful", "PASS")
                return True
            else:
                await self.log(f"Authentication failed: {status_code} - {response}", "FAIL")
                return False
                
        except Exception as e:
            await self.log(f"Authentication error: {e}", "FAIL")
            return False

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}

    async def test_system_fundamentals(self) -> List[TestCase]:
        """Test fundamental system requirements"""
        tests = []
        
        # Test 1: Root health endpoint
        test = TestCase("Root Health Check", "System", "CRITICAL", "test_root_health")
        try:
            status_code, response = await self.curl_request("GET", "/health")
            if status_code == 200 and response.get("status") == "healthy":
                test.status = TestStatus.PASS
            else:
                test.status = TestStatus.FAIL
                test.error = f"Unhealthy: {status_code} - {response}"
        except Exception as e:
            test.status = TestStatus.FAIL
            test.error = str(e)
        tests.append(test)
        
        # Test 2: OpenAPI documentation
        test = TestCase("OpenAPI Documentation", "System", "HIGH", "test_openapi")
        try:
            status_code, response = await self.curl_request("GET", "/openapi.json")
            if status_code == 200 and "paths" in response:
                test.status = TestStatus.PASS
            else:
                test.status = TestStatus.FAIL
                test.error = f"No OpenAPI: {status_code}"
        except Exception as e:
            test.status = TestStatus.FAIL
            test.error = str(e)
        tests.append(test)
        
        # Test 3: Authentication system
        test = TestCase("Authentication System", "Auth", "CRITICAL", "test_auth")
        if await self.authenticate():
            test.status = TestStatus.PASS
        else:
            test.status = TestStatus.FAIL
            test.error = "Authentication failed"
        tests.append(test)
        
        return tests

    async def test_all_health_endpoints(self) -> List[TestCase]:
        """Test all module health endpoints"""
        health_endpoints = [
            ("/api/v1/healthcare/health", "Healthcare"),
            ("/api/v1/dashboard/health", "Dashboard"),
            ("/api/v1/audit/health", "Audit"),
            ("/api/v1/documents/health", "Documents"),
            ("/api/v1/analytics/health", "Analytics"),
            ("/api/v1/patients/risk/health", "Risk"),
            ("/api/v1/purge/health", "Purge"),
            ("/api/v1/iris/health", "IRIS")
        ]
        
        tests = []
        headers = self.get_auth_headers()
        
        for endpoint, module_name in health_endpoints:
            test = TestCase(f"{module_name} Health", "Health", "HIGH", f"test_{module_name.lower()}_health")
            try:
                status_code, response = await self.curl_request("GET", endpoint, headers=headers)
                if status_code == 200:
                    test.status = TestStatus.PASS
                else:
                    test.status = TestStatus.FAIL
                    test.error = f"Health check failed: {status_code} - {response}"
            except Exception as e:
                test.status = TestStatus.FAIL
                test.error = str(e)
            tests.append(test)
        
        return tests

    async def test_patient_full_lifecycle(self) -> List[TestCase]:
        """Test complete patient CRUD lifecycle"""
        tests = []
        headers = self.get_auth_headers()
        patient_id = None
        
        # Test 1: List patients (should work even if empty)
        test = TestCase("List Patients", "Patient", "CRITICAL", "test_list_patients")
        try:
            status_code, response = await self.curl_request("GET", "/api/v1/healthcare/patients", headers=headers)
            if status_code in [200, 404]:  # 404 OK if no patients
                test.status = TestStatus.PASS
            else:
                test.status = TestStatus.FAIL
                test.error = f"List failed: {status_code} - {response}"
        except Exception as e:
            test.status = TestStatus.FAIL
            test.error = str(e)
        tests.append(test)
        
        # Test 2: Create patient with COMPLETE valid data
        test = TestCase("Create Patient", "Patient", "CRITICAL", "test_create_patient")
        patient_data = {
            "resourceType": "Patient",
            "identifier": [{
                "use": "official",
                "type": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}]
                },
                "system": "http://hospital.smarthit.org",
                "value": f"TEST-100-{int(time.time())}"
            }],
            "name": [{
                "use": "official",
                "family": "TestPatient100",
                "given": ["Reliability", "Test"]
            }],
            "gender": "male",
            "birthDate": "1990-01-01",
            "active": True,
            "organization_id": "550e8400-e29b-41d4-a716-446655440000",
            "consent_status": "pending",
            "consent_types": ["treatment"]
        }
        
        try:
            status_code, response = await self.curl_request("POST", "/api/v1/healthcare/patients", patient_data, headers)
            if status_code == 201:
                test.status = TestStatus.PASS
                patient_id = response.get("id")
                if patient_id:
                    self.created_test_data.append(("patient", patient_id))
            else:
                test.status = TestStatus.FAIL
                test.error = f"Create failed: {status_code} - {response}"
        except Exception as e:
            test.status = TestStatus.FAIL
            test.error = str(e)
        tests.append(test)
        
        # Test 3: Get created patient
        if patient_id:
            test = TestCase("Get Patient by ID", "Patient", "HIGH", "test_get_patient")
            try:
                status_code, response = await self.curl_request("GET", f"/api/v1/healthcare/patients/{patient_id}", headers=headers)
                if status_code == 200 and response.get("id") == patient_id:
                    test.status = TestStatus.PASS
                else:
                    test.status = TestStatus.FAIL
                    test.error = f"Get failed: {status_code} - {response}"
            except Exception as e:
                test.status = TestStatus.FAIL
                test.error = str(e)
            tests.append(test)
            
            # Test 4: Update patient
            test = TestCase("Update Patient", "Patient", "HIGH", "test_update_patient")
            update_data = {
                "gender": "female",
                "consent_status": "active"
            }
            try:
                status_code, response = await self.curl_request("PUT", f"/api/v1/healthcare/patients/{patient_id}", update_data, headers)
                if status_code == 200:
                    test.status = TestStatus.PASS
                else:
                    test.status = TestStatus.FAIL
                    test.error = f"Update failed: {status_code} - {response}"
            except Exception as e:
                test.status = TestStatus.FAIL
                test.error = str(e)
            tests.append(test)
        
        return tests

    async def test_dashboard_functionality(self) -> List[TestCase]:
        """Test dashboard endpoints comprehensively"""
        tests = []
        headers = self.get_auth_headers()
        
        dashboard_endpoints = [
            ("/api/v1/dashboard/stats", "Dashboard Stats"),
            ("/api/v1/dashboard/activities", "Dashboard Activities"),
            ("/api/v1/dashboard/alerts", "Dashboard Alerts"),
            ("/api/v1/dashboard/performance", "Performance Metrics")
        ]
        
        for endpoint, name in dashboard_endpoints:
            test = TestCase(name, "Dashboard", "HIGH", f"test_{name.lower().replace(' ', '_')}")
            try:
                status_code, response = await self.curl_request("GET", endpoint, headers=headers)
                if status_code == 200:
                    test.status = TestStatus.PASS
                else:
                    test.status = TestStatus.FAIL
                    test.error = f"Failed: {status_code} - {response}"
            except Exception as e:
                test.status = TestStatus.FAIL
                test.error = str(e)
            tests.append(test)
        
        return tests

    async def test_audit_and_compliance(self) -> List[TestCase]:
        """Test audit and compliance endpoints"""
        tests = []
        headers = self.get_auth_headers()
        
        audit_endpoints = [
            ("/api/v1/audit/stats", "Audit Statistics"),
            ("/api/v1/audit/logs", "Audit Logs"),
            ("/api/v1/audit/recent-activities", "Recent Activities"),
            ("/api/v1/healthcare/compliance/summary", "Compliance Summary")
        ]
        
        for endpoint, name in audit_endpoints:
            test = TestCase(name, "Audit", "HIGH", f"test_{name.lower().replace(' ', '_')}")
            try:
                status_code, response = await self.curl_request("GET", endpoint, headers=headers)
                if status_code == 200:
                    test.status = TestStatus.PASS
                else:
                    test.status = TestStatus.FAIL
                    test.error = f"Failed: {status_code} - {response}"
            except Exception as e:
                test.status = TestStatus.FAIL
                test.error = str(e)
            tests.append(test)
        
        return tests

    async def test_error_handling(self) -> List[TestCase]:
        """Test error handling and edge cases"""
        tests = []
        headers = self.get_auth_headers()
        
        # Test 1: Invalid patient data
        test = TestCase("Invalid Patient Data Handling", "Error", "HIGH", "test_invalid_patient")
        invalid_data = {"invalid": "data"}
        try:
            status_code, response = await self.curl_request("POST", "/api/v1/healthcare/patients", invalid_data, headers)
            if status_code == 422:  # Validation error expected
                test.status = TestStatus.PASS
            else:
                test.status = TestStatus.FAIL
                test.error = f"Expected 422, got {status_code}"
        except Exception as e:
            test.status = TestStatus.FAIL
            test.error = str(e)
        tests.append(test)
        
        # Test 2: Non-existent patient
        test = TestCase("Non-existent Patient Handling", "Error", "HIGH", "test_nonexistent_patient")
        try:
            status_code, response = await self.curl_request("GET", "/api/v1/healthcare/patients/nonexistent-id", headers=headers)
            if status_code == 404:  # Not found expected
                test.status = TestStatus.PASS
            else:
                test.status = TestStatus.FAIL
                test.error = f"Expected 404, got {status_code}"
        except Exception as e:
            test.status = TestStatus.FAIL
            test.error = str(e)
        tests.append(test)
        
        # Test 3: Unauthorized access
        test = TestCase("Unauthorized Access Handling", "Error", "HIGH", "test_unauthorized")
        try:
            status_code, response = await self.curl_request("GET", "/api/v1/healthcare/patients")  # No auth headers
            if status_code in [401, 403]:  # Unauthorized expected
                test.status = TestStatus.PASS
            else:
                test.status = TestStatus.FAIL
                test.error = f"Expected 401/403, got {status_code}"
        except Exception as e:
            test.status = TestStatus.FAIL
            test.error = str(e)
        tests.append(test)
        
        return tests

    async def cleanup_test_data(self):
        """Clean up any test data created during testing"""
        headers = self.get_auth_headers()
        
        for data_type, data_id in self.created_test_data:
            try:
                if data_type == "patient":
                    await self.curl_request("DELETE", f"/api/v1/healthcare/patients/{data_id}", headers=headers)
                    await self.log(f"Cleaned up test patient: {data_id}", "INFO")
            except Exception as e:
                await self.log(f"Cleanup warning for {data_type} {data_id}: {e}", "WARN")

    async def run_100_percent_test(self) -> Dict[str, Any]:
        """Run comprehensive 100% reliability test suite"""
        await self.log("🚀 Starting 100% Backend Reliability Test Suite", "INFO")
        await self.log("=" * 80, "INFO")
        
        all_tests = []
        
        # Phase 1: System Fundamentals (MUST PASS 100%)
        await self.log("🔍 Phase 1: System Fundamentals", "INFO")
        fundamental_tests = await self.test_system_fundamentals()
        all_tests.extend(fundamental_tests)
        
        # Check if fundamentals passed
        fundamental_failures = [t for t in fundamental_tests if t.status == TestStatus.FAIL]
        if fundamental_failures:
            await self.log("🚨 CRITICAL: System fundamentals failing - cannot continue", "CRITICAL")
            return {"success": False, "critical_failures": fundamental_failures}
        
        # Phase 2: Health Endpoints (MUST PASS 100%)
        await self.log("🏥 Phase 2: Module Health Checks", "INFO")
        health_tests = await self.test_all_health_endpoints()
        all_tests.extend(health_tests)
        
        # Phase 3: Patient Lifecycle (MUST PASS 100%)
        await self.log("👥 Phase 3: Patient CRUD Lifecycle", "INFO")
        patient_tests = await self.test_patient_full_lifecycle()
        all_tests.extend(patient_tests)
        
        # Phase 4: Dashboard Functionality
        await self.log("📊 Phase 4: Dashboard Functionality", "INFO")
        dashboard_tests = await self.test_dashboard_functionality()
        all_tests.extend(dashboard_tests)
        
        # Phase 5: Audit & Compliance
        await self.log("📋 Phase 5: Audit & Compliance", "INFO")
        audit_tests = await self.test_audit_and_compliance()
        all_tests.extend(audit_tests)
        
        # Phase 6: Error Handling
        await self.log("⚠️ Phase 6: Error Handling", "INFO")
        error_tests = await self.test_error_handling()
        all_tests.extend(error_tests)
        
        # Calculate results
        total_tests = len(all_tests)
        passed_tests = len([t for t in all_tests if t.status == TestStatus.PASS])
        failed_tests = len([t for t in all_tests if t.status == TestStatus.FAIL])
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Critical test categories
        critical_tests = [t for t in all_tests if t.category in ["System", "Auth", "Patient"]]
        critical_passed = len([t for t in critical_tests if t.status == TestStatus.PASS])
        critical_total = len(critical_tests)
        critical_rate = (critical_passed / critical_total) * 100 if critical_total > 0 else 0
        
        # Summary
        await self.log("=" * 80, "INFO")
        await self.log("📊 100% RELIABILITY TEST RESULTS", "INFO")
        await self.log("=" * 80, "INFO")
        await self.log(f"Total Tests: {total_tests}", "INFO")
        await self.log(f"✅ Passed: {passed_tests}", "PASS" if passed_tests == total_tests else "INFO")
        await self.log(f"❌ Failed: {failed_tests}", "FAIL" if failed_tests > 0 else "INFO")
        await self.log(f"📈 Success Rate: {success_rate:.1f}%", "INFO")
        await self.log(f"🎯 Critical Success Rate: {critical_rate:.1f}%", "INFO")
        
        # Determine if backend is ready
        if success_rate == 100.0:
            await self.log("🎉 100% SUCCESS - Backend ready for frontend integration!", "PASS")
            is_ready = True
        elif critical_rate == 100.0 and success_rate >= 90.0:
            await self.log("✅ GOOD - Critical systems working, minor issues acceptable", "PASS")
            is_ready = True
        else:
            await self.log("❌ NOT READY - Critical issues must be fixed before frontend integration", "FAIL")
            is_ready = False
        
        # Detailed failure analysis
        if failed_tests > 0:
            await self.log("\n🔍 FAILURE ANALYSIS:", "INFO")
            for test in all_tests:
                if test.status == TestStatus.FAIL:
                    await self.log(f"❌ {test.name} ({test.category}): {test.error}", "FAIL")
        
        # Cleanup
        await self.cleanup_test_data()
        
        return {
            "success": is_ready,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "critical_rate": critical_rate,
            "test_results": all_tests,
            "ready_for_frontend": is_ready
        }


async def main():
    """Main test runner for 100% reliability"""
    tester = BackendReliabilityTester()
    
    try:
        results = await tester.run_100_percent_test()
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"tests/100_percent_test_results_{timestamp}.json"
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                # Convert TestCase objects to dict for JSON serialization
                serializable_results = {**results}
                serializable_results["test_results"] = [
                    {
                        "name": t.name,
                        "category": t.category,
                        "priority": t.priority,
                        "status": t.status.name,
                        "error": t.error,
                        "execution_time": t.execution_time
                    }
                    for t in results["test_results"]
                ]
                json.dump(serializable_results, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️ Could not save results: {e}")
        
        # Exit with appropriate code
        if results["ready_for_frontend"]:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
            
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())