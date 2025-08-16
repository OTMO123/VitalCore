# PowerShell script to test login with comprehensive logging
Write-Host "🔐 SECURITY TEST - Login Authentication" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Test server health first
Write-Host "`n1. 🏥 Testing server health..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET
    Write-Host "✅ Server is healthy" -ForegroundColor Green
    $healthResponse | ConvertTo-Json
} catch {
    Write-Host "❌ Server health check failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test login
Write-Host "`n2. 🔑 Testing login endpoint..." -ForegroundColor Yellow

$headers = @{
    'Content-Type' = 'application/x-www-form-urlencoded'
    'User-Agent' = 'PowerShell-SecurityTest/1.0'
}

$body = "username=admin&password=admin123"

Write-Host "Request details:" -ForegroundColor Cyan
Write-Host "  URL: http://localhost:8000/api/v1/auth/login" -ForegroundColor White
Write-Host "  Method: POST" -ForegroundColor White
Write-Host "  Content-Type: application/x-www-form-urlencoded" -ForegroundColor White
Write-Host "  Body: $body" -ForegroundColor White

try {
    $startTime = Get-Date
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers $headers -Body $body
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalMilliseconds
    
    Write-Host "✅ LOGIN SUCCESS" -ForegroundColor Green
    Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Processing Time: $($duration) ms" -ForegroundColor Green
    
    Write-Host "`nResponse Headers:" -ForegroundColor Yellow
    foreach ($header in $response.Headers.GetEnumerator()) {
        Write-Host "  $($header.Key): $($header.Value)" -ForegroundColor White
    }
    
    Write-Host "`nResponse Content:" -ForegroundColor Yellow
    $jsonResponse = $response.Content | ConvertFrom-Json
    $jsonResponse | ConvertTo-Json -Depth 5
    
    # Check for required fields
    Write-Host "`n🔍 Security Analysis:" -ForegroundColor Cyan
    Write-Host "  Has access_token: $($null -ne $jsonResponse.access_token)" -ForegroundColor White
    Write-Host "  Has refresh_token: $($null -ne $jsonResponse.refresh_token)" -ForegroundColor White
    Write-Host "  Token type: $($jsonResponse.token_type)" -ForegroundColor White
    Write-Host "  Expires in: $($jsonResponse.expires_in) seconds" -ForegroundColor White
    
    if ($jsonResponse.user) {
        Write-Host "  User ID: $($jsonResponse.user.id)" -ForegroundColor White
        Write-Host "  Username: $($jsonResponse.user.username)" -ForegroundColor White
        Write-Host "  Role: $($jsonResponse.user.role)" -ForegroundColor White
    }
    
} catch {
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalMilliseconds
    
    Write-Host "❌ LOGIN FAILED" -ForegroundColor Red
    Write-Host "Processing Time: $($duration) ms" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    Write-Host "Status Description: $($_.Exception.Response.StatusDescription)" -ForegroundColor Red
    
    # Try to get response content for error details
    try {
        $errorStream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorStream)
        $errorContent = $reader.ReadToEnd()
        Write-Host "Error Response: $errorContent" -ForegroundColor Red
    } catch {
        Write-Host "Could not read error response" -ForegroundColor Red
    }
}

Write-Host "`n3. 🔍 Testing other endpoints for comparison..." -ForegroundColor Yellow

# Test unauthorized access to protected endpoint
try {
    Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/me" -Method GET
} catch {
    Write-Host "✅ Protected endpoint correctly returns: $($_.Exception.Response.StatusCode)" -ForegroundColor Green
}

Write-Host "`n🎯 Test completed!" -ForegroundColor Cyan