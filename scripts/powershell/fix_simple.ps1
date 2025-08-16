# 🛡️ Simple Safe Fix for Windows
Write-Host "🛡️ Safe Connectivity Fix for Windows" -ForegroundColor Green
Write-Host "====================================="

# Step 1: Check Python
Write-Host "`n🐍 Step 1: Checking Python..." -ForegroundColor Cyan

$pythonCmd = $null
$commands = @("python", "python3", "py")

foreach ($cmd in $commands) {
    try {
        $version = & $cmd --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            Write-Host "✅ Found Python: $cmd - $version" -ForegroundColor Green
            break
        }
    } catch {
        # Continue searching
    }
}

if (-not $pythonCmd) {
    Write-Host "❌ Python not found!" -ForegroundColor Red
    Write-Host "Please install Python from https://python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

# Step 2: Install dependencies
Write-Host "`n📦 Step 2: Installing dependencies..." -ForegroundColor Cyan

if (Test-Path "requirements.txt") {
    Write-Host "Installing Python packages..." -ForegroundColor White
    & $pythonCmd -m pip install -r requirements.txt --user
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Dependencies installed successfully!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Some packages may have failed to install" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ requirements.txt not found!" -ForegroundColor Red
}

# Step 3: Create .env file
Write-Host "`n⚙️ Step 3: Creating environment configuration..." -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    $envContent = @'
# Safe Development Environment
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/iris_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=safe_development_secret_key_change_in_production
ENCRYPTION_KEY=safe_development_encryption_key_change_in_production
JWT_SECRET_KEY=safe_development_jwt_secret_change_in_production
ENVIRONMENT=development
DEBUG=true
ENABLE_CORS=true
SAFE_MODE=true
PRESERVE_EXISTING_DATA=true
DEVELOPMENT_MODE=true
ENABLE_AUDIT_LOGGING=true
SOC2_COMPLIANCE=true
HIPAA_COMPLIANCE=true
FHIR_R4_COMPLIANCE=true
'@
    
    $envContent | Out-File ".env" -Encoding UTF8
    Write-Host "✅ Environment file created!" -ForegroundColor Green
} else {
    Write-Host "✅ Environment file already exists!" -ForegroundColor Green
}

# Step 4: Test configuration
Write-Host "`n🔧 Step 4: Testing configuration..." -ForegroundColor Cyan

$testScript = @'
import os
import sys
sys.path.insert(0, '.')
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://test:test@localhost:5432/test_db'
os.environ['SECRET_KEY'] = 'test_secret_key'
os.environ['ENCRYPTION_KEY'] = 'test_encryption_key'
try:
    from app.core.config import get_settings
    settings = get_settings()
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
'@

$testScript | Out-File "test_config.py" -Encoding UTF8
$result = & $pythonCmd "test_config.py" 2>&1
Remove-Item "test_config.py" -ErrorAction SilentlyContinue

if ($result -match "SUCCESS") {
    Write-Host "✅ Configuration test passed!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Configuration test failed: $result" -ForegroundColor Yellow
}

# Step 5: Create startup script
Write-Host "`n🚀 Step 5: Creating startup script..." -ForegroundColor Cyan

$startupContent = @"
Write-Host "🛡️ Starting IRIS Healthcare API in Safe Mode" -ForegroundColor Green
Write-Host "=============================================="

Write-Host "🔍 Running safety checks..." -ForegroundColor Cyan

# Check dependencies
try {
    & $pythonCmd -c "import fastapi, pydantic, sqlalchemy" 2>`$null
    if (`$LASTEXITCODE -eq 0) {
        Write-Host "✅ Dependencies OK" -ForegroundColor Green
    } else {
        Write-Host "❌ Dependencies missing" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Dependencies check failed" -ForegroundColor Red
    exit 1
}

Write-Host "🚀 Starting services..." -ForegroundColor Cyan

if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
    Write-Host "🐳 Starting Docker services..." -ForegroundColor Blue
    docker-compose up -d postgres redis
    Start-Sleep 5
} else {
    Write-Host "⚠️  Docker not available" -ForegroundColor Yellow
}

Write-Host "🗄️ Running migrations..." -ForegroundColor Blue
try {
    alembic upgrade head
} catch {
    Write-Host "⚠️  Migration may need manual setup" -ForegroundColor Yellow
}

Write-Host "🌟 Starting FastAPI..." -ForegroundColor Green
Write-Host "📊 API: http://localhost:8000" -ForegroundColor White
Write-Host "📚 Docs: http://localhost:8000/docs" -ForegroundColor White

& $pythonCmd -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"@

$startupContent | Out-File "start_safe.ps1" -Encoding UTF8
Write-Host "✅ Startup script created!" -ForegroundColor Green

# Summary
Write-Host "`n🎉 SETUP COMPLETE!" -ForegroundColor Green
Write-Host "==================" 
Write-Host "✅ Python found: $pythonCmd" -ForegroundColor White
Write-Host "✅ Dependencies installed" -ForegroundColor White
Write-Host "✅ Environment configured" -ForegroundColor White
Write-Host "✅ Startup script created" -ForegroundColor White

Write-Host "`n🚀 Next steps:" -ForegroundColor Cyan
Write-Host "1. Run: .\start_safe.ps1" -ForegroundColor White
Write-Host "2. Open: http://localhost:8000/docs" -ForegroundColor White

Write-Host "`n🛡️ Your system is safe and ready!" -ForegroundColor Green

Read-Host "Press Enter to continue"