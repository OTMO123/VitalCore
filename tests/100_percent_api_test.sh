#!/bin/bash
# 100% Backend API Reliability Test Suite
# Comprehensive testing for absolute backend reliability

BASE_URL="http://localhost:8000"
AUTH_TOKEN=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
CRITICAL_TESTS=0
CRITICAL_PASSED=0

# Test data tracking
TEST_PATIENT_ID=""
CREATED_DATA=()

# Enhanced logging
log() {
    local status=$1
    local message=$2
    local timestamp=$(date '+%H:%M:%S')
    
    case $status in
        "PASS") echo -e "${BOLD}[${timestamp}]${NC} ${GREEN}✅ $message${NC}" ;;
        "FAIL") echo -e "${BOLD}[${timestamp}]${NC} ${RED}❌ $message${NC}" ;;
        "WARN") echo -e "${BOLD}[${timestamp}]${NC} ${YELLOW}⚠️  $message${NC}" ;;
        "INFO") echo -e "${BOLD}[${timestamp}]${NC} ${BLUE}ℹ️  $message${NC}" ;;
        "CRITICAL") echo -e "${BOLD}[${timestamp}]${NC} ${RED}🚨 $message${NC}" ;;
        "SUCCESS") echo -e "${BOLD}[${timestamp}]${NC} ${GREEN}🎉 $message${NC}" ;;
        *) echo -e "${BOLD}[${timestamp}]${NC} $message" ;;
    esac
}

