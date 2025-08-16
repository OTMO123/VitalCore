# Тест логина с существующим аккаунтом admin/admin123
Write-Host "Testing IRIS API Login" -ForegroundColor Green

# Тест 1: Регистрация нового пользователя
Write-Host "=== Test 1: Register New User ===" -ForegroundColor Yellow
$headers = @{ "Content-Type" = "application/json" }
$body = @{
    username = "testuser999"
    password = "testpass123"
    email = "test999@example.com"
    role = "user"
} | ConvertTo-Json

try {
    $register = Invoke-WebRequest -Uri "http://localhost:8003/api/v1/auth/register" -Method POST -Headers $headers -Body $body
    Write-Host "Registration Status: $($register.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($register.Content)" -ForegroundColor White
}
catch {
    Write-Host "Registration Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    }
}

Write-Host ""

# Тест 2: Логин с admin аккаунтом
Write-Host "=== Test 2: Login with admin/admin123 ===" -ForegroundColor Yellow
$loginHeaders = @{ "Content-Type" = "application/x-www-form-urlencoded" }
$loginBody = "username=admin&password=admin123"

try {
    $login = Invoke-WebRequest -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    Write-Host "Login Status: $($login.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($login.Content)" -ForegroundColor White
}
catch {
    Write-Host "Login Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "Status Code: $statusCode" -ForegroundColor Red
        
        if ($statusCode -eq 500) {
            Write-Host ""
            Write-Host "500 ERROR DETECTED!" -ForegroundColor Red
            Write-Host "Check your uvicorn terminal for the exact error!" -ForegroundColor Yellow
        }
    }
}

Write-Host ""

# Тест 3: Логин с неправильными данными
Write-Host "=== Test 3: Login with wrong credentials ===" -ForegroundColor Yellow
$badLoginBody = "username=wronguser&password=wrongpass"

try {
    $badLogin = Invoke-WebRequest -Uri "http://localhost:8003/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $badLoginBody
    Write-Host "Bad Login Status: $($badLogin.StatusCode)" -ForegroundColor Yellow
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "Bad Login Status: $statusCode (Expected 401)" -ForegroundColor Green
    if ($statusCode -eq 500) {
        Write-Host "UNEXPECTED 500 ERROR!" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Test completed. Check uvicorn logs for any 500 errors!" -ForegroundColor Cyan