#!/bin/bash
# Quick API Smoke Test - Быстрая проверка backend API
# Использует curl для тестирования критических эндпоинтов

BASE_URL="http://localhost:8000"
AUTH_TOKEN=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Logging function
log() {
    local status=$1
    local message=$2
    case $status in
        "PASS") echo -e "${GREEN}✅ $message${NC}" ;;
        "FAIL") echo -e "${RED}❌ $message${NC}" ;;
        "WARN") echo -e "${YELLOW}⚠️  $message${NC}" ;;
        "INFO") echo -e "${BLUE}ℹ️  $message${NC}" ;;
        *) echo -e "$message" ;;
    esac
}

# Test function
run_test() {
    local test_name=$1
    local curl_command=$2
    local expected_status=${3:-200}
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -e "\n${BLUE}Testing: $test_name${NC}"
    
    # Execute curl and capture status code
    response=$(eval "$curl_command" 2>/dev/null)
    status_code=$(echo "$response" | tail -n1)
    
    if [ "$status_code" = "$expected_status" ]; then
        log "PASS" "$test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        log "FAIL" "$test_name (Status: $status_code, Expected: $expected_status)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Authentication function
authenticate() {
    log "INFO" "Attempting authentication..."
    
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=admin&password=admin123" \
        "$BASE_URL/api/v1/auth/login")
    
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" = "200" ]; then
        AUTH_TOKEN=$(echo "$body" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        if [ -n "$AUTH_TOKEN" ]; then
            log "PASS" "Authentication successful"
            return 0
        else
            log "FAIL" "No access token received"
            return 1
        fi
    else
        log "FAIL" "Authentication failed (Status: $status_code)"
        return 1
    fi
}

# Main test suite
main() {
    echo "🚀 Quick API Smoke Test Suite"
    echo "=================================="
    echo ""
    
    # Test 1: System Health
    run_test "System Health Check" \
        "curl -s -w '\n%{http_code}' '$BASE_URL/health' | tail -n1" \
        "200"
    
    # Test 2: Authentication
    if authenticate; then
        AUTH_HEADER="Authorization: Bearer $AUTH_TOKEN"
        
        # Test 3: Dashboard Stats
        run_test "Dashboard Stats" \
            "curl -s -w '\n%{http_code}' -H '$AUTH_HEADER' '$BASE_URL/api/v1/dashboard/stats' | tail -n1" \
            "200"
        
        # Test 4: List Patients
        run_test "List Patients" \
            "curl -s -w '\n%{http_code}' -H '$AUTH_HEADER' '$BASE_URL/api/v1/healthcare/patients' | tail -n1" \
            "200"
        
        # Test 5: Healthcare Health
        run_test "Healthcare Module Health" \
            "curl -s -w '\n%{http_code}' -H '$AUTH_HEADER' '$BASE_URL/api/v1/healthcare/health' | tail -n1" \
            "200"
        
        # Test 6: Create Patient (the failing one)
        patient_data='{
            "resourceType": "Patient",
            "identifier": [{"use": "official", "value": "SMOKE-001"}],
            "name": [{"use": "official", "family": "Test", "given": ["Smoke"]}],
            "gender": "male",
            "birthDate": "1990-01-01",
            "active": true
        }'
        
        echo -e "\n${BLUE}Testing: Patient Creation (Known Issue)${NC}"
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        
        response=$(curl -s -w "\n%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -H "$AUTH_HEADER" \
            -d "$patient_data" \
            "$BASE_URL/api/v1/healthcare/patients")
        
        status_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | head -n -1)
        
        if [ "$status_code" = "201" ]; then
            log "PASS" "Patient Creation"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        elif [ "$status_code" = "500" ]; then
            log "FAIL" "Patient Creation - Internal Server Error (Schema validation issue)"
            echo "      Response: $body"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        else
            log "WARN" "Patient Creation - Unexpected status: $status_code"
            echo "      Response: $body"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
        
        # Test 7: Audit Health  
        run_test "Audit Module Health" \
            "curl -s -w '\n%{http_code}' -H '$AUTH_HEADER' '$BASE_URL/api/v1/audit/health' | tail -n1" \
            "200"
        
        # Test 8: Documents Health
        run_test "Documents Module Health" \
            "curl -s -w '\n%{http_code}' -H '$AUTH_HEADER' '$BASE_URL/api/v1/documents/health' | tail -n1" \
            "200"
        
    else
        log "FAIL" "Cannot run authenticated tests - authentication failed"
        FAILED_TESTS=$((FAILED_TESTS + 5))  # Skip 5 auth-required tests
        TOTAL_TESTS=$((TOTAL_TESTS + 5))
    fi
    
    # Summary
    echo ""
    echo "=================================="
    echo "📊 TEST SUMMARY"
    echo "=================================="
    echo "Total Tests: $TOTAL_TESTS"
    echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
    
    success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo "Success Rate: $success_rate%"
    
    echo ""
    if [ $FAILED_TESTS -eq 0 ]; then
        log "PASS" "ALL TESTS PASSED - Backend ready for frontend integration!"
        exit 0
    elif [ $PASSED_TESTS -ge 5 ]; then
        log "WARN" "Core systems working - Some issues need fixing"
        echo ""
        echo "🔧 RECOMMENDATIONS:"
        echo "1. Fix patient creation schema validation"
        echo "2. Run comprehensive test suite"
        echo "3. Then proceed with frontend integration"
        exit 1
    else
        log "FAIL" "CRITICAL ISSUES - Backend not ready for integration"
        echo ""
        echo "🚨 CRITICAL ACTIONS NEEDED:"
        echo "1. Check if backend server is running"
        echo "2. Verify database connectivity"
        echo "3. Fix authentication system"
        exit 2
    fi
}

# Run the test suite
main "$@"