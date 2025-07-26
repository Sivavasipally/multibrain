#!/bin/bash

# RAG Chatbot PWA Production Deployment Script
# This script deploys the application to production using Docker Compose

set -e

echo "🚀 RAG Chatbot PWA Production Deployment"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root for security reasons"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    local missing_deps=()
    
    if ! command -v docker &> /dev/null; then
        missing_deps+=("Docker")
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        missing_deps+=("Docker Compose")
    fi
    
    if ! command -v openssl &> /dev/null; then
        missing_deps+=("OpenSSL")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies:"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done
        exit 1
    fi
    
    print_success "All prerequisites are installed"
}

# Setup environment
setup_environment() {
    print_status "Setting up production environment..."
    
    if [ ! -f ".env.prod" ]; then
        if [ -f ".env.prod.example" ]; then
            cp .env.prod.example .env.prod
            print_warning "Created .env.prod from example. Please edit it with your actual values."
            print_warning "Deployment will continue in 10 seconds. Press Ctrl+C to abort and edit .env.prod first."
            sleep 10
        else
            print_error "No .env.prod.example found. Cannot create production environment file."
            exit 1
        fi
    fi
    
    # Source the environment file
    set -a
    source .env.prod
    set +a
    
    print_success "Environment configuration loaded"
}

# Generate SSL certificates if they don't exist
setup_ssl() {
    print_status "Setting up SSL certificates..."
    
    mkdir -p docker/nginx/ssl
    
    if [ ! -f "docker/nginx/ssl/cert.pem" ] || [ ! -f "docker/nginx/ssl/key.pem" ]; then
        print_warning "SSL certificates not found. Generating self-signed certificates..."
        print_warning "For production, replace these with certificates from a trusted CA."
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout docker/nginx/ssl/key.pem \
            -out docker/nginx/ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        
        print_success "Self-signed SSL certificates generated"
    else
        print_success "SSL certificates found"
    fi
}

