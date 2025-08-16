# HEMA3N RTX 2070 Quick Setup
Write-Host "RTX 2070 Setup Starting..." -ForegroundColor Green

# Create virtual environment
python -m venv venv
& ".\venv\Scripts\Activate.ps1"

# Install RTX-optimized packages
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install unsloth transformers datasets trl peft accelerate bitsandbytes timm

Write-Host "RTX 2070 setup complete!" -ForegroundColor Green
Write-Host "Start training with:" -ForegroundColor Yellow  
Write-Host ".\Train-MedicalAgent-Fixed.ps1 -Agent cardiology -MedicalData" -ForegroundColor Cyan