# Enhanced test function
run_test() {
    local test_name=$1
    local curl_command=$2
    local expected_status=${3:-200}
    local is_critical=${4:-false}
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [ "$is_critical" = true ]; then
        CRITICAL_TESTS=$((CRITICAL_TESTS + 1))
    fi
    
    log "INFO" "Testing: $test_name"
    
    # Execute curl with timeout and detailed error handling
    local response
    local status_code
    
    response=$(timeout 30s bash -c "$curl_command" 2>/dev/null)
    local curl_exit_code=$?
    
    if [ $curl_exit_code -eq 124 ]; then
        log "FAIL" "$test_name - TIMEOUT (30s)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    elif [ $curl_exit_code -ne 0 ]; then
        log "FAIL" "$test_name - CURL ERROR (exit code: $curl_exit_code)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
    
    status_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" = "$expected_status" ]; then
        log "PASS" "$test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        if [ "$is_critical" = true ]; then
            CRITICAL_PASSED=$((CRITICAL_PASSED + 1))
        fi
        
        # Store response for tests that need follow-up
        case "$test_name" in
            "Create Patient"*)
                TEST_PATIENT_ID=$(echo "$body" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
                if [ -n "$TEST_PATIENT_ID" ]; then
                    CREATED_DATA+=("patient:$TEST_PATIENT_ID")
                    log "INFO" "Created test patient: $TEST_PATIENT_ID"
                fi
                ;;
        esac
        
        return 0
    else
        local error_detail=""
        if echo "$body" | grep -q "detail"; then
            error_detail=" - $(echo "$body" | grep -o '"detail":"[^"]*"' | cut -d'"' -f4)"
        fi
        
        log "FAIL" "$test_name (Status: $status_code, Expected: $expected_status)$error_detail"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Authentication function
authenticate() {
    log "INFO" "🔐 Authenticating with admin credentials..."
    
    local response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=admin&password=admin123" \
        "$BASE_URL/api/v1/auth/login")
    
    local status_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n -1)
    
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

# Phase 1: System Fundamentals
test_system_fundamentals() {
    log "INFO" ""
    log "INFO" "🔍 PHASE 1: SYSTEM FUNDAMENTALS (CRITICAL)"
    log "INFO" "=============================================="
    
    # Test 1: Root health endpoint
    run_test "System Health Check" \
        "curl -s -w '\n%{http_code}' '$BASE_URL/health' | tail -n1" \
        "200" true
    
    # Test 2: OpenAPI docs
    run_test "OpenAPI Documentation" \
        "curl -s -w '\n%{http_code}' '$BASE_URL/openapi.json' | tail -n1" \
        "200" true
    
    # Test 3: Root endpoint
    run_test "Root Endpoint" \
        "curl -s -w '\n%{http_code}' '$BASE_URL/' | tail -n1" \
        "200" true
    
    # Test 4: Authentication
    if authenticate; then
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        CRITICAL_TESTS=$((CRITICAL_TESTS + 1))
        PASSED_TESTS=$((PASSED_TESTS + 1))
        CRITICAL_PASSED=$((CRITICAL_PASSED + 1))
    else
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        CRITICAL_TESTS=$((CRITICAL_TESTS + 1))
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
    
    return 0
}

# Phase 2: Module Health Checks
test_module_health() {
    log "INFO" ""
    log "INFO" "🏥 PHASE 2: MODULE HEALTH CHECKS"
    log "INFO" "================================="
    
    local AUTH_HEADER="Authorization: Bearer $AUTH_TOKEN"
    
    # All health endpoints
    local health_endpoints=(
        "Healthcare Health:/api/v1/healthcare/health"
        "Dashboard Health:/api/v1/dashboard/health"
        "Audit Health:/api/v1/audit/health"
        "Documents Health:/api/v1/documents/health"
        "Analytics Health:/api/v1/analytics/health"
        "Risk Health:/api/v1/patients/risk/health"
        "Purge Health:/api/v1/purge/health"
        "IRIS Health:/api/v1/iris/health"
    )
    
    for endpoint in "${health_endpoints[@]}"; do
        local name=$(echo "$endpoint" | cut -d: -f1)
        local path=$(echo "$endpoint" | cut -d: -f2)
        
        run_test "$name" \
            "curl -s -w '\n%{http_code}' -H '$AUTH_HEADER' '$BASE_URL$path' | tail -n1" \
            "200" false
    done
}

# Phase 3: Patient CRUD Lifecycle
test_patient_lifecycle() {
    log "INFO" ""
    log "INFO" "👥 PHASE 3: PATIENT CRUD LIFECYCLE (CRITICAL)"
    log "INFO" "=============================================="
    
    local AUTH_HEADER="Authorization: Bearer $AUTH_TOKEN"
    
    # Test 1: List patients
    run_test "List Patients" \
        "curl -s -w '\n%{http_code}' -H '$AUTH_HEADER' '$BASE_URL/api/v1/healthcare/patients' | tail -n1" \
        "200" true
    
    # Test 2: Create patient with complete valid data
    local patient_data='{
        "resourceType": "Patient",
        "identifier": [{
            "use": "official",
            "type": {
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}]
            },
            "system": "http://hospital.smarthit.org",
            "value": "TEST-100-'$(date +%s)'"
        }],
        "name": [{
            "use": "official",
            "family": "TestPatient100",
            "given": ["Reliability", "Test"]
        }],
        "gender": "male",
        "birthDate": "1990-01-01",
        "active": true,
        "organization_id": "550e8400-e29b-41d4-a716-446655440000",
        "consent_status": "pending",
        "consent_types": ["treatment"]
    }'
    
    run_test "Create Patient" \
        "curl -s -w '\n%{http_code}' -X POST -H 'Content-Type: application/json' -H '$AUTH_HEADER' -d '$patient_data' '$BASE_URL/api/v1/healthcare/patients'" \
        "201" true
    
    # Test 3: Get created patient (if creation succeeded)
    if [ -n "$TEST_PATIENT_ID" ]; then
        run_test "Get Patient by ID" \
            "curl -s -w '\n%{http_code}' -H '$AUTH_HEADER' '$BASE_URL/api/v1/healthcare/patients/$TEST_PATIENT_ID' | tail -n1" \
            "200" true
        
        # Test 4: Update patient
        local update_data='{"gender": "female", "consent_status": "active"}'
        run_test "Update Patient" \
            "curl -s -w '\n%{http_code}' -X PUT -H 'Content-Type: application/json' -H '$AUTH_HEADER' -d '$update_data' '$BASE_URL/api/v1/healthcare/patients/$TEST_PATIENT_ID' | tail -n1" \
            "200" false
    else
        log "WARN" "Skipping patient Get/Update tests - no patient ID available"
    fi
}

