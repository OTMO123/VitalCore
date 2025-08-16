# VitalCore Quick Start Script
# Simplified deployment for Windows

param(
    [string]$Action = "start"
)

$ErrorActionPreference = "Continue"

# Configuration
$ComposeFile = "docker-compose.frontend.yml"
$FrontendPort = 5173
$BackendPort = 8000

Write-Host "🚀 VitalCore Quick Start" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Green

try {
    switch ($Action.ToLower()) {
        "start" {
            Write-Host "🔧 Starting VitalCore services..." -ForegroundColor Blue
            
            # Check if Docker is running
            try {
                docker --version | Out-Null
                Write-Host "✅ Docker is available" -ForegroundColor Green
            }
            catch {
                Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
                exit 1
            }
            
            # Check compose file
            if (-not (Test-Path $ComposeFile)) {
                Write-Host "❌ Compose file not found: $ComposeFile" -ForegroundColor Red
                exit 1
            }
            
            # Stop existing containers
            Write-Host "🛑 Stopping existing containers..." -ForegroundColor Yellow
            docker-compose -f $ComposeFile down 2>$null
            
            # Start services
            Write-Host "🚀 Starting new containers..." -ForegroundColor Blue
            docker-compose -f $ComposeFile up -d --build
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Services started successfully!" -ForegroundColor Green
                Write-Host ""
                Write-Host "🌐 Access URLs:" -ForegroundColor Yellow
                Write-Host "   Frontend: http://localhost:$FrontendPort" -ForegroundColor White
                Write-Host "   MedBrain: http://localhost:$FrontendPort/components/core/VitalCore-Production.html" -ForegroundColor White
                Write-Host "   Backend:  http://localhost:$BackendPort" -ForegroundColor White
                Write-Host "   API Docs: http://localhost:$BackendPort/docs" -ForegroundColor White
                Write-Host ""
                Write-Host "⏳ Services are starting up... Please wait 30-60 seconds for full initialization." -ForegroundColor Yellow
                Write-Host ""
                Write-Host "💡 To check status: .\Start-VitalCore.ps1 status" -ForegroundColor Blue
                Write-Host "💡 To stop services: .\Start-VitalCore.ps1 stop" -ForegroundColor Blue
                Write-Host "💡 To view logs: .\Start-VitalCore.ps1 logs" -ForegroundColor Blue
            } else {
                Write-Host "❌ Failed to start services" -ForegroundColor Red
                exit 1
            }
        }
        
        "stop" {
            Write-Host "🛑 Stopping VitalCore services..." -ForegroundColor Yellow
            docker-compose -f $ComposeFile down
            Write-Host "✅ Services stopped" -ForegroundColor Green
        }
        
        "status" {
            Write-Host "📊 Service Status:" -ForegroundColor Blue
            docker-compose -f $ComposeFile ps
        }
        
        "logs" {
            Write-Host "📋 Recent Logs:" -ForegroundColor Blue
            docker-compose -f $ComposeFile logs --tail=20
        }
        
        "restart" {
            Write-Host "🔄 Restarting VitalCore services..." -ForegroundColor Blue
            docker-compose -f $ComposeFile restart
            Write-Host "✅ Services restarted" -ForegroundColor Green
        }
        
        "clean" {
            Write-Host "🧹 Cleaning up..." -ForegroundColor Yellow
            docker-compose -f $ComposeFile down -v --remove-orphans
            docker system prune -f
            Write-Host "✅ Cleanup completed" -ForegroundColor Green
        }
        
        "test" {
            Write-Host "🧪 Testing services..." -ForegroundColor Blue
            
            # Test backend
            try {
                $response = Invoke-WebRequest "http://localhost:$BackendPort/health" -TimeoutSec 10 -ErrorAction Stop
                Write-Host "✅ Backend API: OK" -ForegroundColor Green
            }
            catch {
                Write-Host "❌ Backend API: Failed" -ForegroundColor Red
            }
            
            # Test frontend
            try {
                $response = Invoke-WebRequest "http://localhost:$FrontendPort" -TimeoutSec 10 -ErrorAction Stop
                Write-Host "✅ Frontend: OK" -ForegroundColor Green
            }
            catch {
                Write-Host "❌ Frontend: Failed" -ForegroundColor Red
            }
        }
        
        default {
            Write-Host "Usage: .\Start-VitalCore.ps1 [action]" -ForegroundColor White
            Write-Host ""
            Write-Host "Actions:" -ForegroundColor Yellow
            Write-Host "  start    - Start all services (default)" -ForegroundColor White
            Write-Host "  stop     - Stop all services" -ForegroundColor White
            Write-Host "  restart  - Restart all services" -ForegroundColor White
            Write-Host "  status   - Show service status" -ForegroundColor White
            Write-Host "  logs     - Show recent logs" -ForegroundColor White
            Write-Host "  test     - Test service connectivity" -ForegroundColor White
            Write-Host "  clean    - Stop and cleanup all containers" -ForegroundColor White
        }
    }
}
catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}