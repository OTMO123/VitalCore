#!/bin/bash

echo "Testing 404 error handling..."

# Get fresh token
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@example.com","password":"admin123"}' \
  -s | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "Got token: ${TOKEN:0:50}..."

# Test the main Get Patient endpoint
echo "Testing main Get Patient endpoint..."
response=$(curl -X GET "http://localhost:8000/api/v1/healthcare/patients/00000000-0000-0000-0000-000000000000" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -w "Status: %{http_code}\n" \
  -s)

echo "Response: $response"

# Test debug endpoint for comparison
echo "Testing debug endpoint..."
debug_response=$(curl -X GET "http://localhost:8000/api/v1/healthcare/debug-get-patient/00000000-0000-0000-0000-000000000000" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -s)

echo "Debug response: $debug_response"