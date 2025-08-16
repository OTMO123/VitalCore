# HEMA3N Medical LoRA Fine-tuning Environment Setup - PowerShell Version
# Sets up Unsloth, Gemma 3N, and all required dependencies for Windows

param(
    [switch]$SkipGPUCheck,
    [switch]$InstallCUDA,
    [string]$PythonPath = "python"
)

# Enable strict mode for better error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Colors for output
$Colors = @{
    Red = "Red"
    Green = "Green" 
    Yellow = "Yellow"
    Blue = "Cyan"
    White = "White"
}

function Write-LogInfo($Message) {
    Write-Host "[INFO] $Message" -ForegroundColor $Colors.Blue
}

function Write-LogSuccess($Message) {
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Colors.Green
}

function Write-LogWarning($Message) {
    Write-Host "[WARNING] $Message" -ForegroundColor $Colors.Yellow
}

function Write-LogError($Message) {
    Write-Host "[ERROR] $Message" -ForegroundColor $Colors.Red
}

function Write-Header($Title) {
    Write-Host ""
    Write-Host "=" * 70 -ForegroundColor $Colors.Blue
    Write-Host $Title -ForegroundColor $Colors.White
    Write-Host "=" * 70 -ForegroundColor $Colors.Blue
    Write-Host ""
}

function Test-PythonVersion {
    Write-LogInfo "Checking Python version..."
    
    try {
        $pythonVersion = & $PythonPath --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-LogInfo "Python version: $pythonVersion"
            
            # Check if version is 3.8+
            $versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
            if ($versionMatch) {
                $major = [int]$matches[1]
                $minor = [int]$matches[2]
                
                if ($major -ge 3 -and $minor -ge 8) {
                    Write-LogSuccess "Python version is compatible (>= 3.8)"
                    return $true
                } else {
                    Write-LogError "Python 3.8+ required. Current version: $pythonVersion"
                    return $false
                }
            }
        }
    } catch {
        Write-LogError "Python not found. Please install Python 3.8+ from https://python.org"
        Write-LogInfo "Make sure to add Python to PATH during installation"
        return $false
    }
    
    return $false
}

function Test-VirtualEnvironment {
    if ($env:VIRTUAL_ENV) {
        Write-LogSuccess "Running in virtual environment: $env:VIRTUAL_ENV"
    } else {
        Write-LogWarning "Not running in virtual environment. Consider creating one:"
        Write-Host "  python -m venv venv" -ForegroundColor Yellow
        Write-Host "  venv\Scripts\activate.ps1" -ForegroundColor Yellow
        Write-Host ""
        
        $response = Read-Host "Would you like to create a virtual environment now? (y/N)"
        if ($response -match "^[Yy]") {
            Create-VirtualEnvironment
            return $true
        }
    }
    return $false
}

function Create-VirtualEnvironment {
    Write-LogInfo "Creating virtual environment..."
    
    try {
        & $PythonPath -m venv venv
        Write-LogSuccess "Virtual environment created"
        
        Write-LogInfo "Activating virtual environment..."
        & "venv\Scripts\activate.ps1"
        
        # Update Python path to use venv
        $script:PythonPath = "venv\Scripts\python.exe"
        
        Write-LogSuccess "Virtual environment activated"
    } catch {
        Write-LogError "Failed to create virtual environment: $_"
        return $false
    }
    
    return $true
}

function Test-GPUAvailability {
    if ($SkipGPUCheck) {
        Write-LogInfo "Skipping GPU check as requested"
        return
    }
    
    Write-LogInfo "Checking GPU availability..."
    
    try {
        $nvidiaInfo = nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits 2>$null
        if ($nvidiaInfo) {
            Write-LogSuccess "NVIDIA GPU(s) detected:"
            $nvidiaInfo | ForEach-Object {
                Write-Host "  - $_" -ForegroundColor Green
            }
            
            # Check CUDA version
            $cudaVersion = nvidia-smi | Select-String "CUDA Version" | ForEach-Object { ($_ -split "\s+")[8] }
            if ($cudaVersion) {
                Write-LogInfo "CUDA Version: $cudaVersion"
            }
        } else {
            Write-LogWarning "nvidia-smi found but no GPU detected"
        }
    } catch {
        Write-LogWarning "No NVIDIA GPU detected. Training will be much slower on CPU."
        Write-LogInfo "For GPU acceleration, install CUDA from: https://developer.nvidia.com/cuda-downloads"
        
        if ($InstallCUDA) {
            Write-LogInfo "Consider installing CUDA for much faster training"
        }
    }
}