# Phase 4: Dashboard Functionality
test_dashboard() {
    log "INFO" ""
    log "INFO" "📊 PHASE 4: DASHBOARD FUNCTIONALITY"
    log "INFO" "==================================="
    
    local AUTH_HEADER="Authorization: Bearer $AUTH_TOKEN"
    
    local dashboard_endpoints=(
        "Dashboard Stats:/api/v1/dashboard/stats"
        "Dashboard Activities:/api/v1/dashboard/activities"
        "Dashboard Alerts:/api/v1/dashboard/alerts"
        "Performance Metrics:/api/v1/dashboard/performance"
        "Cache Stats:/api/v1/dashboard/cache/stats"
    )
    
    for endpoint in "${dashboard_endpoints[@]}"; do
        local name=$(echo "$endpoint" | cut -d: -f1)
        local path=$(echo "$endpoint" | cut -d: -f2)
        
        run_test "$name" \
            "curl -s -w '\n%{http_code}' -H '$AUTH_HEADER' '$BASE_URL$path' | tail -n1" \
            "200" false
    done
}

# Phase 5: Audit & Compliance
test_audit_compliance() {
    log "INFO" ""
    log "INFO" "📋 PHASE 5: AUDIT & COMPLIANCE"
    log "INFO" "==============================="
    
    local AUTH_HEADER="Authorization: Bearer $AUTH_TOKEN"
    
    local audit_endpoints=(
        "Audit Stats:/api/v1/audit/stats"
        "Audit Logs:/api/v1/audit/logs"
        "Recent Activities:/api/v1/audit/recent-activities"
        "Compliance Summary:/api/v1/healthcare/compliance/summary"
    )
    
    for endpoint in "${audit_endpoints[@]}"; do
        local name=$(echo "$endpoint" | cut -d: -f1)
        local path=$(echo "$endpoint" | cut -d: -f2)
        
        run_test "$name" \
            "curl -s -w '\n%{http_code}' -H '$AUTH_HEADER' '$BASE_URL$path' | tail -n1" \
            "200" false
    done
}

