# VitalCore Simple Start Script
param([string]$action = "start")

$compose = "docker-compose.frontend.yml"

switch ($action) {
    "start" {
        Write-Host "Starting VitalCore..." -ForegroundColor Green
        docker-compose -f $compose down 2>$null
        docker-compose -f $compose up -d --build
        
        Write-Host ""
        Write-Host "Access URLs:" -ForegroundColor Yellow
        Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
        Write-Host "  MedBrain: http://localhost:5173/components/core/VitalCore-Production.html" -ForegroundColor White
        Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
        Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
        Write-Host ""
        Write-Host "Please wait 30-60 seconds for all services to start..." -ForegroundColor Yellow
    }
    "stop" {
        Write-Host "Stopping VitalCore..." -ForegroundColor Red
        docker-compose -f $compose down
        Write-Host "Services stopped." -ForegroundColor Green
    }
    "status" {
        Write-Host "Service Status:" -ForegroundColor Blue
        docker-compose -f $compose ps
    }
    "logs" {
        Write-Host "Recent Logs:" -ForegroundColor Blue
        docker-compose -f $compose logs --tail=30
    }
    "clean" {
        Write-Host "Cleaning up containers and volumes..." -ForegroundColor Yellow
        docker-compose -f $compose down -v --remove-orphans
        docker system prune -f
        Write-Host "Cleanup completed." -ForegroundColor Green
    }
    default {
        Write-Host "VitalCore Docker Management" -ForegroundColor Cyan
        Write-Host "==========================" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Usage: .\StartVitalCore.ps1 [action]" -ForegroundColor White
        Write-Host ""
        Write-Host "Actions:" -ForegroundColor Yellow
        Write-Host "  start   - Start all services (default)" -ForegroundColor White
        Write-Host "  stop    - Stop all services" -ForegroundColor White
        Write-Host "  status  - Show service status" -ForegroundColor White
        Write-Host "  logs    - Show recent logs" -ForegroundColor White
        Write-Host "  clean   - Remove all containers and data" -ForegroundColor White
    }
}