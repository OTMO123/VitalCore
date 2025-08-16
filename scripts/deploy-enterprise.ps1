# Enterprise Healthcare API Deployment Script (PowerShell)
# Deploys the healthcare API with SOC2/HIPAA compliance

param(
    [switch]$UseDocker,
    [switch]$UseKubernetes,
    [switch]$SkipPrerequisites,
    [switch]$Help
)

# Colors for output
$Red = "Red"
$Green = "Green"  
$Yellow = "Yellow"
$Blue = "Cyan"

function Write-Info {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Blue
}

function Write-Success {
    param($Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Green
}

function Write-Warning {
    param($Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Red
}

function Show-Help {
    Write-Host @"
Healthcare API Enterprise Deployment Script

Usage: .\scripts\deploy-enterprise.ps1 [OPTIONS]

Options:
  -UseDocker           Use Docker Compose for quick deployment
  -UseKubernetes       Use Kubernetes for enterprise deployment  
  -SkipPrerequisites   Skip prerequisites check
  -Help               Show this help message

Examples:
  .\scripts\deploy-enterprise.ps1 -UseDocker
  .\scripts\deploy-enterprise.ps1 -UseKubernetes
"@
}

function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    $issues = @()
    
    # Check Docker
    try {
        $dockerVersion = docker --version 2>$null
        if ($dockerVersion) {
            Write-Success "Docker found: $dockerVersion"
        } else {
            $issues += "Docker not found"
        }
    } catch {
        $issues += "Docker not found or not accessible"
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker-compose --version 2>$null
        if ($composeVersion) {
            Write-Success "Docker Compose found: $composeVersion"
        } else {
            $issues += "Docker Compose not found"
        }
    } catch {
        $issues += "Docker Compose not found or not accessible"
    }
    
    if ($UseKubernetes) {
        # Check kubectl
        try {
            $kubectlVersion = kubectl version --client --short 2>$null
            if ($kubectlVersion) {
                Write-Success "Kubectl found: $kubectlVersion"
            } else {
                $issues += "Kubectl not found"
            }
        } catch {
            $issues += "Kubectl not found or not accessible"
        }
        
        # Check Helm
        try {
            $helmVersion = helm version --short 2>$null
            if ($helmVersion) {
                Write-Success "Helm found: $helmVersion"
            } else {
                $issues += "Helm not found"
            }
        } catch {
            $issues += "Helm not found or not accessible"
        }
    }
    
    if ($issues.Count -gt 0) {
        Write-Error "Prerequisites check failed:"
        foreach ($issue in $issues) {
            Write-Error "  - $issue"
        }
        return $false
    }
    
    Write-Success "Prerequisites check completed successfully"
    return $true
}

function Deploy-WithDocker {
    Write-Info "Deploying with Docker Compose..."
    
    # Check available docker-compose files
    $composeFiles = @()
    if (Test-Path "docker-compose.yml") { $composeFiles += "docker-compose.yml" }
    if (Test-Path "docker-compose.enterprise.yml") { $composeFiles += "docker-compose.enterprise.yml" }
    if (Test-Path "docker-compose.complete.yml") { $composeFiles += "docker-compose.complete.yml" }
    
    if ($composeFiles.Count -eq 0) {
        Write-Error "No docker-compose files found"
        return $false
    }
    
    Write-Info "Available compose files: $($composeFiles -join ', ')"
    
    # Use enterprise compose if available, otherwise use the first available
    $selectedCompose = if ($composeFiles -contains "docker-compose.enterprise.yml") {
        "docker-compose.enterprise.yml"
    } elseif ($composeFiles -contains "docker-compose.complete.yml") {
        "docker-compose.complete.yml"
    } else {
        $composeFiles[0]
    }
    
    Write-Info "Using compose file: $selectedCompose"
    
    try {
        Write-Info "Starting services with Docker Compose..."
        docker-compose -f $selectedCompose up -d
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Docker services started successfully"
            
            # Wait for services to be ready
            Write-Info "Waiting for services to be ready..."
            Start-Sleep -Seconds 30
            
            # Check service health
            Test-ServiceHealth
            return $true
        } else {
            Write-Error "Docker Compose failed with exit code $LASTEXITCODE"
            return $false
        }
    } catch {
        Write-Error "Failed to start Docker services: $($_.Exception.Message)"
        return $false
    }
}

