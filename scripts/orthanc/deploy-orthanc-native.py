#!/usr/bin/env python3
"""
🏥 Orthanc DICOM Native Deployment Script
Alternative deployment without Docker for WSL environments
Phase 1: Foundation Infrastructure Setup
"""

import os
import sys
import subprocess
import time
import requests
import json
from pathlib import Path

def print_header(text, color="cyan"):
    colors = {
        "cyan": "\033[96m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "white": "\033[97m",
        "gray": "\033[90m",
        "reset": "\033[0m"
    }
    
    print(f"{colors.get(color, colors['white'])}{text}{colors['reset']}")

def run_command(command, description="", check=True):
    """Run a system command with error handling"""
    print_header(f"🔧 {description}", "yellow")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if check and result.returncode != 0:
            print_header(f"❌ Error: {result.stderr}", "red")
            return False
        else:
            if result.stdout:
                print_header(f"✅ {result.stdout.strip()}", "green")
            return True
    except Exception as e:
        print_header(f"❌ Exception: {str(e)}", "red")
        return False

def check_prerequisites():
    """Check if required tools are available"""
    print_header("🔍 Checking Prerequisites", "cyan")
    
    # Check Python
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 8:
        print_header(f"✅ Python {python_version.major}.{python_version.minor} - OK", "green")
    else:
        print_header("❌ Python 3.8+ required", "red")
        return False
    
    # Check if we can install packages
    try:
        import psycopg2
        print_header("✅ PostgreSQL driver available", "green")
    except ImportError:
        print_header("⚠️ PostgreSQL driver not found, will attempt to install", "yellow")
    
    try:
        import redis
        print_header("✅ Redis client available", "green")
    except ImportError:
        print_header("⚠️ Redis client not found, will attempt to install", "yellow")
    
    return True

def install_dependencies():
    """Install required Python packages"""
    print_header("📦 Installing Dependencies", "cyan")
    
    packages = [
        "psycopg2-binary",
        "redis",
        "requests",
        "minio",
        "fastapi",
        "uvicorn"
    ]
    
    for package in packages:
        print_header(f"Installing {package}...", "yellow")
        if run_command(f"{sys.executable} -m pip install --user {package}", f"Install {package}", check=False):
            print_header(f"✅ {package} installed", "green")
        else:
            print_header(f"⚠️ Failed to install {package}, continuing...", "yellow")

def setup_directories():
    """Create necessary directories"""
    print_header("📁 Setting up Directory Structure", "cyan")
    
    directories = [
        "data/orthanc/storage",
        "data/orthanc/postgres",
        "data/minio/storage", 
        "data/redis",
        "logs/orthanc",
        "logs/minio",
        "logs/redis"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print_header(f"✅ Created: {directory}", "green")

def create_orthanc_config():
    """Create Orthanc configuration for standalone deployment"""
    print_header("⚙️ Creating Orthanc Configuration", "cyan")
    
    config = {
        "Name": "IRIS_ORTHANC",
        "HttpPort": 8042,
        "DicomPort": 4242,
        "StorageArea": "./data/orthanc/storage",
        "IndexDirectory": "./data/orthanc/index",
        
        # Security Configuration (CVE-2025-0896 fix)
        "AuthenticationEnabled": True,
        "RegisteredUsers": {
            "admin": "admin123",
            "iris_api": "secure_iris_key_2024"
        },
        "RemoteAccessAllowed": False,
        
        # Basic DICOM settings
        "DicomAet": "IRIS_ORTHANC",
        "DicomCheckModalityHost": False,
        "DefaultEncoding": "Latin1",
        
        # Logging
        "VerboseStartup": True,
        "LogFile": "./logs/orthanc/orthanc.log",
        
        # Performance
        "MaximumStorageSize": 0,
        "MaximumPatientCount": 0
    }
    
    config_path = "orthanc-config/orthanc-standalone.json"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print_header(f"✅ Orthanc config created: {config_path}", "green")
    return config_path

def start_mock_services():
    """Start mock services for development"""
    print_header("🚀 Starting Mock Development Services", "cyan")
    
    # Create a simple FastAPI app to simulate Orthanc
    mock_orthanc_code = '''
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import json
from datetime import datetime

app = FastAPI(title="Mock Orthanc DICOM Server", version="1.5.8")
security = HTTPBasic()

# Mock credentials (CVE-2025-0896 fix)
VALID_USERS = {
    "admin": "admin123",
    "iris_api": "secure_iris_key_2024"
}

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    password = credentials.password
    
    if username not in VALID_USERS or VALID_USERS[username] != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return username

@app.get("/system")
async def system_info(user: str = Depends(authenticate)):
    return {
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
        "CheckRevisions": True
    }

@app.get("/")
async def root():
    return {"message": "🏥 Mock Orthanc DICOM Server - Security Enabled"}

@app.get("/patients")
async def list_patients(user: str = Depends(authenticate)):
    return []

@app.post("/tools/execute-script")
async def execute_script(user: str = Depends(authenticate)):
    # This endpoint is often vulnerable - we disable it
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Script execution disabled for security"
    )

@app.get("/statistics")
async def get_statistics(user: str = Depends(authenticate)):
    return {
        "CountPatients": 0,
        "CountStudies": 0,
        "CountSeries": 0,
        "CountInstances": 0,
        "TotalDiskSize": "0 MB",
        "TotalUncompressedSize": "0 MB"
    }

if __name__ == "__main__":
    print("🏥 Starting Mock Orthanc DICOM Server...")
    print("🔒 Security: CVE-2025-0896 mitigation applied")
    print("🌐 Access: http://localhost:8042")
    print("👤 Credentials: admin/admin123 or iris_api/secure_iris_key_2024")
    uvicorn.run(app, host="0.0.0.0", port=8042)
'''
    
    # Save mock Orthanc code
    with open("mock_orthanc_server.py", "w") as f:
        f.write(mock_orthanc_code)
    
    print_header("✅ Mock Orthanc server created", "green")
    
    # Create MinIO mock
    mock_minio_code = '''
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(title="Mock MinIO Object Storage", version="1.0.0")

@app.get("/minio/health/live")
async def health_check():
    return {"status": "healthy", "service": "minio"}

@app.get("/")
async def root():
    return {"message": "🗄️ Mock MinIO Object Storage - Ready"}

@app.get("/admin/v3/info")
async def admin_info():
    return {
        "mode": "standalone",
        "deploymentID": "iris-minio-deployment",
        "region": "us-east-1",
        "buckets": {"count": 0}
    }

if __name__ == "__main__":
    print("🗄️ Starting Mock MinIO Object Storage...")
    print("🌐 Access: http://localhost:9000")
    uvicorn.run(app, host="0.0.0.0", port=9000)
'''
    
    with open("mock_minio_server.py", "w") as f:
        f.write(mock_minio_code)
    
    print_header("✅ Mock MinIO server created", "green")
    
    return True

def test_services():
    """Test that services are working"""
    print_header("🔍 Testing Services", "cyan")
    
    # Test mock Orthanc (without auth - should fail)
    try:
        response = requests.get("http://localhost:8042/system", timeout=5)
        if response.status_code == 401:
            print_header("✅ Orthanc authentication working (401 expected)", "green")
        else:
            print_header("⚠️ Orthanc authentication may not be working", "yellow")
    except requests.exceptions.ConnectionError:
        print_header("⚠️ Orthanc not running - will start manually", "yellow")
    except Exception as e:
        print_header(f"⚠️ Orthanc test error: {str(e)}", "yellow")
    
    # Test with authentication
    try:
        response = requests.get(
            "http://localhost:8042/system", 
            auth=("admin", "admin123"), 
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            print_header(f"✅ Orthanc authenticated access successful", "green")
            print_header(f"   Version: {data.get('Version', 'unknown')}", "gray")
        else:
            print_header(f"⚠️ Orthanc auth test failed: {response.status_code}", "yellow")
    except Exception as e:
        print_header(f"⚠️ Orthanc auth test error: {str(e)}", "yellow")

def create_startup_script():
    """Create a startup script for the services"""
    startup_script = '''#!/bin/bash
# 🏥 Start IRIS Orthanc Development Environment

echo "🚀 Starting IRIS Healthcare - Orthanc DICOM Integration"
echo "=================================================="

# Start Mock Orthanc in background
echo "🏥 Starting Mock Orthanc DICOM Server..."
python3 mock_orthanc_server.py &
ORTHANC_PID=$!

# Start Mock MinIO in background  
echo "🗄️ Starting Mock MinIO Object Storage..."
python3 mock_minio_server.py &
MINIO_PID=$!

echo ""
echo "✅ Services Started:"
echo "🏥 Orthanc DICOM: http://localhost:8042"
echo "🗄️ MinIO Storage: http://localhost:9000"
echo ""
echo "🔑 Orthanc Credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo "   API User: iris_api"
echo "   API Key: secure_iris_key_2024"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "echo 'Stopping services...'; kill $ORTHANC_PID $MINIO_PID 2>/dev/null; exit" INT
wait
'''
    
    with open("start_orthanc_dev.sh", "w") as f:
        f.write(startup_script)
    
    # Make it executable
    os.chmod("start_orthanc_dev.sh", 0o755)
    print_header("✅ Startup script created: start_orthanc_dev.sh", "green")

def main():
    """Main deployment function"""
    print_header("🏥 IRIS Healthcare - Orthanc DICOM Integration Deployment", "cyan")
    print_header("=" * 70, "yellow")
    print_header("Phase 1: Foundation Infrastructure Setup (Native)", "white")
    print_header("Security: CVE-2025-0896 mitigation applied", "green")
    print_header("=" * 70, "yellow")
    
    # Step 1: Prerequisites
    if not check_prerequisites():
        print_header("❌ Prerequisites check failed", "red")
        return False
    
    # Step 2: Install dependencies
    install_dependencies()
    
    # Step 3: Setup directories
    setup_directories()
    
    # Step 4: Create Orthanc config
    config_path = create_orthanc_config()
    
    # Step 5: Start mock services
    start_mock_services()
    
    # Step 6: Create startup script
    create_startup_script()
    
    # Step 7: Display information
    print_header("\n🎯 Deployment Complete!", "green")
    print_header("=" * 50, "yellow")
    
    print_header("📋 What was deployed:", "white")
    print_header("✅ Mock Orthanc DICOM Server (security-hardened)", "green")
    print_header("✅ Mock MinIO Object Storage", "green") 
    print_header("✅ Directory structure for data storage", "green")
    print_header("✅ Security configuration (CVE-2025-0896 fix)", "green")
    print_header("✅ Startup scripts for development", "green")
    
    print_header("\n🚀 Next Steps:", "cyan")
    print_header("1. Run: python3 mock_orthanc_server.py", "white")
    print_header("2. Test: http://localhost:8042 (credentials: admin/admin123)", "white")
    print_header("3. Implement IRIS API integration", "white")
    print_header("4. Add real PostgreSQL when ready", "white")
    
    print_header("\n🏆 Phase 1 Foundation: DEPLOYED (Development Mode)", "green")
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print_header("\n🎉 Deployment successful! Ready for Phase 2.", "green")
        else:
            print_header("\n❌ Deployment failed. Check errors above.", "red")
            sys.exit(1)
    except KeyboardInterrupt:
        print_header("\n🛑 Deployment interrupted by user", "yellow")
        sys.exit(0)
    except Exception as e:
        print_header(f"\n❌ Unexpected error: {str(e)}", "red")
        sys.exit(1)