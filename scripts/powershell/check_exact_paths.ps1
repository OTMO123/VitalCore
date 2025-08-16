# Check Exact Clinical Workflows Paths
# This script will show the exact registered paths for clinical workflows

Write-Host "CHECKING EXACT CLINICAL WORKFLOWS PATHS" -ForegroundColor Green
Write-Host "======================================="

$pythonScript = @"
from app.main import app

print('Clinical Workflows Routes:')
for route in app.routes:
    if hasattr(route, 'path') and 'clinical-workflows' in route.path:
        methods = getattr(route, 'methods', set())
        print(f'  {list(methods)} {route.path}')

print('')
print('All /api/v1/ routes:')
count = 0
for route in app.routes:
    if hasattr(route, 'path') and route.path.startswith('/api/v1/'):
        if count < 20:  # Show first 20 to avoid spam
            methods = getattr(route, 'methods', set())
            print(f'  {list(methods)} {route.path}')
        count += 1

if count > 20:
    print(f'  ... and {count - 20} more routes')
"@

try {
    Write-Host "Getting exact paths from FastAPI app..." -ForegroundColor White
    $result = docker-compose exec app python -c $pythonScript
    
    Write-Host "`nEXACT PATHS:" -ForegroundColor Green
    Write-Host $result -ForegroundColor White
    
} catch {
    Write-Host "`nERROR:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host "`nTEST THESE EXACT PATHS:" -ForegroundColor Cyan
Write-Host "Copy the exact paths above and test them:" -ForegroundColor White
Write-Host "curl http://localhost:8000[EXACT_PATH_HERE]" -ForegroundColor Gray