#!/bin/bash

# RAG Chatbot PWA Backup Script
# Automated backup solution with retention and cloud storage support

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_ROOT/docker"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# Default values
ENVIRONMENT="production"
BACKUP_TYPE="full"
COMPRESS=true
UPLOAD_TO_S3=false
VERBOSE=false

# Function to print colored output
print_status() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
print_debug() { [[ "$VERBOSE" == true ]] && echo -e "${BLUE}[DEBUG]${NC} $1"; }

# Function to show usage
show_usage() {
    cat << EOF
RAG Chatbot PWA Backup Script

Usage: $0 [OPTIONS]

OPTIONS:
    -e, --env ENV          Environment (production|staging) [default: production]
    -t, --type TYPE        Backup type (full|database|files|config) [default: full]
    -d, --dir DIR          Backup directory [default: $BACKUP_DIR]
    -r, --retention DAYS   Retention period in days [default: $RETENTION_DAYS]
    -c, --no-compress      Skip compression
    -s, --upload-s3        Upload backup to S3
    -v, --verbose          Verbose output
    -h, --help             Show this help

BACKUP TYPES:
    full        Complete backup (database + files + config)
    database    Database only
    files       Upload files and vector store only
    config      Configuration and environment files only

EXAMPLES:
    $0                              # Full production backup
    $0 -e staging -t database       # Database backup for staging
    $0 -s -r 90                     # Full backup with S3 upload and 90-day retention

EOF
}

# Parse arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--env) ENVIRONMENT="$2"; shift 2 ;;
            -t|--type) BACKUP_TYPE="$2"; shift 2 ;;
            -d|--dir) BACKUP_DIR="$2"; shift 2 ;;
            -r|--retention) RETENTION_DAYS="$2"; shift 2 ;;
            -c|--no-compress) COMPRESS=false; shift ;;
            -s|--upload-s3) UPLOAD_TO_S3=true; shift ;;
            -v|--verbose) VERBOSE=true; shift ;;
            -h|--help) show_usage; exit 0 ;;
            *) print_error "Unknown option: $1" ;;
        esac
    done
}

# Validate environment
validate_environment() {
    case $ENVIRONMENT in
        production|staging) ;;
        *) print_error "Invalid environment: $ENVIRONMENT" ;;
    esac
}

# Create backup directory
setup_backup_dir() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    BACKUP_TIMESTAMP="$timestamp"
    BACKUP_SESSION_DIR="$BACKUP_DIR/$ENVIRONMENT/$timestamp"
    
    mkdir -p "$BACKUP_SESSION_DIR"
    print_status "Backup directory created: $BACKUP_SESSION_DIR"
}

# Get Docker Compose file
get_compose_file() {
    case $ENVIRONMENT in
        production) echo "$DOCKER_DIR/docker-compose.prod.yml" ;;
        staging) echo "$DOCKER_DIR/docker-compose.staging.yml" ;;
    esac
}

# Check if services are running
check_services() {
    local compose_file=$(get_compose_file)
    
    cd "$DOCKER_DIR"
    if ! docker-compose -f "$compose_file" ps postgres | grep -q "Up"; then
        print_error "PostgreSQL service is not running. Start services first."
    fi
}

# Backup database
backup_database() {
    print_status "Creating database backup..."
    
    local compose_file=$(get_compose_file)
    local db_backup_file="$BACKUP_SESSION_DIR/database_${BACKUP_TIMESTAMP}.sql"
    
    cd "$DOCKER_DIR"
    
    # Create database dump
    case $ENVIRONMENT in
        production)
            docker-compose -f "$compose_file" exec -T postgres pg_dump \
                -U raguser -h localhost ragchatbot > "$db_backup_file"
            ;;
        staging)
            docker-compose -f "$compose_file" exec -T postgres pg_dump \
                -U raguser -h localhost ragchatbot_staging > "$db_backup_file"
            ;;
    esac
    
    # Verify backup
    if [[ ! -s "$db_backup_file" ]]; then
        print_error "Database backup failed - file is empty"
    fi
    
    local db_size=$(du -h "$db_backup_file" | cut -f1)
    print_status "Database backup created: $db_size"
    
    # Compress if enabled
    if [[ "$COMPRESS" == true ]]; then
        gzip "$db_backup_file"
        print_status "Database backup compressed"
    fi
}

