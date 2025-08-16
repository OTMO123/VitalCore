# Working Enterprise Healthcare Platform Deployment
# Deploys core services with verified Docker images

param(
    [switch]$SkipBuild,
    [switch]$StopOnly
)

Write-Host "Working Enterprise Healthcare Platform Deployment" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

if ($StopOnly) {
    Write-Host "`nStopping all services..." -ForegroundColor Yellow
    docker-compose -f docker-compose.working.yml down --remove-orphans
    Write-Host "All services stopped." -ForegroundColor Green
    exit 0
}

# Verify required environment variables
Write-Host "`nVerifying environment variables..." -ForegroundColor Cyan
$requiredVars = @('SECRET_KEY', 'JWT_SECRET_KEY', 'PHI_ENCRYPTION_KEY', 'AUDIT_SIGNING_KEY')
$missingVars = @()

foreach ($var in $requiredVars) {
    if ([string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($var))) {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "   Missing required environment variables:" -ForegroundColor Red
    foreach ($var in $missingVars) {
        Write-Host "      - $var" -ForegroundColor Red
    }
    Write-Host "`n   Please set environment variables first." -ForegroundColor Yellow
    Write-Host "   Run: .\deploy-complete-stack.ps1 -GenerateSecrets" -ForegroundColor Cyan
    exit 1
} else {
    Write-Host "   All required environment variables are set" -ForegroundColor Green
}

# Create necessary directories
Write-Host "`nCreating directories..." -ForegroundColor Cyan
$directories = @("logs", "monitoring")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "   Created: $dir" -ForegroundColor Green
    }
}

# Stop existing services
Write-Host "`nStopping existing services..." -ForegroundColor Cyan
docker-compose -f docker-compose.working.yml down --remove-orphans 2>$null

# Build if not skipping
if (!$SkipBuild) {
    Write-Host "`nBuilding application..." -ForegroundColor Cyan
    docker-compose -f docker-compose.working.yml build --no-cache
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   Build failed!" -ForegroundColor Red
        exit 1
    }
}

# Deploy core services
Write-Host "`nDeploying core enterprise services..." -ForegroundColor Cyan
Write-Host "   Core Services:" -ForegroundColor Gray
Write-Host "   • PostgreSQL Database" -ForegroundColor Gray
Write-Host "   • Redis Cache" -ForegroundColor Gray
Write-Host "   • MinIO Object Storage" -ForegroundColor Gray
Write-Host "   • Milvus Vector Database" -ForegroundColor Gray
Write-Host "   • Orthanc DICOM Server" -ForegroundColor Gray
Write-Host "   • Prometheus Monitoring" -ForegroundColor Gray
Write-Host "   • FastAPI Application" -ForegroundColor Gray
Write-Host "   • Celery Worker" -ForegroundColor Gray

docker-compose -f docker-compose.working.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "   Deployment failed!" -ForegroundColor Red
    Write-Host "`nTrying to get more details..." -ForegroundColor Yellow
    docker-compose -f docker-compose.working.yml logs
    exit 1
}

Write-Host "   Core services deployed!" -ForegroundColor Green

# Wait for services
Write-Host "`nWaiting for services to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 45

# Show status
Write-Host "`nService Status:" -ForegroundColor Cyan
docker-compose -f docker-compose.working.yml ps

# Show URLs
Write-Host "`nService URLs:" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host "Main Application:    http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs:           http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Vector Database:    http://localhost:9091" -ForegroundColor Cyan
Write-Host "DICOM Server:       http://localhost:8042" -ForegroundColor Cyan
Write-Host "MinIO Console:      http://localhost:9001" -ForegroundColor Cyan
Write-Host "Prometheus:         http://localhost:9090" -ForegroundColor Cyan

# Health checks
Write-Host "`nRunning health checks..." -ForegroundColor Cyan
Start-Sleep -Seconds 15

$services = @(
    @{Name="Main Application"; URL="http://localhost:8000/health"},
    @{Name="Vector Database"; URL="http://localhost:9091/health"},
    @{Name="DICOM Server"; URL="http://localhost:8042/system"},
    @{Name="MinIO Storage"; URL="http://localhost:9001/minio/health/live"}
)

foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri $service.URL -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "   $($service.Name): Healthy" -ForegroundColor Green
        }
    } catch {
        Write-Host "   $($service.Name): Not ready yet" -ForegroundColor Yellow
    }
}

Write-Host "`nCore Enterprise Platform Ready!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host "`nTo stop: .\deploy-working-stack.ps1 -StopOnly" -ForegroundColor Cyan
Write-Host "To rebuild: .\deploy-working-stack.ps1" -ForegroundColor Cyan