# VitalCore Docker Start Script - Simple version
param([string]$cmd = "start")

$compose = "docker-compose.frontend.yml"

switch ($cmd) {
    "start" {
        Write-Host "Starting VitalCore..." -ForegroundColor Green
        docker-compose -f $compose down 2>$null
        docker-compose -f $compose up -d --build
        
        Write-Host ""
        Write-Host "URLs:" -ForegroundColor Yellow
        Write-Host "  Frontend: http://localhost:5173"
        Write-Host "  MedBrain: http://localhost:5173/components/core/VitalCore-Production.html"
        Write-Host "  Backend:  http://localhost:8000"
        Write-Host "  API Docs: http://localhost:8000/docs"
        Write-Host ""
        Write-Host "Wait 30-60 seconds for services to start..." -ForegroundColor Yellow
    }
    "stop" {
        Write-Host "Stopping VitalCore..." -ForegroundColor Red
        docker-compose -f $compose down
    }
    "status" {
        docker-compose -f $compose ps
    }
    "logs" {
        docker-compose -f $compose logs --tail=20
    }
    default {
        Write-Host "Usage: .\Start-Docker.ps1 [start|stop|status|logs]"
    }
}

Write-Host "Enterprise Healthcare API - Docker Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Gray

if ($Status) {
    Write-Host "Checking service status..." -ForegroundColor Yellow
    docker-compose ps
    exit 0
}

if ($Logs) {
    Write-Host "Showing container logs..." -ForegroundColor Yellow
    docker-compose logs --tail=50 -f
    exit 0
}

if ($Clean) {
    Write-Host "Performing clean rebuild..." -ForegroundColor Yellow
    Write-Host "WARNING: This will remove all data!" -ForegroundColor Red
    $confirm = Read-Host "Continue? (y/N)"
    if ($confirm -eq "y" -or $confirm -eq "Y") {
        docker-compose down -v --remove-orphans
        docker system prune -f
        Write-Host "Clean completed" -ForegroundColor Green
    } else {
        Write-Host "Clean cancelled" -ForegroundColor Yellow
        exit 0
    }
}

# Start services
Write-Host "Starting healthcare services..." -ForegroundColor Yellow

try {
    # Start database first
    Write-Host "Starting PostgreSQL database..." -ForegroundColor White
    docker-compose up -d db
    
    # Wait for database
    Write-Host "Waiting for database to be ready..." -ForegroundColor White
    $maxWait = 30
    $waited = 0
    
    while ($waited -lt $maxWait) {
        $dbStatus = docker-compose exec -T db pg_isready -U postgres 2>$null
        if ($dbStatus -match "accepting connections") {
            Write-Host "Database is ready!" -ForegroundColor Green
            break
        }
        Write-Host "." -NoNewline
        Start-Sleep 2
        $waited += 2
    }
    
    if ($waited -ge $maxWait) {
        Write-Host "`nDatabase startup timeout!" -ForegroundColor Red
        exit 1
    }
    
    # Start Redis
    Write-Host "`nStarting Redis..." -ForegroundColor White
    docker-compose up -d redis
    
    # Start remaining services
    Write-Host "Starting remaining services..." -ForegroundColor White
    docker-compose up -d
    
    # Run database migrations
    Write-Host "Running database migrations..." -ForegroundColor White
    Start-Sleep 5  # Give app time to start
    docker-compose exec app alembic upgrade head
    
    Write-Host "`nServices started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "ENDPOINTS:" -ForegroundColor Cyan
    Write-Host "  Healthcare API:     http://localhost:8000" -ForegroundColor White
    Write-Host "  API Documentation:  http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  Health Check:       http://localhost:8000/health" -ForegroundColor White
    Write-Host "  MinIO Console:      http://localhost:9001" -ForegroundColor White
    Write-Host ""
    Write-Host "DATABASE:" -ForegroundColor Cyan
    Write-Host "  Host: localhost:5432" -ForegroundColor White
    Write-Host "  Database: iris_db" -ForegroundColor White
    Write-Host "  User: postgres" -ForegroundColor White
    Write-Host "  Password: password" -ForegroundColor White
    Write-Host ""
    Write-Host "USEFUL COMMANDS:" -ForegroundColor Cyan
    Write-Host "  View logs:    docker-compose logs -f" -ForegroundColor White
    Write-Host "  Check status: .\start-docker.ps1 -Status" -ForegroundColor White
    Write-Host "  Stop all:     docker-compose down" -ForegroundColor White
    Write-Host ""
    Write-Host "Run tests with: .\test-all-fixes.ps1" -ForegroundColor Yellow
    
} catch {
    Write-Host "`nSetup failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Check Docker is running and try again." -ForegroundColor Yellow
    exit 1
}