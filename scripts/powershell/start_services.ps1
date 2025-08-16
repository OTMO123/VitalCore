# IRIS API Service Startup Script
# This script starts all required services and the FastAPI application

Write-Host "🚀 IRIS API Integration System - Service Startup" -ForegroundColor Green
Write-Host "=" * 60

# Step 1: Start Docker services
Write-Host "`n1. Starting Docker services..." -ForegroundColor Yellow
Write-Host "Starting PostgreSQL and Redis containers..."

try {
    docker-compose up -d db redis
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker services started successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to start Docker services" -ForegroundColor Red
        Write-Host "Please ensure Docker Desktop is running" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Docker not available or failed to start services" -ForegroundColor Red
    Write-Host "Please ensure Docker Desktop is installed and running" -ForegroundColor Yellow
    exit 1
}

# Step 2: Wait for services to be ready
Write-Host "`n2. Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Step 3: Test database connectivity
Write-Host "`n3. Testing database connectivity..." -ForegroundColor Yellow

try {
    python start_app.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Pre-flight checks passed!" -ForegroundColor Green
    } else {
        Write-Host "❌ Pre-flight checks failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Failed to run pre-flight checks" -ForegroundColor Red
    exit 1
}

# Step 4: Start the FastAPI application
Write-Host "`n4. Starting FastAPI application..." -ForegroundColor Yellow
Write-Host "🌐 Server will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "🏥 Health Check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Yellow

try {
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
} catch {
    Write-Host "`n❌ Server stopped or failed to start" -ForegroundColor Red
}

Write-Host "`n🛑 Stopping services..." -ForegroundColor Yellow
# docker-compose down