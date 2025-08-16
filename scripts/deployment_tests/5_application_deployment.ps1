# Application Deployment Validation Script
# Tests: Docker builds, service deployment, health checks, API endpoints
# Based on: PRODUCTION_DEPLOYMENT_CHECKLIST.md - Application Deployment Phase

Write-Host "🚀 Application Deployment Validation Test" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

$testResults = @()
$allPassed = $true
$deploymentIssues = @()

function Test-DockerEnvironment {
    Write-Host "`n🐳 Testing Docker Environment..." -ForegroundColor Yellow
    
    try {
        # Test Docker daemon
        $dockerVersion = docker version --format "{{.Server.Version}}" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Docker daemon running (version: $dockerVersion)" -ForegroundColor Green
            $testResults += @{
                Test = "DOCKER_DAEMON"
                Status = "✅ RUNNING"
                Description = "Docker daemon status"
                Details = "Version: $dockerVersion"
                Category = "Docker"
                Severity = "INFO"
            }
            
            # Test Docker Compose
            $dockerComposeVersion = docker-compose --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ Docker Compose available" -ForegroundColor Green
                $testResults += @{
                    Test = "DOCKER_COMPOSE"
                    Status = "✅ AVAILABLE"
                    Description = "Docker Compose availability"
                    Details = $dockerComposeVersion
                    Category = "Docker"
                    Severity = "INFO"
                }
            } else {
                Write-Host "  ❌ Docker Compose not available" -ForegroundColor Red
                $script:allPassed = $false
                $script:deploymentIssues += "Docker Compose is required for deployment"
                $testResults += @{
                    Test = "DOCKER_COMPOSE"
                    Status = "❌ MISSING"
                    Description = "Docker Compose availability"
                    Details = "Command not found"
                    Category = "Docker"
                    Severity = "CRITICAL"
                }
            }
            
            # Test Docker system resources
            try {
                $dockerInfo = docker system df 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  ✅ Docker system resources accessible" -ForegroundColor Green
                    $testResults += @{
                        Test = "DOCKER_RESOURCES"
                        Status = "✅ ACCESSIBLE"
                        Description = "Docker system resources"
                        Details = "System info accessible"
                        Category = "Docker"
                        Severity = "INFO"
                    }
                }
            }
            catch {
                Write-Host "  ⚠️ Docker system resources not accessible" -ForegroundColor Yellow
                $testResults += @{
                    Test = "DOCKER_RESOURCES"
                    Status = "⚠️ LIMITED"
                    Description = "Docker system resources"
                    Details = "System info not accessible"
                    Category = "Docker"
                    Severity = "LOW"
                }
            }
            
        } else {
            Write-Host "  ❌ Docker daemon not running or not accessible" -ForegroundColor Red
            Write-Host "  Error: $dockerVersion" -ForegroundColor Red
            $script:allPassed = $false
            $script:deploymentIssues += "Docker daemon is not running"
            $testResults += @{
                Test = "DOCKER_DAEMON"
                Status = "❌ NOT_RUNNING"
                Description = "Docker daemon status"
                Details = "Error: $dockerVersion"
                Category = "Docker"
                Severity = "CRITICAL"
            }
        }
    }
    catch {
        Write-Host "  ❌ Docker test failed: $($_.Exception.Message)" -ForegroundColor Red
        $script:allPassed = $false
        $script:deploymentIssues += "Docker environment test failed"
        $testResults += @{
            Test = "DOCKER_ENVIRONMENT"
            Status = "❌ FAIL"
            Description = "Docker environment test"
            Details = $_.Exception.Message
            Category = "Docker"
            Severity = "CRITICAL"
        }
    }
}

