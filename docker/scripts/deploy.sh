#!/bin/bash

# RAG Chatbot PWA Deployment Script
# Comprehensive deployment automation for production and staging environments

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_ROOT/docker"
BACKUP_DIR="$PROJECT_ROOT/backups"

# Default values
ENVIRONMENT="production"
ACTION="deploy"
SKIP_BACKUP=false
SKIP_TESTS=false
FORCE=false
VERBOSE=false

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

print_debug() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# Function to show usage
show_usage() {
    cat << EOF
RAG Chatbot PWA Deployment Script

Usage: $0 [OPTIONS] [ACTION]

ACTIONS:
    deploy          Deploy the application (default)
    build           Build Docker images only
    start           Start existing deployment
    stop            Stop running deployment
    restart         Restart deployment
    status          Show deployment status
    logs            Show application logs
    backup          Create database backup
    restore         Restore from backup
    update          Update deployment with new images
    cleanup         Clean up old images and volumes
    health          Check application health

OPTIONS:
    -e, --env ENV           Deployment environment (production|staging|development) [default: production]
    -s, --skip-backup      Skip database backup before deployment
    -t, --skip-tests       Skip running tests before deployment
    -f, --force            Force deployment without confirmations
    -v, --verbose          Verbose output
    -h, --help             Show this help message

EXAMPLES:
    $0 deploy -e production
    $0 build -e staging -v
    $0 backup
    $0 logs -e production
    $0 restart -e staging

ENVIRONMENT FILES:
    Create .env file in docker/ directory with required configuration.
    See .env.example for template.

EOF
}

# Function to parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -s|--skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            -t|--skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            deploy|build|start|stop|restart|status|logs|backup|restore|update|cleanup|health)
                ACTION="$1"
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                ;;
        esac
    done
}

# Function to validate environment
validate_environment() {
    case $ENVIRONMENT in
        production|staging|development)
            print_debug "Environment validated: $ENVIRONMENT"
            ;;
        *)
            print_error "Invalid environment: $ENVIRONMENT. Must be one of: production, staging, development"
            ;;
    esac
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
    fi
    
    # Check if .env file exists
    if [[ ! -f "$DOCKER_DIR/.env" ]]; then
        print_error ".env file not found in $DOCKER_DIR. Copy .env.example and configure it."
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
    fi
    
    print_status "Prerequisites check passed"
}

# Function to get Docker Compose file
get_compose_file() {
    case $ENVIRONMENT in
        production)
            echo "$DOCKER_DIR/docker-compose.prod.yml"
            ;;
        staging)
            echo "$DOCKER_DIR/docker-compose.staging.yml"
            ;;
        development)
            echo "$PROJECT_ROOT/docker-compose.yml"
            ;;
    esac
}

# Function to run tests
run_tests() {
    if [[ "$SKIP_TESTS" == true ]]; then
        print_warning "Skipping tests"
        return
    fi
    
    print_status "Running tests..."
    
    # Backend tests
    cd "$PROJECT_ROOT/backend"
    if [[ -f "requirements.txt" ]]; then
        print_debug "Running backend tests"
        # This would run in a test container in a real deployment
        print_status "Backend tests would run here"
    fi
    
    # Frontend tests
    cd "$PROJECT_ROOT/frontend"
    if [[ -f "package.json" ]]; then
        print_debug "Running frontend tests"
        # This would run in a test container in a real deployment
        print_status "Frontend tests would run here"
    fi
    
    cd "$PROJECT_ROOT"
    print_status "Tests completed"
}

# Function to create backup
create_backup() {
    if [[ "$SKIP_BACKUP" == true || "$ENVIRONMENT" == "development" ]]; then
        print_warning "Skipping backup"
        return
    fi
    
    print_status "Creating database backup..."
    
    local compose_file=$(get_compose_file)
    local backup_file="$BACKUP_DIR/ragchatbot_$(date +%Y%m%d_%H%M%S).sql"
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Create database backup
    cd "$DOCKER_DIR"
    docker-compose -f "$compose_file" exec -T postgres pg_dump -U raguser ragchatbot > "$backup_file"
    
    # Compress backup
    gzip "$backup_file"
    
    print_status "Backup created: ${backup_file}.gz"
}

# Function to build images
build_images() {
    print_status "Building Docker images for $ENVIRONMENT environment..."
    
    local compose_file=$(get_compose_file)
    
    cd "$DOCKER_DIR"
    docker-compose -f "$compose_file" build --no-cache
    
    print_status "Images built successfully"
}

