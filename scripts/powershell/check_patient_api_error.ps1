# Check detailed error in patient API
Write-Host "Getting detailed error from patient API..." -ForegroundColor Yellow

# Get auth token
$loginBody = "username=admin&password=admin123"
$loginHeaders = @{"Content-Type" = "application/x-www-form-urlencoded"}
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
$token = $response.access_token

$authHeaders = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Check what's in the database currently
Write-Host "Checking current patients in database:" -ForegroundColor Cyan
docker exec -it iris_postgres psql -U postgres -d iris_db -c "SELECT id, external_id, mrn, data_classification, created_at FROM patients LIMIT 5;"

Write-Host "`nChecking dataclassification enum values:" -ForegroundColor Cyan
docker exec -it iris_postgres psql -U postgres -d iris_db -c "SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'dataclassification');"

# Try to get more specific error by checking the actual API response
Write-Host "`nTrying patient API with verbose error handling:" -ForegroundColor Yellow
try {
    $patients = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/healthcare/patients" -Headers $authHeaders -UseBasicParsing
    Write-Host "Success: $($patients.Content)" -ForegroundColor Green
} catch {
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Host "Error Response: $($_.Exception.Response)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response Body: $responseBody" -ForegroundColor Red
    }
}

Write-Host "`nChecking recent app logs for specific error:" -ForegroundColor Yellow
docker logs iris_app --tail 20