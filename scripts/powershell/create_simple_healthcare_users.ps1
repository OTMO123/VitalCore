# Simple Healthcare User Creation Script
Write-Host "Creating Healthcare Users for Role-Based Security Testing" -ForegroundColor Cyan

$baseUrl = "http://localhost:8000"

# Healthcare users to create with simplified passwords
$users = @(
    @{ username = "patient"; email = "patient@test.com"; password = "Patient123"; role = "patient" },
    @{ username = "doctor"; email = "doctor@test.com"; password = "Doctor123"; role = "doctor" },
    @{ username = "lab_tech"; email = "lab_tech@test.com"; password = "LabTech123"; role = "lab_technician" }
)

Write-Host "Testing backend connectivity..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
    Write-Host "Backend is healthy: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "Backend is not available at $baseUrl" -ForegroundColor Red
    exit 1
}

# Get admin token
Write-Host "`nAuthenticating as admin..." -ForegroundColor Yellow
try {
    $loginData = @{
        username = "admin"
        password = "admin123"
    } | ConvertTo-Json

    $authResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $loginData
    $adminToken = $authResponse.access_token
    Write-Host "Admin authentication successful" -ForegroundColor Green
} catch {
    Write-Host "Admin authentication failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $adminToken"
    "Content-Type" = "application/json"
}

# Check existing users
Write-Host "`nChecking existing users..." -ForegroundColor Yellow
try {
    $existingUsers = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/users" -Method GET -Headers $headers
    $existingUsernames = $existingUsers | ForEach-Object { $_.username }
    Write-Host "Existing users: $($existingUsernames -join ', ')" -ForegroundColor Gray
} catch {
    Write-Host "Could not fetch existing users: $($_.Exception.Message)" -ForegroundColor Yellow
    $existingUsernames = @()
}

# Create healthcare users
Write-Host "`nCreating healthcare users..." -ForegroundColor Yellow
$created = 0

foreach ($user in $users) {
    if ($existingUsernames -contains $user.username) {
        Write-Host "User '$($user.username)' already exists, skipping..." -ForegroundColor Yellow
        continue
    }

    Write-Host "Creating user: $($user.username) ($($user.role))" -ForegroundColor Cyan
    
    $userJson = @{
        username = $user.username
        email = $user.email
        password = $user.password
        role = $user.role
    } | ConvertTo-Json

    try {
        $createResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/register" -Method POST -ContentType "application/json" -Body $userJson
        Write-Host "  Successfully created: $($user.username)" -ForegroundColor Green
        $created++
    } catch {
        Write-Host "  Failed to create $($user.username): $($_.Exception.Message)" -ForegroundColor Red
        
        # Try to get more details from the error
        if ($_.Exception.Response) {
            try {
                $errorStream = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($errorStream)
                $errorContent = $reader.ReadToEnd()
                $errorDetails = $errorContent | ConvertFrom-Json
                Write-Host "    Error details: $($errorDetails.detail)" -ForegroundColor Red
            } catch {
                Write-Host "    Could not parse error details" -ForegroundColor Red
            }
        }
    }
}

# Verify created users can login
Write-Host "`nVerifying user logins..." -ForegroundColor Yellow
foreach ($user in $users) {
    $testLogin = @{
        username = $user.username
        password = $user.password
    } | ConvertTo-Json

    try {
        $testResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $testLogin
        Write-Host "  $($user.username) login successful" -ForegroundColor Green
    } catch {
        Write-Host "  $($user.username) login failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`nCreated $created new healthcare users" -ForegroundColor Cyan
Write-Host "Healthcare user creation completed!" -ForegroundColor Green