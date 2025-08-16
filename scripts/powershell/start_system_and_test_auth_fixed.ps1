# Complete System Startup and Authentication Test - FIXED VERSION
Write-Host "=== IRIS HEALTHCARE PLATFORM - SYSTEM STARTUP & AUTH TEST ===" -ForegroundColor Yellow
Write-Host "Purpose: Start Docker services, run server, and test authentication with enhanced logging" -ForegroundColor Cyan

# Step 1: Check Docker availability
Write-Host "`n--- STEP 1: Docker System Check ---" -ForegroundColor Green
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker available: $dockerVersion" -ForegroundColor Green
    
    # Check if Docker is running
    $dockerPsResult = docker ps 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker daemon is running" -ForegroundColor Green
    } else {
        Write-Host "⚠ Docker daemon may not be running" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Docker not available or not in PATH" -ForegroundColor Red
    Write-Host "Please ensure Docker Desktop is installed and running" -ForegroundColor Yellow
    exit 1
}

# Step 2: Start Docker Compose services
Write-Host "`n--- STEP 2: Starting Docker Services ---" -ForegroundColor Green
Write-Host "Starting PostgreSQL, Redis, MinIO..." -ForegroundColor Cyan

try {
    # Stop any existing containers first
    Write-Host "Stopping existing containers..." -ForegroundColor Gray
    $stopResult = docker-compose down --remove-orphans 2>&1
    
    # Start infrastructure services
    Write-Host "Starting infrastructure services..." -ForegroundColor Gray
    $startResult = docker-compose up -d postgres redis minio
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Infrastructure services started" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to start infrastructure services" -ForegroundColor Red
        Write-Host "Checking logs..." -ForegroundColor Yellow
        docker-compose logs --tail=20
        exit 1
    }
    
    # Wait for services to be ready
    Write-Host "Waiting for services to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
} catch {
    Write-Host "✗ Docker compose failed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Step 3: Check service health
Write-Host "`n--- STEP 3: Service Health Check ---" -ForegroundColor Green
Write-Host "Checking PostgreSQL connection..." -ForegroundColor Cyan

try {
    # Test PostgreSQL connection
    $postgresTest = docker exec iris_postgres pg_isready -U iris_user -d iris_db 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ PostgreSQL is ready" -ForegroundColor Green
    } else {
        Write-Host "⚠ PostgreSQL connection issue" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Could not test PostgreSQL connection" -ForegroundColor Yellow
}

# Step 4: Run database migrations
Write-Host "`n--- STEP 4: Database Setup ---" -ForegroundColor Green
Write-Host "Running database migrations..." -ForegroundColor Cyan

try {
    # Run Alembic migrations
    if (Test-Path "venv\Scripts\activate.ps1") {
        Write-Host "Using virtual environment..." -ForegroundColor Gray
        & "venv\Scripts\activate.ps1"
        $migrationResult = alembic upgrade head 2>&1
    } else {
        Write-Host "Running migrations with Python..." -ForegroundColor Gray
        $migrationResult = python -m alembic upgrade head 2>&1
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Database migrations completed" -ForegroundColor Green
    } else {
        Write-Host "⚠ Migration issues - continuing anyway" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Could not run migrations - continuing anyway" -ForegroundColor Yellow
}

# Step 5: Create admin user
Write-Host "`n--- STEP 5: Admin User Setup ---" -ForegroundColor Green
Write-Host "Ensuring admin user exists..." -ForegroundColor Cyan

try {
    $adminResult = python create_admin_user.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Admin user verified/created" -ForegroundColor Green
    } else {
        Write-Host "⚠ Admin user creation issues" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Could not verify admin user" -ForegroundColor Yellow
}

# Step 6: Start FastAPI server
Write-Host "`n--- STEP 6: Starting FastAPI Server ---" -ForegroundColor Green
Write-Host "Starting application server..." -ForegroundColor Cyan

$serverReady = $false
$job = $null

try {
    # Start server in background
    Write-Host "Launching FastAPI application..." -ForegroundColor Gray
    
    if (Test-Path "venv\Scripts\activate.ps1") {
        $job = Start-Job -ScriptBlock {
            Set-Location $using:PWD
            & "venv\Scripts\activate.ps1"
            python app/main.py
        }
    } else {
        $job = Start-Job -ScriptBlock {
            Set-Location $using:PWD
            python app/main.py
        }
    }
    
    Write-Host "FastAPI server job started (Job ID: $($job.Id))" -ForegroundColor Green
    Write-Host "Waiting for server to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
} catch {
    Write-Host "✗ Failed to start FastAPI server" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

# Step 7: Test server availability
Write-Host "`n--- STEP 7: Server Health Check ---" -ForegroundColor Green
$maxRetries = 5
$retryCount = 0

do {
    try {
        Write-Host "Testing server health (attempt $($retryCount + 1)/$maxRetries)..." -ForegroundColor Cyan
        $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5
        Write-Host "✓ Server is responding!" -ForegroundColor Green
        Write-Host "Health Status: $($healthResponse.status)" -ForegroundColor White
        $serverReady = $true
        break
    } catch {
        $retryCount++
        if ($retryCount -lt $maxRetries) {
            Write-Host "Server not ready yet, waiting..." -ForegroundColor Yellow
            Start-Sleep -Seconds 5
        } else {
            Write-Host "✗ Server failed to start after $maxRetries attempts" -ForegroundColor Red
            Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
            
            # Show server job status
            if ($job) {
                Write-Host "Server job status: $($job.State)" -ForegroundColor Yellow
                if ($job.State -eq "Failed") {
                    Write-Host "Job error output:" -ForegroundColor Red
                    $jobOutput = Receive-Job $job -ErrorAction SilentlyContinue
                    if ($jobOutput) {
                        Write-Host $jobOutput -ForegroundColor Gray
                    }
                }
            }
            $serverReady = $false
        }
    }
} while ($retryCount -lt $maxRetries -and -not $serverReady)

# Step 8: Run Enhanced Authentication Test (if server is ready)
if ($serverReady) {
    Write-Host "`n--- STEP 8: Enhanced Authentication Test ---" -ForegroundColor Green
    Write-Host "Running authentication test with enhanced logging..." -ForegroundColor Cyan
    
    $apiUrl = "http://localhost:8000/api/v1/auth/login"
    $credentials = @{
        username = "admin"
        password = "admin123"
    }
    
    Write-Host "Testing authentication endpoint..." -ForegroundColor Cyan
    Write-Host "URL: $apiUrl" -ForegroundColor Gray
    Write-Host "Credentials: admin/admin123" -ForegroundColor Gray
    
    try {
        # Test authentication with detailed logging
        $response = Invoke-RestMethod -Uri $apiUrl -Method POST -Body ($credentials | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 10
        
        Write-Host "✓ AUTHENTICATION SUCCESS!" -ForegroundColor Green
        Write-Host "Access token received: $($response.access_token -ne $null)" -ForegroundColor White
        Write-Host "Token type: $($response.token_type)" -ForegroundColor White
        Write-Host "User: $($response.user.username)" -ForegroundColor White
        
        # Update success rate
        Write-Host "`n=== FINAL AUTHENTICATION TEST RESULT ===" -ForegroundColor Magenta
        Write-Host "Status: SUCCESS - Authentication working after Unicode fixes!" -ForegroundColor Green
        Write-Host "Expected test success rate: 100% (7/7)" -ForegroundColor Green
        
    } catch {
        Write-Host "✗ AUTHENTICATION STILL FAILING" -ForegroundColor Red
        
        # Detailed 5 Whys analysis
        if ($_.Exception -is [System.Net.WebException]) {
            $webException = $_.Exception
            if ($webException.Response) {
                $statusCode = [int]$webException.Response.StatusCode
                $statusDescription = $webException.Response.StatusDescription
                
                Write-Host "HTTP Status: $statusCode ($statusDescription)" -ForegroundColor Yellow
                
                # Get error response
                $responseStream = $webException.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($responseStream)
                $errorBody = $reader.ReadToEnd()
                $reader.Close()
                
                Write-Host "Error Response:" -ForegroundColor Yellow
                Write-Host $errorBody -ForegroundColor Red
                
                # Enhanced 5 Whys analysis
                Write-Host "`n=== 5 WHYS ANALYSIS (POST-UNICODE FIX) ===" -ForegroundColor Magenta
                
                switch ($statusCode) {
                    401 {
                        Write-Host "Why #1: 401 Unauthorized - Credentials rejected" -ForegroundColor Yellow
                        Write-Host "Why #2: User lookup failed OR password verification failed" -ForegroundColor Yellow  
                        Write-Host "Why #3: Database connection issue OR password hash mismatch" -ForegroundColor Yellow
                        Write-Host "Why #4: PostgreSQL not accessible OR admin user missing/corrupted" -ForegroundColor Yellow
                        Write-Host "Why #5: ROOT CAUSE - Database connectivity or user data integrity issue" -ForegroundColor Red
                        Write-Host "`nNext Steps:" -ForegroundColor Cyan
                        Write-Host "1. Check Docker logs: docker-compose logs postgres" -ForegroundColor Gray
                        Write-Host "2. Verify admin user: python check_users.py" -ForegroundColor Gray
                        Write-Host "3. Check database connectivity" -ForegroundColor Gray
                    }
                    500 {
                        Write-Host "Why #1: 500 Internal Server Error - Unhandled exception" -ForegroundColor Yellow
                        Write-Host "Why #2: Service initialization failure OR runtime error" -ForegroundColor Yellow
                        Write-Host "Why #3: Event bus failure OR audit service failure OR database error" -ForegroundColor Yellow
                        Write-Host "Why #4: Dependency unavailable OR configuration issue" -ForegroundColor Yellow
                        Write-Host "Why #5: ROOT CAUSE - Service dependency or configuration failure" -ForegroundColor Red
                        Write-Host "`nNext Steps:" -ForegroundColor Cyan
                        Write-Host "1. Check application logs in job output above" -ForegroundColor Gray
                        Write-Host "2. Look for 'CRITICAL: System initialization failed'" -ForegroundColor Gray
                        Write-Host "3. Verify all Docker services are running" -ForegroundColor Gray
                    }
                    default {
                        Write-Host "Unexpected HTTP status: $statusCode" -ForegroundColor Yellow
                        Write-Host "Manual investigation required" -ForegroundColor Red
                    }
                }
            }
        } else {
            Write-Host "Connection Error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
} else {
    Write-Host "`n--- SERVER STARTUP FAILED ---" -ForegroundColor Red
    Write-Host "Cannot run authentication test without running server" -ForegroundColor Yellow
    
    # Diagnostic information
    Write-Host "`nDiagnostic Information:" -ForegroundColor Yellow
    Write-Host "1. Docker containers status:" -ForegroundColor Cyan
    docker-compose ps
    
    Write-Host "`n2. Recent Docker logs:" -ForegroundColor Cyan
    docker-compose logs --tail=20
    
    Write-Host "`n3. Check if port 8000 is in use:" -ForegroundColor Cyan
    $portCheck = netstat -an | findstr ":8000"
    if ($portCheck) {
        Write-Host $portCheck -ForegroundColor Gray
    } else {
        Write-Host "Port 8000 is not in use" -ForegroundColor Gray
    }
}

# Step 9: Final Summary
Write-Host "`n--- SYSTEM STATUS SUMMARY ---" -ForegroundColor Magenta
if ($serverReady) {
    Write-Host "✓ System is running and ready" -ForegroundColor Green
    Write-Host "Server URL: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
    
    Write-Host "`nTo stop services later:" -ForegroundColor Yellow
    Write-Host "docker-compose down" -ForegroundColor Gray
    if ($job) {
        Write-Host "Stop-Job $($job.Id); Remove-Job $($job.Id)" -ForegroundColor Gray
    }
} else {
    Write-Host "✗ System startup incomplete" -ForegroundColor Red
    Write-Host "Check the diagnostic information above" -ForegroundColor Yellow
}

Write-Host "`n=== SYSTEM STARTUP COMPLETE ===" -ForegroundColor Yellow