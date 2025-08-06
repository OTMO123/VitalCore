#!/bin/bash

# VitalCore Frontend Docker Deployment Script
# Comprehensive deployment for frontend + backend integration

set -e

echo "🚀 VitalCore Frontend Docker Deployment"
echo "========================================"

# Configuration
COMPOSE_FILE="docker-compose.frontend.yml"
PROJECT_NAME="vitalcore"
FRONTEND_PORT=5173
BACKEND_PORT=8000
NGINX_PORT=80

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Stop existing containers
stop_existing() {
    log_info "Stopping existing containers..."
    
    if docker-compose -f "$COMPOSE_FILE" ps -q | head -1 &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" down
        log_success "Existing containers stopped"
    else
        log_info "No existing containers to stop"
    fi
}

# Build and start services
build_and_start() {
    log_info "Building and starting services..."
    
    # Build images
    log_info "Building Docker images..."
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    
    # Start services
    log_info "Starting services..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log_success "Services started"
}

# Wait for services to be ready
wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    # Wait for database
    log_info "Waiting for PostgreSQL..."
    until docker-compose -f "$COMPOSE_FILE" exec db pg_isready -U postgres > /dev/null 2>&1; do
        printf "."
        sleep 2
    done
    echo ""
    log_success "PostgreSQL is ready"
    
    # Wait for Redis
    log_info "Waiting for Redis..."
    until docker-compose -f "$COMPOSE_FILE" exec redis redis-cli ping > /dev/null 2>&1; do
        printf "."
        sleep 2
    done
    echo ""
    log_success "Redis is ready"
    
    # Wait for backend API
    log_info "Waiting for backend API..."
    until curl -s http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; do
        printf "."
        sleep 3
    done
    echo ""
    log_success "Backend API is ready"
    
    # Wait for frontend
    log_info "Waiting for frontend..."
    until curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; do
        printf "."
        sleep 3
    done
    echo ""
    log_success "Frontend is ready"
}

# Run health checks
health_check() {
    log_info "Running health checks..."
    
    # Check all services
    local all_healthy=true
    
    services=(
        "db:PostgreSQL"
        "redis:Redis" 
        "app:Backend API"
        "frontend:Frontend"
        "worker:Celery Worker"
        "scheduler:Celery Beat"
        "minio:MinIO"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r service_name service_desc <<< "$service"
        
        if docker-compose -f "$COMPOSE_FILE" ps "$service_name" | grep -q "Up (healthy)"; then
            log_success "$service_desc is healthy"
        elif docker-compose -f "$COMPOSE_FILE" ps "$service_name" | grep -q "Up"; then
            log_warning "$service_desc is running (health check not available)"
        else
            log_error "$service_desc is not running"
            all_healthy=false
        fi
    done
    
    if [ "$all_healthy" = true ]; then
        log_success "All services are healthy"
    else
        log_error "Some services are not healthy"
        return 1
    fi
}

# Show service URLs
show_urls() {
    log_info "Service URLs:"
    echo "=============="
    echo "🏥 VitalCore Frontend:     http://localhost:$FRONTEND_PORT"
    echo "🩺 Production Frontend:    http://localhost:$FRONTEND_PORT/components/core/VitalCore-Production.html"
    echo "🧠 MedBrain Enhanced:      http://localhost:$FRONTEND_PORT/components/core/MedBrain-Enhanced.html"
    echo "🔧 Backend API:            http://localhost:$BACKEND_PORT"
    echo "📚 API Documentation:     http://localhost:$BACKEND_PORT/docs"
    echo "🗄️  MinIO Console:         http://localhost:9001"
    echo "🔍 Database:               localhost:5432 (postgres/password)"
    echo "🔴 Redis:                  localhost:6379"
    
    if docker-compose -f "$COMPOSE_FILE" ps nginx &> /dev/null; then
        echo "🌐 Nginx Proxy:           http://localhost:$NGINX_PORT"
    fi
    echo ""
}

# Show service status
show_status() {
    log_info "Service Status:"
    echo "==============="
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
}

# Show logs
show_logs() {
    if [ "$1" = "follow" ]; then
        log_info "Following logs (Ctrl+C to stop)..."
        docker-compose -f "$COMPOSE_FILE" logs -f
    else
        log_info "Recent logs:"
        docker-compose -f "$COMPOSE_FILE" logs --tail=50
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    docker-compose -f "$COMPOSE_FILE" down
    docker system prune -f
    log_success "Cleanup completed"
}

# Main deployment function
deploy() {
    log_info "Starting VitalCore deployment..."
    
    check_prerequisites
    stop_existing
    build_and_start
    wait_for_services
    
    if health_check; then
        log_success "🎉 VitalCore deployment completed successfully!"
        echo ""
        show_urls
        show_status
        
        log_info "🎯 Quick Test Commands:"
        echo "curl http://localhost:$BACKEND_PORT/health    # Backend health"
        echo "curl http://localhost:$FRONTEND_PORT           # Frontend"
        echo ""
        
        log_info "📋 Management Commands:"
        echo "./deploy-frontend.sh logs          # View logs"
        echo "./deploy-frontend.sh logs follow   # Follow logs"
        echo "./deploy-frontend.sh status        # Service status" 
        echo "./deploy-frontend.sh stop          # Stop services"
        echo "./deploy-frontend.sh cleanup       # Full cleanup"
        echo ""
        
        log_info "🧪 Test the enhanced MedBrain with voice recognition!"
        log_info "Visit: http://localhost:$FRONTEND_PORT/components/core/VitalCore-Production.html"
        
    else
        log_error "Deployment failed - some services are not healthy"
        exit 1
    fi
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy"|"start")
        deploy
        ;;
    "stop")
        log_info "Stopping services..."
        docker-compose -f "$COMPOSE_FILE" down
        log_success "Services stopped"
        ;;
    "restart")
        log_info "Restarting services..."
        docker-compose -f "$COMPOSE_FILE" restart
        wait_for_services
        health_check
        show_urls
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs "${2:-}"
        ;;
    "health")
        health_check
        ;;
    "cleanup")
        cleanup
        ;;
    "urls")
        show_urls
        ;;
    *)
        echo "Usage: $0 {deploy|start|stop|restart|status|logs|health|cleanup|urls}"
        echo ""
        echo "Commands:"
        echo "  deploy    - Deploy all services (default)"
        echo "  start     - Same as deploy"
        echo "  stop      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  status    - Show service status"
        echo "  logs      - Show recent logs"
        echo "  logs follow - Follow logs in real-time"
        echo "  health    - Check service health"
        echo "  cleanup   - Stop services and cleanup"
        echo "  urls      - Show service URLs"
        exit 1
        ;;
esac