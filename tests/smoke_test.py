#!/usr/bin/env python3
"""
Smoke Test Suite - Быстрая проверка критических функций (2-3 минуты)
Проверяет основной функционал перед запуском полного тестирования
"""

import asyncio
import json
import httpx
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class SmokeTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=10.0)
        self.auth_token = None
        self.test_patient_id = None
        
    async def log(self, message: str, status: str = "INFO"):
        """Log test progress"""
        icons = {"INFO": "ℹ️", "PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}
        print(f"{icons.get(status, 'ℹ️')} {message}")

    async def test_system_health(self) -> bool:
        """Test 1: Basic system health"""
        await self.log("Testing system health...")
        
        try:
            # Test root health endpoint
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code != 200:
                await self.log(f"Health endpoint failed: {response.status_code}", "FAIL")
                return False
            
            health_data = response.json()
            if health_data.get("status") != "healthy":
                await self.log(f"System not healthy: {health_data}", "FAIL")
                return False
                
            await self.log("System health OK", "PASS")
            return True
            
        except Exception as e:
            await self.log(f"Health check failed: {e}", "FAIL")
            return False

    async def test_authentication(self) -> bool:
        """Test 2: Authentication system"""
        await self.log("Testing authentication...")
        
        try:
            # Login with admin credentials
            login_data = {"username": "admin", "password": "admin123"}
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                await self.log(f"Login failed: {response.status_code}", "FAIL")
                return False
            
            auth_data = response.json()
            self.auth_token = auth_data.get("access_token")
            
            if not self.auth_token:
                await self.log("No access token received", "FAIL")
                return False
            
            # Test token validity
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            me_response = await self.client.get(f"{self.base_url}/api/v1/auth/me", headers=headers)
            
            if me_response.status_code != 200:
                await self.log(f"Token validation failed: {me_response.status_code}", "FAIL")
                return False
                
            user_data = me_response.json()
            if user_data.get("username") != "admin":
                await self.log(f"Wrong user data: {user_data}", "FAIL")
                return False
            
            await self.log("Authentication OK", "PASS")
            return True
            
        except Exception as e:
            await self.log(f"Authentication failed: {e}", "FAIL")
            return False

    async def test_database_connectivity(self) -> bool:
        """Test 3: Database connectivity through dashboard stats"""
        await self.log("Testing database connectivity...")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = await self.client.get(f"{self.base_url}/api/v1/dashboard/stats", headers=headers)
            
            if response.status_code != 200:
                await self.log(f"Dashboard stats failed: {response.status_code}", "FAIL")
                return False
            
            stats_data = response.json()
            if not isinstance(stats_data, dict):
                await self.log(f"Invalid stats format: {stats_data}", "FAIL")
                return False
            
            await self.log("Database connectivity OK", "PASS")
            return True
            
        except Exception as e:
            await self.log(f"Database test failed: {e}", "FAIL")
            return False

    async def test_patient_api_basic(self) -> bool:
        """Test 4: Basic patient API functionality"""
        await self.log("Testing patient API...")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}", "Content-Type": "application/json"}
            
            # Test list patients
            list_response = await self.client.get(f"{self.base_url}/api/v1/healthcare/patients", headers=headers)
            
            if list_response.status_code not in [200, 404]:  # 404 is OK if no patients exist
                await self.log(f"List patients failed: {list_response.status_code}", "FAIL")
                return False
            
            # Test patient creation with minimal data
            minimal_patient = {
                "resourceType": "Patient",
                "identifier": [{
                    "use": "official",
                    "value": f"SMOKE-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                }],
                "name": [{
                    "use": "official", 
                    "family": "SmokeTest",
                    "given": ["API"]
                }],
                "gender": "unknown",
                "birthDate": "1990-01-01",
                "active": True
            }
            
            create_response = await self.client.post(
                f"{self.base_url}/api/v1/healthcare/patients",
                json=minimal_patient,
                headers=headers
            )
            
            # Patient creation might fail due to schema issues, but we test the response
            if create_response.status_code == 201:
                await self.log("Patient creation OK", "PASS")
                
                # Try to get the created patient
                created_patient = create_response.json()
                patient_id = created_patient.get("id")
                if patient_id:
                    self.test_patient_id = patient_id
                    
                return True
            elif create_response.status_code == 500:
                await self.log("Patient creation has server errors (schema validation issue)", "WARN")
                return False  # This is the problem we're trying to fix
            else:
                await self.log(f"Patient creation failed: {create_response.status_code}", "WARN")
                return False
                
        except Exception as e:
            await self.log(f"Patient API test failed: {e}", "FAIL")
            return False

    async def test_critical_modules(self) -> bool:
        """Test 5: Critical module health checks"""
        await self.log("Testing critical modules...")
        
        critical_endpoints = [
            ("/api/v1/healthcare/health", "Healthcare"),
            ("/api/v1/dashboard/health", "Dashboard"),
            ("/api/v1/audit/health", "Audit"),
            ("/api/v1/documents/health", "Documents")
        ]
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        all_healthy = True
        
        for endpoint, module_name in critical_endpoints:
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}", headers=headers)
                if response.status_code == 200:
                    await self.log(f"{module_name} module OK", "PASS")
                else:
                    await self.log(f"{module_name} module issues: {response.status_code}", "WARN")
                    all_healthy = False
                    
            except Exception as e:
                await self.log(f"{module_name} module failed: {e}", "FAIL")
                all_healthy = False
        
        return all_healthy

    async def cleanup_test_data(self):
        """Clean up any test data created"""
        if self.test_patient_id and self.auth_token:
            try:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                delete_response = await self.client.delete(
                    f"{self.base_url}/api/v1/healthcare/patients/{self.test_patient_id}",
                    headers=headers
                )
                if delete_response.status_code in [200, 204, 404]:
                    await self.log("Test patient cleaned up", "INFO")
                    
            except Exception as e:
                await self.log(f"Cleanup warning: {e}", "WARN")

    async def run_smoke_tests(self) -> Dict[str, bool]:
        """Run all smoke tests"""
        await self.log("🚀 Starting Smoke Test Suite", "INFO")
        await self.log("=" * 50, "INFO")
        
        results = {}
        
        # Test 1: System Health
        results["system_health"] = await self.test_system_health()
        if not results["system_health"]:
            await self.log("❌ CRITICAL: System not responding - check if backend is running", "FAIL")
            return results
        
        # Test 2: Authentication
        results["authentication"] = await self.test_authentication()
        if not results["authentication"]:
            await self.log("❌ CRITICAL: Authentication broken - cannot proceed", "FAIL")
            return results
        
        # Test 3: Database
        results["database"] = await self.test_database_connectivity()
        
        # Test 4: Patient API (the main issue)
        results["patient_api"] = await self.test_patient_api_basic()
        
        # Test 5: Critical modules
        results["critical_modules"] = await self.test_critical_modules()
        
        # Summary
        await self.log("=" * 50, "INFO")
        await self.print_smoke_summary(results)
        
        # Cleanup
        await self.cleanup_test_data()
        
        return results

    async def print_smoke_summary(self, results: Dict[str, bool]):
        """Print smoke test summary"""
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        await self.log("📊 SMOKE TEST SUMMARY:", "INFO")
        await self.log(f"Tests: {passed_tests}/{total_tests} passed", "INFO")
        
        for test_name, passed in results.items():
            status = "PASS" if passed else "FAIL"
            await self.log(f"{test_name.replace('_', ' ').title()}: {'✅' if passed else '❌'}", status)
        
        # Overall assessment
        if passed_tests == total_tests:
            await self.log("🎯 ALL SMOKE TESTS PASSED - Backend ready for comprehensive testing", "PASS")
        elif results.get("system_health") and results.get("authentication"):
            await self.log("⚠️  CORE SYSTEMS OK - Some features need fixes before frontend integration", "WARN")
        else:
            await self.log("❌ CRITICAL SYSTEMS FAILING - Fix required before any integration", "FAIL")

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


async def main():
    """Main smoke test runner"""
    smoke_tester = SmokeTest()
    
    try:
        results = await smoke_tester.run_smoke_tests()
        
        # Return appropriate exit code
        core_systems = results.get("system_health", False) and results.get("authentication", False)
        if core_systems:
            exit_code = 0 if all(results.values()) else 1
        else:
            exit_code = 2  # Critical failure
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\n⏹️  Smoke test interrupted")
        return 130
    except Exception as e:
        print(f"\n❌ Smoke test failed: {e}")
        return 1
    finally:
        await smoke_tester.close()


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)