# Healthcare Monitoring Stack - Fix and Deploy Script
# This script fixes configuration issues and deploys the monitoring stack

Write-Host "🏥 Healthcare Monitoring Stack - Fix and Deploy" -ForegroundColor Green
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

# Check if services are responding
Write-Host "`n8. Testing service connectivity..." -ForegroundColor Yellow

$services = @{
    "Prometheus" = "http://localhost:9090/-/healthy"
    "Grafana" = "http://localhost:3000/api/health"
    "Alertmanager" = "http://localhost:9093/-/healthy"
    "Node Exporter" = "http://localhost:9100/metrics"
}

foreach ($service in $services.GetEnumerator()) {
    try {
        $response = Invoke-WebRequest -Uri $service.Value -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $($service.Key): OK" -ForegroundColor Green
        } else {
            Write-Host "⚠️  $($service.Key): Status $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ $($service.Key): Not responding" -ForegroundColor Red
    }
}

# Display access URLs
Write-Host "`n🎉 Deployment Complete!" -ForegroundColor Green
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

# Show logs if there are issues
Write-Host "9. Checking for any service errors..." -ForegroundColor Yellow
$logs = docker-compose -f docker-compose.monitoring-only.yml logs --tail=5 2>&1
if ($logs -match "error|Error|ERROR|failed|Failed|FAILED") {
    Write-Host "⚠️  Some services may have errors. Check logs with:" -ForegroundColor Yellow
    Write-Host "docker-compose -f docker-compose.monitoring-only.yml logs [service-name]" -ForegroundColor Gray
} else {
    Write-Host "✅ All services appear to be running without critical errors" -ForegroundColor Green
}

Write-Host "`n📊 Healthcare Monitoring Stack is ready!" -ForegroundColor Green
Write-Host "Open http://localhost:3000 in your browser to access Grafana" -ForegroundColor Cyan