function Install-CoreDependencies {
    Write-LogInfo "Installing core dependencies..."
    
    # Upgrade pip first
    Write-LogInfo "Upgrading pip..."
    & $PythonPath -m pip install --upgrade pip
    
    if ($LASTEXITCODE -ne 0) {
        Write-LogError "Failed to upgrade pip"
        return $false
    }
    
    # Install PyTorch with CUDA support
    Write-LogInfo "Installing PyTorch with CUDA support..."
    & $PythonPath -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
    
    if ($LASTEXITCODE -ne 0) {
        Write-LogWarning "CUDA PyTorch installation failed, trying CPU version..."
        & $PythonPath -m pip install torch torchvision torchaudio
    }
    
    # Install transformers (latest for Gemma 3N)
    Write-LogInfo "Installing latest transformers for Gemma 3N..."
    & $PythonPath -m pip install --upgrade transformers
    
    # Install additional ML dependencies
    Write-LogInfo "Installing ML dependencies..."
    $mlPackages = @(
        "datasets", 
        "accelerate", 
        "peft", 
        "trl",
        "bitsandbytes",
        "scipy", 
        "numpy"
    )
    
    foreach ($package in $mlPackages) {
        Write-LogInfo "Installing $package..."
        & $PythonPath -m pip install $package
        
        if ($LASTEXITCODE -ne 0) {
            Write-LogWarning "Failed to install $package"
        }
    }
    
    Write-LogSuccess "Core dependencies installed"
    return $true
}

function Install-Unsloth {
    Write-LogInfo "Installing Unsloth for optimized LoRA training..."
    
    try {
        # Check if running in Google Colab (unlikely on Windows, but let's check)
        $isColab = $env:COLAB_GPU -or $env:COLAB_TPU
        
        if ($isColab) {
            Write-LogInfo "Colab environment detected - using Colab-specific installation"
            & $PythonPath -m pip install --no-deps bitsandbytes accelerate xformers peft trl triton
            & $PythonPath -m pip install sentencepiece protobuf "datasets>=3.4.1,<4.0.0" "huggingface_hub>=0.34.0" hf_transfer
            & $PythonPath -m pip install --no-deps unsloth
        } else {
            Write-LogInfo "Local Windows environment detected - using standard installation"
            
            # Try installing unsloth
            & $PythonPath -m pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
            
            if ($LASTEXITCODE -ne 0) {
                Write-LogWarning "Git installation failed, trying alternative method..."
                & $PythonPath -m pip install unsloth
            }
        }
        
        Write-LogSuccess "Unsloth installed"
        return $true
    } catch {
        Write-LogError "Unsloth installation failed: $_"
        Write-LogInfo "You can continue without Unsloth, but training will be slower"
        return $false
    }
}

function Install-MedicalDependencies {
    Write-LogInfo "Installing medical AI dependencies..."
    
    $medicalPackages = @{
        "pyyaml" = "YAML configuration support"
        "pandas" = "Data processing"
        "scikit-learn" = "Machine learning utilities"
        "Pillow" = "Image processing (optional)"
        "opencv-python" = "Computer vision (optional)"
        "wandb" = "Experiment tracking (optional)"
    }
    
    foreach ($package in $medicalPackages.Keys) {
        Write-LogInfo "Installing $package - $($medicalPackages[$package])..."
        & $PythonPath -m pip install $package
        
        if ($LASTEXITCODE -eq 0) {
            Write-LogSuccess "$package installed successfully"
        } else {
            Write-LogWarning "$package installation failed (optional dependency)"
        }
    }
    
    Write-LogSuccess "Medical dependencies installation completed"
}

function Test-Installation {
    Write-LogInfo "Verifying installation..."
    
    $testScript = @"
import sys
print(f'Python: {sys.version.split()[0]}')

try:
    import torch
    print(f'✓ PyTorch: {torch.__version__}')
    print(f'✓ CUDA available: {torch.cuda.is_available()}')
    if torch.cuda.is_available():
        print(f'✓ CUDA devices: {torch.cuda.device_count()}')
        for i in range(torch.cuda.device_count()):
            print(f'  - GPU {i}: {torch.cuda.get_device_name(i)}')
    else:
        print('⚠ CUDA not available (CPU only)')
except ImportError as e:
    print(f'✗ PyTorch: {e}')

try:
    import transformers
    print(f'✓ Transformers: {transformers.__version__}')
except ImportError as e:
    print(f'✗ Transformers: {e}')

try:
    from unsloth import FastModel
    print('✓ Unsloth: Available')
except ImportError as e:
    print(f'⚠ Unsloth: {e}')

try:
    from trl import SFTTrainer, SFTConfig
    print('✓ TRL: Available')
except ImportError as e:
    print(f'✗ TRL: {e}')

try:
    import peft
    print(f'✓ PEFT: {peft.__version__}')
except ImportError as e:
    print(f'✗ PEFT: {e}')

try:
    import yaml
    print('✓ YAML: Available')
except ImportError as e:
    print(f'⚠ YAML: {e}')
"@
    
    $testScript | & $PythonPath -c "exec(open(0).read())"
    
    Write-LogSuccess "Installation verification completed"
}

