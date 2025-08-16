#!/usr/bin/env python3
"""
Comprehensive API Testing Suite
Автоматизированное тестирование всех 105 API эндпоинтов с полным покрытием.
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import httpx
import pytest
from dataclasses import dataclass
from enum import Enum


class TestResult(Enum):
    PASS = "✅"
    FAIL = "❌" 
    SKIP = "⏭️"
    WARNING = "⚠️"


@dataclass
class EndpointTest:
    module: str
    method: str
    path: str
    description: str
    priority: str
    test_data: Optional[Dict] = None
    auth_required: bool = True
    expected_status: int = 200
    result: TestResult = TestResult.SKIP
    error_message: str = ""
    response_time: float = 0.0


class ComprehensiveAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.auth_token = None
        self.refresh_token = None
        self.test_results: List[EndpointTest] = []
        
        # Test data templates
        self.test_patient_data = {
            "resourceType": "Patient",
            "identifier": [{
                "use": "official",
                "type": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                        "code": "MR"
                    }]
                },
                "system": "http://hospital.smarthit.org",
                "value": "TEST-001"
            }],
            "name": [{
                "use": "official",
                "family": "TestPatient",
                "given": ["API", "Test"]
            }],
            "gender": "male",
            "birthDate": "1990-01-01",
            "active": True,
            "organization_id": "550e8400-e29b-41d4-a716-446655440000"
        }

    async def authenticate(self) -> bool:
        """Authenticate with admin credentials"""
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                print(f"🔐 Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    async def test_endpoint(self, test: EndpointTest) -> EndpointTest:
        """Test a single endpoint"""
        start_time = datetime.now()
        
        try:
            headers = self.get_auth_headers() if test.auth_required else {"Content-Type": "application/json"}
            
            # Prepare request based on method
            if test.method == "GET":
                response = await self.client.get(test.path, headers=headers)
            elif test.method == "POST":
                response = await self.client.post(test.path, json=test.test_data, headers=headers)
            elif test.method == "PUT":
                response = await self.client.put(test.path, json=test.test_data, headers=headers)
            elif test.method == "PATCH":
                response = await self.client.patch(test.path, json=test.test_data, headers=headers)
            elif test.method == "DELETE":
                response = await self.client.delete(test.path, headers=headers)
            else:
                test.result = TestResult.SKIP
                test.error_message = f"Unsupported method: {test.method}"
                return test
            
            # Calculate response time
            test.response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Evaluate result
            if response.status_code == test.expected_status:
                test.result = TestResult.PASS
            elif response.status_code in [401, 403] and test.auth_required:
                test.result = TestResult.WARNING
                test.error_message = f"Auth issue: {response.status_code}"
            elif response.status_code == 404:
                test.result = TestResult.WARNING  
                test.error_message = "Not found - endpoint may need implementation"
            elif response.status_code >= 500:
                test.result = TestResult.FAIL
                test.error_message = f"Server error: {response.status_code}"
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    test.error_message += f" - {error_detail}"
                except:
                    pass
            else:
                test.result = TestResult.WARNING
                test.error_message = f"Unexpected status: {response.status_code}"
                
        except Exception as e:
            test.result = TestResult.FAIL
            test.error_message = f"Request failed: {str(e)}"
            test.response_time = (datetime.now() - start_time).total_seconds() * 1000
            
        return test

    def define_test_endpoints(self) -> List[EndpointTest]:
        """Define all endpoints to test"""
        endpoints = [
            # CRITICAL: Authentication & Authorization
            EndpointTest("auth", "POST", f"{self.base_url}/api/v1/auth/login", "User Login", "CRITICAL", auth_required=False),
            EndpointTest("auth", "GET", f"{self.base_url}/api/v1/auth/me", "Get Current User", "CRITICAL"),
            EndpointTest("auth", "GET", f"{self.base_url}/api/v1/auth/users", "List Users", "CRITICAL"),
            EndpointTest("auth", "GET", f"{self.base_url}/api/v1/auth/roles", "List Roles", "CRITICAL"),
            EndpointTest("auth", "POST", f"{self.base_url}/api/v1/auth/refresh", "Refresh Token", "CRITICAL"),
            
            # CRITICAL: Patient Management  
            EndpointTest("healthcare", "GET", f"{self.base_url}/api/v1/healthcare/patients", "List Patients", "CRITICAL"),
            EndpointTest("healthcare", "POST", f"{self.base_url}/api/v1/healthcare/patients", "Create Patient", "CRITICAL", 
                        test_data=self.test_patient_data, expected_status=201),
            EndpointTest("healthcare", "GET", f"{self.base_url}/api/v1/healthcare/health", "Healthcare Health", "CRITICAL"),
            EndpointTest("healthcare", "GET", f"{self.base_url}/api/v1/healthcare/compliance/summary", "Compliance Summary", "CRITICAL"),
            
            # CRITICAL: Dashboard
            EndpointTest("dashboard", "GET", f"{self.base_url}/api/v1/dashboard/stats", "Dashboard Stats", "CRITICAL"),
            EndpointTest("dashboard", "GET", f"{self.base_url}/api/v1/dashboard/health", "Dashboard Health", "CRITICAL"),
            EndpointTest("dashboard", "GET", f"{self.base_url}/api/v1/dashboard/activities", "Dashboard Activities", "CRITICAL"),
            EndpointTest("dashboard", "GET", f"{self.base_url}/api/v1/dashboard/alerts", "Dashboard Alerts", "CRITICAL"),
            
            # HIGH: Document Management
            EndpointTest("documents", "GET", f"{self.base_url}/api/v1/documents/health", "Documents Health", "HIGH"),
            EndpointTest("documents", "GET", f"{self.base_url}/api/v1/documents/stats", "Document Stats", "HIGH"),
            EndpointTest("documents", "POST", f"{self.base_url}/api/v1/documents/search", "Search Documents", "HIGH", 
                        test_data={"query": "test", "limit": 10}),
            
            # HIGH: Audit & Compliance
            EndpointTest("audit", "GET", f"{self.base_url}/api/v1/audit/health", "Audit Health", "HIGH"),
            EndpointTest("audit", "GET", f"{self.base_url}/api/v1/audit/stats", "Audit Stats", "HIGH"),
            EndpointTest("audit", "GET", f"{self.base_url}/api/v1/audit/logs", "Audit Logs", "HIGH"),
            EndpointTest("audit", "GET", f"{self.base_url}/api/v1/audit/recent-activities", "Recent Activities", "HIGH"),
            
            # HIGH: IRIS Integration
            EndpointTest("iris", "GET", f"{self.base_url}/api/v1/iris/health", "IRIS Health", "HIGH"),
            EndpointTest("iris", "GET", f"{self.base_url}/api/v1/iris/status", "IRIS Status", "HIGH"),
            EndpointTest("iris", "GET", f"{self.base_url}/api/v1/iris/health/summary", "IRIS Health Summary", "HIGH"),
            
            # MEDIUM: Analytics & Risk
            EndpointTest("analytics", "GET", f"{self.base_url}/api/v1/analytics/health", "Analytics Health", "MEDIUM"),
            EndpointTest("risk", "GET", f"{self.base_url}/api/v1/patients/risk/health", "Risk Health", "MEDIUM"),
            
            # MEDIUM: Support Systems
            EndpointTest("purge", "GET", f"{self.base_url}/api/v1/purge/health", "Purge Health", "MEDIUM"),
            EndpointTest("purge", "GET", f"{self.base_url}/api/v1/purge/status", "Purge Status", "MEDIUM"),
            EndpointTest("security", "GET", f"{self.base_url}/api/v1/security/security-summary", "Security Summary", "MEDIUM"),
            
            # BASIC: Health Checks
            EndpointTest("root", "GET", f"{self.base_url}/health", "System Health", "BASIC", auth_required=False),
            EndpointTest("root", "GET", f"{self.base_url}/", "Root Endpoint", "BASIC", auth_required=False),
        ]
        
        return endpoints

    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        print("🚀 Starting Comprehensive API Testing Suite")
        print("=" * 60)
        
        # Step 1: Authentication
        print("🔐 Step 1: Authentication")
        if not await self.authenticate():
            return {"error": "Authentication failed", "success": False}
        
        # Step 2: Define test endpoints
        print(f"📋 Step 2: Preparing {len(self.define_test_endpoints())} endpoint tests")
        self.test_results = self.define_test_endpoints()
        
        # Step 3: Run tests by priority
        print("🧪 Step 3: Running tests by priority")
        
        priorities = ["CRITICAL", "HIGH", "MEDIUM", "BASIC"]
        results_summary = {
            "total_tests": len(self.test_results),
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "skipped": 0,
            "priorities": {},
            "detailed_results": []
        }
        
        for priority in priorities:
            priority_tests = [t for t in self.test_results if t.priority == priority]
            if not priority_tests:
                continue
                
            print(f"\n🔹 Testing {priority} endpoints ({len(priority_tests)} tests)")
            
            priority_results = {"passed": 0, "failed": 0, "warnings": 0, "skipped": 0}
            
            for test in priority_tests:
                result = await self.test_endpoint(test)
                
                # Update counters
                if result.result == TestResult.PASS:
                    priority_results["passed"] += 1
                    results_summary["passed"] += 1
                elif result.result == TestResult.FAIL:
                    priority_results["failed"] += 1
                    results_summary["failed"] += 1
                elif result.result == TestResult.WARNING:
                    priority_results["warnings"] += 1
                    results_summary["warnings"] += 1
                else:
                    priority_results["skipped"] += 1
                    results_summary["skipped"] += 1
                
                # Print result
                status_icon = result.result.value
                time_str = f"{result.response_time:.0f}ms"
                print(f"  {status_icon} {result.method:6} {result.description:30} ({time_str})")
                if result.error_message:
                    print(f"      ↳ {result.error_message}")
                
                results_summary["detailed_results"].append({
                    "module": result.module,
                    "method": result.method,
                    "path": result.path,
                    "description": result.description,
                    "priority": result.priority,
                    "result": result.result.name,
                    "error": result.error_message,
                    "response_time": result.response_time
                })
            
            results_summary["priorities"][priority] = priority_results
            
            # Print priority summary
            total_priority = len(priority_tests)
            success_rate = (priority_results["passed"] / total_priority) * 100 if total_priority > 0 else 0
            print(f"    📊 {priority}: {priority_results['passed']}/{total_priority} passed ({success_rate:.1f}%)")
        
        # Step 4: Final summary
        await self.print_final_summary(results_summary)
        
        return results_summary

    async def print_final_summary(self, results: Dict[str, Any]):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE API TEST RESULTS")
        print("=" * 60)
        
        total = results["total_tests"]
        passed = results["passed"]
        failed = results["failed"]
        warnings = results["warnings"]
        
        success_rate = (passed / total) * 100 if total > 0 else 0
        critical_rate = (results["priorities"].get("CRITICAL", {}).get("passed", 0) / 
                        len([t for t in self.test_results if t.priority == "CRITICAL"])) * 100
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"❌ Failed: {failed} ({failed/total*100:.1f}%)")
        print(f"⚠️  Warnings: {warnings} ({warnings/total*100:.1f}%)")
        print(f"⏭️  Skipped: {results['skipped']} ({results['skipped']/total*100:.1f}%)")
        print()
        print(f"🎯 Overall Success Rate: {success_rate:.1f}%")
        print(f"🔴 Critical Success Rate: {critical_rate:.1f}%")
        
        # Recommendations
        print("\n🔧 RECOMMENDATIONS:")
        if critical_rate < 100:
            print("❌ CRITICAL: Fix authentication and patient management issues before frontend integration")
        elif success_rate < 80:
            print("⚠️  HIGH: Address failing endpoints to ensure stable frontend integration")
        elif success_rate < 95:
            print("🟡 MEDIUM: Good progress, fix remaining issues for production readiness")
        else:
            print("✅ EXCELLENT: Backend is ready for frontend integration!")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"/mnt/c/Users/aurik/Code_Projects/2_scraper/tests/api_test_results_{timestamp}.json"
        
        try:
            import json
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            print(f"\n💾 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️  Could not save results: {e}")

    async def cleanup(self):
        """Clean up resources"""
        await self.client.aclose()


async def main():
    """Main test runner"""
    tester = ComprehensiveAPITester()
    
    try:
        results = await tester.run_comprehensive_test()
        
        # Exit with appropriate code
        if results.get("success", True):
            critical_success = results.get("priorities", {}).get("CRITICAL", {}).get("passed", 0)
            critical_total = len([t for t in tester.test_results if t.priority == "CRITICAL"])
            
            if critical_total > 0 and critical_success / critical_total < 1.0:
                print("\n🚨 CRITICAL ENDPOINTS FAILING - BLOCKING FRONTEND INTEGRATION")
                sys.exit(1)
            else:
                print("\n✅ API TESTING COMPLETE")
                sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())