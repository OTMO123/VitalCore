# API Endpoints Diagnostic Script for IRIS API
# PowerShell version for detailed endpoint testing and error capture

param(
    [string]$BaseUrl = "http://localhost:8000",
    [switch]$Verbose,
    [switch]$SaveLogs
)

# Global variables for tracking
$script:TotalTests = 0
$script:PassedTests = 0
$script:FailedTests = 0
$script:TestResults = @()
$script:AuthToken = $null
$script:TestPatientId = $null

function Write-TestLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss.fff"
    $icons = @{
        "INFO" = "ℹ️"
        "PASS" = "✅" 
        "FAIL" = "❌"
        "WARN" = "⚠️"
        "DEBUG" = "🔍"
        "ERROR" = "💥"
    }
    
    $icon = $icons[$Level]
    $logEntry = "[$timestamp] $icon $Message"
    
    Write-Host $logEntry -ForegroundColor $(
        switch ($Level) {
            "PASS" { "Green" }
            "FAIL" { "Red" }
            "WARN" { "Yellow" }
            "DEBUG" { "Cyan" }
            "ERROR" { "Magenta" }
            default { "White" }
        }
    )
    
    # Store in results for later analysis
    $script:TestResults += @{
        Timestamp = $timestamp
        Level = $Level
        Message = $Message
    }
}

function Invoke-ApiRequest {
    param(
        [string]$Method,
        [string]$Endpoint,
        [hashtable]$Headers = @{},
        [object]$Body = $null,
        [string]$ContentType = "application/json"
    )
    
    $url = "$BaseUrl$Endpoint"
    $script:TotalTests++
    
    Write-TestLog "🔍 $Method $Endpoint" "DEBUG"
    
    try {
        $requestParams = @{
            Uri = $url
            Method = $Method
            Headers = $Headers
            TimeoutSec = 30
            UseBasicParsing = $true
        }
        
        if ($Body) {
            if ($ContentType -eq "application/x-www-form-urlencoded") {
                $requestParams.Body = $Body
                $requestParams.ContentType = $ContentType
            } else {
                $requestParams.Body = ($Body | ConvertTo-Json -Depth 10)
                $requestParams.ContentType = "application/json"
            }
        }
        
        $response = Invoke-WebRequest @requestParams
        
        # Parse response
        $responseData = try {
            $response.Content | ConvertFrom-Json
        } catch {
            @{ raw_response = $response.Content.Substring(0, [Math]::Min(500, $response.Content.Length)) }
        }
        
        Write-TestLog "✅ Response: $($response.StatusCode)" "DEBUG"
        
        return @{
            Success = $true
            StatusCode = $response.StatusCode
            Data = $responseData
            Headers = $response.Headers
        }
        
    } catch {
        $errorDetails = $_.Exception.Message
        $statusCode = 0
        $responseData = @{ error = $errorDetails }
        
        # Extract status code if available
        if ($_.Exception -is [System.Net.WebException]) {
            if ($_.Exception.Response) {
                $statusCode = [int]$_.Exception.Response.StatusCode
                try {
                    $stream = $_.Exception.Response.GetResponseStream()
                    $reader = New-Object System.IO.StreamReader($stream)
                    $responseText = $reader.ReadToEnd()
                    $responseData = $responseText | ConvertFrom-Json
                } catch {
                    $responseData = @{ error = $errorDetails, raw_response = $responseText }
                }
            }
        }
        
        Write-TestLog "❌ ERROR: $Method $Endpoint - $errorDetails" "ERROR"
        
        if ($Verbose -and $statusCode -ge 400) {
            Write-TestLog "   Status Code: $statusCode" "ERROR"
            Write-TestLog "   Response: $($responseData | ConvertTo-Json -Depth 3)" "ERROR"
        }
        
        return @{
            Success = $false
            StatusCode = $statusCode
            Data = $responseData
            Error = $errorDetails
        }
    }
}

function Test-Authentication {
    Write-TestLog "🔐 Testing Authentication" "INFO"
    
    $authData = "username=admin&password=admin123"
    $headers = @{}
    
    $result = Invoke-ApiRequest -Method "POST" -Endpoint "/api/v1/auth/login" -Body $authData -ContentType "application/x-www-form-urlencoded"
    
    if ($result.Success -and $result.StatusCode -eq 200 -and $result.Data.access_token) {
        $script:AuthToken = $result.Data.access_token
        $script:PassedTests++
        Write-TestLog "Authentication successful" "PASS"
        return $true
    } else {
        $script:FailedTests++
        Write-TestLog "Authentication failed: $($result.StatusCode) - $($result.Data | ConvertTo-Json)" "FAIL"
        return $false
    }
}

