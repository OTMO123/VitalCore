# Create audit table via PostgreSQL
Write-Host "=== CREATING AUDIT_LOGS TABLE ===" -ForegroundColor Cyan

try {
    # Check if psql is available
    $psqlPath = Get-Command psql -ErrorAction SilentlyContinue
    if ($psqlPath) {
        Write-Host "✅ Found psql at: $($psqlPath.Source)" -ForegroundColor Green
        
        # Execute SQL script
        Write-Host "Creating audit_logs table..." -ForegroundColor Yellow
        $env:PGPASSWORD = "test_password"
        psql -h localhost -p 5433 -U test_user -d test_iris_db -f create_audit_table.sql
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Audit table created successfully!" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to create audit table" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ psql not found. Please install PostgreSQL client tools" -ForegroundColor Red
        Write-Host "Alternative: Run this SQL manually in your PostgreSQL client:" -ForegroundColor Yellow
        Write-Host (Get-Content "create_audit_table.sql" -Raw) -ForegroundColor White
    }
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Manual SQL creation required" -ForegroundColor Yellow
}

Write-Host "`n=== TABLE CREATION COMPLETE ===" -ForegroundColor Cyan