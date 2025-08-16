# Phase 2: AI/ML Capabilities Deployment
Write-Host "Phase 2: AI/ML Capabilities Deployment" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

# Set environment variables
$env:SECRET_KEY = '3h5dPMCVjESdKNEJFcpgr2pkyb8hLfImMkgBLIJjX8+CBeNHbfLm5s0TZjrKPr4qwvsK3RUU2+dimXdGWSOqAg=='
$env:ENCRYPTION_KEY = 'wLS/8tedW1PE0EoZZLcuWhfIul5+xg05OJVISJHnr/E='
$env:JWT_SECRET_KEY = 'aUEoE2V9yrejA9RdlbyDylcN2NY7fNGEkvmVN7FH+hHkiRzlLIdbYBnitaSwyZiiBmagumE/wcnK6BQ52WUv2Q=='
$env:PHI_ENCRYPTION_KEY = 'xJM+yHn5/5RwwEvOHhRkP01DbbX7wxf1TWEOPOJV+sM='
$env:AUDIT_SIGNING_KEY = 'ac8b33202bb1fafe9bac30d568b51128f05d05a116651cb0b5daf8de55ecb1400261e9ab33c9f2a2de44b203e8ef368bb579e1712527c7d71188be4b7a8cd956'

Write-Host "Environment variables set" -ForegroundColor Green

# Verify Phase 1 is running
Write-Host "`nVerifying Phase 1 Foundation..." -ForegroundColor Cyan
$phase1Services = @("iris_postgres_p1", "iris_redis_p1", "iris_app_p1")
$missingServices = @()

foreach ($service in $phase1Services) {
    try {
        $status = docker inspect $service --format='{{.State.Status}}' 2>$null
        if ($status -ne "running") {
            $missingServices += $service
        }
    } catch {
        $missingServices += $service
    }
}

if ($missingServices.Count -gt 0) {
    Write-Host "   FAILED: Phase 1 services not running:" -ForegroundColor Red
    foreach ($service in $missingServices) {
        Write-Host "      - $service" -ForegroundColor Red
    }
    Write-Host "`n   Please deploy Phase 1 first: .\deploy-phase1.ps1" -ForegroundColor Yellow
    exit 1
}
Write-Host "   PASSED: Phase 1 foundation is running" -ForegroundColor Green

# Create ML models directory
if (!(Test-Path "ml_models")) {
    New-Item -ItemType Directory -Path "ml_models" -Force | Out-Null
    
    $modelConfig = 'model_config_list { config { name: "healthcare_model" base_path: "/models/healthcare_model" model_platform: "tensorflow" } }'
    $modelConfig | Set-Content -Path "ml_models/models.config" -Encoding UTF8
    Write-Host "   Created: ml_models directory" -ForegroundColor Green
}

# Ensure network exists
$networkCheck = docker network inspect iris_network 2>$null
if ($LASTEXITCODE -ne 0) {
    docker network create iris_network
    Write-Host "   Created: iris_network" -ForegroundColor Green
}

# Deploy Phase 2
Write-Host "`nDeploying Phase 2 AI/ML Services..." -ForegroundColor Cyan
Write-Host "   • Milvus Vector Database" -ForegroundColor Yellow
Write-Host "   • Orthanc DICOM Server" -ForegroundColor Yellow  
Write-Host "   • TensorFlow Serving" -ForegroundColor Yellow

docker-compose -f docker-compose.phase2.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "   FAILED: Phase 2 deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host "   PASSED: Phase 2 services started" -ForegroundColor Green

Write-Host "`nPhase 2 Service URLs:" -ForegroundColor Cyan
Write-Host "  Enhanced Application: http://localhost:8001" -ForegroundColor White
Write-Host "  Vector Database:      http://localhost:9091" -ForegroundColor White
Write-Host "  DICOM Server:         http://localhost:8042" -ForegroundColor White

Write-Host "`nPhase 2 AI/ML Platform: READY" -ForegroundColor Green