function Get-AuthHeaders {
    if ($script:AuthToken) {
        return @{ "Authorization" = "Bearer $script:AuthToken" }
    }
    return @{}
}

function Test-DocumentsHealth {
    Write-TestLog "📄 Testing Documents Health Endpoint" "INFO"
    
    $headers = Get-AuthHeaders
    $result = Invoke-ApiRequest -Method "GET" -Endpoint "/api/v1/documents/health" -Headers $headers
    
    if ($result.Success -and $result.StatusCode -eq 200) {
        $script:PassedTests++
        Write-TestLog "Documents health OK: $($result.Data.status)" "PASS"
        return $true
    } else {
        $script:FailedTests++
        Write-TestLog "Documents health failed: $($result.StatusCode) - $($result.Data | ConvertTo-Json)" "FAIL"
        
        # Additional 5 Whys analysis for documents health
        Write-TestLog "🔍 5 WHYS ANALYSIS - Documents Health:" "DEBUG"
        Write-TestLog "   Why 1: Status $($result.StatusCode) suggests routing or auth issue" "DEBUG"
        Write-TestLog "   Why 2: Check if health endpoint is before parameterized routes" "DEBUG"
        Write-TestLog "   Why 3: Verify authentication token is valid" "DEBUG"
        Write-TestLog "   Why 4: Check if document services can instantiate" "DEBUG"
        Write-TestLog "   Why 5: Verify all dependencies are available" "DEBUG"
        
        return $false
    }
}

function Test-CreatePatient {
    Write-TestLog "👤 Testing Patient Creation" "INFO"
    
    $headers = Get-AuthHeaders
    $patientData = @{
        resourceType = "Patient"
        identifier = @(@{ value = "TEST-API-$(Get-Random)" })
        name = @(@{ family = "ApiTest"; given = @("Diagnostic") })
        gender = "male"
        birthDate = "1990-01-01"
        active = $true
        organization_id = "550e8400-e29b-41d4-a716-446655440000"
        consent_status = "pending"
        consent_types = @("treatment")
    }
    
    $result = Invoke-ApiRequest -Method "POST" -Endpoint "/api/v1/healthcare/patients" -Headers $headers -Body $patientData
    
    if ($result.Success -and $result.StatusCode -eq 201) {
        $script:TestPatientId = $result.Data.id
        $script:PassedTests++
        Write-TestLog "Patient created successfully: $script:TestPatientId" "PASS"
        return $true
    } else {
        $script:FailedTests++
        Write-TestLog "Patient creation failed: $($result.StatusCode) - $($result.Data | ConvertTo-Json)" "FAIL"
        return $false
    }
}

function Test-GetPatient {
    if (-not $script:TestPatientId) {
        Write-TestLog "⚠️ No patient ID available for get test" "WARN"
        return $false
    }
    
    Write-TestLog "👤 Testing Get Patient by ID: $script:TestPatientId" "INFO"
    
    $headers = Get-AuthHeaders
    $result = Invoke-ApiRequest -Method "GET" -Endpoint "/api/v1/healthcare/patients/$script:TestPatientId" -Headers $headers
    
    if ($result.Success -and $result.StatusCode -eq 200) {
        $script:PassedTests++
        Write-TestLog "Get patient successful" "PASS"
        return $true
    } else {
        $script:FailedTests++
        Write-TestLog "Get patient failed: $($result.StatusCode) - $($result.Data | ConvertTo-Json)" "FAIL"
        
        # 5 Whys analysis for get patient failure
        Write-TestLog "🔍 5 WHYS ANALYSIS - Get Patient:" "DEBUG"
        Write-TestLog "   Why 1: Status $($result.StatusCode) indicates server error" "DEBUG"
        Write-TestLog "   Why 2: Check if dependency injection is correct (verify_token vs get_current_user_id)" "DEBUG"
        Write-TestLog "   Why 3: Verify database imports (database_unified vs database_advanced)" "DEBUG"
        Write-TestLog "   Why 4: Check if service layer can access patient data" "DEBUG"
        Write-TestLog "   Why 5: Verify patient model fields match API expectations" "DEBUG"
        
        return $false
    }
}

