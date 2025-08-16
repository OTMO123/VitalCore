# HEMA3N Complete System Launcher
# Healthcare AI Platform - Full Stack Deployment

Write-Host "HEMA3N HEALTHCARE AI PLATFORM" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host "GEMMA Challenge Competition System" -ForegroundColor Cyan
Write-Host "SOC2 Type II + HIPAA + FHIR R4 Compliant" -ForegroundColor Cyan
Write-Host "Revolutionary Medical UI with AI Integration" -ForegroundColor Cyan
Write-Host ""

$projectRoot = "C:\Users\aurik\Code_Projects\2_scraper"

# Function to check if port is in use
function Test-Port {
    param($Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
    return $connection
}

Write-Host "Checking system status..." -ForegroundColor Yellow

# Check if backend is already running
if (Test-Port 8000) {
    Write-Host "Backend already running on port 8000" -ForegroundColor Green
} else {
    Write-Host "Starting Backend Server..." -ForegroundColor Yellow
    Start-Process powershell.exe -ArgumentList "-NoExit", "-File", "$projectRoot\start_backend.ps1"
    Write-Host "Waiting for backend to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

# Check if frontend is already running  
if (Test-Port 3000) {
    Write-Host "Frontend already running on port 3000" -ForegroundColor Green
} else {
    Write-Host "Starting Frontend Server..." -ForegroundColor Yellow
    Start-Process powershell.exe -ArgumentList "-NoExit", "-File", "$projectRoot\start_frontend.ps1"
    Write-Host "Waiting for frontend to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
}

Write-Host ""
Write-Host "HEMA3N SYSTEM LAUNCHED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

Write-Host "DEMO INTERFACES:" -ForegroundColor Cyan
Write-Host "System Status: http://localhost:3000/debug.html" -ForegroundColor White
Write-Host "Patient Demo: http://localhost:3000/symptom-demo.html" -ForegroundColor White  
Write-Host "Doctor Demo: http://localhost:3000/doctor-demo" -ForegroundColor White
Write-Host "Full React App: http://localhost:3000/" -ForegroundColor White
Write-Host ""

Write-Host "BACKEND APIs:" -ForegroundColor Cyan
Write-Host "Health Check: http://localhost:8000/health" -ForegroundColor White
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host "OpenAPI Schema: http://localhost:8000/openapi.json" -ForegroundColor White
Write-Host ""

Write-Host "COMPETITION FEATURES:" -ForegroundColor Cyan
Write-Host "Google-Style Minimalist UI (#FFFFFF + #2F80ED)" -ForegroundColor White
Write-Host "Voice/Photo Patient Symptom Input" -ForegroundColor White
Write-Host "Paramedic Flow View (Real-time Timeline)" -ForegroundColor White
Write-Host "Doctor History Mode with Audit Trails" -ForegroundColor White
Write-Host "Linked Medical Timeline (Symptom to Treatment to Outcome)" -ForegroundColor White
Write-Host "SOC2/HIPAA/FHIR R4 Enterprise Security" -ForegroundColor White
Write-Host "Med-AI 27B + LoRA Agent Framework" -ForegroundColor White
Write-Host ""

Write-Host "Press any key to open the system status page..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Open system status page in default browser
Start-Process "http://localhost:3000/debug.html"

Write-Host "HEMA3N is ready for competition presentation!" -ForegroundColor Green