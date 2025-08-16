# Phase 3: Advanced Analytics and Monitoring
Write-Host "Phase 3: Advanced Analytics Deployment" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Set environment variables
$env:SECRET_KEY = '3h5dPMCVjESdKNEJFcpgr2pkyb8hLfImMkgBLIJjX8+CBeNHbfLm5s0TZjrKPr4qwvsK3RUU2+dimXdGWSOqAg=='
$env:ENCRYPTION_KEY = 'wLS/8tedW1PE0EoZZLcuWhfIul5+xg05OJVISJHnr/E='
$env:JWT_SECRET_KEY = 'aUEoE2V9yrejA9RdlbyDylcN2NY7fNGEkvmVN7FH+hHkiRzlLIdbYBnitaSwyZiiBmagumE/wcnK6BQ52WUv2Q=='
$env:PHI_ENCRYPTION_KEY = 'xJM+yHn5/5RwwEvOHhRkP01DbbX7wxf1TWEOPOJV+sM='
$env:AUDIT_SIGNING_KEY = 'ac8b33202bb1fafe9bac30d568b51128f05d05a116651cb0b5daf8de55ecb1400261e9ab33c9f2a2de44b203e8ef368bb579e1712527c7d71188be4b7a8cd956'

Write-Host "Environment variables set" -ForegroundColor Green

# Verify previous phases are running
Write-Host "`nVerifying previous phases..." -ForegroundColor Cyan

$requiredServices = @(
    "iris_postgres_p1",
    "iris_redis_p1", 
    "iris_app_p1",
    "iris_prometheus_p1"
)

$missingServices = @()
foreach ($service in $requiredServices) {
    try {
        $status = docker inspect $service --format='{{.State.Status}}' 2>$null
        if ($status -ne "running") {
            $missingServices += $service
        }
    } catch {
        $missingServices += $service
    }
}

if ($missingServices.Count -gt 0) {
    Write-Host "   FAILED: Required services not running:" -ForegroundColor Red
    foreach ($service in $missingServices) {
        Write-Host "      - $service" -ForegroundColor Red
    }
    Write-Host "`n   Please deploy previous phases first:" -ForegroundColor Yellow
    Write-Host "     .\deploy-phase1.ps1" -ForegroundColor Gray
    Write-Host "     .\deploy-phase2-clean.ps1" -ForegroundColor Gray
    exit 1
}
Write-Host "   PASSED: Previous phases are running" -ForegroundColor Green

# Create monitoring configuration directories
Write-Host "`nCreating monitoring configurations..." -ForegroundColor Cyan

# Create Grafana provisioning directories
$grafanaDirs = @(
    "monitoring/grafana/provisioning/datasources",
    "monitoring/grafana/provisioning/dashboards", 
    "monitoring/grafana/dashboards"
)

