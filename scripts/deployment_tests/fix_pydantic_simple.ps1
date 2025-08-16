# Fix Pydantic const=True to Literal - Simple Version
# Russian PowerShell compatible

Write-Host "Fixing Pydantic const=True compatibility issue..." -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

$fileToFix = "../../app/core/events/definitions.py"

if (!(Test-Path $fileToFix)) {
    Write-Host "ERROR - File not found - $fileToFix" -ForegroundColor Red
    exit 1
}

Write-Host "Reading file - $fileToFix" -ForegroundColor Cyan

try {
    # Read the file content
    $content = Get-Content -Path $fileToFix -Raw -Encoding UTF8
    
    Write-Host "Original file size - $($content.Length) characters" -ForegroundColor Gray
    
    # Count const=True occurrences
    $constCount = ($content | Select-String -Pattern "const=True" -AllMatches).Matches.Count
    Write-Host "Found $constCount occurrences of const=True to fix" -ForegroundColor Yellow
    
    if ($constCount -eq 0) {
        Write-Host "No const=True found - file may already be fixed" -ForegroundColor Green
        exit 0
    }
    
    Write-Host "`nApplying fixes..." -ForegroundColor Cyan
    
    # Create backup
    $backupFile = $fileToFix + ".backup"
    $content | Out-File -FilePath $backupFile -Encoding UTF8
    Write-Host "Created backup - $backupFile" -ForegroundColor Gray
    
    # Apply fixes using simple string replacement
    Write-Host "Fix 1 - event_type fields..." -ForegroundColor Cyan
    $content = $content -replace 'event_type: str = Field\(default="([^"]+)", const=True\)', 'event_type: Literal["$1"] = Field(default="$1")'
    
    Write-Host "Fix 2 - aggregate_type fields..." -ForegroundColor Cyan  
    $content = $content -replace 'aggregate_type: str = Field\(default="([^"]+)", const=True\)', 'aggregate_type: Literal["$1"] = Field(default="$1")'
    
    Write-Host "Fix 3 - category fields..." -ForegroundColor Cyan
    $content = $content -replace 'category: EventCategory = Field\(default=EventCategory\.([^,]+), const=True\)', 'category: Literal[EventCategory.$1] = Field(default=EventCategory.$1)'
    
    Write-Host "Fix 4 - priority fields..." -ForegroundColor Cyan
    $content = $content -replace 'priority: EventPriority = Field\(default=EventPriority\.([^,]+), const=True\)', 'priority: Literal[EventPriority.$1] = Field(default=EventPriority.$1)'
    
    Write-Host "Fix 5 - delivery_mode fields..." -ForegroundColor Cyan
    $content = $content -replace 'delivery_mode: DeliveryMode = Field\(default=DeliveryMode\.([^,]+), const=True\)', 'delivery_mode: Literal[DeliveryMode.$1] = Field(default=DeliveryMode.$1)'
    
    Write-Host "Fix 6 - cleanup remaining const=True..." -ForegroundColor Cyan
    $content = $content -replace ', const=True\)', ')'
    
    # Verify fixes
    $remainingCount = ($content | Select-String -Pattern "const=True" -AllMatches).Matches.Count
    Write-Host "Remaining const=True after fix - $remainingCount" -ForegroundColor $(if ($remainingCount -eq 0) { "Green" } else { "Red" })
    
    # Write fixed content
    $content | Out-File -FilePath $fileToFix -Encoding UTF8
    Write-Host "Fixed file saved - $fileToFix" -ForegroundColor Green
    
    Write-Host "`nSUCCESS - Pydantic compatibility fixed!" -ForegroundColor Green
    Write-Host "Fixed $constCount const=True occurrences" -ForegroundColor Green
    Write-Host "File size after fix - $($content.Length) characters" -ForegroundColor Gray
    
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "  1. Run - .\start_production_fixed.ps1" -ForegroundColor White
    Write-Host "  2. Test - .\working_test.ps1" -ForegroundColor White
    
}
catch {
    Write-Host "ERROR - Failed to fix file - $($_.Exception.Message)" -ForegroundColor Red
    
    # Restore backup if it exists
    $backupFile = $fileToFix + ".backup"
    if (Test-Path $backupFile) {
        Write-Host "Restoring from backup..." -ForegroundColor Yellow
        Copy-Item $backupFile $fileToFix -Force
        Write-Host "File restored from backup" -ForegroundColor Green
    }
    
    exit 1
}