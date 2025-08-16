# Example: Train HEMA3N Cardiology Agent with LoRA
# PowerShell version

Write-Host "рџ«Ђ Training HEMA3N Cardiology Agent with LoRA fine-tuning..." -ForegroundColor Green

python scripts/finetune_gemma3n_medical.py `
    --agent cardiology `
    --model "unsloth/gemma-3n-E2B-it" `
    --epochs 1 `
    --steps 60 `
    --batch-size 1 `
    --learning-rate 2e-4 `
    --lora-rank 8 `
    --dataset-size 500 `
    --medical-data `
    --output-dir "./models/medical_agents"

Write-Host "вњ… Cardiology agent training completed!" -ForegroundColor Green
Write-Host "рџ§Є Test the model with:" -ForegroundColor Yellow
Write-Host "python scripts/finetune_gemma3n_medical.py --agent cardiology --test-only" -ForegroundColor Yellow
