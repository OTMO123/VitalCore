# Simple API Test
Write-Host "Testing API endpoints..." -ForegroundColor Green

$baseUrl = "http://localhost:8000"

# Test health endpoint
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
    Write-Host "✅ Health endpoint working" -ForegroundColor Green
}
catch {
    Write-Host "❌ Health endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test docs endpoint  
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/docs" -Method GET
    Write-Host "✅ Docs endpoint working (Status: $($response.StatusCode))" -ForegroundColor Green
}
catch {
    Write-Host "❌ Docs endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test auth endpoint
try {
    $authData = @{
        username = "admin"
        password = "admin123"
    }
    $body = $authData | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/login" -Method POST -Body $body -ContentType "application/json"
    Write-Host "✅ Auth endpoint working" -ForegroundColor Green
    
    if ($response.access_token) {
        Write-Host "✅ Auth token received" -ForegroundColor Green
        
        # Test protected endpoint
        $headers = @{
            "Authorization" = "Bearer $($response.access_token)"
        }
        
        try {
            $userResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/me" -Method GET -Headers $headers
            Write-Host "✅ Protected endpoint working" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Protected endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}
catch {
    Write-Host "❌ Auth endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nAPI test complete!" -ForegroundColor Cyan