function Test-ServiceHealth {
    Write-Info "Checking service health..."
    
    # Check PostgreSQL
    try {
        $pgResult = docker-compose exec -T db pg_isready -U postgres 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "PostgreSQL: Ready"
        } else {
            Write-Warning "PostgreSQL: Not ready"
        }
    } catch {
        Write-Warning "PostgreSQL: Health check failed"
    }
    
    # Check Redis
    try {
        $redisResult = docker-compose exec -T redis redis-cli ping 2>$null
        if ($redisResult -like "*PONG*") {
            Write-Success "Redis: Ready"
        } else {
            Write-Warning "Redis: Not ready"
        }
    } catch {
        Write-Warning "Redis: Health check failed"
    }
    
    # Check API health endpoint
    Start-Sleep -Seconds 5
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 10 -ErrorAction SilentlyContinue
        if ($response) {
            Write-Success "Healthcare API: Ready"
        } else {
            Write-Warning "Healthcare API: Not responding"
        }
    } catch {
        Write-Warning "Healthcare API: Health check failed - $($_.Exception.Message)"
    }
}

function Deploy-WithKubernetes {
    Write-Info "Deploying with Kubernetes..."
    
    # Check if cluster is accessible
    try {
        kubectl cluster-info --request-timeout=10s | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Cannot connect to Kubernetes cluster"
            return $false
        }
        Write-Success "Kubernetes cluster accessible"
    } catch {
        Write-Error "Kubernetes cluster not accessible"
        return $false
    }
    
    # Apply Kubernetes manifests
    $manifestDirs = @("k8s/base", "k8s/database", "k8s/cache", "k8s/app", "k8s/istio")
    
    foreach ($dir in $manifestDirs) {
        if (Test-Path $dir) {
            Write-Info "Applying manifests from $dir..."
            kubectl apply -f $dir/
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Failed to apply manifests from $dir"
                return $false
            }
        } else {
            Write-Warning "Directory $dir not found, skipping..."
        }
    }
    
    Write-Success "Kubernetes deployment completed"
    return $true
}

function Show-DeploymentSummary {
    Write-Host ""
    Write-Host "=========================================================================================" -ForegroundColor Green
    Write-Host "🏥 Healthcare API Enterprise Deployment Summary" -ForegroundColor Green
    Write-Host "=========================================================================================" -ForegroundColor Green
    Write-Host ""
    
    if ($UseDocker) {
        Write-Host "📊 Docker Services Status:" -ForegroundColor Cyan
        docker-compose ps
        
        Write-Host ""
        Write-Host "🌐 Access Information:" -ForegroundColor Cyan
        Write-Host "  API Endpoint:  http://localhost:8000" -ForegroundColor White
        Write-Host "  Health Check:  http://localhost:8000/health" -ForegroundColor White
        Write-Host "  Database:      localhost:5432" -ForegroundColor White
        Write-Host "  Redis:         localhost:6379" -ForegroundColor White
        Write-Host "  MinIO:         http://localhost:9000" -ForegroundColor White
    }
    
    if ($UseKubernetes) {
        Write-Host "📊 Kubernetes Deployment Status:" -ForegroundColor Cyan
        kubectl get pods -n healthcare-api
        
        Write-Host ""
        Write-Host "🌐 Access Information:" -ForegroundColor Cyan
        Write-Host "  Use kubectl port-forward to access services locally" -ForegroundColor White
        Write-Host "  kubectl port-forward -n healthcare-api svc/healthcare-api 8000:8000" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "✅ Next Steps:" -ForegroundColor Green
    Write-Host "  1. Run tests: pytest app/tests/ -v" -ForegroundColor White
    Write-Host "  2. Check API health: curl http://localhost:8000/health" -ForegroundColor White
    Write-Host "  3. View logs: docker-compose logs -f (Docker) or kubectl logs -n healthcare-api deployment/healthcare-api (K8s)" -ForegroundColor White
    Write-Host ""
    Write-Host "=========================================================================================" -ForegroundColor Green
}

function Main {
    if ($Help) {
        Show-Help
        return
    }
    
    Write-Host "🏥 Healthcare API Enterprise Deployment" -ForegroundColor Green
    Write-Host "=======================================" -ForegroundColor Green
    Write-Host ""
    
    # Prerequisites check
    if (-not $SkipPrerequisites) {
        if (-not (Test-Prerequisites)) {
            Write-Error "Prerequisites check failed. Use -SkipPrerequisites to bypass."
            return
        }
    }
    
    # Determine deployment method
    if (-not $UseDocker -and -not $UseKubernetes) {
        Write-Info "No deployment method specified. Defaulting to Docker Compose."
        $UseDocker = $true
    }
    
    $success = $false
    
    if ($UseDocker) {
        $success = Deploy-WithDocker
    }
    
    if ($UseKubernetes) {
        $success = Deploy-WithKubernetes
    }
    
    if ($success) {
        Show-DeploymentSummary
        Write-Success "Healthcare API Enterprise deployment completed successfully! 🚀"
    } else {
        Write-Error "Deployment failed. Please check the error messages above."
    }
}

# Execute main function
Main