function New-ExampleScript {
    Write-LogInfo "Creating example training script..."
    
    $exampleScript = @"
# Example: Train HEMA3N Cardiology Agent with LoRA
# PowerShell version

Write-Host "🫀 Training HEMA3N Cardiology Agent with LoRA fine-tuning..." -ForegroundColor Green

python scripts/finetune_gemma3n_medical.py ``
    --agent cardiology ``
    --model "unsloth/gemma-3n-E2B-it" ``
    --epochs 1 ``
    --steps 60 ``
    --batch-size 1 ``
    --learning-rate 2e-4 ``
    --lora-rank 8 ``
    --dataset-size 500 ``
    --medical-data ``
    --output-dir "./models/medical_agents"

Write-Host "✅ Cardiology agent training completed!" -ForegroundColor Green
Write-Host "🧪 Test the model with:" -ForegroundColor Yellow
Write-Host "python scripts/finetune_gemma3n_medical.py --agent cardiology --test-only" -ForegroundColor Yellow
"@
    
    $exampleScript | Out-File -FilePath "Train-CardiologyAgent.ps1" -Encoding UTF8
    Write-LogSuccess "Example script created: Train-CardiologyAgent.ps1"
}

function New-RequirementsFile {
    Write-LogInfo "Creating requirements.txt..."
    
    $requirements = @"
# HEMA3N Medical LoRA Fine-tuning Requirements - Windows

# Core ML Framework
torch>=2.0.0
torchvision
torchaudio

# Transformers and Model Training  
transformers>=4.40.0
datasets>=2.14.0
accelerate>=0.20.0
peft>=0.4.0
trl>=0.7.0

# Quantization and Optimization
bitsandbytes>=0.41.0
unsloth

# Medical AI and Data Processing
pyyaml>=6.0
pandas>=1.5.0
scikit-learn>=1.3.0
numpy>=1.24.0
scipy>=1.10.0

# Image and Audio Processing (Optional)
pillow>=9.0.0
opencv-python>=4.7.0

# Monitoring and Logging (Optional)
wandb>=0.15.0

# Utilities
sentencepiece>=0.1.99
protobuf>=3.20.0
huggingface_hub>=0.16.0
hf_transfer>=0.1.0
"@
    
    $requirements | Out-File -FilePath "requirements_lora_windows.txt" -Encoding UTF8
    Write-LogSuccess "Requirements file created: requirements_lora_windows.txt"
}

function Show-NextSteps {
    Write-Header "🎉 HEMA3N Medical LoRA Environment Setup Complete!"
    
    Write-Host "Next steps:" -ForegroundColor Green
    Write-Host "1. Review the configuration: config/lora_training_config.yaml" -ForegroundColor Yellow
    Write-Host "2. Start training: .\Train-CardiologyAgent.ps1" -ForegroundColor Yellow
    Write-Host "3. Or use the full script: python scripts/finetune_gemma3n_medical.py --help" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Available models for training:" -ForegroundColor Green
    Write-Host "  - unsloth/gemma-3n-E2B-it (2B parameters, recommended for development)" -ForegroundColor Cyan
    Write-Host "  - unsloth/gemma-3n-E4B-it (4B parameters, better performance)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🏥 Ready to train specialized medical AI agents!" -ForegroundColor Green
    
    if ($env:VIRTUAL_ENV) {
        Write-Host ""
        Write-Host "Remember: You're in a virtual environment. To reactivate later:" -ForegroundColor Yellow
        Write-Host "  venv\Scripts\activate.ps1" -ForegroundColor Cyan
    }
}

function Install-CUDAIfRequested {
    if ($InstallCUDA) {
        Write-LogInfo "CUDA installation requested..."
        Write-LogWarning "Please download and install CUDA manually from:"
        Write-Host "https://developer.nvidia.com/cuda-downloads" -ForegroundColor Cyan
        Write-LogInfo "After CUDA installation, restart PowerShell and run this script again"
        
        $response = Read-Host "Have you already installed CUDA? (y/N)"
        if ($response -notmatch "^[Yy]") {
            Write-LogInfo "Please install CUDA first, then run this script again"
            exit 1
        }
    }
}

# Main execution
function Main {
    Write-Header "🏥 HEMA3N Medical LoRA Fine-tuning Environment Setup - PowerShell"
    
    Write-LogInfo "Starting HEMA3N Medical LoRA Environment Setup..."
    
    # Check CUDA installation if requested
    Install-CUDAIfRequested
    
    # Check Python version
    if (-not (Test-PythonVersion)) {
        Write-LogError "Python setup failed. Please install Python 3.8+ from https://python.org"
        exit 1
    }
    
    # Check/create virtual environment
    Test-VirtualEnvironment
    
    # Check GPU availability
    Test-GPUAvailability
    
    Write-LogInfo "Installing dependencies..."
    
    # Install core dependencies
    if (-not (Install-CoreDependencies)) {
        Write-LogError "Core dependencies installation failed"
        exit 1
    }
    
    # Install Unsloth
    Install-Unsloth
    
    # Install medical dependencies
    Install-MedicalDependencies
    
    Write-LogInfo "Verifying installation..."
    Test-Installation
    
    Write-LogInfo "Creating additional files..."
    New-ExampleScript
    New-RequirementsFile
    
    Show-NextSteps
}

# Execute main function
try {
    Main
} catch {
    Write-LogError "Setup failed: $_"
    Write-LogInfo "Error details: $($_.Exception.Message)"
    exit 1
}