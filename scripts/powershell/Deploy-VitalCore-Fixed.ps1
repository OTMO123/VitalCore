# VitalCore Frontend Docker Deployment Script - Fixed Version
# Comprehensive deployment for frontend + backend integration

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

# Colors
function Write-Info { param([string]$Message); Write-Host "[INFO] $Message" -ForegroundColor Blue }
function Write-Success { param([string]$Message); Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message); Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error { param([string]$Message); Write-Host "[ERROR] $Message" -ForegroundColor Red }

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    try {
        $null = docker --version
        Write-Success "Docker is installed"
    }
    catch {
        Write-Error "Docker is not installed or not in PATH"
        return $false
    }
    
    try {
        $null = docker-compose --version
        Write-Success "Docker Compose is installed"
    }
    catch {
        Write-Error "Docker Compose is not installed"
        return $false
    }
    
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
        $runningContainers = docker-compose -f $ComposeFile ps -q 2>$null
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

# Start services
function Start-Services {
    Write-Info "Building and starting services..."
    
    try {
        Write-Info "Building Docker images..."
        docker-compose -f $ComposeFile build --no-cache
        
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

# Wait for services
function Wait-ForServices {
    Write-Info "Waiting for services to be ready..."
    $timeout = 60
    
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

# Show service URLs
function Show-ServiceUrls {
    Write-Info "Service URLs:"
    Write-Host "==============" -ForegroundColor White
    Write-Host "🏥 VitalCore Frontend:     http://localhost:$FrontendPort" -ForegroundColor Green
    Write-Host "🩺 Production Frontend:    http://localhost:$FrontendPort/components/core/VitalCore-Production.html" -ForegroundColor Green
    Write-Host "🧠 MedBrain Enhanced:      http://localhost:$FrontendPort/components/core/MedBrain-Enhanced.html" -ForegroundColor Green
    Write-Host "🔧 Backend API:            http://localhost:$BackendPort" -ForegroundColor Blue
    Write-Host "📚 API Documentation:     http://localhost:$BackendPort/docs" -ForegroundColor Blue
    Write-Host "🗄️  MinIO Console:         http://localhost:9001" -ForegroundColor Yellow
    Write-Host ""
}

# Show service status
function Show-ServiceStatus {
    Write-Info "Service Status:"
    Write-Host "===============" -ForegroundColor White
    try {
        docker-compose -f $ComposeFile ps
    }
    catch {
        Write-Error "Failed to get service status"
    }
    Write-Host ""
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
    
    Write-Success "🎉 VitalCore deployment completed successfully!"
    Write-Host ""
    
    Show-ServiceUrls
    Show-ServiceStatus
    
    Write-Info "🧪 Test the enhanced MedBrain with voice recognition!"
    Write-Info "Visit: http://localhost:$FrontendPort/components/core/VitalCore-Production.html"
}

# Main script logic
Write-Host "🚀 VitalCore Frontend Docker Deployment" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

try {
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
                Show-ServiceUrls
            }
        }
        "status" {
            Show-ServiceStatus
        }
        "logs" {
            if ($LogAction -eq "follow") {
                Write-Info "Following logs (Ctrl+C to stop)..."
                docker-compose -f $ComposeFile logs -f
            } else {
                Write-Info "Recent logs:"
                docker-compose -f $ComposeFile logs --tail=20
            }
        }
        "cleanup" {
            Write-Info "Cleaning up..."
            docker-compose -f $ComposeFile down -v --remove-orphans
            docker system prune -f
            Write-Success "Cleanup completed"
        }
        "urls" {
            Show-ServiceUrls
        }
        default {
            Write-Host "Usage: .\Deploy-VitalCore-Fixed.ps1 [action]" -ForegroundColor White
            Write-Host ""
            Write-Host "Actions:" -ForegroundColor Yellow
            Write-Host "  deploy    - Deploy all services (default)" -ForegroundColor White
            Write-Host "  start     - Same as deploy" -ForegroundColor White
            Write-Host "  stop      - Stop all services" -ForegroundColor White
            Write-Host "  restart   - Restart all services" -ForegroundColor White
            Write-Host "  status    - Show service status" -ForegroundColor White
            Write-Host "  logs      - Show recent logs" -ForegroundColor White
            Write-Host "  cleanup   - Stop and cleanup" -ForegroundColor White
            Write-Host "  urls      - Show service URLs" -ForegroundColor White
        }
    }
}
catch {
    Write-Error "Script execution failed: $($_.Exception.Message)"
    exit 1
}

Write-Info "Script completed successfully"