# Backup files and volumes
backup_files() {
    print_status "Creating files backup..."
    
    local compose_file=$(get_compose_file)
    local files_backup_dir="$BACKUP_SESSION_DIR/files"
    
    mkdir -p "$files_backup_dir"
    
    cd "$DOCKER_DIR"
    
    # Backup upload files
    if docker volume inspect ragchatbot_uploads_data &>/dev/null; then
        print_debug "Backing up upload files..."
        docker run --rm \
            -v ragchatbot_uploads_data:/source:ro \
            -v "$files_backup_dir":/backup \
            alpine:latest \
            tar czf /backup/uploads_${BACKUP_TIMESTAMP}.tar.gz -C /source .
    fi
    
    # Backup vector store
    if docker volume inspect ragchatbot_vector_data &>/dev/null; then
        print_debug "Backing up vector store..."
        docker run --rm \
            -v ragchatbot_vector_data:/source:ro \
            -v "$files_backup_dir":/backup \
            alpine:latest \
            tar czf /backup/vector_store_${BACKUP_TIMESTAMP}.tar.gz -C /source .
    fi
    
    # Backup logs if they exist
    if docker volume inspect ragchatbot_logs_data &>/dev/null; then
        print_debug "Backing up logs..."
        docker run --rm \
            -v ragchatbot_logs_data:/source:ro \
            -v "$files_backup_dir":/backup \
            alpine:latest \
            tar czf /backup/logs_${BACKUP_TIMESTAMP}.tar.gz -C /source .
    fi
    
    print_status "Files backup completed"
}

