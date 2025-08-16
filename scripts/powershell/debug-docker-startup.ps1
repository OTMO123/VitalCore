# Debug Docker Startup Issues
# Comprehensive diagnostic script for healthcare API startup problems

Write-Host "🔍 Docker Startup Diagnostics" -ForegroundColor Cyan
Write-Host "=" * 40 -ForegroundColor Gray

function Test-DockerService {
    param([string]$ServiceName)
    Write-Host "`n[CHECK] $ServiceName Service" -ForegroundColor White
    
    try {
        $containerStatus = docker-compose ps $ServiceName
        if ($containerStatus -match "Up") {
            Write-Host "  ✅ $ServiceName is running" -ForegroundColor Green
            return $true
        } else {
            Write-Host "  ❌ $ServiceName is not running" -ForegroundColor Red
            Write-Host "  Status: $containerStatus" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "  ❌ Error checking $ServiceName`: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Show-ServiceLogs {
    param([string]$ServiceName, [int]$Lines = 20)
    Write-Host "`n[LOGS] Last $Lines lines from $ServiceName" -ForegroundColor Yellow
    Write-Host "-" * 50 -ForegroundColor Gray
    docker-compose logs --tail=$Lines $ServiceName
    Write-Host "-" * 50 -ForegroundColor Gray
}

# Step 1: Check Docker is running
Write-Host "`n🐳 Step 1: Docker System Check" -ForegroundColor Cyan
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker: $dockerVersion" -ForegroundColor Green
    
    $composeVersion = docker-compose --version  
    Write-Host "✅ Docker Compose: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not running or not installed!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

# Step 2: Check current service status
Write-Host "`n🔍 Step 2: Service Status Check" -ForegroundColor Cyan
docker-compose ps

# Step 3: Check individual services
Write-Host "`n🧪 Step 3: Individual Service Health" -ForegroundColor Cyan
$services = @("db", "redis", "app", "worker", "minio")
$runningServices = @()
$failedServices = @()

foreach ($service in $services) {
    if (Test-DockerService $service) {
        $runningServices += $service
    } else {
        $failedServices += $service
    }
}

# Step 4: Start missing services
if ($failedServices.Count -gt 0) {
    Write-Host "`n🚀 Step 4: Starting Failed Services" -ForegroundColor Cyan
    
    foreach ($service in $failedServices) {
        Write-Host "Starting $service..." -ForegroundColor Yellow
        
        if ($service -eq "db") {
            # Database needs special handling
            docker-compose up -d db
            Write-Host "Waiting for database to initialize..." -ForegroundColor White
            
            $maxWait = 60
            $waited = 0
            while ($waited -lt $maxWait) {
                $dbReady = docker-compose exec -T db pg_isready -U postgres 2>$null
                if ($dbReady -match "accepting connections") {
                    Write-Host "✅ Database is ready!" -ForegroundColor Green
                    break
                }
                Write-Host "." -NoNewline
                Start-Sleep 2
                $waited += 2
            }
            
            if ($waited -ge $maxWait) {
                Write-Host "`n❌ Database failed to start!" -ForegroundColor Red
                Show-ServiceLogs "db"
                continue
            }
        } elseif ($service -eq "app") {
            # App service - most critical
            docker-compose up -d app
            Write-Host "Waiting for app to start..." -ForegroundColor White
            Start-Sleep 10
            
            # Check if app is healthy
            try {
                $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
                if ($response.status -eq "ok") {
                    Write-Host "✅ App is healthy!" -ForegroundColor Green
                } else {
                    Write-Host "⚠️  App started but health check failed" -ForegroundColor Yellow
                    Show-ServiceLogs "app"
                }
            } catch {
                Write-Host "❌ App health check failed: $($_.Exception.Message)" -ForegroundColor Red
                Show-ServiceLogs "app"
            }
        } else {
            # Other services
            docker-compose up -d $service
            Start-Sleep 3
        }
    }
} else {
    Write-Host "✅ All services are running!" -ForegroundColor Green
}

# Step 5: Database migration check
Write-Host "`n📊 Step 5: Database Migration Check" -ForegroundColor Cyan
if ("app" -in $runningServices -or "app" -in $failedServices) {
    try {
        Write-Host "Checking database migrations..." -ForegroundColor White
        $migrationResult = docker-compose exec app alembic current 2>&1
        
        if ($migrationResult -match "ERROR" -or $migrationResult -match "FAILED") {
            Write-Host "❌ Migration check failed" -ForegroundColor Red
            Write-Host "Running migrations..." -ForegroundColor Yellow
            docker-compose exec app alembic upgrade head
        } else {
            Write-Host "✅ Migrations are current" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️  Could not check migrations: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Step 6: Create test user for authentication
Write-Host "`n👤 Step 6: Test User Creation" -ForegroundColor Cyan
try {
    Write-Host "Creating test admin user..." -ForegroundColor White
    
    $createUserScript = @"
import sys
sys.path.insert(0, '.')
import asyncio
from app.core.database_unified import get_db
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import UserCreate

async def create_test_user():
    try:
        db_gen = get_db()
        db = await db_gen.__anext__()
        
        auth_service = AuthService()
        
        # Check if admin user exists
        existing_user = await auth_service.get_user_by_username('admin', db)
        if existing_user:
            print('✅ Admin user already exists')
            return True
            
        # Create admin user
        user_data = UserCreate(
            username='admin',
            email='admin@healthcare.local',
            password='admin123',
            role='admin'
        )
        
        user = await auth_service.create_user(user_data, db)
        if user:
            print('✅ Admin user created successfully')
            return True
        else:
            print('❌ Failed to create admin user')
            return False
            
    except Exception as e:
        print(f'❌ Error creating user: {e}')
        return False

result = asyncio.run(create_test_user())
"@
    
    $result = docker-compose exec app python -c $createUserScript
    Write-Host $result
    
} catch {
    Write-Host "⚠️  Could not create test user: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Step 7: Final health check
Write-Host "`n🏥 Step 7: Final System Health Check" -ForegroundColor Cyan

$healthChecks = @(
    @{ Name="API Health"; Url="http://localhost:8000/health" },
    @{ Name="API Docs"; Url="http://localhost:8000/docs" },
    @{ Name="Database Status"; Url="http://localhost:8000/health/detailed" }
)

foreach ($check in $healthChecks) {
    try {
        $response = Invoke-RestMethod -Uri $check.Url -TimeoutSec 5
        Write-Host "✅ $($check.Name): OK" -ForegroundColor Green
    } catch {
        Write-Host "❌ $($check.Name): Failed - $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Step 8: Test authentication
Write-Host "`n🔐 Step 8: Authentication Test" -ForegroundColor Cyan
try {
    $loginData = @{
        username = "admin"
        password = "admin123"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $loginData -ContentType "application/json" -TimeoutSec 10
    
    if ($response.access_token) {
        Write-Host "✅ Authentication working! Token received." -ForegroundColor Green
        Write-Host "🎉 System is ready for testing!" -ForegroundColor Green
    } else {
        Write-Host "❌ Authentication failed - no token received" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Authentication test failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "You may need to create users manually or check the auth service." -ForegroundColor Yellow
}

# Summary
Write-Host "`n📋 DIAGNOSTIC SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 40 -ForegroundColor Gray
Write-Host "Running Services: $($runningServices -join ', ')" -ForegroundColor Green
if ($failedServices.Count -gt 0) {
    Write-Host "Failed Services: $($failedServices -join ', ')" -ForegroundColor Red
}

Write-Host "`n🚀 NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. If services are running, try: .\test-all-fixes.ps1" -ForegroundColor White
Write-Host "2. If authentication works, try: .\validate-role-based-security.ps1" -ForegroundColor White  
Write-Host "3. If issues persist, check logs: docker-compose logs -f app" -ForegroundColor White
Write-Host "4. For clean restart: docker-compose down && docker-compose up -d" -ForegroundColor White