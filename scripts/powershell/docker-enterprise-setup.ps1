# Enterprise Healthcare Docker Setup Script
# Sets up the complete Docker environment for SOC2/HIPAA compliant healthcare API

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("dev", "prod", "test")]
    [string]$Environment = "dev",
    
    [switch]$Clean,
    [switch]$Logs,
    [switch]$Status,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
🏥 Enterprise Healthcare Docker Setup

USAGE:
    .\docker-enterprise-setup.ps1 [OPTIONS]

OPTIONS:
    -Environment <dev|prod|test>   Environment mode (default: dev)
    -Clean                         Clean rebuild with fresh volumes
    -Logs                         Show container logs
    -Status                       Show service status
    -Help                         Show this help

EXAMPLES:
    .\docker-enterprise-setup.ps1                    # Start development environment
    .\docker-enterprise-setup.ps1 -Environment prod  # Production deployment
    .\docker-enterprise-setup.ps1 -Clean             # Fresh rebuild
    .\docker-enterprise-setup.ps1 -Status            # Check status

SERVICES:
    📊 PostgreSQL Database    - Port 5432
    🔴 Redis Cache            - Port 6379
    📦 MinIO Object Storage   - Port 9000/9001
    🚀 Healthcare API         - Port 8000
    ⚙️  Celery Worker         - Background tasks
    ⏰ Celery Scheduler       - Scheduled tasks

SECURITY FEATURES:
    • SOC2 Type II audit logging
    • HIPAA-compliant PHI encryption (AES-256-GCM)
    • FHIR R4 healthcare standards
    • JWT authentication with RS256
    • Role-based access control
"@
    exit 0
}

# Script configuration
$ComposeFile = "docker-compose.yml"
$EnvFile = ".env"
$LogFile = "docker-setup.log"

# Colors and formatting
function Write-Banner {
    param([string]$Text, [string]$Color = "Cyan")
    Write-Host ""
    Write-Host "🏥 $Text" -ForegroundColor $Color
    Write-Host ("=" * ($Text.Length + 3)) -ForegroundColor Gray
}

function Write-Step {
    param([string]$Text, [string]$Color = "Yellow")
    Write-Host "🔧 $Text" -ForegroundColor $Color
}

function Write-Success {
    param([string]$Text)
    Write-Host "✅ $Text" -ForegroundColor Green
}

function Write-Error {
    param([string]$Text)
    Write-Host "❌ $Text" -ForegroundColor Red
}

function Write-Info {
    param([string]$Text)
    Write-Host "ℹ️  $Text" -ForegroundColor Blue
}

