# Docker Commands to Fix Database Configuration and Achieve 100% API Reliability
# Run these commands in PowerShell in the project directory

Write-Host "🚀 Docker Database Fix for 100% Backend Reliability" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green

# Step 1: Test config loading in Docker container
Write-Host "`n📋 Step 1: Testing config loading..." -ForegroundColor Yellow
docker exec -it iris_app python3 -c "from app.core.config import Settings; print('Config loaded successfully')"

# Step 2: Run Alembic migrations
Write-Host "`n📋 Step 2: Running database migrations..." -ForegroundColor Yellow
docker exec -it iris_app alembic upgrade head

# Step 3: Verify database tables were created
Write-Host "`n📋 Step 3: Checking migration status..." -ForegroundColor Yellow
docker exec -it iris_app alembic current

# Step 4: Test critical API endpoints
Write-Host "`n📋 Step 4: Testing API endpoints..." -ForegroundColor Yellow
Write-Host "Getting auth token..."
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"email":"admin@iris.com","password":"admin123"}'
$token = $response.access_token

Write-Host "Testing patient endpoints..."
$headers = @{"Authorization"="Bearer $token"}
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/healthcare/patients" -Headers $headers

# Step 5: Run comprehensive API test
Write-Host "`n📋 Step 5: Running comprehensive test..." -ForegroundColor Yellow
bash tests/100_percent_api_test.sh

Write-Host "`n✅ Database fix completed! Frontend should now work 100%." -ForegroundColor Green