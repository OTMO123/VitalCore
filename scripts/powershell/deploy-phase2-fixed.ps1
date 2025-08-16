# Phase 2: AI/ML Capabilities Deployment - FIXED VERSION
# Vector Database, DICOM Imaging, and ML Services

param(
    [switch]$SkipPhase1Check,
    [switch]$ValidateOnly
)

Write-Host "Phase 2: AI/ML Capabilities Deployment" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

# Set environment variables if not already set
if (-not $env:SECRET_KEY) {
    $env:SECRET_KEY = '3h5dPMCVjESdKNEJFcpgr2pkyb8hLfImMkgBLIJjX8+CBeNHbfLm5s0TZjrKPr4qwvsK3RUU2+dimXdGWSOqAg=='
    $env:ENCRYPTION_KEY = 'wLS/8tedW1PE0EoZZLcuWhfIul5+xg05OJVISJHnr/E='
    $env:JWT_SECRET_KEY = 'aUEoE2V9yrejA9RdlbyDylcN2NY7fNGEkvmVN7FH+hHkiRzlLIdbYBnitaSwyZiiBmagumE/wcnK6BQ52WUv2Q=='
    $env:DATABASE_URL = 'postgresql://postgres:password@localhost:5432/iris_db'
    $env:REDIS_URL = 'redis://localhost:6379/0'
    $env:PHI_ENCRYPTION_KEY = 'xJM+yHn5/5RwwEvOHhRkP01DbbX7wxf1TWEOPOJV+sM='
    $env:MINIO_ACCESS_KEY = 'Jqxh7ZTNKjGRChtjGX9f'
    $env:MINIO_SECRET_KEY = '692pek0uzf9wDUZvVWEDom5J6/UxRXdrU+p3b9dQmarT44zDJqYHvg=='
    $env:AUDIT_SIGNING_KEY = 'ac8b33202bb1fafe9bac30d568b51128f05d05a116651cb0b5daf8de55ecb1400261e9ab33c9f2a2de44b203e8ef368bb579e1712527c7d71188be4b7a8cd956'
    $env:SOC2_COMPLIANCE_MODE = 'true'
    $env:DATABASE_PASSWORD = 'password'
    $env:REDIS_PASSWORD = 'redis_password'
    $env:ORTHANC_API_KEY = 'iris_key'
    Write-Host "   Environment variables set" -ForegroundColor Green
}

# Verify Phase 1 is running
if (-not $SkipPhase1Check) {
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
}

if ($ValidateOnly) {
    Write-Host "`nPhase 2 Deployment Plan:" -ForegroundColor Cyan
    Write-Host "   ✓ Milvus Vector Database (AI/ML Search)" -ForegroundColor Green
    Write-Host "   ✓ Orthanc DICOM Server (Medical Imaging)" -ForegroundColor Green
    Write-Host "   ✓ ML Model Services (Predictions)" -ForegroundColor Green
    Write-Host "`nValidation complete - ready for Phase 2 deployment" -ForegroundColor Green
    exit 0
}

# Generate Phase 2 compose configuration
Write-Host "`nGenerating Phase 2 Docker Compose configuration..." -ForegroundColor Cyan

# Create compose content as a single string to avoid PowerShell parsing issues
$composeContent = @"
version: '3.8'

