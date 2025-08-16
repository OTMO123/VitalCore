# Test PowerShell syntax validation
$testContent = "version: '3.8'"
$testContent | Out-File -FilePath "test-output.yml" -Encoding UTF8
Write-Host "Syntax test passed" -ForegroundColor Green