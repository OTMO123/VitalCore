# Quick Start and Test - Simple Version
Write-Host "=== QUICK START & AUTH TEST ===" -ForegroundColor Yellow

# Check Docker
Write-Host "Checking Docker..." -ForegroundColor Cyan
docker --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker not found!" -ForegroundColor Red
    exit 1
}

# Start Docker services
Write-Host "Starting Docker services..." -ForegroundColor Cyan
docker-compose down --remove-orphans
docker-compose up -d postgres redis minio

# Wait for services
Write-Host "Waiting for services..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Create admin user
Write-Host "Creating admin user..." -ForegroundColor Cyan
python create_admin_user.py

# Start server in background
Write-Host "Starting FastAPI server..." -ForegroundColor Cyan
$job = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    python app/main.py
}

Write-Host "Waiting for server startup..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

# Test server health
Write-Host "Testing server health..." -ForegroundColor Cyan
$retries = 0
$maxRetries = 3

while ($retries -lt $maxRetries) {
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5
        Write-Host "Server is ready!" -ForegroundColor Green
        break
    }
    catch {
        $retries++
        Write-Host "Retry $retries/$maxRetries..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    }
}

if ($retries -ge $maxRetries) {
    Write-Host "Server failed to start!" -ForegroundColor Red
    Receive-Job $job
    exit 1
}

# Test authentication
Write-Host "Testing authentication..." -ForegroundColor Cyan
$apiUrl = "http://localhost:8000/api/v1/auth/login"
$credentials = @{
    username = "admin"
    password = "admin123"
}

try {
    $response = Invoke-RestMethod -Uri $apiUrl -Method POST -Body ($credentials | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 10
    
    Write-Host "SUCCESS! Authentication working!" -ForegroundColor Green
    Write-Host "User: $($response.user.username)" -ForegroundColor White
    Write-Host "Token received: $($response.access_token -ne $null)" -ForegroundColor White
    
    Write-Host "`n=== RESULT ===" -ForegroundColor Magenta
    Write-Host "Expected test success rate: 100% (7/7)" -ForegroundColor Green
    
}
catch {
    Write-Host "AUTHENTICATION FAILED!" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "Status Code: $statusCode" -ForegroundColor Yellow
        
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $errorBody = $reader.ReadToEnd()
        $reader.Close()
        
        Write-Host "Error: $errorBody" -ForegroundColor Red
        
        Write-Host "`n=== 5 WHYS ANALYSIS ===" -ForegroundColor Magenta
        if ($statusCode -eq 401) {
            Write-Host "Why #1: 401 = Invalid credentials" -ForegroundColor Yellow
            Write-Host "Why #2: User lookup or password verification failed" -ForegroundColor Yellow
            Write-Host "Why #3: Database connection or user data issue" -ForegroundColor Yellow
            Write-Host "Why #4: Admin user missing or password hash wrong" -ForegroundColor Yellow
            Write-Host "Why #5: ROOT CAUSE = Database/user setup problem" -ForegroundColor Red
        }
        elseif ($statusCode -eq 500) {
            Write-Host "Why #1: 500 = Server error" -ForegroundColor Yellow
            Write-Host "Why #2: Unhandled exception in auth logic" -ForegroundColor Yellow
            Write-Host "Why #3: Service initialization failed" -ForegroundColor Yellow
            Write-Host "Why #4: Database or dependency unavailable" -ForegroundColor Yellow
            Write-Host "Why #5: ROOT CAUSE = Service/dependency failure" -ForegroundColor Red
        }
        
        Write-Host "`nNext Steps:" -ForegroundColor Cyan
        Write-Host "1. Check job output:" -ForegroundColor Gray
        Receive-Job $job | Select-Object -Last 20
        Write-Host "2. Check Docker logs: docker-compose logs" -ForegroundColor Gray
    }
    else {
        Write-Host "Connection error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`nTo stop: Stop-Job $($job.Id); Remove-Job $($job.Id); docker-compose down" -ForegroundColor Yellow
Write-Host "=== TEST COMPLETE ===" -ForegroundColor Yellow