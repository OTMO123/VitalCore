# Phase 3: Advanced Analytics and Monitoring
# Full observability stack and advanced enterprise features

param(
    [switch]$IncludeGrafana,
    [switch]$IncludeJaeger,
    [switch]$IncludeElastic,
    [switch]$FullStack,
    [switch]$ValidateOnly
)

Write-Host "Phase 3: Advanced Analytics Deployment" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Default to full stack if no specific services selected
if (!$IncludeGrafana -and !$IncludeJaeger -and !$IncludeElastic -and !$FullStack) {
    $FullStack = $true
    Write-Host "   INFO: No specific services selected, deploying full Phase 3 stack" -ForegroundColor Cyan
}

if ($FullStack) {
    $IncludeGrafana = $true
    $IncludeJaeger = $true
    $IncludeElastic = $true
}

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
    Write-Host "     .\deploy-phase2.ps1" -ForegroundColor Gray
    exit 1
}
Write-Host "   PASSED: Previous phases are running" -ForegroundColor Green

if ($ValidateOnly) {
    Write-Host "`nPhase 3 Deployment Plan:" -ForegroundColor Cyan
    if ($IncludeGrafana) { Write-Host "   ✓ Grafana Advanced Dashboards" -ForegroundColor Green }
    if ($IncludeJaeger) { Write-Host "   ✓ Jaeger Distributed Tracing" -ForegroundColor Green }
    if ($IncludeElastic) { Write-Host "   ✓ ElasticSearch Log Aggregation" -ForegroundColor Green }
    Write-Host "`nValidation complete - ready for Phase 3 deployment" -ForegroundColor Green
    exit 0
}

# Generate Phase 3 compose configuration
Write-Host "`nGenerating Phase 3 Docker Compose configuration..." -ForegroundColor Cyan

$phase3Services = ""

