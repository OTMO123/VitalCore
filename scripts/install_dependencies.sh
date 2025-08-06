#!/bin/bash

# Phase 1.1.1.2: Dependency Installation Script for Phase 5 Implementation
# This script ensures all required Phase 5 dependencies are properly installed
# with comprehensive validation and fallback mechanisms.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="${PROJECT_ROOT}/venv"
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"
LOG_FILE="${PROJECT_ROOT}/logs/dependency_install.log"

# Create logs directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    log_info "Checking Python version..."
    
    if ! command_exists python3; then
        log_error "Python 3 is not installed or not in PATH"
        return 1
    fi
    
    local python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    local required_version="3.9"
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
        log_error "Python 3.9+ is required, but found Python $python_version"
        return 1
    fi
    
    log_success "Python $python_version is compatible"
    return 0
}

# Function to create virtual environment
setup_virtual_environment() {
    log_info "Setting up virtual environment..."
    
    if [ ! -d "$VENV_PATH" ]; then
        log_info "Creating virtual environment at $VENV_PATH"
        python3 -m venv "$VENV_PATH"
    else
        log_info "Virtual environment already exists at $VENV_PATH"
    fi
    
    # Activate virtual environment
    source "$VENV_PATH/bin/activate"
    
    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel
    
    log_success "Virtual environment ready"
}

# Function to install system dependencies
install_system_dependencies() {
    log_info "Checking system dependencies..."
    
    # Check for required system packages
    local missing_packages=()
    
    # For PostgreSQL
    if ! command_exists pg_config; then
        missing_packages+=("postgresql-dev")
    fi
    
    # For image processing
    if ! command_exists tesseract; then
        missing_packages+=("tesseract-ocr")
    fi
    
    # For Redis
    if ! command_exists redis-server; then
        missing_packages+=("redis-server")
    fi
    
    if [ ${#missing_packages[@]} -gt 0 ]; then
        log_warning "Missing system packages: ${missing_packages[*]}"
        log_info "Please install them using your system package manager:"
        
        if command_exists apt-get; then
            log_info "  sudo apt-get install ${missing_packages[*]}"
        elif command_exists yum; then
            log_info "  sudo yum install ${missing_packages[*]}"
        elif command_exists brew; then
            log_info "  brew install ${missing_packages[*]}"
        fi
        
        log_warning "Continuing with Python dependencies..."
    else
        log_success "All required system dependencies are available"
    fi
}

# Function to install Python dependencies
install_python_dependencies() {
    log_info "Installing Python dependencies from $REQUIREMENTS_FILE..."
    
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        log_error "Requirements file not found: $REQUIREMENTS_FILE"
        return 1
    fi
    
    # Install dependencies with retry mechanism
    local max_retries=3
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        if pip install -r "$REQUIREMENTS_FILE"; then
            log_success "All Python dependencies installed successfully"
            return 0
        else
            retry_count=$((retry_count + 1))
            log_warning "Installation attempt $retry_count failed. Retrying..."
            sleep 5
        fi
    done
    
    log_error "Failed to install dependencies after $max_retries attempts"
    return 1
}

# Function to verify Phase 5 critical dependencies
verify_phase5_dependencies() {
    log_info "Verifying Phase 5 critical dependencies..."
    
    local critical_packages=(
        "structlog"
        "brotli"
        "opentelemetry-api"
        "prometheus_client"
        "locust"
        "geoip2"
        "psutil"
        "user_agents"
        "watchdog"
    )
    
    local failed_packages=()
    
    for package in "${critical_packages[@]}"; do
        if python3 -c "import ${package}" 2>/dev/null; then
            log_success "✓ $package"
        else
            log_error "✗ $package"
            failed_packages+=("$package")
        fi
    done
    
    if [ ${#failed_packages[@]} -gt 0 ]; then
        log_error "Failed to import critical packages: ${failed_packages[*]}"
        return 1
    fi
    
    log_success "All Phase 5 critical dependencies verified"
    return 0
}

# Function to create dependency report
create_dependency_report() {
    log_info "Creating dependency report..."
    
    local report_file="${PROJECT_ROOT}/logs/dependency_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "=== Dependency Installation Report ==="
        echo "Timestamp: $(date)"
        echo "Python Version: $(python3 --version)"
        echo "Pip Version: $(pip --version)"
        echo ""
        echo "=== Installed Packages ==="
        pip list
        echo ""
        echo "=== Environment Variables ==="
        env | grep -E "(PYTHON|PIP|VIRTUAL_ENV)" || echo "No relevant environment variables"
    } > "$report_file"
    
    log_success "Dependency report created: $report_file"
}

# Function to run post-installation tests
run_post_installation_tests() {
    log_info "Running post-installation tests..."
    
    # Test critical imports
    if python3 -c "
import sys
import structlog
import brotli
import opentelemetry.api
import prometheus_client
import geoip2
import psutil
import user_agents
import watchdog
print('All critical imports successful')
" 2>/dev/null; then
        log_success "Post-installation tests passed"
        return 0
    else
        log_error "Post-installation tests failed"
        return 1
    fi
}

# Main installation function
main() {
    log_info "Starting Phase 5 dependency installation..."
    log_info "Project root: $PROJECT_ROOT"
    
    # Pre-installation checks
    if ! check_python_version; then
        exit 1
    fi
    
    # Setup environment
    if ! setup_virtual_environment; then
        log_error "Failed to setup virtual environment"
        exit 1
    fi
    
    # Install system dependencies
    install_system_dependencies
    
    # Install Python dependencies
    if ! install_python_dependencies; then
        log_error "Failed to install Python dependencies"
        exit 1
    fi
    
    # Verify critical dependencies
    if ! verify_phase5_dependencies; then
        log_error "Phase 5 dependency verification failed"
        exit 1
    fi
    
    # Run tests
    if ! run_post_installation_tests; then
        log_error "Post-installation tests failed"
        exit 1
    fi
    
    # Create report
    create_dependency_report
    
    log_success "Phase 5 dependency installation completed successfully!"
    log_info "Virtual environment: $VENV_PATH"
    log_info "To activate: source $VENV_PATH/bin/activate"
}

# Help function
show_help() {
    cat << EOF
Phase 5 Dependency Installation Script

Usage: $0 [OPTIONS]

OPTIONS:
    -h, --help          Show this help message
    -v, --verbose       Enable verbose output
    --skip-system       Skip system dependency checks
    --requirements FILE Specify custom requirements file

Examples:
    $0                          # Standard installation
    $0 --verbose               # Verbose installation
    $0 --requirements custom.txt # Use custom requirements file

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            set -x
            shift
            ;;
        --skip-system)
            SKIP_SYSTEM=1
            shift
            ;;
        --requirements)
            REQUIREMENTS_FILE="$2"
            shift 2
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Run main function
main "$@"