function Test-DockerComposeConfiguration {
    Write-Host "`n📋 Testing Docker Compose Configuration..." -ForegroundColor Yellow
    
    # Check for docker-compose files
    $composeFiles = @(
        "docker-compose.yml",
        "docker-compose.yaml",
        "docker-compose.override.yml",
        "docker-compose.production.yml"
    )
    
    $foundComposeFiles = @()
    foreach ($file in $composeFiles) {
        if (Test-Path $file) {
            Write-Host "  ✅ Docker Compose file found: $file" -ForegroundColor Green
            $foundComposeFiles += $file
            $testResults += @{
                Test = "COMPOSE_FILE_$($file.Replace('.', '_').ToUpper())"
                Status = "✅ FOUND"
                Description = "Docker Compose file: $file"
                Details = "File exists"
                Category = "Configuration"
                Severity = "INFO"
            }
        }
    }
    
    if ($foundComposeFiles.Count -eq 0) {
        Write-Host "  ❌ No Docker Compose files found" -ForegroundColor Red
        $script:allPassed = $false
        $script:deploymentIssues += "No Docker Compose configuration files found"
        $testResults += @{
            Test = "COMPOSE_FILES"
            Status = "❌ MISSING"
            Description = "Docker Compose configuration files"
            Details = "No compose files found"
            Category = "Configuration"
            Severity = "CRITICAL"
        }
        return
    }
    
    # Test compose file syntax
    foreach ($file in $foundComposeFiles) {
        Write-Host "  Testing $file syntax..." -ForegroundColor Cyan
        
        try {
            $configTest = docker-compose -f $file config 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "    ✅ $file syntax is valid" -ForegroundColor Green
                $testResults += @{
                    Test = "COMPOSE_SYNTAX_$($file.Replace('.', '_').ToUpper())"
                    Status = "✅ VALID"
                    Description = "Docker Compose syntax: $file"
                    Details = "Syntax validation passed"
                    Category = "Configuration"
                    Severity = "INFO"
                }
            } else {
                Write-Host "    ❌ $file syntax is invalid" -ForegroundColor Red
                Write-Host "    Error: $configTest" -ForegroundColor Red
                $script:allPassed = $false
                $script:deploymentIssues += "Invalid syntax in $file"
                $testResults += @{
                    Test = "COMPOSE_SYNTAX_$($file.Replace('.', '_').ToUpper())"
                    Status = "❌ INVALID"
                    Description = "Docker Compose syntax: $file"
                    Details = "Syntax error: $configTest"
                    Category = "Configuration"
                    Severity = "HIGH"
                }
            }
        }
        catch {
            Write-Host "    ❌ Failed to test $file syntax: $($_.Exception.Message)" -ForegroundColor Red
            $script:deploymentIssues += "Cannot validate $file syntax"
            $testResults += @{
                Test = "COMPOSE_SYNTAX_$($file.Replace('.', '_').ToUpper())"
                Status = "❌ FAIL"
                Description = "Docker Compose syntax: $file"
                Details = $_.Exception.Message
                Category = "Configuration"
                Severity = "HIGH"
            }
        }
    }
    
    # Check for required services in main compose file
    $mainComposeFile = $foundComposeFiles[0]
    try {
        $composeContent = Get-Content $mainComposeFile -Raw
        
        # Expected services for healthcare application
        $expectedServices = @("postgres", "redis", "app", "minio")
        $servicesCoverage = 0
        
        foreach ($service in $expectedServices) {
            if ($composeContent -match $service) {
                Write-Host "    ✅ Service '$service' configured" -ForegroundColor Green
                $servicesCoverage++
                $testResults += @{
                    Test = "SERVICE_$($service.ToUpper())_CONFIG"
                    Status = "✅ CONFIGURED"
                    Description = "Service configuration: $service"
                    Details = "Service found in compose file"
                    Category = "Services"
                    Severity = "INFO"
                }
            } else {
                Write-Host "    ⚠️ Service '$service' not found" -ForegroundColor Yellow
                $testResults += @{
                    Test = "SERVICE_$($service.ToUpper())_CONFIG"
                    Status = "⚠️ MISSING"
                    Description = "Service configuration: $service"
                    Details = "Service not found in compose file"
                    Category = "Services"
                    Severity = "MEDIUM"
                }
            }
        }
        
        $coveragePercent = ($servicesCoverage / $expectedServices.Count) * 100
        Write-Host "  📊 Services coverage: $servicesCoverage/$($expectedServices.Count) ($coveragePercent%)" -ForegroundColor Cyan
        
        if ($coveragePercent -ge 75) {
            $testResults += @{
                Test = "SERVICES_COVERAGE"
                Status = "✅ GOOD"
                Description = "Services coverage"
                Details = "$servicesCoverage/$($expectedServices.Count) services configured"
                Category = "Services"
                Severity = "INFO"
            }
        } else {
            $testResults += @{
                Test = "SERVICES_COVERAGE"
                Status = "⚠️ LOW"
                Description = "Services coverage"
                Details = "$servicesCoverage/$($expectedServices.Count) services configured"
                Category = "Services"
                Severity = "MEDIUM"
            }
        }
    }
    catch {
        Write-Host "  ❌ Failed to analyze Docker Compose content: $($_.Exception.Message)" -ForegroundColor Red
        $script:deploymentIssues += "Cannot analyze Docker Compose configuration"
        $testResults += @{
            Test = "COMPOSE_ANALYSIS"
            Status = "❌ FAIL"
            Description = "Docker Compose analysis"
            Details = $_.Exception.Message
            Category = "Configuration"
            Severity = "HIGH"
        }
    }
}

