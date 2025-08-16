# Fix Pydantic const=True to Literal - Production Fix
# Fixes compatibility issue with Pydantic v2

Write-Host "Fixing Pydantic const=True compatibility issue..." -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

$fileToFix = "../../app/core/events/definitions.py"

if (!(Test-Path $fileToFix)) {
    Write-Host "ERROR: File not found - $fileToFix" -ForegroundColor Red
    exit 1
}

Write-Host "Reading file: $fileToFix" -ForegroundColor Cyan

try {
    # Read the file content
    $content = Get-Content -Path $fileToFix -Raw -Encoding UTF8
    $originalContent = $content
    
    Write-Host "Original file size: $($content.Length) characters" -ForegroundColor Gray
    
    # Count const=True occurrences
    $constMatches = [regex]::Matches($content, 'const=True')
    Write-Host "Found $($constMatches.Count) occurrences of const=True to fix" -ForegroundColor Yellow
    
    if ($constMatches.Count -eq 0) {
        Write-Host "No const=True found - file may already be fixed" -ForegroundColor Green
        exit 0
    }
    
    Write-Host "`nApplying fixes..." -ForegroundColor Cyan
    
    # Replace patterns systematically
    # Pattern 1: event_type with const=True
    $content = $content -replace 'event_type: str = Field\(default="([^"]+)", const=True\)', 'event_type: Literal["$1"] = Field(default="$1")'
    
    # Pattern 2: aggregate_type with const=True  
    $content = $content -replace 'aggregate_type: str = Field\(default="([^"]+)", const=True\)', 'aggregate_type: Literal["$1"] = Field(default="$1")'
    
    # Pattern 3: category with const=True
    $content = $content -replace 'category: EventCategory = Field\(default=EventCategory\.([^,]+), const=True\)', 'category: Literal[EventCategory.$1] = Field(default=EventCategory.$1)'
    
    # Pattern 4: priority with const=True
    $content = $content -replace 'priority: EventPriority = Field\(default=EventPriority\.([^,]+), const=True\)', 'priority: Literal[EventPriority.$1] = Field(default=EventPriority.$1)'
    
    # Pattern 5: delivery_mode with const=True
    $content = $content -replace 'delivery_mode: DeliveryMode = Field\(default=DeliveryMode\.([^,]+), const=True\)', 'delivery_mode: Literal[DeliveryMode.$1] = Field(default=DeliveryMode.$1)'
    
    # Pattern 6: any remaining const=True (fallback)
    $content = $content -replace ', const=True\)', ')'
    
    # Verify fixes
    $remainingConst = [regex]::Matches($content, 'const=True')
    Write-Host "Remaining const=True after fix: $($remainingConst.Count)" -ForegroundColor $(if ($remainingConst.Count -eq 0) { "Green" } else { "Red" })
    
    if ($remainingConst.Count -gt 0) {
        Write-Host "WARNING: Some const=True patterns may need manual fixing" -ForegroundColor Yellow
        foreach ($match in $remainingConst) {
            $lineStart = $content.Substring(0, $match.Index).Split("`n").Count
            Write-Host "  Line ~$lineStart: ...$(($content.Substring($match.Index - 20, 40) -replace "`n", " "))..." -ForegroundColor Gray
        }
    }
    
    # Backup original file
    $backupFile = $fileToFix + ".backup"
    $originalContent | Out-File -FilePath $backupFile -Encoding UTF8
    Write-Host "Created backup: $backupFile" -ForegroundColor Gray
    
    # Write fixed content
    $content | Out-File -FilePath $fileToFix -Encoding UTF8
    Write-Host "Fixed file saved: $fileToFix" -ForegroundColor Green
    
    Write-Host "`nSUCCESS: Pydantic compatibility fixed!" -ForegroundColor Green
    Write-Host "Fixed $($constMatches.Count) const=True occurrences" -ForegroundColor Green
    Write-Host "File size after fix: $($content.Length) characters" -ForegroundColor Gray
    
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "  1. Run: .\start_production_fixed.ps1" -ForegroundColor White
    Write-Host "  2. Test: .\working_test.ps1" -ForegroundColor White
    
}
catch {
    Write-Host "ERROR: Failed to fix file - $($_.Exception.Message)" -ForegroundColor Red
    
    # Restore backup if it exists
    $backupFile = $fileToFix + ".backup"
    if (Test-Path $backupFile) {
        Write-Host "Restoring from backup..." -ForegroundColor Yellow
        Copy-Item $backupFile $fileToFix -Force
        Write-Host "File restored from backup" -ForegroundColor Green
    }
    
    exit 1
}