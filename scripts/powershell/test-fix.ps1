# Test the Event Bus Fix
Write-Host "Testing Event Bus Fix" -ForegroundColor Cyan

# Restart the app container
Write-Host "Restarting app container..." -ForegroundColor Yellow
docker-compose restart app

# Wait for startup
Write-Host "Waiting for app to start..." -ForegroundColor White
Start-Sleep 15

# Test health endpoint
Write-Host "Testing health endpoint..." -ForegroundColor White
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 10
    if ($response.status -eq "ok") {
        Write-Host "SUCCESS! API is healthy!" -ForegroundColor Green
        
        # Test authentication
        Write-Host "Testing authentication..." -ForegroundColor White
        try {
            $loginData = '{"username": "admin", "password": "admin123"}'
            $authResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $loginData -ContentType "application/json" -TimeoutSec 10
            
            if ($authResponse.access_token) {
                Write-Host "Authentication working!" -ForegroundColor Green
                Write-Host "Ready for testing!" -ForegroundColor Green
            } else {
                Write-Host "Authentication failed - creating admin user..." -ForegroundColor Yellow
                
                # Create admin user
                $pythonScript = "import sys; sys.path.insert(0, '.'); "
                $pythonScript += "import asyncio; "
                $pythonScript += "from app.core.database_unified import get_db; "
                $pythonScript += "from app.modules.auth.service import AuthService; "
                $pythonScript += "from app.modules.auth.schemas import UserCreate; "
                $pythonScript += "async def create_admin(): "
                $pythonScript += "    db_gen = get_db(); db = await db_gen.__anext__(); "
                $pythonScript += "    auth_service = AuthService(); "
                $pythonScript += "    admin_data = UserCreate(username='admin', email='admin@test.com', password='admin123', role='admin'); "
                $pythonScript += "    user = await auth_service.create_user(admin_data, db); "
                $pythonScript += "    print('Admin created!' if user else 'Failed!'); "
                $pythonScript += "asyncio.run(create_admin())"
                
                docker-compose exec app python -c $pythonScript
                
                # Test again
                $authResponse2 = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $loginData -ContentType "application/json" -TimeoutSec 10
                if ($authResponse2.access_token) {
                    Write-Host "Authentication now working!" -ForegroundColor Green
                }
            }
        } catch {
            Write-Host "Authentication test failed: $($_.Exception.Message)" -ForegroundColor Red
        }
        
    } else {
        Write-Host "Health check failed" -ForegroundColor Red
    }
} catch {
    Write-Host "API not responding. Checking logs..." -ForegroundColor Red
    docker-compose logs --tail=10 app
}

Write-Host "`nCurrent container status:" -ForegroundColor White
docker-compose ps