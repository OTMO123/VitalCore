# Security Validation Script - Prevent Future Security Bypasses
# Run this script to verify all security functions are active

param(
    [string]$BaseUrl = "http://localhost:8000"
)

Write-Host "🔒 SECURITY VALIDATION SCRIPT" -ForegroundColor Green
Write-Host "Verifying all security functions are active..." -ForegroundColor Yellow

# Test 1: Verify Security Headers
Write-Host "`n1. Testing Security Headers..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/health" -Method GET
    
    $requiredHeaders = @(
        'Content-Security-Policy',
        'X-Content-Type-Options', 
        'X-Frame-Options',
        'X-XSS-Protection'
    )
    
    $missingHeaders = @()
    foreach ($header in $requiredHeaders) {
        if (-not $response.Headers[$header]) {
            $missingHeaders += $header
        }
    }
    
    if ($missingHeaders.Count -eq 0) {
        Write-Host "   ✅ All security headers present" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Missing headers: $($missingHeaders -join ', ')" -ForegroundColor Red
        Write-Host "   🚨 CRITICAL: SecurityHeadersMiddleware not active!" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Failed to test security headers: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Verify PHI Audit Logging
Write-Host "`n2. Testing PHI Audit Middleware..." -ForegroundColor Cyan
try {
    # Check if logs contain PHI audit entries
    $logs = docker logs iris_app --tail 50 2>&1
    $phiLogs = $logs | Where-Object { $_ -match "PHI|Security headers applied|Audit" }
    
    if ($phiLogs.Count -gt 0) {
        Write-Host "   ✅ PHI Audit Middleware active (found $($phiLogs.Count) audit entries)" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  No PHI audit logs found - middleware may not be active" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Failed to check PHI audit logs: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Verify Authentication Required
Write-Host "`n3. Testing Authentication Enforcement..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/api/v1/healthcare/patients" -Method GET -ErrorAction SilentlyContinue
    Write-Host "   ❌ SECURITY BREACH: Access granted without authentication!" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "   ✅ Authentication properly enforced (401 Unauthorized)" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Unexpected response: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
    }
}

# Test 4: Verify HTTPS Enforcement (in production)
Write-Host "`n4. Testing HTTPS Configuration..." -ForegroundColor Cyan
if ($BaseUrl.StartsWith("https://")) {
    Write-Host "   ✅ Using HTTPS" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Using HTTP (acceptable in development only)" -ForegroundColor Yellow
}

Write-Host "`n🔒 SECURITY VALIDATION COMPLETE" -ForegroundColor Green
Write-Host "Run this script regularly to ensure security functions remain active" -ForegroundColor Gray