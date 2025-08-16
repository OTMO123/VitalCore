# Simple Server Startup and Authentication Test (No Docker)
Write-Host "=== SIMPLE SERVER STARTUP & AUTH TEST ===" -ForegroundColor Yellow
Write-Host "Purpose: Start FastAPI server directly and test authentication" -ForegroundColor Cyan

# Step 1: Check Python availability
Write-Host "`n--- STEP 1: Python Environment Check ---" -ForegroundColor Green
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Python available: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "Trying python3..." -ForegroundColor Yellow
        $pythonVersion = python3 --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Python3 available: $pythonVersion" -ForegroundColor Green
            $pythonCmd = "python3"
        } else {
            Write-Host "✗ Python not found" -ForegroundColor Red
            exit 1
        }
    }
    
    if (-not $pythonCmd) { $pythonCmd = "python" }
} catch {
    Write-Host "✗ Python not available" -ForegroundColor Red
    exit 1
}

# Step 2: Check if virtual environment exists
Write-Host "`n--- STEP 2: Virtual Environment Check ---" -ForegroundColor Green
if (Test-Path "venv\Scripts\activate.ps1") {
    Write-Host "✓ Virtual environment found" -ForegroundColor Green
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    try {
        & "venv\Scripts\activate.ps1"
        Write-Host "✓ Virtual environment activated" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Could not activate virtual environment" -ForegroundColor Yellow
    }
} elseif (Test-Path ".venv\Scripts\activate.ps1") {
    Write-Host "✓ Virtual environment found in .venv" -ForegroundColor Green
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    try {
        & ".venv\Scripts\activate.ps1"
        Write-Host "✓ Virtual environment activated" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Could not activate virtual environment" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠ No virtual environment found, using system Python" -ForegroundColor Yellow
}

# Step 3: Install dependencies if needed
Write-Host "`n--- STEP 3: Dependencies Check ---" -ForegroundColor Green
Write-Host "Checking if FastAPI is installed..." -ForegroundColor Cyan

try {
    $fastApiCheck = & $pythonCmd -c "import fastapi; print('FastAPI available')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ FastAPI is available" -ForegroundColor Green
    } else {
        Write-Host "✗ FastAPI not available" -ForegroundColor Red
        Write-Host "Installing requirements..." -ForegroundColor Yellow
        & $pythonCmd -m pip install -r requirements.txt
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Dependencies installed" -ForegroundColor Green
        } else {
            Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
            Write-Host "Please run: pip install -r requirements.txt" -ForegroundColor Yellow
            exit 1
        }
    }
} catch {
    Write-Host "⚠ Could not check dependencies" -ForegroundColor Yellow
}

# Step 4: Start FastAPI server
Write-Host "`n--- STEP 4: Starting FastAPI Server ---" -ForegroundColor Green
Write-Host "Starting server with enhanced logging..." -ForegroundColor Cyan

