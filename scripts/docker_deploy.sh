#!/bin/bash
# Docker Quick Deploy Script for Email Receipts Application
# Usage: ./docker_deploy.sh [start|stop|restart|rebuild|logs|status]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_env_file() {
    if [ ! -f .env ]; then
        print_error ".env file not found!"
        print_info "Creating .env from .env.example..."
        if [ -f .env.example ]; then
            cp .env.example .env
            print_warning "Please update .env with your credentials before starting!"
            exit 1
        else
            print_error ".env.example not found!"
            exit 1
        fi
    fi
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        print_info "Install from: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed!"
        print_info "Install from: https://docs.docker.com/compose/install/"
        exit 1
    fi
}

start_app() {
    echo "🚀 Starting Email Receipts Application..."
    check_env_file
    
    # Build and start
    docker-compose up -d --build
    
    if [ $? -eq 0 ]; then
        print_success "Application started successfully!"
        print_info "Access the application at: http://localhost:5001"
        print_info "View logs with: docker-compose logs -f web"
        
        # Wait for health check
        sleep 3
        print_info "Checking application health..."
        
        if curl -f -s http://localhost:5001/api/health > /dev/null; then
            print_success "Application is healthy!"
        else
            print_warning "Application may still be starting up..."
            print_info "Check logs: docker-compose logs web"
        fi
    else
        print_error "Failed to start application!"
        exit 1
    fi
}

stop_app() {
    echo "🛑 Stopping Email Receipts Application..."
    docker-compose stop
    
    if [ $? -eq 0 ]; then
        print_success "Application stopped successfully!"
    else
        print_error "Failed to stop application!"
        exit 1
    fi
}

restart_app() {
    echo "🔄 Restarting Email Receipts Application..."
    docker-compose restart
    
    if [ $? -eq 0 ]; then
        print_success "Application restarted successfully!"
        print_info "Access the application at: http://localhost:5001"
    else
        print_error "Failed to restart application!"
        exit 1
    fi
}

rebuild_app() {
    echo "🔨 Rebuilding Email Receipts Application..."
    check_env_file
    
    print_info "Stopping existing containers..."
    docker-compose down
    
    print_info "Building fresh images..."
    docker-compose build --no-cache
    
    print_info "Starting application..."
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        print_success "Application rebuilt and started successfully!"
        print_info "Access the application at: http://localhost:5001"
    else
        print_error "Failed to rebuild application!"
        exit 1
    fi
}

show_logs() {
    print_info "Showing application logs (Ctrl+C to exit)..."
    docker-compose logs -f web
}

show_status() {
    echo "📊 Application Status"
    echo "===================="
    echo ""
    
    # Container status
    print_info "Container Status:"
    docker-compose ps
    echo ""
    
    # Health check
    print_info "Health Status:"
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' email-receipts-app 2>/dev/null || echo "not running")
    if [ "$HEALTH" = "healthy" ]; then
        print_success "Container is healthy"
    elif [ "$HEALTH" = "starting" ]; then
        print_warning "Container is starting..."
    elif [ "$HEALTH" = "unhealthy" ]; then
        print_error "Container is unhealthy!"
    else
        print_error "Container is not running"
    fi
    echo ""
    
    # Check if accessible
    print_info "Application Accessibility:"
    if curl -f -s http://localhost:5001/api/health > /dev/null; then
        print_success "Application is accessible at http://localhost:5001"
    else
        print_error "Application is not accessible"
    fi
    echo ""
    
    # Resource usage
    print_info "Resource Usage:"
    docker stats --no-stream email-receipts-app 2>/dev/null || print_warning "Container not running"
}

run_security_check() {
    print_info "Running security check..."
    docker-compose exec web python scripts/check_security.py
}

backup_logs() {
    BACKUP_FILE="logs-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    print_info "Creating log backup: $BACKUP_FILE"
    
    tar -czf "$BACKUP_FILE" logs/ 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "Logs backed up to $BACKUP_FILE"
    else
        print_error "Failed to backup logs"
    fi
}

show_usage() {
    echo "Email Receipts Docker Deployment Script"
    echo "========================================"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start       - Build and start the application"
    echo "  stop        - Stop the application"
    echo "  restart     - Restart the application"
    echo "  rebuild     - Rebuild from scratch and start"
    echo "  logs        - Show application logs"
    echo "  status      - Show application status"
    echo "  security    - Run security check"
    echo "  backup-logs - Backup application logs"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start         # Start the application"
    echo "  $0 logs          # View logs"
    echo "  $0 status        # Check status"
    echo ""
}

# Main script logic
check_docker

case "${1:-help}" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        restart_app
        ;;
    rebuild)
        rebuild_app
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    security)
        run_security_check
        ;;
    backup-logs)
        backup_logs
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
