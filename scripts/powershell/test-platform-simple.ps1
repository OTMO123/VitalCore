# Simple Platform Testing Script
Write-Host "Testing Enterprise Healthcare AI/ML Platform" -ForegroundColor Green

# Test basic smoke tests first
Write-Host "`nRunning basic smoke tests..." -ForegroundColor Cyan
python -m pytest app/tests/smoke/test_basic.py -v

Write-Host "`nRunning core functionality tests..." -ForegroundColor Cyan  
python -m pytest app/tests/core/test_event_bus.py -v

Write-Host "`nRunning security tests..." -ForegroundColor Cyan
python -m pytest app/tests/core/security/test_audit_logging.py -v

Write-Host "`nTesting completed!" -ForegroundColor Green