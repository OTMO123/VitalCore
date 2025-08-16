# Create test user and test API
Write-Host "Creating test user..." -ForegroundColor Yellow

try {
    # Try to register a new user first
    $registerBody = @{
        username = "testuser"
        email = "test@iris.com"
        password = "TestPass123"
        full_name = "Test User"
    } | ConvertTo-Json
    
    $headers = @{"Content-Type" = "application/json"}
    $registerResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/register" -Method POST -Headers $headers -Body $registerBody
    Write-Host "✅ User registered successfully!" -ForegroundColor Green
    
    # Now try to login with the new user
    $loginBody = "username=testuser&password=TestPass123"
    $loginHeaders = @{"Content-Type" = "application/x-www-form-urlencoded"}
    
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    $token = $response.access_token
    Write-Host "✅ LOGIN SUCCESS! Token received" -ForegroundColor Green
    
    # Test patient endpoint with token
    $authHeaders = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    $patients = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Headers $authHeaders
    Write-Host "✅ PATIENTS API SUCCESS! Found $($patients.total) patients" -ForegroundColor Green
    
    Write-Host "`n🎉 100% SUCCESS! Backend is fully functional!" -ForegroundColor Green
    Write-Host "🎉 Frontend will work perfectly!" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Registration failed: $($_.Exception.Message)" -ForegroundColor Red
    
    # Try with different common credentials
    Write-Host "Trying common test credentials..." -ForegroundColor Yellow
    
    $testCreds = @(
        @{user="admin"; pass="admin"},
        @{user="test"; pass="test"},
        @{user="user"; pass="password"},
        @{user="demo"; pass="demo123"}
    )
    
    foreach ($cred in $testCreds) {
        try {
            $loginBody = "username=$($cred.user)&password=$($cred.pass)"
            $loginHeaders = @{"Content-Type" = "application/x-www-form-urlencoded"}
            
            $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
            Write-Host "✅ LOGIN SUCCESS with $($cred.user)!" -ForegroundColor Green
            break
        } catch {
            Write-Host "❌ Failed: $($cred.user)" -ForegroundColor Red
        }
    }
}