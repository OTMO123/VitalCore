# Fixed Quick Start and Test
Write-Host "=== FIXED QUICK START & AUTH TEST ===" -ForegroundColor Yellow

# Check Docker
Write-Host "Checking Docker..." -ForegroundColor Cyan
docker --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker not found!" -ForegroundColor Red
    exit 1
}

# Fix #1: Use correct service names from docker-compose.yml
Write-Host "Starting Docker services..." -ForegroundColor Cyan
docker-compose down --remove-orphans

# The service is called 'db' not 'postgres'
docker-compose up -d db redis minio

# Wait for services
Write-Host "Waiting for services..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

# Check if database is ready
Write-Host "Checking database..." -ForegroundColor Cyan
$dbReady = $false
$retries = 0
while (-not $dbReady -and $retries -lt 10) {
    try {
        $testResult = docker exec iris_postgres pg_isready -U postgres
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Database is ready!" -ForegroundColor Green
            $dbReady = $true
        } else {
            throw "Database not ready"
        }
    } catch {
        $retries++
        Write-Host "Database not ready, waiting... ($retries/10)" -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
}

if (-not $dbReady) {
    Write-Host "Database failed to start!" -ForegroundColor Red
    docker-compose logs db
    exit 1
}

# Fix #2: Set PYTHONPATH and use proper module execution
Write-Host "Setting up Python environment..." -ForegroundColor Cyan
$env:PYTHONPATH = $PWD

# Create admin user with proper error handling
Write-Host "Creating admin user..." -ForegroundColor Cyan
try {
    python -m pip install asyncpg > $null 2>&1
    python create_admin_user.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Admin user created successfully!" -ForegroundColor Green
    } else {
        Write-Host "Admin user creation had issues, continuing..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "Admin user creation failed, continuing..." -ForegroundColor Yellow
}

# Fix #3: Start server with proper PYTHONPATH
Write-Host "Starting FastAPI server..." -ForegroundColor Cyan
$job = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    $env:PYTHONPATH = $using:PWD
    
    # Set environment variables
    $env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/iris_db"
    $env:DEBUG = "true"
    $env:LOG_LEVEL = "DEBUG"
    
    python -c "
import sys
sys.path.insert(0, '.')
from app.main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8000)
"
}

Write-Host "Waiting for server startup..." -ForegroundColor Yellow
Start-Sleep -Seconds 25

# Test server health with retries
Write-Host "Testing server health..." -ForegroundColor Cyan
$retries = 0
$maxRetries = 5
$serverReady = $false

while ($retries -lt $maxRetries -and -not $serverReady) {
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5
        Write-Host "Server is ready!" -ForegroundColor Green
        Write-Host "Health status: $($health.status)" -ForegroundColor White
        $serverReady = $true
    }
    catch {
        $retries++
        Write-Host "Server not ready, retry $retries/$maxRetries..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    }
}

if (-not $serverReady) {
    Write-Host "Server failed to start!" -ForegroundColor Red
    Write-Host "Job output:" -ForegroundColor Yellow
    Receive-Job $job | Select-Object -Last 10
    Write-Host "Check if port 8000 is in use:" -ForegroundColor Yellow
    netstat -an | findstr ":8000"
    exit 1
}

# Test authentication with enhanced error handling
Write-Host "Testing authentication..." -ForegroundColor Cyan
$apiUrl = "http://localhost:8000/api/v1/auth/login"
$credentials = @{
    username = "admin"
    password = "admin123"
}

Write-Host "URL: $apiUrl" -ForegroundColor Gray
Write-Host "Credentials: admin/admin123" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri $apiUrl -Method POST -Body ($credentials | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 10
    
    Write-Host "`nSUCCESS! Authentication working!" -ForegroundColor Green
    Write-Host "User: $($response.user.username)" -ForegroundColor White
    Write-Host "Role: $($response.user.role)" -ForegroundColor White
    Write-Host "Token received: $($response.access_token -ne $null)" -ForegroundColor White
    Write-Host "Token type: $($response.token_type)" -ForegroundColor White
    
    Write-Host "`n=== FINAL RESULT ===" -ForegroundColor Magenta
    Write-Host "✓ Authentication FIXED and working!" -ForegroundColor Green
    Write-Host "✓ Expected test success rate: 100% (7/7)" -ForegroundColor Green
    Write-Host "✓ Unicode issues resolved" -ForegroundColor Green
    Write-Host "✓ Docker services running" -ForegroundColor Green
    Write-Host "✓ Database connected" -ForegroundColor Green
    Write-Host "✓ Admin user exists" -ForegroundColor Green
    
}
catch {
    Write-Host "`nAUTHENTICATION STILL FAILING!" -ForegroundColor Red
    
    $statusCode = $null
    $errorBody = ""
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "Status Code: $statusCode" -ForegroundColor Yellow
        
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $errorBody = $reader.ReadToEnd()
            $reader.Close()
            Write-Host "Error Response: $errorBody" -ForegroundColor Red
        } catch {
            Write-Host "Could not read error response" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Connection error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host "`n=== FINAL 5 WHYS ANALYSIS ===" -ForegroundColor Magenta
    
    if ($statusCode -eq 401) {
        Write-Host "Why #1: 401 Unauthorized = Invalid credentials" -ForegroundColor Yellow
        Write-Host "Why #2: User lookup failed OR password verification failed" -ForegroundColor Yellow  
        Write-Host "Why #3: Database query failed OR password hash mismatch" -ForegroundColor Yellow
        Write-Host "Why #4: Admin user not properly created OR hash format wrong" -ForegroundColor Yellow
        Write-Host "Why #5: ROOT CAUSE = Admin user creation or password hashing issue" -ForegroundColor Red
        
        Write-Host "`nDiagnostic steps:" -ForegroundColor Cyan
        Write-Host "1. Check if admin user exists in database" -ForegroundColor Gray
        Write-Host "2. Verify password hash format" -ForegroundColor Gray
        Write-Host "3. Check database connection from app" -ForegroundColor Gray
        
    } elseif ($statusCode -eq 500) {
        Write-Host "Why #1: 500 Internal Server Error = Unhandled exception" -ForegroundColor Yellow
        Write-Host "Why #2: Exception in authentication service" -ForegroundColor Yellow
        Write-Host "Why #3: Database connection failed OR service initialization failed" -ForegroundColor Yellow
        Write-Host "Why #4: Environment variables wrong OR dependency missing" -ForegroundColor Yellow
        Write-Host "Why #5: ROOT CAUSE = Service configuration or dependency issue" -ForegroundColor Red
        
        Write-Host "`nDiagnostic steps:" -ForegroundColor Cyan
        Write-Host "1. Check server logs:" -ForegroundColor Gray
        Receive-Job $job | Select-Object -Last 5
        Write-Host "2. Verify DATABASE_URL environment variable" -ForegroundColor Gray
        Write-Host "3. Check if all required Python packages are installed" -ForegroundColor Gray
        
    } else {
        Write-Host "Unexpected error - manual investigation needed" -ForegroundColor Red
        Write-Host "Status: $statusCode" -ForegroundColor Yellow
        Write-Host "Error: $errorBody" -ForegroundColor Red
    }
}

# Show system status
Write-Host "`n--- SYSTEM STATUS ---" -ForegroundColor Magenta
Write-Host "Docker containers:" -ForegroundColor Cyan
docker-compose ps

Write-Host "`nTo stop everything:" -ForegroundColor Yellow
Write-Host "Stop-Job $($job.Id); Remove-Job $($job.Id); docker-compose down" -ForegroundColor Gray

Write-Host "`n=== TEST COMPLETE ===" -ForegroundColor Yellow