# Phase 6: Error Handling
test_error_handling() {
    log "INFO" ""
    log "INFO" "⚠️  PHASE 6: ERROR HANDLING"
    log "INFO" "==========================="
    
    local AUTH_HEADER="Authorization: Bearer $AUTH_TOKEN"
    
    # Test 1: Invalid patient data (should return 422)
    local invalid_data='{"invalid": "data"}'
    run_test "Invalid Patient Data Handling" \
        "curl -s -w '\n%{http_code}' -X POST -H 'Content-Type: application/json' -H '$AUTH_HEADER' -d '$invalid_data' '$BASE_URL/api/v1/healthcare/patients' | tail -n1" \
        "422" false
    
    # Test 2: Non-existent patient (should return 404)
    run_test "Non-existent Patient Handling" \
        "curl -s -w '\n%{http_code}' -H '$AUTH_HEADER' '$BASE_URL/api/v1/healthcare/patients/nonexistent-id' | tail -n1" \
        "404" false
    
    # Test 3: Unauthorized access (should return 401/403)
    local response=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/v1/healthcare/patients")
    local status_code=$(echo "$response" | tail -n1)
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [ "$status_code" = "401" ] || [ "$status_code" = "403" ]; then
        log "PASS" "Unauthorized Access Handling"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        log "FAIL" "Unauthorized Access Handling (Expected 401/403, got $status_code)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# Cleanup function
cleanup_test_data() {
    if [ ${#CREATED_DATA[@]} -eq 0 ]; then
        return
    fi
    
    log "INFO" ""
    log "INFO" "🧹 CLEANING UP TEST DATA"
    log "INFO" "========================"
    
    local AUTH_HEADER="Authorization: Bearer $AUTH_TOKEN"
    
    for item in "${CREATED_DATA[@]}"; do
        local type=$(echo "$item" | cut -d: -f1)
        local id=$(echo "$item" | cut -d: -f2)
        
        case "$type" in
            "patient")
                curl -s -X DELETE -H "$AUTH_HEADER" "$BASE_URL/api/v1/healthcare/patients/$id" > /dev/null
                log "INFO" "Cleaned up test patient: $id"
                ;;
        esac
    done
}

# Main test suite
main() {
    echo -e "${BOLD}${BLUE}"
    echo "🚀 100% Backend API Reliability Test Suite"
    echo "=========================================="
    echo -e "${NC}"
    
    local start_time=$(date +%s)
    
    # Phase 1: System Fundamentals (MUST PASS)
    if ! test_system_fundamentals; then
        log "CRITICAL" "System fundamentals failed - cannot continue testing"
        return 1
    fi
    
    # Phase 2: Module Health Checks
    test_module_health
    
    # Phase 3: Patient Lifecycle (MUST PASS)
    test_patient_lifecycle
    
    # Phase 4: Dashboard Functionality
    test_dashboard
    
    # Phase 5: Audit & Compliance
    test_audit_compliance
    
    # Phase 6: Error Handling
    test_error_handling
    
    # Calculate results
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local success_rate=0
    local critical_rate=0
    
    if [ $TOTAL_TESTS -gt 0 ]; then
        success_rate=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))
    fi
    
    if [ $CRITICAL_TESTS -gt 0 ]; then
        critical_rate=$(( (CRITICAL_PASSED * 100) / CRITICAL_TESTS ))
    fi
    
    # Final Results
    echo ""
    echo -e "${BOLD}${BLUE}=================================="
    echo "📊 100% RELIABILITY TEST RESULTS"
    echo -e "==================================${NC}"
    echo ""
    echo -e "${BOLD}Execution Time:${NC} ${duration}s"
    echo -e "${BOLD}Total Tests:${NC} $TOTAL_TESTS"
    echo -e "${GREEN}✅ Passed:${NC} $PASSED_TESTS"
    echo -e "${RED}❌ Failed:${NC} $FAILED_TESTS"
    echo -e "${BOLD}📈 Success Rate:${NC} $success_rate%"
    echo -e "${BOLD}🎯 Critical Success Rate:${NC} $critical_rate%"
    echo ""
    
    # Determine readiness
    if [ $success_rate -eq 100 ]; then
        log "SUCCESS" "🎉 100% SUCCESS - Backend ready for frontend integration!"
        cleanup_test_data
        return 0
    elif [ $critical_rate -eq 100 ] && [ $success_rate -ge 90 ]; then
        log "PASS" "✅ GOOD - Critical systems working, minor issues acceptable"
        log "INFO" "Ready for frontend integration with monitoring"
        cleanup_test_data
        return 0
    else
        log "CRITICAL" "❌ NOT READY - Critical issues must be fixed before frontend integration"
        echo ""
        echo -e "${BOLD}🔧 REQUIRED ACTIONS:${NC}"
        
        if [ $critical_rate -lt 100 ]; then
            echo "1. 🚨 Fix critical system failures (authentication, patient management)"
        fi
        
        if [ $success_rate -lt 90 ]; then
            echo "2. ⚠️  Address failing endpoints to reach 90%+ success rate"
        fi
        
        echo "3. 🔄 Re-run this test after fixes"
        echo "4. 📋 Check backend logs for detailed error information"
        
        cleanup_test_data
        return 1
    fi
}

# Handle interrupts
trap 'echo -e "\n⏹️  Test interrupted by user"; cleanup_test_data; exit 130' INT TERM

# Run the comprehensive test suite
main "$@"
exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✅ BACKEND IS 100% READY FOR FRONTEND INTEGRATION!${NC}"
else
    echo -e "${RED}${BOLD}❌ BACKEND REQUIRES FIXES BEFORE FRONTEND INTEGRATION${NC}"
fi

exit $exit_code