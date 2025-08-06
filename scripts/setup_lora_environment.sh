#!/bin/bash

# HEMA3N Medical LoRA Fine-tuning Environment Setup
# Sets up Unsloth, Gemma 3N, and all required dependencies

set -e

echo "🏥 HEMA3N Medical LoRA Fine-tuning Environment Setup"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running in virtual environment
check_virtual_env() {
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        log_success "Running in virtual environment: $VIRTUAL_ENV"
    else
        log_warning "Not running in virtual environment. Consider creating one:"
        echo "  python -m venv venv"
        echo "  source venv/bin/activate  # Linux/Mac"
        echo "  venv\\Scripts\\activate     # Windows"
    fi
}

# Check Python version
check_python_version() {
    log_info "Checking Python version..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        log_info "Python version: $PYTHON_VERSION"
        
        if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"; then
            log_success "Python version is compatible (>= 3.8)"
        else
            log_error "Python 3.8+ required. Current version: $PYTHON_VERSION"
            exit 1
        fi
    else
        log_error "Python 3 not found. Please install Python 3.8+"
        exit 1
    fi
}

# Check GPU availability
check_gpu() {
    log_info "Checking GPU availability..."
    
    if command -v nvidia-smi &> /dev/null; then
        GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits 2>/dev/null || echo "")
        if [[ ! -z "$GPU_INFO" ]]; then
            log_success "NVIDIA GPU detected:"
            echo "$GPU_INFO" | while read line; do
                echo "  - $line"
            done
            
            # Check CUDA version
            CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}' || echo "Unknown")
            log_info "CUDA Version: $CUDA_VERSION"
        else
            log_warning "nvidia-smi found but no GPU detected"
        fi
    else
        log_warning "No NVIDIA GPU detected. Training will be much slower on CPU."
    fi
}

# Install core dependencies
install_core_dependencies() {
    log_info "Installing core dependencies..."
    
    # Upgrade pip
    python3 -m pip install --upgrade pip
    
    # Install PyTorch with CUDA support
    log_info "Installing PyTorch with CUDA support..."
    python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
    
    # Install transformers (latest for Gemma 3N)
    log_info "Installing latest transformers for Gemma 3N..."
    python3 -m pip install --upgrade transformers
    
    # Install additional ML dependencies
    python3 -m pip install datasets accelerate peft trl
    python3 -m pip install bitsandbytes  # For 4-bit quantization
    python3 -m pip install scipy numpy  # Scientific computing
    
    log_success "Core dependencies installed"
}

# Install Unsloth for optimized training
install_unsloth() {
    log_info "Installing Unsloth for optimized LoRA training..."
    
    # Check if running in Colab
    if python3 -c "import os; exit(0 if 'COLAB_' in ''.join(os.environ.keys()) else 1)" 2>/dev/null; then
        log_info "Google Colab detected - using Colab-specific installation"
        python3 -m pip install --no-deps bitsandbytes accelerate xformers peft trl triton
        python3 -m pip install sentencepiece protobuf "datasets>=3.4.1,<4.0.0" "huggingface_hub>=0.34.0" hf_transfer
        python3 -m pip install --no-deps unsloth
    else
        log_info "Local environment detected - using standard installation"
        python3 -m pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
    fi
    
    log_success "Unsloth installed"
}

# Install additional medical AI dependencies
install_medical_dependencies() {
    log_info "Installing medical AI dependencies..."
    
    # YAML for configuration
    python3 -m pip install pyyaml
    
    # Medical data processing
    python3 -m pip install pandas scikit-learn
    
    # Optional: Medical NLP libraries
    log_info "Installing optional medical NLP libraries..."
    python3 -m pip install spacy || log_warning "spaCy installation failed (optional)"
    
    # Optional: Weights & Biases for monitoring
    python3 -m pip install wandb || log_warning "wandb installation failed (optional)"
    
    # Optional: Medical image processing
    python3 -m pip install pillow opencv-python || log_warning "Image processing libraries failed (optional)"
    
    log_success "Medical dependencies installed"
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    # Test imports
    python3 -c "
import torch
print(f'✓ PyTorch: {torch.__version__}')
print(f'✓ CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'✓ CUDA devices: {torch.cuda.device_count()}')
    for i in range(torch.cuda.device_count()):
        print(f'  - GPU {i}: {torch.cuda.get_device_name(i)}')
"
    
    python3 -c "
import transformers
print(f'✓ Transformers: {transformers.__version__}')
"
    
    python3 -c "
try:
    from unsloth import FastModel
    print('✓ Unsloth: Available')
except ImportError as e:
    print(f'✗ Unsloth: {e}')
"
    
    python3 -c "
try:
    from trl import SFTTrainer, SFTConfig
    print('✓ TRL: Available')
except ImportError as e:
    print(f'✗ TRL: {e}')
"
    
    python3 -c "
try:
    import peft
    print(f'✓ PEFT: {peft.__version__}')
except ImportError as e:
    print(f'✗ PEFT: {e}')
"
    
    log_success "Installation verification completed"
}

# Create example training script
create_example_script() {
    log_info "Creating example training script..."
    
    cat > example_train_cardiology.sh << 'EOF'
#!/bin/bash

# Example: Train HEMA3N Cardiology Agent with LoRA

echo "🫀 Training HEMA3N Cardiology Agent with LoRA fine-tuning..."

python3 scripts/finetune_gemma3n_medical.py \
    --agent cardiology \
    --model "unsloth/gemma-3n-E2B-it" \
    --epochs 1 \
    --steps 60 \
    --batch-size 1 \
    --learning-rate 2e-4 \
    --lora-rank 8 \
    --dataset-size 500 \
    --medical-data \
    --output-dir "./models/medical_agents"

echo "✅ Cardiology agent training completed!"
echo "🧪 Test the model with:"
echo "python3 scripts/finetune_gemma3n_medical.py --agent cardiology --test-only"
EOF

    chmod +x example_train_cardiology.sh
    log_success "Example script created: example_train_cardiology.sh"
}

# Create requirements.txt
create_requirements() {
    log_info "Creating requirements.txt..."
    
    cat > requirements_lora.txt << 'EOF'
# HEMA3N Medical LoRA Fine-tuning Requirements

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

# Medical NLP (Optional)
spacy>=3.6.0

# Utilities
sentencepiece>=0.1.99
protobuf>=3.20.0
huggingface_hub>=0.16.0
hf_transfer>=0.1.0
EOF

    log_success "Requirements file created: requirements_lora.txt"
}

# Main execution
main() {
    echo
    log_info "Starting HEMA3N Medical LoRA Environment Setup..."
    echo
    
    check_virtual_env
    check_python_version
    check_gpu
    
    echo
    log_info "Installing dependencies..."
    install_core_dependencies
    install_unsloth
    install_medical_dependencies
    
    echo
    log_info "Verifying installation..."
    verify_installation
    
    echo
    log_info "Creating additional files..."
    create_example_script
    create_requirements
    
    echo
    log_success "🎉 HEMA3N Medical LoRA Environment Setup Complete!"
    echo
    echo "Next steps:"
    echo "1. Review the configuration: config/lora_training_config.yaml"
    echo "2. Start training: ./example_train_cardiology.sh"
    echo "3. Or use the full script: python3 scripts/finetune_gemma3n_medical.py --help"
    echo
    echo "Available models for training:"
    echo "  - unsloth/gemma-3n-E2B-it (2B parameters, recommended for development)"
    echo "  - unsloth/gemma-3n-E4B-it (4B parameters, better performance)"
    echo
    echo "🏥 Ready to train specialized medical AI agents!"
}

# Run main function
main "$@"