# Healthcare Monitoring Stack - Fix Configuration Issues
# This script fixes YAML configuration errors and deploys stable services

Write-Host "Healthcare Monitoring - Configuration Fix" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

# Stop all containers
Write-Host "`n1. Stopping all containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.monitoring-only.yml down

# Fix Grafana dashboards configuration (YAML syntax error)
Write-Host "`n2. Fixing Grafana dashboards configuration..." -ForegroundColor Yellow
$grafanaDashboardConfig = @"
apiVersion: 1
providers:
- name: default
  orgId: 1
  folder: ""
  type: file
  disableDeletion: false
  updateIntervalSeconds: 10
  allowUiUpdates: true
  options:
    path: /var/lib/grafana/dashboards
"@
$grafanaDashboardConfig | Out-File "grafana\dashboards\dashboards.yml" -Encoding UTF8

# Fix Grafana datasources configuration
Write-Host "`n3. Fixing Grafana datasources configuration..." -ForegroundColor Yellow
$grafanaDataSourceConfig = @"
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
"@
$grafanaDataSourceConfig | Out-File "grafana\datasources\datasources.yml" -Encoding UTF8

# Fix Prometheus config - remove problematic remote_write section
Write-Host "`n4. Fixing Prometheus configuration..." -ForegroundColor Yellow
$prometheusContent = Get-Content "prometheus\prometheus.yml"
$fixedContent = $prometheusContent | Where-Object {$_ -notmatch "^# Remote write|^remote_write:|^  - url:|^    basic_auth:|^    username:|^    password:|^    write_relabel_configs:|^      - source_labels:|^        regex:|^        action:"}
$fixedContent | Out-File "prometheus\prometheus.yml" -Encoding UTF8

# Verify fixed configurations
Write-Host "`n5. Verifying fixed configurations..." -ForegroundColor Yellow
Write-Host "Grafana dashboards config:" -ForegroundColor Cyan
Get-Content "grafana\dashboards\dashboards.yml"

Write-Host "`nGrafana datasources config:" -ForegroundColor Cyan
Get-Content "grafana\datasources\datasources.yml" 

Write-Host "`nPrometheus config (last 5 lines):" -ForegroundColor Cyan
Get-Content "prometheus\prometheus.yml" | Select-Object -Last 5

# Start core services first (without problematic ones)
Write-Host "`n6. Starting core monitoring services..." -ForegroundColor Yellow
docker-compose -f docker-compose.monitoring-only.yml up -d grafana node-exporter blackbox-exporter cadvisor

# Wait for services to initialize
Write-Host "`n7. Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

# Check status of core services
Write-Host "`n8. Checking core services status..." -ForegroundColor Yellow
docker-compose -f docker-compose.monitoring-only.yml ps

# Test Grafana connectivity
Write-Host "`n9. Testing service connectivity..." -ForegroundColor Yellow

$services = @{
    "Grafana" = "http://localhost:3000/api/health"
    "Node Exporter" = "http://localhost:9100/metrics"
    "Blackbox Exporter" = "http://localhost:9115"
    "cAdvisor" = "http://localhost:8080/containers/"
}

foreach ($service in $services.GetEnumerator()) {
    try {
        $response = Invoke-WebRequest -Uri $service.Value -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $($service.Key): Working" -ForegroundColor Green
        } else {
            Write-Host "⚠️  $($service.Key): Status $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ $($service.Key): Not responding" -ForegroundColor Red
    }
}

# Try to start Prometheus and Alertmanager
Write-Host "`n10. Attempting to start Prometheus and Alertmanager..." -ForegroundColor Yellow
docker-compose -f docker-compose.monitoring-only.yml up -d prometheus alertmanager

Start-Sleep -Seconds 15

# Final status check
Write-Host "`n11. Final status check..." -ForegroundColor Yellow
docker-compose -f docker-compose.monitoring-only.yml ps

# Display results
Write-Host "`nConfiguration Fix Complete!" -ForegroundColor Green
Write-Host "============================" -ForegroundColor Green
Write-Host ""
Write-Host "Working Services:" -ForegroundColor Cyan
Write-Host "• Grafana Dashboard: http://localhost:3000" -ForegroundColor White
Write-Host "  Username: admin" -ForegroundColor Gray
Write-Host "  Password: healthcare_admin_2025" -ForegroundColor Gray
Write-Host "• Node Exporter: http://localhost:9100" -ForegroundColor White
Write-Host "• Blackbox Exporter: http://localhost:9115" -ForegroundColor White
Write-Host "• cAdvisor: http://localhost:8080" -ForegroundColor White
Write-Host ""

# Check if Prometheus is now working
try {
    $promResponse = Invoke-WebRequest -Uri "http://localhost:9090" -TimeoutSec 5 -UseBasicParsing
    Write-Host "• Prometheus: http://localhost:9090" -ForegroundColor White
} catch {
    Write-Host "• Prometheus: Still having issues (check logs)" -ForegroundColor Yellow
}

try {
    $alertResponse = Invoke-WebRequest -Uri "http://localhost:9093" -TimeoutSec 5 -UseBasicParsing
    Write-Host "• Alertmanager: http://localhost:9093" -ForegroundColor White
} catch {
    Write-Host "• Alertmanager: Still having issues (check logs)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Primary dashboard ready at: http://localhost:3000" -ForegroundColor Green
Write-Host "Login with admin/healthcare_admin_2025" -ForegroundColor Cyan