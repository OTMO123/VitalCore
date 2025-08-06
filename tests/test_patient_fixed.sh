#!/bin/bash
# Test patient creation with fixed schema
BASE_URL="http://localhost:8000"

# Get auth token
echo "🔐 Getting auth token..."
AUTH_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin&password=admin123" \
    "$BASE_URL/api/v1/auth/login")

TOKEN=$(echo "$AUTH_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Authentication failed"
    exit 1
fi

echo "✅ Authentication successful"

# Test with complete, valid patient data
PATIENT_DATA='{
    "resourceType": "Patient",
    "identifier": [{
        "use": "official",
        "type": {
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}]
        },
        "system": "http://hospital.smarthit.org",
        "value": "TEST-SCHEMA-001"
    }],
    "name": [{
        "use": "official",
        "family": "SchemaTest",
        "given": ["Fixed", "API"]
    }],
    "gender": "male",
    "birthDate": "1990-01-01",
    "active": true,
    "organization_id": "550e8400-e29b-41d4-a716-446655440000",
    "consent_status": "pending",
    "consent_types": ["treatment"]
}'

echo "🧪 Testing patient creation with complete schema..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "$PATIENT_DATA" \
    "$BASE_URL/api/v1/healthcare/patients")

STATUS_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n -1)

echo "Response Status: $STATUS_CODE"
echo "Response Body: $BODY"

if [ "$STATUS_CODE" = "201" ]; then
    echo "✅ Patient creation SUCCESS!"
    exit 0
elif [ "$STATUS_CODE" = "422" ]; then
    echo "❌ Schema validation still failing"
    echo "Details: $BODY"
    exit 1
elif [ "$STATUS_CODE" = "500" ]; then
    echo "❌ Internal server error - backend needs restart"
    exit 2
else
    echo "⚠️  Unexpected status: $STATUS_CODE"
    exit 1
fi