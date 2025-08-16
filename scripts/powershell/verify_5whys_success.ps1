# 5 Whys UUID Fix Verification Script
# Проверяет успешность исправления UUID проблемы

Write-Host "=== 🔍 5 WHYS UUID FIX VERIFICATION ===" -ForegroundColor Cyan
Write-Host "Проверяем исправление UUID проблемы..." -ForegroundColor Yellow
Write-Host ""

$baseUrl = "http://localhost:8000"
$successCount = 0
$totalTests = 0

# Функция для тестирования
function Test-PatientCreation {
    param($testName, $patientData)
    
    $global:totalTests++
    Write-Host "🧪 Тест $global:totalTests`: $testName" -ForegroundColor Yellow
    
    try {
        # Авторизация
        $loginHeaders = @{
            'Content-Type' = 'application/x-www-form-urlencoded'
        }
        $loginBody = "username=admin&password=admin123"
        
        $loginResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody -ErrorAction Stop
        $token = $loginResponse.access_token
        
        # Создание пациента
        $headers = @{
            'Authorization' = "Bearer $token"
            'Content-Type' = 'application/json'
        }
        
        $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/healthcare/patients" -Method POST -Headers $headers -Body ($patientData | ConvertTo-Json -Depth 5) -ErrorAction Stop
        
        if ($response.id -and $response.id.Length -eq 36) {
            Write-Host "   ✅ УСПЕХ - Patient ID: $($response.id)" -ForegroundColor Green
            Write-Host "   📝 Имя: $($response.name[0].given[0]) $($response.name[0].family)" -ForegroundColor White
            $global:successCount++
            return $true
        } else {
            Write-Host "   ❌ НЕУДАЧА - Неверный формат ответа" -ForegroundColor Red
            return $false
        }
    }
    catch {
        $errorMessage = $_.Exception.Message
        if ($errorMessage -like "*badly formed hexadecimal UUID string*") {
            Write-Host "   ❌ UUID ОШИБКА - НЕ ИСПРАВЛЕНО!" -ForegroundColor Red
        } else {
            Write-Host "   ❌ ОШИБКА: $errorMessage" -ForegroundColor Red
        }
        return $false
    }
}

# Тест 1: Простой пациент
Write-Host "=" * 60
$simplePatient = @{
    identifier = @(
        @{
            value = "VERIFY-SIMPLE-$(Get-Random)"
        }
    )
    name = @(
        @{
            family = "ПростойТест"
            given = @("Проверка")
        }
    )
}

Test-PatientCreation "Простое создание пациента" $simplePatient

# Тест 2: Полный пациент
Write-Host "=" * 60
$fullPatient = @{
    identifier = @(
        @{
            use = "official"
            type = @{
                coding = @(
                    @{
                        system = "http://terminology.hl7.org/CodeSystem/v2-0203"
                        code = "MR"
                    }
                )
            }
            system = "http://hospital.smarthit.org"
            value = "VERIFY-FULL-$(Get-Random)"
        }
    )
    name = @(
        @{
            use = "official"
            family = "ПолныйТест"
            given = @("Максимальный", "Функционал")
        }
    )
    gender = "male"
    birthDate = "1990-01-01"
    active = $true
}

Test-PatientCreation "Полное создание пациента с FHIR данными" $fullPatient

# Тест 3: Множественные пациенты
Write-Host "=" * 60
Write-Host "🔄 Тест стабильности - создание 3 пациентов подряд..." -ForegroundColor Yellow

for ($i = 1; $i -le 3; $i++) {
    $batchPatient = @{
        identifier = @(
            @{
                value = "BATCH-$i-$(Get-Random)"
            }
        )
        name = @(
            @{
                family = "БатчТест$i"
                given = @("Стабильность")
            }
        )
    }
    
    Test-PatientCreation "Батч тест $i/3" $batchPatient
    Start-Sleep -Milliseconds 500
}

# Итоговые результаты
Write-Host ""
Write-Host "=" * 60
Write-Host "📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ 5 WHYS UUID FIX" -ForegroundColor Cyan
Write-Host "=" * 60

$successRate = [math]::Round(($successCount / $totalTests) * 100, 1)

Write-Host "Всего тестов: $totalTests" -ForegroundColor White
Write-Host "Успешных: $successCount" -ForegroundColor Green
Write-Host "Неудачных: $($totalTests - $successCount)" -ForegroundColor Red
Write-Host "Процент успеха: $successRate%" -ForegroundColor $(if ($successRate -eq 100) { "Green" } else { "Yellow" })

Write-Host ""
if ($successRate -eq 100) {
    Write-Host "🎉 ПОЗДРАВЛЯЕМ! 5 WHYS FRAMEWORK СРАБОТАЛ НА 100%!" -ForegroundColor Green
    Write-Host "✅ UUID проблема полностью решена" -ForegroundColor Green
    Write-Host "✅ Patient creation работает идеально" -ForegroundColor Green
    Write-Host "✅ Система готова для frontend интеграции" -ForegroundColor Green
} elseif ($successRate -ge 80) {
    Write-Host "✅ ХОРОШО! Большинство тестов прошло успешно" -ForegroundColor Yellow
    Write-Host "⚠️  Есть незначительные проблемы для доработки" -ForegroundColor Yellow
} else {
    Write-Host "❌ ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ РАБОТА" -ForegroundColor Red
    Write-Host "❌ UUID проблема не полностью решена" -ForegroundColor Red
}

Write-Host ""
Write-Host "📋 Детальный отчет доступен в:" -ForegroundColor Cyan
Write-Host "   reports/fix-reports/2025-07-19-5whys-uuid-resolution-complete.md" -ForegroundColor White
Write-Host ""
Write-Host "=== ПРОВЕРКА ЗАВЕРШЕНА ===" -ForegroundColor Cyan