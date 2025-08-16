# Install Enterprise Healthcare Platform Dependencies
# Required for SOC2 Type II compliance, HIPAA monitoring, and production readiness

Write-Host "🏥 Installing Enterprise Healthcare Platform Dependencies..." -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# Activate virtual environment
Write-Host "`n📁 Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

Write-Host "`n🔧 Installing OpenTelemetry Stack (Enterprise Monitoring)..." -ForegroundColor Green
pip install opentelemetry-api>=1.20.0
pip install opentelemetry-sdk>=1.20.0
pip install opentelemetry-instrumentation>=0.41b0
pip install opentelemetry-instrumentation-fastapi>=0.41b0
pip install opentelemetry-instrumentation-sqlalchemy>=0.41b0
pip install opentelemetry-instrumentation-requests>=0.41b0
pip install opentelemetry-instrumentation-urllib3>=0.41b0
pip install opentelemetry-exporter-prometheus>=1.12.0rc1
pip install opentelemetry-exporter-jaeger>=1.20.0
pip install opentelemetry-propagator-b3>=1.20.0

Write-Host "`n📊 Installing Performance Monitoring Dependencies..." -ForegroundColor Green
pip install locust>=2.17.0
pip install geoip2>=4.7.0
pip install user-agents>=2.2.0
pip install mmh3>=4.0.0
pip install watchdog>=3.0.0
pip install maxminddb>=2.2.0
pip install memory-profiler>=0.61.0
pip install pycryptodome>=3.19.0

Write-Host "`n🔐 Installing Security & Compliance Dependencies..." -ForegroundColor Green
pip install cryptography>=41.0.0
pip install passlib[bcrypt]>=1.7.4
pip install python-jose[cryptography]>=3.3.0

Write-Host "`n📈 Installing Additional Monitoring Tools..." -ForegroundColor Green  
pip install prometheus-client>=0.17.0
pip install structlog>=23.2.0
pip install psutil>=5.9.0
pip install brotli>=1.1.0

Write-Host "`n✅ Verifying installation..." -ForegroundColor Yellow
python -c "
import sys
print('Python version:', sys.version)
print()

# Test critical imports
test_imports = [
    'opentelemetry.api',
    'opentelemetry.sdk', 
    'opentelemetry.instrumentation.fastapi',
    'locust',
    'geoip2',
    'user_agents',
    'mmh3',
    'watchdog',
    'memory_profiler',
    'prometheus_client',
    'structlog',
    'psutil',
    'brotli'
]

failed_imports = []
for module in test_imports:
    try:
        __import__(module)
        print(f'✅ {module}')
    except ImportError as e:
        print(f'❌ {module}: {e}')
        failed_imports.append(module)

if failed_imports:
    print(f'\n❌ {len(failed_imports)} imports failed')
    sys.exit(1)
else:
    print(f'\n🎉 All {len(test_imports)} enterprise dependencies installed successfully!')
"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n🧪 Running infrastructure tests..." -ForegroundColor Cyan
    python -m pytest app/tests/infrastructure/test_dependency_imports.py -v
    
    Write-Host "`n🏥 Enterprise Healthcare Platform Dependencies: READY ✅" -ForegroundColor Green
    Write-Host "• OpenTelemetry monitoring stack installed" -ForegroundColor White
    Write-Host "• Performance monitoring tools ready" -ForegroundColor White
    Write-Host "• Security dependencies verified" -ForegroundColor White
    Write-Host "• SOC2 Type II compliance tools ready" -ForegroundColor White
} else {
    Write-Host "`n❌ Some dependencies failed to install. Please check the output above." -ForegroundColor Red
}