try {
    # Kill any existing server on port 8000
    $existingProcess = Get-Process | Where-Object { $_.ProcessName -eq "python" -and $_.MainWindowTitle -like "*8000*" } -ErrorAction SilentlyContinue
    if ($existingProcess) {
        Write-Host "Stopping existing server..." -ForegroundColor Yellow
        $existingProcess | Stop-Process -Force
        Start-Sleep -Seconds 2
    }
    
    # Start server in background job
    Write-Host "Launching FastAPI application..." -ForegroundColor Gray
    $serverJob = Start-Job -ScriptBlock {
        param($pythonPath, $workingDir, $pythonCmd)
        Set-Location $workingDir
        
        # Set environment variables for enhanced logging
        $env:PYTHONUNBUFFERED = "1"
        $env:LOG_LEVEL = "DEBUG"
        
        if (Test-Path "venv\Scripts\activate.ps1") {
            & "venv\Scripts\activate.ps1"
        } elseif (Test-Path ".venv\Scripts\activate.ps1") {
            & ".venv\Scripts\activate.ps1"
        }
        
        # Start the server
        & $pythonCmd app/main.py
    } -ArgumentList $pythonCmd, $PWD, $pythonCmd
    
    Write-Host "Server job started (ID: $($serverJob.Id))" -ForegroundColor Green
    Write-Host "Waiting for server to initialize..." -ForegroundColor Yellow
    
    # Wait and check for server readiness
    $maxWaitTime = 30
    $waitTime = 0
    $serverReady = $false
    
    while ($waitTime -lt $maxWaitTime -and -not $serverReady) {
        Start-Sleep -Seconds 2
        $waitTime += 2
        
        try {
            $healthTest = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 3 -ErrorAction Stop
            Write-Host "✓ Server is ready!" -ForegroundColor Green
            Write-Host "Health Status: $($healthTest.status)" -ForegroundColor White
            $serverReady = $true
        } catch {
            Write-Host "." -NoNewline -ForegroundColor Yellow
        }
    }
    
    if (-not $serverReady) {
        Write-Host "`n✗ Server failed to start within $maxWaitTime seconds" -ForegroundColor Red
        Write-Host "Job State: $($serverJob.State)" -ForegroundColor Yellow
        
        # Get job output for diagnosis
        $jobOutput = Receive-Job $serverJob -ErrorAction SilentlyContinue
        if ($jobOutput) {
            Write-Host "Server output:" -ForegroundColor Yellow
            Write-Host $jobOutput -ForegroundColor Gray
        }
        
        # Check if port is in use
        Write-Host "`nChecking if port 8000 is in use:" -ForegroundColor Cyan
        netstat -an | findstr ":8000"
        
        exit 1
    }
    
} catch {
    Write-Host "✗ Failed to start server" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Step 5: Run Enhanced Authentication Test
Write-Host "`n--- STEP 5: Enhanced Authentication Test ---" -ForegroundColor Green
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
    # Test authentication
    $response = Invoke-RestMethod -Uri $apiUrl -Method POST -Body ($credentials | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 10
    
    Write-Host "✓ AUTHENTICATION SUCCESS!" -ForegroundColor Green
    Write-Host "Access token received: $($response.access_token -ne $null)" -ForegroundColor White
    Write-Host "Token type: $($response.token_type)" -ForegroundColor White
    Write-Host "User: $($response.user.username)" -ForegroundColor White
    
    # Update success rate
    Write-Host "`n=== AUTHENTICATION TEST RESULT ===" -ForegroundColor Magenta
    Write-Host "Status: SUCCESS - Authentication working!" -ForegroundColor Green
    Write-Host "Expected test success rate: 100% (7/7)" -ForegroundColor Green
    
} catch {
    Write-Host "✗ AUTHENTICATION FAILED" -ForegroundColor Red
    
    # Detailed error analysis
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
            
            # 5 Whys analysis
            Write-Host "`n=== 5 WHYS ANALYSIS ===" -ForegroundColor Magenta
            Write-Host "Status Code: $statusCode" -ForegroundColor Yellow
            
            switch ($statusCode) {
                401 { 
                    Write-Host "Root Cause: Invalid credentials or user lookup failure" -ForegroundColor Red
                    Write-Host "Check: Admin user exists and password is correct" -ForegroundColor Cyan
                }
                500 { 
                    Write-Host "Root Cause: Server-side error during authentication" -ForegroundColor Red
                    Write-Host "Check: Application logs for stack traces" -ForegroundColor Cyan
                }
                default { 
                    Write-Host "Root Cause: Unexpected authentication error" -ForegroundColor Red
                }
            }
        }
    } else {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Step 6: Cleanup and summary
Write-Host "`n--- CLEANUP & SUMMARY ---" -ForegroundColor Green
Write-Host "Server is running in background job (ID: $($serverJob.Id))" -ForegroundColor Cyan
Write-Host "To stop server: Stop-Job $($serverJob.Id); Remove-Job $($serverJob.Id)" -ForegroundColor Yellow

Write-Host "`nSystem URLs:" -ForegroundColor Cyan
Write-Host "• API Server: http://localhost:8000" -ForegroundColor Gray
Write-Host "• Documentation: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "• Health Check: http://localhost:8000/health" -ForegroundColor Gray

Write-Host "`n=== SIMPLE SERVER TEST COMPLETE ===" -ForegroundColor Yellow