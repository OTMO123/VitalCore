# Phase 2: AI/ML Capabilities Deployment
# Vector Database, DICOM Imaging, and ML Services

param(
    [switch]$IncludeVectorDB,
    [switch]$IncludeDICOM,
    [switch]$IncludeMLModels,
    [switch]$SkipPhase1Check,
    [switch]$ValidateOnly
)

Write-Host "Phase 2: AI/ML Capabilities Deployment" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

# Verify Phase 1 is running
if (!$SkipPhase1Check) {
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

# Default to all Phase 2 services if no specific flags provided
if (!$IncludeVectorDB -and !$IncludeDICOM -and !$IncludeMLModels) {
    $IncludeVectorDB = $true
    $IncludeDICOM = $true
    $IncludeMLModels = $true
    Write-Host "   INFO: No specific services selected, deploying all Phase 2 services" -ForegroundColor Cyan
}

if ($ValidateOnly) {
    Write-Host "`nPhase 2 Deployment Plan:" -ForegroundColor Cyan
    if ($IncludeVectorDB) { Write-Host "   ✓ Milvus Vector Database (AI/ML Search)" -ForegroundColor Green }
    if ($IncludeDICOM) { Write-Host "   ✓ Orthanc DICOM Server (Medical Imaging)" -ForegroundColor Green }
    if ($IncludeMLModels) { Write-Host "   ✓ ML Model Services (Predictions)" -ForegroundColor Green }
    Write-Host "`nValidation complete - ready for Phase 2 deployment" -ForegroundColor Green
    exit 0
}

# Generate Phase 2 compose configuration
Write-Host "`nGenerating Phase 2 Docker Compose configuration..." -ForegroundColor Cyan

$vectorDbServices = ""
$dicomServices = ""
$mlServices = ""

# Vector Database Services
if ($IncludeVectorDB) {
    $vectorDbServices = @'
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
      MINIO_ACCESS_KEY: ${MILVUS_ACCESS_KEY:-minioadmin}
      MINIO_SECRET_KEY: ${MILVUS_SECRET_KEY:-minioadmin}  
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
      MINIO_ACCESS_KEY: ${MILVUS_ACCESS_KEY:-minioadmin}
      MINIO_SECRET_KEY: ${MILVUS_SECRET_KEY:-minioadmin}
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

'@
}

# DICOM Services
if ($IncludeDICOM) {
    $dicomServices = @'
  # ORTHANC DICOM SERVER
  postgres-orthanc:
    image: postgres:15-alpine
    container_name: iris_postgres_orthanc_p2
    environment:
      POSTGRES_DB: orthanc_db
      POSTGRES_USER: orthanc_user
      POSTGRES_PASSWORD: ${ORTHANC_DB_PASSWORD:-orthanc_password}
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
      - 'ORTHANC__REGISTERED_USERS={"admin":"${ORTHANC_PASSWORD:-admin123}","iris_api":"${ORTHANC_API_KEY:-iris_key}"}'
      - ORTHANC__POSTGRESQL__HOST=postgres-orthanc
      - ORTHANC__POSTGRESQL__PORT=5432
      - ORTHANC__POSTGRESQL__DATABASE=orthanc_db
      - ORTHANC__POSTGRESQL__USERNAME=orthanc_user
      - ORTHANC__POSTGRESQL__PASSWORD=${ORTHANC_DB_PASSWORD:-orthanc_password}
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

'@
}

# ML Model Services
if ($IncludeMLModels) {
    $mlServices = @'
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
      - JUPYTER_TOKEN=${JUPYTER_TOKEN:-iris_notebook_token}
    ports:
      - "8888:8888"
    volumes:
      - jupyter_data:/home/jovyan/work
      - ./ml_models:/home/jovyan/models
    networks:
      - iris_network
    restart: unless-stopped

'@
}

# Build the complete compose content with proper concatenation
$composeServices = $vectorDbServices + $dicomServices + $mlServices

# Determine environment variables for enhanced app
$milvusHost = if ($IncludeVectorDB) { "milvus-standalone" } else { "localhost" }
$orthancUrl = if ($IncludeDICOM) { "http://orthanc:8042" } else { "http://localhost:8042" }
$tensorflowUrl = if ($IncludeMLModels) { "http://tensorflow-serving:8501" } else { "http://localhost:8501" }
$vectorDbEnabled = $IncludeVectorDB.ToString().ToLower()
$dicomEnabled = $IncludeDICOM.ToString().ToLower()
$mlModelsEnabled = $IncludeMLModels.ToString().ToLower()

# Create compose content by building it piece by piece to avoid PowerShell parsing issues
$composeHeader = @'
version: '3.8'

services:
'@

$appService = @'
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
      - DATABASE_URL=postgresql://postgres:${DATABASE_PASSWORD:-password}@iris_postgres_p1:5432/iris_db
      - REDIS_URL=redis://:${REDIS_PASSWORD:-redis_password}@iris_redis_p1:6379/0
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - PHI_ENCRYPTION_KEY=${PHI_ENCRYPTION_KEY}
'@

$appService += "`n      - MILVUS_HOST=$milvusHost"
$appService += "`n      - MILVUS_PORT=19530"
$appService += "`n      - ORTHANC_URL=$orthancUrl"
$appService += "`n      - ORTHANC_USERNAME=iris_api"
$appService += "`n      - ORTHANC_PASSWORD=`${ORTHANC_API_KEY:-iris_key}"
$appService += "`n      - TENSORFLOW_SERVING_URL=$tensorflowUrl"
$appService += "`n      - SOC2_COMPLIANCE_MODE=true"
$appService += "`n      - AUDIT_SIGNING_KEY=`${AUDIT_SIGNING_KEY}"
$appService += "`n      - DEPLOYMENT_PHASE=2"
$appService += "`n      - VECTOR_DB_ENABLED=$vectorDbEnabled"
$appService += "`n      - DICOM_ENABLED=$dicomEnabled"
$appService += "`n      - ML_MODELS_ENABLED=$mlModelsEnabled"

$appService += @'

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

'@

$volumesHeader = @'

volumes:
'@

# Build the complete compose content
$phase2Compose = $composeHeader + $composeServices + $appService + $volumesHeader

# Add volumes conditionally
if ($IncludeVectorDB) {
    $phase2Compose += @"
  etcd_data:
  milvus_minio_data:
  milvus_data:
"@
}

if ($IncludeDICOM) {
    $phase2Compose += @"
  postgres_orthanc_data:
  orthanc_data:
"@
}

if ($IncludeMLModels) {
    $phase2Compose += @"
  jupyter_data:
"@
}

$phase2Compose += @'

networks:
  iris_network:
    external: true
'@

# Write the compose file
$phase2Compose | Out-File -FilePath "docker-compose.phase2.yml" -Encoding UTF8
Write-Host "   Generated docker-compose.phase2.yml" -ForegroundColor Green

# Create ML models directory if needed
if ($IncludeMLModels) {
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
        $modelConfig | Out-File -FilePath "ml_models/models.config" -Encoding UTF8
        Write-Host "   Created: ml_models directory with sample config" -ForegroundColor Green
    }
}

