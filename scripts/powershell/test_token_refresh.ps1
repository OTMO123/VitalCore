# Test token refresh functionality
Write-Host "=== TOKEN REFRESH TEST ===" -ForegroundColor Cyan

# First, login to get tokens
Write-Host "1. Getting initial tokens..." -ForegroundColor Yellow
$loginHeaders = @{
    'Content-Type' = 'application/x-www-form-urlencoded'
}
$loginBody = "username=admin&password=admin123"

try {
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    Write-Host "✅ Login successful" -ForegroundColor Green
    
    $accessToken = $loginResponse.access_token
    $refreshToken = $loginResponse.refresh_token
    
    Write-Host "Access Token (first 50 chars): $($accessToken.Substring(0, 50))..." -ForegroundColor White
    Write-Host "Refresh Token (first 50 chars): $($refreshToken.Substring(0, 50))..." -ForegroundColor White
    
    # Test protected endpoint with access token
    Write-Host "`n2. Testing protected endpoint..." -ForegroundColor Yellow
    $authHeaders = @{
        'Authorization' = "Bearer $accessToken"
        'Content-Type' = 'application/json'
    }
    
    $protectedResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/audit/logs" -Method GET -Headers $authHeaders
    Write-Host "✅ Protected endpoint accessible" -ForegroundColor Green
    Write-Host "Response: $($protectedResponse | ConvertTo-Json -Depth 1)" -ForegroundColor White
    
    # Test refresh token endpoint
    Write-Host "`n3. Testing refresh token..." -ForegroundColor Yellow
    $refreshHeaders = @{
        'Content-Type' = 'application/json'
    }
    $refreshBody = @{
        refresh_token = $refreshToken
    } | ConvertTo-Json
    
    try {
        $refreshResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/auth/refresh" -Method POST -Headers $refreshHeaders -Body $refreshBody
        Write-Host "✅ Token refresh successful" -ForegroundColor Green
        Write-Host "New Access Token (first 50 chars): $($refreshResponse.access_token.Substring(0, 50))..." -ForegroundColor White
    } catch {
        Write-Host "❌ Token refresh failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ Login failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
}

Write-Host "`n=== TOKEN TEST COMPLETE ===" -ForegroundColor Cyan