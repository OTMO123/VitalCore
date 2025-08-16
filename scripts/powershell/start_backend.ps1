# HEMA3N Backend Server Startup Script
# Healthcare AI Platform - SOC2/HIPAA Compliant API

Write-Host "Starting HEMA3N Healthcare Backend..." -ForegroundColor Green
Write-Host "Security: SOC2 Type II + HIPAA + FHIR R4 Compliant" -ForegroundColor Cyan
Write-Host "Features: AES-256-GCM encryption, JWT auth, audit logging" -ForegroundColor Cyan

# Set working directory
Set-Location -Path "C:\Users\aurik\Code_Projects\2_scraper"

# Start the backend server using uvicorn directly
Write-Host "Starting FastAPI server on http://localhost:8000..." -ForegroundColor Yellow
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "Health Check: http://localhost:8000/health" -ForegroundColor Yellow
Write-Host ""

try {
    # Method 1: Use uvicorn module directly
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}
catch {
    Write-Host "Method 1 failed, trying alternative..." -ForegroundColor Red
    
    # Method 2: Use Python inline command (single line)
    python -c "import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=8000, reload=True)"
}

Write-Host "Backend server stopped." -ForegroundColor Red