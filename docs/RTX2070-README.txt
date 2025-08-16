HEMA3N RTX 2070 Training Package

Quick Start (5 minutes setup):

1. Setup Environment:
   .\Setup-RTX2070-Simple.ps1

2. Start Training:
   .\Train-MedicalAgent-Fixed.ps1 -Agent cardiology -MedicalData

RTX 2070 Advantages:
- 10-15 minutes vs 2-3 hours on CPU  
- Unsloth 2x speed optimizations
- 8GB VRAM for larger models
- Native GPU acceleration

Training Time Estimate:
- Model loading: ~30 seconds (vs 3-4 minutes)
- LoRA setup: ~10 seconds (vs 30 seconds)  
- Training 60 steps: ~10-12 minutes (vs 2-3 hours)
- Total: ~12-15 minutes

System Requirements:
- NVIDIA RTX 2070 (You have this)
- 16GB RAM (You have this) 
- 10GB free space (You have 50GB)
- CUDA 11.8+ (Will be installed)

Troubleshooting:
If any issues, run: nvidia-smi to verify GPU availability.