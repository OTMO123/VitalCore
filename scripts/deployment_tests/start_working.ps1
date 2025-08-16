# Start FastAPI Application - Working Configuration
# Uses only the environment variables defined in the Settings model

Write-Host "Starting Healthcare Backend - Working Configuration" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green

# Navigate to project root
Push-Location "../../"

try {
    Write-Host "Setting working environment variables..." -ForegroundColor Cyan
    
    # Core Application Settings (from Settings model)
    $env:DEBUG = "true"
    $env:ENVIRONMENT = "development"
    $env:SECRET_KEY = "your-secret-key-must-be-at-least-16-chars-long"
    $env:ALGORITHM = "HS256"
    $env:ACCESS_TOKEN_EXPIRE_MINUTES = "30"
    
    # Database
    $env:DATABASE_URL = "postgresql://healthcare_user:healthcare_pass@localhost:5432/healthcare_db"
    $env:DATABASE_POOL_SIZE = "5"
    $env:DATABASE_MAX_OVERFLOW = "10"
    
    # IRIS API (with defaults from model)
    $env:IRIS_API_BASE_URL = "https://api.mock-iris.com/v1"
    $env:IRIS_API_TIMEOUT = "30"
    $env:IRIS_API_RETRY_ATTEMPTS = "3"
    
    # Encryption (will use defaults if not set - auto-generated)
    $env:ENCRYPTION_KEY = "your-encryption-key-must-be-at-least-16-chars-long"
    
    # Audit Logging
    $env:AUDIT_LOG_RETENTION_DAYS = "2555"
    $env:AUDIT_LOG_ENCRYPTION = "true"
    
    # Purge Scheduler
    $env:PURGE_CHECK_INTERVAL_MINUTES = "60"
    $env:DEFAULT_RETENTION_DAYS = "90"
    $env:ENABLE_EMERGENCY_PURGE_SUSPENSION = "true"
    
    # Redis
    $env:REDIS_URL = "redis://localhost:6379/0"
    
    # CORS - Note: This expects a JSON list format
    $env:ALLOWED_ORIGINS = '["http://localhost:3000", "http://localhost:8000"]'
    
    # Rate Limiting
    $env:RATE_LIMIT_REQUESTS_PER_MINUTE = "100"
    $env:RATE_LIMIT_BURST = "20"
    
    # Performance Settings
    $env:API_RESPONSE_COMPRESSION = "true"
    $env:API_CACHE_TTL_SECONDS = "300"
    $env:API_MAX_RESPONSE_SIZE_MB = "50"
    
    # Database Performance
    $env:DB_QUERY_TIMEOUT_SECONDS = "30"
    $env:DB_CONNECTION_POOL_RECYCLE = "3600"
    $env:DB_ENABLE_QUERY_LOGGING = "false"
    $env:DB_SLOW_QUERY_THRESHOLD_MS = "1000"
    
    # Performance Monitoring
    $env:ENABLE_PERFORMANCE_MONITORING = "true"
    $env:METRICS_COLLECTION_INTERVAL = "60"
    $env:PERFORMANCE_ALERTS_ENABLED = "true"
    
    # OpenTelemetry
    $env:OTEL_ENABLED = "true"
    $env:OTEL_SERVICE_NAME = "iris-healthcare-api"
    $env:OTEL_SAMPLE_RATE = "0.1"
    
    # Prometheus
    $env:PROMETHEUS_ENABLED = "true"
    $env:PROMETHEUS_PORT = "8001"
    $env:PROMETHEUS_NAMESPACE = "iris_healthcare"
    
    # Load Testing
    $env:LOAD_TESTING_ENABLED = "false"
    $env:MAX_CONCURRENT_REQUESTS = "1000"
    $env:REQUEST_QUEUE_SIZE = "5000"
    
    # Security
    $env:ENABLE_GEOGRAPHIC_BLOCKING = "false"
    $env:ALLOWED_COUNTRIES = '["US", "CA"]'
    
    # System Alerts
    $env:CPU_ALERT_THRESHOLD = "80.0"
    $env:MEMORY_ALERT_THRESHOLD = "85.0"
    $env:DISK_ALERT_THRESHOLD = "90.0"
    
    # Caching
    $env:REDIS_CACHE_TTL = "3600"
    $env:ENABLE_QUERY_RESULT_CACHING = "true"
    $env:CACHE_WARMUP_ENABLED = "true"
    
    # Advanced Security
    $env:ADVANCED_THREAT_DETECTION = "true"
    $env:IP_REPUTATION_CHECKING = "true"
    $env:USER_AGENT_VALIDATION = "true"
    
    # File Monitoring
    $env:ENABLE_FILE_MONITORING = "true"
    $env:MONITORED_DIRECTORIES = '["/app/logs", "/app/data"]'
    
    Write-Host "All required environment variables set!" -ForegroundColor Green
    Write-Host "Total variables set: $((Get-ChildItem env: | Where-Object { $_.Name -match '^(DEBUG|ENVIRONMENT|SECRET_KEY|ALGORITHM|ACCESS_TOKEN|DATABASE|IRIS_API|ENCRYPTION|AUDIT|PURGE|REDIS|ALLOWED|RATE_LIMIT|API_|DB_|ENABLE_|OTEL|PROMETHEUS|LOAD_TESTING|MAX_CONCURRENT|REQUEST_QUEUE|GEOGRAPHIC|CPU_ALERT|MEMORY_ALERT|DISK_ALERT|CACHE|ADVANCED_THREAT|IP_REPUTATION|USER_AGENT|FILE_MONITORING|MONITORED)' }).Count)" -ForegroundColor Gray
    
    Write-Host "`nStarting FastAPI server..." -ForegroundColor Green
    Write-Host "Server endpoints:" -ForegroundColor Cyan
    Write-Host "  Main application: http://localhost:8000" -ForegroundColor White
    Write-Host "  Health check: http://localhost:8000/health" -ForegroundColor White
    Write-Host "  Healthcare API: http://localhost:8000/api/v1/healthcare-records/health" -ForegroundColor White
    Write-Host "  API documentation: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  Prometheus metrics: http://localhost:8001" -ForegroundColor White
    Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Yellow
    
    # Start the server
    & python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    
}
catch {
    Write-Host "Error starting server: $($_.Exception.Message)" -ForegroundColor Red
    
    Write-Host "`nTrying without reload (more stable)..." -ForegroundColor Yellow
    try {
        & python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
    }
    catch {
        Write-Host "Server startup failed: $($_.Exception.Message)" -ForegroundColor Red
        
        Write-Host "`nDebug information:" -ForegroundColor Cyan
        Write-Host "Current directory: $(Get-Location)" -ForegroundColor Gray
        Write-Host "Python version: $(python --version 2>&1)" -ForegroundColor Gray
        Write-Host "FastAPI installed: $((python -c 'import fastapi; print(fastapi.__version__)' 2>&1))" -ForegroundColor Gray
        Write-Host "Uvicorn installed: $((python -c 'import uvicorn; print(uvicorn.__version__)' 2>&1))" -ForegroundColor Gray
        
        Write-Host "`nTrying direct execution as fallback..." -ForegroundColor Yellow
        try {
            $env:PYTHONPATH = (Get-Location).Path
            & python app/main.py
        }
        catch {
            Write-Host "All startup methods failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}
finally {
    Pop-Location
    Write-Host "`nApplication stopped." -ForegroundColor Yellow
    Write-Host "Run .\working_test.ps1 to test all services." -ForegroundColor Cyan
}