# Healthcare API Endpoint Health Check
# Tests all critical API endpoints to verify functionality

Write-Host "🏥 HEALTHCARE API ENDPOINT HEALTH CHECK" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

$baseUrl = "http://localhost:8000"
$results = @()
$passed = 0
$failed = 0

# Test endpoint function
function Test-Endpoint {
    param(
        [string]$Method,
        [string]$Path,
        [string]$Name,
        [hashtable]$Headers = @{},
        [object]$Body = $null,
        [int]$ExpectedStatus = 200
    )
    
    $url = "$baseUrl$Path"
    $startTime = Get-Date
    
    try {
        $response = $null
        if ($Method -eq "GET") {
            $response = Invoke-RestMethod -Uri $url -Method $Method -Headers $Headers -ErrorAction Stop
        } elseif ($Method -eq "POST") {
            if ($Body) {
                $bodyJson = $Body | ConvertTo-Json
                $response = Invoke-RestMethod -Uri $url -Method $Method -Headers $Headers -Body $bodyJson -ContentType "application/json" -ErrorAction Stop
            } else {
                $response = Invoke-RestMethod -Uri $url -Method $Method -Headers $Headers -ErrorAction Stop
            }
        }
        
        $endTime = Get-Date
        $responseTime = ($endTime - $startTime).TotalMilliseconds
        
        Write-Host "✅ $Method $Path - $([math]::Round($responseTime, 2))ms" -ForegroundColor Green
        return @{
            Success = $true
            Method = $Method
            Path = $Path
            Name = $Name
            ResponseTime = $responseTime
            Status = "Success"
        }
    }
    catch {
        $endTime = Get-Date
        $responseTime = ($endTime - $startTime).TotalMilliseconds
        $errorMsg = $_.Exception.Message
        
        Write-Host "❌ $Method $Path - Error: $errorMsg" -ForegroundColor Red
        return @{
            Success = $false
            Method = $Method
            Path = $Path
            Name = $Name
            ResponseTime = $responseTime
            Status = "Failed"
            Error = $errorMsg
        }
    }
}

Write-Host "`n🔍 Testing Public Endpoints..." -ForegroundColor Yellow

# Test public endpoints (no auth required)
$publicEndpoints = @(
    @{ Method = "GET"; Path = "/health"; Name = "Basic Health Check" },
    @{ Method = "GET"; Path = "/health/detailed"; Name = "Detailed Health Check" },
    @{ Method = "GET"; Path = "/docs"; Name = "API Documentation" },
    @{ Method = "GET"; Path = "/openapi.json"; Name = "OpenAPI Schema" }
)

foreach ($endpoint in $publicEndpoints) {
    $result = Test-Endpoint -Method $endpoint.Method -Path $endpoint.Path -Name $endpoint.Name
    $results += $result
    if ($result.Success) { $passed++ } else { $failed++ }
}

Write-Host "`n🔐 Testing Authentication..." -ForegroundColor Yellow

# Test authentication
$authData = @{
    username = "admin"
    password = "admin123"
}

$authResult = Test-Endpoint -Method "POST" -Path "/api/v1/auth/login" -Name "User Login" -Body $authData
$results += $authResult
if ($authResult.Success) { $passed++ } else { $failed++ }

# Get auth token if login successful
$authToken = $null
if ($authResult.Success) {
    try {
        $authResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/login" -Method POST -Body ($authData | ConvertTo-Json) -ContentType "application/json"
        $authToken = $authResponse.access_token
        Write-Host "🔑 Authentication token obtained" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ Could not extract auth token" -ForegroundColor Yellow
    }
}

