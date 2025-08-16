# Create complete HEMA3N training package for RTX 2070 laptop
Write-Host "📦 Creating HEMA3N RTX 2070 Training Package" -ForegroundColor Green

# Create temporary directory for packaging
$packageDir = "hema3n_rtx_package"
New-Item -ItemType Directory -Force -Path $packageDir

# Copy essential training files
Copy-Item "scripts/finetune_gemma3n_medical.py" "$packageDir/"
Copy-Item "scripts/Train-MedicalAgent-Fixed.ps1" "$packageDir/"
Copy-Item "scripts/Setup-LoRAEnvironment.ps1" "$packageDir/"

# Create RTX-optimized setup script
$setupScript = @'
# HEMA3N RTX 2070 Quick Setup
Write-Host "RTX 2070 Setup Starting..." -ForegroundColor Green

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install RTX-optimized packages
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install unsloth transformers datasets trl peft accelerate bitsandbytes timm

Write-Host "RTX 2070 setup complete!" -ForegroundColor Green
Write-Host "Start training with:" -ForegroundColor Yellow  
Write-Host ".\Train-MedicalAgent-Fixed.ps1 -Agent cardiology -MedicalData" -ForegroundColor Cyan
'@
$setupScript | Out-File -FilePath "$packageDir/Setup-RTX2070.ps1" -Encoding UTF8

# Create quick training script for RTX
$trainingScript = @'
# Quick RTX 2070 training launcher
Write-Host "HEMA3N RTX 2070 Training Starting..." -ForegroundColor Green

python finetune_gemma3n_medical.py --agent cardiology --medical-data --steps 60 --dataset-size 500

Write-Host "Training completed on RTX 2070!" -ForegroundColor Green
'@
$trainingScript | Out-File -FilePath "$packageDir/Start-RTX-Training.ps1" -Encoding UTF8

# Create README for RTX setup
$readmeContent = @'
# HEMA3N RTX 2070 Training Package

## Quick Start (5 minutes setup):

1. Setup Environment:
   .\Setup-RTX2070.ps1

2. Start Training:
   .\Start-RTX-Training.ps1

## RTX 2070 Advantages:
- 10-15 minutes vs 2-3 hours on CPU  
- Unsloth 2x speed optimizations
- 8GB VRAM for larger models
- Native GPU acceleration

## Training Time Estimate:
- Model loading: ~30 seconds (vs 3-4 minutes)
- LoRA setup: ~10 seconds (vs 30 seconds)  
- Training 60 steps: ~10-12 minutes (vs 2-3 hours)
- Total: ~12-15 minutes

## System Requirements:
- NVIDIA RTX 2070 (You have this)
- 16GB RAM (You have this)
- 10GB free space (You have 50GB)
- CUDA 11.8+ (Will be installed)

## Troubleshooting:
If any issues, run: nvidia-smi to verify GPU availability.
'@
$readmeContent | Out-File -FilePath "$packageDir/README.md" -Encoding UTF8

# Create the archive
Compress-Archive -Path $packageDir -DestinationPath "HEMA3N_RTX2070_Package.zip" -Force

# Cleanup
Remove-Item -Recurse -Force $packageDir

Write-Host "✅ Package created: HEMA3N_RTX2070_Package.zip" -ForegroundColor Green
Write-Host "📋 Package contains:" -ForegroundColor Yellow
Write-Host "  • finetune_gemma3n_medical.py (Training script)" -ForegroundColor White
Write-Host "  • Setup-RTX2070.ps1 (Quick RTX setup)" -ForegroundColor White  
Write-Host "  • Start-RTX-Training.ps1 (One-click training)" -ForegroundColor White
Write-Host "  • README.md (Instructions)" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Transfer this file to your RTX 2070 laptop and unzip!" -ForegroundColor Cyan