#!/usr/bin/env python3
"""
🏥 Simple Orthanc Mock Server (No External Dependencies)
Phase 1: Foundation Infrastructure - Basic HTTP Server
Security: CVE-2025-0896 mitigation applied
"""

import http.server
import socketserver
import json
import base64
import urllib.parse
from datetime import datetime

class OrthancMockHandler(http.server.BaseHTTPRequestHandler):
    # Mock credentials (CVE-2025-0896 fix)
    VALID_USERS = {
        "admin": "admin123",
        "iris_api": "secure_iris_key_2024"
    }
    
    def do_GET(self):
        """Handle GET requests"""
        # Check authentication first
        if not self.authenticate():
            return
        
        if self.path == '/system':
            self.send_system_info()
        elif self.path == '/':
            self.send_root_response()
        elif self.path == '/patients':
            self.send_patients_list()
        elif self.path == '/statistics':
            self.send_statistics()
        elif self.path == '/health':
            self.send_health_check()
        else:
            self.send_404()
    
    def do_POST(self):
        """Handle POST requests"""
        if not self.authenticate():
            return
            
        if self.path == '/tools/execute-script':
            self.send_script_execution_disabled()
        else:
            self.send_404()
    
    def authenticate(self):
        """Check HTTP Basic Authentication (CVE-2025-0896 fix)"""
        auth_header = self.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Basic '):
            self.send_unauthorized()
            return False
        
        try:
            # Decode base64 credentials
            encoded_credentials = auth_header[6:]  # Remove 'Basic '
            decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
            username, password = decoded_credentials.split(':', 1)
            
            # Validate credentials
            if username in self.VALID_USERS and self.VALID_USERS[username] == password:
                return True
            else:
                self.send_unauthorized()
                return False
                
        except Exception:
            self.send_unauthorized()
            return False
    
    def send_unauthorized(self):
        """Send 401 Unauthorized response"""
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Orthanc DICOM Server"')
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "error": "Authentication required",
            "message": "CVE-2025-0896 mitigation: Authentication enabled"
        }
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def send_system_info(self):
        """Send system information"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        system_info = {
            "Name": "IRIS_ORTHANC",
            "Version": "1.5.8",
            "ApiVersion": 18,
            "DicomAet": "IRIS_ORTHANC",
            "DicomPort": 4242,
            "HttpPort": 8042,
            "PluginsEnabled": True,
            "DatabaseVersion": 6,
            "StorageAreaPlugin": None,
            "DatabaseBackendPlugin": None,
            "UserMetadata": {},
            "PatientsCount": 0,
            "StudiesCount": 0,
            "SeriesCount": 0,
            "InstancesCount": 0,
            "CheckRevisions": True,
            "Security": {
                "AuthenticationEnabled": True,
                "CVE-2025-0896": "Mitigated",
                "RemoteAccessAllowed": False
            }
        }
        
        self.wfile.write(json.dumps(system_info, indent=2).encode())
    
    def send_root_response(self):
        """Send root response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "message": "🏥 Mock Orthanc DICOM Server - IRIS Healthcare Integration",
            "status": "operational",
            "security": "CVE-2025-0896 mitigation applied",
            "authentication": "enabled",
            "phase": "1_foundation_infrastructure",
            "timestamp": datetime.now().isoformat()
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def send_patients_list(self):
        """Send empty patients list"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Empty list for now - will be populated in Phase 2
        self.wfile.write(json.dumps([], indent=2).encode())
    
    def send_statistics(self):
        """Send statistics"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        stats = {
            "CountPatients": 0,
            "CountStudies": 0,
            "CountSeries": 0,
            "CountInstances": 0,
            "TotalDiskSize": "0 MB",
            "TotalUncompressedSize": "0 MB",
            "TotalDiskSizeMB": 0,
            "TotalUncompressedSizeMB": 0
        }
        
        self.wfile.write(json.dumps(stats, indent=2).encode())
    
    def send_health_check(self):
        """Send health check response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        health = {
            "status": "healthy",
            "service": "orthanc_dicom",
            "version": "1.5.8",
            "timestamp": datetime.now().isoformat(),
            "security_status": "CVE-2025-0896_mitigated"
        }
        
        self.wfile.write(json.dumps(health, indent=2).encode())
    
    def send_script_execution_disabled(self):
        """Disable script execution for security"""
        self.send_response(403)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "error": "Script execution disabled",
            "message": "Security policy: /tools/execute-script disabled",
            "security": "CVE-2025-0896 mitigation"
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def send_404(self):
        """Send 404 response"""
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "error": "Not Found",
            "path": self.path,
            "message": "Endpoint not available in mock server"
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def log_message(self, format, *args):
        """Custom log message format"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {format % args}")

def main():
    """Start the mock Orthanc server"""
    PORT = 8042
    
    print("🏥 IRIS Healthcare - Mock Orthanc DICOM Server")
    print("=" * 60)
    print("🔒 Security: CVE-2025-0896 mitigation applied")
    print("🔐 Authentication: ENABLED (Basic Auth required)")
    print("🌐 Server: http://localhost:8042")
    print("=" * 60)
    print()
    print("🔑 Valid Credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print("   -or-")
    print("   Username: iris_api") 
    print("   Password: secure_iris_key_2024")
    print()
    print("🎯 Available Endpoints:")
    print("   GET  /           - Root information")
    print("   GET  /system     - System information")
    print("   GET  /patients   - List patients")
    print("   GET  /statistics - DICOM statistics")
    print("   GET  /health     - Health check")
    print("   POST /tools/*    - Disabled for security")
    print()
    print("🚀 Starting server...")
    
    try:
        with socketserver.TCPServer(("", PORT), OrthancMockHandler) as httpd:
            print(f"✅ Mock Orthanc server running on port {PORT}")
            print("📊 Ready for Phase 2: API Integration")
            print("🛑 Press Ctrl+C to stop")
            print()
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {str(e)}")

if __name__ == "__main__":
    main()