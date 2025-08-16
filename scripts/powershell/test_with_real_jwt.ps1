# Test with Real JWT Token
Write-Host "=== TESTING WITH REAL JWT TOKEN ===" -ForegroundColor Green

try {
    # Step 1: Get valid JWT token
    $authBody = '{"username":"admin","password":"admin123"}'
    $authResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $authBody -ContentType "application/json" -UseBasicParsing -TimeoutSec 10
    
    if ($authResponse.StatusCode -eq 200) {
        $authData = $authResponse.Content | ConvertFrom-Json
        $token = $authData.access_token
        Write-Host "✅ JWT Token obtained: ${token:0:50}..." -ForegroundColor Green
        
        # Step 2: Test workflows endpoint with real token
        Write-Host "`nTesting workflows endpoint..." -ForegroundColor Cyan
        $headers = @{ "Authorization" = "Bearer $token" }
        $workflowResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/clinical-workflows/workflows" -Headers $headers -UseBasicParsing -TimeoutSec 10
        
        Write-Host "✅ Workflows endpoint: SUCCESS ($($workflowResponse.StatusCode))" -ForegroundColor Green
        Write-Host "Response: $($workflowResponse.Content)" -ForegroundColor Gray
        
    } else {
        Write-Host "❌ Failed to get JWT token: $($authResponse.StatusCode)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $errorContent = $reader.ReadToEnd()
            Write-Host "Error details: $errorContent" -ForegroundColor Red
        } catch {
            Write-Host "Could not read error response" -ForegroundColor Red
        }
    }
}