services:
  # MILVUS VECTOR DATABASE STACK
  milvus-etcd:
    container_name: iris_milvus_etcd_p2
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - etcd_data:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd
    networks:
      - iris_network
    restart: unless-stopped

  milvus-minio:
    container_name: iris_milvus_minio_p2
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - milvus_minio_data:/minio_data
    command: minio server /minio_data
    ports:
      - "9002:9000"
    networks:
      - iris_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3
    restart: unless-stopped

  milvus-standalone:
    container_name: iris_milvus_vector_p2
    image: milvusdb/milvus:v2.3.4
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: milvus-etcd:2379
      MINIO_ADDRESS: milvus-minio:9000
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - milvus_data:/var/lib/milvus
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - "milvus-etcd"
      - "milvus-minio"
    networks:
      - iris_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9091/health"]
      interval: 30s
      timeout: 20s
      retries: 5
    restart: unless-stopped

  # ORTHANC DICOM SERVER
  postgres-orthanc:
    image: postgres:15-alpine
    container_name: iris_postgres_orthanc_p2
    environment:
      POSTGRES_DB: orthanc_db
      POSTGRES_USER: orthanc_user
      POSTGRES_PASSWORD: orthanc_password
    ports:
      - "5433:5432"
    volumes:
      - postgres_orthanc_data:/var/lib/postgresql/data
    networks:
      - iris_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U orthanc_user -d orthanc_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  orthanc:
    image: orthancteam/orthanc:24.6.1
    container_name: iris_orthanc_p2
    environment:
      - ORTHANC__AUTHENTICATION_ENABLED=true
      - 'ORTHANC__REGISTERED_USERS={"admin":"admin123","iris_api":"iris_key"}'
      - ORTHANC__POSTGRESQL__HOST=postgres-orthanc
      - ORTHANC__POSTGRESQL__PORT=5432
      - ORTHANC__POSTGRESQL__DATABASE=orthanc_db
      - ORTHANC__POSTGRESQL__USERNAME=orthanc_user
      - ORTHANC__POSTGRESQL__PASSWORD=orthanc_password
      - ORTHANC__POSTGRESQL__ENABLE_STORAGE=true
      - ORTHANC__POSTGRESQL__ENABLE_INDEX=true
      - ORTHANC__DICOM_AET=IRIS_ORTHANC
      - ORTHANC__DICOM_PORT=4242
    ports:
      - "8042:8042"
      - "4242:4242"
    volumes:
      - orthanc_data:/var/lib/orthanc/db
    depends_on:
      postgres-orthanc:
        condition: service_healthy
    networks:
      - iris_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8042/system"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # MACHINE LEARNING SERVICES
  tensorflow-serving:
    image: tensorflow/serving:2.13.0
    container_name: iris_tensorflow_p2
    environment:
      - MODEL_CONFIG_FILE=/models/models.config
      - MODEL_CONFIG_FILE_POLL_WAIT_SECONDS=60
    ports:
      - "8501:8501"
      - "8500:8500"
    volumes:
      - ./ml_models:/models:ro
    networks:
      - iris_network
    restart: unless-stopped

  jupyter:
    image: jupyter/tensorflow-notebook:python-3.10
    container_name: iris_jupyter_p2
    environment:
      - JUPYTER_ENABLE_LAB=yes
      - JUPYTER_TOKEN=iris_notebook_token
    ports:
      - "8888:8888"
    volumes:
      - jupyter_data:/home/jovyan/work
      - ./ml_models:/home/jovyan/models
    networks:
      - iris_network
    restart: unless-stopped

  # ENHANCED APPLICATION WITH PHASE 2 CAPABILITIES
  app-enhanced:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: iris_app_enhanced_p2
    environment:
      - DEBUG=false
      - ENVIRONMENT=production
      - SECRET_KEY=${SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - DATABASE_URL=postgresql://postgres:password@iris_postgres_p1:5432/iris_db
      - REDIS_URL=redis://:redis_password@iris_redis_p1:6379/0
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - PHI_ENCRYPTION_KEY=${PHI_ENCRYPTION_KEY}
      - MILVUS_HOST=milvus-standalone
      - MILVUS_PORT=19530
      - ORTHANC_URL=http://orthanc:8042
      - ORTHANC_USERNAME=iris_api
      - ORTHANC_PASSWORD=iris_key
      - TENSORFLOW_SERVING_URL=http://tensorflow-serving:8501
      - SOC2_COMPLIANCE_MODE=true
      - AUDIT_SIGNING_KEY=${AUDIT_SIGNING_KEY}
      - DEPLOYMENT_PHASE=2
      - VECTOR_DB_ENABLED=true
      - DICOM_ENABLED=true
      - ML_MODELS_ENABLED=true
    ports:
      - "8001:8000"
    volumes:
      - ./logs:/app/logs
    networks:
      - iris_network
    external_links:
      - iris_postgres_p1:postgres
      - iris_redis_p1:redis
      - iris_minio_p1:minio
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

volumes:
  etcd_data:
  milvus_minio_data:
  milvus_data:
  postgres_orthanc_data:
  orthanc_data:
  jupyter_data:

networks:
  iris_network:
    external: true
"@

# Write compose file
$composeContent | Set-Content -Path "docker-compose.phase2.yml" -Encoding UTF8
Write-Host "   Generated: docker-compose.phase2.yml" -ForegroundColor Green

# Create ML models directory if needed
if (!(Test-Path "ml_models")) {
    New-Item -ItemType Directory -Path "ml_models" -Force | Out-Null
    
    # Create sample model config
    $modelConfig = @'
model_config_list {
  config {
    name: 'healthcare_model'
    base_path: '/models/healthcare_model'
    model_platform: 'tensorflow'
  }
}
'@
    $modelConfig | Set-Content -Path "ml_models/models.config" -Encoding UTF8
    Write-Host "   Created: ml_models directory with sample config" -ForegroundColor Green
}

# Deploy Phase 2
Write-Host "`nDeploying Phase 2 AI/ML Services..." -ForegroundColor Cyan
Write-Host "   • Milvus Vector Database for AI/ML search" -ForegroundColor Yellow
Write-Host "   • Orthanc DICOM Server for medical imaging" -ForegroundColor Yellow
Write-Host "   • TensorFlow Serving and Jupyter notebooks" -ForegroundColor Yellow

# Ensure Phase 1 network exists
$networkCheck = docker network inspect iris_network 2>$null
if ($LASTEXITCODE -ne 0) {
    docker network create iris_network
    Write-Host "   Created: iris_network Docker network" -ForegroundColor Green
}

# Deploy Phase 2 services
docker-compose -f docker-compose.phase2.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "   FAILED: Phase 2 deployment failed" -ForegroundColor Red
    Write-Host "`nGetting deployment logs..." -ForegroundColor Yellow
    docker-compose -f docker-compose.phase2.yml logs --tail=50
    exit 1
}

