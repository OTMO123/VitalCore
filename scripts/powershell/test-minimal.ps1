$testContent = "test"
$testContent | Out-File -FilePath "test.yml" -Encoding UTF8
Write-Host "Success" -ForegroundColor Green