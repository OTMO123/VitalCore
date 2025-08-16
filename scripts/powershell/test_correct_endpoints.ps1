# Test correct existing endpoints
Write-Host "=== TESTING EXISTING ENDPOINTS ===" -ForegroundColor Cyan

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
    Write-Host "User role: $($loginResponse.user.role)" -ForegroundColor White
    
    $authHeaders = @{
        'Authorization' = "Bearer $token"
        'Content-Type' = 'application/json'
    }
    
    # Test existing endpoints that should work
    $endpoints = @(
        @{url = "/health"; method = "GET"; name = "Health Check"; noAuth = $true},
        @{url = "/api/v1/auth/profile"; method = "GET"; name = "User Profile"},
        @{url = "/api/v1/audit/health"; method = "GET"; name = "Audit Health"},
        @{url = "/api/v1/audit/stats"; method = "GET"; name = "Audit Stats (Admin)"},
        @{url = "/api/v1/healthcare/health"; method = "GET"; name = "Healthcare Health"},
        @{url = "/api/v1/iris/health"; method = "GET"; name = "IRIS Health"},
        @{url = "/api/v1/purge/health"; method = "GET"; name = "Purge Health"}
    )
    
    foreach ($endpoint in $endpoints) {
        Write-Host "`nTesting $($endpoint.name)..." -ForegroundColor Yellow
        
        $headers = if ($endpoint.noAuth) { @{} } else { $authHeaders }
        $fullUrl = if ($endpoint.url.StartsWith("/api")) { "http://localhost:8003$($endpoint.url)" } else { "http://localhost:8003$($endpoint.url)" }
        
        try {
            $response = Invoke-RestMethod -Uri $fullUrl -Method $endpoint.method -Headers $headers
            Write-Host "✅ $($endpoint.name): SUCCESS" -ForegroundColor Green
            
            # Show response
            if ($response -is [object]) {
                $responseText = $response | ConvertTo-Json -Compress
                if ($responseText.Length -gt 100) {
                    $responseText = $responseText.Substring(0, 100) + "..."
                }
                Write-Host "   Response: $responseText" -ForegroundColor Gray
            }
        } catch {
            $statusCode = if ($_.Exception.Response) { $_.Exception.Response.StatusCode } else { "Unknown" }
            
            if ($statusCode -eq 401) {
                Write-Host "❌ $($endpoint.name): UNAUTHORIZED (401)" -ForegroundColor Red
                Write-Host "   → Token authentication issue" -ForegroundColor Yellow
            } elseif ($statusCode -eq 403) {
                Write-Host "❌ $($endpoint.name): FORBIDDEN (403)" -ForegroundColor Red
                Write-Host "   → Insufficient permissions (needs admin/auditor role)" -ForegroundColor Yellow
            } elseif ($statusCode -eq 404) {
                Write-Host "❌ $($endpoint.name): NOT FOUND (404)" -ForegroundColor Red
                Write-Host "   → Endpoint does not exist" -ForegroundColor Yellow
            } elseif ($statusCode -eq 500) {
                Write-Host "❌ $($endpoint.name): SERVER ERROR (500)" -ForegroundColor Red
                Write-Host "   → Backend implementation issue" -ForegroundColor Yellow
            } else {
                Write-Host "❌ $($endpoint.name): ERROR ($statusCode)" -ForegroundColor Red
                Write-Host "   → $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    }
    
} catch {
    Write-Host "❌ Login failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== ENDPOINT TEST COMPLETE ===" -ForegroundColor Cyan