function Test-UpdatePatient {
    if (-not $script:TestPatientId) {
        Write-TestLog "⚠️ No patient ID available for update test" "WARN"
        return $false
    }
    
    Write-TestLog "✏️ Testing Update Patient: $script:TestPatientId" "INFO"
    
    $headers = Get-AuthHeaders
    $updateData = @{
        gender = "female"
        consent_status = "active"
    }
    
    $result = Invoke-ApiRequest -Method "PUT" -Endpoint "/api/v1/healthcare/patients/$script:TestPatientId" -Headers $headers -Body $updateData
    
    if ($result.Success -and $result.StatusCode -eq 200) {
        $script:PassedTests++
        Write-TestLog "Update patient successful" "PASS"
        return $true
    } else {
        $script:FailedTests++
        Write-TestLog "Update patient failed: $($result.StatusCode) - $($result.Data | ConvertTo-Json)" "FAIL"
        
        # 5 Whys analysis for update patient failure
        Write-TestLog "🔍 5 WHYS ANALYSIS - Update Patient:" "DEBUG"
        Write-TestLog "   Why 1: Status $($result.StatusCode) suggests database or service error" "DEBUG"
        Write-TestLog "   Why 2: Check if database imports are correct" "DEBUG"
        Write-TestLog "   Why 3: Verify patient model has required fields for update" "DEBUG"
        Write-TestLog "   Why 4: Check if update validation is working" "DEBUG"
        Write-TestLog "   Why 5: Verify encryption service is available" "DEBUG"
        
        return $false
    }
}

function Test-AuditLogs {
    Write-TestLog "📋 Testing Audit Logs Endpoint" "INFO"
    
    $headers = Get-AuthHeaders
    $result = Invoke-ApiRequest -Method "GET" -Endpoint "/api/v1/audit/logs" -Headers $headers
    
    if ($result.Success -and $result.StatusCode -eq 200) {
        $script:PassedTests++
        Write-TestLog "Audit logs successful" "PASS"
        return $true
    } else {
        $script:FailedTests++
        Write-TestLog "Audit logs failed: $($result.StatusCode) - $($result.Data | ConvertTo-Json)" "FAIL"
        
        # 5 Whys analysis for audit logs failure
        Write-TestLog "🔍 5 WHYS ANALYSIS - Audit Logs:" "DEBUG"
        Write-TestLog "   Why 1: Status $($result.StatusCode) indicates service unavailability" "DEBUG"
        Write-TestLog "   Why 2: Check if audit service is properly initialized" "DEBUG"
        Write-TestLog "   Why 3: Verify audit database tables exist" "DEBUG"
        Write-TestLog "   Why 4: Check if audit logger dependencies are available" "DEBUG"
        Write-TestLog "   Why 5: Verify audit service configuration" "DEBUG"
        
        return $false
    }
}

function Test-ErrorHandling {
    Write-TestLog "⚠️ Testing Error Handling (Non-existent Patient)" "INFO"
    
    $headers = Get-AuthHeaders
    $fakeId = "00000000-0000-0000-0000-000000000000"
    
    $result = Invoke-ApiRequest -Method "GET" -Endpoint "/api/v1/healthcare/patients/$fakeId" -Headers $headers
    
    if ($result.StatusCode -eq 404) {
        $script:PassedTests++
        Write-TestLog "Error handling correct: 404 for non-existent patient" "PASS"
        return $true
    } else {
        $script:FailedTests++
        Write-TestLog "Error handling incorrect: Expected 404, got $($result.StatusCode)" "FAIL"
        
        # 5 Whys analysis for error handling
        Write-TestLog "🔍 5 WHYS ANALYSIS - Error Handling:" "DEBUG"
        Write-TestLog "   Why 1: Should return 404, got $($result.StatusCode)" "DEBUG"
        Write-TestLog "   Why 2: Check if proper exception handling exists" "DEBUG"
        Write-TestLog "   Why 3: Verify database query handles non-existent records" "DEBUG"
        Write-TestLog "   Why 4: Check if service layer returns appropriate errors" "DEBUG"
        Write-TestLog "   Why 5: Verify error mapping in router" "DEBUG"
        
        return $false
    }
}

function Test-AllHealthEndpoints {
    Write-TestLog "🏥 Testing All Health Endpoints" "INFO"
    
    $healthEndpoints = @(
        "/health",
        "/api/v1/healthcare/health",
        "/api/v1/dashboard/health", 
        "/api/v1/audit/health",
        "/api/v1/documents/health",
        "/api/v1/analytics/health",
        "/api/v1/patients/risk/health",
        "/api/v1/purge/health",
        "/api/v1/iris/health"
    )
    
    $healthResults = @{}
    $headers = Get-AuthHeaders
    
    foreach ($endpoint in $healthEndpoints) {
        $result = Invoke-ApiRequest -Method "GET" -Endpoint $endpoint -Headers $headers
        $healthResults[$endpoint] = $result.Success -and $result.StatusCode -eq 200
        
        if ($healthResults[$endpoint]) {
            Write-TestLog "✅ $endpoint - OK" "PASS"
        } else {
            Write-TestLog "❌ $endpoint - FAIL ($($result.StatusCode))" "FAIL"
        }
    }
    
    $healthyCount = ($healthResults.Values | Where-Object { $_ }).Count
    $totalHealth = $healthResults.Count
    $healthRate = [math]::Round(($healthyCount / $totalHealth) * 100, 1)
    
    Write-TestLog "Health endpoints: $healthyCount/$totalHealth ($healthRate%)" "INFO"
    
    return $healthRate -ge 80
}

