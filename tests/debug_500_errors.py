#!/usr/bin/env python3
"""
Debug 500 Error Analyzer
Analyzes and fixes specific 500 internal server errors preventing 100% reliability.
"""

import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any


class Error500Debugger:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.auth_token = None
        
    def log(self, message: str, level: str = "INFO"):
        icons = {"INFO": "ℹ️", "DEBUG": "🔍", "ERROR": "❌", "FIX": "🔧", "SUCCESS": "✅"}
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {icons.get(level, 'ℹ️')} {message}")

    def curl_with_verbose(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> Tuple[int, str, str]:
        """Make request with verbose output to capture detailed error info"""
        
        cmd = ["curl", "-v", "-s", "-w", "\\nHTTP_CODE:%{http_code}", "-X", method.upper()]
        
        if headers:
            for key, value in headers.items():
                cmd.extend(["-H", f"{key}: {value}"])
        
        if data and method.upper() in ["POST", "PUT", "PATCH"]:
            cmd.extend(["-H", "Content-Type: application/json"])
            cmd.extend(["-d", json.dumps(data)])
        
        url = f"{self.base_url}{endpoint}"
        cmd.append(url)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            stderr = result.stderr  # Verbose output
            stdout = result.stdout
            
            # Extract HTTP code
            if "HTTP_CODE:" in stdout:
                parts = stdout.split("HTTP_CODE:")
                body = parts[0]
                status_code = int(parts[1].strip())
            else:
                body = stdout
                status_code = 0
            
            return status_code, body, stderr
            
        except Exception as e:
            return 0, f"Request failed: {e}", ""

    def authenticate(self) -> bool:
        """Get auth token"""
        status_code, body, stderr = self.curl_with_verbose(
            "POST", 
            "/api/v1/auth/login",
            data={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if status_code == 200:
            try:
                data = json.loads(body)
                self.auth_token = data.get("access_token")
                return True
            except:
                pass
        return False

    def debug_patient_api_500(self):
        """Debug patient API 500 errors in detail"""
        self.log("🔍 Debugging Patient API 500 errors...", "DEBUG")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test 1: List patients - detailed analysis
        self.log("Testing List Patients with verbose output...", "DEBUG")
        status_code, body, stderr = self.curl_with_verbose("GET", "/api/v1/healthcare/patients", headers=headers)
        
        self.log(f"List Patients Response: {status_code}", "DEBUG")
        if status_code >= 500:
            self.log("Response Body:", "ERROR")
            print(body)
            self.log("Verbose Headers/Debug:", "DEBUG") 
            print(stderr)
        
        # Test 2: Create patient - detailed analysis
        self.log("Testing Create Patient with verbose output...", "DEBUG")
        
        # Try minimal patient data first
        minimal_patient = {
            "resourceType": "Patient",
            "identifier": [{"use": "official", "value": "DEBUG-001"}],
            "name": [{"use": "official", "family": "Debug", "given": ["Test"]}],
            "gender": "male",
            "birthDate": "1990-01-01",
            "active": True
        }
        
        status_code, body, stderr = self.curl_with_verbose(
            "POST", "/api/v1/healthcare/patients", 
            data=minimal_patient, headers=headers
        )
        
        self.log(f"Create Patient Response: {status_code}", "DEBUG")
        if status_code >= 400:
            self.log("Response Body:", "ERROR")
            print(body)
            self.log("Verbose Headers/Debug:", "DEBUG")
            print(stderr)
            
            # If 422, it's validation - if 500, it's server error
            if status_code == 422:
                self.log("422 = Validation error - checking required fields...", "DEBUG")
                try:
                    error_data = json.loads(body)
                    if "detail" in error_data:
                        self.log("Validation errors:", "ERROR")
                        for error in error_data["detail"]:
                            print(f"  - {error.get('loc', [])} : {error.get('msg', 'Unknown error')}")
                except:
                    pass

    def debug_documents_health_500(self):
        """Debug documents health endpoint 500 error"""
        self.log("🔍 Debugging Documents Health 500 error...", "DEBUG")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        status_code, body, stderr = self.curl_with_verbose("GET", "/api/v1/documents/health", headers=headers)
        
        self.log(f"Documents Health Response: {status_code}", "DEBUG")
        if status_code >= 500:
            self.log("Response Body:", "ERROR")
            print(body)
            self.log("Verbose Headers/Debug:", "DEBUG")
            print(stderr)

    def debug_audit_logs_500(self):
        """Debug audit logs endpoint 500 error"""
        self.log("🔍 Debugging Audit Logs 500 error...", "DEBUG")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        status_code, body, stderr = self.curl_with_verbose("GET", "/api/v1/audit/logs", headers=headers)
        
        self.log(f"Audit Logs Response: {status_code}", "DEBUG")
        if status_code >= 500:
            self.log("Response Body:", "ERROR")
            print(body)
            self.log("Verbose Headers/Debug:", "DEBUG")
            print(stderr)

    def check_database_connectivity(self):
        """Check if database connectivity is the root cause"""
        self.log("🔍 Checking database connectivity...", "DEBUG")
        
        # Try endpoints that should work if DB is connected
        working_endpoints = [
            "/api/v1/dashboard/stats",
            "/api/v1/healthcare/health", 
            "/api/v1/audit/stats"
        ]
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        for endpoint in working_endpoints:
            status_code, body, stderr = self.curl_with_verbose("GET", endpoint, headers=headers)
            self.log(f"{endpoint}: {status_code}", "DEBUG")
            
            if status_code >= 500:
                self.log(f"Database connectivity issue detected at {endpoint}", "ERROR")
                return False
        
        self.log("Basic database connectivity appears OK", "SUCCESS")
        return True

    def generate_specific_fixes(self) -> List[str]:
        """Generate specific fixes based on 500 error analysis"""
        fixes = []
        
        self.log("🔧 Generating specific fixes for 500 errors...", "FIX")
        
        # Fix 1: Patient API Schema Issue
        fixes.append("""
# Fix 1: Patient API Schema Validation
# The patient schema is still too strict. Need to make more fields optional.

# In app/modules/healthcare_records/schemas.py:
# Make birthDate optional:
birthDate: Optional[date] = Field(None, description="Date of birth (encrypted)")

# Make all name fields optional with defaults:
class PatientName(BaseModel):
    use: str = Field(default="official", description="Name use")
    family: str = Field(default="", description="Family name (encrypted)")
    given: List[str] = Field(default_factory=lambda: [""], description="Given names (encrypted)")
""")
        
        # Fix 2: Documents Health Endpoint
        fixes.append("""
# Fix 2: Documents Health Endpoint
# Check if the health endpoint is properly implemented

# In app/modules/document_management/router.py:
@router.get("/health", response_model=dict)
async def health_check():
    try:
        return {
            "status": "healthy",
            "module": "document_management",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "module": "document_management", 
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
""")
        
        # Fix 3: Database Migration Issues
        fixes.append("""
# Fix 3: Database Schema Issues
# Run database migrations to ensure all tables exist

# Commands to run:
alembic upgrade head
# OR
python tools/database/run_migration.py

# Check if patient table exists:
# Connect to PostgreSQL and verify table structure
""")
        
        return fixes

    def run_comprehensive_debug(self):
        """Run comprehensive debugging of all 500 errors"""
        self.log("🚀 Starting comprehensive 500 error debugging...", "INFO")
        self.log("=" * 60, "INFO")
        
        # Step 1: Authenticate
        if not self.authenticate():
            self.log("❌ Cannot authenticate - cannot proceed with debugging", "ERROR")
            return
        
        self.log("✅ Authentication successful", "SUCCESS")
        
        # Step 2: Check basic database connectivity
        if not self.check_database_connectivity():
            self.log("❌ Database connectivity issues detected", "ERROR")
            return
        
        # Step 3: Debug specific 500 errors
        self.log("", "INFO")
        self.debug_patient_api_500()
        
        self.log("", "INFO") 
        self.debug_documents_health_500()
        
        self.log("", "INFO")
        self.debug_audit_logs_500()
        
        # Step 4: Generate fixes
        self.log("", "INFO")
        fixes = self.generate_specific_fixes()
        
        self.log("📋 RECOMMENDED FIXES:", "INFO")
        for i, fix in enumerate(fixes, 1):
            print(f"\n{fix}")
        
        # Step 5: Create quick fix script
        self.create_quick_fix_script()

    def create_quick_fix_script(self):
        """Create a quick fix script for the most common issues"""
        script_content = '''#!/bin/bash
# Quick Fix for 500 Errors
# Auto-generated based on error analysis

echo "🔧 Applying quick fixes for 500 errors..."

# Fix 1: Check if database is running
echo "1. Checking database connectivity..."
if ! pg_isready -h localhost -p 5432 2>/dev/null; then
    echo "⚠️  PostgreSQL not accessible on default port"
    echo "   Try: docker-compose up -d postgres"
    echo "   Or check if PostgreSQL is running on different port"
fi

# Fix 2: Run database migrations
echo "2. Running database migrations..."
if [ -f "alembic.ini" ]; then
    alembic upgrade head || echo "⚠️  Migration failed"
else
    echo "⚠️  No alembic.ini found"
fi

# Fix 3: Check patient table exists
echo "3. Checking patient table..."
if command -v psql > /dev/null; then
    psql $DATABASE_URL -c "\\dt" | grep -q patient || echo "⚠️  Patient table may not exist"
else
    echo "⚠️  psql not available to check tables"
fi

# Fix 4: Restart backend with clean environment
echo "4. Restarting backend..."
./restart_backend.sh

echo "✅ Quick fixes applied. Re-run tests to check."
'''
        
        with open("quick_fix_500_errors.sh", "w") as f:
            f.write(script_content)
        
        import os
        os.chmod("quick_fix_500_errors.sh", 0o755)
        
        self.log("Created quick_fix_500_errors.sh script", "SUCCESS")


def main():
    debugger = Error500Debugger()
    debugger.run_comprehensive_debug()


if __name__ == "__main__":
    main()