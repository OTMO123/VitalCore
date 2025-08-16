# Quick Competition Readiness Check
Write-Host "🏆 HEMA3N Quick Competition Check" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

$score = 0
$total = 0

# Check 1: Node.js
Write-Host "🔍 Checking Node.js..." -NoNewline
try {
    $nodeVersion = node --version
    Write-Host " ✅ ($nodeVersion)" -ForegroundColor Green
    $score++
}
catch {
    Write-Host " ❌ Not found" -ForegroundColor Red
}
$total++

# Check 2: Frontend dependencies
Write-Host "📦 Checking dependencies..." -NoNewline
if (Test-Path ".\frontend\node_modules") {
    Write-Host " ✅ Installed" -ForegroundColor Green
    $score++
}
else {
    Write-Host " ❌ Missing" -ForegroundColor Red
}
$total++

# Check 3: Backend server
Write-Host "🖥️  Checking backend..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 3 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host " ✅ Running" -ForegroundColor Green
        $score++
    }
    else {
        Write-Host " ⚠️  Not responding" -ForegroundColor Yellow
    }
}
catch {
    Write-Host " ❌ Not running" -ForegroundColor Red
}
$total++

# Check 4: Frontend server
Write-Host "🌐 Checking frontend..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 3 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host " ✅ Running" -ForegroundColor Green
        $score++
    }
    else {
        Write-Host " ⚠️  Not responding" -ForegroundColor Yellow
    }
}
catch {
    Write-Host " ❌ Not running" -ForegroundColor Red
}
$total++

# Check 5: Test files exist
Write-Host "📋 Checking test files..." -NoNewline
$testFiles = @(
    ".\frontend\tests\visual-regression\ui-test-suite.test.ts",
    ".\frontend\tests\accessibility\a11y-test-suite.test.ts",
    ".\frontend\tests\integration\api-ui-integration.test.ts",
    ".\frontend\tests\performance\performance-benchmarks.test.ts"
)

$testFilesExist = 0
foreach ($file in $testFiles) {
    if (Test-Path $file) {
        $testFilesExist++
    }
}

if ($testFilesExist -eq $testFiles.Count) {
    Write-Host " ✅ All test files present" -ForegroundColor Green
    $score++
}
else {
    Write-Host " ❌ Missing test files ($testFilesExist/$($testFiles.Count))" -ForegroundColor Red
}
$total++

# Check 6: Basic frontend structure
Write-Host "🏗️  Checking app structure..." -NoNewline
$structureFiles = @(
    ".\frontend\src\App.tsx",
    ".\frontend\src\main.tsx", 
    ".\frontend\src\pages\auth\LoginPage.tsx",
    ".\frontend\package.json"
)

$structureFilesExist = 0
foreach ($file in $structureFiles) {
    if (Test-Path $file) {
        $structureFilesExist++
    }
}

if ($structureFilesExist -eq $structureFiles.Count) {
    Write-Host " ✅ App structure complete" -ForegroundColor Green
    $score++
}
else {
    Write-Host " ❌ Missing structure files ($structureFilesExist/$($structureFiles.Count))" -ForegroundColor Red
}
$total++

# Calculate final score
$percentage = [math]::Round(($score / $total) * 100, 0)

Write-Host ""
Write-Host "📊 QUICK CHECK RESULTS" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host "Score: $score / $total tests passed ($percentage%)" -ForegroundColor White

if ($percentage -ge 85) {
    Write-Host ""
    Write-Host "🎉 COMPETITION READY!" -ForegroundColor Green
    Write-Host "Your HEMA3N platform is ready for competition" -ForegroundColor Green
}
elseif ($percentage -ge 70) {
    Write-Host ""
    Write-Host "⚠️  MOSTLY READY" -ForegroundColor Yellow
    Write-Host "Fix remaining issues before competition" -ForegroundColor Yellow
}
else {
    Write-Host ""
    Write-Host "❌ NEEDS WORK" -ForegroundColor Red
    Write-Host "Address critical issues before competition" -ForegroundColor Red
}

Write-Host ""
Write-Host "🔗 Your Competition Platform:" -ForegroundColor Yellow
Write-Host "   URL: http://localhost:3000/" -ForegroundColor White
Write-Host "   Credentials: admin / admin123" -ForegroundColor White
Write-Host ""

# Simple test run if everything looks good
if ($percentage -ge 70 -and $score -ge 4) {
    Write-Host "🧪 Running basic component test..." -ForegroundColor Magenta
    
    Set-Location .\frontend
    
    # Try to run one simple test
    try {
        $testOutput = npm test -- --run --reporter=basic tests/visual-regression/ui-test-suite.test.ts 2>&1 | Select-Object -First 10
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Basic tests passing" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️  Some tests may need attention" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "⚠️  Test runner needs configuration" -ForegroundColor Yellow
    }
    
    Set-Location ..
}

Write-Host "✨ Quick check complete!" -ForegroundColor Green