# Main execution
try {
    Write-Banner "Enterprise Healthcare Docker Setup"
    Write-Info "Environment: $Environment"
    Write-Info "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    
    if ($Status) {
        Write-Step "Checking service status..."
        docker-compose ps
        Write-Host ""
        
        # Check individual service health
        $services = @("db", "redis", "app", "worker", "scheduler", "minio")
        foreach ($service in $services) {
            $status = docker-compose ps -q $service
            if ($status) {
                $health = docker inspect --format='{{.State.Health.Status}}' $status 2>$null
                if ($health -eq "healthy") {
                    Write-Success "$service is healthy"
                } elseif ($health -eq "unhealthy") {
                    Write-Error "$service is unhealthy"
                } else {
                    Write-Info "$service is running (no health check)"
                }
            } else {
                Write-Error "$service is not running"
            }
        }
        exit 0
    }
    
    if ($Logs) {
        Write-Step "Showing container logs..."
        docker-compose logs --tail=50 -f
        exit 0
    }
    
    # Clean rebuild if requested
    if ($Clean) {
        Write-Step "Performing clean rebuild..."
        Write-Host "⚠️  This will remove all data and containers!" -ForegroundColor Yellow
        $confirm = Read-Host "Continue? (y/N)"
        if ($confirm -eq "y" -or $confirm -eq "Y") {
            docker-compose down -v --remove-orphans
            docker system prune -f
            Write-Success "Clean completed"
        } else {
            Write-Info "Clean cancelled"
            exit 0
        }
    }
    
    # Environment setup
    Write-Step "Setting up environment configuration..."
    
    # Create environment file based on mode
    $debugValue = if ($Environment -eq "dev") { "true" } else { "false" }
    $secretKey = if ($Environment -eq "prod") { "CHANGE-THIS-SECRET-KEY-IN-PRODUCTION" } else { "development-secret-key" }
    $encryptionKey = if ($Environment -eq "prod") { "CHANGE-THIS-ENCRYPTION-KEY-IN-PRODUCTION" } else { "development-encryption-key" }
    $jwtSecretKey = if ($Environment -eq "prod") { "CHANGE-THIS-JWT-SECRET-IN-PRODUCTION" } else { "development-jwt-secret" }
    $logLevel = if ($Environment -eq "prod") { "INFO" } else { "DEBUG" }
    $workerCount = if ($Environment -eq "prod") { "4" } else { "1" }
    
    $envContent = @"
# Healthcare API Environment Configuration
ENVIRONMENT=$Environment
DEBUG=$debugValue

# Database Configuration  
DATABASE_URL=postgresql://postgres:password@db:5432/iris_db
POSTGRES_DB=iris_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Security Configuration (CHANGE IN PRODUCTION!)
SECRET_KEY=$secretKey
ENCRYPTION_KEY=$encryptionKey
JWT_SECRET_KEY=$jwtSecretKey

# MinIO Configuration
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minio123secure
MINIO_KMS_SECRET_KEY=my-minio-key:OSMM+vkIiXEQKs4K1bL7YYjHp8xQIm9xJFf/F1lPdg0=

# Healthcare API Configuration
API_TITLE=Enterprise Healthcare API
API_VERSION=1.0.0
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Logging Configuration
LOG_LEVEL=$logLevel
AUDIT_LOG_RETENTION_DAYS=2555

# Performance Configuration
WORKER_COUNT=$workerCount
MAX_CONNECTIONS=100
"@
    
    $envContent | Out-File -FilePath $EnvFile -Encoding UTF8
    Write-Success "Environment configuration created"
    
    # Check Docker prerequisites
    Write-Step "Checking Docker prerequisites..."
    
    try {
        $dockerVersion = docker --version
        Write-Success "Docker found: $dockerVersion"
    } catch {
        Write-Error "Docker not found! Please install Docker Desktop"
        exit 1
    }
    
    try {
        $composeVersion = docker-compose --version
        Write-Success "Docker Compose found: $composeVersion"
    } catch {
        Write-Error "Docker Compose not found! Please install Docker Compose"
        exit 1
    }
    
    # Start services
    Write-Step "Starting healthcare services..."
    
    if ($Environment -eq "prod") {
        Write-Host "⚠️  Production mode detected!" -ForegroundColor Yellow
        Write-Host "⚠️  Ensure you've changed default secrets!" -ForegroundColor Yellow
    }
    
    # Build and start services
    docker-compose up -d --build
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Services started successfully"
    } else {
        Write-Error "Failed to start services"
        exit 1
    }
    
    # Wait for services to be healthy
    Write-Step "Waiting for services to be ready..."
    $maxWait = 120  # 2 minutes
    $waited = 0
    $interval = 5
    
    while ($waited -lt $maxWait) {
        $dbReady = docker-compose exec -T db pg_isready -U postgres 2>$null
        $redisReady = docker-compose exec -T redis redis-cli ping 2>$null
        
        if ($dbReady -match "accepting connections" -and $redisReady -match "PONG") {
            Write-Success "Core services are ready"
            break
        }
        
        Write-Host "." -NoNewline
        Start-Sleep $interval
        $waited += $interval
    }
    
    if ($waited -ge $maxWait) {
        Write-Error "Services did not become ready in time"
        Write-Info "Check logs with: docker-compose logs"
        exit 1
    }
    
    # Run database migrations
    Write-Step "Running database migrations..."
    docker-compose exec app alembic upgrade head
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Database migrations completed"
    } else {
        Write-Error "Database migrations failed"
        Write-Info "Check app logs: docker-compose logs app"
    }
    
    # Service status summary
    Write-Banner "Healthcare API Services Ready" "Green"
    
    Write-Host ""
    Write-Host "🌐 SERVICE ENDPOINTS:" -ForegroundColor Cyan
    Write-Host "   Healthcare API:    http://localhost:8000" -ForegroundColor White
    Write-Host "   API Documentation: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "   Health Check:      http://localhost:8000/health" -ForegroundColor White
    Write-Host "   MinIO Console:     http://localhost:9001" -ForegroundColor White
    Write-Host ""
    
    Write-Host "🗄️  DATABASE ACCESS:" -ForegroundColor Cyan
    Write-Host "   PostgreSQL:        localhost:5432" -ForegroundColor White
    Write-Host "   Database:          iris_db" -ForegroundColor White
    Write-Host "   Username:          postgres" -ForegroundColor White
    Write-Host "   Password:          password" -ForegroundColor White
    Write-Host ""
    
    Write-Host "🔴 REDIS ACCESS:" -ForegroundColor Cyan
    Write-Host "   Redis:             localhost:6379" -ForegroundColor White
    Write-Host ""
    
    Write-Host "🔧 USEFUL COMMANDS:" -ForegroundColor Cyan
    Write-Host "   View logs:         docker-compose logs -f" -ForegroundColor White
    Write-Host "   Check status:      .\docker-enterprise-setup.ps1 -Status" -ForegroundColor White
    Write-Host "   Stop services:     docker-compose down" -ForegroundColor White
    Write-Host "   Clean rebuild:     .\docker-enterprise-setup.ps1 -Clean" -ForegroundColor White
    Write-Host ""
    
    if ($Environment -eq "dev") {
        Write-Host "🧪 TESTING:" -ForegroundColor Cyan
        Write-Host "   Run tests:         .\validate_core_security_fixes.ps1" -ForegroundColor White
        Write-Host "   Role validation:   .\validate-role-based-security.ps1" -ForegroundColor White
        Write-Host ""
    }
    
    Write-Success "Enterprise Healthcare API is ready for $Environment operations!"
    
    if ($Environment -eq "prod") {
        Write-Host ""
        Write-Host "🚨 PRODUCTION CHECKLIST:" -ForegroundColor Red
        Write-Host "   □ Change default SECRET_KEY" -ForegroundColor Yellow
        Write-Host "   □ Change default ENCRYPTION_KEY" -ForegroundColor Yellow  
        Write-Host "   □ Change default JWT_SECRET_KEY" -ForegroundColor Yellow
        Write-Host "   □ Change default database password" -ForegroundColor Yellow
        Write-Host "   □ Configure SSL/TLS certificates" -ForegroundColor Yellow
        Write-Host "   □ Set up backup procedures" -ForegroundColor Yellow
        Write-Host "   □ Configure monitoring and alerting" -ForegroundColor Yellow
    }
    
} catch {
    Write-Error "Setup failed: $($_.Exception.Message)"
    Write-Info "Check logs: $LogFile"
    $_.Exception | Out-File -FilePath $LogFile -Append
    exit 1
}