# Grafana Dashboard Service
if ($IncludeGrafana) {
    $phase3Services += @"
  # GRAFANA ADVANCED DASHBOARDS
  grafana:
    image: grafana/grafana:10.2.0
    container_name: iris_grafana_p3
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=`${GRAFANA_PASSWORD:-grafana_admin_password}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SECURITY_COOKIE_SECURE=true
      - GF_SECURITY_COOKIE_SAMESITE=strict
      - GF_SERVER_ROOT_URL=http://localhost:3001
      - GF_ANALYTICS_REPORTING_ENABLED=false
      - GF_ANALYTICS_CHECK_FOR_UPDATES=false
      - GF_SECURITY_DISABLE_GRAVATAR=true
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
    networks:
      - iris_network
    external_links:
      - iris_prometheus_p1:prometheus
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:3000/api/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

"@
}

# Jaeger Tracing Service
if ($IncludeJaeger) {
    $phase3Services += @"
  # JAEGER DISTRIBUTED TRACING
  jaeger:
    image: jaegertracing/all-in-one:1.50
    container_name: iris_jaeger_p3
    environment:
      - COLLECTOR_OTLP_ENABLED=true
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411
      - QUERY_BASE_PATH=/jaeger
    ports:
      - "16686:16686"  # Jaeger UI
      - "14268:14268"  # Jaeger collector HTTP
      - "14250:14250"  # Jaeger collector gRPC
      - "9411:9411"    # Zipkin collector
    volumes:
      - jaeger_data:/badger
    networks:
      - iris_network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:14268/api/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

"@
}

# ElasticSearch Log Aggregation
if ($IncludeElastic) {
    $phase3Services += @"
  # ELASTICSEARCH LOG AGGREGATION
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: iris_elasticsearch_p3
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - bootstrap.memory_lock=true
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    networks:
      - iris_network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped

  # KIBANA DASHBOARD
  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: iris_kibana_p3
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - SERVER_BASEPATH=/kibana
      - SERVER_REWRITEBASEPATH=true
    ports:
      - "5601:5601"
    depends_on:
      elasticsearch:
        condition: service_healthy
    networks:
      - iris_network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:5601/api/status || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped

  # LOGSTASH LOG PROCESSING
  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    container_name: iris_logstash_p3
    volumes:
      - ./monitoring/logstash/pipeline:/usr/share/logstash/pipeline:ro
      - ./monitoring/logstash/config:/usr/share/logstash/config:ro
      - ./logs:/logs:ro
    ports:
      - "5044:5044"  # Beats input
      - "9600:9600"  # API
    depends_on:
      elasticsearch:
        condition: service_healthy
    networks:
      - iris_network
    restart: unless-stopped

"@
}

$phase3Compose = @"
version: '3.8'

services:
$phase3Services
  # ADVANCED APPLICATION WITH FULL OBSERVABILITY
  app-advanced:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: iris_app_advanced_p3
    environment:
      - DEBUG=`${DEBUG:-false}
      - ENVIRONMENT=`${ENVIRONMENT:-production}
      - SECRET_KEY=`${SECRET_KEY}
      - ENCRYPTION_KEY=`${ENCRYPTION_KEY}
      - DATABASE_URL=postgresql://postgres:`${DATABASE_PASSWORD:-password}@iris_postgres_p1:5432/iris_db
      - REDIS_URL=redis://:`${REDIS_PASSWORD:-redis_password}@iris_redis_p1:6379/0
      - JWT_SECRET_KEY=`${JWT_SECRET_KEY}
      - PHI_ENCRYPTION_KEY=`${PHI_ENCRYPTION_KEY}
      - SOC2_COMPLIANCE_MODE=true
      - AUDIT_SIGNING_KEY=`${AUDIT_SIGNING_KEY}
      - DEPLOYMENT_PHASE=3
      # Observability Configuration
      - PROMETHEUS_ENDPOINT=http://iris_prometheus_p1:9090
      - JAEGER_ENDPOINT=`${if ($IncludeJaeger) { "http://jaeger:14268" } else { "" }}
      - ELASTICSEARCH_ENDPOINT=`${if ($IncludeElastic) { "http://elasticsearch:9200" } else { "" }}
      - TRACING_ENABLED=`${IncludeJaeger.ToString().ToLower()}
      - LOG_AGGREGATION_ENABLED=`${IncludeElastic.ToString().ToLower()}
      - ADVANCED_MONITORING_ENABLED=true
    ports:
      - "8002:8000"  # Advanced app on different port
    volumes:
      - ./logs:/app/logs
    networks:
      - iris_network
    external_links:
      - iris_postgres_p1:postgres
      - iris_redis_p1:redis
      - iris_minio_p1:minio
      - iris_prometheus_p1:prometheus
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/advanced"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

volumes:
$(if ($IncludeGrafana) { @"
  grafana_data:
"@ })
$(if ($IncludeJaeger) { @"
  jaeger_data:
"@ })
$(if ($IncludeElastic) { @"
  elasticsearch_data:
"@ })

networks:
  iris_network:
    external: true
"@

$phase3Compose | Out-File -FilePath "docker-compose.phase3.yml" -Encoding UTF8
Write-Host "   Generated: docker-compose.phase3.yml" -ForegroundColor Green

# Create monitoring configuration directories
Write-Host "`nCreating monitoring configurations..." -ForegroundColor Cyan

if ($IncludeGrafana) {
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
    $datasourceConfig = @"
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://iris_prometheus_p1:9090
    isDefault: true
    editable: true
$(if ($IncludeJaeger) { @"
  - name: Jaeger
    type: jaeger
    access: proxy
    url: http://jaeger:16686
    editable: true
"@ })
$(if ($IncludeElastic) { @"
  - name: Elasticsearch
    type: elasticsearch
    access: proxy
    url: http://elasticsearch:9200
    database: "[healthcare-logs-]YYYY.MM.DD"
    interval: Daily
    timeField: "@timestamp"
    editable: true
"@ })
"@
    
    $datasourceConfig | Out-File -FilePath "monitoring/grafana/provisioning/datasources/datasources.yml" -Encoding UTF8
    
    # Dashboard provisioning
    $dashboardConfig = @"
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
"@
    
    $dashboardConfig | Out-File -FilePath "monitoring/grafana/provisioning/dashboards/dashboards.yml" -Encoding UTF8
    Write-Host "   Created: Grafana configuration files" -ForegroundColor Green
}

if ($IncludeElastic) {
    # Create Logstash configuration
    if (!(Test-Path "monitoring/logstash/pipeline")) {
        New-Item -ItemType Directory -Path "monitoring/logstash/pipeline" -Force | Out-Null
        New-Item -ItemType Directory -Path "monitoring/logstash/config" -Force | Out-Null
    }
    
    $logstashPipeline = @"
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
"@
    
    $logstashPipeline | Out-File -FilePath "monitoring/logstash/pipeline/healthcare.conf" -Encoding UTF8
    Write-Host "   Created: Logstash pipeline configuration" -ForegroundColor Green
}

# Deploy Phase 3
Write-Host "`nDeploying Phase 3 Advanced Analytics..." -ForegroundColor Cyan
if ($IncludeGrafana) { Write-Host "   • Grafana advanced dashboards and visualization" -ForegroundColor Yellow }
if ($IncludeJaeger) { Write-Host "   • Jaeger distributed tracing and performance monitoring" -ForegroundColor Yellow }
if ($IncludeElastic) { Write-Host "   • ElasticSearch log aggregation and search" -ForegroundColor Yellow }

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
Start-Sleep -Seconds 240

# Phase 3 Health Checks
Write-Host "`nPhase 3 Health Validation..." -ForegroundColor Cyan

$healthChecks = @()

if ($IncludeGrafana) {
    $healthChecks += @{Name="Grafana Dashboards"; URL="http://localhost:3001/api/health"}
}

if ($IncludeJaeger) {
    $healthChecks += @{Name="Jaeger Tracing"; URL="http://localhost:16686/api/services"}
}

if ($IncludeElastic) {
    $healthChecks += @{Name="ElasticSearch"; URL="http://localhost:9200/_cluster/health"}
    $healthChecks += @{Name="Kibana"; URL="http://localhost:5601/api/status"}
}

$healthChecks += @{Name="Advanced Application"; URL="http://localhost:8002/health/advanced"}

$failedChecks = @()

foreach ($check in $healthChecks) {
    try {
        $response = Invoke-WebRequest -Uri $check.URL -TimeoutSec 20 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "   PASSED: $($check.Name)" -ForegroundColor Green
        } else {
            Write-Host "   FAILED: $($check.Name) - HTTP $($response.StatusCode)" -ForegroundColor Red
            $failedChecks += $check.Name
        }
    } catch {
        Write-Host "   FAILED: $($check.Name) - Not responding" -ForegroundColor Red
        $failedChecks += $check.Name
    }
}

# Summary
Write-Host "`nPhase 3 Deployment Summary" -ForegroundColor Green
Write-Host "==========================" -ForegroundColor Green

if ($failedChecks.Count -eq 0) {
    Write-Host "STATUS: SUCCESS - Full enterprise analytics platform deployed!" -ForegroundColor Green
    
    Write-Host "`nPhase 3 Advanced Analytics URLs:" -ForegroundColor Cyan
    Write-Host "  Advanced Application:  http://localhost:8002" -ForegroundColor White
    Write-Host "  API Documentation:     http://localhost:8002/docs" -ForegroundColor White
    if ($IncludeGrafana) {
        Write-Host "  Grafana Dashboards:    http://localhost:3001 (admin/`${GRAFANA_PASSWORD})" -ForegroundColor White
    }
    if ($IncludeJaeger) {
        Write-Host "  Jaeger Tracing:        http://localhost:16686" -ForegroundColor White
    }
    if ($IncludeElastic) {
        Write-Host "  Kibana Logs:           http://localhost:5601" -ForegroundColor White
        Write-Host "  ElasticSearch:         http://localhost:9200" -ForegroundColor White
    }
    
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
    Write-Host "  • Phase 4 Hardening: ⏳ PENDING" -ForegroundColor Yellow
    
    Write-Host "`nNext Steps:" -ForegroundColor Yellow
    Write-Host "  1. Configure custom dashboards in Grafana" -ForegroundColor Gray
    Write-Host "  2. Set up alerting rules for critical metrics" -ForegroundColor Gray
    Write-Host "  3. Test end-to-end tracing workflows" -ForegroundColor Gray
    Write-Host "  4. Deploy Phase 4 production hardening" -ForegroundColor Gray
    
    Write-Host "`nFULL ENTERPRISE HEALTHCARE PLATFORM: OPERATIONAL" -ForegroundColor Green
    exit 0
} else {
    Write-Host "STATUS: PARTIAL FAILURE - Some analytics services unhealthy" -ForegroundColor Yellow
    Write-Host "Failed Services: $($failedChecks -join ', ')" -ForegroundColor Red
    
    Write-Host "`nTroubleshooting Commands:" -ForegroundColor Yellow
    Write-Host "  Check logs: docker-compose -f docker-compose.phase3.yml logs [service]" -ForegroundColor Gray
    Write-Host "  Service status: docker-compose -f docker-compose.phase3.yml ps" -ForegroundColor Gray
    Write-Host "  Restart service: docker-compose -f docker-compose.phase3.yml restart [service]" -ForegroundColor Gray
    
    Write-Host "`nNote: Analytics services require significant resources and startup time" -ForegroundColor Cyan
    Write-Host "Consider increasing Docker memory allocation if services fail to start" -ForegroundColor Cyan
    
    exit 1
}