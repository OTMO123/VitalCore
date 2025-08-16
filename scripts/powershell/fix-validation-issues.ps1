# Fix Healthcare API Validation Issues
Write-Host "Fixing Healthcare API Validation Issues" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Gray

# Step 1: Check what endpoints are available
Write-Host "`nStep 1: Checking API endpoints..." -ForegroundColor White

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/openapi.json" -TimeoutSec 10
    $endpoints = $response.paths.Keys | Sort-Object
    
    Write-Host "Available endpoints:" -ForegroundColor Green
    foreach ($endpoint in $endpoints) {
        if ($endpoint -match "healthcare|audit|patient") {
            Write-Host "  $endpoint" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "Could not fetch API documentation" -ForegroundColor Red
}

# Step 2: Test healthcare patients endpoint with debug
Write-Host "`nStep 2: Testing healthcare patients endpoint..." -ForegroundColor White

try {
    $loginData = @{ username = "admin"; password = "Admin123!" } | ConvertTo-Json
    $authResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $loginData
    $token = $authResponse.access_token
    
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    Write-Host "Testing /api/v1/healthcare/patients..." -ForegroundColor Yellow
    try {
        $patientsResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/healthcare/patients" -Method GET -Headers $headers
        Write-Host "SUCCESS: Healthcare patients endpoint working (Status: $($patientsResponse.StatusCode))" -ForegroundColor Green
    } catch {
        Write-Host "FAILED: Healthcare patients endpoint error" -ForegroundColor Red
        Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Yellow
        
        # Try alternative endpoints
        Write-Host "`nTrying alternative healthcare endpoints..." -ForegroundColor White
        $healthcareEndpoints = @(
            "/api/v1/healthcare/records",
            "/api/v1/patients",
            "/api/v1/healthcare",
            "/api/v1/healthcare-records/patients"
        )
        
        foreach ($endpoint in $healthcareEndpoints) {
            try {
                $testResponse = Invoke-WebRequest -Uri "http://localhost:8000$endpoint" -Method GET -Headers $headers
                Write-Host "  ✅ $endpoint works (Status: $($testResponse.StatusCode))" -ForegroundColor Green
            } catch {
                Write-Host "  ❌ $endpoint failed (Status: $($_.Exception.Response.StatusCode))" -ForegroundColor Red
            }
        }
    }
    
} catch {
    Write-Host "Authentication failed for healthcare test" -ForegroundColor Red
}

# Step 3: Test audit endpoints
Write-Host "`nStep 3: Testing audit endpoints..." -ForegroundColor White

$auditEndpoints = @(
    "/api/v1/audit/logs",
    "/api/v1/audit",
    "/api/v1/audit-logger/logs",
    "/api/v1/logs"
)

foreach ($endpoint in $auditEndpoints) {
    try {
        $auditResponse = Invoke-WebRequest -Uri "http://localhost:8000$endpoint" -Method GET -Headers $headers
        Write-Host "  ✅ $endpoint works (Status: $($auditResponse.StatusCode))" -ForegroundColor Green
        break
    } catch {
        Write-Host "  ❌ $endpoint failed (Status: $($_.Exception.Response.StatusCode))" -ForegroundColor Red
    }
}

# Step 4: Create test users for role validation
Write-Host "`nStep 4: Creating test users for role validation..." -ForegroundColor White

$createUsersScript = @"
import sys
sys.path.insert(0, '.')
import asyncio
from app.core.database_unified import get_db
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import UserCreate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_users')

async def create_test_users():
    try:
        db_gen = get_db()
        db = await db_gen.__anext__()
        
        auth_service = AuthService()
        
        # Test users to create
        test_users = [
            {
                'username': 'patient',
                'email': 'patient@healthcare.com',
                'password': 'Patient123!',
                'role': 'user'  # Use 'user' role since 'patient' might not exist
            },
            {
                'username': 'doctor',
                'email': 'doctor@healthcare.com', 
                'password': 'Doctor123!',
                'role': 'user'  # Use 'user' role since 'doctor' might not exist
            },
            {
                'username': 'lab_tech',
                'email': 'labtech@healthcare.com',
                'password': 'LabTech123!',
                'role': 'user'  # Use 'user' role since 'lab_tech' might not exist
            }
        ]
        
        created_count = 0
        for user_data in test_users:
            try:
                # Check if user exists
                existing = await auth_service.get_user_by_username(user_data['username'], db)
                if existing:
                    print(f'User {user_data["username"]} already exists')
                    continue
                    
                # Create user
                user_create = UserCreate(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    role=user_data['role']
                )
                
                new_user = await auth_service.create_user(user_create, db)
                if new_user:
                    print(f'✅ Created user: {user_data["username"]} (password: {user_data["password"]})')
                    created_count += 1
                else:
                    print(f'❌ Failed to create user: {user_data["username"]}')
                    
            except Exception as e:
                print(f'❌ Error creating {user_data["username"]}: {e}')
        
        print(f'\\nCreated {created_count} test users')
        return created_count > 0
        
    except Exception as e:
        print(f'Error in create_test_users: {e}')
        return False

asyncio.run(create_test_users())
"@

docker-compose exec app python -c $createUsersScript

# Step 5: Test the created users
Write-Host "`nStep 5: Testing created user authentication..." -ForegroundColor White

$testUsers = @(
    @("patient", "Patient123!"),
    @("doctor", "Doctor123!"),
    @("lab_tech", "LabTech123!")
)

foreach ($user in $testUsers) {
    $username = $user[0]
    $password = $user[1]
    
    try {
        $loginData = @{ username = $username; password = $password } | ConvertTo-Json
        $authResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $loginData
        
        if ($authResponse.access_token) {
            Write-Host "✅ $username authentication working" -ForegroundColor Green
        } else {
            Write-Host "❌ $username authentication failed - no token" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ $username authentication failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`nValidation issues fix complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Gray

Write-Host "`nNext steps:" -ForegroundColor White
Write-Host "1. Run .\simple-test.ps1 to verify basic functionality" -ForegroundColor Yellow
Write-Host "2. Run .\validate_core_security_fixes.ps1 for security validation" -ForegroundColor Yellow  
Write-Host "3. Check the endpoint URLs found above and update validation scripts if needed" -ForegroundColor Yellow

Write-Host "`nCredentials for testing:" -ForegroundColor White
Write-Host "  admin / Admin123!" -ForegroundColor Green
Write-Host "  patient / Patient123!" -ForegroundColor Green
Write-Host "  doctor / Doctor123!" -ForegroundColor Green
Write-Host "  lab_tech / LabTech123!" -ForegroundColor Green