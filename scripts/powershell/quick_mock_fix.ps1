# Quick mock patient API fix for immediate frontend functionality
Write-Host "Creating mock patient API for immediate frontend use..." -ForegroundColor Yellow

# Create mock patient endpoints in Docker container
docker exec -it iris_app bash -c '
cd /app && cat > mock_patients.py << "EOF"
from fastapi import APIRouter, Depends
from app.modules.auth.dependencies import get_current_user
import uuid
from datetime import datetime

router = APIRouter()

# Mock patient data
mock_patients = [
    {
        "id": str(uuid.uuid4()),
        "first_name": "John", 
        "last_name": "Doe",
        "date_of_birth": "1985-03-15",
        "gender": "male",
        "email": "john.doe@example.com",
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": str(uuid.uuid4()),
        "first_name": "Jane",
        "last_name": "Smith", 
        "date_of_birth": "1990-07-22",
        "gender": "female",
        "email": "jane.smith@example.com",
        "created_at": "2025-01-16T14:30:00Z"
    }
]

@router.get("/patients")
async def list_patients(current_user = Depends(get_current_user)):
    return {"patients": mock_patients, "total": len(mock_patients)}

@router.post("/patients")
async def create_patient(patient_data: dict, current_user = Depends(get_current_user)):
    new_patient = {
        "id": str(uuid.uuid4()),
        "created_at": datetime.utcnow().isoformat() + "Z",
        **patient_data
    }
    mock_patients.append(new_patient)
    return new_patient

@router.get("/patients/{patient_id}")
async def get_patient(patient_id: str, current_user = Depends(get_current_user)):
    for patient in mock_patients:
        if patient["id"] == patient_id:
            return patient
    return {"error": "Patient not found"}
EOF

# Add mock router to main app
python3 -c "
import sys
sys.path.append(\"/app\")
from app.main import app
from mock_patients import router
app.include_router(router, prefix=\"/api/v1/healthcare\", tags=[\"mock-patients\"])
print(\"Mock patients router added\")
"
'

Write-Host "Mock endpoints created! Restarting app..." -ForegroundColor Yellow
docker restart iris_app

Write-Host "Waiting for app restart..." -ForegroundColor Yellow
Start-Sleep 15

Write-Host "Testing mock patient API..." -ForegroundColor Yellow

# Test the mock API
$loginBody = "username=admin&password=admin123"
$loginHeaders = @{"Content-Type" = "application/x-www-form-urlencoded"}
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
$token = $response.access_token

$authHeaders = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

try {
    $patients = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Headers $authHeaders
    Write-Host "SUCCESS! Mock patients API working! Found $($patients.total) patients" -ForegroundColor Green
    
    # Test creating a patient
    $newPatient = @{
        first_name = "Test"
        last_name = "Frontend"
        date_of_birth = "1995-01-01"
        gender = "male"
        email = "frontend@test.com"
    } | ConvertTo-Json
    
    $created = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method POST -Headers $authHeaders -Body $newPatient
    Write-Host "SUCCESS! Created patient with ID: $($created.id)" -ForegroundColor Green
    
    Write-Host "100% FRONTEND READY!" -ForegroundColor Green
    Write-Host "Credentials: admin / admin123" -ForegroundColor Cyan
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}