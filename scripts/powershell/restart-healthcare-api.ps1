# Restart Healthcare API - Complete System Reset
# Fixes common startup issues and ensures proper service order

Write-Host "🏥 Restarting Enterprise Healthcare API" -ForegroundColor Cyan
Write-Host "=" * 40 -ForegroundColor Gray

# Step 1: Stop everything
Write-Host "`n🛑 Step 1: Stopping all services..." -ForegroundColor Yellow
docker-compose down

# Step 2: Clean up any orphaned containers
Write-Host "🧹 Step 2: Cleaning up..." -ForegroundColor Yellow
docker-compose down --remove-orphans

# Step 3: Start database first
Write-Host "`n🗄️  Step 3: Starting PostgreSQL database..." -ForegroundColor White
docker-compose up -d db

Write-Host "Waiting for database to be ready..." -ForegroundColor White
$maxWait = 60
$waited = 0

while ($waited -lt $maxWait) {
    try {
        $dbStatus = docker-compose exec -T db pg_isready -U postgres 2>$null
        if ($dbStatus -match "accepting connections") {
            Write-Host "✅ Database is ready!" -ForegroundColor Green
            break
        }
    } catch {
        # Continue waiting
    }
    
    Write-Host "." -NoNewline
    Start-Sleep 2
    $waited += 2
}

if ($waited -ge $maxWait) {
    Write-Host "`n❌ Database startup timeout!" -ForegroundColor Red
    Write-Host "Check database logs: docker-compose logs db" -ForegroundColor Yellow
    exit 1
}

# Step 4: Start Redis
Write-Host "`n🔴 Step 4: Starting Redis..." -ForegroundColor White
docker-compose up -d redis
Start-Sleep 5

# Step 5: Start the main application
Write-Host "`n🚀 Step 5: Starting Healthcare API..." -ForegroundColor White
docker-compose up -d app

Write-Host "Waiting for API to start..." -ForegroundColor White
Start-Sleep 15

# Check if app is responding
$maxAttempts = 10
$attempts = 0

while ($attempts -lt $maxAttempts) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
        if ($response.status -eq "ok") {
            Write-Host "✅ Healthcare API is responding!" -ForegroundColor Green
            break
        }
    } catch {
        # Continue trying
    }
    
    $attempts++
    Write-Host "Attempt $attempts/$maxAttempts..." -ForegroundColor White
    Start-Sleep 3
}

if ($attempts -ge $maxAttempts) {
    Write-Host "❌ API not responding. Checking logs..." -ForegroundColor Red
    docker-compose logs --tail=20 app
    Write-Host "`nTry manual restart: docker-compose restart app" -ForegroundColor Yellow
} else {
    # Step 6: Run database migrations
    Write-Host "`n📊 Step 6: Running database migrations..." -ForegroundColor White
    try {
        docker-compose exec app alembic upgrade head
        Write-Host "✅ Migrations completed!" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Migration warning: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Step 7: Start remaining services
Write-Host "`n⚙️  Step 7: Starting background services..." -ForegroundColor White
docker-compose up -d worker scheduler minio

# Step 8: Create admin user
Write-Host "`n👤 Step 8: Ensuring admin user exists..." -ForegroundColor White

$createAdminScript = @"
import sys, os
sys.path.insert(0, '.')

try:
    import asyncio
    from app.core.database_unified import get_db
    from app.modules.auth.service import AuthService
    from app.modules.auth.schemas import UserCreate
    from sqlalchemy.ext.asyncio import AsyncSession

    async def ensure_admin_user():
        try:
            # Get database session
            db_gen = get_db()
            db = await db_gen.__anext__()
            
            auth_service = AuthService()
            
            # Check if admin exists
            admin_user = await auth_service.get_user_by_username('admin', db)
            if admin_user:
                print('✅ Admin user already exists')
                return True
            
            # Create admin user
            admin_data = UserCreate(
                username='admin',
                email='admin@healthcare.local', 
                password='admin123',
                role='admin'
            )
            
            new_admin = await auth_service.create_user(admin_data, db)
            if new_admin:
                print('✅ Admin user created: admin/admin123')
                return True
            else:
                print('❌ Failed to create admin user')
                return False
                
        except Exception as e:
            print(f'❌ Error with admin user: {e}')
            return False

    # Run the function
    result = asyncio.run(ensure_admin_user())
    
except Exception as e:
    print(f'❌ Script error: {e}')
"@

try {
    $adminResult = docker-compose exec app python -c $createAdminScript
    Write-Host $adminResult
} catch {
    Write-Host "⚠️  Could not create admin user automatically" -ForegroundColor Yellow
}

# Step 9: Final status check
Write-Host "`n🏥 Step 9: Final System Status" -ForegroundColor Cyan
Write-Host "=" * 30 -ForegroundColor Gray

# Check service status
Write-Host "Service Status:" -ForegroundColor White
docker-compose ps

# Check API endpoints
Write-Host "`nAPI Health Checks:" -ForegroundColor White
$endpoints = @(
    @{ Name="Health Check"; Url="http://localhost:8000/health" },
    @{ Name="API Documentation"; Url="http://localhost:8000/docs" }
)

foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-RestMethod -Uri $endpoint.Url -TimeoutSec 5
        Write-Host "✅ $($endpoint.Name): OK" -ForegroundColor Green
    } catch {
        Write-Host "❌ $($endpoint.Name): Failed" -ForegroundColor Red
    }
}

# Test authentication
Write-Host "`nAuthentication Test:" -ForegroundColor White
try {
    $loginData = @{
        username = "admin"
        password = "admin123"
    } | ConvertTo-Json

    $authResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $loginData -ContentType "application/json" -TimeoutSec 10
    
    if ($authResponse.access_token) {
        Write-Host "✅ Authentication: Working" -ForegroundColor Green
    } else {
        Write-Host "❌ Authentication: Failed - No token" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Authentication: Failed - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎉 SYSTEM READY!" -ForegroundColor Green
Write-Host "=" * 20 -ForegroundColor Gray
Write-Host "Healthcare API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Health Check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Admin Login: admin / admin123" -ForegroundColor Yellow
Write-Host ""
Write-Host "Run tests with:" -ForegroundColor White
Write-Host "  .\test-all-fixes.ps1" -ForegroundColor Green
Write-Host "  .\validate-role-based-security.ps1" -ForegroundColor Green