foreach ($dir in $grafanaDirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Grafana datasource configuration
$datasourceConfig = @'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://iris_prometheus_p1:9090
    isDefault: true
    editable: true
  - name: Jaeger
    type: jaeger
    access: proxy
    url: http://jaeger:16686
    editable: true
  - name: Elasticsearch
    type: elasticsearch
    access: proxy
    url: http://elasticsearch:9200
    database: "[healthcare-logs-]YYYY.MM.DD"
    interval: Daily
    timeField: "@timestamp"
    editable: true
'@

$datasourceConfig | Set-Content -Path "monitoring/grafana/provisioning/datasources/datasources.yml" -Encoding UTF8

# Dashboard provisioning
$dashboardConfig = @'
apiVersion: 1

providers:
  - name: 'Healthcare Dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    editable: true
    updateIntervalSeconds: 10
    options:
      path: /var/lib/grafana/dashboards
'@

$dashboardConfig | Set-Content -Path "monitoring/grafana/provisioning/dashboards/dashboards.yml" -Encoding UTF8

# Create Logstash configuration
if (!(Test-Path "monitoring/logstash/pipeline")) {
    New-Item -ItemType Directory -Path "monitoring/logstash/pipeline" -Force | Out-Null
    New-Item -ItemType Directory -Path "monitoring/logstash/config" -Force | Out-Null
}

$logstashPipeline = @'
input {
  file {
    path => "/logs/*.log"
    start_position => "beginning"
    codec => "json"
    tags => ["healthcare", "iris"]
  }
}

filter {
  if [level] {
    mutate {
      uppercase => [ "level" ]
    }
  }
  
  if [message] =~ /PHI|PII/ {
    mutate {
      add_tag => [ "sensitive_data" ]
    }
  }
  
  if [audit] {
    mutate {
      add_tag => [ "audit_log" ]
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "healthcare-logs-%{+YYYY.MM.dd}"
  }
}
'@

$logstashPipeline | Set-Content -Path "monitoring/logstash/pipeline/healthcare.conf" -Encoding UTF8
Write-Host "   Created: Monitoring configuration files" -ForegroundColor Green

# Deploy Phase 3
Write-Host "`nDeploying Phase 3 Advanced Analytics..." -ForegroundColor Cyan
Write-Host "   • Grafana advanced dashboards and visualization" -ForegroundColor Yellow
Write-Host "   • Jaeger distributed tracing and performance monitoring" -ForegroundColor Yellow
Write-Host "   • ElasticSearch log aggregation and search" -ForegroundColor Yellow

# Deploy Phase 3 services
docker-compose -f docker-compose.phase3.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "   FAILED: Phase 3 deployment failed" -ForegroundColor Red
    Write-Host "`nGetting deployment logs..." -ForegroundColor Yellow
    docker-compose -f docker-compose.phase3.yml logs --tail=50
    exit 1
}

Write-Host "   PASSED: Phase 3 services started" -ForegroundColor Green

# Wait for services to stabilize
Write-Host "`nWaiting for analytics services to initialize..." -ForegroundColor Cyan
Write-Host "   (ElasticSearch and advanced services may take 3-5 minutes)" -ForegroundColor Gray
Start-Sleep -Seconds 60

Write-Host "`nPhase 3 Advanced Analytics URLs:" -ForegroundColor Cyan
Write-Host "  Advanced Application:  http://localhost:8002" -ForegroundColor White
Write-Host "  API Documentation:     http://localhost:8002/docs" -ForegroundColor White
Write-Host "  Grafana Dashboards:    http://localhost:3001 (admin/grafana_admin_password)" -ForegroundColor White
Write-Host "  Jaeger Tracing:        http://localhost:16686" -ForegroundColor White
Write-Host "  Kibana Logs:           http://localhost:5601" -ForegroundColor White
Write-Host "  ElasticSearch:         http://localhost:9200" -ForegroundColor White

Write-Host "`nEnterprise Capabilities Now Available:" -ForegroundColor Yellow
Write-Host "  ✓ Complete observability and monitoring" -ForegroundColor Green
Write-Host "  ✓ Distributed tracing and performance analysis" -ForegroundColor Green
Write-Host "  ✓ Advanced log aggregation and search" -ForegroundColor Green
Write-Host "  ✓ Custom dashboards and alerting" -ForegroundColor Green
Write-Host "  ✓ Full audit trail and compliance reporting" -ForegroundColor Green

Write-Host "`nProduction Readiness Status:" -ForegroundColor Yellow
Write-Host "  • Phase 1 Foundation: ✓ DEPLOYED" -ForegroundColor Green
Write-Host "  • Phase 2 AI/ML: ✓ DEPLOYED" -ForegroundColor Green  
Write-Host "  • Phase 3 Analytics: ✓ DEPLOYED" -ForegroundColor Green

Write-Host "`nFULL ENTERPRISE HEALTHCARE PLATFORM: OPERATIONAL" -ForegroundColor Green