# Create Healthcare Role Users for Security Testing
Write-Host "=== CREATING HEALTHCARE ROLE USERS ===" -ForegroundColor Cyan

$baseUrl = "http://localhost:8003"

# Healthcare users to create
$healthcareUsers = @(
    @{
        username = "patient"
        email = "patient@test.com"
        password = "TestPassword123!"
        role = "patient"
        description = "Test patient user for role-based security testing"
    },
    @{
        username = "doctor" 
        email = "doctor@test.com"
        password = "TestPassword123!"
        role = "doctor"
        description = "Test doctor user for role-based security testing"
    },
    @{
        username = "lab_tech"
        email = "lab_tech@test.com" 
        password = "TestPassword123!"
        role = "lab_technician"
        description = "Test lab technician user for role-based security testing"
    }
)

try {
    Write-Host "Checking existing users..." -ForegroundColor Yellow
    
    # First, try to login with admin to get an auth token
    Write-Host "1. Getting admin authentication token..." -ForegroundColor Yellow
    $loginHeaders = @{
        'Content-Type' = 'application/json'
    }
    $loginBody = @{
        username = "admin"
        password = "admin123"
    } | ConvertTo-Json

    $loginResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    $adminToken = $loginResponse.access_token
    Write-Host "✅ Admin token obtained" -ForegroundColor Green
    
    $authHeaders = @{
        'Authorization' = "Bearer $adminToken"
        'Content-Type' = 'application/json'
    }
    
    # Get list of existing users
    Write-Host "`n2. Checking existing users..." -ForegroundColor Yellow
    try {
        $existingUsers = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/users" -Method GET -Headers $authHeaders
        $existingUsernames = $existingUsers | ForEach-Object { $_.username }
        Write-Host "Found $($existingUsers.Count) existing users: $($existingUsernames -join ', ')" -ForegroundColor Gray
    } catch {
        Write-Host "Could not fetch existing users list (continuing anyway): $($_.Exception.Message)" -ForegroundColor Yellow
        $existingUsernames = @()
    }
    
    # Create each healthcare user
    Write-Host "`n3. Creating healthcare users..." -ForegroundColor Yellow
    $createdCount = 0
    
    foreach ($user in $healthcareUsers) {
        Write-Host "`nCreating user: $($user.username) ($($user.role))" -ForegroundColor Cyan
        
        # Check if user already exists
        if ($existingUsernames -contains $user.username) {
            Write-Host "  ❓ User '$($user.username)' already exists, skipping..." -ForegroundColor Yellow
            continue
        }
        
        # Create user via registration endpoint
        $userBody = @{
            username = $user.username
            email = $user.email 
            password = $user.password
            role = $user.role
        } | ConvertTo-Json
        
        try {
            $createResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/register" -Method POST -Headers $loginHeaders -Body $userBody
            Write-Host "  ✅ Successfully created user: $($user.username)" -ForegroundColor Green
            Write-Host "     Email: $($user.email)" -ForegroundColor Gray
            Write-Host "     Role: $($user.role)" -ForegroundColor Gray
            Write-Host "     Password: $($user.password)" -ForegroundColor Gray
            $createdCount++
        } catch {
            $errorMessage = $_.Exception.Message
            if ($_.Exception.Response) {
                try {
                    $errorContent = $_.Exception.Response.GetResponseStream()
                    $reader = New-Object System.IO.StreamReader($errorContent)
                    $errorBody = $reader.ReadToEnd() | ConvertFrom-Json
                    $errorMessage = $errorBody.detail
                } catch {
                    # Fallback to original error message
                }
            }
            Write-Host "  ❌ Failed to create user '$($user.username)': $errorMessage" -ForegroundColor Red
        }
    }
    
    Write-Host "`n=== SUMMARY ===" -ForegroundColor Cyan
    Write-Host "Successfully created $createdCount new healthcare users" -ForegroundColor Green
    
    if ($createdCount -gt 0) {
        Write-Host "`nYou can now test with these credentials:" -ForegroundColor Yellow
        foreach ($user in $healthcareUsers) {
            Write-Host "  $($user.role): $($user.username) / $($user.password)" -ForegroundColor Gray
        }
    }
    
    # Verify the healthcare users can login
    Write-Host "`n4. Verifying healthcare user logins..." -ForegroundColor Yellow
    foreach ($user in $healthcareUsers) {
        try {
            $testLoginBody = @{
                username = $user.username
                password = $user.password
            } | ConvertTo-Json
            
            $testLoginResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $testLoginBody
            Write-Host "  ✅ $($user.username) ($($user.role)) login verification successful" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ $($user.username) ($($user.role)) login verification failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
} catch {
    Write-Host "❌ Error in main process: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Stack trace:" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Healthcare user creation process completed!" -ForegroundColor Green