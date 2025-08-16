# Test role-based access control
Write-Host "=== ROLE-BASED ACCESS TEST ===" -ForegroundColor Cyan

# Test admin access
Write-Host "1. Testing ADMIN access..." -ForegroundColor Yellow
$loginHeaders = @{
    'Content-Type' = 'application/x-www-form-urlencoded'
}
$adminBody = "username=admin&password=admin123"

try {
    $adminResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $adminBody
    Write-Host "✅ Admin login successful" -ForegroundColor Green
    Write-Host "   Role: $($adminResponse.user.role)" -ForegroundColor White
    Write-Host "   User ID: $($adminResponse.user.id)" -ForegroundColor White
    Write-Host "   Active: $($adminResponse.user.is_active)" -ForegroundColor White
    
    # Test admin-only endpoints
    $adminAuthHeaders = @{
        'Authorization' = "Bearer $($adminResponse.access_token)"
        'Content-Type' = 'application/json'
    }
    
    # Try accessing admin-specific endpoints
    try {
        $auditLogs = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/audit/logs" -Method GET -Headers $adminAuthHeaders
        Write-Host "✅ Admin can access audit logs" -ForegroundColor Green
    } catch {
        Write-Host "❌ Admin cannot access audit logs: $($_.Exception.Message)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ Admin login failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test if user exists (if not, we'll note it)
Write-Host "`n2. Testing USER access (if user exists)..." -ForegroundColor Yellow
$userBody = "username=user&password=user123"

try {
    $userResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $userBody
    Write-Host "✅ User login successful" -ForegroundColor Green
    Write-Host "   Role: $($userResponse.user.role)" -ForegroundColor White
    Write-Host "   User ID: $($userResponse.user.id)" -ForegroundColor White
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "Regular user account does not exist - only admin account available" -ForegroundColor Yellow
        Write-Host "   This is normal for initial setup" -ForegroundColor Gray
    } else {
        Write-Host "❌ User login error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n=== ROLE ACCESS TEST COMPLETE ===" -ForegroundColor Cyan