Write-Host "   PASSED: Phase 2 services started" -ForegroundColor Green

# Wait for services to stabilize
Write-Host "`nWaiting for AI/ML services to initialize..." -ForegroundColor Cyan
Write-Host "   (Vector databases and ML services may take 2-3 minutes)" -ForegroundColor Gray
Start-Sleep -Seconds 180

# Phase 2 Health Checks
Write-Host "`nPhase 2 Health Validation..." -ForegroundColor Cyan

$healthChecks = @(
    @{Name="Milvus Vector Database"; URL="http://localhost:9091/health"},
    @{Name="Orthanc DICOM Server"; URL="http://localhost:8042/system"},
    @{Name="TensorFlow Serving"; URL="http://localhost:8501/v1/models"},
    @{Name="Jupyter Notebooks"; URL="http://localhost:8888/api"},
    @{Name="Enhanced Application"; URL="http://localhost:8001/health"}
)

$failedChecks = @()

foreach ($check in $healthChecks) {
    try {
        $response = Invoke-WebRequest -Uri $check.URL -TimeoutSec 15 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "   PASSED: $($check.Name)" -ForegroundColor Green
        } else {
            Write-Host "   FAILED: $($check.Name) - HTTP $($response.StatusCode)" -ForegroundColor Red
            $failedChecks += $check.Name
        }
    } catch {
        Write-Host "   FAILED: $($check.Name) - Not responding" -ForegroundColor Red
        $failedChecks += $check.Name
    }
}

# Summary
Write-Host "`nPhase 2 Deployment Summary" -ForegroundColor Green
Write-Host "==========================" -ForegroundColor Green

if ($failedChecks.Count -eq 0) {
    Write-Host "STATUS: SUCCESS - All Phase 2 AI/ML services healthy" -ForegroundColor Green
    
    Write-Host "`nPhase 2 Service URLs:" -ForegroundColor Cyan
    Write-Host "  Enhanced Application: http://localhost:8001" -ForegroundColor White
    Write-Host "  API Documentation:    http://localhost:8001/docs" -ForegroundColor White
    Write-Host "  Vector Database:      http://localhost:9091" -ForegroundColor White
    Write-Host "  DICOM Server:         http://localhost:8042" -ForegroundColor White
    Write-Host "  TensorFlow Serving:   http://localhost:8501" -ForegroundColor White
    Write-Host "  Jupyter Notebooks:    http://localhost:8888" -ForegroundColor White
    
    Write-Host "`nAI/ML Capabilities Now Available:" -ForegroundColor Yellow
    Write-Host "  ✓ Vector similarity search and embeddings" -ForegroundColor Green
    Write-Host "  ✓ Medical imaging upload and viewing" -ForegroundColor Green
    Write-Host "  ✓ Machine learning model serving and development" -ForegroundColor Green
    
    Write-Host "`nNext Steps:" -ForegroundColor Yellow
    Write-Host "  1. Test AI/ML features at http://localhost:8001/docs" -ForegroundColor Gray
    Write-Host "  2. Upload test DICOM images to validate imaging workflow" -ForegroundColor Gray
    Write-Host "  3. Deploy Phase 3: .\deploy-phase3.ps1" -ForegroundColor Gray
    
    Write-Host "`nPhase 2 AI/ML Platform: READY FOR ADVANCED WORKFLOWS" -ForegroundColor Green
    exit 0
} else {
    Write-Host "STATUS: PARTIAL FAILURE - Some AI/ML services unhealthy" -ForegroundColor Yellow
    Write-Host "Failed Services: $($failedChecks -join ', ')" -ForegroundColor Red
    
    Write-Host "`nTroubleshooting Commands:" -ForegroundColor Yellow
    Write-Host "  Check logs: docker-compose -f docker-compose.phase2.yml logs [service]" -ForegroundColor Gray
    Write-Host "  Service status: docker-compose -f docker-compose.phase2.yml ps" -ForegroundColor Gray
    Write-Host "  Restart service: docker-compose -f docker-compose.phase2.yml restart [service]" -ForegroundColor Gray
    
    Write-Host "`nNote: Some AI/ML services may need additional time to fully initialize" -ForegroundColor Cyan
    Write-Host "Wait 5 minutes and re-run health checks if services are still starting" -ForegroundColor Cyan
    
    exit 1
}
"@

# Write the compose file
Set-Content -Path "docker-compose.phase2.yml" -Value $composeContent -Encoding UTF8
Write-Host "   Generated: docker-compose.phase2.yml" -ForegroundColor Green