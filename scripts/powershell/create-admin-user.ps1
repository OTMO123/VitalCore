# Create Admin User for Healthcare API
Write-Host "Creating Admin User" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Gray

# Method 1: Try to create admin user directly
Write-Host "Method 1: Creating admin user via API..." -ForegroundColor White

$createUserScript = @"
import sys
import os
sys.path.insert(0, '.')

# Set environment variables that might be needed
os.environ.setdefault('PYTHONPATH', '.')

try:
    import asyncio
    from app.core.database_unified import get_db
    from app.modules.auth.service import AuthService
    from app.modules.auth.schemas import UserCreate
    from sqlalchemy.ext.asyncio import AsyncSession
    import logging
    
    # Set up logging to see what's happening
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    async def create_admin_user():
        try:
            logger.info('Getting database session...')
            
            # Get database session
            db_gen = get_db()
            db = await db_gen.__anext__()
            
            logger.info('Creating auth service...')
            auth_service = AuthService()
            
            # Check if admin already exists
            logger.info('Checking if admin user exists...')
            existing_admin = await auth_service.get_user_by_username('admin', db)
            
            if existing_admin:
                logger.info('Admin user already exists!')
                print('SUCCESS: Admin user already exists')
                print('Username: admin')
                print('Use password: admin123 (if you set it before)')
                return True
            
            logger.info('Creating new admin user...')
            
            # Create admin user data
            admin_data = UserCreate(
                username='admin',
                email='admin@healthcare.local',
                password='admin123',
                role='admin'
            )
            
            logger.info('Calling create_user...')
            new_admin = await auth_service.create_user(admin_data, db)
            
            if new_admin:
                logger.info('Admin user created successfully!')
                print('SUCCESS: Admin user created!')
                print('Username: admin')
                print('Password: admin123')
                print('Email: admin@healthcare.local')
                print('Role: admin')
                return True
            else:
                logger.error('Failed to create admin user - no user returned')
                print('FAILED: create_user returned None')
                return False
                
        except Exception as e:
            logger.error(f'Error creating admin user: {e}')
            print(f'ERROR: {e}')
            import traceback
            traceback.print_exc()
            return False
    
    # Run the creation
    print('Starting admin user creation...')
    result = asyncio.run(create_admin_user())
    print(f'Final result: {result}')
    
except Exception as e:
    print(f'SCRIPT ERROR: {e}')
    import traceback
    traceback.print_exc()
"@

try {
    Write-Host "Running user creation script..." -ForegroundColor Yellow
    docker-compose exec app python -c $createUserScript
    
    # Test if admin login works now
    Write-Host "`nTesting admin login..." -ForegroundColor White
    
    $loginData = '{"username": "admin", "password": "admin123"}'
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $loginData -ContentType "application/json" -TimeoutSec 10
    
    if ($response.access_token) {
        Write-Host "SUCCESS! Admin login working!" -ForegroundColor Green
        Write-Host "Access token received: $($response.access_token.Substring(0,50))..." -ForegroundColor Gray
        
        # Test authenticated endpoint
        $headers = @{ "Authorization" = "Bearer $($response.access_token)" }
        $userInfo = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/me" -Headers $headers -TimeoutSec 10
        
        Write-Host "User info retrieved: $($userInfo.username) ($($userInfo.role))" -ForegroundColor Green
        
        Write-Host "`nREADY FOR TESTING!" -ForegroundColor Green
        Write-Host "Login credentials: admin / admin123" -ForegroundColor Yellow
        
    } else {
        Write-Host "Login test failed - no token received" -ForegroundColor Red
    }
    
} catch {
    Write-Host "Method 1 failed: $($_.Exception.Message)" -ForegroundColor Red
    
    # Method 2: Try direct database insertion
    Write-Host "`nMethod 2: Direct database user creation..." -ForegroundColor White
    
    $directDbScript = @"
import sys
sys.path.insert(0, '.')

try:
    import asyncio
    import uuid
    from datetime import datetime
    from app.core.database_unified import get_db, User
    from app.core.security import pwd_context
    from sqlalchemy import text
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    async def create_user_direct():
        try:
            logger.info('Getting database session...')
            db_gen = get_db()
            db = await db_gen.__anext__()
            
            # Check if user exists
            result = await db.execute(text('SELECT username FROM users WHERE username = :username'), {'username': 'admin'})
            existing = result.fetchone()
            
            if existing:
                logger.info('Admin user already exists in database')
                print('SUCCESS: Admin user exists in database')
                return True
            
            # Hash password
            password_hash = pwd_context.hash('admin123')
            
            # Insert user directly
            insert_sql = text('''
                INSERT INTO users (id, username, email, password_hash, role, is_active, email_verified, created_at)
                VALUES (:id, :username, :email, :password_hash, :role, :is_active, :email_verified, :created_at)
            ''')
            
            user_id = str(uuid.uuid4())
            await db.execute(insert_sql, {
                'id': user_id,
                'username': 'admin',
                'email': 'admin@healthcare.local',
                'password_hash': password_hash,
                'role': 'admin',
                'is_active': True,
                'email_verified': True,
                'created_at': datetime.utcnow()
            })
            
            await db.commit()
            
            logger.info('User inserted directly into database')
            print('SUCCESS: Admin user created directly in database')
            print('Username: admin')
            print('Password: admin123')
            return True
            
        except Exception as e:
            logger.error(f'Direct database creation failed: {e}')
            print(f'FAILED: {e}')
            return False
    
    result = asyncio.run(create_user_direct())
    print(f'Direct creation result: {result}')
    
except Exception as e:
    print(f'Method 2 failed: {e}')
"@
    
    try {
        docker-compose exec app python -c $directDbScript
        
        # Test login again
        Write-Host "`nTesting login after direct creation..." -ForegroundColor White
        $loginData2 = '{"username": "admin", "password": "admin123"}'
        $response2 = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $loginData2 -ContentType "application/json" -TimeoutSec 10
        
        if ($response2.access_token) {
            Write-Host "SUCCESS! Direct database creation worked!" -ForegroundColor Green
        } else {
            Write-Host "Still no success after direct creation" -ForegroundColor Red
        }
        
    } catch {
        Write-Host "Method 2 also failed: $($_.Exception.Message)" -ForegroundColor Red
        
        # Method 3: Check what's in the database
        Write-Host "`nMethod 3: Checking current database state..." -ForegroundColor White
        
        $checkDbScript = @"
import sys
sys.path.insert(0, '.')
import asyncio
from app.core.database_unified import get_db
from sqlalchemy import text

async def check_database():
    try:
        db_gen = get_db()
        db = await db_gen.__anext__()
        
        # Check if users table exists
        result = await db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_name = 'users'"))
        table_exists = result.fetchone()
        
        if table_exists:
            print('✅ Users table exists')
            
            # Check users in table
            result = await db.execute(text('SELECT username, email, role FROM users LIMIT 10'))
            users = result.fetchall()
            
            print(f'Found {len(users)} users in database:')
            for user in users:
                print(f'  - {user[0]} ({user[1]}) - Role: {user[2]}')
                
        else:
            print('❌ Users table does not exist')
            
            # Show all tables
            result = await db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = result.fetchall()
            print('Available tables:')
            for table in tables:
                print(f'  - {table[0]}')
                
    except Exception as e:
        print(f'Database check failed: {e}')

asyncio.run(check_database())
"@
        
        docker-compose exec app python -c $checkDbScript
    }
}

Write-Host "`nFinal status check:" -ForegroundColor White
Write-Host "Try running: .\simple-test.ps1" -ForegroundColor Yellow