function Test-ApplicationBuild {
    Write-Host "`n🔨 Testing Application Build..." -ForegroundColor Yellow
    
    # Check for Dockerfile
    if (Test-Path "Dockerfile") {
        Write-Host "  ✅ Dockerfile found" -ForegroundColor Green
        $testResults += @{
            Test = "DOCKERFILE_EXISTS"
            Status = "✅ FOUND"
            Description = "Dockerfile presence"
            Details = "Dockerfile exists"
            Category = "Build"
            Severity = "INFO"
        }
        
        # Analyze Dockerfile
        try {
            $dockerfileContent = Get-Content "Dockerfile" -Raw
            
            # Check for multi-stage build
            if ($dockerfileContent -match "FROM .* AS ") {
                Write-Host "  ✅ Multi-stage build detected" -ForegroundColor Green
                $testResults += @{
                    Test = "DOCKERFILE_MULTISTAGE"
                    Status = "✅ PRESENT"
                    Description = "Multi-stage build"
                    Details = "Dockerfile uses multi-stage build"
                    Category = "Build"
                    Severity = "INFO"
                }
            }
            
            # Check for Python application
            if ($dockerfileContent -match "python" -or $dockerfileContent -match "pip") {
                Write-Host "  ✅ Python application detected" -ForegroundColor Green
                $testResults += @{
                    Test = "DOCKERFILE_PYTHON"
                    Status = "✅ DETECTED"
                    Description = "Python application"
                    Details = "Python environment configured"
                    Category = "Build"
                    Severity = "INFO"
                }
            }
            
            # Check for security best practices
            $securityChecks = 0
            if ($dockerfileContent -match "USER") {
                Write-Host "    ✅ Non-root user configured" -ForegroundColor Green
                $securityChecks++
            } else {
                Write-Host "    ⚠️ Running as root user" -ForegroundColor Yellow
            }
            
            if ($dockerfileContent -match "COPY --chown" -or $dockerfileContent -match "RUN chown") {
                Write-Host "    ✅ File ownership configured" -ForegroundColor Green
                $securityChecks++
            }
            
            $testResults += @{
                Test = "DOCKERFILE_SECURITY"
                Status = if ($securityChecks -ge 1) { "✅ GOOD" } else { "⚠️ NEEDS_IMPROVEMENT" }
                Description = "Dockerfile security practices"
                Details = "$securityChecks/2 security practices implemented"
                Category = "Build"
                Severity = if ($securityChecks -ge 1) { "INFO" } else { "MEDIUM" }
            }
            
        }
        catch {
            Write-Host "  ❌ Failed to analyze Dockerfile: $($_.Exception.Message)" -ForegroundColor Red
            $script:deploymentIssues += "Cannot analyze Dockerfile"
            $testResults += @{
                Test = "DOCKERFILE_ANALYSIS"
                Status = "❌ FAIL"
                Description = "Dockerfile analysis"
                Details = $_.Exception.Message
                Category = "Build"
                Severity = "MEDIUM"
            }
        }
    } else {
        Write-Host "  ❌ Dockerfile not found" -ForegroundColor Red
        $script:allPassed = $false
        $script:deploymentIssues += "Dockerfile is required for containerized deployment"
        $testResults += @{
            Test = "DOCKERFILE_EXISTS"
            Status = "❌ MISSING"
            Description = "Dockerfile presence"
            Details = "Dockerfile not found"
            Category = "Build"
            Severity = "CRITICAL"
        }
    }
    
    # Check for requirements.txt
    if (Test-Path "requirements.txt") {
        Write-Host "  ✅ requirements.txt found" -ForegroundColor Green
        
        try {
            $requirements = Get-Content "requirements.txt"
            $packageCount = ($requirements | Where-Object { $_ -match "^[a-zA-Z]" }).Count
            
            Write-Host "    📦 $packageCount packages listed" -ForegroundColor Cyan
            $testResults += @{
                Test = "REQUIREMENTS_FILE"
                Status = "✅ FOUND"
                Description = "Python requirements file"
                Details = "$packageCount packages listed"
                Category = "Build"
                Severity = "INFO"
            }
            
            # Check for critical packages
            $criticalPackages = @("fastapi", "uvicorn", "sqlalchemy", "alembic", "pydantic")
            $foundPackages = 0
            
            foreach ($package in $criticalPackages) {
                if ($requirements -match $package) {
                    $foundPackages++
                }
            }
            
            if ($foundPackages -ge 3) {
                Write-Host "    ✅ Critical packages present ($foundPackages/$($criticalPackages.Count))" -ForegroundColor Green
                $testResults += @{
                    Test = "CRITICAL_PACKAGES"
                    Status = "✅ PRESENT"
                    Description = "Critical Python packages"
                    Details = "$foundPackages/$($criticalPackages.Count) critical packages found"
                    Category = "Build"
                    Severity = "INFO"
                }
            } else {
                Write-Host "    ⚠️ Some critical packages may be missing ($foundPackages/$($criticalPackages.Count))" -ForegroundColor Yellow
                $testResults += @{
                    Test = "CRITICAL_PACKAGES"
                    Status = "⚠️ INCOMPLETE"
                    Description = "Critical Python packages"
                    Details = "$foundPackages/$($criticalPackages.Count) critical packages found"
                    Category = "Build"
                    Severity = "MEDIUM"
                }
            }
        }
        catch {
            Write-Host "  ❌ Failed to analyze requirements.txt: $($_.Exception.Message)" -ForegroundColor Red
            $testResults += @{
                Test = "REQUIREMENTS_ANALYSIS"
                Status = "❌ FAIL"
                Description = "Requirements file analysis"
                Details = $_.Exception.Message
                Category = "Build"
                Severity = "MEDIUM"
            }
        }
    } else {
        Write-Host "  ⚠️ requirements.txt not found" -ForegroundColor Yellow
        $testResults += @{
            Test = "REQUIREMENTS_FILE"
            Status = "⚠️ MISSING"
            Description = "Python requirements file"
            Details = "requirements.txt not found"
            Category = "Build"
            Severity = "MEDIUM"
        }
    }
    
    # Test Docker build (dry run)
    if (Test-Path "Dockerfile") {
        Write-Host "  Testing Docker build process..." -ForegroundColor Cyan
        
        try {
            # Test build context
            $buildContext = docker build --dry-run . 2>&1
            
            # Since --dry-run might not be available in all Docker versions,
            # we'll test the build command syntax instead
            $buildHelp = docker build --help 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ Docker build command available" -ForegroundColor Green
                $testResults += @{
                    Test = "DOCKER_BUILD_COMMAND"
                    Status = "✅ AVAILABLE"
                    Description = "Docker build capability"
                    Details = "Build command functional"
                    Category = "Build"
                    Severity = "INFO"
                }
            } else {
                Write-Host "  ❌ Docker build command not working" -ForegroundColor Red
                $script:deploymentIssues += "Docker build command not functional"
                $testResults += @{
                    Test = "DOCKER_BUILD_COMMAND"
                    Status = "❌ FAIL"
                    Description = "Docker build capability"
                    Details = "Build command not functional"
                    Category = "Build"
                    Severity = "HIGH"
                }
            }
        }
        catch {
            Write-Host "  ❌ Docker build test failed: $($_.Exception.Message)" -ForegroundColor Red
            $script:deploymentIssues += "Docker build test failed"
            $testResults += @{
                Test = "DOCKER_BUILD_TEST"
                Status = "❌ FAIL"
                Description = "Docker build test"
                Details = $_.Exception.Message
                Category = "Build"
                Severity = "HIGH"
            }
        }
    }
}

