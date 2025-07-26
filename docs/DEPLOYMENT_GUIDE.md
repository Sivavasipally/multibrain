# RAG Chatbot Deployment Guide

## 🎯 **Overview**

This guide provides comprehensive instructions for deploying the RAG Chatbot application in various environments, from local development to production cloud deployments.

---

## 🏠 **Local Development Setup**

### **Prerequisites**
- Python 3.10+ (recommended 3.11)
- Node.js 16+ (for frontend)
- Git
- 4GB+ RAM
- 10GB+ free disk space

### **Quick Start**

#### **1. Clone and Setup**
```bash
# Clone repository
git clone <repository-url>
cd myrag

# Backend setup
cd backend
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment configuration
cp .env.template .env
# Edit .env with your settings
```

#### **2. Database Initialization**
```bash
# Create database tables
python -c "from app_local import app, db; app.app_context().push(); db.create_all(); print('Database created successfully')"

# Verify setup
python test_all_fixes.py
```

#### **3. Start Services**
```bash
# Terminal 1: Backend
cd backend
python app_local.py

# Terminal 2: Frontend (if applicable)
cd frontend
npm install
npm run dev
```

### **Environment Configuration (.env)**
```bash
# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-here
SECRET_KEY=your-flask-secret-key-here

# Database
DATABASE_URL=sqlite:///ragchatbot.db

# File Upload
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=104857600

# AI Services (Optional)
GEMINI_API_KEY=your-gemini-api-key-here
OPENAI_API_KEY=your-openai-api-key-here

# Development
FLASK_ENV=development
FLASK_DEBUG=false
```

---

## 🐳 **Docker Deployment**

### **Docker Setup**

#### **Backend Dockerfile**
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads vector_stores instance

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app_local:app"]
```

#### **Frontend Dockerfile**
```dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### **Docker Compose**
```yaml
version: '3.8'

services:
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/ragchatbot
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./data:/app/instance
      - ./uploads:/app/uploads
      - ./vector_stores:/app/vector_stores
    depends_on:
      - db
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=ragchatbot
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  postgres_data:
```

#### **Deploy with Docker Compose**
```bash
# Create environment file
cp .env.template .env
# Edit .env with production values

# Build and start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

---

## ☁️ **Cloud Deployment**

### **AWS Deployment**

#### **EC2 Instance Setup**
```bash
# Launch EC2 instance (Ubuntu 22.04 LTS)
# Instance type: t3.medium or larger
# Security groups: HTTP (80), HTTPS (443), SSH (22)

# Connect to instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone and deploy
git clone <your-repo>
cd myrag
cp .env.template .env
# Edit .env with production values
docker-compose up -d
```

#### **RDS Database Setup**
```bash
# Create RDS PostgreSQL instance
# Instance class: db.t3.micro (for testing) or db.t3.small (production)
# Storage: 20GB minimum

# Update .env file
DATABASE_URL=postgresql://username:password@your-rds-endpoint:5432/ragchatbot
```

#### **S3 File Storage (Optional)**
```bash
# Create S3 bucket for file storage
aws s3 mb s3://your-ragchatbot-files

# Update environment variables
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=your-ragchatbot-files
```

### **Google Cloud Platform**

#### **App Engine Deployment**
```yaml
# app.yaml
runtime: python311

env_variables:
  JWT_SECRET_KEY: "your-secret-key"
  DATABASE_URL: "postgresql://user:pass@/dbname?host=/cloudsql/project:region:instance"
  GEMINI_API_KEY: "your-gemini-key"

automatic_scaling:
  min_instances: 1
  max_instances: 10
  target_cpu_utilization: 0.6

resources:
  cpu: 1
  memory_gb: 2
  disk_size_gb: 10
```

```bash
# Deploy to App Engine
gcloud app deploy app.yaml

# Set up Cloud SQL
gcloud sql instances create ragchatbot-db \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=us-central1

# Create database
gcloud sql databases create ragchatbot --instance=ragchatbot-db
```

### **Heroku Deployment**

#### **Heroku Setup**
```bash
# Install Heroku CLI
# Create Heroku app
heroku create your-ragchatbot-app

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set JWT_SECRET_KEY=your-secret-key
heroku config:set GEMINI_API_KEY=your-gemini-key
heroku config:set FLASK_ENV=production

# Deploy
git push heroku main

# Run database migrations
heroku run python -c "from app_local import app, db; app.app_context().push(); db.create_all()"
```

#### **Procfile**
```
web: gunicorn --bind 0.0.0.0:$PORT --workers 4 app_local:app
```

---

## 🔧 **Production Configuration**

### **Environment Variables**
```bash
# Security (REQUIRED)
JWT_SECRET_KEY=your-super-secret-jwt-key-here
SECRET_KEY=your-flask-secret-key-here

