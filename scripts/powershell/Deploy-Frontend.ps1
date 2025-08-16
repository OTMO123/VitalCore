# VitalCore Frontend Docker Deployment Script
# Comprehensive deployment for frontend + backend integration
# PowerShell version for Windows

param(
    [Parameter(Position=0)]
    [ValidateSet("deploy", "start", "stop", "restart", "status", "logs", "health", "cleanup", "urls", "help")]
    [string]$Action = "deploy",
    
    [Parameter(Position=1)]
    [string]$LogAction = ""
)

# Configuration
$ComposeFile = "docker-compose.frontend.yml"
$ProjectName = "vitalcore"
$FrontendPort = 5173
$BackendPort = 8000
$NginxPort = 80

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"
$White = "White"

# Logging functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Red
}

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check Docker
    try {
        $null = docker --version
        Write-Success "Docker is installed"
    }
    catch {
        Write-Error "Docker is not installed or not in PATH"
        return $false
    }
    
    # Check Docker Compose
    try {
        $null = docker-compose --version
        Write-Success "Docker Compose is installed"
    }
    catch {
        Write-Error "Docker Compose is not installed or not in PATH"
        return $false
    }
    
    # Check compose file
    if (-not (Test-Path $ComposeFile)) {
        Write-Error "Docker Compose file not found: $ComposeFile"
        return $false
    }
    
    Write-Success "Prerequisites check passed"
    return $true
}

# Stop existing containers
function Stop-ExistingContainers {
    Write-Info "Stopping existing containers..."
    
    try {
        $runningContainers = docker-compose -f $ComposeFile ps -q
        if ($runningContainers) {
            docker-compose -f $ComposeFile down
            Write-Success "Existing containers stopped"
        } else {
            Write-Info "No existing containers to stop"
        }
    }
    catch {
        Write-Warning "Error stopping containers: $($_.Exception.Message)"
    }
}

# Build and start services
function Start-Services {
    Write-Info "Building and starting services..."
    
    try {
        # Build images
        Write-Info "Building Docker images..."
        docker-compose -f $ComposeFile build --no-cache
        
        # Start services
        Write-Info "Starting services..."
        docker-compose -f $ComposeFile up -d
        
        Write-Success "Services started"
        return $true
    }
    catch {
        Write-Error "Failed to start services: $($_.Exception.Message)"
        return $false
    }
}

# Wait for services to be ready
function Wait-ForServices {
    Write-Info "Waiting for services to be ready..."
    
    # Wait for database
    Write-Info "Waiting for PostgreSQL..."
    $timeout = 60
    $elapsed = 0
    do {
        try {
            $null = docker-compose -f $ComposeFile exec -T db pg_isready -U postgres 2>$null
            if ($LASTEXITCODE -eq 0) { break }
        }
        catch { }
        
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
        $elapsed += 2
    } while ($elapsed -lt $timeout)
    
    if ($elapsed -ge $timeout) {
        Write-Error "PostgreSQL failed to start within $timeout seconds"
        return $false
    }
    Write-Host ""
    Write-Success "PostgreSQL is ready"
    
    # Wait for Redis
    Write-Info "Waiting for Redis..."
    $elapsed = 0
    do {
        try {
            $null = docker-compose -f $ComposeFile exec -T redis redis-cli ping 2>$null
            if ($LASTEXITCODE -eq 0) { break }
        }
        catch { }
        
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
        $elapsed += 2
    } while ($elapsed -lt $timeout)
    
    if ($elapsed -ge $timeout) {
        Write-Error "Redis failed to start within $timeout seconds"
        return $false
    }
    Write-Host ""
    Write-Success "Redis is ready"
    
    # Wait for backend API
    Write-Info "Waiting for backend API..."
    $elapsed = 0
    do {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$BackendPort/health" -TimeoutSec 3 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) { break }
        }
        catch { }
        
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 3
        $elapsed += 3
    } while ($elapsed -lt $timeout)
    
    if ($elapsed -ge $timeout) {
        Write-Error "Backend API failed to start within $timeout seconds"
        return $false
    }
    Write-Host ""
    Write-Success "Backend API is ready"
    
    # Wait for frontend
    Write-Info "Waiting for frontend..."
    $elapsed = 0
    do {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$FrontendPort" -TimeoutSec 3 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) { break }
        }
        catch { }
        
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 3
        $elapsed += 3
    } while ($elapsed -lt $timeout)
    
    if ($elapsed -ge $timeout) {
        Write-Error "Frontend failed to start within $timeout seconds"
        return $false
    }
    Write-Host ""
    Write-Success "Frontend is ready"
    
    return $true
}

