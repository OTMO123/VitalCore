# HEMA3N Medical Agent Training Script - PowerShell
# Quick and easy training of specialized medical AI agents

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("cardiology", "neurology", "emergency", "pulmonology", "pediatric", "infection", "psychiatry", "orthopedic", "general", "all")]
    [string]$Agent = "cardiology",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("unsloth/gemma-3n-E2B-it", "unsloth/gemma-3n-E4B-it", "unsloth/gemma-3n-E2B-it-unsloth-bnb-4bit", "unsloth/gemma-3n-E4B-it-unsloth-bnb-4bit")]
    [string]$Model = "unsloth/gemma-3n-E2B-it",
    
    [Parameter(Mandatory=$false)]
    [int]$Epochs = 1,
    
    [Parameter(Mandatory=$false)]
    [int]$Steps = 60,
    
    [Parameter(Mandatory=$false)]
    [int]$BatchSize = 1,
    
    [Parameter(Mandatory=$false)]
    [double]$LearningRate = 0.0002,
    
    [Parameter(Mandatory=$false)]
    [int]$LoRARank = 8,
    
    [Parameter(Mandatory=$false)]
    [int]$DatasetSize = 500,
    
    [Parameter(Mandatory=$false)]
    [switch]$TestOnly,
    
    [Parameter(Mandatory=$false)]
    [switch]$MedicalData,
    
    [Parameter(Mandatory=$false)]
    [switch]$Multimodal,
    
    [Parameter(Mandatory=$false)]
    [string]$OutputDir = "./models/medical_agents",
    
    [Parameter(Mandatory=$false)]
    [switch]$Quick,
    
    [Parameter(Mandatory=$false)]
    [switch]$ShowDetails
)

