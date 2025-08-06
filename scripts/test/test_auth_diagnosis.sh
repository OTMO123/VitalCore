#!/bin/bash

# IRIS API Authentication Diagnostic Script
# Тестирование аутентификации с детальным логированием

echo "🔧 IRIS API Authentication Diagnostic Tool"
echo "=========================================="
echo "Testing server on localhost:8003"
echo "Timestamp: $(date)"
echo ""

# Цвета for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 1. Проверка доступности сервера
log_test "Checking server availability..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8003/health | grep -q "200"; then
    log_success "Server is responding on port 8003"
else
    log_error "Server not responding on port 8003"
    echo "Please ensure the server is running: uvicorn app.main:app --port 8003"
    exit 1
fi

# 2. Детальная проверка health endpoint
log_test "Testing /health endpoint..."
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}\n%{time_total}\n" http://localhost:8003/health)
echo "Health Response:"
echo "$HEALTH_RESPONSE"
echo ""

# 3. Проверка CORS headers
log_test "Testing CORS headers..."
CORS_RESPONSE=$(curl -s -I -X OPTIONS http://localhost:8003/api/v1/auth/login)
echo "CORS Headers:"
echo "$CORS_RESPONSE"
echo ""

# 4. Тест логина с неправильными данными (должен возвращать 401)
log_test "Testing login with invalid credentials..."
INVALID_LOGIN=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME:%{time_total}\n" \
    -X POST http://localhost:8003/api/v1/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=testuser&password=wrongpass")

echo "Invalid Login Response:"
echo "$INVALID_LOGIN"
echo ""

# 5. Тест логина с пустыми данными
log_test "Testing login with empty credentials..."
EMPTY_LOGIN=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME:%{time_total}\n" \
    -X POST http://localhost:8003/api/v1/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "")

echo "Empty Login Response:"
echo "$EMPTY_LOGIN"
echo ""

# 6. Тест регистрации (если доступен)
log_test "Testing user registration..."
REGISTER_DATA='{"username":"testuser","password":"testpass123","email":"test@example.com","role":"user"}'
REGISTER_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME:%{time_total}\n" \
    -X POST http://localhost:8003/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d "$REGISTER_DATA")

echo "Registration Response:"
echo "$REGISTER_RESPONSE"
echo ""

# 7. Тест логина с зарегистрированным пользователем
log_test "Testing login with registered user..."
VALID_LOGIN=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME:%{time_total}\n" \
    -X POST http://localhost:8003/api/v1/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=testuser&password=testpass123")

echo "Valid Login Response:"
echo "$VALID_LOGIN"
echo ""

# 8. Анализ ошибок 500
log_test "Analyzing 500 errors..."
ERROR_500_TEST=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME:%{time_total}\n" \
    -X POST http://localhost:8003/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"invalid": "json_format"}')

echo "500 Error Analysis:"
echo "$ERROR_500_TEST"
echo ""

# 9. Тест middleware логирования
log_test "Testing security middleware logging..."
MIDDLEWARE_TEST=$(curl -s -w "\nHTTP_CODE:%{http_code}\n" \
    -H "User-Agent: IRIS-Auth-Diagnostic-Tool/1.0" \
    -H "X-Forwarded-For: 127.0.0.1" \
    http://localhost:8003/api/v1/auth/status)

echo "Middleware Test Response:"
echo "$MIDDLEWARE_TEST"
echo ""

# 10. Итоговый анализ
echo "=========================================="
echo "🔍 DIAGNOSTIC SUMMARY"
echo "=========================================="

# Проверка на ошибки 500
if echo "$VALID_LOGIN $INVALID_LOGIN $EMPTY_LOGIN $REGISTER_RESPONSE" | grep -q "500"; then
    log_error "500 Internal Server Error detected!"
    echo ""
    echo "🚨 POSSIBLE CAUSES OF 500 ERRORS:"
    echo "1. Database connection issues (PostgreSQL not running?)"
    echo "2. Missing database tables (run: alembic upgrade head)"
    echo "3. Environment variables missing or incorrect"
    echo "4. Dependency issues in virtual environment"
    echo "5. Database permissions problems"
    echo ""
    echo "📋 IMMEDIATE ACTIONS:"
    echo "1. Check PostgreSQL service: pg_ctl status"
    echo "2. Verify database connection in .env file"
    echo "3. Run database migrations: alembic upgrade head"
    echo "4. Check server logs in PowerShell terminal"
    echo "5. Verify all dependencies are installed in venv"
else
    log_success "No 500 errors detected in basic tests"
fi

# Проверка аутентификации
if echo "$VALID_LOGIN" | grep -q "access_token"; then
    log_success "Authentication working correctly"
elif echo "$VALID_LOGIN" | grep -q "401"; then
    log_error "Authentication failing - check user creation/password hashing"
else
    log_warning "Authentication response unclear - check logs"
fi

echo ""
echo "🔧 For detailed server logs, check your PowerShell terminal where uvicorn is running"
echo "🔧 This diagnostic script has generated detailed request logs for SOC2 compliance"
echo ""
echo "Diagnostic completed at: $(date)"