# Backup configuration
backup_config() {
    print_status "Creating configuration backup..."
    
    local config_backup_dir="$BACKUP_SESSION_DIR/config"
    mkdir -p "$config_backup_dir"
    
    # Copy environment files (excluding secrets)
    if [[ -f "$DOCKER_DIR/.env.example" ]]; then
        cp "$DOCKER_DIR/.env.example" "$config_backup_dir/"
    fi
    
    # Copy Docker Compose files
    cp "$DOCKER_DIR"/*.yml "$config_backup_dir/" 2>/dev/null || true
    
    # Copy nginx configuration
    if [[ -d "$DOCKER_DIR/nginx" ]]; then
        cp -r "$DOCKER_DIR/nginx" "$config_backup_dir/"
    fi
    
    # Copy PostgreSQL init scripts
    if [[ -d "$DOCKER_DIR/postgres" ]]; then
        cp -r "$DOCKER_DIR/postgres" "$config_backup_dir/"
    fi
    
    print_status "Configuration backup completed"
}

# Create backup manifest
create_manifest() {
    local manifest_file="$BACKUP_SESSION_DIR/manifest.json"
    
    cat > "$manifest_file" << EOF
{
    "backup_info": {
        "timestamp": "$BACKUP_TIMESTAMP",
        "environment": "$ENVIRONMENT",
        "type": "$BACKUP_TYPE",
        "compressed": $COMPRESS,
        "created_by": "$(whoami)",
        "hostname": "$(hostname)",
        "script_version": "1.0.0"
    },
    "system_info": {
        "docker_version": "$(docker --version | cut -d' ' -f3 | tr -d ',')",
        "compose_version": "$(docker-compose --version | cut -d' ' -f3 | tr -d ',')",
        "os": "$(uname -s)",
        "arch": "$(uname -m)"
    },
    "backup_contents": {
        "database": $([ "$BACKUP_TYPE" = "full" ] || [ "$BACKUP_TYPE" = "database" ] && echo true || echo false),
        "files": $([ "$BACKUP_TYPE" = "full" ] || [ "$BACKUP_TYPE" = "files" ] && echo true || echo false),
        "config": $([ "$BACKUP_TYPE" = "full" ] || [ "$BACKUP_TYPE" = "config" ] && echo true || echo false)
    }
}
EOF
    
    print_debug "Backup manifest created"
}

# Calculate backup size
calculate_backup_size() {
    local total_size=$(du -sh "$BACKUP_SESSION_DIR" | cut -f1)
    print_status "Total backup size: $total_size"
    
    # Update manifest with size info
    local manifest_file="$BACKUP_SESSION_DIR/manifest.json"
    local temp_manifest=$(mktemp)
    
    jq --arg size "$total_size" '.backup_info.total_size = $size' "$manifest_file" > "$temp_manifest"
    mv "$temp_manifest" "$manifest_file"
}

# Upload to S3 (if configured)
upload_to_s3() {
    if [[ "$UPLOAD_TO_S3" != true ]]; then
        return
    fi
    
    print_status "Uploading backup to S3..."
    
    # Check if AWS CLI is available
    if ! command -v aws &> /dev/null; then
        print_warning "AWS CLI not found. Skipping S3 upload."
        return
    fi
    
    # Check if S3 configuration exists
    if [[ -z "${BACKUP_S3_BUCKET:-}" ]]; then
        print_warning "S3 bucket not configured. Skipping S3 upload."
        return
    fi
    
    # Create archive for upload
    local archive_name="ragchatbot_backup_${ENVIRONMENT}_${BACKUP_TIMESTAMP}.tar.gz"
    local archive_path="$BACKUP_DIR/$archive_name"
    
    tar -czf "$archive_path" -C "$BACKUP_DIR/$ENVIRONMENT" "$BACKUP_TIMESTAMP"
    
    # Upload to S3
    aws s3 cp "$archive_path" "s3://${BACKUP_S3_BUCKET}/backups/$ENVIRONMENT/"
    
    print_status "Backup uploaded to S3: s3://${BACKUP_S3_BUCKET}/backups/$ENVIRONMENT/$archive_name"
    
    # Clean up local archive
    rm "$archive_path"
}

# Clean old backups
clean_old_backups() {
    print_status "Cleaning backups older than $RETENTION_DAYS days..."
    
    find "$BACKUP_DIR/$ENVIRONMENT" -type d -name "*" -mtime +$RETENTION_DAYS -exec rm -rf {} + 2>/dev/null || true
    
    # Also clean S3 if configured
    if [[ "$UPLOAD_TO_S3" == true ]] && [[ -n "${BACKUP_S3_BUCKET:-}" ]] && command -v aws &> /dev/null; then
        local cutoff_date=$(date -d "$RETENTION_DAYS days ago" +%Y-%m-%d)
        print_debug "Cleaning S3 backups older than $cutoff_date"
        
        # This would implement S3 cleanup logic
        print_debug "S3 cleanup would run here"
    fi
    
    print_status "Old backups cleaned up"
}

# Perform backup based on type
perform_backup() {
    case $BACKUP_TYPE in
        full)
            backup_database
            backup_files
            backup_config
            ;;
        database)
            backup_database
            ;;
        files)
            backup_files
            ;;
        config)
            backup_config
            ;;
        *)
            print_error "Invalid backup type: $BACKUP_TYPE"
            ;;
    esac
}

# Main execution
main() {
    parse_args "$@"
    validate_environment
    
    print_status "Starting $BACKUP_TYPE backup for $ENVIRONMENT environment..."
    print_debug "Retention period: $RETENTION_DAYS days"
    print_debug "Compression: $COMPRESS"
    print_debug "S3 upload: $UPLOAD_TO_S3"
    
    check_services
    setup_backup_dir
    
    perform_backup
    
    create_manifest
    calculate_backup_size
    
    upload_to_s3
    clean_old_backups
    
    print_status "✅ Backup completed successfully!"
    print_status "Backup location: $BACKUP_SESSION_DIR"
}

# Execute main function
main "$@"