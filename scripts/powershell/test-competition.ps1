# HEMA3N Competition Test Runner - Simplified Version
param(
    [switch]$FullSuite,
    [switch]$QuickCheck,
    [switch]$Visual
)

Write-Host "🏆 HEMA3N Competition Test Suite" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

$frontendPath = ".\frontend"
$testResults = @()

# Check prerequisites
Write-Host "🔍 Checking Prerequisites..." -ForegroundColor Yellow

try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ Node.js not found" -ForegroundColor Red
    exit 1
}

if (Test-Path "$frontendPath\node_modules") {
    Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green
}
else {
    Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location $frontendPath
    npm install
    Set-Location ..
}

# Check if servers are running
try {
    $backendCheck = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 3 -ErrorAction SilentlyContinue
    if ($backendCheck.StatusCode -eq 200) {
        Write-Host "✅ Backend server running" -ForegroundColor Green
    }
}
catch {
    Write-Host "⚠️  Backend server not responding" -ForegroundColor Yellow
}

try {
    $frontendCheck = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 3 -ErrorAction SilentlyContinue
    if ($frontendCheck.StatusCode -eq 200) {
        Write-Host "✅ Frontend server running" -ForegroundColor Green
    }
}
catch {
    Write-Host "⚠️  Frontend server not responding" -ForegroundColor Yellow
}

Write-Host ""

# Run Visual Tests
Write-Host "📱 Running Visual Tests..." -ForegroundColor Magenta
Set-Location $frontendPath

try {
    $visualOutput = npm test -- --run tests/visual-regression/ui-test-suite.test.ts 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Visual regression tests passed" -ForegroundColor Green
        $testResults += $true
    }
    else {
        Write-Host "❌ Visual regression tests failed" -ForegroundColor Red  
        $testResults += $false
    }
}
catch {
    Write-Host "❌ Visual tests error" -ForegroundColor Red
    $testResults += $false
}

# Run Accessibility Tests  
Write-Host "♿ Running Accessibility Tests..." -ForegroundColor Magenta

try {
    $a11yOutput = npm test -- --run tests/accessibility/a11y-test-suite.test.ts 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Accessibility tests passed" -ForegroundColor Green
        $testResults += $true
    }
    else {
        Write-Host "❌ Accessibility tests failed" -ForegroundColor Red
        $testResults += $false
    }
}
catch {
    Write-Host "❌ Accessibility tests error" -ForegroundColor Red
    $testResults += $false
}

if ($FullSuite -or !$Visual) {
    # Run Integration Tests
    Write-Host "🔌 Running Integration Tests..." -ForegroundColor Magenta
    
    try {
        $integrationOutput = npm test -- --run tests/integration/api-ui-integration.test.ts 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Integration tests passed" -ForegroundColor Green
            $testResults += $true
        }
        else {
            Write-Host "❌ Integration tests failed" -ForegroundColor Red
            $testResults += $false
        }
    }
    catch {
        Write-Host "❌ Integration tests error" -ForegroundColor Red
        $testResults += $false
    }

    # Run Performance Tests
    Write-Host "⚡ Running Performance Tests..." -ForegroundColor Magenta
    
    try {
        $perfOutput = npm test -- --run tests/performance/performance-benchmarks.test.ts 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Performance tests passed" -ForegroundColor Green
            $testResults += $true
        }
        else {
            Write-Host "❌ Performance tests failed" -ForegroundColor Red
            $testResults += $false
        }
    }
    catch {
        Write-Host "❌ Performance tests error" -ForegroundColor Red
        $testResults += $false
    }
}

if ($FullSuite) {
    # Run Responsive Tests
    Write-Host "📱 Running Responsive Tests..." -ForegroundColor Magenta
    
    try {
        $responsiveOutput = npm test -- --run tests/responsive/viewport-testing.test.ts 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Responsive tests passed" -ForegroundColor Green
            $testResults += $true
        }
        else {
            Write-Host "❌ Responsive tests failed" -ForegroundColor Red
            $testResults += $false
        }
    }
    catch {
        Write-Host "❌ Responsive tests error" -ForegroundColor Red
        $testResults += $false
    }
}

Set-Location ..

# Calculate results
$passed = ($testResults | Where-Object { $_ -eq $true }).Count
$total = $testResults.Count
$score = if ($total -gt 0) { [math]::Round(($passed / $total) * 100, 0) } else { 0 }

Write-Host ""
Write-Host "🏆 COMPETITION READINESS SUMMARY" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "Tests Passed: $passed / $total" -ForegroundColor White

if ($score -ge 85) {
    Write-Host "Overall Score: $score%" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎉 COMPETITION READY!" -ForegroundColor Green
    Write-Host "Your HEMA3N platform passes all quality gates" -ForegroundColor Green
}
else {
    Write-Host "Overall Score: $score%" -ForegroundColor Red
    Write-Host ""
    Write-Host "⚠️  IMPROVEMENTS NEEDED" -ForegroundColor Yellow
    Write-Host "Score below competition threshold (85%)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔗 Access your platform:" -ForegroundColor Yellow
Write-Host "   Full App: http://localhost:3000/" -ForegroundColor White
Write-Host "   Demo Credentials:" -ForegroundColor White
Write-Host "   - Admin: admin / admin123" -ForegroundColor White
Write-Host "   - Operator: operator / operator123" -ForegroundColor White
Write-Host "   - Viewer: viewer / viewer123" -ForegroundColor White
Write-Host ""

# Generate report
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$reportPath = ".\test-report_$timestamp.txt"

@"
HEMA3N Competition Test Report
Generated: $(Get-Date)
========================================

Test Results: $passed / $total tests passed ($score%)
Competition Ready: $(if ($score -ge 85) { "YES" } else { "NO" })

Platform Access:
- Main Application: http://localhost:3000/
- API Documentation: http://localhost:8000/docs

Demo Credentials:
- Admin: admin / admin123
- Operator: operator / operator123  
- Viewer: viewer / viewer123
"@ | Out-File -FilePath $reportPath -Encoding UTF8

Write-Host "📄 Report saved to: $reportPath" -ForegroundColor Gray