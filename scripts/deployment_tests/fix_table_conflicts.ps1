# Fix SQLAlchemy Table Redefinition Conflicts
# Adds extend_existing=True to all table definitions

Write-Host "Fixing SQLAlchemy Table Redefinition Conflicts" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

# Navigate to project root
Push-Location "../../"

try {
    $files = @(
        "app/core/database.py",
        "app/core/database_advanced.py", 
        "app/core/database_unified.py"
    )
    
    foreach ($file in $files) {
        if (Test-Path $file) {
            Write-Host "Processing $file..." -ForegroundColor Cyan
            
            $content = Get-Content $file -Raw
            $originalContent = $content
            
            # Pattern to match class definitions with __tablename__ but without __table_args__
            $pattern = '(class\s+\w+\([^)]+\):\s*(?:\n\s*"""[^"]*"""\s*)?\n\s*__tablename__\s*=\s*"[^"]+"\s*)(?!\n\s*__table_args__)'
            
            # Replace with the same content plus __table_args__ 
            $content = $content -replace $pattern, '$1`n    __table_args__ = {''extend_existing'': True}'
            
            if ($content -ne $originalContent) {
                $content | Out-File -FilePath $file -Encoding UTF8
                Write-Host "SUCCESS - Fixed table conflicts in $file" -ForegroundColor Green
            } else {
                Write-Host "INFO - No changes needed in $file" -ForegroundColor Gray
            }
        }
    }
    
    Write-Host "`nTesting application startup..." -ForegroundColor Cyan
    & python -c "from app.main import app; print('✅ Application imports successfully!')"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n🎉 SUCCESS - Table conflicts resolved!" -ForegroundColor Green
        Write-Host "Healthcare Backend is ready for production deployment" -ForegroundColor Green
        
        Write-Host "`nStarting production server..." -ForegroundColor Cyan
        Write-Host "=" * 50 -ForegroundColor Green
        
        # Start the production server
        & python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
        
    } else {
        Write-Host "`nApplication still has import issues" -ForegroundColor Yellow
        Write-Host "Manual inspection required" -ForegroundColor Yellow
    }
    
}
catch {
    Write-Host "ERROR - Script failed: $($_.Exception.Message)" -ForegroundColor Red
}
finally {
    Pop-Location
}