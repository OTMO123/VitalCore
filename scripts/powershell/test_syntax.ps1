# Test syntax for Start-Training function
function Test-StartTraining {
    param($AgentName)
    
    if ($TestOnly) {
        Write-Host "Test only mode"
    } else {
        Write-Host "Full training mode"
        if ($MedicalData) {
            Write-Host "Using medical data"
        }
        if ($Multimodal) {
            Write-Host "Using multimodal"
        }
        if ($Quick) {
            Write-Host "Quick mode"
        }
    }
    
    try {
        Write-Host "Training started"
        if ($true) {
            Write-Host "Training completed"
        } else {
            Write-Host "Training failed"
            return $false
        }
    } catch {
        Write-Host "Error occurred"
        return $false
    }
    
    return $true
}

Write-Host "Syntax test passed"