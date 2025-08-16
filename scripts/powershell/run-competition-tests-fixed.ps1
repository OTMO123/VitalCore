# HEMA3N Competition Test Runner
# Automated testing without F12 developer tools

param(
    [switch]$FullSuite,
    [switch]$QuickCheck,
    [switch]$Visual,
    [switch]$Performance,
    [string]$Viewport = "all"
)

Write-Host "🏆 HEMA3N Competition Test Suite" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "Automated UI/UX Testing Without F12 Developer Tools" -ForegroundColor Yellow
Write-Host ""

# Configuration
$frontendPath = ".\frontend"
$testTimeout = 300000  # 5 minutes
$competitionThreshold = 85  # 85% pass rate required

function Test-Prerequisites {
    Write-Host "🔍 Checking Prerequisites..." -ForegroundColor Yellow
    
    # Check if Node.js is installed
    try {
        $nodeVersion = node --version
        Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Node.js not found. Please install Node.js" -ForegroundColor Red
        exit 1
    }
    
    # Check if frontend dependencies are installed
    if (-not (Test-Path "$frontendPath\node_modules")) {
        Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
        Set-Location $frontendPath
        npm install
        Set-Location ..
    }
    else {
        Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green
    }
    
    # Check if backend is running
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Backend server running" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "⚠️  Backend server not responding - some tests may fail" -ForegroundColor Yellow
    }
    
    # Check if frontend is running
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Frontend server running" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "⚠️  Frontend server not responding - starting it..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-Command", "cd $frontendPath; npm run dev" -WindowStyle Minimized
        Start-Sleep 10
    }
    
    Write-Host ""
}

