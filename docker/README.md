# RAG Chatbot PWA - Docker Deployment Guide

This directory contains comprehensive Docker configuration and deployment scripts for the RAG Chatbot PWA. The setup supports multiple environments with production-ready configurations, monitoring, and automated deployment workflows.

## 🏗️ Architecture Overview

The application is deployed using a microservices architecture with the following components:

- **Frontend**: React PWA served by Nginx
- **Backend**: Flask API with Gunicorn
- **Database**: PostgreSQL with optimizations
- **Cache**: Redis for session storage and caching
- **Worker**: Celery for background tasks
- **Monitoring**: Prometheus, Grafana, ELK stack
- **Reverse Proxy**: Nginx with SSL termination

## 📁 Directory Structure

```
docker/
├── .env.example                 # Environment template
├── docker-compose.prod.yml      # Production configuration
├── docker-compose.staging.yml   # Staging configuration
├── docker-compose.monitoring.yml # Enhanced monitoring setup
├── Dockerfile.backend.prod      # Production backend image
├── Dockerfile.frontend.prod     # Production frontend image
├── Dockerfile.devtools         # Development tools container
├── nginx/                      # Nginx configurations
│   ├── nginx.conf             # Production nginx config
│   └── nginx.staging.conf     # Staging nginx config
├── postgres/                  # Database initialization
│   ├── init.sql              # Production DB setup
│   └── init-staging.sql      # Staging DB setup
├── monitoring/               # Monitoring configurations
│   ├── prometheus.yml       # Prometheus config
│   └── grafana/            # Grafana dashboards
└── scripts/                # Deployment automation
    ├── deploy.sh          # Main deployment script
    └── backup.sh         # Backup automation
```

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- At least 4GB RAM
- 10GB free disk space

### 1. Environment Setup

```bash
# Copy environment template
cp docker/.env.example docker/.env

# Edit configuration (required)
nano docker/.env
```

### 2. Production Deployment

```bash
# Deploy to production
./docker/scripts/deploy.sh -e production

# Check status
./docker/scripts/deploy.sh status -e production
```

### 3. Staging Deployment

```bash
# Deploy to staging
./docker/scripts/deploy.sh -e staging

# View logs
./docker/scripts/deploy.sh logs -e staging
```

## 🔧 Environment Configurations

### Production Environment

**File**: `docker-compose.prod.yml`

Features:
- Multi-stage Docker builds
- SSL termination with Nginx
- Health checks for all services
- Resource limits and constraints
- Monitoring with Prometheus/Grafana
- Automated backups
- Security hardening

**Services**:
- `nginx` - Reverse proxy with SSL
- `backend` - Flask API (4 Gunicorn workers)
- `celery` - Background task processor
- `celery-beat` - Scheduled task runner
- `postgres` - PostgreSQL database
- `redis` - Cache and message broker
- `prometheus` - Metrics collection
- `grafana` - Monitoring dashboards

### Staging Environment

**File**: `docker-compose.staging.yml`

Features:
- Development-friendly logging
- Direct service access (ports exposed)
- Relaxed security for testing
- Debug tools container
- Enhanced CORS settings

### Development Environment

**File**: `../docker-compose.yml` (project root)

Features:
- Hot reload for development
- Volume mounts for live editing
- SQLite database (local)
- Simplified networking

## 🛠️ Deployment Scripts

### Main Deployment Script

**File**: `scripts/deploy.sh`

```bash
# Full deployment with tests and backup
./deploy.sh deploy -e production

# Build images only
./deploy.sh build -e staging

# Check application health
./deploy.sh health -e production

# View real-time logs
./deploy.sh logs -e production

# Update deployment
./deploy.sh update -e production

# Cleanup old resources
./deploy.sh cleanup --force
```

**Options**:
- `-e, --env ENV` - Target environment
- `-s, --skip-backup` - Skip database backup
- `-t, --skip-tests` - Skip test execution
- `-f, --force` - Force operations without confirmation
- `-v, --verbose` - Detailed output

### Backup Script

**File**: `scripts/backup.sh`

```bash
# Full backup (database + files + config)
./backup.sh -e production

# Database only backup
./backup.sh -t database -e production

# Backup with S3 upload
./backup.sh -s -r 90 -e production

# Staging backup
./backup.sh -e staging -v
```

**Features**:
- Multiple backup types (full, database, files, config)
- Compression and encryption
- S3 upload support
- Automated retention management
- Backup verification and manifest

## 🔍 Monitoring & Observability

### Prometheus Metrics

**Endpoint**: `http://localhost:9090`

Monitored metrics:
- HTTP request rates and response times
- Database connection pools
- Redis cache performance
- System resources (CPU, memory, disk)
- Application-specific metrics