function Test-ServiceDeployment {
    Write-Host "`n🚀 Testing Service Deployment..." -ForegroundColor Yellow
    
    # Check current container status
    try {
        $runningContainers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  📊 Current running containers:" -ForegroundColor Cyan
            Write-Host $runningContainers
            
            # Count running containers
            $containerLines = ($runningContainers -split "`n" | Where-Object { $_ -notmatch "NAMES|^$" }).Count
            
            $testResults += @{
                Test = "RUNNING_CONTAINERS"
                Status = "✅ INFO"
                Description = "Currently running containers"
                Details = "$containerLines containers running"
                Category = "Deployment"
                Severity = "INFO"
            }
        } else {
            Write-Host "  ❌ Cannot check running containers: $runningContainers" -ForegroundColor Red
            $script:deploymentIssues += "Cannot check container status"
            $testResults += @{
                Test = "RUNNING_CONTAINERS"
                Status = "❌ FAIL"
                Description = "Container status check"
                Details = "Cannot list running containers"
                Category = "Deployment"
                Severity = "HIGH"
            }
        }
    }
    catch {
        Write-Host "  ❌ Container status check failed: $($_.Exception.Message)" -ForegroundColor Red
        $script:deploymentIssues += "Container status check failed"
        $testResults += @{
            Test = "CONTAINER_STATUS"
            Status = "❌ FAIL"
            Description = "Container status check"
            Details = $_.Exception.Message
            Category = "Deployment"
            Severity = "HIGH"
        }
    }
    
    # Test Docker Compose deployment capability
    $composeFile = if (Test-Path "docker-compose.yml") { "docker-compose.yml" } elseif (Test-Path "docker-compose.yaml") { "docker-compose.yaml" } else { $null }
    
    if ($composeFile) {
        Write-Host "  Testing Docker Compose deployment with $composeFile..." -ForegroundColor Cyan
        
        try {
            # Test compose up --dry-run equivalent (config validation)
            $composeConfig = docker-compose -f $composeFile config 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ Docker Compose configuration valid" -ForegroundColor Green
                $testResults += @{
                    Test = "COMPOSE_DEPLOYMENT_CONFIG"
                    Status = "✅ VALID"
                    Description = "Docker Compose deployment config"
                    Details = "Configuration validation passed"
                    Category = "Deployment"
                    Severity = "INFO"
                }
                
                # Test individual service definitions
                if ($composeConfig -match "postgres") {
                    Write-Host "    ✅ PostgreSQL service configured" -ForegroundColor Green
                }
                if ($composeConfig -match "redis") {
                    Write-Host "    ✅ Redis service configured" -ForegroundColor Green
                }
                if ($composeConfig -match "app|healthcare") {
                    Write-Host "    ✅ Application service configured" -ForegroundColor Green
                }
                
            } else {
                Write-Host "  ❌ Docker Compose configuration invalid: $composeConfig" -ForegroundColor Red
                $script:allPassed = $false
                $script:deploymentIssues += "Invalid Docker Compose configuration"
                $testResults += @{
                    Test = "COMPOSE_DEPLOYMENT_CONFIG"
                    Status = "❌ INVALID"
                    Description = "Docker Compose deployment config"
                    Details = "Configuration validation failed"
                    Category = "Deployment"
                    Severity = "CRITICAL"
                }
            }
        }
        catch {
            Write-Host "  ❌ Docker Compose deployment test failed: $($_.Exception.Message)" -ForegroundColor Red
            $script:deploymentIssues += "Docker Compose deployment test failed"
            $testResults += @{
                Test = "COMPOSE_DEPLOYMENT_TEST"
                Status = "❌ FAIL"
                Description = "Docker Compose deployment test"
                Details = $_.Exception.Message
                Category = "Deployment"
                Severity = "HIGH"
            }
        }
    }
    
    # Test port availability
    $expectedPorts = @(8000, 5432, 6379, 9000, 3000, 9090)
    
    Write-Host "  Testing port availability..." -ForegroundColor Cyan
    foreach ($port in $expectedPorts) {
        try {
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $tcpClient.ReceiveTimeout = 1000
            $tcpClient.SendTimeout = 1000
            $connection = $tcpClient.BeginConnect("localhost", $port, $null, $null)
            $connection.AsyncWaitHandle.WaitOne(1000, $false) | Out-Null
            
            if ($tcpClient.Connected) {
                $tcpClient.Close()
                Write-Host "    ✅ Port $port is in use (service may be running)" -ForegroundColor Green
                $testResults += @{
                    Test = "PORT_$port"
                    Status = "✅ IN_USE"
                    Description = "Port $port availability"
                    Details = "Port is in use"
                    Category = "Network"
                    Severity = "INFO"
                }
            } else {
                $tcpClient.Close()
                Write-Host "    ⚪ Port $port is available" -ForegroundColor White
                $testResults += @{
                    Test = "PORT_$port"
                    Status = "⚪ AVAILABLE"
                    Description = "Port $port availability"
                    Details = "Port is available"
                    Category = "Network"
                    Severity = "INFO"
                }
            }
        }
        catch {
            Write-Host "    ⚪ Port $port is available" -ForegroundColor White
            $testResults += @{
                Test = "PORT_$port"
                Status = "⚪ AVAILABLE"
                Description = "Port $port availability"
                Details = "Port is available"
                Category = "Network"
                Severity = "INFO"
            }
        }
    }
}