function Write-ComprehensiveAnalysis {
    Write-TestLog "📊 COMPREHENSIVE 5 WHYS ANALYSIS" "INFO"
    Write-Host "=" * 80
    
    $successRate = if ($script:TotalTests -gt 0) { 
        [math]::Round(($script:PassedTests / $script:TotalTests) * 100, 1) 
    } else { 0 }
    
    Write-TestLog "🎯 OVERALL RESULTS:" "INFO"
    Write-TestLog "  Total Tests: $script:TotalTests" "INFO"
    Write-TestLog "  Passed: $script:PassedTests" "PASS"
    Write-TestLog "  Failed: $script:FailedTests" "FAIL" 
    Write-TestLog "  Success Rate: $successRate%" "INFO"
    
    Write-Host ""
    Write-TestLog "🔍 ROOT CAUSE ANALYSIS:" "INFO"
    
    if ($script:FailedTests -eq 0) {
        Write-TestLog "🎉 ALL TESTS PASSED - READY FOR DEPLOYMENT!" "PASS"
    } elseif ($successRate -ge 90) {
        Write-TestLog "✅ EXCELLENT - Minor issues only" "PASS"
        Write-TestLog "Recommendation: Review failed tests and deploy" "INFO"
    } elseif ($successRate -ge 70) {
        Write-TestLog "⚠️ GOOD - Some issues need fixing" "WARN"
        Write-TestLog "Recommendation: Fix failed endpoints before deployment" "WARN"
    } else {
        Write-TestLog "❌ NEEDS WORK - Major issues detected" "FAIL"
        Write-TestLog "Recommendation: Systematic debugging required" "FAIL"
        
        # Provide specific guidance
        Write-TestLog "🔧 SPECIFIC FIXES NEEDED:" "INFO"
        Write-TestLog "1. Check Docker services are running" "INFO"
        Write-TestLog "2. Verify database connectivity" "INFO"
        Write-TestLog "3. Fix import errors (database_unified vs database_advanced)" "INFO"
        Write-TestLog "4. Correct dependency injection issues" "INFO"
        Write-TestLog "5. Ensure service layer properly handles encryption/decryption" "INFO"
    }
    
    return $successRate
}

function Save-DiagnosticReport {
    param([double]$SuccessRate)
    
    if ($SaveLogs) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $reportFile = "diagnostic_scripts\api_test_report_$timestamp.json"
        
        $report = @{
            timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            success_rate = $SuccessRate
            total_tests = $script:TotalTests
            passed_tests = $script:PassedTests
            failed_tests = $script:FailedTests
            test_results = $script:TestResults
            recommendations = @(
                "Fix database import issues",
                "Correct dependency injection",
                "Ensure Docker services running",
                "Verify authentication flow"
            )
        }
        
        $report | ConvertTo-Json -Depth 10 | Out-File -FilePath $reportFile -Encoding UTF8
        Write-TestLog "📄 Diagnostic report saved: $reportFile" "INFO"
    }
}

# Main execution
Write-Host "🧪 IRIS API ENDPOINT DIAGNOSTICS" -ForegroundColor Cyan
Write-Host "=" * 80
Write-TestLog "Starting comprehensive API endpoint testing..." "INFO"
Write-TestLog "Base URL: $BaseUrl" "INFO"
Write-TestLog "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "INFO"
Write-Host ""

# Execute all tests
$authOk = Test-Authentication

if ($authOk) {
    Write-Host ""
    $docsHealthOk = Test-DocumentsHealth
    $createPatientOk = Test-CreatePatient
    $getPatientOk = Test-GetPatient
    $updatePatientOk = Test-UpdatePatient
    $auditLogsOk = Test-AuditLogs
    $errorHandlingOk = Test-ErrorHandling
    
    Write-Host ""
    $healthEndpointsOk = Test-AllHealthEndpoints
} else {
    Write-TestLog "❌ Cannot continue without authentication" "FAIL"
}

Write-Host ""
$finalSuccessRate = Write-ComprehensiveAnalysis
Save-DiagnosticReport -SuccessRate $finalSuccessRate

# Exit with appropriate code
if ($finalSuccessRate -eq 100) {
    Write-TestLog "🚀 SYSTEM READY FOR DEPLOYMENT!" "PASS"
    exit 0
} elseif ($finalSuccessRate -ge 80) {
    Write-TestLog "⚠️ MOSTLY READY - Minor fixes needed" "WARN"
    exit 1
} else {
    Write-TestLog "❌ NOT READY - Major fixes required" "FAIL"
    exit 2
}