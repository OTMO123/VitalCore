
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