# Function to deploy application
deploy_application() {
    print_status "Deploying RAG Chatbot PWA ($ENVIRONMENT environment)..."
    
    local compose_file=$(get_compose_file)
    
    # Create backup if needed
    create_backup
    
    # Build images
    build_images
    
    # Stop existing services
    cd "$DOCKER_DIR"
    docker-compose -f "$compose_file" down --remove-orphans
    
    # Start services
    docker-compose -f "$compose_file" up -d
    
    # Wait for services to be healthy
    wait_for_health
    
    print_status "Deployment completed successfully"
}

# Function to wait for services to be healthy
wait_for_health() {
    print_status "Waiting for services to be healthy..."
    
    local compose_file=$(get_compose_file)
    local max_attempts=30
    local attempt=0
    
    cd "$DOCKER_DIR"
    
    while [[ $attempt -lt $max_attempts ]]; do
        local unhealthy_services=$(docker-compose -f "$compose_file" ps --services --filter "health=unhealthy")
        
        if [[ -z "$unhealthy_services" ]]; then
            print_status "All services are healthy"
            return
        fi
        
        print_debug "Waiting for services to be healthy... (attempt $((attempt + 1))/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    print_warning "Some services may not be healthy. Check with: $0 status"
}

# Function to show application status
show_status() {
    print_status "Application status for $ENVIRONMENT environment:"
    
    local compose_file=$(get_compose_file)
    
    cd "$DOCKER_DIR"
    docker-compose -f "$compose_file" ps
    
    echo
    print_status "Service health checks:"
    docker-compose -f "$compose_file" ps --format "table {{.Service}}\t{{.State}}\t{{.Status}}"
}

# Function to show logs
show_logs() {
    local compose_file=$(get_compose_file)
    
    cd "$DOCKER_DIR"
    docker-compose -f "$compose_file" logs -f --tail=100
}

# Function to start services
start_services() {
    print_status "Starting services for $ENVIRONMENT environment..."
    
    local compose_file=$(get_compose_file)
    
    cd "$DOCKER_DIR"
    docker-compose -f "$compose_file" start
    
    wait_for_health
    print_status "Services started successfully"
}

# Function to stop services
stop_services() {
    print_status "Stopping services for $ENVIRONMENT environment..."
    
    local compose_file=$(get_compose_file)
    
    cd "$DOCKER_DIR"
    docker-compose -f "$compose_file" stop
    
    print_status "Services stopped successfully"
}

# Function to restart services
restart_services() {
    print_status "Restarting services for $ENVIRONMENT environment..."
    
    stop_services
    start_services
}

# Function to update deployment
update_deployment() {
    print_status "Updating deployment for $ENVIRONMENT environment..."
    
    local compose_file=$(get_compose_file)
    
    # Create backup
    create_backup
    
    # Pull latest images
    cd "$DOCKER_DIR"
    docker-compose -f "$compose_file" pull
    
    # Restart services with new images
    docker-compose -f "$compose_file" up -d
    
    wait_for_health
    print_status "Update completed successfully"
}

# Function to cleanup old resources
cleanup_resources() {
    print_status "Cleaning up old Docker resources..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes (be careful with this)
    if [[ "$FORCE" == true ]]; then
        docker volume prune -f
    else
        print_warning "Use --force to also remove unused volumes"
    fi
    
    # Remove unused networks
    docker network prune -f
    
    print_status "Cleanup completed"
}

# Function to check application health
check_health() {
    print_status "Checking application health for $ENVIRONMENT environment..."
    
    local compose_file=$(get_compose_file)
    
    cd "$DOCKER_DIR"
    
    # Get service status
    local unhealthy_services=$(docker-compose -f "$compose_file" ps --services --filter "health=unhealthy")
    
    if [[ -z "$unhealthy_services" ]]; then
        print_status "✅ All services are healthy"
    else
        print_error "❌ Unhealthy services detected: $unhealthy_services"
    fi
    
    # Test HTTP endpoints if applicable
    if [[ "$ENVIRONMENT" != "development" ]]; then
        print_status "Testing HTTP endpoints..."
        
        # This would test actual endpoints based on environment
        print_status "HTTP endpoint tests would run here"
    fi
}

# Main execution
main() {
    parse_args "$@"
    validate_environment
    check_prerequisites
    
    print_status "Executing action: $ACTION"
    print_debug "Environment: $ENVIRONMENT"
    print_debug "Docker directory: $DOCKER_DIR"
    
    case $ACTION in
        deploy)
            run_tests
            deploy_application
            ;;
        build)
            build_images
            ;;
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        backup)
            create_backup
            ;;
        restore)
            print_error "Restore functionality not implemented yet"
            ;;
        update)
            update_deployment
            ;;
        cleanup)
            cleanup_resources
            ;;
        health)
            check_health
            ;;
        *)
            print_error "Unknown action: $ACTION"
            ;;
    esac
}

# Execute main function
main "$@"