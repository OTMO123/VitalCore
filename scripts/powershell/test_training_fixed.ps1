# Quick test of the fixed training script
# This should now work with both timm library and CPU fallback

Write-Host "🏥 Testing HEMA3N Fixed Training Script" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Blue

Write-Host "Testing with cardiology agent (quick mode)..." -ForegroundColor Cyan

try {
    python scripts/finetune_gemma3n_medical.py --agent cardiology --steps 10 --dataset-size 50 --medical-data
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Training completed successfully!" -ForegroundColor Green
        Write-Host "🎉 Both issues have been resolved:" -ForegroundColor Yellow
        Write-Host "  • timm library now installed" -ForegroundColor White
        Write-Host "  • CPU fallback for LoRA configuration implemented" -ForegroundColor White
    } else {
        Write-Host "❌ Training failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

Write-Host "`n🚀 To run full training:" -ForegroundColor Green
Write-Host ".\Train-MedicalAgent-Fixed.ps1 -Agent cardiology -MedicalData" -ForegroundColor Yellow