### Grafana Dashboards

**Endpoint**: `http://localhost:3000`

Default credentials: `admin / ${GRAFANA_PASSWORD}`

Pre-configured dashboards:
- Application Overview
- Infrastructure Metrics
- Database Performance
- Error Tracking
- User Activity

### Log Aggregation (ELK Stack)

**Components**:
- **Elasticsearch**: Log storage and indexing
- **Logstash**: Log processing and enrichment
- **Kibana**: Log visualization and analysis

**Endpoint**: `http://localhost:5601`

### Distributed Tracing

**Jaeger**: `http://localhost:16686`

Traces request flows across services for performance optimization.

## 🔐 Security Configuration

### SSL/TLS Setup

1. **Let's Encrypt (Automated)**:
```bash
# Install certbot
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem docker/nginx/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem docker/nginx/ssl/key.pem
```

2. **Self-signed (Development)**:
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/nginx/ssl/key.pem \
  -out docker/nginx/ssl/cert.pem
```

### Network Security

- Internal Docker network isolation
- Rate limiting on API endpoints
- CORS configuration for frontend
- Security headers (HSTS, CSP, etc.)

### Secrets Management

- Environment variables for sensitive data
- Docker secrets for production
- Encrypted backup storage
- Regular secret rotation

## 🧪 Health Checks & Testing

### Health Check Endpoints

- **Application**: `GET /health`
- **Database**: `GET /health/db`
- **Cache**: `GET /health/redis`
- **Nginx Status**: `GET /nginx_status`

### Automated Testing

```bash
# Run all tests before deployment
./deploy.sh deploy -e staging

# Run specific test suites
docker-compose -f docker-compose.staging.yml run --rm backend pytest tests/

# Frontend tests
docker-compose -f docker-compose.staging.yml run --rm frontend npm test
```

## 📊 Performance Tuning

### Database Optimization

PostgreSQL configuration in `postgres/init.sql`:
- Connection pooling
- Memory settings based on available RAM
- Index optimization
- Query performance monitoring

### Application Scaling

**Horizontal Scaling**:
```bash
# Scale backend workers
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Scale Celery workers
docker-compose -f docker-compose.prod.yml up -d --scale celery=4
```

**Vertical Scaling**:
- Adjust resource limits in compose files
- Optimize Gunicorn worker settings
- Configure Redis memory limits

### Caching Strategy

- Application-level caching with Redis
- Nginx static file caching
- Database query result caching
- CDN integration for static assets

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Production
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          ./docker/scripts/deploy.sh deploy -e production -t
```

### GitLab CI Example

```yaml
deploy_production:
  stage: deploy
  script:
    - ./docker/scripts/deploy.sh deploy -e production
  only:
    - main
```

## 🛠️ Troubleshooting

### Common Issues

1. **Services not starting**:
```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# View service logs
docker-compose -f docker-compose.prod.yml logs backend

# Check health status
curl http://localhost/health
```

2. **Database connection issues**:
```bash
# Check PostgreSQL logs
docker-compose -f docker-compose.prod.yml logs postgres

# Test database connection
docker-compose -f docker-compose.prod.yml exec backend python -c "from app import db; print(db.engine.execute('SELECT 1').scalar())"
```

3. **High memory usage**:
```bash
# Monitor resource usage
docker stats

# Check for memory leaks
docker-compose -f docker-compose.prod.yml exec backend ps aux
```

### Development Tools

**Access development container**:
```bash
docker-compose -f docker-compose.staging.yml run --rm devtools bash
```

**Available tools**:
- `pgcli` - PostgreSQL client
- `redis-cli` - Redis client
- `ipython` - Enhanced Python shell
- `jupyter` - Jupyter notebooks
- Code quality tools (black, flake8, mypy)

### Log Analysis

**View application logs**:
```bash
# Real-time logs
./deploy.sh logs -e production

# Specific service logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Error logs only
docker-compose -f docker-compose.prod.yml logs backend 2>&1 | grep ERROR
```

## 📚 Additional Resources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Nginx Configuration Guide](https://nginx.org/en/docs/beginners_guide.html)
- [Prometheus Monitoring](https://prometheus.io/docs/guides/getting-started/)
- [Redis Optimization](https://redis.io/topics/memory-optimization)

## 🤝 Contributing

When contributing to the Docker configuration:

1. Test changes in staging environment first
2. Update documentation for any new services
3. Ensure backward compatibility
4. Add health checks for new services
5. Update monitoring configuration

## 📄 License

This Docker configuration is part of the RAG Chatbot PWA project and follows the same license terms.