if ($authToken) {
    Write-Host "`n🔒 Testing Protected Endpoints..." -ForegroundColor Yellow
    
    $authHeaders = @{
        "Authorization" = "Bearer $authToken"
    }
    
    # Test protected endpoints
    $protectedEndpoints = @(
        @{ Method = "GET"; Path = "/api/v1/auth/me"; Name = "Get Current User" },
        @{ Method = "GET"; Path = "/api/v1/patients"; Name = "List Patients" },
        @{ Method = "GET"; Path = "/api/v1/clinical-workflows"; Name = "List Clinical Workflows" },
        @{ Method = "GET"; Path = "/api/v1/audit-logs"; Name = "List Audit Logs" },
        @{ Method = "GET"; Path = "/api/v1/iris"; Name = "IRIS API Status" },
        @{ Method = "GET"; Path = "/api/v1/analytics/dashboard"; Name = "Analytics Dashboard" },
        @{ Method = "GET"; Path = "/api/v1/documents"; Name = "List Documents" }
    )
    
    foreach ($endpoint in $protectedEndpoints) {
        $result = Test-Endpoint -Method $endpoint.Method -Path $endpoint.Path -Name $endpoint.Name -Headers $authHeaders
        $results += $result
        if ($result.Success) { $passed++ } else { $failed++ }
    }
} else {
    Write-Host "⚠️ Skipping protected endpoint tests - no auth token" -ForegroundColor Yellow
}

Write-Host "`n🏥 Testing Healthcare-Specific Endpoints..." -ForegroundColor Yellow

# Test healthcare endpoints
$healthcareEndpoints = @(
    @{ Method = "GET"; Path = "/api/v1/clinical-workflows/health"; Name = "Clinical Workflows Health" },
    @{ Method = "GET"; Path = "/api/v1/iris/health"; Name = "IRIS Health Check" },
    @{ Method = "GET"; Path = "/api/v1/risk-stratification/health"; Name = "Risk Stratification Health" }
)

foreach ($endpoint in $healthcareEndpoints) {
    $result = Test-Endpoint -Method $endpoint.Method -Path $endpoint.Path -Name $endpoint.Name
    $results += $result
    if ($result.Success) { $passed++ } else { $failed++ }
}

# Generate summary report
$total = $passed + $failed
$successRate = if ($total -gt 0) { [math]::Round(($passed / $total) * 100, 1) } else { 0 }

Write-Host "`n📊 SUMMARY REPORT" -ForegroundColor Cyan
Write-Host "=================" -ForegroundColor Cyan
Write-Host "Total Tests: $total" -ForegroundColor White
Write-Host "✅ Passed: $passed" -ForegroundColor Green
Write-Host "❌ Failed: $failed" -ForegroundColor Red
Write-Host "📈 Success Rate: $successRate%" -ForegroundColor $(if ($successRate -ge 80) { "Green" } elseif ($successRate -ge 60) { "Yellow" } else { "Red" })

if ($failed -gt 0) {
    Write-Host "`n⚠️ Failed Endpoints:" -ForegroundColor Yellow
    $results | Where-Object { -not $_.Success } | ForEach-Object {
        Write-Host "   $($_.Method) $($_.Path) - $($_.Error)" -ForegroundColor Red
    }
}

# Save results to file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportFile = "api_health_report_$timestamp.json"
$reportData = @{
    timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    total_tests = $total
    passed = $passed
    failed = $failed
    success_rate = $successRate
    results = $results
}

$reportData | ConvertTo-Json -Depth 3 | Out-File -FilePath $reportFile -Encoding UTF8
Write-Host "`n💾 Report saved to: $reportFile" -ForegroundColor Cyan

if ($successRate -eq 100) {
    Write-Host "`n🎉 ALL ENDPOINTS ARE WORKING PERFECTLY!" -ForegroundColor Green
} elseif ($successRate -ge 80) {
    Write-Host "`n👍 Most endpoints are working well!" -ForegroundColor Green
} else {
    Write-Host "`n🔧 Some endpoints need attention!" -ForegroundColor Yellow
}

Write-Host "`nRun this script regularly to monitor API health!" -ForegroundColor Cyan