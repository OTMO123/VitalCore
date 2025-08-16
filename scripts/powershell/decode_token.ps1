# Decode JWT token to see what's inside
Write-Host "=== JWT TOKEN ANALYSIS ===" -ForegroundColor Cyan

# Login and get token
$loginHeaders = @{
    'Content-Type' = 'application/x-www-form-urlencoded'
}
$loginBody = "username=admin&password=admin123"

try {
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    $token = $loginResponse.access_token
    
    Write-Host "✅ Token obtained" -ForegroundColor Green
    Write-Host "User from response: $($loginResponse.user | ConvertTo-Json)" -ForegroundColor White
    
    # Decode JWT payload (base64 decode middle part)
    $tokenParts = $token.Split('.')
    if ($tokenParts.Length -eq 3) {
        $payload = $tokenParts[1]
        
        # Add padding if needed for base64 decode
        while ($payload.Length % 4 -ne 0) {
            $payload += "="
        }
        
        try {
            $decodedBytes = [System.Convert]::FromBase64String($payload)
            $decodedText = [System.Text.Encoding]::UTF8.GetString($decodedBytes)
            $payloadJson = $decodedText | ConvertFrom-Json
            
            Write-Host "`nToken payload:" -ForegroundColor Yellow
            Write-Host "User ID: $($payloadJson.user_id)" -ForegroundColor White
            Write-Host "Username: $($payloadJson.username)" -ForegroundColor White
            Write-Host "Role: $($payloadJson.role)" -ForegroundColor White
            Write-Host "Email: $($payloadJson.email)" -ForegroundColor White
            Write-Host "Expires: $(Get-Date -UnixTimeSeconds $payloadJson.exp)" -ForegroundColor White
            Write-Host "Issued: $(Get-Date -UnixTimeSeconds $payloadJson.iat)" -ForegroundColor White
            
        } catch {
            Write-Host "❌ Failed to decode token payload: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ Invalid JWT format" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ Login failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== TOKEN ANALYSIS COMPLETE ===" -ForegroundColor Cyan