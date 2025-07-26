#!/bin/bash

# RAG Chatbot PWA Deployment Script
# This script sets up the complete development environment

set -e

echo "🚀 RAG Chatbot PWA Deployment Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if running on Windows (Git Bash/WSL)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    IS_WINDOWS=true
else
    IS_WINDOWS=false
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    local missing_deps=()
    
    if ! command_exists node; then
        missing_deps+=("Node.js 18+")
    fi
    
    if ! command_exists python; then
        missing_deps+=("Python 3.9+")
    fi
    
    if ! command_exists docker; then
        missing_deps+=("Docker")
    fi
    
    if ! command_exists docker-compose; then
        missing_deps+=("Docker Compose")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies:"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done
        echo ""
        echo "Please install the missing dependencies and run this script again."
        exit 1
    fi
    
    print_success "All prerequisites are installed"
}

# Setup environment files
setup_environment() {
    print_status "Setting up environment files..."
    
    # Backend environment
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Created backend .env file from example"
        else
            print_warning "No .env.example found, creating basic .env file"
            cat > .env << EOF
# Database
DATABASE_URL=postgresql://raguser:ragpass@localhost:5432/ragchatbot

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Gemini AI (replace with your API key)
GEMINI_API_KEY=your-gemini-api-key-here

# GitHub OAuth (optional)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# File Upload
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=104857600

# CORS
FRONTEND_URL=http://localhost:5173
EOF
        fi
    else
        print_warning "Backend .env file already exists"
    fi
    
    # Frontend environment
    if [ ! -f "frontend/.env" ]; then
        if [ -f "frontend/.env.example" ]; then
            cp frontend/.env.example frontend/.env
            print_success "Created frontend .env file from example"
        else
            print_warning "No frontend/.env.example found, creating basic .env file"
            cat > frontend/.env << EOF
VITE_API_URL=http://localhost:5000
VITE_APP_NAME=RAG Chatbot PWA
EOF
        fi
    else
        print_warning "Frontend .env file already exists"
    fi
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Backend dependencies
    print_status "Installing Python dependencies..."
    cd backend
    
    if [ ! -d "venv" ]; then
        python -m venv venv
        print_success "Created Python virtual environment"
    fi
    
    # Activate virtual environment
    if [ "$IS_WINDOWS" = true ]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    
    pip install -r requirements.txt
    print_success "Installed Python dependencies"
    
    cd ..
    
    # Frontend dependencies
    print_status "Installing Node.js dependencies..."
    cd frontend
    npm install
    print_success "Installed Node.js dependencies"
    cd ..
}

# Setup database
setup_database() {
    print_status "Setting up database..."
    
    # Check if PostgreSQL is running in Docker
    if docker ps | grep -q postgres; then
        print_success "PostgreSQL container is already running"
    else
        print_status "Starting PostgreSQL container..."
        docker run -d \
            --name ragchatbot-postgres \
            -e POSTGRES_DB=ragchatbot \
            -e POSTGRES_USER=raguser \
            -e POSTGRES_PASSWORD=ragpass \
            -p 5432:5432 \
            postgres:13
        
        # Wait for PostgreSQL to be ready
        print_status "Waiting for PostgreSQL to be ready..."
        sleep 10
        print_success "PostgreSQL container started"
    fi
    
    # Check if Redis is running in Docker
    if docker ps | grep -q redis; then
        print_success "Redis container is already running"
    else
        print_status "Starting Redis container..."
        docker run -d \
            --name ragchatbot-redis \
            -p 6379:6379 \
            redis:6-alpine
        print_success "Redis container started"
    fi
}

# Initialize database
init_database() {
    print_status "Initializing database..."
    
    cd backend
    
    # Activate virtual environment
    if [ "$IS_WINDOWS" = true ]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    
    # Initialize database
    flask db upgrade
    print_success "Database initialized"
    
    cd ..
}

# Start services
start_services() {
    print_status "Starting services..."
    
    # Start Celery worker in background
    cd backend
    if [ "$IS_WINDOWS" = true ]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    
    print_status "Starting Celery worker..."
    celery -A app.celery worker --loglevel=info &
    CELERY_PID=$!
    print_success "Celery worker started (PID: $CELERY_PID)"
    
    # Start Flask backend in background
    print_status "Starting Flask backend..."
    python app.py &
    FLASK_PID=$!
    print_success "Flask backend started (PID: $FLASK_PID)"
    
    cd ..
    
    # Start React frontend
    print_status "Starting React frontend..."
    cd frontend
    npm run dev &
    VITE_PID=$!
    print_success "React frontend started (PID: $VITE_PID)"
    
    cd ..
    
    # Save PIDs for cleanup
    echo "$CELERY_PID" > .celery.pid
    echo "$FLASK_PID" > .flask.pid
    echo "$VITE_PID" > .vite.pid
}

# Cleanup function
cleanup() {
    print_status "Cleaning up..."
    
    if [ -f ".celery.pid" ]; then
        kill $(cat .celery.pid) 2>/dev/null || true
        rm .celery.pid
    fi
    
    if [ -f ".flask.pid" ]; then
        kill $(cat .flask.pid) 2>/dev/null || true
        rm .flask.pid
    fi
    
    if [ -f ".vite.pid" ]; then
        kill $(cat .vite.pid) 2>/dev/null || true
        rm .vite.pid
    fi
    
    print_success "Cleanup completed"
}

# Trap cleanup on script exit
trap cleanup EXIT

# Main deployment function
deploy() {
    print_status "Starting RAG Chatbot PWA deployment..."
    
    check_prerequisites
    setup_environment
    install_dependencies
    setup_database
    init_database
    start_services
    
    print_success "🎉 Deployment completed successfully!"
    echo ""
    echo "📱 Frontend: http://localhost:5173"
    echo "🔧 Backend API: http://localhost:5000"
    echo "📊 API Docs: http://localhost:5000/api/docs"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Wait for user interrupt
    wait
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "stop")
        cleanup
        ;;
    "clean")
        cleanup
        docker stop ragchatbot-postgres ragchatbot-redis 2>/dev/null || true
        docker rm ragchatbot-postgres ragchatbot-redis 2>/dev/null || true
        print_success "All services stopped and containers removed"
        ;;
    *)
        echo "Usage: $0 [deploy|stop|clean]"
        echo "  deploy: Start all services (default)"
        echo "  stop: Stop all services"
        echo "  clean: Stop and remove all containers"
        exit 1
        ;;
esac
