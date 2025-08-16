# Set environment variables for deployment
$env:SECRET_KEY = '3h5dPMCVjESdKNEJFcpgr2pkyb8hLfImMkgBLIJjX8+CBeNHbfLm5s0TZjrKPr4qwvsK3RUU2+dimXdGWSOqAg=='
$env:ENCRYPTION_KEY = 'wLS/8tedW1PE0EoZZLcuWhfIul5+xg05OJVISJHnr/E='
$env:JWT_SECRET_KEY = 'aUEoE2V9yrejA9RdlbyDylcN2NY7fNGEkvmVN7FH+hHkiRzlLIdbYBnitaSwyZiiBmagumE/wcnK6BQ52WUv2Q=='  
$env:DATABASE_URL = 'postgresql://postgres:password@localhost:5432/iris_db'
$env:REDIS_URL = 'redis://localhost:6379/0'
$env:PHI_ENCRYPTION_KEY = 'xJM+yHn5/5RwwEvOHhRkP01DbbX7wxf1TWEOPOJV+sM='
$env:MINIO_ACCESS_KEY = 'Jqxh7ZTNKjGRChtjGX9f'
$env:MINIO_SECRET_KEY = '692pek0uzf9wDUZvVWEDom5J6/UxRXdrU+p3b9dQmarT44zDJqYHvg=='
$env:AUDIT_SIGNING_KEY = 'ac8b33202bb1fafe9bac30d568b51128f05d05a116651cb0b5daf8de55ecb1400261e9ab33c9f2a2de44b203e8ef368bb579e1712527c7d71188be4b7a8cd956'
$env:SOC2_COMPLIANCE_MODE = 'true'
$env:DATABASE_PASSWORD = 'password'
$env:REDIS_PASSWORD = 'redis_password'
$env:ORTHANC_API_KEY = 'iris_key'

Write-Host "Environment variables set successfully!" -ForegroundColor Green

# Now run the Phase 2 deployment
Write-Host "Starting Phase 2 deployment..." -ForegroundColor Cyan
& ".\deploy-phase2.ps1"