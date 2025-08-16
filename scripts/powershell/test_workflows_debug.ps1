# Debug Workflows Endpoint
Write-Host "=== WORKFLOW ENDPOINT DEBUG ===" -ForegroundColor Green

# Get a valid JWT token
try {
    $authBody = '{"username":"admin","password":"admin123"}'
    $authResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $authBody -ContentType "application/json" -UseBasicParsing -TimeoutSec 10
    if ($authResponse.StatusCode -eq 200) {
        $authData = $authResponse.Content | ConvertFrom-Json
        $token = $authData.access_token
        Write-Host "✅ JWT Token obtained successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to get JWT token" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Auth failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test workflows endpoint with proper auth
Write-Host "`nTesting workflows endpoint with JWT..." -ForegroundColor Cyan
try {
    $headers = @{ "Authorization" = "Bearer $token" }
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/clinical-workflows/workflows" -Headers $headers -UseBasicParsing -TimeoutSec 30 -ErrorAction Stop
    
    Write-Host "✅ Workflows endpoint: SUCCESS ($($response.StatusCode))" -ForegroundColor Green
    Write-Host "Response length: $($response.Content.Length) bytes"
    
} catch {
    Write-Host "❌ Workflows endpoint failed" -ForegroundColor Red
    Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Yellow
    
    # Try to get response content for more details
    if ($_.Exception.Response) {
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $errorContent = $reader.ReadToEnd()
            Write-Host "Error Response: $errorContent" -ForegroundColor Red
        } catch {
            Write-Host "Could not read error response" -ForegroundColor Red
        }
    }
}

Write-Host "`n=== DEBUG COMPLETE ===" -ForegroundColor Green