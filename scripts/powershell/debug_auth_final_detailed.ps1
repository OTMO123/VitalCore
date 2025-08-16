# Ultra-Detailed Authentication Debug - Capture EXACT Error
Write-Host "=== FINAL DETAILED AUTHENTICATION DEBUG ===" -ForegroundColor Yellow
Write-Host "Goal: Find EXACT reason authentication fails after Unicode fix" -ForegroundColor Cyan

$apiUrl = "http://localhost:8000/api/v1/auth/login"
$credentials = @{
    username = "admin"
    password = "admin123"
}

# Test 1: Basic connectivity
Write-Host "`n--- TEST 1: Server Connectivity ---" -ForegroundColor Green
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5
    Write-Host "✓ Server is reachable" -ForegroundColor Green
    Write-Host "Health Status: $($healthResponse.status)" -ForegroundColor White
} catch {
    Write-Host "✗ Server connectivity FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 2: API Documentation Access
Write-Host "`n--- TEST 2: API Documentation ---" -ForegroundColor Green
try {
    $docsResponse = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method GET -TimeoutSec 5
    Write-Host "✓ API docs accessible (Status: $($docsResponse.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "✗ API docs not accessible" -ForegroundColor Red
}

# Test 3: Auth endpoint existence
Write-Host "`n--- TEST 3: Auth Endpoint Check ---" -ForegroundColor Green
try {
    $openApiResponse = Invoke-RestMethod -Uri "http://localhost:8000/openapi.json" -Method GET -TimeoutSec 5
    $authPaths = $openApiResponse.paths | Get-Member -MemberType NoteProperty | Where-Object {$_.Name -like "*auth*"}
    Write-Host "✓ OpenAPI spec retrieved" -ForegroundColor Green
    Write-Host "Auth endpoints found:" -ForegroundColor White
    $authPaths | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Gray }
} catch {
    Write-Host "✗ Could not retrieve OpenAPI spec" -ForegroundColor Red
}

# Test 4: Authentication attempt with FULL error capture
Write-Host "`n--- TEST 4: Authentication Attempt ---" -ForegroundColor Green
Write-Host "URL: $apiUrl" -ForegroundColor Cyan
Write-Host "Payload: $($credentials | ConvertTo-Json)" -ForegroundColor Cyan

try {
    # Create web request manually for better error handling
    $request = [System.Net.WebRequest]::Create($apiUrl)
    $request.Method = "POST"
    $request.ContentType = "application/json"
    $request.Timeout = 10000
    
    # Convert credentials to JSON bytes
    $jsonPayload = $credentials | ConvertTo-Json
    $payloadBytes = [System.Text.Encoding]::UTF8.GetBytes($jsonPayload)
    $request.ContentLength = $payloadBytes.Length
    
    # Write payload
    $requestStream = $request.GetRequestStream()
    $requestStream.Write($payloadBytes, 0, $payloadBytes.Length)
    $requestStream.Close()
    
    # Get response
    $response = $request.GetResponse()
    $responseStream = $response.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($responseStream)
    $responseText = $reader.ReadToEnd()
    $reader.Close()
    $responseStream.Close()
    $response.Close()
    
    Write-Host "✓ SUCCESS: Authentication worked!" -ForegroundColor Green
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Green
    Write-Host $responseText -ForegroundColor White
    
} catch [System.Net.WebException] {
    $webException = $_.Exception
    Write-Host "✗ AUTHENTICATION FAILED - WebException Details:" -ForegroundColor Red
    
    # Get HTTP status
    if ($webException.Response) {
        $statusCode = [int]$webException.Response.StatusCode
        $statusDescription = $webException.Response.StatusDescription
        
        Write-Host "HTTP Status: $statusCode ($statusDescription)" -ForegroundColor Yellow
        
        # Get response body
        $responseStream = $webException.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($responseStream)
        $errorResponseText = $reader.ReadToEnd()
        $reader.Close()
        $responseStream.Close()
        
        Write-Host "Error Response Body:" -ForegroundColor Yellow
        Write-Host $errorResponseText -ForegroundColor Red
        
        # Try to parse as JSON
        try {
            $errorJson = $errorResponseText | ConvertFrom-Json
            Write-Host "Parsed Error Details:" -ForegroundColor Yellow
            Write-Host "  Message: $($errorJson.detail)" -ForegroundColor Red
            if ($errorJson.errors) {
                Write-Host "  Validation Errors:" -ForegroundColor Red
                $errorJson.errors | ForEach-Object {
                    Write-Host "    - $($_)" -ForegroundColor Red
                }
            }
        } catch {
            Write-Host "Could not parse error response as JSON" -ForegroundColor Gray
        }
        
        # 5 Whys Analysis based on status code
        Write-Host "`n--- 5 WHYS ANALYSIS ---" -ForegroundColor Yellow
        switch ($statusCode) {
            400 {
                Write-Host "Why #1: 400 Bad Request - Malformed request data"
                Write-Host "Why #2: Request validation failed - check JSON format"
                Write-Host "Why #3: Schema mismatch - verify UserLogin schema"
                Write-Host "Why #4: FastAPI validation error - check Pydantic models"
                Write-Host "Why #5: ROOT CAUSE: Authentication schema incompatibility"
            }
            401 {
                Write-Host "Why #1: 401 Unauthorized - Invalid credentials"
                Write-Host "Why #2: User authentication failed - password/username wrong"
                Write-Host "Why #3: Database lookup failed - user not found or password hash mismatch"
                Write-Host "Why #4: Password verification failed - bcrypt/hashing issue"
                Write-Host "Why #5: ROOT CAUSE: Credential verification process broken"
            }
            422 {
                Write-Host "Why #1: 422 Unprocessable Entity - Validation error"
                Write-Host "Why #2: Request data doesn't match expected schema"
                Write-Host "Why #3: UserLogin Pydantic model validation failed"
                Write-Host "Why #4: Field types or required fields mismatch"
                Write-Host "Why #5: ROOT CAUSE: API schema definition problem"
            }
            500 {
                Write-Host "Why #1: 500 Internal Server Error - Server-side exception"
                Write-Host "Why #2: Unhandled exception in authentication logic"
                Write-Host "Why #3: Database connection or query failure"
                Write-Host "Why #4: Service dependency failure (event bus, logging, etc.)"
                Write-Host "Why #5: ROOT CAUSE: Application runtime error"
            }
            default {
                Write-Host "Why #1: Unexpected HTTP status $statusCode"
                Write-Host "Why #2: Unknown server behavior"
                Write-Host "Why #3: Possible proxy/network issue"
                Write-Host "Why #4: Server misconfiguration"
                Write-Host "Why #5: ROOT CAUSE: Investigation needed for status $statusCode"
            }
        }
    } else {
        Write-Host "No HTTP response received" -ForegroundColor Red
        Write-Host "Connection Error: $($webException.Message)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "✗ UNEXPECTED ERROR:" -ForegroundColor Red
    Write-Host "Exception Type: $($_.Exception.GetType().Name)" -ForegroundColor Red
    Write-Host "Exception Message: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Full Exception:" -ForegroundColor Red
    Write-Host $_.Exception -ForegroundColor Red
}

Write-Host "`n=== DEBUG COMPLETE ===" -ForegroundColor Yellow
Write-Host "Next: Run this script to get EXACT error details, then analyze root cause" -ForegroundColor Cyan