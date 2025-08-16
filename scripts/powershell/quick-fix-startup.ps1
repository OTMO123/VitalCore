# Quick Fix for Healthcare API Startup Issues
# Simple script compatible with all PowerShell versions

Write-Host "Healthcare API Quick Fix" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Gray

# Step 1: Stop everything cleanly
Write-Host "`nStep 1: Stopping all services..." -ForegroundColor Yellow
docker-compose down --remove-orphans

# Step 2: Start database first and wait
Write-Host "`nStep 2: Starting database..." -ForegroundColor White
docker-compose up -d db

Write-Host "Waiting for database (60 seconds max)..." -ForegroundColor White
$count = 0
while ($count -lt 30) {
    try {
        $result = docker-compose exec -T db pg_isready -U postgres 2>$null
        if ($result -like "*accepting connections*") {
            Write-Host "Database ready!" -ForegroundColor Green
            break
        }
    } catch {
        # Continue waiting
    }
    Write-Host "." -NoNewline
    Start-Sleep 2
    $count++
}

if ($count -ge 30) {
    Write-Host "`nDatabase timeout! Check logs:" -ForegroundColor Red
    docker-compose logs db
    exit 1
}

# Step 3: Start Redis
Write-Host "`nStep 3: Starting Redis..." -ForegroundColor White
docker-compose up -d redis
Start-Sleep 3

# Step 4: Start main app
Write-Host "`nStep 4: Starting main application..." -ForegroundColor White
docker-compose up -d app

Write-Host "Waiting for app to start..." -ForegroundColor White
Start-Sleep 15

# Step 5: Check if app is working
Write-Host "`nStep 5: Testing API health..." -ForegroundColor White
$attempts = 0
$maxAttempts = 5

while ($attempts -lt $maxAttempts) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 10
        if ($response.status -eq "ok") {
            Write-Host "API is healthy!" -ForegroundColor Green
            break
        }
    } catch {
        Write-Host "Attempt $($attempts + 1) failed, retrying..." -ForegroundColor Yellow
    }
    $attempts++
    Start-Sleep 5
}

if ($attempts -ge $maxAttempts) {
    Write-Host "API health check failed. Checking logs..." -ForegroundColor Red
    Write-Host "Last 20 lines from app:" -ForegroundColor Yellow
    docker-compose logs --tail=20 app
    Write-Host "`nTry manual restart: docker-compose restart app" -ForegroundColor Yellow
} else {
    # Step 6: Run migrations
    Write-Host "`nStep 6: Running database migrations..." -ForegroundColor White
    docker-compose exec app alembic upgrade head
    
    # Step 7: Create admin user
    Write-Host "`nStep 7: Creating admin user..." -ForegroundColor White
    
    $pythonScript = "import sys; sys.path.insert(0, '.'); "
    $pythonScript += "import asyncio; "
    $pythonScript += "from app.core.database_unified import get_db; "
    $pythonScript += "from app.modules.auth.service import AuthService; "
    $pythonScript += "from app.modules.auth.schemas import UserCreate; "
    $pythonScript += "async def create_admin(): "
    $pythonScript += "    db_gen = get_db(); db = await db_gen.__anext__(); "
    $pythonScript += "    auth_service = AuthService(); "
    $pythonScript += "    existing = await auth_service.get_user_by_username('admin', db); "
    $pythonScript += "    if existing: print('Admin exists'); return True; "
    $pythonScript += "    admin_data = UserCreate(username='admin', email='admin@test.com', password='admin123', role='admin'); "
    $pythonScript += "    user = await auth_service.create_user(admin_data, db); "
    $pythonScript += "    print('Admin created!' if user else 'Failed!'); "
    $pythonScript += "asyncio.run(create_admin())"
    
    docker-compose exec app python -c $pythonScript
    
    # Step 8: Start remaining services
    Write-Host "`nStep 8: Starting remaining services..." -ForegroundColor White
    docker-compose up -d
    
    # Step 9: Final test
    Write-Host "`nStep 9: Final authentication test..." -ForegroundColor White
    try {
        $loginData = '{"username": "admin", "password": "admin123"}'
        $authResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $loginData -ContentType "application/json" -TimeoutSec 10
        
        if ($authResponse.access_token) {
            Write-Host "SUCCESS! Authentication working!" -ForegroundColor Green
            Write-Host ""
            Write-Host "SYSTEM READY:" -ForegroundColor Cyan
            Write-Host "  API: http://localhost:8000" -ForegroundColor White
            Write-Host "  Docs: http://localhost:8000/docs" -ForegroundColor White
            Write-Host "  Health: http://localhost:8000/health" -ForegroundColor White
            Write-Host "  Login: admin / admin123" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Run tests with: .\test-all-fixes.ps1" -ForegroundColor Green
        } else {
            Write-Host "Authentication failed - no token received" -ForegroundColor Red
        }
    } catch {
        Write-Host "Authentication test failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "But API might still work. Try: .\test-all-fixes.ps1" -ForegroundColor Yellow
    }
}

Write-Host "`nService Status:" -ForegroundColor White
docker-compose ps