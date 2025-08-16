# Phase 1: Foundation Deployment
# Critical P0 services that must work for system to function

param(
    [ValidateSet("Development", "Staging", "Production")]
    [string]$Environment = "Development",
    [switch]$EnableSSL,
    [switch]$SkipBuild,
    [switch]$ValidateOnly
)

Write-Host "Phase 1: Foundation Deployment" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green
Write-Host "Environment: $Environment" -ForegroundColor Cyan

# Phase 1 Service Priority Matrix
$Phase1Services = @{
    "P0_Critical" = @("postgres", "redis", "app")
    "P1_High" = @("minio", "prometheus")
}

# Validate environment variables
Write-Host "`nValidating environment configuration..." -ForegroundColor Cyan
$requiredVars = @('SECRET_KEY', 'JWT_SECRET_KEY', 'PHI_ENCRYPTION_KEY', 'AUDIT_SIGNING_KEY')
$missingVars = @()

foreach ($var in $requiredVars) {
    if ([string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($var))) {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "   FAILED: Missing environment variables:" -ForegroundColor Red
    foreach ($var in $missingVars) {
        Write-Host "      - $var" -ForegroundColor Red
    }
    Write-Host "`n   Run: .\deploy-complete-stack.ps1 -GenerateSecrets" -ForegroundColor Yellow
    exit 1
}
Write-Host "   PASSED: All required environment variables present" -ForegroundColor Green

# Check Docker availability
Write-Host "`nValidating Docker environment..." -ForegroundColor Cyan
try {
    $dockerVersion = docker --version
    Write-Host "   PASSED: Docker available - $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "   FAILED: Docker not available" -ForegroundColor Red
    exit 1
}

if ($ValidateOnly) {
    Write-Host "`nValidation complete - ready for Phase 1 deployment" -ForegroundColor Green
    exit 0
}

# Create Phase 1 compose file
Write-Host "`nGenerating Phase 1 Docker Compose configuration..." -ForegroundColor Cyan

$phase1Compose = @"
version: '3.8'

services:
  # P0 CRITICAL SERVICES
  postgres:
    image: postgres:15-alpine
    container_name: iris_postgres_p1
    environment:
      POSTGRES_DB: iris_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: `${DATABASE_PASSWORD:-password}
      POSTGRES_INITDB_ARGS: "--auth=scram-sha-256"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - iris_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d iris_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: iris_redis_p1
    command: redis-server --requirepass `${REDIS_PASSWORD:-redis_password} --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - iris_network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    restart: unless-stopped

  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: iris_app_p1
    environment:
      - DEBUG=`${DEBUG:-false}
      - ENVIRONMENT=`$Environment
      - SECRET_KEY=`${SECRET_KEY}
      - ENCRYPTION_KEY=`${ENCRYPTION_KEY}
      - DATABASE_URL=postgresql://postgres:`${DATABASE_PASSWORD:-password}@postgres:5432/iris_db
      - REDIS_URL=redis://:`${REDIS_PASSWORD:-redis_password}@redis:6379/0
      - JWT_SECRET_KEY=`${JWT_SECRET_KEY}
      - PHI_ENCRYPTION_KEY=`${PHI_ENCRYPTION_KEY}
      - SOC2_COMPLIANCE_MODE=true
      - AUDIT_SIGNING_KEY=`${AUDIT_SIGNING_KEY}
      - DEPLOYMENT_PHASE=1
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - iris_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # P1 HIGH PRIORITY SERVICES  
  minio:
    image: minio/minio:latest
    container_name: iris_minio_p1
    environment:
      MINIO_ROOT_USER: `${MINIO_ACCESS_KEY:-minioadmin}
      MINIO_ROOT_PASSWORD: `${MINIO_SECRET_KEY:-minio123secure}
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    networks:
      - iris_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:v2.45.0
    container_name: iris_prometheus_p1
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    networks:
      - iris_network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  minio_data:
  prometheus_data:

networks:
  iris_network:
    driver: bridge
"@

$phase1Compose | Out-File -FilePath "docker-compose.phase1.yml" -Encoding UTF8
Write-Host "   Generated: docker-compose.phase1.yml" -ForegroundColor Green

# Deploy Phase 1
Write-Host "`nDeploying Phase 1 Foundation Services..." -ForegroundColor Cyan
Write-Host "   Priority P0 (Critical): PostgreSQL, Redis, FastAPI Core" -ForegroundColor Yellow
Write-Host "   Priority P1 (High): MinIO Storage, Basic Monitoring" -ForegroundColor Gray

# Stop any existing services
docker-compose -f docker-compose.phase1.yml down --remove-orphans 2>$null

# Build if not skipping
if (!$SkipBuild) {
    Write-Host "`nBuilding application for Phase 1..." -ForegroundColor Cyan
    docker-compose -f docker-compose.phase1.yml build --no-cache
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   FAILED: Application build failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "   PASSED: Application built successfully" -ForegroundColor Green
}

# Deploy services
docker-compose -f docker-compose.phase1.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "   FAILED: Phase 1 deployment failed" -ForegroundColor Red
    Write-Host "`nGetting deployment logs..." -ForegroundColor Yellow
    docker-compose -f docker-compose.phase1.yml logs --tail=50
    exit 1
}

