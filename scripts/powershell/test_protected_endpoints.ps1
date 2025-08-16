# Test protected endpoints with authentication
Write-Host "=== PROTECTED ENDPOINTS TEST ===" -ForegroundColor Cyan

# Login first
Write-Host "Getting authentication token..." -ForegroundColor Yellow
$loginHeaders = @{
    'Content-Type' = 'application/x-www-form-urlencoded'
}
$loginBody = "username=admin&password=admin123"

try {
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    $token = $loginResponse.access_token
    Write-Host "✅ Token obtained" -ForegroundColor Green
    
    $authHeaders = @{
        'Authorization' = "Bearer $token"
        'Content-Type' = 'application/json'
    }
    
    # Test different protected endpoints
    $endpoints = @(
        @{url = "/api/v1/audit/logs"; name = "Audit Logs"},
        @{url = "/api/v1/iris/sync/status"; name = "IRIS Sync Status"},
        @{url = "/api/v1/healthcare/documents"; name = "Healthcare Documents"},
        @{url = "/api/v1/purge/status"; name = "Purge Status"}
    )
    
    foreach ($endpoint in $endpoints) {
        Write-Host "`nTesting $($endpoint.name)..." -ForegroundColor Yellow
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:8003$($endpoint.url)" -Method GET -Headers $authHeaders
            Write-Host "✅ $($endpoint.name): SUCCESS" -ForegroundColor Green
            
            # Show first few lines of response
            if ($response -is [array] -and $response.Count -gt 0) {
                Write-Host "   Sample data: $($response[0] | ConvertTo-Json -Compress)" -ForegroundColor Gray
            } elseif ($response -is [object]) {
                Write-Host "   Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Gray
            }
        } catch {
            Write-Host "❌ $($endpoint.name): FAILED - $($_.Exception.Message)" -ForegroundColor Red
            if ($_.Exception.Response.StatusCode -eq 401) {
                Write-Host "   → Authentication issue" -ForegroundColor Yellow
            } elseif ($_.Exception.Response.StatusCode -eq 404) {
                Write-Host "   → Endpoint not found" -ForegroundColor Yellow
            }
        }
    }
    
} catch {
    Write-Host "❌ Login failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== PROTECTED ENDPOINTS TEST COMPLETE ===" -ForegroundColor Cyan