# Setup monitoring
setup_monitoring() {
    print_status "Setting up monitoring configuration..."
    
    mkdir -p docker/monitoring/grafana/{dashboards,datasources}
    mkdir -p docker/monitoring
    
    # Create Prometheus configuration
    cat > docker/monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'ragchatbot-backend'
    static_configs:
      - targets: ['ragchatbot-backend:5000']
    metrics_path: '/metrics'

  - job_name: 'nginx'
    static_configs:
      - targets: ['ragchatbot-nginx:8080']
    metrics_path: '/nginx_status'

  - job_name: 'postgres'
    static_configs:
      - targets: ['ragchatbot-postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['ragchatbot-redis:6379']
EOF

    # Create Grafana datasource configuration
    cat > docker/monitoring/grafana/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    print_success "Monitoring configuration created"
}

# Build and deploy
deploy() {
    print_status "Building and deploying application..."
    
    # Pull latest images
    docker-compose -f docker/docker-compose.prod.yml pull
    
    # Build custom images
    docker-compose -f docker/docker-compose.prod.yml build --no-cache
    
    # Start services
    docker-compose -f docker/docker-compose.prod.yml up -d
    
    print_success "Application deployed successfully"
}

# Wait for services to be healthy
wait_for_services() {
    print_status "Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f docker/docker-compose.prod.yml ps | grep -q "healthy"; then
            print_success "Services are healthy"
            return 0
        fi
        
        print_status "Attempt $attempt/$max_attempts - waiting for services..."
        sleep 10
        ((attempt++))
    done
    
    print_error "Services failed to become healthy within timeout"
    return 1
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    docker-compose -f docker/docker-compose.prod.yml exec -T backend flask db upgrade
    
    print_success "Database migrations completed"
}

# Setup backup
setup_backup() {
    print_status "Setting up backup system..."
    
    # Create backup script
    cat > scripts/backup.sh << 'EOF'
#!/bin/bash

# Backup script for RAG Chatbot PWA
BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup database
docker-compose -f docker/docker-compose.prod.yml exec -T postgres pg_dump -U raguser ragchatbot > "$BACKUP_DIR/database.sql"

# Backup uploads
docker cp ragchatbot-backend:/app/uploads "$BACKUP_DIR/"

# Backup vector store
docker cp ragchatbot-backend:/app/vector_store "$BACKUP_DIR/"

# Compress backup
tar -czf "$BACKUP_DIR.tar.gz" -C "$(dirname "$BACKUP_DIR")" "$(basename "$BACKUP_DIR")"
rm -rf "$BACKUP_DIR"

echo "Backup completed: $BACKUP_DIR.tar.gz"
EOF

    chmod +x scripts/backup.sh
    
    # Setup cron job for daily backups
    (crontab -l 2>/dev/null; echo "0 2 * * * $(pwd)/scripts/backup.sh") | crontab -
    
    print_success "Backup system configured"
}

# Show deployment information
show_info() {
    print_success "🎉 Production deployment completed!"
    echo ""
    echo "📱 Application: https://your-domain.com"
    echo "🔧 API: https://your-domain.com/api"
    echo "📊 Monitoring: http://your-server:3000 (Grafana)"
    echo "📈 Metrics: http://your-server:9090 (Prometheus)"
    echo ""
    echo "🔍 Check service status:"
    echo "  docker-compose -f docker/docker-compose.prod.yml ps"
    echo ""
    echo "📋 View logs:"
    echo "  docker-compose -f docker/docker-compose.prod.yml logs -f [service]"
    echo ""
    echo "🛑 Stop services:"
    echo "  docker-compose -f docker/docker-compose.prod.yml down"
    echo ""
    echo "🔄 Update deployment:"
    echo "  ./scripts/deploy-prod.sh update"
    echo ""
    
    if [ -f ".env.prod" ]; then
        print_warning "Remember to:"
        print_warning "1. Update .env.prod with your actual values"
        print_warning "2. Replace self-signed SSL certificates with trusted ones"
        print_warning "3. Configure your domain DNS to point to this server"
        print_warning "4. Set up proper firewall rules"
    fi
}

# Update deployment
update_deployment() {
    print_status "Updating production deployment..."
    
    # Pull latest code (if using git)
    if [ -d ".git" ]; then
        git pull origin main
    fi
    
    # Rebuild and restart services
    docker-compose -f docker/docker-compose.prod.yml build --no-cache
    docker-compose -f docker/docker-compose.prod.yml up -d
    
    # Run migrations
    run_migrations
    
    print_success "Deployment updated successfully"
}

# Cleanup old images and containers
cleanup() {
    print_status "Cleaning up old Docker images and containers..."
    
    docker system prune -f
    docker image prune -f
    
    print_success "Cleanup completed"
}

# Main deployment function
main_deploy() {
    check_root
    check_prerequisites
    setup_environment
    setup_ssl
    setup_monitoring
    deploy
    wait_for_services
    run_migrations
    setup_backup
    show_info
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy")
        main_deploy
        ;;
    "update")
        update_deployment
        ;;
    "cleanup")
        cleanup
        ;;
    "backup")
        ./scripts/backup.sh
        ;;
    "logs")
        docker-compose -f docker/docker-compose.prod.yml logs -f "${2:-}"
        ;;
    "status")
        docker-compose -f docker/docker-compose.prod.yml ps
        ;;
    "stop")
        docker-compose -f docker/docker-compose.prod.yml down
        ;;
    "restart")
        docker-compose -f docker/docker-compose.prod.yml restart "${2:-}"
        ;;
    *)
        echo "Usage: $0 [deploy|update|cleanup|backup|logs|status|stop|restart]"
        echo ""
        echo "Commands:"
        echo "  deploy    Full production deployment (default)"
        echo "  update    Update existing deployment"
        echo "  cleanup   Clean up old Docker images"
        echo "  backup    Run backup manually"
        echo "  logs      View service logs"
        echo "  status    Show service status"
        echo "  stop      Stop all services"
        echo "  restart   Restart services"
        exit 1
        ;;
esac
