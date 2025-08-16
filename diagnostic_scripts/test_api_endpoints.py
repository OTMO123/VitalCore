#!/usr/bin/env python3
"""
API Endpoints Diagnostic Script
Tests specific endpoints that are failing and captures detailed error logs
"""

import requests
import json
import sys
import time
import uuid
from datetime import datetime
import traceback

class APITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.token = None
        self.test_patient_id = None
        self.session = requests.Session()
        self.session.timeout = 30
        
    def log(self, message, level="INFO"):
        """Enhanced logging with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        icons = {"INFO": "ℹ️", "PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "DEBUG": "🔍"}
        print(f"[{timestamp}] {icons.get(level, 'ℹ️')} {message}")
    
    def make_request(self, method, endpoint, data=None, headers=None, expected_status=None):
        """Make HTTP request with detailed error logging"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            self.log(f"{method} {endpoint}", "DEBUG")
            
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers)
            elif method.upper() == "POST":
                if endpoint == "/api/v1/auth/login":
                    response = self.session.post(url, data=data, headers=headers)
                else:
                    response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Log response details
            self.log(f"Response: {response.status_code}", "DEBUG")
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text[:500]}
            
            # Detailed logging for errors
            if response.status_code >= 400:
                self.log(f"ERROR DETAILS for {method} {endpoint}:", "FAIL")
                self.log(f"  Status: {response.status_code}", "FAIL")
                self.log(f"  Response: {json.dumps(response_data, indent=2)}", "FAIL")
                self.log(f"  Headers: {dict(response.headers)}", "DEBUG")
                
                if hasattr(response, 'request'):
                    self.log(f"  Request Headers: {dict(response.request.headers)}", "DEBUG")
                    if response.request.body:
                        body_str = response.request.body
                        if isinstance(body_str, bytes):
                            body_str = body_str.decode('utf-8')
                        self.log(f"  Request Body: {body_str[:500]}", "DEBUG")
            
            return response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            self.log(f"REQUEST EXCEPTION for {method} {endpoint}: {str(e)}", "FAIL")
            return 0, {"error": str(e)}
        except Exception as e:
            self.log(f"UNEXPECTED ERROR for {method} {endpoint}: {str(e)}", "FAIL")
            self.log(f"Traceback: {traceback.format_exc()}", "DEBUG")
            return 0, {"error": str(e)}
    
    def test_authentication(self):
        """Test authentication and get token"""
        self.log("Testing Authentication", "INFO")
        
        auth_data = "username=admin&password=admin123"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        status, response = self.make_request("POST", "/api/v1/auth/login", data=auth_data, headers=headers)
        
        if status == 200 and "access_token" in response:
            self.token = response["access_token"]
            self.log("Authentication successful", "PASS")
            return True
        else:
            self.log(f"Authentication failed: {status} - {response}", "FAIL")
            return False
    
    def get_auth_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    def test_documents_health(self):
        """Test the fixed documents health endpoint"""
        self.log("Testing Documents Health Endpoint", "INFO")
        
        headers = self.get_auth_headers()
        status, response = self.make_request("GET", "/api/v1/documents/health", headers=headers)
        
        if status == 200:
            self.log(f"Documents health OK: {response.get('status', 'healthy')}", "PASS")
            return True
        else:
            self.log(f"Documents health failed: {status} - {response}", "FAIL")
            return False
    
    def test_create_patient(self):
        """Test patient creation to get valid patient ID"""
        self.log("Testing Patient Creation", "INFO")
        
        headers = self.get_auth_headers()
        patient_data = {
            "resourceType": "Patient",
            "identifier": [{"value": f"DIAG-TEST-{int(time.time())}"}],
            "name": [{"family": "DiagnosticTest", "given": ["API"]}],
            "gender": "male",
            "birthDate": "1990-01-01",
            "active": True,
            "organization_id": "550e8400-e29b-41d4-a716-446655440000",
            "consent_status": "pending",
            "consent_types": ["treatment"]
        }
        
        status, response = self.make_request("POST", "/api/v1/healthcare/patients", data=patient_data, headers=headers)
        
        if status == 201:
            self.test_patient_id = response.get("id")
            self.log(f"Patient created successfully: {self.test_patient_id}", "PASS")
            return True
        else:
            self.log(f"Patient creation failed: {status} - {response}", "FAIL")
            return False
    
    def test_get_patient(self):
        """Test get patient by ID (the failing endpoint)"""
        if not self.test_patient_id:
            self.log("No patient ID available for get test", "WARN")
            return False
        
        self.log(f"Testing Get Patient by ID: {self.test_patient_id}", "INFO")
        
        headers = self.get_auth_headers()
        status, response = self.make_request("GET", f"/api/v1/healthcare/patients/{self.test_patient_id}", headers=headers)
        
        if status == 200:
            self.log("Get patient successful", "PASS")
            return True
        else:
            self.log(f"Get patient failed: {status} - {response}", "FAIL")
            return False
    
    def test_update_patient(self):
        """Test update patient (the failing endpoint)"""
        if not self.test_patient_id:
            self.log("No patient ID available for update test", "WARN")
            return False
        
        self.log(f"Testing Update Patient: {self.test_patient_id}", "INFO")
        
        headers = self.get_auth_headers()
        update_data = {
            "gender": "female",
            "consent_status": "active"
        }
        
        status, response = self.make_request("PUT", f"/api/v1/healthcare/patients/{self.test_patient_id}", data=update_data, headers=headers)
        
        if status == 200:
            self.log("Update patient successful", "PASS")
            return True
        else:
            self.log(f"Update patient failed: {status} - {response}", "FAIL")
            return False
    
    def test_audit_logs(self):
        """Test audit logs endpoint"""
        self.log("Testing Audit Logs Endpoint", "INFO")
        
        headers = self.get_auth_headers()
        status, response = self.make_request("GET", "/api/v1/audit/logs", headers=headers)
        
        if status == 200:
            self.log("Audit logs successful", "PASS")
            return True
        else:
            self.log(f"Audit logs failed: {status} - {response}", "FAIL")
            return False
    
    def test_error_handling(self):
        """Test error handling for non-existent patient"""
        self.log("Testing Error Handling (Non-existent Patient)", "INFO")
        
        headers = self.get_auth_headers()
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        status, response = self.make_request("GET", f"/api/v1/healthcare/patients/{fake_id}", headers=headers)
        
        if status == 404:
            self.log("Error handling correct: 404 for non-existent patient", "PASS")
            return True
        else:
            self.log(f"Error handling incorrect: Expected 404, got {status} - {response}", "FAIL")
            return False
    
    def run_diagnostic_tests(self):
        """Run comprehensive diagnostic tests"""
        self.log("🧪 STARTING API ENDPOINT DIAGNOSTICS", "INFO")
        self.log("=" * 80, "INFO")
        
        results = {}
        
        # Test 1: Authentication
        results["auth"] = self.test_authentication()
        if not results["auth"]:
            self.log("❌ Cannot continue without authentication", "FAIL")
            return results
        
        # Test 2: Documents Health (fixed endpoint)
        results["docs_health"] = self.test_documents_health()
        
        # Test 3: Create Patient (to get valid ID)
        results["create_patient"] = self.test_create_patient()
        
        # Test 4: Get Patient (failing endpoint)
        results["get_patient"] = self.test_get_patient()
        
        # Test 5: Update Patient (failing endpoint)
        results["update_patient"] = self.test_update_patient()
        
        # Test 6: Audit Logs (failing endpoint)
        results["audit_logs"] = self.test_audit_logs()
        
        # Test 7: Error Handling
        results["error_handling"] = self.test_error_handling()
        
        # Summary
        self.log("=" * 80, "INFO")
        self.log("📊 TEST RESULTS SUMMARY", "INFO")
        self.log("=" * 80, "INFO")
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        for test_name, result in results.items():
            status_icon = "✅" if result else "❌"
            self.log(f"{status_icon} {test_name}: {'PASS' if result else 'FAIL'}")
        
        self.log(f"📈 Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})", "INFO")
        
        if success_rate == 100:
            self.log("🎉 ALL TESTS PASSED - READY FOR DEPLOYMENT!", "PASS")
        elif success_rate >= 80:
            self.log("⚠️ MOSTLY WORKING - Minor fixes needed", "WARN")
        else:
            self.log("❌ MAJOR ISSUES - Need comprehensive fixes", "FAIL")
        
        return results

def main():
    """Main test runner"""
    try:
        tester = APITester()
        results = tester.run_diagnostic_tests()
        
        # Exit code based on results
        if all(results.values()):
            sys.exit(0)  # All tests passed
        else:
            sys.exit(1)  # Some tests failed
            
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()