Write-Host "   PASSED: Phase 1 services started" -ForegroundColor Green

# Wait for services to stabilize
Write-Host "`nWaiting for services to stabilize..." -ForegroundColor Cyan
Start-Sleep -Seconds 60

# Phase 1 Health Checks
Write-Host "`nPhase 1 Health Validation..." -ForegroundColor Cyan

$healthChecks = @(
    @{Name="PostgreSQL Database"; Command="docker exec iris_postgres_p1 pg_isready -U postgres"},
    @{Name="Redis Cache"; Command="docker exec iris_redis_p1 redis-cli ping"},
    @{Name="FastAPI Application"; URL="http://localhost:8000/health"},
    @{Name="MinIO Storage"; URL="http://localhost:9000/minio/health/live"},
    @{Name="Prometheus Monitoring"; URL="http://localhost:9090/-/healthy"}
)

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
            $response = Invoke-WebRequest -Uri $check.URL -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
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
Write-Host "`nPhase 1 Deployment Summary" -ForegroundColor Green
Write-Host "==========================" -ForegroundColor Green

if ($failedChecks.Count -eq 0) {
    Write-Host "STATUS: SUCCESS - All Phase 1 services healthy" -ForegroundColor Green
    
    Write-Host "`nPhase 1 Service URLs:" -ForegroundColor Cyan
    Write-Host "  Main Application:    http://localhost:8000" -ForegroundColor White
    Write-Host "  API Documentation:   http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  MinIO Console:       http://localhost:9001" -ForegroundColor White
    Write-Host "  Prometheus:          http://localhost:9090" -ForegroundColor White
    
    Write-Host "`nNext Steps:" -ForegroundColor Yellow
    Write-Host "  1. Validate core functionality at http://localhost:8000/docs" -ForegroundColor Gray
    Write-Host "  2. Run comprehensive tests: .\scripts\test-phase1.ps1" -ForegroundColor Gray
    Write-Host "  3. Deploy Phase 2: .\deploy-phase2.ps1" -ForegroundColor Gray
    
    Write-Host "`nPhase 1 Foundation: READY FOR PRODUCTION" -ForegroundColor Green
    exit 0
} else {
    Write-Host "STATUS: PARTIAL FAILURE - Some services unhealthy" -ForegroundColor Yellow
    Write-Host "Failed Services: $($failedChecks -join ', ')" -ForegroundColor Red
    
    Write-Host "`nTroubleshooting Commands:" -ForegroundColor Yellow
    Write-Host "  Check logs: docker-compose -f docker-compose.phase1.yml logs [service]" -ForegroundColor Gray
    Write-Host "  Service status: docker-compose -f docker-compose.phase1.yml ps" -ForegroundColor Gray
    Write-Host "  Restart service: docker-compose -f docker-compose.phase1.yml restart [service]" -ForegroundColor Gray
    
    exit 1
}