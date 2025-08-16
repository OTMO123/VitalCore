# Create Admin User - Fixed Validation Issues
Write-Host "Creating Admin User (Fixed)" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Gray

$fixedScript = @"
import sys
sys.path.insert(0, '.')

try:
    import asyncio
    from app.core.database_unified import get_db
    from app.modules.auth.service import AuthService
    from app.modules.auth.schemas import UserCreate
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('admin_creation')
    
    async def create_admin_fixed():
        try:
            logger.info('Creating admin user with fixed validation...')
            
            # Get database session
            db_gen = get_db()
            db = await db_gen.__anext__()
            
            # Use official AuthService
            auth_service = AuthService()
            
            # Check if admin exists
            existing = await auth_service.get_user_by_username('admin', db)
            if existing:
                print('SUCCESS: Admin user already exists')
                return True
            
            # Create admin user with FIXED validation
            admin_data = UserCreate(
                username='admin',
                email='admin@healthcare.com',  # Fixed: .com instead of .local
                password='Admin123!',          # Fixed: uppercase + special char
                role='admin'
            )
            
            logger.info('Attempting to create user with valid data...')
            new_admin = await auth_service.create_user(admin_data, db)
            
            if new_admin:
                print('SUCCESS: Admin user created!')
                print('Username: admin')
                print('Password: Admin123!')
                print('Email: admin@healthcare.com')
                print('Role: admin')
                return True
            else:
                print('FAILED: Could not create admin user')
                return False
                
        except Exception as e:
            print(f'ERROR: {e}')
            import traceback
            traceback.print_exc()
            return False
    
    result = asyncio.run(create_admin_fixed())
    
except Exception as e:
    print(f'SCRIPT ERROR: {e}')
"@

Write-Host "Creating admin user with fixed validation..." -ForegroundColor White
docker-compose exec app python -c $fixedScript

# Test authentication with new password
Write-Host "`nTesting authentication with new password..." -ForegroundColor White
try {
    $loginData = '{"username": "admin", "password": "Admin123!"}'
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $loginData -ContentType "application/json" -TimeoutSec 10
    
    if ($response.access_token) {
        Write-Host "SUCCESS! Authentication working!" -ForegroundColor Green
        Write-Host "Admin credentials: admin / Admin123!" -ForegroundColor Yellow
        
        # Test protected endpoint
        $headers = @{ "Authorization" = "Bearer $($response.access_token)" }
        $userInfo = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/me" -Headers $headers -TimeoutSec 10
        
        Write-Host "User verified: $($userInfo.username) (Role: $($userInfo.role))" -ForegroundColor Green
        
        Write-Host "`nREADY FOR ENTERPRISE TESTING!" -ForegroundColor Green
        Write-Host "=============================" -ForegroundColor Gray
        Write-Host "Login: admin / Admin123!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Run your validation scripts:" -ForegroundColor White
        Write-Host "  .\simple-test.ps1" -ForegroundColor Green
        Write-Host "  .\validate-role-based-security.ps1" -ForegroundColor Green
        Write-Host "  .\validate_core_security_fixes.ps1" -ForegroundColor Green
        
    } else {
        Write-Host "Authentication failed - no token received" -ForegroundColor Red
    }
} catch {
    Write-Host "Authentication test failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Check if user was created but password is different" -ForegroundColor Yellow
}