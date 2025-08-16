# Run Database Migration - Fix audit_logs schema
# Usage: .\Run-Database-Migration.ps1

Write-Host "🔧 Running database migrations to fix audit_logs schema..." -ForegroundColor Cyan

try {
    # Change to project directory
    $projectRoot = Split-Path -Path $PSScriptRoot -Parent | Split-Path -Parent
    Set-Location $projectRoot
    
    Write-Host "📍 Project directory: $projectRoot" -ForegroundColor Yellow
    
    # Check if alembic.ini exists
    if (-not (Test-Path "alembic.ini")) {
        Write-Host "❌ alembic.ini not found in $projectRoot" -ForegroundColor Red
        exit 1
    }
    
    # Activate virtual environment if it exists
    if (Test-Path "venv/Scripts/Activate.ps1") {
        Write-Host "🔗 Activating virtual environment..." -ForegroundColor Green
        & "venv/Scripts/Activate.ps1"
    }
    
    # Run alembic upgrade
    Write-Host "🚀 Running: alembic upgrade head" -ForegroundColor Green
    & alembic upgrade head
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database migration completed successfully!" -ForegroundColor Green
        Write-Host "🔍 Fixed issues:" -ForegroundColor Yellow
        Write-Host "   - audit_logs.result → audit_logs.outcome" -ForegroundColor White
        Write-Host "   - Added sequence_number column" -ForegroundColor White
        Write-Host "   - Updated check constraints" -ForegroundColor White
    } else {
        Write-Host "❌ Migration failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    }
}
catch {
    Write-Host "❌ Error during migration: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "Next: Test the audit endpoints to verify the fix" -ForegroundColor Cyan