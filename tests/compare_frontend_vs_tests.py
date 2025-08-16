#!/usr/bin/env python3
"""
Frontend vs Tests Comparison
Анализирует различия между запросами frontend и наших тестов
"""

import json
import subprocess
from typing import Dict, Any
from datetime import datetime


class FrontendTestComparison:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.auth_token = None
        
    def log(self, message: str, level: str = "INFO"):
        icons = {"INFO": "ℹ️", "COMPARE": "🔍", "DIFF": "⚡", "ISSUE": "❌", "SUCCESS": "✅"}
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {icons.get(level, 'ℹ️')} {message}")

    def get_auth_token(self) -> str:
        """Get fresh auth token"""
        cmd = [
            "curl", "-s", "-X", "POST",
            "-H", "Content-Type: application/x-www-form-urlencoded",
            "-d", "username=admin&password=admin123",
            f"{self.base_url}/api/v1/auth/login"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                return data.get("access_token", "")
            except:
                return ""
        return ""

    def make_request(self, method: str, endpoint: str, data: Dict = None, extra_headers: Dict = None) -> Dict[str, Any]:
        """Make HTTP request and capture detailed info"""
        
        cmd = ["curl", "-s", "-v", "-w", "\\nHTTP_STATUS:%{http_code}\\nTIME:%{time_total}", "-X", method]
        
        # Add auth header
        if self.auth_token:
            cmd.extend(["-H", f"Authorization: Bearer {self.auth_token}"])
        
        # Add content type for data requests
        if data:
            cmd.extend(["-H", "Content-Type: application/json"])
            cmd.extend(["-d", json.dumps(data)])
        
        # Add extra headers
        if extra_headers:
            for key, value in extra_headers.items():
                cmd.extend(["-H", f"{key}: {value}"])
        
        cmd.append(f"{self.base_url}{endpoint}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse response
        stdout = result.stdout
        stderr = result.stderr
        
        # Extract status and time
        status_code = 0
        time_taken = 0
        body = stdout
        
        if "HTTP_STATUS:" in stdout:
            parts = stdout.split("HTTP_STATUS:")
            body = parts[0]
            status_line = parts[1]
            if "TIME:" in status_line:
                status_part, time_part = status_line.split("TIME:")
                status_code = int(status_part.strip()) if status_part.strip().isdigit() else 0
                time_taken = float(time_part.strip()) if time_part.strip() else 0
        
        return {
            "status_code": status_code,
            "body": body,
            "time_taken": time_taken,
            "headers_sent": stderr,
            "method": method,
            "endpoint": endpoint,
            "data_sent": data
        }

    def compare_patient_creation_requests(self):
        """Compare how frontend vs tests create patients"""
        self.log("🔍 Comparing Patient Creation Requests", "COMPARE")
        
        # Test 1: Наш тест (упрощенный)
        test_patient_data = {
            "resourceType": "Patient",
            "identifier": [{"use": "official", "value": "TEST-001"}],
            "name": [{"use": "official", "family": "Test", "given": ["User"]}],
            "active": True
        }
        
        self.log("Testing our simplified patient data...", "INFO")
        test_response = self.make_request("POST", "/api/v1/healthcare/patients", test_patient_data)
        
        self.log(f"Our test result: {test_response['status_code']}", "INFO")
        if test_response['status_code'] >= 400:
            self.log(f"Our test error: {test_response['body'][:200]}", "ISSUE")
        
        # Test 2: Frontend полные данные (как в форме)
        frontend_patient_data = {
            "resourceType": "Patient",
            "identifier": [{
                "use": "official",
                "type": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}]
                },
                "system": "http://hospital.smarthit.org",
                "value": "18999"
            }],
            "name": [{
                "use": "official",
                "family": "Morkovitz",
                "given": ["Lord"]
            }],
            "gender": "male",
            "birthDate": "1992-07-10", 
            "active": True,
            "organization_id": "550e8400-e29b-41d4-a716-446655440000",
            "telecom": [
                {
                    "system": "phone",
                    "value": "0545830756",
                    "use": "mobile"
                },
                {
                    "system": "email", 
                    "value": "datmanhhh@yandex.ru",
                    "use": "home"
                }
            ],
            "address": [{
                "use": "home",
                "line": ["ruppin 4"],
                "city": "rishon le zion",
                "state": "State",
                "postalCode": "7525623",
                "country": "US"
            }]
        }
        
        self.log("Testing frontend complete patient data...", "INFO")
        frontend_response = self.make_request("POST", "/api/v1/healthcare/patients", frontend_patient_data)
        
        self.log(f"Frontend test result: {frontend_response['status_code']}", "INFO")
        if frontend_response['status_code'] >= 400:
            self.log(f"Frontend test error: {frontend_response['body'][:200]}", "ISSUE")
        
        # Compare results
        self.log("", "INFO")
        self.log("📊 COMPARISON RESULTS:", "COMPARE")
        self.log(f"Our Test Status: {test_response['status_code']}", "INFO")
        self.log(f"Frontend Status: {frontend_response['status_code']}", "INFO")
        
        if test_response['status_code'] != frontend_response['status_code']:
            self.log("⚡ DIFFERENT RESULTS DETECTED!", "DIFF")
            self.log("This explains why tests pass but frontend fails", "ISSUE")
        else:
            self.log("Same results - issue is elsewhere", "INFO")

    def check_frontend_service_expectations(self):
        """Check what frontend service expects vs what API provides"""
        self.log("", "INFO") 
        self.log("🔍 Checking Frontend Service Expectations", "COMPARE")
        
        # Check patient service expectations
        patient_service_path = "/mnt/c/Users/aurik/Code_Projects/2_scraper/frontend/src/services/patient.service.ts"
        
        try:
            with open(patient_service_path, 'r') as f:
                content = f.read()
            
            # Check for specific patterns that frontend expects
            expectations = {
                "Status 201 for create": "status_code == 201" in content or "201" in content,
                "Response data structure": "response.data" in content,
                "Error handling": "response.error" in content,
                "API base URL": "localhost:8000" in content or "baseURL" in content
            }
            
            self.log("Frontend Service Expectations:", "INFO")
            for expectation, found in expectations.items():
                status = "✅" if found else "❌"
                self.log(f"  {status} {expectation}", "INFO")
                
        except Exception as e:
            self.log(f"Could not read frontend service: {e}", "ISSUE")

    def test_exact_frontend_requests(self):
        """Test exact requests that frontend would make"""
        self.log("", "INFO")
        self.log("🔍 Testing Exact Frontend Request Patterns", "COMPARE")
        
        # 1. Test frontend API client pattern
        frontend_headers = {
            "X-Request-ID": "req_123456789_abcdef",
            "User-Agent": "Mozilla/5.0 (frontend)",
            "Accept": "application/json"
        }
        
        self.log("Testing with frontend headers...", "INFO")
        response = self.make_request("GET", "/api/v1/healthcare/patients", extra_headers=frontend_headers)
        self.log(f"With frontend headers: {response['status_code']}", "INFO")
        
        # 2. Test without any special headers (like our tests)
        self.log("Testing without special headers...", "INFO")
        response2 = self.make_request("GET", "/api/v1/healthcare/patients")
        self.log(f"Without special headers: {response2['status_code']}", "INFO")
        
        # 3. Test CORS preflight (OPTIONS request)
        self.log("Testing CORS preflight...", "INFO")
        cors_headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization"
        }
        response3 = self.make_request("OPTIONS", "/api/v1/healthcare/patients", extra_headers=cors_headers)
        self.log(f"CORS preflight: {response3['status_code']}", "INFO")

    def analyze_api_client_differences(self):
        """Analyze differences between our curl and frontend's axios/fetch"""
        self.log("", "INFO")
        self.log("🔍 Analyzing API Client Differences", "COMPARE")
        
        # Test different ways of sending the same request
        patient_data = {"resourceType": "Patient", "active": True}
        
        methods = [
            ("Standard JSON", {"Content-Type": "application/json"}),
            ("With charset", {"Content-Type": "application/json; charset=utf-8"}),
            ("With CORS headers", {
                "Content-Type": "application/json",
                "Origin": "http://localhost:3000"
            }),
            ("With frontend headers", {
                "Content-Type": "application/json", 
                "User-Agent": "axios/0.27.2",
                "Accept": "application/json, text/plain, */*"
            })
        ]
        
        results = {}
        
        for method_name, headers in methods:
            self.log(f"Testing {method_name}...", "INFO")
            response = self.make_request("POST", "/api/v1/healthcare/patients", patient_data, headers)
            results[method_name] = response['status_code']
            self.log(f"  Result: {response['status_code']}", "INFO")
        
        # Check if all results are the same
        unique_results = set(results.values())
        if len(unique_results) > 1:
            self.log("⚡ DIFFERENT RESULTS WITH DIFFERENT HEADERS!", "DIFF")
            for method, status in results.items():
                self.log(f"  {method}: {status}", "INFO")
        else:
            self.log("All header combinations give same result", "SUCCESS")

    def run_comprehensive_comparison(self):
        """Run all comparison tests"""
        self.log("🚀 Frontend vs Tests Comprehensive Comparison", "INFO")
        self.log("=" * 60, "INFO")
        
        # Get auth token
        self.auth_token = self.get_auth_token()
        if not self.auth_token:
            self.log("❌ Could not get auth token", "ISSUE")
            return
        
        self.log("✅ Got auth token", "SUCCESS")
        
        # Run all comparisons
        self.compare_patient_creation_requests()
        self.check_frontend_service_expectations() 
        self.test_exact_frontend_requests()
        self.analyze_api_client_differences()
        
        # Summary
        self.log("", "INFO")
        self.log("📋 ANALYSIS SUMMARY:", "COMPARE")
        self.log("", "INFO")
        self.log("Key findings will help identify why frontend fails while tests pass", "INFO")
        self.log("Check the output above for specific differences", "INFO")
        self.log("", "INFO")
        self.log("🔧 RECOMMENDATIONS:", "INFO")
        self.log("1. Check if frontend uses correct API base URL", "INFO")
        self.log("2. Verify CORS configuration allows frontend origin", "INFO") 
        self.log("3. Ensure frontend sends complete required data", "INFO")
        self.log("4. Check if frontend handles 500 errors properly", "INFO")


def main():
    """Main function"""
    comparator = FrontendTestComparison()
    comparator.run_comprehensive_comparison()


if __name__ == "__main__":
    main()