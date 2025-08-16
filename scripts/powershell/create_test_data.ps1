# Test Data Population Script for Healthcare AI Platform
# Creates users and patients via API calls

$ErrorActionPreference = "Stop"

# Configuration
$BaseUrl = "http://localhost:8000"
$ApiBase = "$BaseUrl/api/v1"

Write-Host "🚀 Healthcare AI Platform - Test Data Creation" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Blue

# Function to make API requests
function Invoke-ApiRequest {
    param(
        [string]$Method,
        [string]$Endpoint,
        [object]$Body = $null,
        [hashtable]$Headers = @{}
    )
    
    $uri = "$ApiBase$Endpoint"
    $params = @{
        Uri = $uri
        Method = $Method
        Headers = $Headers
        ContentType = "application/json"
    }
    
    if ($Body) {
        $params.Body = ($Body | ConvertTo-Json -Depth 10)
    }
    
    try {
        $response = Invoke-RestMethod @params
        return $response
    }
    catch {
        Write-Host "❌ API Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "URI: $uri" -ForegroundColor Yellow
        if ($_.Exception.Response) {
            $statusCode = $_.Exception.Response.StatusCode.value__
            Write-Host "Status Code: $statusCode" -ForegroundColor Yellow
        }
        throw
    }
}

# Test backend availability
Write-Host "`n🔍 Testing backend availability..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "$BaseUrl/health" -TimeoutSec 5
    Write-Host "✅ Backend is available" -ForegroundColor Green
}
catch {
    Write-Host "❌ Backend is not available at $BaseUrl" -ForegroundColor Red
    Write-Host "Please start the backend with: python app/main.py" -ForegroundColor Yellow
    exit 1
}

# Create test users
Write-Host "`n👥 Creating test users..." -ForegroundColor Yellow

$testUsers = @(
    @{
        username = "admin"
        email = "admin@healthcare.local"
        password = "admin123"
        role = "admin"
        full_name = "System Administrator"
    },
    @{
        username = "doctor1"
        email = "doctor1@healthcare.local"
        password = "doctor123"
        role = "doctor"
        full_name = "Dr. John Smith"
    },
    @{
        username = "nurse1"
        email = "nurse1@healthcare.local"
        password = "nurse123"
        role = "nurse"
        full_name = "Nurse Jane Wilson"
    },
    @{
        username = "operator1"
        email = "operator1@healthcare.local"
        password = "operator123"
        role = "operator"
        full_name = "Medical Operator Sarah Brown"
    }
)