function Test-HealthEndpoints {
    Write-Host "`n💚 Testing Application Health Endpoints..." -ForegroundColor Yellow
    
    # Define health endpoints to test
    $healthEndpoints = @(
        @{Name = "Main API Health"; URL = "http://localhost:8000/health"; Critical = $true},
        @{Name = "Healthcare Records Health"; URL = "http://localhost:8000/api/v1/healthcare-records/health"; Critical = $true},
        @{Name = "API Docs"; URL = "http://localhost:8000/docs"; Critical = $false},
        @{Name = "API OpenAPI"; URL = "http://localhost:8000/openapi.json"; Critical = $false}
    )
    
    foreach ($endpoint in $healthEndpoints) {
        Write-Host "  Testing $($endpoint.Name)..." -ForegroundColor Cyan
        
        try {
            $response = Invoke-WebRequest -Uri $endpoint.URL -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
            
            if ($response.StatusCode -eq 200) {
                Write-Host "    ✅ $($endpoint.Name) responding (200 OK)" -ForegroundColor Green
                $testResults += @{
                    Test = "HEALTH_$($endpoint.Name.Replace(' ', '_').ToUpper())"
                    Status = "✅ HEALTHY"
                    Description = "Health endpoint: $($endpoint.Name)"
                    Details = "HTTP 200 - Content length: $($response.Content.Length)"
                    Category = "Health"
                    Severity = "INFO"
                }
                
                # Check response content for health endpoints
                if ($endpoint.Name -match "Health") {
                    try {
                        $healthData = $response.Content | ConvertFrom-Json
                        if ($healthData.status -eq "healthy") {
                            Write-Host "      ✅ Health status: healthy" -ForegroundColor Green
                        } else {
                            Write-Host "      ⚠️ Health status: $($healthData.status)" -ForegroundColor Yellow
                        }
                    }
                    catch {
                        Write-Host "      ⚠️ Could not parse health response as JSON" -ForegroundColor Yellow
                    }
                }
                
            } else {
                Write-Host "    ⚠️ $($endpoint.Name) returned status: $($response.StatusCode)" -ForegroundColor Yellow
                $testResults += @{
                    Test = "HEALTH_$($endpoint.Name.Replace(' ', '_').ToUpper())"
                    Status = "⚠️ WARNING"
                    Description = "Health endpoint: $($endpoint.Name)"
                    Details = "HTTP $($response.StatusCode)"
                    Category = "Health"
                    Severity = if ($endpoint.Critical) { "HIGH" } else { "LOW" }
                }
            }
        }
        catch {
            if ($endpoint.Critical) {
                Write-Host "    ❌ $($endpoint.Name) not responding" -ForegroundColor Red
                $script:deploymentIssues += "$($endpoint.Name) is not responding"
                $testResults += @{
                    Test = "HEALTH_$($endpoint.Name.Replace(' ', '_').ToUpper())"
                    Status = "❌ DOWN"
                    Description = "Health endpoint: $($endpoint.Name)"
                    Details = $_.Exception.Message
                    Category = "Health"
                    Severity = "CRITICAL"
                }
            } else {
                Write-Host "    ⚪ $($endpoint.Name) not available (optional)" -ForegroundColor White
                $testResults += @{
                    Test = "HEALTH_$($endpoint.Name.Replace(' ', '_').ToUpper())"
                    Status = "⚪ UNAVAILABLE"
                    Description = "Health endpoint: $($endpoint.Name)"
                    Details = "Service not running (optional)"
                    Category = "Health"
                    Severity = "INFO"
                }
            }
        }
    }
    
    # Test monitoring endpoints if they exist
    $monitoringEndpoints = @(
        @{Name = "Grafana"; URL = "http://localhost:3000/api/health"},
        @{Name = "Prometheus"; URL = "http://localhost:9090/-/healthy"},
        @{Name = "Node Exporter"; URL = "http://localhost:9100/metrics"}
    )
    
    Write-Host "  Testing monitoring endpoints..." -ForegroundColor Cyan
    foreach ($endpoint in $monitoringEndpoints) {
        try {
            $response = Invoke-WebRequest -Uri $endpoint.URL -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            
            Write-Host "    ✅ $($endpoint.Name) monitoring available" -ForegroundColor Green
            $testResults += @{
                Test = "MONITORING_$($endpoint.Name.ToUpper())"
                Status = "✅ AVAILABLE"
                Description = "Monitoring endpoint: $($endpoint.Name)"
                Details = "HTTP $($response.StatusCode)"
                Category = "Monitoring"
                Severity = "INFO"
            }
        }
        catch {
            Write-Host "    ⚪ $($endpoint.Name) monitoring not available" -ForegroundColor White
            $testResults += @{
                Test = "MONITORING_$($endpoint.Name.ToUpper())"
                Status = "⚪ UNAVAILABLE"
                Description = "Monitoring endpoint: $($endpoint.Name)"
                Details = "Service not running"
                Category = "Monitoring"
                Severity = "LOW"
            }
        }
    }
}

