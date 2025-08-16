# Test direct HTTP call within container
Write-Host "Testing direct HTTP call within container..." -ForegroundColor Yellow

# Test HTTP directly from inside container
docker exec -it iris_app bash -c "
# Get auth token
TOKEN=\$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin&password=admin123' | \
  python3 -c 'import sys, json; print(json.load(sys.stdin)[\"access_token\"])')

echo 'Auth token obtained'

# Test patient endpoint
echo 'Testing patients endpoint...'
curl -s -X GET http://localhost:8000/api/v1/healthcare/patients \
  -H \"Authorization: Bearer \$TOKEN\" \
  -H 'Content-Type: application/json' \
  -w '\nHTTP Status: %{http_code}\n'
"

Write-Host "Direct HTTP test completed" -ForegroundColor Green