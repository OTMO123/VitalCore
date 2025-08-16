# IRIS API Authentication Diagnostic PowerShell Script
# Запустите в PowerShell в том же окружении где работает uvicorn

param(
    [string]$ServerUrl = "http://localhost:8003",
    [switch]$Verbose = $false
)

Write-Host "🔧 IRIS API Authentication Diagnostic Tool (PowerShell)" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "Testing server: $ServerUrl" -ForegroundColor Green
Write-Host "Timestamp: $(Get-Date)" -ForegroundColor Green
Write-Host ""

# Функции логирования
function Write-TestLog {
    param([string]$Message)
    Write-Host "[TEST] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

# Функция для выполнения HTTP запросов с детальным логированием
function Invoke-DiagnosticRequest {
    param(
        [string]$Url,
        [string]$Method = "GET",
        [hashtable]$Headers = @{},
        [string]$Body = $null,
        [string]$ContentType = "application/json"
    )
    
    try {
        $requestParams = @{
            Uri = $Url
            Method = $Method
            Headers = $Headers
            UseBasicParsing = $true
        }
        
        if ($Body) {
            $requestParams.Body = $Body
            $requestParams.ContentType = $ContentType
        }
        
        Write-Host "📤 Request: $Method $Url" -ForegroundColor Magenta
        if ($Body -and $Verbose) {
            Write-Host "📝 Body: $Body" -ForegroundColor DarkGray
        }
        
        $response = Invoke-WebRequest @requestParams -ErrorAction Stop
        
        Write-Host "📥 Response: $($response.StatusCode) $($response.StatusDescription)" -ForegroundColor Green
        Write-Host "📄 Content: $($response.Content)" -ForegroundColor White
        Write-Host ""
        
        return @{
            Success = $true
            StatusCode = $response.StatusCode
            Content = $response.Content
            Headers = $response.Headers
        }
    }
    catch {
        Write-Host "❌ Request failed: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            $statusCode = $_.Exception.Response.StatusCode.value__
            Write-Host "📥 Status Code: $statusCode" -ForegroundColor Red
            
            # Чтение содержимого ошибки
            try {
                $errorContent = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($errorContent)
                $errorBody = $reader.ReadToEnd()
                Write-Host "📄 Error Content: $errorBody" -ForegroundColor Red
            }
            catch {
                Write-Host "Could not read error content" -ForegroundColor DarkRed
            }
        }
        Write-Host ""
        
        return @{
            Success = $false
            Error = $_.Exception.Message
            StatusCode = if ($_.Exception.Response) { $_.Exception.Response.StatusCode.value__ } else { 0 }
        }
    }
}

# Тест 1: Проверка доступности сервера
Write-TestLog "Checking server health..."
$healthTest = Invoke-DiagnosticRequest -Url "$ServerUrl/health"

if (-not $healthTest.Success) {
    Write-Error "Server is not responding. Please ensure uvicorn is running on port 8003"
    Write-Host "Expected command: uvicron app.main:app --port 8003 --reload" -ForegroundColor Yellow
    exit 1
}

# Тест 2: Проверка middleware
Write-TestLog "Testing security middleware..."
$middlewareHeaders = @{
    "User-Agent" = "IRIS-PowerShell-Diagnostic/1.0"
    "X-Request-ID" = [System.Guid]::NewGuid().ToString()
}
$middlewareTest = Invoke-DiagnosticRequest -Url "$ServerUrl/" -Headers $middlewareHeaders

# Тест 3: Тест регистрации пользователя
Write-TestLog "Testing user registration..."
$registerData = @{
    username = "testuser_ps"
    password = "testpass123"
    email = "testps@example.com"
    role = "user"
} | ConvertTo-Json

$registerTest = Invoke-DiagnosticRequest -Url "$ServerUrl/api/v1/auth/register" -Method "POST" -Body $registerData

# Тест 4: Тест логина с пустыми данными (должен вернуть 400)
Write-TestLog "Testing login with empty credentials..."
$emptyLoginTest = Invoke-DiagnosticRequest -Url "$ServerUrl/api/v1/auth/login" -Method "POST" -Body "" -ContentType "application/x-www-form-urlencoded"

# Тест 5: Тест логина с неправильными данными (должен вернуть 401)
Write-TestLog "Testing login with invalid credentials..."
$invalidLoginData = "username=wronguser`&password=wrongpass"
$invalidLoginTest = Invoke-DiagnosticRequest -Url "$ServerUrl/api/v1/auth/login" -Method "POST" -Body $invalidLoginData -ContentType "application/x-www-form-urlencoded"

