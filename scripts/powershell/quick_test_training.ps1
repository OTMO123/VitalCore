# Quick training test - minimal parameters to save time
Write-Host "🚀 Quick HEMA3N Training Test" -ForegroundColor Green

try {
    # Use minimal parameters to test the training pipeline
    python scripts/finetune_gemma3n_medical.py `
        --agent cardiology `
        --steps 3 `
        --dataset-size 10 `
        --medical-data `
        --batch-size 1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Quick test successful! Training pipeline works." -ForegroundColor Green
        Write-Host "🎉 Ready for full training!" -ForegroundColor Yellow
    } else {
        Write-Host "❌ Quick test failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}