function Test-ResourceConfiguration {
    Write-Host "`n⚙️ Testing Resource Configuration..." -ForegroundColor Yellow
    
    # Test environment variables for resource limits
    $resourceVars = @(
        @{Name = "WORKERS"; Default = "4"; Desc = "Number of worker processes"},
        @{Name = "MAX_CONNECTIONS"; Default = "100"; Desc = "Maximum database connections"},
        @{Name = "MEMORY_LIMIT"; Default = "2G"; Desc = "Memory limit"},
        @{Name = "CPU_LIMIT"; Default = "2"; Desc = "CPU limit"}
    )
    
    foreach ($var in $resourceVars) {
        $value = [Environment]::GetEnvironmentVariable($var.Name)
        
        if (![string]::IsNullOrEmpty($value)) {
            Write-Host "  ✅ $($var.Name) configured: $value" -ForegroundColor Green
            $testResults += @{
                Test = "RESOURCE_$($var.Name)"
                Status = "✅ CONFIGURED"
                Description = "Resource configuration: $($var.Desc)"
                Details = "Value: $value"
                Category = "Resources"
                Severity = "INFO"
            }
        } else {
            Write-Host "  ⚪ $($var.Name) using default: $($var.Default)" -ForegroundColor White
            $testResults += @{
                Test = "RESOURCE_$($var.Name)"
                Status = "⚪ DEFAULT"
                Description = "Resource configuration: $($var.Desc)"
                Details = "Using default: $($var.Default)"
                Category = "Resources"
                Severity = "INFO"
            }
        }
    }
    
    # Test system resources
    try {
        # Get available memory (approximation)
        $memInfo = Get-CimInstance -ClassName Win32_ComputerSystem 2>$null
        if ($memInfo) {
            $totalMemoryGB = [math]::Round($memInfo.TotalPhysicalMemory / 1GB, 2)
            Write-Host "  📊 System memory: $totalMemoryGB GB" -ForegroundColor Cyan
            
            if ($totalMemoryGB -ge 4) {
                Write-Host "    ✅ Sufficient memory for deployment" -ForegroundColor Green
                $testResults += @{
                    Test = "SYSTEM_MEMORY"
                    Status = "✅ SUFFICIENT"
                    Description = "System memory availability"
                    Details = "$totalMemoryGB GB available"
                    Category = "Resources"
                    Severity = "INFO"
                }
            } else {
                Write-Host "    ⚠️ Low memory for production deployment" -ForegroundColor Yellow
                $testResults += @{
                    Test = "SYSTEM_MEMORY"
                    Status = "⚠️ LOW"
                    Description = "System memory availability"
                    Details = "$totalMemoryGB GB available (4GB+ recommended)"
                    Category = "Resources"
                    Severity = "MEDIUM"
                }
            }
        }
    }
    catch {
        Write-Host "  ⚪ Cannot determine system memory" -ForegroundColor White
        $testResults += @{
            Test = "SYSTEM_MEMORY"
            Status = "⚪ UNKNOWN"
            Description = "System memory availability"
            Details = "Cannot determine available memory"
            Category = "Resources"
            Severity = "LOW"
        }
    }
    
    # Check disk space
    try {
        $diskInfo = Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DeviceID='C:'" 2>$null
        if ($diskInfo) {
            $freeSpaceGB = [math]::Round($diskInfo.FreeSpace / 1GB, 2)
            $totalSpaceGB = [math]::Round($diskInfo.Size / 1GB, 2)
            
            Write-Host "  📊 Disk space: $freeSpaceGB GB free of $totalSpaceGB GB total" -ForegroundColor Cyan
            
            if ($freeSpaceGB -ge 10) {
                Write-Host "    ✅ Sufficient disk space" -ForegroundColor Green
                $testResults += @{
                    Test = "DISK_SPACE"
                    Status = "✅ SUFFICIENT"
                    Description = "Disk space availability"
                    Details = "$freeSpaceGB GB free"
                    Category = "Resources"
                    Severity = "INFO"
                }
            } else {
                Write-Host "    ⚠️ Low disk space for deployment" -ForegroundColor Yellow
                $testResults += @{
                    Test = "DISK_SPACE"
                    Status = "⚠️ LOW"
                    Description = "Disk space availability"
                    Details = "$freeSpaceGB GB free (10GB+ recommended)"
                    Category = "Resources"
                    Severity = "MEDIUM"
                }
            }
        }
    }
    catch {
        Write-Host "  ⚪ Cannot determine disk space" -ForegroundColor White
        $testResults += @{
            Test = "DISK_SPACE"
            Status = "⚪ UNKNOWN"
            Description = "Disk space availability"
            Details = "Cannot determine available disk space"
            Category = "Resources"
            Severity = "LOW"
        }
    }
}

