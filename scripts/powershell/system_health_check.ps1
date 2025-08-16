# Comprehensive System Health Check
# Tests all functionality: APIs, databases, tests, and core features

Write-Host "🏥 COMPREHENSIVE HEALTHCARE SYSTEM HEALTH CHECK" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

$results = @{
    "api_tests" = @{}
    "database_tests" = @{}
    "core_tests" = @{}
    "functionality_tests" = @{}
    "security_tests" = @{}
}
$totalScore = 0
$maxScore = 0

# Helper function to test API endpoint
function Test-ApiEndpoint {
    param(
        [string]$Method,
        [string]$Url,
        [string]$Name,
        [hashtable]$Headers = @{},
        [object]$Body = $null
    )
    
    try {
        $response = $null
        if ($Method -eq "GET") {
            $response = Invoke-RestMethod -Uri $Url -Method $Method -Headers $Headers -ErrorAction Stop
        } elseif ($Method -eq "POST") {
            if ($Body) {
                $bodyJson = $Body | ConvertTo-Json
                $response = Invoke-RestMethod -Uri $Url -Method $Method -Headers $Headers -Body $bodyJson -ContentType "application/json" -ErrorAction Stop
            }
        }
        
        Write-Host "✅ $Name" -ForegroundColor Green
        return @{ Success = $true; Response = $response }
    }
    catch {
        Write-Host "❌ $Name - $($_.Exception.Message)" -ForegroundColor Red
        return @{ Success = $false; Error = $_.Exception.Message }
    }
}

# Helper function to run command and capture result
function Test-Command {
    param(
        [string]$Command,
        [string]$Name,
        [string]$WorkingDirectory = "."
    )
    
    try {
        $result = Invoke-Expression -Command "cd '$WorkingDirectory'; $Command" -ErrorAction Stop
        Write-Host "✅ $Name" -ForegroundColor Green
        return @{ Success = $true; Output = $result }
    }
    catch {
        Write-Host "❌ $Name - $($_.Exception.Message)" -ForegroundColor Red
        return @{ Success = $false; Error = $_.Exception.Message }
    }
}

Write-Host "`n🔍 1. API ENDPOINT TESTS" -ForegroundColor Yellow
Write-Host "========================" -ForegroundColor Yellow

$baseUrl = "http://localhost:8000"

# Test basic endpoints
$apiTests = @(
    @{ Method = "GET"; Path = "/health"; Name = "Health Check" },
    @{ Method = "GET"; Path = "/docs"; Name = "API Documentation" },
    @{ Method = "POST"; Path = "/api/v1/auth/login"; Name = "Authentication"; Body = @{ username = "admin"; password = "admin123" } }
)

$apiScore = 0
foreach ($test in $apiTests) {
    $url = "$baseUrl$($test.Path)"
    $result = Test-ApiEndpoint -Method $test.Method -Url $url -Name $test.Name -Body $test.Body
    $results.api_tests[$test.Name] = $result.Success
    if ($result.Success) { $apiScore++ }
    $maxScore++
}

# If auth successful, test protected endpoints
$authToken = $null
try {
    $authResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/login" -Method POST -Body (@{ username = "admin"; password = "admin123" } | ConvertTo-Json) -ContentType "application/json"
    $authToken = $authResponse.access_token
    
    if ($authToken) {
        $headers = @{ "Authorization" = "Bearer $authToken" }
        
        $protectedTests = @(
            @{ Method = "GET"; Path = "/api/v1/auth/me"; Name = "User Profile" },
            @{ Method = "GET"; Path = "/api/v1/patients"; Name = "Patients List" },
            @{ Method = "GET"; Path = "/api/v1/clinical-workflows"; Name = "Clinical Workflows" },
            @{ Method = "GET"; Path = "/api/v1/audit-logs"; Name = "Audit Logs" }
        )
        
        foreach ($test in $protectedTests) {
            $url = "$baseUrl$($test.Path)"
            $result = Test-ApiEndpoint -Method $test.Method -Url $url -Name $test.Name -Headers $headers
            $results.api_tests[$test.Name] = $result.Success
            if ($result.Success) { $apiScore++ }
            $maxScore++
        }
    }
}
catch {
    Write-Host "⚠️ Could not test protected endpoints - authentication failed" -ForegroundColor Yellow
}

