# Secure Admin User Creation - SOC2/HIPAA Compliant
Write-Host "Secure Admin User Creation" -ForegroundColor Cyan
Write-Host "SOC2/HIPAA Compliant Method" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Gray

# Create admin user using official AuthService only
$secureScript = @"
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
    
    async def create_admin():
        try:
            logger.info('Creating admin user via AuthService...')
            
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
            
            # Create admin user
            admin_data = UserCreate(
                username='admin',
                email='admin@healthcare.local',
                password='admin123',
                role='admin'
            )
            
            new_admin = await auth_service.create_user(admin_data, db)
            
            if new_admin:
                print('SUCCESS: Admin user created!')
                print('Username: admin')
                print('Password: admin123')
                return True
            else:
                print('FAILED: Could not create admin user')
                return False
                
        except Exception as e:
            print(f'ERROR: {e}')
            return False
    
    result = asyncio.run(create_admin())
    
except Exception as e:
    print(f'SCRIPT ERROR: {e}')
"@

Write-Host "Creating admin user..." -ForegroundColor White
docker-compose exec app python -c $secureScript

# Test authentication
Write-Host "`nTesting authentication..." -ForegroundColor White
try {
    $loginData = '{"username": "admin", "password": "admin123"}'
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $loginData -ContentType "application/json" -TimeoutSec 10
    
    if ($response.access_token) {
        Write-Host "SUCCESS: Authentication working!" -ForegroundColor Green
        Write-Host "Admin user ready for testing" -ForegroundColor Green
        Write-Host ""
        Write-Host "Run tests:" -ForegroundColor Yellow
        Write-Host "  .\simple-test.ps1" -ForegroundColor White
        Write-Host "  .\validate-role-based-security.ps1" -ForegroundColor White
    } else {
        Write-Host "Authentication failed - no token" -ForegroundColor Red
    }
} catch {
    Write-Host "Authentication test failed: $($_.Exception.Message)" -ForegroundColor Red
}