# Fix Admin Authentication Issues
Write-Host "Fixing Admin Authentication" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Gray

# Step 1: Check current users in database
Write-Host "`nStep 1: Checking current users..." -ForegroundColor White

$checkUsersScript = @"
import sys
sys.path.insert(0, '.')
import asyncio
from app.core.database_unified import get_db
from sqlalchemy import text

async def check_users():
    try:
        db_gen = get_db()
        db = await db_gen.__anext__()
        
        result = await db.execute(text('SELECT username, email, role, is_active FROM users'))
        users = result.fetchall()
        
        print(f'Found {len(users)} users:')
        for user in users:
            print(f'  {user[0]} ({user[1]}) - Role: {user[2]}, Active: {user[3]}')
            
        return len(users)
    except Exception as e:
        print(f'Error checking users: {e}')
        return 0

asyncio.run(check_users())
"@

docker-compose exec app python -c $checkUsersScript

# Step 2: Delete existing admin user if it exists
Write-Host "`nStep 2: Cleaning up existing admin user..." -ForegroundColor White

$cleanupScript = @"
import sys
sys.path.insert(0, '.')
import asyncio
from app.core.database_unified import get_db
from sqlalchemy import text

async def cleanup_admin():
    try:
        db_gen = get_db()
        db = await db_gen.__anext__()
        
        # Delete existing admin user
        result = await db.execute(text('DELETE FROM users WHERE username = :username'), {'username': 'admin'})
        await db.commit()
        
        print(f'Deleted {result.rowcount} admin users')
        return True
    except Exception as e:
        print(f'Cleanup error: {e}')
        return False

asyncio.run(cleanup_admin())
"@

docker-compose exec app python -c $cleanupScript

# Step 3: Create fresh admin user with correct password
Write-Host "`nStep 3: Creating fresh admin user..." -ForegroundColor White

$createAdminScript = @"
import sys
sys.path.insert(0, '.')
import asyncio
from app.core.database_unified import get_db
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import UserCreate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('admin_creation')

async def create_admin():
    try:
        db_gen = get_db()
        db = await db_gen.__anext__()
        
        auth_service = AuthService()
        
        # Create admin with exact password
        admin_data = UserCreate(
            username='admin',
            email='admin@healthcare.com',
            password='Admin123!',
            role='admin'
        )
        
        logger.info('Creating admin user...')
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
        print(f'Creation error: {e}')
        import traceback
        traceback.print_exc()
        return False

asyncio.run(create_admin())
"@

docker-compose exec app python -c $createAdminScript

# Step 4: Test authentication
Write-Host "`nStep 4: Testing authentication..." -ForegroundColor White

try {
    $loginData = @{
        username = "admin"
        password = "Admin123!"
    } | ConvertTo-Json
    
    Write-Host "Attempting login with: admin / Admin123!" -ForegroundColor Yellow
    
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $loginData -ContentType "application/json" -TimeoutSec 10
    
    if ($response.access_token) {
        Write-Host "SUCCESS! Authentication working!" -ForegroundColor Green
        Write-Host "Access token: $($response.access_token.Substring(0,50))..." -ForegroundColor Gray
        
        # Test protected endpoint
        $headers = @{ "Authorization" = "Bearer $($response.access_token)" }
        $userInfo = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/me" -Headers $headers -TimeoutSec 10
        
        Write-Host "User verified: $($userInfo.username) (Role: $($userInfo.role))" -ForegroundColor Green
        
        Write-Host "`nREADY FOR VALIDATION TESTS!" -ForegroundColor Green
        Write-Host "============================" -ForegroundColor Gray
        Write-Host "Credentials: admin / Admin123!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Run validation scripts:" -ForegroundColor White
        Write-Host "  .\simple-test.ps1" -ForegroundColor Green
        Write-Host "  .\validate-role-based-security.ps1" -ForegroundColor Green
        Write-Host "  .\validate_core_security_fixes.ps1" -ForegroundColor Green
        
    } else {
        Write-Host "FAILED: No access token received" -ForegroundColor Red
    }
    
} catch {
    Write-Host "FAILED: Authentication test failed" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    Write-Host "`nDEBUG: Checking login endpoint directly..." -ForegroundColor Yellow
    
    try {
        $debugResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $loginData -ContentType "application/json" -TimeoutSec 10
        Write-Host "Response status: $($debugResponse.StatusCode)" -ForegroundColor Yellow
        Write-Host "Response content: $($debugResponse.Content)" -ForegroundColor Yellow
    } catch {
        Write-Host "Debug request failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`nAdmin authentication fix complete!" -ForegroundColor Cyan