# 🤖 RAG Chatbot PWA - Comprehensive Documentation

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-19+-blue.svg)](https://reactjs.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

A sophisticated AI-powered Progressive Web App (PWA) that combines document retrieval with large language models to provide contextually accurate responses based on uploaded documents, repositories, and databases.

---

## 📚 **Table of Contents**

- [🎯 Quick Start](#-quick-start)
- [✨ Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [🗃️ Database Structure](#️-database-structure)
- [🔌 API Reference](#-api-reference)
- [📱 Application Logic](#-application-logic)
- [🛠️ Installation & Setup](#️-installation--setup)
- [🔧 Configuration](#-configuration)
- [🧪 Testing](#-testing)
- [🚀 Deployment](#-deployment)
- [📊 Monitoring](#-monitoring)
- [🔒 Security](#-security)
- [🔧 Database Management](#-database-management)
- [🤝 Contributing](#-contributing)

---

## 🎯 **Quick Start**

### **Option 1: Local Development (Recommended)**
```bash
# 1. Clone repository
git clone <repository-url>
cd multibrain/backend

# 2. Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.template .env
# Edit .env with your GEMINI_API_KEY

# 4. Initialize database
python reset_database.py  # Creates fresh database with sample users

# 5. Start application
python app_local.py
```

### **Option 2: Docker Setup**
```bash
# Using provided scripts
./scripts/deploy-local.ps1     # Windows
./scripts/deploy-local.sh      # Linux/Mac

# Or manual Docker
docker-compose up -d
```

🎉 **Application running at**: 
- **Backend**: `http://localhost:5000`
- **Frontend**: `http://localhost:5173`

### **Default Login Accounts** (after reset_database.py):
- **Admin**: `admin` / `admin123`
- **Test User**: `testuser` / `test123`
- **Demo User**: `demo` / `demo123`

---

## ✨ **Features**

### **🔐 Core Capabilities**
- ✅ **Multi-Source Document Processing**: PDF, Word, Excel, code files, archives
- ✅ **Repository Integration**: GitHub/Bitbucket clone and analysis
- ✅ **Database Connectivity**: SQLite, MySQL, PostgreSQL, MongoDB, Cassandra
- ✅ **Intelligent Chunking**: Language-aware text processing with Tree-sitter
- ✅ **Vector Search**: FAISS-powered semantic similarity search
- ✅ **Multi-Model AI**: Google Gemini 2.0 Flash and text-embedding-004
- ✅ **Real-time Chat**: Streaming responses with citations
- ✅ **Context Management**: Organize knowledge bases by source type
- ✅ **Progressive Web App**: Installable, offline-capable interface

### **🚀 Advanced Features**
- ✅ **Admin Dashboard**: System monitoring, user management, analytics
- ✅ **Performance Monitoring**: Request tracking, system metrics, alerts
- ✅ **Security Middleware**: Rate limiting, IP blocking, security headers
- ✅ **Comprehensive Logging**: Structured logging with rotation
- ✅ **Drag & Drop Upload**: Intuitive file upload with preview
- ✅ **Citation Generation**: Automatic source attribution with scores
- ✅ **Context Reprocessing**: Refresh knowledge bases on demand
- ✅ **Health Monitoring**: Application and service health checks

### **📋 Recently Implemented**
- ✅ Fixed all critical blueprint registration issues
- ✅ Enhanced document processing (PDF, DOCX, Excel parsing)
- ✅ Complete admin authentication system
- ✅ Security middleware with rate limiting
- ✅ Comprehensive logging infrastructure
- ✅ Database management tools and migrations
- ✅ Repository processing service
- ✅ Database connectivity service

---

## 🏗️ **Architecture**

### **System Overview**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Storage       │
│   React PWA     │◄──►│   Flask API     │◄──►│   SQLite/PG     │
│   Port: 5173    │    │   Port: 5000    │    │   + FAISS       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          │                       ▼                       ▼
          │              ┌─────────────────┐    ┌─────────────────┐
          │              │   AI Services   │    │  External APIs  │
          └──────────────┤   Gemini 2.0    │    │  GitHub/DB APIs │
                         └─────────────────┘    └─────────────────┘
```

### **Technology Stack**

#### **Backend (Flask API)**
- **Framework**: Flask 3.0+ with blueprints
- **Database**: SQLAlchemy 2.0+ ORM
- **Authentication**: JWT with role-based access
- **AI Integration**: Google Gemini 2.0 Flash
- **Vector Search**: FAISS with embeddings
- **Security**: Custom middleware with rate limiting
- **Monitoring**: Structured logging and metrics

#### **Frontend (React PWA)**
- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite with hot reload
- **UI Library**: Material-UI (MUI) v7
- **State Management**: Context API + custom hooks
- **PWA Features**: Service worker, offline storage
- **Drag & Drop**: react-dropzone integration

#### **Data Processing**
- **Vector Embeddings**: text-embedding-004 (768-dim)
- **Similarity Search**: FAISS IndexFlatIP
- **Text Extraction**: PyMuPDF, python-docx, openpyxl
- **Code Analysis**: Language-aware chunking
- **Repository Cloning**: GitPython + subprocess fallback

---

## 🗃️ **Database Structure**

### **Schema Overview**
The application uses 6 main tables with full referential integrity:

```sql
-- Core Tables Structure (SQLite/PostgreSQL compatible)

TABLE users {
  id INTEGER PRIMARY KEY
  username VARCHAR(80) UNIQUE NOT NULL
  email VARCHAR(120) UNIQUE NOT NULL  
  password_hash VARCHAR(255) NOT NULL
  created_at DATETIME
  is_active BOOLEAN DEFAULT 1
  is_admin BOOLEAN DEFAULT 0  -- ✅ Recently added
  github_id VARCHAR(50) UNIQUE
  bitbucket_id VARCHAR(50) UNIQUE
}

TABLE contexts {
  id INTEGER PRIMARY KEY
  name VARCHAR(200) NOT NULL
  description TEXT
  user_id INTEGER NOT NULL REFERENCES users(id)
  created_at DATETIME
  updated_at DATETIME
  source_type VARCHAR(50) NOT NULL  -- 'files', 'repo', 'database'
  config TEXT  -- JSON configuration
  chunk_strategy VARCHAR(50) DEFAULT 'language-specific'
  embedding_model VARCHAR(100) DEFAULT 'text-embedding-004'
  status VARCHAR(20) DEFAULT 'pending'  -- 'pending', 'processing', 'ready', 'error'
  progress INTEGER DEFAULT 0  -- 0-100
  error_message TEXT
  total_chunks INTEGER DEFAULT 0
  total_tokens INTEGER DEFAULT 0
  vector_store_path VARCHAR(500)
}

TABLE documents {
  id INTEGER PRIMARY KEY
  context_id INTEGER NOT NULL REFERENCES contexts(id)
  filename VARCHAR(500) NOT NULL
  file_path VARCHAR(1000)
  file_type VARCHAR(50)  -- 'pdf', 'docx', 'code', etc.
  file_size INTEGER
  chunks_count INTEGER
  tokens_count INTEGER
  language VARCHAR(50)
  created_at DATETIME
  processed_at DATETIME
}

TABLE text_chunks {
  id INTEGER PRIMARY KEY
  context_id INTEGER NOT NULL REFERENCES contexts(id)
  file_name VARCHAR(255) NOT NULL
  chunk_index INTEGER NOT NULL
  content TEXT NOT NULL
  file_info TEXT  -- JSON metadata
  created_at DATETIME
}

TABLE chat_sessions {
  id INTEGER PRIMARY KEY
  user_id INTEGER NOT NULL REFERENCES users(id)
  title VARCHAR(200) DEFAULT 'New Chat'
  created_at DATETIME
  updated_at DATETIME
}

TABLE messages {
  id INTEGER PRIMARY KEY
  session_id INTEGER NOT NULL REFERENCES chat_sessions(id)
  role VARCHAR(20) NOT NULL  -- 'user', 'assistant'
  content TEXT NOT NULL
  context_ids TEXT  -- JSON array of context IDs
  citations TEXT  -- JSON array of citations
  tokens_used INTEGER
  model_used VARCHAR(100)
  created_at DATETIME
}
```

### **Relationships & Constraints**
- **Users** can have multiple **Contexts** and **ChatSessions**
- **Contexts** contain multiple **Documents** and **TextChunks**
- **ChatSessions** contain multiple **Messages**
- **Messages** can reference multiple **Contexts** via JSON array
- All foreign keys maintain referential integrity with CASCADE deletes

### **Database Management Tools**
```bash
# View current schema
python3 simple_schema_viewer.py

# Reset database with sample data
python3 reset_database.py

# Fix specific issues (e.g., missing columns)
python3 fix_admin_column.py

# Verify database health
python3 verify_fix.py
```

---

## 🔌 **API Reference**

### **Authentication Endpoints**

#### **POST** `/api/auth/register`
Register a new user account.
```json
{
  "username": "johndoe",
  "email": "john@example.com", 
  "password": "securepassword"
}
```
**Response**: `201` - User created with JWT token

#### **POST** `/api/auth/login`
Authenticate user and return JWT token.
```json
{
  "username": "johndoe",
  "password": "securepassword"
}
```
**Response**: `200` - JWT token and user info

#### **GET** `/api/auth/me`
Get current user information (requires JWT).
**Headers**: `Authorization: Bearer <token>`
**Response**: `200` - User profile data

### **Context Management Endpoints**

#### **GET** `/api/contexts`
List all contexts for authenticated user.
**Headers**: `Authorization: Bearer <token>`
**Response**: `200` - Array of user's contexts

#### **POST** `/api/contexts`
Create a new context.
```json
{
  "name": "My Knowledge Base",
  "description": "Company documents and policies",
  "source_type": "files",  // 'files', 'repo', 'database'
  "chunk_strategy": "language-specific",
  "embedding_model": "text-embedding-004",
  "repo_config": {  // If source_type = 'repo'
    "url": "https://github.com/user/repo",
    "branch": "main",
    "access_token": "optional_token"
  },
  "database_config": {  // If source_type = 'database'
    "type": "postgresql",
    "connection_string": "postgresql://user:pass@host:5432/db",
    "tables": ["users", "products"]
  }
}
```
**Response**: `201` - Created context object

#### **GET** `/api/contexts/{id}`
Get specific context with documents.
**Response**: `200` - Context details with document list

#### **DELETE** `/api/contexts/{id}`
Delete context and all associated data.
**Response**: `200` - Confirmation with cleanup statistics

#### **POST** `/api/contexts/{id}/reprocess`
Reprocess context (re-extract and re-embed documents).
**Response**: `200` - Reprocessing started confirmation

#### **GET** `/api/contexts/{id}/status`
Get context processing status.
**Response**: `200` - Status, progress, error info

### **File Upload Endpoints**

#### **POST** `/api/upload/files`
Upload files to a context.
**Headers**: `Authorization: Bearer <token>`
**Form Data**:
- `files`: Multiple file uploads
- `context_id`: Target context ID
**Supported Formats**: PDF, DOCX, XLSX, TXT, MD, code files, archives
**Response**: `200` - Upload confirmation with processing stats

#### **POST** `/api/upload/extract-zip`
Extract and process ZIP archive.
**Form Data**:
- `file`: ZIP file
- `context_id`: Target context ID
**Response**: `200` - Extraction confirmation

#### **GET** `/api/upload/supported-extensions`
Get list of supported file types.
**Response**: `200` - File extension categories and limits

### **Chat Endpoints**

#### **GET** `/api/chat/sessions`
Get user's chat sessions.
**Response**: `200` - Array of chat sessions

#### **POST** `/api/chat/sessions`
Create new chat session.
```json
{
  "title": "Project Discussion"
}
```
**Response**: `201` - Created session object

#### **POST** `/api/chat/query`
Send chat message with RAG processing.
```json
{
  "message": "What are the key features mentioned in the documentation?",
  "session_id": 1,
  "context_ids": [1, 2],
  "stream": false  // Set to true for streaming response
}
```
**Response**: `200` - AI response with citations

**Streaming Response** (if `stream: true`):
```
data: {"chunk": "Based on the documentation..."}
data: {"chunk": " the key features include..."}
data: {"done": true, "citations": [...]}
```

### **Admin Endpoints**

#### **GET** `/api/admin/dashboard`
Get admin dashboard overview (admin only).
**Response**: `200` - System metrics, user stats, performance data

#### **GET** `/api/admin/users`
Get user management data (admin only).
**Query Parameters**:
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20)
**Response**: `200` - Paginated user list with statistics

#### **GET** `/api/admin/contexts`
Get contexts overview for admin.
**Response**: `200` - Context statistics and recent activity

#### **POST** `/api/admin/make-admin`
Promote current user to admin (only if no admin exists).
**Response**: `200` - Admin promotion confirmation

#### **GET** `/api/admin/system/health`
Get detailed system health information.
**Response**: `200` - Health status and current alerts

#### **POST** `/api/admin/cleanup/orphaned`
Clean up orphaned data across the system.
**Response**: `200` - Cleanup statistics

### **Monitoring Endpoints**

#### **GET** `/api/health`
Basic health check.
**Response**: `200` - Application status

#### **GET** `/api/metrics`
Get system metrics (Prometheus format).
**Response**: `200` - Performance metrics

### **Error Response Format**
All endpoints return consistent error responses:
```json
{
  "error": "Description of the error",
  "code": "ERROR_CODE",
  "details": {
    "field": "specific field error"
  }
}
```

**Common HTTP Status Codes**:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized (missing/invalid JWT)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `429` - Rate Limited
- `500` - Internal Server Error

---

## 📱 **Application Logic**

### **Document Processing Pipeline**

1. **File Upload**
   - Validate file type and size (100MB limit)
   - Generate secure filename and store
   - Create Document record in database

2. **Text Extraction**
   - **PDF**: PyMuPDF with fallback to pdfplumber
   - **DOCX**: python-docx with structure preservation
   - **Excel**: openpyxl + pandas with sheet analysis
   - **Code Files**: Direct UTF-8/latin-1 reading
   - **Archives**: Automatic extraction and processing

3. **Text Chunking**
   - **Language-Specific**: Smart chunking based on file type
   - **Semantic**: Embedding-based chunk boundaries
   - **Fixed-Size**: Simple character-based chunks (1000 chars, 100 overlap)

4. **Vector Processing**
   - Generate embeddings using text-embedding-004
   - Create FAISS IndexFlatIP for cosine similarity
   - Store chunks in database with metadata
   - Update context statistics

### **RAG Query Processing**

1. **Query Reception**
   - Authenticate user and validate context access
   - Parse query and extract context IDs

2. **Retrieval Phase**
   - Generate query embedding
   - Search across selected contexts using FAISS
   - Retrieve top-k similar chunks (k=5)
   - Score and rank results

3. **Augmentation Phase**
   - Compile retrieved chunks into context
   - Add chat history for conversation continuity
   - Format prompt for LLM with system instructions

4. **Generation Phase**
   - Send augmented prompt to Gemini 2.0 Flash
   - Generate response (streaming or complete)
   - Extract citations and metadata
   - Store conversation in database

### **Context Management Logic**

#### **Context States**
- `pending` - Just created, awaiting processing
- `processing` - Files being uploaded/processed
- `ready` - Available for chat queries
- `error` - Processing failed

#### **Source Type Handling**
- **Files**: Direct upload and processing
- **Repository**: Clone → analyze → extract → process
- **Database**: Connect → schema discovery → data extraction

### **Security & Access Control**

#### **Authentication Flow**
1. User registers/logs in → JWT token issued
2. Token includes user ID and expiration
3. All API requests validated against JWT
4. Admin routes check `is_admin` flag

#### **Rate Limiting**
- **Default**: 1000 requests/hour per IP
- **Auth**: 10 attempts/5 minutes per IP
- **Upload**: 20 files/hour per user
- **Admin**: 100 requests/hour per user

#### **Security Middleware**
- XSS protection headers
- CSRF prevention
- Content type validation  
- Request size limits (100MB)
- Suspicious activity detection

---

## 🛠️ **Installation & Setup**

### **Prerequisites**
- **Python**: 3.10+ (3.11 recommended)
- **Node.js**: 16+ (for frontend development)
- **Memory**: 4GB+ RAM recommended
- **Storage**: 10GB+ free space
- **OS**: Windows 10+, macOS 10.15+, Linux (Ubuntu 18+)

### **Environment Setup**

#### **1. Clone Repository**
```bash
git clone <repository-url>
cd multibrain
```

#### **2. Backend Setup**
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Alternative if main requirements fail:
pip install flask flask-sqlalchemy flask-cors flask-jwt-extended
pip install requests python-docx openpyxl PyMuPDF faiss-cpu
pip install google-generativeai python-dotenv werkzeug
```

#### **3. Environment Configuration**
```bash
# Create environment file
cp .env.template .env

# Edit .env with required settings
```

**Required .env variables:**
```bash
# Security (Required)
JWT_SECRET_KEY=your-super-secret-jwt-key-here-min-32-chars
SECRET_KEY=your-flask-secret-key-here

# AI Service (Required for full functionality)
GEMINI_API_KEY=your-gemini-api-key-from-google-ai-studio

# Database (Optional - defaults to SQLite)
DATABASE_URL=sqlite:///ragchatbot.db

# Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=104857600

# Application Settings
FRONTEND_URL=http://localhost:5173
FLASK_ENV=development
LOG_LEVEL=INFO
```

#### **4. Database Initialization**

**Option A: Fresh Database with Sample Data** (Recommended)
```bash
python reset_database.py
```
This creates:
- Admin user: `admin` / `admin123`
- Test user: `testuser` / `test123`
- Demo user: `demo` / `demo123` (with sample context)

**Option B: Empty Database**
```bash
python -c "from app_local import app, db; app.app_context().push(); db.create_all()"
```

**Option C: Fix Existing Database**
```bash
python fix_admin_column.py  # If you get "no such column: is_admin" error
```

#### **5. Verify Installation**
```bash
# Run tests
python test_all_fixes.py

# Check database schema
python simple_schema_viewer.py

# Start application
python app_local.py
```

### **Frontend Setup** (Optional for API-only usage)
```bash
cd ../frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### **Docker Setup** (Alternative)
```bash
# Quick setup using scripts
./scripts/deploy-local.ps1  # Windows PowerShell
./scripts/deploy-local.sh   # Linux/macOS

# Manual Docker Compose
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f backend
```

---

## 🔧 **Configuration**

### **Application Configuration**

#### **Chunking Strategies**
```python
CHUNKING_STRATEGIES = {
    'language-specific': {
        'description': 'Smart chunking based on file type and structure',
        'max_chunk_size': 1000,
        'overlap': 100,
        'preserve_structure': True
    },
    'semantic': {
        'description': 'Embedding-based semantic boundary detection',
        'max_chunk_size': 800,
        'overlap': 150,
        'similarity_threshold': 0.7
    },
    'fixed-size': {
        'description': 'Simple character-based chunking',
        'max_chunk_size': 1000,
        'overlap': 100
    }
}
```

#### **Supported File Types**
```python
SUPPORTED_EXTENSIONS = {
    'text': ['.txt', '.md', '.rst', '.log'],
    'code': ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.go', '.rs'],
    'document': ['.pdf', '.docx', '.doc', '.rtf'], 
    'data': ['.csv', '.xlsx', '.xls', '.json', '.xml', '.yaml'],
    'config': ['.ini', '.cfg', '.conf', '.toml'],
    'web': ['.html', '.htm', '.css', '.scss'],
    'archive': ['.zip', '.tar', '.gz', '.rar']
}
```

#### **AI Model Configuration**
```python
AI_MODELS = {
    'chat': 'gemini-2.0-flash-exp',      # Primary chat model
    'embedding': 'text-embedding-004',   # Embedding model (768-dim)
    'fallback_chat': 'gemini-1.5-flash', # Fallback if primary unavailable
}
```

### **Security Configuration**

#### **Rate Limiting Rules**
```python
RATE_LIMITS = {
    'default': {'limit': 1000, 'window': 3600},    # 1000/hour
    'auth': {'limit': 10, 'window': 300},          # 10/5min  
    'upload': {'limit': 20, 'window': 3600},       # 20/hour
    'admin': {'limit': 100, 'window': 3600}        # 100/hour
}
```

#### **Security Headers**
```python
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY', 
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'",
    'Referrer-Policy': 'strict-origin-when-cross-origin'
}
```

### **Database Configuration**

#### **SQLite (Development)**
```python
DATABASE_CONFIG = {
    'url': 'sqlite:///ragchatbot.db',
    'echo': False,  # Set True for SQL query logging
    'pool_recycle': 3600
}
```

#### **PostgreSQL (Production)**
```python
DATABASE_CONFIG = {
    'url': 'postgresql://user:password@localhost:5432/ragchatbot',
    'echo': False,
    'pool_size': 20,
    'pool_recycle': 3600
}
```

### **Logging Configuration**
```python
LOGGING_CONFIG = {
    'level': 'INFO',
    'file': 'logs/ragchatbot.log',
    'max_file_size_mb': 10,
    'backup_count': 5,
    'format': '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
}
```

---

## 🧪 **Testing**

### **Test Suite Overview**
The application includes comprehensive testing across multiple layers:

#### **Unit Tests**
```bash
# Run all tests
python test_all_fixes.py

# Specific test categories
python test_models.py          # Database models
python test_auth.py           # Authentication
python test_contexts.py       # Context management
python test_file_upload.py    # File processing
python test_cleanup.py        # Data cleanup
```

#### **Integration Tests**
```bash
# Test complete workflows
python test_context_creation.py    # End-to-end context creation
python test_context_deletion.py    # Context deletion with cleanup
python test_simple_context.py      # Basic context operations
```

#### **API Testing**
```bash
# Using pytest
python -m pytest tests/ -v

# Specific test files
python -m pytest tests/test_auth.py -v
python -m pytest tests/test_contexts.py -v
```

#### **Database Testing**
```bash
# Test database operations
python test_models.py

# Test schema integrity
python simple_schema_viewer.py

# Test migrations
python verify_fix.py
```

### **Manual Testing Workflows**

#### **1. User Registration & Authentication**
```bash
# Register new user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'
```

#### **2. Context Management**
```bash
# Create file context
curl -X POST http://localhost:5000/api/contexts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Context","source_type":"files","chunk_strategy":"language-specific"}'

# Upload files
curl -X POST http://localhost:5000/api/upload/files \
  -H "Authorization: Bearer <token>" \
  -F "files=@test_document.pdf" \
  -F "context_id=1"
```

#### **3. Chat Testing**
```bash
# Create chat session
curl -X POST http://localhost:5000/api/chat/sessions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Chat"}'

# Send query
curl -X POST http://localhost:5000/api/chat/query \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"What is this document about?","session_id":1,"context_ids":[1]}'
```

### **Performance Testing**
```bash
# Load testing with curl
for i in {1..100}; do
  curl -X GET http://localhost:5000/api/health &
done
wait

# Monitor system metrics
curl http://localhost:5000/api/metrics
```

### **Test Data Management**
```bash
# Reset to clean state with test data
python reset_database.py

# Create specific test scenarios
python -c "
from app_local import app, db
from models import User, Context
with app.app_context():
    # Create test users and contexts
    pass
"
```

---

## 🚀 **Deployment**

### **Local Development Deployment**

#### **Using Built-in Scripts** (Recommended)
```bash
# Windows PowerShell
.\scripts\deploy-local.ps1

# Linux/macOS  
./scripts/deploy-local.sh

# Features:
# - Automatic dependency installation
# - Environment setup
# - Database initialization  
# - Service startup
# - Health checks
```

#### **Manual Local Deployment**
```bash
# 1. Setup environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.template .env
# Edit .env with your settings

# 3. Initialize database
python reset_database.py

# 4. Start services
python app_local.py  # Backend on :5000
cd frontend && npm run dev  # Frontend on :5173
```

### **Docker Deployment**

#### **Development Docker Setup**
```bash
# Single command deployment
docker-compose up -d

# Services included:
# - Backend (Flask API)
# - Frontend (React PWA) 
# - Database (PostgreSQL)
# - Redis (for caching)

# Check status
docker-compose ps
docker-compose logs -f backend
```

#### **Production Docker Setup**
```bash
# Production compose file
docker-compose -f docker-compose.prod.yml up -d

# Features:
# - Multi-stage builds
# - Production optimizations
# - SSL/TLS support
# - Load balancing ready
# - Monitoring included
```

### **Cloud Platform Deployment**

#### **Heroku Deployment**
```bash
# 1. Install Heroku CLI
# 2. Login and create app
heroku login
heroku create your-ragchatbot-app

# 3. Set environment variables
heroku config:set JWT_SECRET_KEY=your-super-secret-key
heroku config:set GEMINI_API_KEY=your-gemini-api-key
heroku config:set DATABASE_URL=postgresql://...

# 4. Deploy
git push heroku main

# 5. Initialize database
heroku run python reset_database.py
```

#### **AWS EC2 Deployment**
```bash
# 1. Launch EC2 instance (Ubuntu 20.04+)
# 2. SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# 3. Install dependencies
sudo apt update
sudo apt install python3-pip python3-venv git nginx

# 4. Clone and setup application
git clone <your-repo>
cd multibrain/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Configure reverse proxy (nginx)
sudo cp deployment/nginx.conf /etc/nginx/sites-available/ragchatbot
sudo ln -s /etc/nginx/sites-available/ragchatbot /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# 6. Setup systemd service
sudo cp deployment/ragchatbot.service /etc/systemd/system/
sudo systemctl enable ragchatbot
sudo systemctl start ragchatbot
```

#### **Google Cloud Deployment**
```bash
# 1. Install gcloud CLI
# 2. Initialize project
gcloud init
gcloud app create

# 3. Deploy with app.yaml
gcloud app deploy

# 4. Set environment variables
gcloud app versions --service=default describe --format="export" > env.yaml
# Edit env.yaml with your variables
gcloud app deploy env.yaml
```

#### **Azure Deployment**
```bash
# 1. Install Azure CLI
# 2. Create resource group and app service
az group create --name ragchatbot-rg --location eastus
az appservice plan create --name ragchatbot-plan --resource-group ragchatbot-rg --sku B1

# 3. Create web app
az webapp create --resource-group ragchatbot-rg --plan ragchatbot-plan --name your-ragchatbot

# 4. Deploy code
az webapp deployment source config-zip --resource-group ragchatbot-rg --name your-ragchatbot --src deployment.zip
```

### **SSL/TLS Configuration**

#### **Let's Encrypt (Free SSL)**
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### **Custom SSL Certificate**
```bash
# Place certificates in /etc/ssl/
sudo cp your-cert.pem /etc/ssl/certs/
sudo cp your-key.pem /etc/ssl/private/

# Update nginx configuration
server {
    listen 443 ssl;
    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;
}
```

### **Environment-Specific Configuration**

#### **Production Environment Variables**
```bash
# Security
JWT_SECRET_KEY=<strong-random-key-64-chars>
SECRET_KEY=<strong-flask-secret-key>

# Database
DATABASE_URL=postgresql://user:password@db-host:5432/ragchatbot

# AI Services
GEMINI_API_KEY=<your-production-gemini-key>

# Application
FLASK_ENV=production
LOG_LEVEL=INFO
DEBUG=False

# Upload & Storage
UPLOAD_FOLDER=/var/www/ragchatbot/uploads
MAX_CONTENT_LENGTH=104857600

# Security
ALLOWED_ORIGINS=https://your-domain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
```

---

## 📊 **Monitoring**

### **Health Check Endpoints**
```bash
# Basic health check
curl http://localhost:5000/api/health
# Response: {"status": "healthy", "timestamp": "..."}

# Detailed health check (admin only)
curl -H "Authorization: Bearer <admin-token>" \
  http://localhost:5000/api/admin/system/health
```

### **Metrics Collection**

#### **Application Metrics** (Prometheus format)
```bash
# Get metrics
curl http://localhost:5000/api/metrics

# Sample metrics:
# http_requests_total{method="GET",endpoint="/api/contexts"} 150
# http_request_duration_seconds{method="POST",endpoint="/api/chat/query"} 2.34
# active_users_total 25
# contexts_total 45
# vector_search_operations_total 89
```

#### **System Metrics** (Admin dashboard)
```bash
curl -H "Authorization: Bearer <admin-token>" \
  http://localhost:5000/api/admin/dashboard

# Returns:
# - CPU, memory, disk usage
# - Request counts and error rates
# - Active users and sessions
# - Context statistics
# - Performance metrics
```

### **Logging**

#### **Log Configuration**
```python
# Application logs
logs/ragchatbot.log          # Main application logs
logs/error.log               # Error-specific logs
logs/security.log           # Security events
logs/performance.log        # Performance metrics
```

#### **Log Monitoring**
```bash
# Real-time log monitoring
tail -f logs/ragchatbot.log

# Error monitoring
tail -f logs/ragchatbot.log | grep ERROR

# Search for specific events
grep "user_login" logs/ragchatbot.log
grep "context_created" logs/ragchatbot.log
grep "rate_limit_exceeded" logs/security.log
```

#### **Log Rotation**
```bash
# Automatic log rotation configured
# - Max file size: 10MB
# - Backup files: 5
# - Compression: Yes
# - Rotation: Daily
```

### **Performance Monitoring**

#### **Built-in Performance Tracking**
```python
# Request timing
@app.before_request
def start_timer():
    g.start_time = time.time()

@app.after_request  
def log_request(response):
    duration = time.time() - g.start_time
    # Log request with timing
```

#### **Database Performance**
```bash
# Query performance monitoring
export SQLALCHEMY_ECHO=True  # Log all SQL queries

# Database query analysis
python -c "
from app_local import app, db
with app.app_context():
    # Analyze slow queries
    result = db.engine.execute('SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10')
"
```

### **Alerting**

#### **Built-in Alert System**
```python
# Alert conditions monitored:
# - High CPU usage (>80%)
# - High memory usage (>85%) 
# - High error rate (>10%)
# - Slow response times (>5s)
# - Disk space low (<10%)
```

#### **Email Alerts** (Configuration)
```bash
# Add to .env
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_SMTP_HOST=smtp.gmail.com
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_USERNAME=your-email@gmail.com
ALERT_EMAIL_PASSWORD=your-app-password
ALERT_EMAIL_FROM=ragchatbot@your-domain.com
ALERT_EMAIL_TO=admin@your-domain.com
```

#### **Webhook Alerts** (Slack/Discord)
```bash
# Add to .env
ALERT_WEBHOOK_ENABLED=true
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

### **Monitoring Tools Integration**

#### **Grafana Dashboard** (Optional)
```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
```

#### **Prometheus Setup** (Optional)
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ragchatbot'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: /api/metrics
```

---

## 🔒 **Security**

### **Authentication & Authorization**

#### **JWT Token Security**
- **Algorithm**: HS256 with secure secret key
- **Expiration**: 24 hours (configurable)
- **Refresh**: Automatic on activity
- **Storage**: HttpOnly cookies (recommended) or localStorage

#### **Password Security**
- **Hashing**: Werkzeug PBKDF2 with salt
- **Minimum Requirements**: 8+ characters
- **Rate Limiting**: 10 attempts per 5 minutes
- **Lockout**: Temporary account lock after failed attempts

#### **Role-Based Access Control**
```python
# User roles
ROLES = {
    'user': {
        'permissions': ['read_own', 'write_own', 'chat', 'upload']
    },
    'admin': {
        'permissions': ['read_all', 'write_all', 'admin_panel', 'system_metrics']
    }
}
```

### **Input Validation & Sanitization**

#### **File Upload Security**
```python
UPLOAD_SECURITY = {
    'allowed_extensions': ['.pdf', '.docx', '.txt', ...],
    'max_file_size': 100 * 1024 * 1024,  # 100MB
    'scan_uploads': True,  # Virus scanning
    'quarantine_suspicious': True,
    'filename_sanitization': True
}
```

#### **SQL Injection Prevention**
- **ORM**: SQLAlchemy parameterized queries
- **Raw Queries**: Always use text() with bound parameters
- **Input Validation**: Pydantic models for all inputs

#### **XSS Prevention**
```python
# Security headers applied
SECURITY_HEADERS = {
    'Content-Security-Policy': "default-src 'self'; script-src 'self'",
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block'
}
```

### **Rate Limiting & DDoS Protection**

#### **Rate Limiting Rules**
```python
RATE_LIMITS = {
    'api_default': '1000/hour',
    'auth_login': '10/5minutes', 
    'file_upload': '20/hour',
    'chat_query': '100/hour',
    'admin_endpoints': '100/hour'
}
```

#### **IP-based Protection**
- **Automatic blocking**: Suspicious activity detection
- **Whitelist/Blacklist**: Manual IP management
- **Geographic blocking**: Optional country-based restrictions

### **Data Protection**

#### **Encryption**
- **Data at Rest**: Database encryption (optional)
- **Data in Transit**: TLS 1.3 for all connections
- **API Keys**: Encrypted storage in environment variables

#### **Data Privacy**
- **User Isolation**: Strict tenant separation
- **Data Retention**: Configurable retention policies
- **GDPR Compliance**: Data deletion and export capabilities

#### **Backup Security**
```bash
# Encrypted backups
gpg --symmetric --cipher-algo AES256 ragchatbot.db
# Store encrypted backups securely
```

### **Security Monitoring**

#### **Security Event Logging**
```python
# Events logged:
# - Failed login attempts
# - Admin privilege escalation
# - Suspicious file uploads
# - Rate limit violations
# - SQL injection attempts
# - XSS attempts
```

#### **Intrusion Detection**
```python
# Patterns monitored:
# - Rapid requests from single IP
# - Multiple failed logins
# - Unusual file upload patterns
# - Admin endpoint access from new IPs
# - Large response times (possible attacks)
```

### **Security Best Practices**

#### **Environment Security**
```bash
# Production checklist:
✓ Strong JWT secret keys (64+ random characters)
✓ HTTPS enabled with valid certificates
✓ Database credentials secured
✓ API keys in environment variables only
✓ Debug mode disabled
✓ Error messages sanitized
✓ Security headers configured
✓ Rate limiting enabled
✓ Log monitoring active
```

#### **Deployment Security**
```bash
# Server hardening:
✓ Firewall configured (only necessary ports open)
✓ SSH key-based authentication
✓ Regular security updates
✓ Non-root application user
✓ File permissions properly set
✓ Backup encryption enabled
```

#### **Code Security**
```bash
# Development practices:
✓ Dependency vulnerability scanning
✓ Code review for security issues
✓ Input validation on all endpoints
✓ Output encoding for user data
✓ Secure session management
✓ Error handling without information disclosure
```

---

## 🔧 **Database Management**

### **Schema Management Tools**

#### **View Current Schema**
```bash
# Quick schema overview
python3 simple_schema_viewer.py

# Detailed analysis (requires Flask environment)  
python3 show_schema.py

# Example output:
# 📊 Tables found: 6
# 👥 Users: 4 rows
# 📁 Contexts: 2 rows  
# 📄 Documents: 5 rows
# 🧩 Text Chunks: 123 rows
# 💬 Chat Sessions: 3 rows
# 💭 Messages: 15 rows
```

#### **Database Reset & Migration**
```bash
# Complete reset with sample data
python3 reset_database.py

# Features:
# ✅ Automatic backup creation
# ✅ Clean schema recreation  
# ✅ Sample users and data
# ✅ Schema verification

# Sample accounts created:
# - admin / admin123 (Admin)
# - testuser / test123 (User)
# - demo / demo123 (Demo with context)
```

#### **Fix Database Issues**
```bash
# Fix missing columns (e.g., is_admin column)
python3 fix_admin_column.py

# Verify database state
python3 verify_fix.py

# Manual SQL fixes if needed:
sqlite3 ragchatbot.db "ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"
```

### **Backup & Recovery**

#### **Automatic Backups**
```bash
# All management scripts create automatic backups
# Location: same directory as database
# Format: ragchatbot_backup_YYYYMMDD_HHMMSS.db

# Manual backup
cp instance/ragchatbot.db "backup_$(date +%Y%m%d_%H%M%S).db"
```

#### **Database Migration Workflow**
```bash
# 1. Always backup first
python3 -c "
import shutil
from datetime import datetime
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy('instance/ragchatbot.db', f'backup_{timestamp}.db')
print(f'Backup created: backup_{timestamp}.db')
"

# 2. View current state
python3 simple_schema_viewer.py

# 3. Apply changes
python3 fix_admin_column.py  # or other migration script

# 4. Verify changes  
python3 verify_fix.py

# 5. Test application
python3 app_local.py
```

### **Database Optimization**

#### **Performance Tuning**
```sql
-- Add indexes for common queries
CREATE INDEX idx_contexts_user_id ON contexts(user_id);
CREATE INDEX idx_documents_context_id ON documents(context_id);
CREATE INDEX idx_text_chunks_context_id ON text_chunks(context_id);
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
```

#### **Data Cleanup**
```bash
# Remove orphaned data
python3 -c "
from app_local import app, db
from routes.admin import admin_bp
with app.app_context():
    # Use admin cleanup endpoint
    import requests
    # Call cleanup API
"

# Manual cleanup queries:
# - Remove documents without contexts
# - Remove chunks without documents  
# - Remove messages from deleted sessions
```

#### **Database Maintenance**
```sql
-- SQLite maintenance
VACUUM;  -- Reclaim space
ANALYZE; -- Update statistics

-- PostgreSQL maintenance  
VACUUM ANALYZE; -- Reclaim space and update stats
REINDEX;        -- Rebuild indexes
```

### **Database Monitoring**

#### **Health Checks**
```python
# Database health monitoring
def check_database_health():
    try:
        # Test connection
        db.session.execute('SELECT 1')
        
        # Check table integrity
        tables = db.engine.table_names()
        expected = ['users', 'contexts', 'documents', 'text_chunks', 'chat_sessions', 'messages']
        missing = set(expected) - set(tables)
        
        # Check for locks
        # Check disk space
        # Check connection pool
        
        return {'status': 'healthy', 'issues': missing}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}
```

#### **Performance Metrics**
```bash
# Monitor query performance
export SQLALCHEMY_ECHO=True  # Log all queries

# Analyze slow queries (PostgreSQL)
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

# SQLite query analysis
.timer on
.explain query_plan SELECT * FROM contexts WHERE user_id = 1;
```

---

## 🤝 **Contributing**

### **Development Workflow**

#### **Getting Started**
```bash
# 1. Fork the repository
git fork <original-repo>

# 2. Clone your fork  
git clone <your-fork-url>
cd multibrain

# 3. Set up development environment
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Create development database
python reset_database.py

# 5. Run tests to ensure everything works
python test_all_fixes.py
```

#### **Feature Development**
```bash
# 1. Create feature branch
git checkout -b feature/new-awesome-feature

# 2. Make your changes
# - Write code
# - Add tests  
# - Update documentation

# 3. Test your changes
python test_all_fixes.py
python test_your_new_feature.py

# 4. Commit with descriptive messages
git add .
git commit -m "feat: add awesome new feature with tests

- Implements new document processing pipeline
- Adds support for PowerPoint files
- Includes comprehensive test coverage
- Updates API documentation

Closes #123"

# 5. Push and create pull request
git push origin feature/new-awesome-feature
```

### **Code Standards**

#### **Python Code Style**
```python
# Follow PEP 8 guidelines
# Use type hints where possible
# Add docstrings to all functions

def process_document(file_path: str, context_id: int) -> Dict[str, Any]:
    """
    Process a document and extract text chunks.
    
    Args:
        file_path: Path to the document file
        context_id: ID of the target context
        
    Returns:
        Dictionary containing processing results
        
    Raises:
        ValueError: If file_path is invalid
        ProcessingError: If document processing fails
    """
    # Implementation here
    pass
```

#### **API Endpoint Standards**
```python
@contexts_bp.route('/<int:context_id>/process', methods=['POST'])
@jwt_required()
def process_context(context_id: int):
    """
    Process context documents.
    
    Request Body:
        {
            "chunk_strategy": "language-specific",
            "force_reprocess": false
        }
    
    Returns:
        200: Processing started successfully
        404: Context not found
        403: Insufficient permissions
    """
    try:
        # Validate input
        data = request.get_json()
        
        # Process
        result = process_context_documents(context_id, **data)
        
        # Return response
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Context processing failed: {e}")
        return jsonify({'error': str(e)}), 500
```

#### **Frontend Code Style**
```typescript
// Use TypeScript with strict mode
// Follow React best practices
// Add proper error boundaries

interface ProcessContextProps {
  contextId: number;
  onComplete: (result: ProcessingResult) => void;
  onError: (error: Error) => void;
}

const ProcessContext: React.FC<ProcessContextProps> = ({
  contextId,
  onComplete,
  onError,
}) => {
  // Implementation with proper error handling
  // and loading states
};
```

### **Testing Requirements**

#### **Test Coverage Standards**
- **Unit Tests**: >80% code coverage required
- **Integration Tests**: All API endpoints tested
- **End-to-End Tests**: Critical user workflows covered

#### **Writing Tests**
```python
# test_new_feature.py
import pytest
from app_local import app, db
from models import User, Context

class TestNewFeature:
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                yield client
                db.drop_all()
    
    def test_feature_functionality(self, client):
        """Test core feature functionality"""
        # Setup test data
        # Execute feature
        # Assert expected results
        
    def test_feature_error_handling(self, client):
        """Test error scenarios"""
        # Test invalid input
        # Test edge cases
        # Assert proper error responses
```

### **Documentation Requirements**

#### **Code Documentation**
- **Docstrings**: All functions and classes
- **Type Hints**: All function parameters and returns  
- **Comments**: Complex logic explained
- **README Updates**: New features documented

#### **API Documentation**
- **Endpoint Description**: Clear purpose statement
- **Request/Response Examples**: Full JSON examples
- **Error Codes**: All possible error responses
- **Rate Limits**: If applicable

### **Review Process**

#### **Pull Request Requirements**
- [ ] **Tests**: All tests pass
- [ ] **Code Style**: Follows project standards
- [ ] **Documentation**: Updated appropriately
- [ ] **Breaking Changes**: Clearly marked
- [ ] **Performance**: No significant regressions

#### **Review Checklist**
```markdown
## PR Review Checklist

### Functionality
- [ ] Feature works as described
- [ ] Edge cases handled appropriately
- [ ] Error handling is comprehensive
- [ ] Performance is acceptable

### Code Quality  
- [ ] Code follows style guidelines
- [ ] Functions have appropriate docstrings
- [ ] Variable names are descriptive
- [ ] No code duplication

### Testing
- [ ] All tests pass
- [ ] New functionality is tested
- [ ] Test coverage is maintained
- [ ] Integration tests updated

### Security
- [ ] No sensitive data exposed
- [ ] Input validation appropriate
- [ ] Authentication/authorization correct
- [ ] No security vulnerabilities introduced

### Documentation
- [ ] README updated if needed
- [ ] API documentation updated
- [ ] Code comments are clear
- [ ] Breaking changes documented
```

### **Release Process**

#### **Version Management**
```bash
# Semantic versioning: MAJOR.MINOR.PATCH
# MAJOR: Breaking changes
# MINOR: New features (backwards compatible)  
# PATCH: Bug fixes

# Example releases:
v1.0.0 - Initial release
v1.1.0 - Added repository integration
v1.1.1 - Fixed authentication bug
v2.0.0 - Breaking API changes
```

#### **Release Checklist**
```bash
# 1. Update version numbers
# 2. Update CHANGELOG.md
# 3. Run full test suite
# 4. Create release branch
# 5. Deploy to staging
# 6. Manual testing
# 7. Create GitHub release
# 8. Deploy to production
# 9. Monitor for issues
```

---

## 📈 **Roadmap**

### **Completed Features** ✅
- [x] Multi-source document processing (Files, Repos, Databases)
- [x] Advanced text extraction (PDF, DOCX, Excel with structure)  
- [x] Vector search with FAISS and Gemini embeddings
- [x] Real-time chat with streaming responses
- [x] Admin dashboard with system monitoring
- [x] Comprehensive security middleware
- [x] Database management tools
- [x] PWA with offline capabilities
- [x] Drag & drop file upload interface
- [x] Context reprocessing functionality

### **Near-term Roadmap** (Next 3 months)

#### **Enhanced AI Features**
- [ ] **Multi-modal AI**: Image and document understanding
- [ ] **Advanced RAG**: Hybrid search (keyword + semantic)
- [ ] **Citation Enhancement**: Page numbers and exact locations
- [ ] **Query Expansion**: Automatic query enhancement
- [ ] **Response Summarization**: Configurable response lengths

#### **User Experience Improvements** 
- [ ] **Context Search & Filtering**: Advanced context discovery
- [ ] **Chat Session Management**: Better conversation organization
- [ ] **User Preferences**: Customizable interface and behavior
- [ ] **Export Functionality**: PDF/Word export of conversations
- [ ] **Collaboration Features**: Context sharing between users

#### **Performance & Scalability**
- [ ] **Background Task Processing**: Celery alternative implementation
- [ ] **Advanced Caching**: Redis integration for better performance
- [ ] **Database Optimization**: Query optimization and indexing
- [ ] **Load Balancing**: Multi-instance deployment support
- [ ] **CDN Integration**: Static asset optimization

### **Medium-term Roadmap** (3-6 months)

#### **Enterprise Features**
- [ ] **SSO Integration**: SAML/OAuth enterprise authentication
- [ ] **Advanced Admin Controls**: User management, audit logs
- [ ] **Team Management**: Organizations and team workspaces
- [ ] **Usage Analytics**: Detailed usage reporting and insights
- [ ] **API Rate Plans**: Tiered access controls

#### **Advanced Document Processing**
- [ ] **Tree-sitter Integration**: Better code analysis and parsing
- [ ] **OCR Integration**: Scanned document processing
- [ ] **Video/Audio Processing**: Transcript extraction and indexing
- [ ] **Real-time Collaboration**: Live document editing and chat
- [ ] **Version Control**: Document and context versioning

#### **Integration & Ecosystem**
- [ ] **Webhook System**: Event-driven integrations
- [ ] **Plugin Architecture**: Custom processor plugins
- [ ] **API SDK**: Client libraries for multiple languages
- [ ] **Mobile Applications**: iOS and Android apps
- [ ] **Browser Extension**: Web page knowledge capture

### **Long-term Vision** (6+ months)

#### **AI & Machine Learning**
- [ ] **Custom Model Training**: Domain-specific model fine-tuning
- [ ] **Automated Insights**: Proactive knowledge discovery
- [ ] **Natural Language Queries**: SQL/API query generation
- [ ] **Predictive Analytics**: Usage and performance prediction
- [ ] **Multi-language Support**: Global localization

#### **Enterprise Scale**
- [ ] **Kubernetes Deployment**: Container orchestration
- [ ] **High Availability**: Multi-region deployment
- [ ] **Disaster Recovery**: Automated backup and recovery
- [ ] **Compliance**: SOC2, HIPAA, GDPR certifications
- [ ] **Enterprise Reporting**: Advanced analytics dashboard

#### **Innovation Features**
- [ ] **Graph Knowledge Base**: Relationship mapping between documents
- [ ] **Visual Interface**: Drag-and-drop workflow builder
- [ ] **Voice Interface**: Voice queries and responses
- [ ] **AR/VR Integration**: Immersive knowledge exploration
- [ ] **Blockchain Integration**: Decentralized knowledge verification

---

## 📝 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 RAG Chatbot PWA Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🆘 **Support & Troubleshooting**

### **Common Issues & Solutions**

#### **Database Issues**
```bash
# Error: "no such column: users.is_admin"
python3 fix_admin_column.py

# Error: "database is locked" 
pkill -f app_local.py  # Stop all instances
python3 app_local.py   # Restart

# Error: "table already exists"
python3 reset_database.py  # Complete reset
```

#### **Import/Dependency Issues**
```bash
# Error: "No module named 'flask'"
pip install -r requirements.txt

# Error: "ModuleNotFoundError: No module named 'faiss'"
pip install faiss-cpu

# Python version issues
python3 --version  # Should be 3.10+
python3 -m venv venv  # Create new venv if needed
```

#### **API/Authentication Issues**
```bash
# Error: "JWT token invalid"
# Check JWT_SECRET_KEY in .env
# Token may be expired (24h default)

# Error: "Admin access required"  
# Use admin account or run: 
curl -X POST http://localhost:5000/api/admin/make-admin \
  -H "Authorization: Bearer <token>"
```

#### **File Upload Issues**
```bash
# Error: "File type not supported"
curl http://localhost:5000/api/upload/supported-extensions

# Error: "File too large"
# Check MAX_CONTENT_LENGTH in config (default 100MB)

# Error: "Upload failed"
# Check uploads/ directory permissions
# Verify UPLOAD_FOLDER configuration
```

### **Performance Issues**

#### **Slow Response Times**
- **Check system resources**: CPU, memory, disk I/O
- **Monitor logs**: `tail -f logs/ragchatbot.log`
- **Database optimization**: Add indexes, analyze queries
- **Vector search**: Reduce chunk size or context scope

#### **Memory Usage**
- **Vector stores**: Large FAISS indexes consume memory
- **Document processing**: Limit concurrent uploads
- **Chat history**: Configure message retention policies

### **Getting Help**

#### **Documentation Resources**
- **[API Reference](docs/API_REFERENCE.md)**: Complete API documentation
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)**: Production deployment
- **[Knowledge Document](docs/KNOWLEDGE_DOCUMENT.md)**: Detailed architecture
- **[Database Management](DATABASE_MANAGEMENT.md)**: Database tools and maintenance

#### **Community Support**
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community help
- **Documentation**: Comprehensive guides in `/docs/`

#### **Professional Support**
For enterprise deployments and custom integrations, contact the development team through GitHub.

---

**Version**: 2.0.0  
**Last Updated**: 2024-12-30  
**Status**: Production Ready  
**Maintainer**: RAG Chatbot Development Team

---

*This documentation is continuously updated. For the latest information, please check the repository's main branch.*