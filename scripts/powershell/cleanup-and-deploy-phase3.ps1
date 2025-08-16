# Cleanup and Deploy Phase 3
Write-Host "Cleaning up existing Phase 3 containers..." -ForegroundColor Yellow

# Stop and remove existing Phase 3 containers
docker-compose -f docker-compose.phase3.yml down --remove-orphans 2>$null

# Remove any conflicting containers by name
$phase3Containers = @(
    "iris_grafana_p3",
    "iris_jaeger_p3", 
    "iris_elasticsearch_p3",
    "iris_kibana_p3",
    "iris_logstash_p3",
    "iris_app_advanced_p3"
)

foreach ($container in $phase3Containers) {
    try {
        docker rm -f $container 2>$null
        Write-Host "   Removed: $container" -ForegroundColor Gray
    } catch {
        # Container doesn't exist, which is fine
    }
}

Write-Host "   Cleanup complete" -ForegroundColor Green

# Set environment variables
$env:SECRET_KEY = '3h5dPMCVjESdKNEJFcpgr2pkyb8hLfImMkgBLIJjX8+CBeNHbfLm5s0TZjrKPr4qwvsK3RUU2+dimXdGWSOqAg=='
$env:ENCRYPTION_KEY = 'wLS/8tedW1PE0EoZZLcuWhfIul5+xg05OJVISJHnr/E='
$env:JWT_SECRET_KEY = 'aUEoE2V9yrejA9RdlbyDylcN2NY7fNGEkvmVN7FH+hHkiRzlLIdbYBnitaSwyZiiBmagumE/wcnK6BQ52WUv2Q=='
$env:PHI_ENCRYPTION_KEY = 'xJM+yHn5/5RwwEvOHhRkP01DbbX7wxf1TWEOPOJV+sM='
$env:AUDIT_SIGNING_KEY = 'ac8b33202bb1fafe9bac30d568b51128f05d05a116651cb0b5daf8de55ecb1400261e9ab33c9f2a2de44b203e8ef368bb579e1712527c7d71188be4b7a8cd956'

# Deploy Phase 3
Write-Host "`nDeploying Phase 3 Advanced Analytics..." -ForegroundColor Cyan
docker-compose -f docker-compose.phase3.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "   FAILED: Phase 3 deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host "   PASSED: Phase 3 services started" -ForegroundColor Green

Write-Host "`nPhase 3 Advanced Analytics URLs:" -ForegroundColor Cyan
Write-Host "  Advanced Application:  http://localhost:8002" -ForegroundColor White
Write-Host "  API Documentation:     http://localhost:8002/docs" -ForegroundColor White
Write-Host "  Grafana Dashboards:    http://localhost:3001" -ForegroundColor White
Write-Host "  Jaeger Tracing:        http://localhost:16686" -ForegroundColor White
Write-Host "  Kibana Logs:           http://localhost:5601" -ForegroundColor White
Write-Host "  ElasticSearch:         http://localhost:9200" -ForegroundColor White

Write-Host "`nFULL ENTERPRISE HEALTHCARE PLATFORM: OPERATIONAL" -ForegroundColor Green