# Deploy Phase 2
Write-Host "`nDeploying Phase 2 AI/ML Services..." -ForegroundColor Cyan
if ($IncludeVectorDB) { Write-Host "   • Milvus Vector Database for AI/ML search" -ForegroundColor Yellow }
if ($IncludeDICOM) { Write-Host "   • Orthanc DICOM Server for medical imaging" -ForegroundColor Yellow }
if ($IncludeMLModels) { Write-Host "   • TensorFlow Serving and Jupyter notebooks" -ForegroundColor Yellow }

# Ensure Phase 1 network exists
docker network inspect iris_network >$null 2>&1
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

$healthChecks = @()

if ($IncludeVectorDB) {
    $healthChecks += @{Name="Milvus Vector Database"; URL="http://localhost:9091/health"}
}

if ($IncludeDICOM) {
    $healthChecks += @{Name="Orthanc DICOM Server"; URL="http://localhost:8042/system"}
    $healthChecks += @{Name="Orthanc PostgreSQL"; Command="docker exec iris_postgres_orthanc_p2 pg_isready -U orthanc_user"}
}

if ($IncludeMLModels) {
    $healthChecks += @{Name="TensorFlow Serving"; URL="http://localhost:8501/v1/models"}
    $healthChecks += @{Name="Jupyter Notebooks"; URL="http://localhost:8888/api"}
}

$healthChecks += @{Name="Enhanced Application"; URL="http://localhost:8001/health"}

$failedChecks = @()

foreach ($check in $healthChecks) {
    if ($check.Command) {
        try {
            $result = Invoke-Expression $check.Command 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   PASSED: $($check.Name)" -ForegroundColor Green
            } else {
                Write-Host "   FAILED: $($check.Name)" -ForegroundColor Red
                $failedChecks += $check.Name
            }
        } catch {
            Write-Host "   FAILED: $($check.Name) - $($_.Exception.Message)" -ForegroundColor Red
            $failedChecks += $check.Name
        }
    } elseif ($check.URL) {
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
}

# Summary
Write-Host "`nPhase 2 Deployment Summary" -ForegroundColor Green
Write-Host "==========================" -ForegroundColor Green

if ($failedChecks.Count -eq 0) {
    Write-Host "STATUS: SUCCESS - All Phase 2 AI/ML services healthy" -ForegroundColor Green
    
    Write-Host "`nPhase 2 Service URLs:" -ForegroundColor Cyan
    Write-Host "  Enhanced Application: http://localhost:8001" -ForegroundColor White
    Write-Host "  API Documentation:    http://localhost:8001/docs" -ForegroundColor White
    if ($IncludeVectorDB) {
        Write-Host "  Vector Database:      http://localhost:9091" -ForegroundColor White
    }
    if ($IncludeDICOM) {
        Write-Host "  DICOM Server:         http://localhost:8042" -ForegroundColor White
    }
    if ($IncludeMLModels) {
        Write-Host "  TensorFlow Serving:   http://localhost:8501" -ForegroundColor White
        Write-Host "  Jupyter Notebooks:    http://localhost:8888" -ForegroundColor White
    }
    
    Write-Host "`nAI/ML Capabilities Now Available:" -ForegroundColor Yellow
    if ($IncludeVectorDB) { Write-Host "  ✓ Vector similarity search and embeddings" -ForegroundColor Green }
    if ($IncludeDICOM) { Write-Host "  ✓ Medical imaging upload and viewing" -ForegroundColor Green }
    if ($IncludeMLModels) { Write-Host "  ✓ Machine learning model serving and development" -ForegroundColor Green }
    
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