# Quick VitalCore Deployment Script
# Simplified version for fast deployment

param(
    [switch]$Production,
    [switch]$Development,
    [switch]$Stop,
    [switch]$Status,
    [switch]$Logs,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

# Configuration
$DevComposeFile = "docker-compose.frontend.yml"
$ProdComposeFile = "docker-compose.production.frontend.yml"
$ComposeFile = if ($Production) { $ProdComposeFile } else { $DevComposeFile }

# Colors
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$ForegroundColor = "White"
    )
    Write-Host $Message -ForegroundColor $ForegroundColor
}

# Quick deployment
function Invoke-QuickDeploy {
    Write-ColorOutput "🚀 Quick VitalCore Deployment" "Green"
    Write-ColorOutput "Using: $ComposeFile" "Yellow"
    
    try {
        # Stop existing
        Write-ColorOutput "🛑 Stopping existing services..." "Blue"
        docker-compose -f $ComposeFile down 2>$null
        
        # Start services
        Write-ColorOutput "🔧 Starting services..." "Blue"
        docker-compose -f $ComposeFile up -d --build
        
        # Quick health check
        Write-ColorOutput "⏳ Waiting for services..." "Blue"
        Start-Sleep -Seconds 10
        
        # Show status
        Write-ColorOutput "📊 Service Status:" "Green"
        docker-compose -f $ComposeFile ps
        
        # Show URLs
        Write-ColorOutput "`n🌐 Access URLs:" "Green"
        if ($Production) {
            Write-ColorOutput "Frontend: http://localhost" "White"
            Write-ColorOutput "API: http://localhost/api/" "White"
            Write-ColorOutput "Docs: http://localhost/docs" "White"
        } else {
            Write-ColorOutput "Frontend: http://localhost:5173" "White"
            Write-ColorOutput "MedBrain: http://localhost:5173/components/core/VitalCore-Production.html" "White"
            Write-ColorOutput "API: http://localhost:8000" "White"
            Write-ColorOutput "Docs: http://localhost:8000/docs" "White"
        }
        Write-ColorOutput "MinIO: http://localhost:9001" "White"
        
        Write-ColorOutput "`n✅ Deployment completed!" "Green"
        
    } catch {
        Write-ColorOutput "❌ Deployment failed: $($_.Exception.Message)" "Red"
        exit 1
    }
}

# Main logic
try {
    if ($Stop) {
        Write-ColorOutput "🛑 Stopping services..." "Yellow"
        docker-compose -f $ComposeFile down
        Write-ColorOutput "✅ Services stopped" "Green"
    }
    elseif ($Status) {
        Write-ColorOutput "📊 Service Status:" "Blue"
        docker-compose -f $ComposeFile ps
    }
    elseif ($Logs) {
        Write-ColorOutput "📋 Recent logs:" "Blue"
        docker-compose -f $ComposeFile logs --tail=20
    }
    elseif ($Clean) {
        Write-ColorOutput "🧹 Cleaning up..." "Yellow"
        docker-compose -f $ComposeFile down -v --remove-orphans
        docker system prune -f
        Write-ColorOutput "✅ Cleanup completed" "Green"
    }
    else {
        Invoke-QuickDeploy
    }
} catch {
    Write-ColorOutput "❌ Error: $($_.Exception.Message)" "Red"
    exit 1
}