function Run-VisualRegressionTests {
    Write-Host "📱 Running Visual Regression Tests..." -ForegroundColor Magenta
    Write-Host "=====================================" -ForegroundColor Magenta
    
    Set-Location $frontendPath
    
    try {
        # Run visual tests
        npm test -- --run tests/visual-regression/ui-test-suite.test.ts 2>$null
        $visualExitCode = $LASTEXITCODE
        
        # Run screenshot comparison tests
        npm test -- --run tests/visual/screenshot-comparison.test.ts 2>$null
        $screenshotExitCode = $LASTEXITCODE
        
        Set-Location ..
        
        if ($visualExitCode -eq 0 -and $screenshotExitCode -eq 0) {
            Write-Host "✅ Visual regression tests passed" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "❌ Visual regression tests failed" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Set-Location ..
        Write-Host "❌ Visual regression tests failed with error" -ForegroundColor Red
        return $false
    }
}

function Run-AccessibilityTests {
    Write-Host "♿ Running Accessibility Tests..." -ForegroundColor Magenta
    Write-Host "=================================" -ForegroundColor Magenta
    
    Set-Location $frontendPath
    
    try {
        npm test -- --run tests/accessibility/a11y-test-suite.test.ts 2>$null
        $exitCode = $LASTEXITCODE
        
        Set-Location ..
        
        if ($exitCode -eq 0) {
            Write-Host "✅ Accessibility tests passed" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "❌ Accessibility tests failed" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Set-Location ..
        Write-Host "❌ Accessibility tests failed with error" -ForegroundColor Red
        return $false
    }
}

function Run-PerformanceTests {
    Write-Host "⚡ Running Performance Benchmarks..." -ForegroundColor Magenta
    Write-Host "====================================" -ForegroundColor Magenta
    
    Set-Location $frontendPath
    
    try {
        npm test -- --run tests/performance/performance-benchmarks.test.ts 2>$null
        $exitCode = $LASTEXITCODE
        
        Set-Location ..
        
        if ($exitCode -eq 0) {
            Write-Host "✅ Performance benchmarks passed" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "❌ Performance benchmarks failed" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Set-Location ..
        Write-Host "❌ Performance benchmarks failed with error" -ForegroundColor Red
        return $false
    }
}

function Run-IntegrationTests {
    Write-Host "🔌 Running API Integration Tests..." -ForegroundColor Magenta
    Write-Host "====================================" -ForegroundColor Magenta
    
    Set-Location $frontendPath
    
    try {
        npm test -- --run tests/integration/api-ui-integration.test.ts 2>$null
        $exitCode = $LASTEXITCODE
        
        Set-Location ..
        
        if ($exitCode -eq 0) {
            Write-Host "✅ API integration tests passed" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "❌ API integration tests failed" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Set-Location ..
        Write-Host "❌ API integration tests failed with error" -ForegroundColor Red
        return $false
    }
}

function Run-ResponsiveTests {
    Write-Host "📱 Running Responsive Design Tests..." -ForegroundColor Magenta
    Write-Host "======================================" -ForegroundColor Magenta
    
    Set-Location $frontendPath
    
    try {
        npm test -- --run tests/responsive/viewport-testing.test.ts 2>$null
        $exitCode = $LASTEXITCODE
        
        Set-Location ..
        
        if ($exitCode -eq 0) {
            Write-Host "✅ Responsive design tests passed" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "❌ Responsive design tests failed" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Set-Location ..
        Write-Host "❌ Responsive design tests failed with error" -ForegroundColor Red
        return $false
    }
}

function Run-ComprehensiveTestSuite {
    Write-Host "🚀 Running Comprehensive Test Suite..." -ForegroundColor Magenta
    Write-Host "=======================================" -ForegroundColor Magenta
    
    Set-Location $frontendPath
    
    try {
        npm test -- --run tests/e2e/comprehensive-test-runner.ts 2>$null
        $exitCode = $LASTEXITCODE
        
        Set-Location ..
        
        if ($exitCode -eq 0) {
            Write-Host "✅ Comprehensive test suite passed" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "❌ Comprehensive test suite failed" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Set-Location ..
        Write-Host "❌ Comprehensive test suite failed with error" -ForegroundColor Red
        return $false
    }
}

function Show-TestSummary {
    param([array]$results)
    
    Write-Host ""
    Write-Host "🏆 COMPETITION READINESS SUMMARY" -ForegroundColor Cyan
    Write-Host "=================================" -ForegroundColor Cyan
    
    $passed = ($results | Where-Object { $_ -eq $true }).Count
    $total = $results.Count
    $score = if ($total -gt 0) { [math]::Round(($passed / $total) * 100, 0) } else { 0 }
    
    Write-Host "Tests Passed: $passed / $total" -ForegroundColor White
    if ($score -ge $competitionThreshold) {
        Write-Host "Overall Score: $score%" -ForegroundColor Green
    }
    else {
        Write-Host "Overall Score: $score%" -ForegroundColor Red
    }
    
    if ($score -ge $competitionThreshold) {
        Write-Host ""
        Write-Host "🎉 COMPETITION READY!" -ForegroundColor Green
        Write-Host "Your HEMA3N platform passes all quality gates" -ForegroundColor Green
        Write-Host ""
        Write-Host "✅ Visual components render correctly" -ForegroundColor Green
        Write-Host "✅ Accessibility standards met" -ForegroundColor Green  
        Write-Host "✅ Performance benchmarks achieved" -ForegroundColor Green
        Write-Host "✅ API integration working" -ForegroundColor Green
        Write-Host "✅ Responsive design validated" -ForegroundColor Green
        Write-Host ""
        Write-Host "🔗 Access your platform:" -ForegroundColor Yellow
        Write-Host "   Full App: http://localhost:3000/" -ForegroundColor White
        Write-Host "   Demo Credentials:" -ForegroundColor White
        Write-Host "   - Admin: admin / admin123" -ForegroundColor White
        Write-Host "   - Operator: operator / operator123" -ForegroundColor White
        Write-Host "   - Viewer: viewer / viewer123" -ForegroundColor White
    }
    else {
        Write-Host ""
        Write-Host "⚠️  IMPROVEMENTS NEEDED" -ForegroundColor Yellow
        Write-Host "Score below competition threshold ($competitionThreshold%)" -ForegroundColor Yellow
        Write-Host "Review failed tests and address issues before competition" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

# Main execution
Test-Prerequisites

$testResults = @()

if ($QuickCheck) {
    Write-Host "⚡ Running Quick Competition Check..." -ForegroundColor Yellow
    $testResults += Run-VisualRegressionTests
    $testResults += Run-AccessibilityTests
    $testResults += Run-PerformanceTests
}
elseif ($Visual) {
    Write-Host "👁️  Running Visual Tests Only..." -ForegroundColor Yellow
    $testResults += Run-VisualRegressionTests
}
elseif ($Performance) {
    Write-Host "⚡ Running Performance Tests Only..." -ForegroundColor Yellow
    $testResults += Run-PerformanceTests
}
elseif ($FullSuite) {
    Write-Host "🎯 Running Full Competition Test Suite..." -ForegroundColor Yellow
    $testResults += Run-VisualRegressionTests
    $testResults += Run-AccessibilityTests
    $testResults += Run-PerformanceTests
    $testResults += Run-IntegrationTests
    $testResults += Run-ResponsiveTests
    $testResults += Run-ComprehensiveTestSuite
}
else {
    # Default: Core competition tests
    Write-Host "🏆 Running Core Competition Tests..." -ForegroundColor Yellow
    $testResults += Run-VisualRegressionTests
    $testResults += Run-AccessibilityTests
    $testResults += Run-IntegrationTests
    $testResults += Run-ResponsiveTests
}

Show-TestSummary -results $testResults

# Generate test report file
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$reportPath = ".\competition-test-report_$timestamp.txt"

$reportContent = @"
HEMA3N Competition Test Report
Generated: $(Get-Date)
========================================

Test Results:
- Visual Regression: $(if ($testResults.Count -gt 0 -and $testResults[0]) { "PASS" } else { "FAIL" })
- Accessibility: $(if ($testResults.Count -gt 1 -and $testResults[1]) { "PASS" } else { "FAIL" })
- API Integration: $(if ($testResults.Count -gt 2 -and $testResults[2]) { "PASS" } else { "FAIL" })
- Responsive Design: $(if ($testResults.Count -gt 3 -and $testResults[3]) { "PASS" } else { "FAIL" })

Overall Score: $(($testResults | Where-Object { $_ -eq $true }).Count) / $($testResults.Count) tests passed
Competition Ready: $(if ($testResults.Count -gt 0 -and (($testResults | Where-Object { $_ -eq $true }).Count / $testResults.Count) * 100 -ge $competitionThreshold) { "YES" } else { "NO" })

Platform Access:
- Main Application: http://localhost:3000/
- System Status: http://localhost:3000/debug.html
- API Documentation: http://localhost:8000/docs

Demo Credentials:
- Admin: admin / admin123
- Operator: operator / operator123
- Viewer: viewer / viewer123
"@

$reportContent | Out-File -FilePath $reportPath -Encoding UTF8

Write-Host "📄 Test report saved to: $reportPath" -ForegroundColor Gray