# VitalCore Quick Start - No Build Version
param([string]$action = "start")

Write-Host "VitalCore Quick Start" -ForegroundColor Green
Write-Host "====================" -ForegroundColor Green

switch ($action) {
    "start" {
        Write-Host "Starting VitalCore services..." -ForegroundColor Blue
        
        # Stop any existing containers
        docker-compose -f docker-compose.yml down 2>$null
        
        # Start basic services without frontend build
        Write-Host "Starting database and backend services..." -ForegroundColor Yellow
        docker-compose -f docker-compose.yml up -d
        
        Write-Host ""
        Write-Host "Services Starting:" -ForegroundColor Green
        Write-Host "  Database: PostgreSQL on port 5432" -ForegroundColor White
        Write-Host "  Backend:  FastAPI on port 8000" -ForegroundColor White  
        Write-Host "  Redis:    Cache on port 6379" -ForegroundColor White
        Write-Host "  MinIO:    Storage on ports 9000/9001" -ForegroundColor White
        Write-Host ""
        Write-Host "Access URLs:" -ForegroundColor Yellow
        Write-Host "  Backend API: http://localhost:8000" -ForegroundColor White
        Write-Host "  API Docs:    http://localhost:8000/docs" -ForegroundColor White
        Write-Host "  MinIO:       http://localhost:9001 (minioadmin/minio123secure)" -ForegroundColor White
        Write-Host ""
        Write-Host "Wait 30-60 seconds for all services to initialize..." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "For frontend, use: python start_frontend_fixed.py" -ForegroundColor Cyan
    }
    
    "frontend" {
        Write-Host "Starting frontend server..." -ForegroundColor Blue
        if (Test-Path "start_frontend_fixed.py") {
            python start_frontend_fixed.py
        } elseif (Test-Path "frontend") {
            Set-Location frontend
            if (Test-Path "package.json") {
                npm run dev
            } else {
                Write-Host "No package.json found in frontend directory" -ForegroundColor Red
            }
        } else {
            Write-Host "Frontend files not found" -ForegroundColor Red
        }
    }
    
    "stop" {
        Write-Host "Stopping VitalCore..." -ForegroundColor Red
        docker-compose -f docker-compose.yml down
        Write-Host "Services stopped" -ForegroundColor Green
    }
    
    "status" {
        Write-Host "Service Status:" -ForegroundColor Blue
        docker-compose -f docker-compose.yml ps
    }
    
    "logs" {
        Write-Host "Recent Logs:" -ForegroundColor Blue
        docker-compose -f docker-compose.yml logs --tail=20
    }
    
    "test" {
        Write-Host "Testing backend connection..." -ForegroundColor Blue
        try {
            $response = Invoke-WebRequest "http://localhost:8000/health" -TimeoutSec 10 -ErrorAction Stop
            Write-Host "Backend API: OK" -ForegroundColor Green
            Write-Host "Response: $($response.Content)" -ForegroundColor Gray
        }
        catch {
            Write-Host "Backend API: Not Ready" -ForegroundColor Yellow
            Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    default {
        Write-Host "VitalCore Management Commands:" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Usage: .\QuickStart.ps1 [action]" -ForegroundColor White
        Write-Host ""
        Write-Host "Actions:" -ForegroundColor Yellow
        Write-Host "  start     - Start backend services" -ForegroundColor White
        Write-Host "  frontend  - Start frontend server" -ForegroundColor White
        Write-Host "  stop      - Stop all services" -ForegroundColor White
        Write-Host "  status    - Show service status" -ForegroundColor White
        Write-Host "  logs      - Show recent logs" -ForegroundColor White
        Write-Host "  test      - Test backend connection" -ForegroundColor White
        Write-Host ""
        Write-Host "Quick Start Guide:" -ForegroundColor Cyan
        Write-Host "1. .\QuickStart.ps1 start      # Start backend" -ForegroundColor White
        Write-Host "2. .\QuickStart.ps1 test       # Test backend" -ForegroundColor White
        Write-Host "3. .\QuickStart.ps1 frontend   # Start frontend" -ForegroundColor White
    }
}