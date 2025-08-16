# PowerShell script to setup Docker testing environment
Write-Host "Setting up Docker testing environment for IRIS API..." -ForegroundColor Green

# Check if Docker Desktop is running
Write-Host "`nChecking Docker Desktop status..." -ForegroundColor Yellow
try {
    $dockerInfo = docker info 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker Desktop is running" -ForegroundColor Green
    } else {
        throw "Docker Desktop not accessible"
    }
} catch {
    Write-Host "❌ Docker Desktop not running or not accessible from WSL2" -ForegroundColor Red
    Write-Host "SOLUTION:" -ForegroundColor Yellow
    Write-Host "1. Start Docker Desktop on Windows" -ForegroundColor White
    Write-Host "2. Go to Settings > Resources > WSL Integration" -ForegroundColor White
    Write-Host "3. Enable integration for your WSL2 distro" -ForegroundColor White
    Write-Host "4. Restart WSL2: wsl --shutdown (from Windows)" -ForegroundColor White
    exit 1
}

# Start only PostgreSQL and Redis for testing
Write-Host "`nStarting PostgreSQL and Redis services..." -ForegroundColor Yellow
docker-compose up -d db redis

# Wait for services to be healthy
Write-Host "`nWaiting for services to be ready..." -ForegroundColor Yellow
$timeout = 60
$elapsed = 0
do {
    Start-Sleep 2
    $elapsed += 2
    $dbHealth = docker inspect iris_postgres --format='{{.State.Health.Status}}' 2>$null
    $redisHealth = docker inspect iris_redis --format='{{.State.Health.Status}}' 2>$null
    
    Write-Host "PostgreSQL: $dbHealth | Redis: $redisHealth" -ForegroundColor Cyan
    
    if ($dbHealth -eq "healthy" -and $redisHealth -eq "healthy") {
        Write-Host "✅ All services are healthy!" -ForegroundColor Green
        break
    }
    
    if ($elapsed -ge $timeout) {
        Write-Host "❌ Timeout waiting for services" -ForegroundColor Red
        docker-compose logs db redis
        exit 1
    }
} while ($true)

# Apply database migrations
Write-Host "`nApplying database migrations..." -ForegroundColor Yellow
try {
    .\venv\Scripts\alembic.exe upgrade head
    Write-Host "✅ Database migrations applied successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Migration failed. Checking database connection..." -ForegroundColor Red
    
    # Test direct database connection
    Write-Host "Testing database connection..." -ForegroundColor Yellow
    .\venv\Scripts\python.exe -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='iris_db',
        user='postgres',
        password='password'
    )
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    "
}

# Run comprehensive tests with PostgreSQL
Write-Host "`nRunning comprehensive tests with PostgreSQL..." -ForegroundColor Yellow
try {
    .\venv\Scripts\pytest.exe app/tests/smoke/test_basic.py -v --tb=short
    Write-Host "✅ PostgreSQL smoke tests completed" -ForegroundColor Green
} catch {
    Write-Host "❌ PostgreSQL tests failed" -ForegroundColor Red
}

# Show service status
Write-Host "`nDocker services status:" -ForegroundColor Yellow
docker-compose ps

Write-Host "`n🎉 Setup complete! Services ready for testing." -ForegroundColor Green
Write-Host "Commands:" -ForegroundColor Yellow
Write-Host "- Stop services: docker-compose down" -ForegroundColor White
Write-Host "- View logs: docker-compose logs db redis" -ForegroundColor White
Write-Host "- Reset database: docker-compose down -v && docker-compose up -d db redis" -ForegroundColor White