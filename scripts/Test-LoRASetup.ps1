# Test HEMA3N LoRA Setup - Quick Verification Script

param(
    [switch]$Detailed
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

function Write-TestResult {
    param(
        [string]$Test,
        [bool]$Result,
        [string]$Details = ""
    )
    
    $emoji = if ($Result) { "OK" } else { "FAIL" }
    $color = if ($Result) { "Green" } else { "Red" }
    
    Write-Host "$emoji $Test" -ForegroundColor $color
    if ($Details -and $Detailed) {
        Write-Host "   $Details" -ForegroundColor Gray
    }
}

function Test-LoRAEnvironment {
    Write-Host ""
    Write-Host "HEMA3N LoRA Setup Verification" -ForegroundColor Blue
    Write-Host "=" * 40 -ForegroundColor Blue
    Write-Host ""
    
    $allPassed = $true
    
    # Test 1: Python availability
    try {
        $pythonVersion = & python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-TestResult -Test "Python Installation" -Result $true -Details $pythonVersion
        } else {
            Write-TestResult -Test "Python Installation" -Result $false -Details "Python command failed"
            $allPassed = $false
        }
    } catch {
        Write-TestResult -Test "Python Installation" -Result $false -Details "Python not found in PATH"
        $allPassed = $false
    }
    
    # Test 2: Required files exist
    $requiredFiles = @(
        "scripts/Setup-LoRAEnvironment.ps1",
        "scripts/Train-MedicalAgent.ps1", 
        "scripts/finetune_gemma3n_medical.py",
        "config/lora_training_config.yaml",
        "POWERSHELL_QUICKSTART.md"
    )
    
    foreach ($file in $requiredFiles) {
        $exists = Test-Path $file
        Write-TestResult "File: $file" $exists
        if (-not $exists) { $allPassed = $false }
    }
    
    # Test 3: Python packages (basic check)
    $pythonTest = @'
try:
    import sys
    print(f"Python: {sys.version.split()[0]}")
    
    try:
        import torch
        print(f"PyTorch: Available")
        cuda_available = torch.cuda.is_available()
        print(f"CUDA: {cuda_available}")
    except ImportError:
        print("PyTorch: Not installed")
    
    try:
        import transformers
        print("Transformers: Available")
    except ImportError:
        print("Transformers: Not installed")
        
    try:
        from unsloth import FastModel
        print("Unsloth: Available")
    except ImportError:
        print("Unsloth: Not installed")
        
    try:
        import yaml
        print("YAML: Available")
    except ImportError:
        print("YAML: Not installed")
        
except Exception as e:
    print(f"Error: {e}")
'@
    
    Write-Host ""
    Write-Host "Python Package Check:" -ForegroundColor Yellow
    try {
        # Create temp file for Python script
        $tempFile = [System.IO.Path]::GetTempFileName() + ".py"
        $pythonTest | Out-File -FilePath $tempFile -Encoding UTF8
        $pythonOutput = python $tempFile 2>&1
        foreach ($line in $pythonOutput) {
            if ($line -match "Available|True") {
                Write-Host "   OK $line" -ForegroundColor Green
            } elseif ($line -match "Not installed|False") {
                Write-Host "   WARN $line" -ForegroundColor Yellow
            } else {
                Write-Host "   INFO $line" -ForegroundColor Cyan
            }
        }
        Remove-Item $tempFile -ErrorAction SilentlyContinue
    } catch {
        Write-Host "   ERROR Python package check failed" -ForegroundColor Red
        $allPassed = $false
    }
    
    # Test 4: GPU Check
    Write-Host ""
    Write-Host "GPU Check:" -ForegroundColor Yellow
    try {
        $gpuInfo = nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits 2>$null
        if ($gpuInfo) {
            Write-Host "   OK NVIDIA GPU detected:" -ForegroundColor Green
            foreach ($gpu in $gpuInfo) {
                Write-Host "      - $gpu" -ForegroundColor Cyan
            }
        } else {
            Write-Host "   WARN No NVIDIA GPU detected (CPU training only)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   WARN GPU check failed (nvidia-smi not found)" -ForegroundColor Yellow
    }
    
    # Summary
    Write-Host ""
    Write-Host "Setup Status:" -ForegroundColor Blue
    if ($allPassed) {
        Write-Host "   SUCCESS All core components verified!" -ForegroundColor Green
        Write-Host "   OK Ready to start LoRA fine-tuning" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "   1. .\\scripts\\Setup-LoRAEnvironment.ps1  # If not run yet" -ForegroundColor Cyan
        Write-Host "   2. .\\scripts\\Train-MedicalAgent.ps1 -Agent cardiology -Quick" -ForegroundColor Cyan
        Write-Host "   3. Get-Content POWERSHELL_QUICKSTART.md  # Read full guide" -ForegroundColor Cyan
    } else {
        Write-Host "   WARN Some components need attention" -ForegroundColor Yellow
        Write-Host "   SETUP Run setup script: .\\scripts\\Setup-LoRAEnvironment.ps1" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

# Run the test
Test-LoRAEnvironment