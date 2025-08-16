# Test if encryption service is causing 422 issues
Write-Host "Testing if encryption service is causing issues..." -ForegroundColor Cyan

try {
    # Test 1: Try direct auth endpoint with curl equivalent
    Write-Host "STEP 1: Testing auth endpoint directly..." -ForegroundColor Yellow
    
    $loginBody = @{
        username = "admin"
        password = "admin123"
    } | ConvertTo-Json
    
    Write-Host "Sending login request..." -ForegroundColor Gray
    Write-Host "Body: $loginBody" -ForegroundColor Gray
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $loginBody -ContentType "application/json" -UseBasicParsing
        Write-Host "✅ Auth SUCCESS: Status $($response.StatusCode)" -ForegroundColor Green
        $authData = $response.Content | ConvertFrom-Json
        Write-Host "Got token: $($authData.access_token -ne $null)" -ForegroundColor Green
    } catch {
        Write-Host "❌ Auth FAILED: Status $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        
        # Try to get response content
        if ($_.Exception.Response) {
            try {
                $errorStream = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($errorStream)
                $errorContent = $reader.ReadToEnd()
                Write-Host "Error details: $errorContent" -ForegroundColor Yellow
            } catch {
                Write-Host "Could not read error details" -ForegroundColor Gray
            }
        }
    }
    
    # Test 2: Try a simple health endpoint
    Write-Host "STEP 2: Testing health endpoint..." -ForegroundColor Yellow
    
    try {
        $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET
        Write-Host "✅ Health endpoint works: $($healthResponse.status)" -ForegroundColor Green
    } catch {
        Write-Host "❌ Health endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Test 3: Try auth health endpoint  
    Write-Host "STEP 3: Testing if server is responding at all..." -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/" -Method GET -UseBasicParsing
        Write-Host "✅ Server responding: Status $($response.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "❌ Server not responding: $($_.Exception.Message)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "FATAL ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "=== ENCRYPTION TEST COMPLETE ===" -ForegroundColor Cyan