# Тест 6: Тест логина с правильными данными
Write-TestLog "Testing login with valid credentials..."
$validLoginData = "username=testuser_ps`&password=testpass123"
$validLoginTest = Invoke-DiagnosticRequest -Url "$ServerUrl/api/v1/auth/login" -Method "POST" -Body $validLoginData -ContentType "application/x-www-form-urlencoded"

# Тест 7: Принудительный тест 500 ошибки
Write-TestLog "Testing potential 500 error scenarios..."
$malformedJsonTest = Invoke-DiagnosticRequest -Url "$ServerUrl/api/v1/auth/login" -Method "POST" -Body '{"malformed": json}' -ContentType "application/json"

# Анализ результатов
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "🔍 DIAGNOSTIC SUMMARY" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

$errors500 = @()
$authIssues = @()
$successes = @()

# Анализ каждого теста
if ($registerTest.StatusCode -eq 500) { $errors500 += "Registration endpoint" }
if ($validLoginTest.StatusCode -eq 500) { $errors500 += "Login endpoint" }
if ($invalidLoginTest.StatusCode -eq 500) { $errors500 += "Invalid login handling" }

if ($validLoginTest.Success -and $validLoginTest.Content -like "*access_token*") {
    $successes += "Authentication working correctly"
} elseif ($validLoginTest.StatusCode -eq 401) {
    $authIssues += "Login credentials may be incorrect"
} elseif ($validLoginTest.StatusCode -eq 500) {
    $authIssues += "Server error during authentication"
}

# Отчет об ошибках 500
if ($errors500.Count -gt 0) {
    Write-Error "🚨 500 INTERNAL SERVER ERRORS DETECTED!"
    Write-Host ""
    Write-Host "Affected endpoints:" -ForegroundColor Red
    foreach ($endpoint in $errors500) {
        Write-Host "  - $endpoint" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "🔍 POSSIBLE CAUSES:" -ForegroundColor Yellow
    Write-Host "1. Database connection failure (PostgreSQL not running)" -ForegroundColor Yellow
    Write-Host "2. Missing database migrations (run: alembic upgrade head)" -ForegroundColor Yellow
    Write-Host "3. Environment variables misconfigured (.env file)" -ForegroundColor Yellow
    Write-Host "4. Virtual environment dependencies missing" -ForegroundColor Yellow
    Write-Host "5. Database user permissions incorrect" -ForegroundColor Yellow
    
    Write-Host ""
    Write-Host "📋 IMMEDIATE ACTIONS:" -ForegroundColor Cyan
    Write-Host "1. Check PowerShell/terminal where uvicorn is running for error details" -ForegroundColor Cyan
    Write-Host "2. Verify .env file DATABASE_URL is correct" -ForegroundColor Cyan
    Write-Host "3. Run: alembic upgrade head (in your venv)" -ForegroundColor Cyan
    Write-Host "4. Test database connection manually" -ForegroundColor Cyan
    Write-Host "5. Check PostgreSQL service status" -ForegroundColor Cyan
} else {
    Write-Success "✅ No 500 errors detected"
}

# Отчет об аутентификации
if ($successes.Count -gt 0) {
    foreach ($success in $successes) {
        Write-Success "✅ $success"
    }
} elseif ($authIssues.Count -gt 0) {
    foreach ($issue in $authIssues) {
        Write-Warning "⚠️ $issue"
    }
}

Write-Host ""
Write-Host "🔧 This diagnostic script provides detailed logging for SOC2 compliance" -ForegroundColor Green
Write-Host "🔧 All requests are logged with security context in the server logs" -ForegroundColor Green
Write-Host ""
Write-Host "Diagnostic completed at: $(Get-Date)" -ForegroundColor Green

# Рекомендации по решению
Write-Host ""
Write-Host "💡 NEXT STEPS:" -ForegroundColor Blue
Write-Host "1. If you see 500 errors, check the uvicorn terminal for detailed stack traces" -ForegroundColor White
Write-Host "2. Enable DEBUG=true in .env for more verbose logging" -ForegroundColor White
Write-Host "3. Check database connectivity: psql -h localhost -p 5432 -U test_user -d test_iris_db" -ForegroundColor White
Write-Host "4. Verify all services are running: PostgreSQL, Redis (if using background tasks)" -ForegroundColor White