# Run health checks
function Test-ServiceHealth {
    Write-Info "Running health checks..."
    
    $services = @(
        @{Name="db"; Description="PostgreSQL"},
        @{Name="redis"; Description="Redis"},
        @{Name="app"; Description="Backend API"},
        @{Name="frontend"; Description="Frontend"},
        @{Name="worker"; Description="Celery Worker"},
        @{Name="scheduler"; Description="Celery Beat"},
        @{Name="minio"; Description="MinIO"}
    )
    
    $allHealthy = $true
    
    foreach ($service in $services) {
        try {
            $status = docker-compose -f $ComposeFile ps $service.Name | Select-String "Up \(healthy\)|Up"
            if ($status -match "Up \(healthy\)") {
                Write-Success "$($service.Description) is healthy"
            }
            elseif ($status -match "Up") {
                Write-Warning "$($service.Description) is running (health check not available)"
            }
            else {
                Write-Error "$($service.Description) is not running"
                $allHealthy = $false
            }
        }
        catch {
            Write-Error "$($service.Description) status check failed"
            $allHealthy = $false
        }
    }
    
    if ($allHealthy) {
        Write-Success "All services are healthy"
        return $true
    } else {
        Write-Error "Some services are not healthy"
        return $false
    }
}

# Show service URLs
function Show-ServiceUrls {
    Write-Info "Service URLs:"
    Write-Host "==============" -ForegroundColor $White
    Write-Host "🏥 VitalCore Frontend:     http://localhost:$FrontendPort" -ForegroundColor $Green
    Write-Host "🩺 Production Frontend:    http://localhost:$FrontendPort/components/core/VitalCore-Production.html" -ForegroundColor $Green
    Write-Host "🧠 MedBrain Enhanced:      http://localhost:$FrontendPort/components/core/MedBrain-Enhanced.html" -ForegroundColor $Green
    Write-Host "🔧 Backend API:            http://localhost:$BackendPort" -ForegroundColor $Blue
    Write-Host "📚 API Documentation:     http://localhost:$BackendPort/docs" -ForegroundColor $Blue
    Write-Host "🗄️  MinIO Console:         http://localhost:9001" -ForegroundColor $Yellow
    Write-Host "🔍 Database:               localhost:5432 (postgres/password)" -ForegroundColor $Yellow
    Write-Host "🔴 Redis:                  localhost:6379" -ForegroundColor $Yellow
    
    try {
        $nginxStatus = docker-compose -f $ComposeFile ps nginx 2>$null
        if ($nginxStatus -and $nginxStatus -match "Up") {
            Write-Host "🌐 Nginx Proxy:           http://localhost:$NginxPort" -ForegroundColor $Green
        }
    }
    catch { }
    
    Write-Host ""
}

# Show service status
function Show-ServiceStatus {
    Write-Info "Service Status:"
    Write-Host "===============" -ForegroundColor $White
    try {
        docker-compose -f $ComposeFile ps
    }
    catch {
        Write-Error "Failed to get service status: $($_.Exception.Message)"
    }
    Write-Host ""
}

# Show logs
function Show-ServiceLogs {
    param([string]$LogAction)
    
    if ($LogAction -eq "follow") {
        Write-Info "Following logs (Ctrl+C to stop)..."
        try {
            docker-compose -f $ComposeFile logs -f
        }
        catch {
            Write-Warning "Log following interrupted"
        }
    } else {
        Write-Info "Recent logs:"
        try {
            docker-compose -f $ComposeFile logs --tail=50
        }
        catch {
            Write-Error "Failed to get logs: $($_.Exception.Message)"
        }
    }
}

# Cleanup function
function Invoke-Cleanup {
    Write-Info "Cleaning up..."
    try {
        docker-compose -f $ComposeFile down
        docker system prune -f
        Write-Success "Cleanup completed"
    }
    catch {
        Write-Error "Cleanup failed: $($_.Exception.Message)"
    }
}

