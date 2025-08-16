# Quick configuration test with proper key length
Write-Host "🔧 Testing configuration with proper keys..." -ForegroundColor Cyan

$testScript = @'
import os
import sys
sys.path.insert(0, '.')

# Set valid environment variables (16+ chars as required)
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://test:test@localhost:5432/test_db'
os.environ['SECRET_KEY'] = 'test_secret_key_16_chars_minimum_length'
os.environ['ENCRYPTION_KEY'] = 'test_encryption_key_16_chars_minimum_length'

try:
    from app.core.config import get_settings
    settings = get_settings()
    print('SUCCESS: Configuration loaded successfully!')
    print(f'Environment: {settings.ENVIRONMENT}')
    print(f'Debug: {settings.DEBUG}')
except Exception as e:
    print(f'ERROR: {e}')
'@

$testScript | Out-File "quick_test.py" -Encoding UTF8
$result = & python "quick_test.py" 2>&1
Remove-Item "quick_test.py" -ErrorAction SilentlyContinue

if ($result -match "SUCCESS") {
    Write-Host "✅ Configuration test PASSED!" -ForegroundColor Green
    Write-Host "🚀 System is ready to start!" -ForegroundColor Green
} else {
    Write-Host "⚠️ Configuration test result: $result" -ForegroundColor Yellow
}

Write-Host "`n🎯 Now run: .\start_safe.ps1" -ForegroundColor Cyan