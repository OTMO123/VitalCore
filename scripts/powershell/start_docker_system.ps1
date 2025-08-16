# Healthcare System Docker Startup Script
Write-Host "🏥 STARTING HEALTHCARE SYSTEM WITH DOCKER" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

# Check if Docker is running
Write-Host "`n🐳 Checking Docker status..." -ForegroundColor Yellow
try {
    $dockerVersion = docker version --format "{{.Server.Version}}" 2>$null
    if ($dockerVersion) {
        Write-Host "✅ Docker is running (Version: $dockerVersion)" -ForegroundColor Green
    } else {
        Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "❌ Docker is not available. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Stop any existing containers
Write-Host "`n🛑 Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

# Pull latest images
Write-Host "`n📥 Pulling Docker images..." -ForegroundColor Yellow
docker-compose pull

# Start the infrastructure services (database, redis, minio)
Write-Host "`n🚀 Starting infrastructure services..." -ForegroundColor Yellow
docker-compose up -d db redis minio

# Wait for services to be ready
Write-Host "`n⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Check service health
Write-Host "`n🔍 Checking service health..." -ForegroundColor Yellow

# Check PostgreSQL
try {
    $dbStatus = docker exec iris_postgres pg_isready -U postgres
    Write-Host "✅ PostgreSQL is ready" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ PostgreSQL not ready yet, waiting..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
}

# Check Redis
try {
    $redisStatus = docker exec iris_redis redis-cli ping
    if ($redisStatus -eq "PONG") {
        Write-Host "✅ Redis is ready" -ForegroundColor Green
    }
}
catch {
    Write-Host "⚠️ Redis not ready yet, waiting..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

# Run database migrations
Write-Host "`n🗄️ Running database migrations..." -ForegroundColor Yellow
try {
    # Set environment variables for database connection
    $env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/iris_db"
    $env:PYTHONPATH = "."
    
    # Run migrations
    alembic upgrade head
    Write-Host "✅ Database migrations completed" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ Migration issues - continuing anyway..." -ForegroundColor Yellow
}

# Start the FastAPI application
Write-Host "`n🚀 Starting FastAPI application..." -ForegroundColor Yellow
try {
    # Set all necessary environment variables
    $env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/iris_db"
    $env:REDIS_URL = "redis://localhost:6379/0"
    $env:ENVIRONMENT = "development"
    $env:SECRET_KEY = "your-secret-key-here"
    $env:PYTHONPATH = "."
    
    Write-Host "Starting server on http://localhost:8000..." -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
    
    # Start the application
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}
catch {
    Write-Host "❌ Failed to start FastAPI application" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    # Show container logs for debugging
    Write-Host "`n📋 Container logs:" -ForegroundColor Yellow
    docker-compose logs --tail=20
}

Write-Host "`n🏥 Healthcare System startup complete!" -ForegroundColor Green
Write-Host "Access the system at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan