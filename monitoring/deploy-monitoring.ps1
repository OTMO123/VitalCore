# Healthcare Monitoring Stack - Fix and Deploy Script
# This script fixes configuration issues and deploys the monitoring stack

Write-Host "Healthcare Monitoring Stack - Fix and Deploy" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# Stop any running containers
Write-Host "`n1. Stopping existing containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.monitoring-only.yml down

# Fix Grafana datasource configuration
Write-Host "`n2. Fixing Grafana datasource configuration..." -ForegroundColor Yellow
$grafanaConfig = @"
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
"@
$grafanaConfig | Out-File "grafana\datasources\datasources.yml" -Encoding UTF8

# Fix Prometheus configuration by removing invalid storage section
Write-Host "`n3. Fixing Prometheus configuration..." -ForegroundColor Yellow
$content = Get-Content "prometheus\prometheus.yml"
$newContent = $content | Where-Object {$_ -notmatch "^# Storage configuration|^storage:|^  tsdb:|retention\.|wal-compression"}
$newContent | Out-File "prometheus\prometheus.yml" -Encoding UTF8

# Verify configurations
Write-Host "`n4. Verifying configurations..." -ForegroundColor Yellow
Write-Host "Grafana datasource config:" -ForegroundColor Cyan
Get-Content "grafana\datasources\datasources.yml"

Write-Host "`nLast 5 lines of Prometheus config:" -ForegroundColor Cyan
Get-Content "prometheus\prometheus.yml" | Select-Object -Last 5

# Deploy the monitoring stack
Write-Host "`n5. Deploying monitoring stack..." -ForegroundColor Yellow
docker-compose -f docker-compose.monitoring-only.yml up -d

# Wait for services to start
Write-Host "`n6. Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check status
Write-Host "`n7. Checking service status..." -ForegroundColor Yellow
docker-compose -f docker-compose.monitoring-only.yml ps

# Display access URLs
Write-Host "`nDeployment Complete!" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green
Write-Host ""
Write-Host "Access URLs:" -ForegroundColor Cyan
Write-Host "• Grafana Dashboard: http://localhost:3000" -ForegroundColor White
Write-Host "  Username: admin" -ForegroundColor Gray
Write-Host "  Password: healthcare_admin_2025" -ForegroundColor Gray
Write-Host "• Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host "• Alertmanager: http://localhost:9093" -ForegroundColor White
Write-Host "• Node Exporter: http://localhost:9100" -ForegroundColor White
Write-Host "• cAdvisor: http://localhost:8080" -ForegroundColor White
Write-Host "• Loki: http://localhost:3100" -ForegroundColor White
Write-Host ""

Write-Host "Healthcare Monitoring Stack is ready!" -ForegroundColor Green
Write-Host "Open http://localhost:3000 to access Grafana" -ForegroundColor Cyan