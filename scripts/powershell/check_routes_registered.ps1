# Check if Clinical Workflows Routes are Registered in FastAPI
# This script will show if the routes are actually registered with the FastAPI app

Write-Host "CHECKING FASTAPI ROUTE REGISTRATION" -ForegroundColor Green
Write-Host "==================================="

Write-Host "`nChecking if clinical workflows routes are registered..." -ForegroundColor Cyan

$pythonScript = @"
from app.main import app

# Get all routes
routes = []
for route in app.routes:
    if hasattr(route, 'path'):
        routes.append({
            'path': route.path,
            'methods': getattr(route, 'methods', [])
        })

# Filter clinical workflows routes
clinical_routes = [r for r in routes if 'clinical-workflows' in r['path']]
print(f'Total routes: {len(routes)}')
print(f'Clinical workflow routes: {len(clinical_routes)}')

if clinical_routes:
    print('Clinical workflow endpoints found:')
    for route in clinical_routes:
        print(f'  {list(route["methods"])} {route["path"]}')
else:
    print('No clinical workflow routes found in FastAPI app')
"@

try {
    Write-Host "Running route check inside Docker container..." -ForegroundColor White
    $result = docker-compose exec app python -c $pythonScript
    
    Write-Host "`nROUTE CHECK RESULTS:" -ForegroundColor Green
    Write-Host $result -ForegroundColor White
    
    # Check if clinical workflows routes were found
    if ($result -match "Clinical workflow routes: 0") {
        Write-Host "`nPROBLEM IDENTIFIED:" -ForegroundColor Red
        Write-Host "  Clinical workflows router is not registered in FastAPI app" -ForegroundColor Red
        Write-Host "  Even though the router can be imported successfully" -ForegroundColor Red
        
        Write-Host "`nPOSSIBLE SOLUTIONS:" -ForegroundColor Yellow
        Write-Host "  1. Check for import errors during app startup" -ForegroundColor Gray
        Write-Host "  2. Verify router is properly included in main.py" -ForegroundColor Gray
        Write-Host "  3. Check for dependency issues preventing registration" -ForegroundColor Gray
    }
    elseif ($result -match "Clinical workflow routes: [1-9]") {
        Write-Host "`nSUCCESS:" -ForegroundColor Green
        Write-Host "  Clinical workflows routes are properly registered!" -ForegroundColor Green
        Write-Host "  The 404 issue must be something else" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "`nERROR running route check:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host "`nNEXT STEPS:" -ForegroundColor Cyan
Write-Host "Based on the results above:" -ForegroundColor White
Write-Host "• If routes found: Check server configuration or URL paths" -ForegroundColor Gray
Write-Host "• If no routes: Fix router registration in FastAPI" -ForegroundColor Gray
Write-Host "• If error: Check Docker container and Python environment" -ForegroundColor Gray