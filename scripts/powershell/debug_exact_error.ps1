# Exact replication of original test authentication logic
Write-Host "=== EXACT ERROR ANALYSIS ===" -ForegroundColor Yellow

try {
    $authBody = '{"username":"admin","password":"admin123"}'
    $authResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $authBody -ContentType "application/json" -UseBasicParsing -TimeoutSec 10 -ErrorAction SilentlyContinue
    
    if ($authResponse -and $authResponse.StatusCode -eq 200) {
        Write-Host "SUCCESS PATH: Status 200" -ForegroundColor Green
        $authData = $authResponse.Content | ConvertFrom-Json
        $token = $authData.access_token
    } else {
        $statusCode = if ($authResponse) { $authResponse.StatusCode } else { "No Response" }
        Write-Host "FAIL PATH: Status $statusCode" -ForegroundColor Red
    }
} catch {
    Write-Host "EXCEPTION PATH ENTERED" -ForegroundColor Red
    Write-Host "Exception Type: $($_.Exception.GetType().Name)" -ForegroundColor Red
    Write-Host "Exception Message: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        Write-Host "Has Response Object: YES" -ForegroundColor Yellow
        Write-Host "Response Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
        Write-Host "Status equals 200? $($_.Exception.Response.StatusCode -eq 200)" -ForegroundColor Yellow
        Write-Host "Status equals 401? $($_.Exception.Response.StatusCode -eq 401)" -ForegroundColor Yellow
    } else {
        Write-Host "Has Response Object: NO" -ForegroundColor Red
    }
    
    # This is the exact logic from the original test
    if ($_.Exception.Response -and $_.Exception.Response.StatusCode -eq 200) {
        Write-Host "ORIGINAL TEST RESULT: PASS" -ForegroundColor Green
    } else {
        Write-Host "ORIGINAL TEST RESULT: ERROR" -ForegroundColor Red
    }
}