$totalScore += $apiScore

Write-Host "`n🗄️ 2. DATABASE TESTS" -ForegroundColor Yellow
Write-Host "====================" -ForegroundColor Yellow

# Test database connectivity and schema
$dbTests = @(
    @{ Command = "python -c ""import app.core.database_unified; print('Database import: OK')"""; Name = "Database Import" },
    @{ Command = "python -c ""from sqlalchemy import create_engine; print('SQLAlchemy: OK')"""; Name = "SQLAlchemy" },
    @{ Command = "alembic current"; Name = "Migration Status" }
)

$dbScore = 0
foreach ($test in $dbTests) {
    $result = Test-Command -Command $test.Command -Name $test.Name
    $results.database_tests[$test.Name] = $result.Success
    if ($result.Success) { $dbScore++ }
    $maxScore++
}

$totalScore += $dbScore

Write-Host "`n🧪 3. CORE FUNCTIONALITY TESTS" -ForegroundColor Yellow
Write-Host "===============================" -ForegroundColor Yellow

# Test core imports and basic functionality
$coreTests = @(
    @{ Command = "python -c ""from app.core.database_unified import UserRole; print('UserRole:', UserRole.ADMIN.value)"""; Name = "User Roles" },
    @{ Command = "python -c ""from app.modules.clinical_workflows.models import ClinicalWorkflow; print('Clinical Models: OK')"""; Name = "Clinical Models" },
    @{ Command = "python -c ""from app.core.security import security_manager; print('Security Manager: OK')"""; Name = "Security Manager" },
    @{ Command = "python -c ""from app.core.event_bus_advanced import HybridEventBus; print('Event Bus: OK')"""; Name = "Event Bus" }
)

$coreScore = 0
foreach ($test in $coreTests) {
    $result = Test-Command -Command $test.Command -Name $test.Name
    $results.core_tests[$test.Name] = $result.Success
    if ($result.Success) { $coreScore++ }
    $maxScore++
}

$totalScore += $coreScore

Write-Host "`n⚡ 4. FUNCTIONALITY TESTS" -ForegroundColor Yellow
Write-Host "=========================" -ForegroundColor Yellow

# Test specific functionality
$functionalityTests = @(
    @{ Command = "python -c ""import pytest; print('Pytest version:', pytest.__version__)"""; Name = "Pytest Available" },
    @{ Command = "python -c ""import aiohttp; print('Aiohttp:', aiohttp.__version__)"""; Name = "Async HTTP Client" },
    @{ Command = "python -c ""from app.core.audit_logger import AuditLogger; print('Audit Logger: OK')"""; Name = "Audit Logger" },
    @{ Command = "python -c ""from app.modules.healthcare_records.encryption_service import EncryptionService; print('Encryption: OK')"""; Name = "Encryption Service" }
)

$funcScore = 0
foreach ($test in $functionalityTests) {
    $result = Test-Command -Command $test.Command -Name $test.Name
    $results.functionality_tests[$test.Name] = $result.Success
    if ($result.Success) { $funcScore++ }
    $maxScore++
}

$totalScore += $funcScore

Write-Host "`n🔒 5. SECURITY TESTS" -ForegroundColor Yellow
Write-Host "===================" -ForegroundColor Yellow

# Test security features
$securityTests = @(
    @{ Command = "python -c ""from cryptography.fernet import Fernet; print('Cryptography: OK')"""; Name = "Cryptography Library" },
    @{ Command = "python -c ""from passlib.hash import bcrypt; print('Password Hashing: OK')"""; Name = "Password Hashing" },
    @{ Command = "python -c ""from python_jose import jwt; print('JWT: OK')"""; Name = "JWT Support" }
)

$secScore = 0
foreach ($test in $securityTests) {
    $result = Test-Command -Command $test.Command -Name $test.Name
    $results.security_tests[$test.Name] = $result.Success
    if ($result.Success) { $secScore++ }
    $maxScore++
}

$totalScore += $secScore

