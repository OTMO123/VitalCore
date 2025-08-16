# Debug Authentication Issue
Write-Host "=== AUTHENTICATION DEBUG ===" -ForegroundColor Yellow

try {
    $authBody = '{"username":"admin","password":"admin123"}'
    Write-Host "Testing: $authBody" -ForegroundColor Gray
    
    $authResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $authBody -ContentType "application/json" -UseBasicParsing -TimeoutSec 10
    
    Write-Host "SUCCESS: Status $($authResponse.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($authResponse.Content)" -ForegroundColor Gray
    
} catch {
    Write-Host "EXCEPTION CAUGHT:" -ForegroundColor Red
    Write-Host "Message: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        Write-Host "Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response Body: $responseBody" -ForegroundColor Red
    }
}