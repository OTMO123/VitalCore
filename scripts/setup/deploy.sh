#!/bin/bash

# IRIS API Integration System - Production Deployment Script
# This script handles database migrations and service deployment

set -euo pipefail

# Configuration
ENVIRONMENT=${ENVIRONMENT:-production}
COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.yml}
MIGRATION_TIMEOUT=${MIGRATION_TIMEOUT:-120}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is required but not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is required but not installed"
        exit 1
    fi
    
    # Check environment file
    if [[ ! -f ".env.${ENVIRONMENT}" ]]; then
        log_error "Environment file .env.${ENVIRONMENT} not found"
        log_info "Please copy .env.production.template to .env.${ENVIRONMENT} and configure it"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

# Backup current deployment
backup_deployment() {
    log_info "Creating deployment backup..."
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup database (if running)
    if docker-compose ps | grep -q "postgres.*Up"; then
        log_info "Backing up database..."
        docker-compose exec -T db pg_dump -U postgres iris_db > "$BACKUP_DIR/database_backup.sql"
    fi
    
    # Backup environment config
    cp ".env.${ENVIRONMENT}" "$BACKUP_DIR/"
    
    log_info "Backup created in $BACKUP_DIR"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Ensure database is up
    log_info "Starting database service..."
    docker-compose up -d db
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    timeout $MIGRATION_TIMEOUT bash -c 'until docker-compose exec db pg_isready -U postgres; do sleep 2; done'
    
    # Run migrations using a temporary container
    log_info "Executing database migrations..."
    docker-compose run --rm app python -m alembic upgrade head
    
    if [[ $? -eq 0 ]]; then
        log_info "Database migrations completed successfully"
    else
        log_error "Database migrations failed"
        exit 1
    fi
}

# Deploy services
deploy_services() {
    log_info "Deploying services..."
    
    # Set environment file
    export ENV_FILE=".env.${ENVIRONMENT}"
    
    # Pull latest images
    log_info "Pulling latest images..."
    docker-compose pull
    
    # Start all services
    log_info "Starting services..."
    docker-compose --env-file "$ENV_FILE" up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 10
    
    # Check service health
    check_service_health
}

# Check service health
check_service_health() {
    log_info "Checking service health..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_info "Application is healthy"
            return 0
        fi
        
        log_warn "Health check failed (attempt $attempt/$max_attempts), retrying..."
        sleep 5
        ((attempt++))
    done
    
    log_error "Application failed to become healthy"
    docker-compose logs app
    exit 1
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check all expected services are running
    local services=("app" "worker" "scheduler" "db" "redis")
    
    for service in "${services[@]}"; do
        if docker-compose ps | grep "$service.*Up" > /dev/null; then
            log_info "✓ $service is running"
        else
            log_error "✗ $service is not running"
            docker-compose logs "$service"
            exit 1
        fi
    done
    
    # Test API endpoints
    log_info "Testing API endpoints..."
    
    # Health check
    if curl -f http://localhost:8000/health | grep -q "healthy"; then
        log_info "✓ Health endpoint working"
    else
        log_error "✗ Health endpoint failed"
        exit 1
    fi
    
    # Auth endpoint (should return 401 without token)
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/auth/me | grep -q "401"; then
        log_info "✓ Auth endpoint working"
    else
        log_error "✗ Auth endpoint failed"
        exit 1
    fi
    
    log_info "Deployment verification completed successfully"
}

# Rollback function
rollback() {
    log_warn "Rolling back deployment..."
    
    # Stop current services
    docker-compose down
    
    # Restore from latest backup
    LATEST_BACKUP=$(ls -t backups/ | head -n1)
    if [[ -n "$LATEST_BACKUP" ]]; then
        log_info "Restoring from backup: $LATEST_BACKUP"
        
        # Restore database
        if [[ -f "backups/$LATEST_BACKUP/database_backup.sql" ]]; then
            docker-compose up -d db
            sleep 10
            docker-compose exec -T db psql -U postgres -d iris_db < "backups/$LATEST_BACKUP/database_backup.sql"
        fi
        
        # Restore environment
        cp "backups/$LATEST_BACKUP/.env.${ENVIRONMENT}" ".env.${ENVIRONMENT}"
        
        # Restart services
        docker-compose --env-file ".env.${ENVIRONMENT}" up -d
        
        log_info "Rollback completed"
    else
        log_error "No backup found for rollback"
        exit 1
    fi
}

# Main deployment function
main() {
    log_info "Starting IRIS API Integration System deployment..."
    log_info "Environment: $ENVIRONMENT"
    
    # Set trap for rollback on error
    trap 'log_error "Deployment failed, initiating rollback..."; rollback' ERR
    
    check_prerequisites
    backup_deployment
    run_migrations
    deploy_services
    verify_deployment
    
    # Remove trap on successful completion
    trap - ERR
    
    log_info "🎉 Deployment completed successfully!"
    log_info "Application is available at: http://localhost:8000"
    log_info "API Documentation: http://localhost:8000/docs (if enabled)"
    log_info ""
    log_info "Next steps:"
    log_info "1. Update your DNS/load balancer to point to this instance"
    log_info "2. Configure SSL/TLS certificates"
    log_info "3. Set up monitoring and alerting"
    log_info "4. Review audit logs for any deployment issues"
}

# Handle command line arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    rollback)
        rollback
        ;;
    health)
        check_service_health
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|health}"
        echo "  deploy   - Full deployment with migrations"
        echo "  rollback - Rollback to previous deployment"
        echo "  health   - Check service health"
        exit 1
        ;;
esac