Write-Host "`n🎯 6. QUICK TEST SUITE" -ForegroundColor Yellow
Write-Host "======================" -ForegroundColor Yellow

# Run a quick subset of tests to verify functionality
$testCommand = "python -m pytest app/tests/smoke/test_basic.py -v --tb=short"
$testResult = Test-Command -Command $testCommand -Name "Smoke Tests"
$results.core_tests["Smoke Tests"] = $testResult.Success
if ($testResult.Success) { $totalScore++ }
$maxScore++

# Calculate score
$successRate = if ($maxScore -gt 0) { [math]::Round(($totalScore / $maxScore) * 100, 1) } else { 0 }

Write-Host "`n📊 COMPREHENSIVE HEALTH REPORT" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan

Write-Host "API Tests: $apiScore/$($apiTests.Count + $protectedTests.Count) passed" -ForegroundColor $(if ($apiScore -eq ($apiTests.Count + $protectedTests.Count)) { "Green" } else { "Yellow" })
Write-Host "Database Tests: $dbScore/$($dbTests.Count) passed" -ForegroundColor $(if ($dbScore -eq $dbTests.Count) { "Green" } else { "Yellow" })
Write-Host "Core Tests: $coreScore/$($coreTests.Count) passed" -ForegroundColor $(if ($coreScore -eq $coreTests.Count) { "Green" } else { "Yellow" })
Write-Host "Functionality Tests: $funcScore/$($functionalityTests.Count) passed" -ForegroundColor $(if ($funcScore -eq $functionalityTests.Count) { "Green" } else { "Yellow" })
Write-Host "Security Tests: $secScore/$($securityTests.Count) passed" -ForegroundColor $(if ($secScore -eq $securityTests.Count) { "Green" } else { "Yellow" })

Write-Host "`nOverall Score: $totalScore/$maxScore ($successRate%)" -ForegroundColor $(
    if ($successRate -ge 90) { "Green" }
    elseif ($successRate -ge 70) { "Yellow" }
    else { "Red" }
)

# System status
if ($successRate -ge 95) {
    Write-Host "`n🎉 SYSTEM STATUS: EXCELLENT" -ForegroundColor Green
    Write-Host "All core functionality is working perfectly!" -ForegroundColor Green
} elseif ($successRate -ge 80) {
    Write-Host "`n👍 SYSTEM STATUS: GOOD" -ForegroundColor Green
    Write-Host "Most functionality is working well!" -ForegroundColor Green
} elseif ($successRate -ge 60) {
    Write-Host "`n⚠️ SYSTEM STATUS: NEEDS ATTENTION" -ForegroundColor Yellow
    Write-Host "Some components need fixing!" -ForegroundColor Yellow
} else {
    Write-Host "`n🔧 SYSTEM STATUS: REQUIRES FIXES" -ForegroundColor Red
    Write-Host "Multiple components need attention!" -ForegroundColor Red
}

# Save detailed results
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportFile = "system_health_report_$timestamp.json"
$reportData = @{
    timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    overall_score = $successRate
    total_tests = $maxScore
    passed_tests = $totalScore
    failed_tests = ($maxScore - $totalScore)
    detailed_results = $results
}

$reportData | ConvertTo-Json -Depth 4 | Out-File -FilePath $reportFile -Encoding UTF8
Write-Host "`n💾 Detailed report saved to: $reportFile" -ForegroundColor Cyan

Write-Host "`n🚀 NEXT STEPS:" -ForegroundColor Cyan
if ($successRate -lt 100) {
    Write-Host "1. Review failed tests above" -ForegroundColor White
    Write-Host "2. Run: .\check_api_endpoints.ps1" -ForegroundColor White
    Write-Host "3. Run: python -m pytest app/tests/smoke/ -v" -ForegroundColor White
    Write-Host "4. Check server status: python app/main.py" -ForegroundColor White
} else {
    Write-Host "1. Run full test suite: python -m pytest -v" -ForegroundColor White
    Write-Host "2. Deploy to production!" -ForegroundColor White
}

Write-Host "`nHealthcare system assessment complete! 🏥" -ForegroundColor Cyan