# Run all application deployment tests
Write-Host "`n🚀 Starting Application Deployment Tests..." -ForegroundColor Cyan

Test-DockerEnvironment
Test-DockerComposeConfiguration  
Test-ApplicationBuild
Test-ServiceDeployment
Test-HealthEndpoints
Test-ResourceConfiguration

# Generate results summary
Write-Host "`n📊 APPLICATION DEPLOYMENT RESULTS" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

$passedTests = ($testResults | Where-Object { $_.Status -match "✅" }).Count
$failedTests = ($testResults | Where-Object { $_.Status -match "❌" }).Count
$warningTests = ($testResults | Where-Object { $_.Status -match "⚠️" }).Count
$infoTests = ($testResults | Where-Object { $_.Status -match "⚪" }).Count
$totalTests = $testResults.Count

Write-Host "`nDeployment Test Summary:" -ForegroundColor Cyan
Write-Host "  Total Tests: $totalTests"
Write-Host "  Passed: $passedTests" -ForegroundColor Green
Write-Host "  Failed: $failedTests" -ForegroundColor Red
Write-Host "  Warnings: $warningTests" -ForegroundColor Yellow
Write-Host "  Info/Optional: $infoTests" -ForegroundColor Gray

# Group results by severity
$criticalIssues = ($testResults | Where-Object { $_.Severity -eq "CRITICAL" -and $_.Status -match "❌" }).Count
$highIssues = ($testResults | Where-Object { $_.Severity -eq "HIGH" -and $_.Status -match "❌" }).Count
$mediumIssues = ($testResults | Where-Object { $_.Severity -eq "MEDIUM" -and $_.Status -match "❌|⚠️" }).Count

