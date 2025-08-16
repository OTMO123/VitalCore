# Complete Enterprise ML/AI Healthcare Platform Deployment
# Deploys the full stack including Vector Database, Orthanc, ML Services, and Monitoring

param(
    [switch]$Production,
    [switch]$GenerateSecrets,
    [switch]$SkipBuild,
    [string]$Profile = "complete"
)

Write-Host "Complete Enterprise ML/AI Healthcare Platform Deployment" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green

# Check Docker availability
Write-Host "`nChecking Docker availability..." -ForegroundColor Cyan
try {
    $dockerVersion = docker --version
    Write-Host "   Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "   Docker not found or not running!" -ForegroundColor Red
    Write-Host "   Please install Docker and ensure it's running." -ForegroundColor Yellow
    exit 1
}

# Check Docker Compose availability
try {
    $composeVersion = docker-compose --version
    Write-Host "   Docker Compose found: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "   Docker Compose not found!" -ForegroundColor Red
    Write-Host "   Please install Docker Compose." -ForegroundColor Yellow
    exit 1
}

# Generate secure environment variables if requested
if ($GenerateSecrets) {
    Write-Host "`nGenerating secure environment variables..." -ForegroundColor Cyan
    
    if (Test-Path "scripts/deployment_tests/generate_secure_env_fixed.ps1") {
        & "scripts/deployment_tests/generate_secure_env_fixed.ps1"
        Write-Host "   Secure environment variables generated" -ForegroundColor Green
        Write-Host "   Please copy the QUICK SETUP COMMAND and run it to set variables" -ForegroundColor Yellow
        
        # Wait for user to set environment variables
        Read-Host "`nPress Enter after you've set the environment variables..."
    } else {
        Write-Host "   Environment generator script not found!" -ForegroundColor Red
        exit 1
    }
}

# Verify environment variables are set
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
    Write-Host "`n   Please run with -GenerateSecrets or set variables manually." -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "   All required environment variables are set" -ForegroundColor Green
}

# Create necessary directories
Write-Host "`nCreating necessary directories..." -ForegroundColor Cyan
$directories = @(
    "data/orthanc/storage",
    "data/orthanc/postgres", 
    "data/minio/storage",
    "data/redis",
    "ml_models",
    "logs",
    "monitoring/prometheus",
    "monitoring/grafana"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "   Created: $dir" -ForegroundColor Green
    }
}

# Stop any existing services
Write-Host "`nStopping existing services..." -ForegroundColor Cyan
docker-compose -f docker-compose.complete.yml down --remove-orphans 2>$null
Write-Host "   Existing services stopped" -ForegroundColor Green

# Build application if not skipping
if (!$SkipBuild) {
    Write-Host "`nBuilding application images..." -ForegroundColor Cyan
    docker-compose -f docker-compose.complete.yml build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   Build failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host "   Application images built successfully" -ForegroundColor Green
}

# Deploy the complete stack
Write-Host "`nDeploying complete enterprise stack..." -ForegroundColor Cyan
Write-Host "   This includes:" -ForegroundColor Gray
Write-Host "   • PostgreSQL (Main + Orthanc)" -ForegroundColor Gray
Write-Host "   • Redis Cache" -ForegroundColor Gray
Write-Host "   • Milvus Vector Database" -ForegroundColor Gray
Write-Host "   • Orthanc DICOM Server" -ForegroundColor Gray
Write-Host "   • MinIO Object Storage" -ForegroundColor Gray
Write-Host "   • TensorFlow Serving" -ForegroundColor Gray
Write-Host "   • Jupyter Notebooks" -ForegroundColor Gray
Write-Host "   • Prometheus + Grafana" -ForegroundColor Gray
Write-Host "   • Jaeger Tracing" -ForegroundColor Gray
Write-Host "   • FastAPI Application" -ForegroundColor Gray
Write-Host "   • Celery Workers" -ForegroundColor Gray

docker-compose -f docker-compose.complete.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "   Deployment failed!" -ForegroundColor Red
    exit 1
}

Write-Host "   Complete enterprise stack deployed successfully!" -ForegroundColor Green

# Wait for services to be healthy
Write-Host "`nWaiting for services to become healthy..." -ForegroundColor Cyan
Start-Sleep -Seconds 30

# Show service status
Write-Host "`nService Status:" -ForegroundColor Cyan
docker-compose -f docker-compose.complete.yml ps

# Show access URLs
Write-Host "`nService Access URLs:" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "Main Application:      http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Documentation:     http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Vector Database:       http://localhost:9091" -ForegroundColor Cyan
Write-Host "Orthanc DICOM:         http://localhost:8042" -ForegroundColor Cyan
Write-Host "MinIO Console:         http://localhost:9001" -ForegroundColor Cyan
Write-Host "TensorFlow Serving:    http://localhost:8501" -ForegroundColor Cyan
Write-Host "Jupyter Notebooks:     http://localhost:8888" -ForegroundColor Cyan
Write-Host "Prometheus:            http://localhost:9090" -ForegroundColor Cyan
Write-Host "Grafana:               http://localhost:3001" -ForegroundColor Cyan
Write-Host "Jaeger Tracing:        http://localhost:16686" -ForegroundColor Cyan

# Run health checks
Write-Host "`nRunning health checks..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# Test main application
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "   Main Application: Healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "   Main Application: Not responding" -ForegroundColor Red
}

# Test vector database
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9091/health" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "   Milvus Vector Database: Healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "   Milvus Vector Database: Not responding" -ForegroundColor Red
}

# Test Orthanc
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8042/system" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "   Orthanc DICOM Server: Healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "   Orthanc DICOM Server: Not responding" -ForegroundColor Red
}

Write-Host "`nEnterprise ML/AI Healthcare Platform Deployment Complete!" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green

if ($Production) {
    Write-Host "Production mode enabled - ensure all security measures are in place!" -ForegroundColor Yellow
    Write-Host "Next steps for production:" -ForegroundColor Yellow
    Write-Host "   • Configure SSL/TLS certificates" -ForegroundColor Gray
    Write-Host "   • Set up backup procedures" -ForegroundColor Gray
    Write-Host "   • Configure monitoring alerts" -ForegroundColor Gray
    Write-Host "   • Review security configurations" -ForegroundColor Gray
}

Write-Host "`nTo stop all services: docker-compose -f docker-compose.complete.yml down" -ForegroundColor Cyan
Write-Host "To view logs: docker-compose -f docker-compose.complete.yml logs -f [service_name]" -ForegroundColor Cyan