$createdUsers = @()
foreach ($user in $testUsers) {
    try {
        Write-Host "Creating user: $($user.username) ($($user.role))" -ForegroundColor Cyan
        $response = Invoke-ApiRequest -Method "POST" -Endpoint "/auth/register" -Body $user
        $createdUsers += $user
        Write-Host "✅ User created successfully" -ForegroundColor Green
    }
    catch {
        if ($_.Exception.Message -like "*already*") {
            Write-Host "⚠️  User already exists, skipping" -ForegroundColor Yellow
            $createdUsers += $user
        }
        else {
            Write-Host "❌ Failed to create user: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# Login as admin to get token for creating patients
Write-Host "`n🔑 Logging in as admin..." -ForegroundColor Yellow
try {
    $loginData = @{
        username = "admin"
        password = "admin123"
    }
    
    # Convert to form data
    $formData = "username=$($loginData.username)&password=$($loginData.password)"
    
    $loginResponse = Invoke-RestMethod -Uri "$ApiBase/auth/login" -Method POST -Body $formData -ContentType "application/x-www-form-urlencoded"
    $token = $loginResponse.access_token
    
    $authHeaders = @{
        "Authorization" = "Bearer $token"
    }
    
    Write-Host "✅ Successfully logged in" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to login: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "⚠️  Will create patients without authentication" -ForegroundColor Yellow
    $authHeaders = @{}
}

# Create test patients
Write-Host "`n🏥 Creating test patients..." -ForegroundColor Yellow

$testPatients = @(
    @{
        identifier = @(@{ use = "official"; value = "P001-2024" })
        name = @(@{ family = "Johnson"; given = @("Alice", "Marie"); use = "official" })
        active = $true
        birthDate = "1985-06-15"
        gender = "female"
        address = @(@{
            use = "home"
            line = @("123 Main Street", "Apt 4B")
            city = "Springfield"
            state = "IL"
            postalCode = "62701"
            country = "US"
        })
        telecom = @(
            @{ system = "phone"; value = "+1-555-0101"; use = "mobile" },
            @{ system = "email"; value = "alice.johnson@email.com"; use = "home" }
        )
        organization_id = "org-001"
    },
    @{
        identifier = @(@{ use = "official"; value = "P002-2024" })
        name = @(@{ family = "Smith"; given = @("Robert", "James"); use = "official" })
        active = $true
        birthDate = "1978-11-22"
        gender = "male"
        address = @(@{
            use = "home"
            line = @("456 Oak Avenue")
            city = "Springfield"
            state = "IL"
            postalCode = "62702"
            country = "US"
        })
        telecom = @(
            @{ system = "phone"; value = "+1-555-0201"; use = "mobile" },
            @{ system = "email"; value = "robert.smith@email.com"; use = "home" }
        )
        organization_id = "org-001"
    },
    @{
        identifier = @(@{ use = "official"; value = "P003-2024" })
        name = @(@{ family = "Williams"; given = @("Emily", "Rose"); use = "official" })
        active = $true
        birthDate = "1992-03-08"
        gender = "female"
        address = @(@{
            use = "home"
            line = @("789 Pine Street")
            city = "Springfield"
            state = "IL"
            postalCode = "62703"
            country = "US"
        })
        telecom = @(
            @{ system = "phone"; value = "+1-555-0301"; use = "mobile" },
            @{ system = "email"; value = "emily.williams@email.com"; use = "home" }
        )
        organization_id = "org-001"
    },
    @{
        identifier = @(@{ use = "official"; value = "P004-2024" })
        name = @(@{ family = "Brown"; given = @("Michael", "Andrew"); use = "official" })
        active = $true
        birthDate = "1965-09-14"
        gender = "male"
        address = @(@{
            use = "home"
            line = @("321 Elm Drive")
            city = "Springfield"
            state = "IL"
            postalCode = "62704"
            country = "US"
        })
        telecom = @(
            @{ system = "phone"; value = "+1-555-0401"; use = "mobile" },
            @{ system = "email"; value = "michael.brown@email.com"; use = "home" }
        )
        organization_id = "org-001"
    },
    @{
        identifier = @(@{ use = "official"; value = "P005-2024" })
        name = @(@{ family = "Davis"; given = @("Sarah", "Elizabeth"); use = "official" })
        active = $true
        birthDate = "1990-12-03"
        gender = "female"
        address = @(@{
            use = "home"
            line = @("654 Maple Court")
            city = "Springfield"
            state = "IL"
            postalCode = "62705"
            country = "US"
        })
        telecom = @(
            @{ system = "phone"; value = "+1-555-0501"; use = "mobile" },
            @{ system = "email"; value = "sarah.davis@email.com"; use = "home" }
        )
        organization_id = "org-001"
    },
    @{
        identifier = @(@{ use = "official"; value = "P006-2024" })
        name = @(@{ family = "Wilson"; given = @("Thomas", "Edward"); use = "official" })
        active = $true
        birthDate = "1972-07-28"
        gender = "male"
        address = @(@{
            use = "home"
            line = @("987 Cedar Lane")
            city = "Springfield"
            state = "IL"
            postalCode = "62706"
            country = "US"
        })
        telecom = @(
            @{ system = "phone"; value = "+1-555-0601"; use = "mobile" },
            @{ system = "email"; value = "thomas.wilson@email.com"; use = "home" }
        )
        organization_id = "org-001"
    },
    @{
        identifier = @(@{ use = "official"; value = "P007-2024" })
        name = @(@{ family = "Garcia"; given = @("Maria", "Isabel"); use = "official" })
        active = $true
        birthDate = "1988-04-19"
        gender = "female"
        address = @(@{
            use = "home"
            line = @("147 Birch Road")
            city = "Springfield"
            state = "IL"
            postalCode = "62707"
            country = "US"
        })
        telecom = @(
            @{ system = "phone"; value = "+1-555-0701"; use = "mobile" },
            @{ system = "email"; value = "maria.garcia@email.com"; use = "home" }
        )
        organization_id = "org-001"
    },
    @{
        identifier = @(@{ use = "official"; value = "P008-2024" })
        name = @(@{ family = "Martinez"; given = @("Jose", "Luis"); use = "official" })
        active = $true
        birthDate = "1983-01-11"
        gender = "male"
        address = @(@{
            use = "home"
            line = @("258 Spruce Street")
            city = "Springfield"
            state = "IL"
            postalCode = "62708"
            country = "US"
        })
        telecom = @(
            @{ system = "phone"; value = "+1-555-0801"; use = "mobile" },
            @{ system = "email"; value = "jose.martinez@email.com"; use = "home" }
        )
        organization_id = "org-001"
    }
)

$createdPatients = @()
foreach ($patient in $testPatients) {
    try {
        $patientName = "$($patient.name[0].given[0]) $($patient.name[0].family)"
        Write-Host "Creating patient: $patientName (ID: $($patient.identifier[0].value))" -ForegroundColor Cyan
        
        $response = Invoke-ApiRequest -Method "POST" -Endpoint "/healthcare/patients" -Body $patient -Headers $authHeaders
        $createdPatients += $patient
        Write-Host "✅ Patient created successfully" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Failed to create patient: $($_.Exception.Message)" -ForegroundColor Red
        
        # If it's a 401 error, try without authentication
        if ($_.Exception.Response.StatusCode.value__ -eq 401) {
            Write-Host "⚠️  Trying without authentication..." -ForegroundColor Yellow
            try {
                $response = Invoke-ApiRequest -Method "POST" -Endpoint "/healthcare/patients" -Body $patient
                $createdPatients += $patient
                Write-Host "✅ Patient created successfully (no auth)" -ForegroundColor Green
            }
            catch {
                Write-Host "❌ Still failed: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
}

# Summary
Write-Host "`n" + "=" * 60 -ForegroundColor Blue
Write-Host "🎉 Test Data Creation Complete!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Blue

Write-Host "`n📊 Summary:" -ForegroundColor Yellow
Write-Host "• Users created: $($createdUsers.Count)" -ForegroundColor White
Write-Host "• Patients created: $($createdPatients.Count)" -ForegroundColor White

if ($createdUsers.Count -gt 0) {
    Write-Host "`n🔑 Login Credentials:" -ForegroundColor Yellow
    Write-Host "-" * 30 -ForegroundColor Gray
    foreach ($user in $createdUsers) {
        Write-Host "Username: $($user.username)" -ForegroundColor Cyan
        Write-Host "Password: $($user.password)" -ForegroundColor Cyan
        Write-Host "Role: $($user.role)" -ForegroundColor White
        Write-Host "-" * 20 -ForegroundColor Gray
    }
}

Write-Host "`n📝 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Navigate to http://localhost:3000/patients" -ForegroundColor White
Write-Host "2. Login with any of the created users" -ForegroundColor White
Write-Host "3. You should now see the test patients" -ForegroundColor White

Write-Host "`n🚀 Quick Login (Admin):" -ForegroundColor Green
Write-Host "Username: admin" -ForegroundColor Cyan
Write-Host "Password: admin123" -ForegroundColor Cyan

Write-Host "`nDone! 🎯" -ForegroundColor Green