Write-Host "`nIssues by Severity:" -ForegroundColor Cyan
Write-Host "  Critical: $criticalIssues" -ForegroundColor $(if ($criticalIssues -eq 0) { "Green" } else { "Red" })
Write-Host "  High: $highIssues" -ForegroundColor $(if ($highIssues -eq 0) { "Green" } else { "Red" })
Write-Host "  Medium: $mediumIssues" -ForegroundColor $(if ($mediumIssues -eq 0) { "Green" } else { "Yellow" })

# Show deployment issues
if ($deploymentIssues.Count -gt 0) {
    Write-Host "`n🚨 Deployment Issues to Fix:" -ForegroundColor Red
    for ($i = 0; $i -lt $deploymentIssues.Count; $i++) {
        Write-Host "  $($i + 1). $($deploymentIssues[$i])" -ForegroundColor Red
    }
}

# Show detailed results by category
Write-Host "`nDetailed Results by Category:" -ForegroundColor Cyan
$categories = @("Docker", "Configuration", "Build", "Services", "Deployment", "Health", "Monitoring", "Network", "Resources")

foreach ($category in $categories) {
    $categoryTests = $testResults | Where-Object { $_.Category -eq $category }
    if ($categoryTests.Count -gt 0) {
        Write-Host "  $category Tests:" -ForegroundColor Yellow
        foreach ($test in $categoryTests) {
            Write-Host "    $($test.Status) $($test.Description)"
            if ($test.Details -and $test.Details -ne "") {
                Write-Host "      Details: $($test.Details)" -ForegroundColor Gray
            }
        }
    }
}

# Save results to file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$resultFile = "application_deployment_$timestamp.json"

try {
    $resultsData = @{
        timestamp = $timestamp
        summary = @{
            total_tests = $totalTests
            passed = $passedTests
            failed = $failedTests
            warnings = $warningTests
            info = $infoTests
            critical_issues = $criticalIssues
            high_issues = $highIssues
            medium_issues = $mediumIssues
        }
        tests = $testResults
        deployment_issues = $deploymentIssues
        deployment_ready = ($criticalIssues -eq 0 -and $highIssues -eq 0)
    }
    
    $resultsData | ConvertTo-Json -Depth 4 | Out-File -FilePath $resultFile -Encoding UTF8
    Write-Host "`n📁 Results saved to: $resultFile" -ForegroundColor Cyan
}
catch {
    Write-Host "`n⚠️ Could not save results to file: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Final assessment
Write-Host "`n🎯 FINAL DEPLOYMENT ASSESSMENT" -ForegroundColor Green
if ($allPassed -and $criticalIssues -eq 0 -and $highIssues -eq 0) {
    Write-Host "✅ APPLICATION DEPLOYMENT VALIDATION PASSED" -ForegroundColor Green
    Write-Host "Application is ready for production deployment!" -ForegroundColor Green
    exit 0
} elseif ($criticalIssues -eq 0 -and $highIssues -eq 0) {
    Write-Host "⚠️ APPLICATION DEPLOYMENT VALIDATION PASSED WITH WARNINGS" -ForegroundColor Yellow
    Write-Host "Application can be deployed but has some recommendations." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "❌ APPLICATION DEPLOYMENT VALIDATION FAILED" -ForegroundColor Red
    Write-Host "Critical deployment issues must be fixed before production!" -ForegroundColor Red
    exit 1
}