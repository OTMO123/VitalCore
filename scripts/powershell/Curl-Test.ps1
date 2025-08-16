# Простейший тест через curl
param([string]$Server = "http://localhost:8003")

Write-Host "🔧 IRIS API Curl Test" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
Write-Host "Testing: $Server" -ForegroundColor Green
Write-Host ""

# Функция для выполнения curl
function Run-Curl {
    param(
        [string]$Url,
        [string]$Method = "GET",
        [string]$Data = "",
        [string]$ContentType = "application/json"
    )
    
    Write-Host "📤 $Method $Url" -ForegroundColor Blue
    
    if ($Data) {
        $result = & curl -s -w "`nHTTP_CODE:%{http_code}`nTIME:%{time_total}" -X $Method -H "Content-Type: $ContentType" -d $Data $Url
    } else {
        $result = & curl -s -w "`nHTTP_CODE:%{http_code}`nTIME:%{time_total}" -X $Method $Url
    }
    
    Write-Host $result -ForegroundColor White
    Write-Host ""
    
    return $result
}

# Тест 1: Health check
Write-Host "=== TEST 1: Health Check ===" -ForegroundColor Yellow
$health = Run-Curl -Url "$Server/health"

if ($health -notlike "*HTTP_CODE:200*") {
    Write-Host "❌ Server not responding!" -ForegroundColor Red
    Write-Host "Make sure uvicorn is running: uvicorn app.main:app --port 8003" -ForegroundColor Red
    exit 1
}

# Тест 2: Registration
Write-Host "=== TEST 2: User Registration ===" -ForegroundColor Yellow
$randomId = Get-Random -Maximum 9999
$registerJson = "{`"username`":`"testuser$randomId`",`"password`":`"testpass123`",`"email`":`"test$randomId@example.com`",`"role`":`"user`"}"

$register = Run-Curl -Url "$Server/api/v1/auth/register" -Method "POST" -Data $registerJson

# Тест 3: Login
Write-Host "=== TEST 3: Login Test ===" -ForegroundColor Yellow
$loginData = "username=testuser$randomId&password=testpass123"
$login = Run-Curl -Url "$Server/api/v1/auth/login" -Method "POST" -Data $loginData -ContentType "application/x-www-form-urlencoded"

# Тест 4: Invalid login
Write-Host "=== TEST 4: Invalid Login ===" -ForegroundColor Yellow
$badLogin = Run-Curl -Url "$Server/api/v1/auth/login" -Method "POST" -Data "username=baduser&password=badpass" -ContentType "application/x-www-form-urlencoded"

# Тест 5: Empty login
Write-Host "=== TEST 5: Empty Login ===" -ForegroundColor Yellow
$emptyLogin = Run-Curl -Url "$Server/api/v1/auth/login" -Method "POST" -Data "" -ContentType "application/x-www-form-urlencoded"

Write-Host "===================" -ForegroundColor Cyan
Write-Host "🔍 ANALYSIS" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan

# Анализ ошибок 500
$all_results = @($register, $login, $badLogin, $emptyLogin)
$has500 = $false

foreach ($result in $all_results) {
    if ($result -like "*HTTP_CODE:500*") {
        $has500 = $true
        break
    }
}

if ($has500) {
    Write-Host "🚨 500 ERRORS DETECTED!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Database diagnostic shows DB is working fine." -ForegroundColor Yellow
    Write-Host "Problem is in application code!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 CHECK YOUR UVICORN TERMINAL NOW!" -ForegroundColor Cyan
    Write-Host "The exact error stack trace should be visible there." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Common causes:" -ForegroundColor White
    Write-Host "- Import errors in Python modules" -ForegroundColor White
    Write-Host "- Event bus initialization failure" -ForegroundColor White
    Write-Host "- Audit service errors" -ForegroundColor White
    Write-Host "- Missing dependencies in venv" -ForegroundColor White
} else {
    Write-Host "✅ No 500 errors detected" -ForegroundColor Green
    
    if ($login -like "*access_token*") {
        Write-Host "✅ Authentication working!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Authentication may have issues" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Test completed: $(Get-Date)" -ForegroundColor Green