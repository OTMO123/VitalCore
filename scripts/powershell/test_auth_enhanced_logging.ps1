# Enhanced Authentication Test with Comprehensive Logging Analysis
Write-Host "=== ENHANCED AUTHENTICATION LOGGING TEST ===" -ForegroundColor Yellow
Write-Host "Purpose: Capture detailed logs to identify exact authentication failure point" -ForegroundColor Cyan

$apiUrl = "http://localhost:8000/api/v1/auth/login"
$credentials = @{
    username = "admin"
    password = "admin123"
}

# Step 1: Test basic connectivity
Write-Host "`n--- STEP 1: Basic System Health ---" -ForegroundColor Green
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5
    Write-Host "✓ Server is running" -ForegroundColor Green
    Write-Host "Status: $($health.status)" -ForegroundColor White
} catch {
    Write-Host "✗ Server not responding" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Step 2: Authentication attempt with full logging
Write-Host "`n--- STEP 2: Authentication Attempt ---" -ForegroundColor Green
Write-Host "URL: $apiUrl" -ForegroundColor Cyan
Write-Host "Credentials: admin/admin123" -ForegroundColor Cyan

# Enable PowerShell verbose logging
$VerbosePreference = "Continue"
$DebugPreference = "Continue"

try {
    Write-Host "`nSending POST request..." -ForegroundColor Yellow
    
    # Manual HTTP request with detailed error capture
    $webClient = New-Object System.Net.WebClient
    $webClient.Headers.Add("Content-Type", "application/json")
    
    $jsonPayload = $credentials | ConvertTo-Json
    Write-Host "JSON Payload: $jsonPayload" -ForegroundColor Gray
    
    $response = $webClient.UploadString($apiUrl, "POST", $jsonPayload)
    
    Write-Host "✓ SUCCESS: Authentication worked!" -ForegroundColor Green
    Write-Host "Response received:" -ForegroundColor Green
    Write-Host $response -ForegroundColor White
    
} catch [System.Net.WebException] {
    $webException = $_.Exception
    Write-Host "`n✗ AUTHENTICATION FAILED - Detailed Analysis:" -ForegroundColor Red
    
    # Get response details
    if ($webException.Response) {
        $statusCode = [int]$webException.Response.StatusCode
        $statusDescription = $webException.Response.StatusDescription
        
        Write-Host "HTTP Status: $statusCode ($statusDescription)" -ForegroundColor Yellow
        
        # Read response stream
        $responseStream = $webException.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($responseStream)
        $errorBody = $reader.ReadToEnd()
        $reader.Close()
        
        Write-Host "`nError Response Body:" -ForegroundColor Yellow
        Write-Host $errorBody -ForegroundColor Red
        
        # 5 WHYS ANALYSIS with Enhanced Logging
        Write-Host "`n=== 5 WHYS ANALYSIS (Enhanced Logging Edition) ===" -ForegroundColor Magenta
        
        switch ($statusCode) {
            401 {
                Write-Host "`nWhy #1: 401 Unauthorized - Authentication failed" -ForegroundColor Yellow
                Write-Host "  → Check: Does admin user exist in database?" -ForegroundColor Cyan
                Write-Host "  → Check: Is password hash correct?" -ForegroundColor Cyan
                Write-Host "  → Expected logs: AUTH_SERVICE - Starting user lookup by username" -ForegroundColor Gray
                
                Write-Host "`nWhy #2: User lookup or password verification failed" -ForegroundColor Yellow  
                Write-Host "  → Check: DB_CONNECTION - Session established" -ForegroundColor Cyan
                Write-Host "  → Check: AUTH_SERVICE - User found by username" -ForegroundColor Cyan
                Write-Host "  → Expected logs: SECURITY_MANAGER - Password verification completed" -ForegroundColor Gray
                
                Write-Host "`nWhy #3: Database query or security manager failed" -ForegroundColor Yellow
                Write-Host "  → Check: Database connection established?" -ForegroundColor Cyan
                Write-Host "  → Check: Password hash format correct?" -ForegroundColor Cyan
                Write-Host "  → Expected logs: SECURITY_MANAGER - Starting password verification" -ForegroundColor Gray
                
                Write-Host "`nWhy #4: Infrastructure or configuration issue" -ForegroundColor Yellow
                Write-Host "  → Check: PostgreSQL running and accessible?" -ForegroundColor Cyan
                Write-Host "  → Check: Environment variables configured?" -ForegroundColor Cyan
                Write-Host "  → Expected logs: DB_CONNECTION - Getting session factory" -ForegroundColor Gray
                
                Write-Host "`nWhy #5: ROOT CAUSE ANALYSIS" -ForegroundColor Yellow
                Write-Host "  → Most Likely: Database connection failure" -ForegroundColor Red
                Write-Host "  → Also Possible: Password hash mismatch" -ForegroundColor Red
                Write-Host "  → Check application logs for:" -ForegroundColor Cyan
                Write-Host "    • DB_CONNECTION errors" -ForegroundColor Gray
                Write-Host "    • AUTH_SERVICE user lookup results" -ForegroundColor Gray
                Write-Host "    • SECURITY_MANAGER password verification" -ForegroundColor Gray
            }
            
            500 {
                Write-Host "`nWhy #1: 500 Internal Server Error - Unhandled exception" -ForegroundColor Yellow
                Write-Host "  → Check: Application logs for stack traces" -ForegroundColor Cyan
                Write-Host "  → Expected logs: CRITICAL errors in any layer" -ForegroundColor Gray
                
                Write-Host "`nWhy #2: Service initialization or dependency failure" -ForegroundColor Yellow
                Write-Host "  → Check: Event bus initialization" -ForegroundColor Cyan
                Write-Host "  → Check: Audit service initialization" -ForegroundColor Cyan
                Write-Host "  → Expected logs: System initialized successfully" -ForegroundColor Gray
                
                Write-Host "`nWhy #3: Database or external dependency unavailable" -ForegroundColor Yellow
                Write-Host "  → Check: PostgreSQL service status" -ForegroundColor Cyan
                Write-Host "  → Check: Redis service status" -ForegroundColor Cyan
                Write-Host "  → Expected logs: Database initialized successfully" -ForegroundColor Gray
                
                Write-Host "`nWhy #4: Configuration or environment issue" -ForegroundColor Yellow
                Write-Host "  → Check: Environment variables" -ForegroundColor Cyan
                Write-Host "  → Check: Database connection string" -ForegroundColor Cyan
                Write-Host "  → Expected logs: Configuration loaded successfully" -ForegroundColor Gray
                
                Write-Host "`nWhy #5: ROOT CAUSE ANALYSIS" -ForegroundColor Yellow
                Write-Host "  → Most Likely: Unhandled exception during authentication" -ForegroundColor Red
                Write-Host "  → Check logs for CRITICAL errors and stack traces" -ForegroundColor Red
            }
            
            422 {
                Write-Host "`nWhy #1: 422 Unprocessable Entity - Request validation failed" -ForegroundColor Yellow
                Write-Host "  → Check: JSON payload format" -ForegroundColor Cyan
                Write-Host "  → Check: UserLogin schema requirements" -ForegroundColor Cyan
                
                Write-Host "`nWhy #5: ROOT CAUSE - Schema validation failure" -ForegroundColor Yellow
                Write-Host "  → Fix: Verify request format matches FastAPI schema" -ForegroundColor Red
            }
            
            default {
                Write-Host "`nUnexpected status code: $statusCode" -ForegroundColor Yellow
                Write-Host "Manual investigation required" -ForegroundColor Red
            }
        }
        
        # Next steps based on analysis
        Write-Host "`n=== IMMEDIATE NEXT STEPS ===" -ForegroundColor Magenta
        Write-Host "1. Check Docker logs: docker-compose logs app" -ForegroundColor Cyan
        Write-Host "2. Look for these specific log patterns:" -ForegroundColor Cyan
        Write-Host "   • 'CRITICAL: System initialization failed'" -ForegroundColor Gray
        Write-Host "   • 'DB_CONNECTION - Failed to get session factory'" -ForegroundColor Gray
        Write-Host "   • 'AUTH_SERVICE - Failed to get user by username'" -ForegroundColor Gray
        Write-Host "   • 'SECURITY_MANAGER - Password verification failed'" -ForegroundColor Gray
        Write-Host "3. Check database connectivity directly" -ForegroundColor Cyan
        Write-Host "4. Verify admin user exists and password hash is correct" -ForegroundColor Cyan
        
    } else {
        Write-Host "No response received - connection issue" -ForegroundColor Red
    }
    
} catch {
    Write-Host "`n✗ UNEXPECTED ERROR:" -ForegroundColor Red
    Write-Host "Type: $($_.Exception.GetType().Name)" -ForegroundColor Yellow
    Write-Host "Message: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nFull Exception:" -ForegroundColor Yellow
    Write-Host $_.Exception -ForegroundColor Gray
}

Write-Host "`n=== ENHANCED LOGGING TEST COMPLETE ===" -ForegroundColor Yellow
Write-Host "Next: Check application logs for the specific patterns mentioned above" -ForegroundColor Cyan