# Enable strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Colors for output
function Write-Info($Message) {
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success($Message) {
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning($Message) {
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error($Message) {
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Header($Title) {
    Write-Host ""
    Write-Host "=" * 70 -ForegroundColor Blue
    Write-Host $Title -ForegroundColor White
    Write-Host "=" * 70 -ForegroundColor Blue
    Write-Host ""
}

function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Info "Python: $pythonVersion"
    } catch {
        Write-Error "Python not found. Please install Python 3.8+"
        return $false
    }
    
    # Check if training script exists
    if (-not (Test-Path "scripts/finetune_gemma3n_medical.py")) {
        Write-Error "Training script not found: scripts/finetune_gemma3n_medical.py"
        return $false
    }
    
    # Check if config exists
    if (-not (Test-Path "config/lora_training_config.yaml")) {
        Write-Warning "Config file not found: config/lora_training_config.yaml"
    }
    
    Write-Success "Prerequisites check completed"
    return $true
}

function Get-AgentEmoji($AgentName) {
    $emojis = @{
        "cardiology" = "🫀"
        "neurology" = "🧠"
        "emergency" = "🚨"
        "pulmonology" = "🫁"
        "pediatric" = "👶"
        "infection" = "🦠"
        "psychiatry" = "🧘"
        "orthopedic" = "🦴"
        "general" = "🩺"
        "all" = "🏥"
    }
    return $emojis[$AgentName]
}

function Start-Training {
    param($AgentName)
    
    $emoji = Get-AgentEmoji $AgentName
    Write-Header "$emoji Training HEMA3N $($AgentName.ToUpper()) Agent with LoRA Fine-tuning"
    
    # Prepare arguments
    $trainingArgs = @(
        "scripts/finetune_gemma3n_medical.py"
        "--agent", $AgentName
        "--model", $Model
        "--output-dir", $OutputDir
    )
    
    if ($TestOnly) {
        $trainingArgs += "--test-only"
        Write-Info "🧪 Running inference test only..."
    } else {
        $trainingArgs += @(
            "--epochs", $Epochs
            "--steps", $Steps
            "--batch-size", $BatchSize
            "--learning-rate", $LearningRate
            "--lora-rank", $LoRARank
            "--dataset-size", $DatasetSize
        )
        
        if ($MedicalData) {
            $trainingArgs += "--medical-data"
        }
        
        if ($Multimodal) {
            $trainingArgs += "--multimodal"
        }
        
        # Quick training mode
        if ($Quick) {
            Write-Info "🚀 Quick training mode enabled"
            $trainingArgs[($trainingArgs.IndexOf("--steps") + 1)] = "20"
            $trainingArgs[($trainingArgs.IndexOf("--dataset-size") + 1)] = "100"
        }
        
        Write-Info "🏋️ Starting training with parameters:"
        Write-Host "  Model: $Model" -ForegroundColor Cyan
        Write-Host "  Epochs: $Epochs" -ForegroundColor Cyan
        Write-Host "  Steps: $Steps" -ForegroundColor Cyan
        Write-Host "  Batch Size: $BatchSize" -ForegroundColor Cyan
        Write-Host "  Learning Rate: $LearningRate" -ForegroundColor Cyan
        Write-Host "  LoRA Rank: $LoRARank" -ForegroundColor Cyan
        Write-Host "  Dataset Size: $DatasetSize" -ForegroundColor Cyan
    }
    
    # Execute training
    Write-Info "🚀 Executing training command..."
    
    if ($ShowDetails) {
        Write-Host "Command: python $($trainingArgs -join ' ')" -ForegroundColor Gray
    }
    
    try {
        $startTime = Get-Date
        & python @trainingArgs
        
        if ($LASTEXITCODE -eq 0) {
            $endTime = Get-Date
            $duration = $endTime - $startTime
            Write-Success "Training completed successfully!"
            Write-Info "⏱️ Total time: $($duration.ToString('hh\\:mm\\:ss'))"
            
            if (-not $TestOnly) {
                Write-Info "📁 Model saved to: $OutputDir/$AgentName"
                Write-Info "🧪 Test your model:"
                Write-Host "  .\\Train-MedicalAgent.ps1 -Agent $AgentName -TestOnly" -ForegroundColor Yellow
            }
        } else {
            Write-Error "Training failed with exit code: $LASTEXITCODE"
            return $false
        }
    } catch {
        Write-Error "Training failed: $_"
        return $false
    }
    
    return $true
}

function Start-AllAgentsTraining {
    Write-Header "🏥 Training ALL HEMA3N Medical Agents"
    
    $agents = @("cardiology", "neurology", "emergency", "pulmonology", "pediatric", "infection", "psychiatry", "orthopedic", "general")
    $results = @{}
    
    Write-Info "Training $($agents.Count) medical agents..."
    
    foreach ($agent in $agents) {
        Write-Info "Starting training for $agent agent ($($agents.IndexOf($agent) + 1)/$($agents.Count))"
        $results[$agent] = Start-Training $agent
        
        if ($results[$agent]) {
            Write-Success "$agent agent training completed"
        } else {
            Write-Error "$agent agent training failed"
        }
        
        # Brief pause between trainings
        Start-Sleep -Seconds 2
    }
    
    Write-Header "🎯 Training Summary"
    
    $successful = 0
    $failed = 0
    
    foreach ($agent in $agents) {
        $emoji = Get-AgentEmoji $agent
        if ($results[$agent]) {
            Write-Host "$emoji $agent : ✅ SUCCESS" -ForegroundColor Green
            $successful++
        } else {
            Write-Host "$emoji $agent : ❌ FAILED" -ForegroundColor Red
            $failed++
        }
    }
    
    Write-Host ""
    Write-Info "Results: $successful successful, $failed failed"
    
    if ($successful -eq $agents.Count) {
        Write-Success "🎉 All medical agents trained successfully!"
    } elseif ($successful -gt 0) {
        Write-Warning "⚠️ Some agents failed. Check logs above for details."
    } else {
        Write-Error "❌ All training sessions failed"
    }
}

function Show-Help {
    Write-Header "🏥 HEMA3N Medical Agent Training - PowerShell"
    
    Write-Host "USAGE:" -ForegroundColor Green
    Write-Host "  .\\Train-MedicalAgent.ps1 [OPTIONS]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "EXAMPLES:" -ForegroundColor Green
    Write-Host "  # Quick cardiology training" -ForegroundColor Gray
    Write-Host "  .\\Train-MedicalAgent.ps1 -Agent cardiology -Quick" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  # Full neurology training" -ForegroundColor Gray
    Write-Host "  .\\Train-MedicalAgent.ps1 -Agent neurology -Epochs 3 -DatasetSize 2000" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  # Test existing model" -ForegroundColor Gray
    Write-Host "  .\\Train-MedicalAgent.ps1 -Agent cardiology -TestOnly" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  # Train all agents (quick mode)" -ForegroundColor Gray
    Write-Host "  .\\Train-MedicalAgent.ps1 -Agent all -Quick" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "AVAILABLE AGENTS:" -ForegroundColor Green
    $agents = @("cardiology", "neurology", "emergency", "pulmonology", "pediatric", "infection", "psychiatry", "orthopedic", "general")
    foreach ($agent in $agents) {
        $emoji = Get-AgentEmoji $agent
        Write-Host "  $emoji $agent" -ForegroundColor Cyan
    }
    Write-Host ""
    Write-Host "MODELS:" -ForegroundColor Green
    Write-Host "  unsloth/gemma-3n-E2B-it (2B - recommended for development)" -ForegroundColor Cyan
    Write-Host "  unsloth/gemma-3n-E4B-it (4B - better performance)" -ForegroundColor Cyan
}

# Main execution
function Main {
    if ($args -contains "-h" -or $args -contains "--help" -or $args -contains "help") {
        Show-Help
        return
    }
    
    Write-Header "🏥 HEMA3N Medical Agent Training - PowerShell"
    
    # Check prerequisites
    if (-not (Test-Prerequisites)) {
        Write-Error "Prerequisites check failed"
        Write-Info "Run setup first: .\\scripts\\Setup-LoRAEnvironment.ps1"
        exit 1
    }
    
    # Training logic
    try {
        if ($Agent -eq "all") {
            Start-AllAgentsTraining
        } else {
            $result = Start-Training $Agent
            if (-not $result) {
                exit 1
            }
        }
        
        Write-Header "🎉 Training Session Completed!"
        Write-Success "Your HEMA3N medical AI agents are ready for deployment!"
        
    } catch {
        Write-Error "Training session failed: $_"
        Write-Info "Error details: $($_.Exception.Message)"
        exit 1
    }
}

# Execute main function
Main