# Main deployment function
function Invoke-Deployment {
    Write-Info "Starting VitalCore deployment..."
    
    if (-not (Test-Prerequisites)) {
        exit 1
    }
    
    Stop-ExistingContainers
    
    if (-not (Start-Services)) {
        exit 1
    }
    
    if (-not (Wait-ForServices)) {
        Write-Error "Services failed to start properly"
        exit 1
    }
    
    if (Test-ServiceHealth) {
        Write-Success "🎉 VitalCore deployment completed successfully!"
        Write-Host ""
        
        Show-ServiceUrls
        Show-ServiceStatus
        
        Write-Info "🎯 Quick Test Commands:"
        Write-Host "Invoke-WebRequest http://localhost:$BackendPort/health    # Backend health" -ForegroundColor $White
        Write-Host "Invoke-WebRequest http://localhost:$FrontendPort           # Frontend" -ForegroundColor $White
        Write-Host ""
        
        Write-Info "📋 Management Commands:"
        Write-Host ".\Deploy-Frontend.ps1 logs          # View logs" -ForegroundColor $White
        Write-Host ".\Deploy-Frontend.ps1 logs follow   # Follow logs" -ForegroundColor $White
        Write-Host ".\Deploy-Frontend.ps1 status        # Service status" -ForegroundColor $White
        Write-Host ".\Deploy-Frontend.ps1 stop          # Stop services" -ForegroundColor $White
        Write-Host ".\Deploy-Frontend.ps1 cleanup       # Full cleanup" -ForegroundColor $White
        Write-Host ""
        
        Write-Info "🧪 Test the enhanced MedBrain with voice recognition!"
        Write-Info "Visit: http://localhost:$FrontendPort/components/core/VitalCore-Production.html"
        
    } else {
        Write-Error "Deployment failed - some services are not healthy"
        exit 1
    }

# Show help
function Show-Help {
    Write-Host "VitalCore Frontend Docker Deployment Script" -ForegroundColor $Green
    Write-Host "===========================================" -ForegroundColor $Green
    Write-Host ""
    Write-Host "Usage: .\Deploy-Frontend.ps1 [Action] [Options]" -ForegroundColor $White
    Write-Host ""
    Write-Host "Actions:" -ForegroundColor $Yellow
    Write-Host "  deploy    - Deploy all services (default)" -ForegroundColor $White
    Write-Host "  start     - Same as deploy" -ForegroundColor $White
    Write-Host "  stop      - Stop all services" -ForegroundColor $White
    Write-Host "  restart   - Restart all services" -ForegroundColor $White
    Write-Host "  status    - Show service status" -ForegroundColor $White
    Write-Host "  logs      - Show recent logs" -ForegroundColor $White
    Write-Host "  logs follow - Follow logs in real-time" -ForegroundColor $White
    Write-Host "  health    - Check service health" -ForegroundColor $White
    Write-Host "  cleanup   - Stop services and cleanup" -ForegroundColor $White
    Write-Host "  urls      - Show service URLs" -ForegroundColor $White
    Write-Host "  help      - Show this help" -ForegroundColor $White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor $Yellow
    Write-Host "  .\Deploy-Frontend.ps1                    # Deploy all services" -ForegroundColor $White
    Write-Host "  .\Deploy-Frontend.ps1 status             # Check status" -ForegroundColor $White
    Write-Host "  .\Deploy-Frontend.ps1 logs follow        # Follow logs" -ForegroundColor $White
    Write-Host "  .\Deploy-Frontend.ps1 stop               # Stop services" -ForegroundColor $White
    Write-Host ""
}

# Main script logic
try {
    Write-Host "🚀 VitalCore Frontend Docker Deployment" -ForegroundColor $Green
    Write-Host "========================================" -ForegroundColor $Green
    Write-Host ""

    switch ($Action.ToLower()) {
        { $_ -in @("deploy", "start") } {
            Invoke-Deployment
        }
        "stop" {
            Write-Info "Stopping services..."
            Stop-ExistingContainers
            Write-Success "Services stopped"
        }
        "restart" {
            Write-Info "Restarting services..."
            docker-compose -f $ComposeFile restart
            if (Wait-ForServices) {
                Test-ServiceHealth
                Show-ServiceUrls
            }
        }
        "status" {
            Show-ServiceStatus
        }
        "logs" {
            Show-ServiceLogs $LogAction
        }
        "health" {
            Test-ServiceHealth
        }
        "cleanup" {
            Invoke-Cleanup
        }
        "urls" {
            Show-ServiceUrls
        }
        "help" {
            Show-Help
        }
        default {
            Write-Warning "Unknown action: $Action"
            Show-Help
            exit 1
        }
    }
}
catch {
    Write-Error "Script execution failed: $($_.Exception.Message)"
    Write-Error "Stack trace: $($_.ScriptStackTrace)"
    exit 1
}

Write-Info "Script completed successfully"