# Database (REQUIRED)
DATABASE_URL=postgresql://user:password@host:port/database

# AI Services (OPTIONAL)
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key

# File Storage
UPLOAD_FOLDER=/app/uploads
MAX_CONTENT_LENGTH=104857600

# Performance
WORKERS=4
TIMEOUT=120
CACHE_TYPE=redis
CACHE_REDIS_URL=redis://localhost:6379/0

# Monitoring
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO

# Production Settings
FLASK_ENV=production
FLASK_DEBUG=false
```

### **Nginx Configuration**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # File Upload Size
    client_max_body_size 100M;

    # Frontend
    location / {
        root /var/www/ragchatbot/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    # Static files
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### **Systemd Service**
```ini
# /etc/systemd/system/ragchatbot.service
[Unit]
Description=RAG Chatbot Application
After=network.target

[Service]
Type=exec
User=ragchatbot
Group=ragchatbot
WorkingDirectory=/app
Environment=PATH=/app/venv/bin
EnvironmentFile=/app/.env
ExecStart=/app/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 app_local:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable ragchatbot
sudo systemctl start ragchatbot
sudo systemctl status ragchatbot
```

---

## 📊 **Monitoring & Logging**

### **Application Monitoring**
```python
# monitoring.py
import logging
from flask import request
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/ragchatbot/app.log'),
        logging.StreamHandler()
    ]
)

@app.before_request
def log_request_info():
    logger.info('Request: %s %s', request.method, request.url)
    request.start_time = time.time()

@app.after_request
def log_response_info(response):
    duration = time.time() - request.start_time
    logger.info('Response: %s - %s - %.3fs', 
                response.status_code, request.url, duration)
    return response
```

### **Health Checks**
```bash
# Health check script
#!/bin/bash
HEALTH_URL="http://localhost:5000/api/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -eq 200 ]; then
    echo "Application is healthy"
    exit 0
else
    echo "Application is unhealthy (HTTP $RESPONSE)"
    exit 1
fi
```

### **Log Rotation**
```bash
# /etc/logrotate.d/ragchatbot
/var/log/ragchatbot/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ragchatbot ragchatbot
    postrotate
        systemctl reload ragchatbot
    endscript
}
```

---

## 🔒 **Security Considerations**

### **SSL/TLS Setup**
```bash
# Let's Encrypt with Certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
sudo certbot renew --dry-run
```

### **Firewall Configuration**
```bash
# UFW (Ubuntu)
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw status
```

### **Database Security**
```bash
# PostgreSQL security
sudo -u postgres psql
\password postgres
CREATE USER ragchatbot WITH PASSWORD 'secure_password';
CREATE DATABASE ragchatbot OWNER ragchatbot;
GRANT ALL PRIVILEGES ON DATABASE ragchatbot TO ragchatbot;
```

---

## 🚀 **Performance Optimization**

### **Database Optimization**
```sql
-- Create indexes for better performance
CREATE INDEX idx_contexts_user_id ON contexts(user_id);
CREATE INDEX idx_documents_context_id ON documents(context_id);
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_text_chunks_context_id ON text_chunks(context_id);
```

### **Caching Configuration**
```python
# Redis caching
CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0',
    'CACHE_DEFAULT_TIMEOUT': 300
}
```

### **Load Balancing**
```nginx
upstream ragchatbot_backend {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
}

server {
    location /api/ {
        proxy_pass http://ragchatbot_backend;
    }
}
```

---

## 🔄 **Backup & Recovery**

### **Database Backup**
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="ragchatbot"

# Create backup
pg_dump $DB_NAME > $BACKUP_DIR/ragchatbot_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/ragchatbot_$DATE.sql

# Remove backups older than 30 days
find $BACKUP_DIR -name "ragchatbot_*.sql.gz" -mtime +30 -delete

echo "Backup completed: ragchatbot_$DATE.sql.gz"
```

### **File Backup**
```bash
#!/bin/bash
# Backup uploads and vector stores
tar -czf /backups/files_$(date +%Y%m%d).tar.gz uploads/ vector_stores/
```

---

## 📋 **Deployment Checklist**

### **Pre-Deployment**
- [ ] Environment variables configured
- [ ] Database connection tested
- [ ] SSL certificates installed
- [ ] Firewall rules configured
- [ ] Backup strategy implemented
- [ ] Monitoring setup complete

### **Post-Deployment**
- [ ] Health checks passing
- [ ] Application accessible
- [ ] File uploads working
- [ ] Chat functionality tested
- [ ] Performance monitoring active
- [ ] Log rotation configured

---

**Deployment Guide Version**: 1.0  
**Last Updated**: 2024-01-01  
**Supported Platforms**: AWS, GCP, Heroku, Docker, Ubuntu/CentOS
