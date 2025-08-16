# Healthcare System Docker Startup Script
Write-Host "🏥 STARTING HEALTHCARE SYSTEM WITH DOCKER" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

# Check if Docker is running
Write-Host "`n🐳 Checking Docker status..." -ForegroundColor Yellow
$dockerRunning = $false
try {
    $dockerVersion = docker version --format "{{.Server.Version}}" 2>$null
    if ($dockerVersion) {
        Write-Host "✅ Docker is running (Version: $dockerVersion)" -ForegroundColor Green
        $dockerRunning = $true
    }
}
catch {
    Write-Host "❌ Docker is not available" -ForegroundColor Red
}

if (-not $dockerRunning) {
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

# Stop any existing containers
Write-Host "`n🛑 Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

# Start the infrastructure services
Write-Host "`n🚀 Starting infrastructure services..." -ForegroundColor Yellow
docker-compose up -d db redis minio

# Wait for services
Write-Host "`n⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

# Check PostgreSQL
Write-Host "`n🔍 Checking PostgreSQL..." -ForegroundColor Yellow
try {
    docker exec iris_postgres pg_isready -U postgres
    Write-Host "✅ PostgreSQL is ready" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ PostgreSQL still starting..." -ForegroundColor Yellow
}

# Check Redis
Write-Host "`n🔍 Checking Redis..." -ForegroundColor Yellow
try {
    $redisCheck = docker exec iris_redis redis-cli ping 2>$null
    if ($redisCheck -eq "PONG") {
        Write-Host "✅ Redis is ready" -ForegroundColor Green
    }
}
catch {
    Write-Host "⚠️ Redis still starting..." -ForegroundColor Yellow
}

# Set environment variables
Write-Host "`n🔧 Setting up environment..." -ForegroundColor Yellow
$env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/iris_db"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:ENVIRONMENT = "development"
$env:SECRET_KEY = "your-secret-key-here"
$env:PYTHONPATH = "."

# Run migrations
Write-Host "`n🗄️ Running database migrations..." -ForegroundColor Yellow
try {
    alembic upgrade head
    Write-Host "✅ Migrations completed" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ Migration warnings (continuing)..." -ForegroundColor Yellow
}

# Start the application
Write-Host "`n🚀 Starting FastAPI application..." -ForegroundColor Green
Write-Host "Server will start on: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs available at: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Yellow

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload