# Простой тест аутентификации IRIS API
param(
    [string]$ServerUrl = "http://localhost:8003"
)

Write-Host "🔧 IRIS API Simple Authentication Test" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Server: $ServerUrl" -ForegroundColor Green
Write-Host "Time: $(Get-Date)" -ForegroundColor Green
Write-Host ""

# Простая функция для HTTP запросов
function Test-Endpoint {
    param(
        [string]$Url,
        [string]$Method = "GET",
        [string]$Body = $null,
        [string]$ContentType = "application/json"
    )
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            UseBasicParsing = $true
        }
        
        if ($Body) {
            $params.Body = $Body
            $params.ContentType = $ContentType
        }
        
        Write-Host "📤 Testing: $Method $Url" -ForegroundColor Blue
        if ($Body) {
            Write-Host "📝 Body: $Body" -ForegroundColor DarkGray
        }
        
        $response = Invoke-WebRequest @params -ErrorAction Stop
        
        Write-Host "✅ Success: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "📄 Response: $($response.Content)" -ForegroundColor White
        Write-Host ""
        
        return @{
            Success = $true
            StatusCode = $response.StatusCode
            Content = $response.Content
        }
    }
    catch {
        Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
        
        $statusCode = 0
        if ($_.Exception.Response) {
            $statusCode = [int]$_.Exception.Response.StatusCode
            Write-Host "📥 Status: $statusCode" -ForegroundColor Red
        }
        Write-Host ""
        
        return @{
            Success = $false
            StatusCode = $statusCode
            Error = $_.Exception.Message
        }
    }
}

# Тест 1: Health check
Write-Host "=== TEST 1: Health Check ===" -ForegroundColor Yellow
$health = Test-Endpoint -Url "$ServerUrl/health"

if (-not $health.Success) {
    Write-Host "❌ Server not responding! Check if uvicorn is running on port 8003" -ForegroundColor Red
    exit 1
}

# Тест 2: Регистрация пользователя
Write-Host "=== TEST 2: User Registration ===" -ForegroundColor Yellow
$randomId = Get-Random -Maximum 9999
$registerJson = @{
    username = "testuser$randomId"
    password = "testpass123"
    email = "test$randomId@example.com"
    role = "user"
} | ConvertTo-Json

$register = Test-Endpoint -Url "$ServerUrl/api/v1/auth/register" -Method "POST" -Body $registerJson

# Извлекаем имя пользователя для логина
$username = "testuser$randomId"
if ($register.Success) {
    Write-Host "✅ Registration successful for user: $username" -ForegroundColor Green
} else {
    Write-Host "⚠️ Registration failed, will try with existing user" -ForegroundColor Yellow
    $username = "testuser"
}

# Тест 3: Логин с form data (обходим проблему с &)
Write-Host "=== TEST 3: Login Test ===" -ForegroundColor Yellow

# Создаем form data без использования & в строке
$loginBody = "username=" + $username + "&" + "password=testpass123"
$login = Test-Endpoint -Url "$ServerUrl/api/v1/auth/login" -Method "POST" -Body $loginBody -ContentType "application/x-www-form-urlencoded"

# Тест 4: Неправильные данные
Write-Host "=== TEST 4: Invalid Login ===" -ForegroundColor Yellow
$badLoginBody = "username=baduser&" + "password=badpass"
$badLogin = Test-Endpoint -Url "$ServerUrl/api/v1/auth/login" -Method "POST" -Body $badLoginBody -ContentType "application/x-www-form-urlencoded"

# Тест 5: Пустые данные
Write-Host "=== TEST 5: Empty Login ===" -ForegroundColor Yellow
$emptyLogin = Test-Endpoint -Url "$ServerUrl/api/v1/auth/login" -Method "POST" -Body "" -ContentType "application/x-www-form-urlencoded"

# Анализ результатов
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "🔍 RESULTS ANALYSIS" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

$has500Errors = $false
$hasAuthSuccess = $false

# Проверка на 500 ошибки
if ($register.StatusCode -eq 500) {
    Write-Host "❌ 500 Error in Registration" -ForegroundColor Red
    $has500Errors = $true
}

if ($login.StatusCode -eq 500) {
    Write-Host "❌ 500 Error in Login" -ForegroundColor Red
    $has500Errors = $true
}

if ($badLogin.StatusCode -eq 500) {
    Write-Host "❌ 500 Error in Invalid Login" -ForegroundColor Red
    $has500Errors = $true
}

if ($emptyLogin.StatusCode -eq 500) {
    Write-Host "❌ 500 Error in Empty Login" -ForegroundColor Red
    $has500Errors = $true
}

# Проверка успешной аутентификации
if ($login.Success -and ($login.Content -like "*access_token*")) {
    Write-Host "✅ Authentication Working!" -ForegroundColor Green
    $hasAuthSuccess = $true
} elseif ($login.StatusCode -eq 401) {
    Write-Host "⚠️ Login returned 401 - user may not exist or wrong password" -ForegroundColor Yellow
} elseif ($login.StatusCode -eq 400) {
    Write-Host "⚠️ Login returned 400 - invalid request format" -ForegroundColor Yellow
}

Write-Host ""
if ($has500Errors) {
    Write-Host "🚨 500 ERRORS DETECTED!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Since database diagnostic shows DB is working:" -ForegroundColor Yellow
    Write-Host "1. Check uvicorn logs for detailed error stack traces" -ForegroundColor Yellow
    Write-Host "2. Look for import/dependency errors in server startup" -ForegroundColor Yellow
    Write-Host "3. Check if event bus or audit service is failing" -ForegroundColor Yellow
    Write-Host "4. Verify all Python packages are installed correctly" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 IMMEDIATE ACTION:" -ForegroundColor Cyan
    Write-Host "Watch the uvicorn terminal while running this test!" -ForegroundColor Cyan
    Write-Host "The exact error will appear in the server logs." -ForegroundColor Cyan
} elseif ($hasAuthSuccess) {
    Write-Host "🎉 ALL SYSTEMS WORKING!" -ForegroundColor Green
    Write-Host "Authentication and registration are functioning correctly." -ForegroundColor Green
} else {
    Write-Host "⚠️ NO 500 ERRORS, BUT AUTHENTICATION ISSUES" -ForegroundColor Yellow
    Write-Host "Check user credentials and registration process." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Test completed: $(Get-Date)" -ForegroundColor Green
Write-Host "Check your uvicorn terminal for detailed server logs!" -ForegroundColor Cyan