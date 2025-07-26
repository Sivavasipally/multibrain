# RAG Chatbot - File Structure Guide

## 📁 **Complete File Structure**

```
myrag/
├── backend/                          # Backend Flask application
│   ├── app_local.py                 # Main application entry point
│   ├── models.py                    # Database models and schemas
│   ├── requirements.txt             # Python dependencies
│   ├── .env.template               # Environment configuration template
│   ├── .env                        # Environment variables (create from template)
│   │
│   ├── routes/                     # API route blueprints
│   │   ├── __init__.py
│   │   ├── admin.py               # Admin management endpoints
│   │   ├── auth.py                # Authentication endpoints
│   │   ├── chat.py                # Chat and query endpoints
│   │   ├── contexts.py            # Context management endpoints
│   │   └── upload.py              # File upload endpoints
│   │
│   ├── services/                  # Business logic services
│   │   ├── __init__.py
│   │   ├── llm_service.py         # LLM integration (Gemini, OpenAI)
│   │   ├── vector_service.py      # Vector storage and retrieval
│   │   ├── monitoring_service.py  # System monitoring
│   │   └── context_cleanup_service.py # Context cleanup operations
│   │
│   ├── performance/               # Performance optimization
│   │   ├── __init__.py
│   │   └── caching.py            # Caching mechanisms
│   │
│   ├── models/                   # Additional model components
│   │   ├── __init__.py
│   │   └── context_version.py    # Context versioning system
│   │
│   ├── clients/                  # API client libraries
│   │   ├── python_client.py      # Python API client
│   │   └── ragchatbot_client/    # CLI client package
│   │       ├── __init__.py
│   │       ├── cli.py           # Command-line interface
│   │       └── client.py        # Core client functionality
│   │
│   ├── uploads/                  # File upload directory
│   ├── vector_stores/           # Vector storage directory
│   ├── instance/                # Flask instance folder
│   │   └── ragchatbot.db       # SQLite database file
│   │
│   ├── tests/                   # Test files
│   │   ├── test_all_fixes.py   # Comprehensive test suite
│   │   ├── test_context_fix.py # Context creation tests
│   │   └── test_file_upload.py # File upload tests
│   │
│   └── docs/                    # Documentation files
│       ├── KNOWLEDGE_DOCUMENT.md    # Complete application documentation
│       ├── API_REFERENCE.md         # API endpoint documentation
│       ├── DEPLOYMENT_GUIDE.md      # Deployment instructions
│       ├── FILE_STRUCTURE_GUIDE.md  # This file
│       └── FIXES_APPLIED.md         # Applied fixes documentation
│
├── frontend/                    # Frontend application
│   ├── src/
│   │   ├── components/         # React/Vue components
│   │   │   ├── Auth/          # Authentication components
│   │   │   │   ├── Login.tsx
│   │   │   │   └── Register.tsx
│   │   │   ├── Context/       # Context management
│   │   │   │   ├── ContextList.tsx
│   │   │   │   ├── ContextWizard.tsx
│   │   │   │   └── ContextDetails.tsx
│   │   │   ├── Chat/          # Chat interface
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   ├── MessageList.tsx
│   │   │   │   └── MessageInput.tsx
│   │   │   └── Admin/         # Admin dashboard
│   │   │       ├── Dashboard.tsx
│   │   │       └── UserManagement.tsx
│   │   ├── services/          # API service layer
│   │   │   ├── api.ts        # Main API service
│   │   │   ├── auth.ts       # Authentication service
│   │   │   └── websocket.ts  # WebSocket service
│   │   ├── utils/            # Utility functions
│   │   │   ├── helpers.ts
│   │   │   └── constants.ts
│   │   ├── styles/           # CSS/styling files
│   │   │   ├── globals.css
│   │   │   └── components.css
│   │   ├── App.tsx           # Main application component
│   │   └── main.tsx          # Application entry point
│   ├── public/               # Static assets
│   │   ├── index.html
│   │   └── favicon.ico
│   ├── package.json          # Node.js dependencies
│   ├── vite.config.ts       # Vite configuration
│   └── tsconfig.json        # TypeScript configuration
│
└── docker/                   # Docker configuration
    ├── docker-compose.yml    # Docker Compose configuration
    ├── Dockerfile.backend    # Backend Docker image
    ├── Dockerfile.frontend   # Frontend Docker image
    └── nginx.conf            # Nginx configuration
```

---

## 📄 **Core Files Explanation**

### **Backend Core Files**

#### **app_local.py** - Main Application Entry Point
```python
# Purpose: Flask application initialization and configuration
# Key Components:
# - Flask app creation and configuration
# - Database initialization
# - Route registration
# - Security headers
# - Error handling
# - Main execution block

# Key Functions:
# - Application factory pattern
# - Database model registration
# - JWT configuration
# - CORS setup
# - File upload handling
# - Text processing functions
```

#### **models.py** - Database Models
```python
# Purpose: SQLAlchemy database models and schemas
# Models Defined:
# - User: User authentication and management
# - Context: Document context management
# - Document: File metadata storage
# - ChatSession: Chat session management
# - Message: Chat message storage
# - TextChunk: Processed text chunks

# Key Features:
# - Relationship definitions
# - JSON serialization methods
# - Password hashing utilities
# - Configuration management
```

#### **requirements.txt** - Python Dependencies
```txt
# Core Flask dependencies
Flask>=3.0.0
Flask-SQLAlchemy>=3.1.1
Flask-CORS>=4.0.0
Flask-JWT-Extended>=4.6.0

# AI/ML dependencies
google-generativeai>=0.3.2
openai>=1.6.1
sentence-transformers>=2.2.2
faiss-cpu>=1.7.4

# Document processing
python-docx>=1.1.0
openpyxl>=3.1.2
PyMuPDF>=1.23.8

# Utilities
python-dotenv>=1.0.0
requests>=2.31.0
psutil>=5.9.0
```

### **Route Blueprints**

#### **routes/auth.py** - Authentication Routes
```python
# Endpoints:
# POST /api/auth/register - User registration
# POST /api/auth/login - User authentication
# POST /api/auth/logout - User logout
# GET /api/auth/profile - User profile

# Features:
# - JWT token generation
# - Password validation
# - User session management
```

#### **routes/contexts.py** - Context Management
```python
# Endpoints:
# GET /api/contexts - List user contexts
# POST /api/contexts - Create new context
# GET /api/contexts/{id} - Get context details
# PUT /api/contexts/{id} - Update context
# DELETE /api/contexts/{id} - Delete context
# GET /api/contexts/{id}/chunks - Get context chunks

# Features:
# - Context CRUD operations
# - File processing integration
# - Progress tracking
```

#### **routes/upload.py** - File Upload
```python
# Endpoints:
# POST /api/upload/files - Upload files to context
# GET /api/upload/status/{context_id} - Check upload status

# Features:
# - Multi-file upload support
# - File type validation
# - Progress tracking
# - Error handling
```

#### **routes/chat.py** - Chat Interface
```python
# Endpoints:
# POST /api/chat/query - Send chat query
# GET /api/chat/sessions - List chat sessions
# POST /api/chat/sessions - Create chat session
# GET /api/chat/sessions/{id}/messages - Get session messages
# DELETE /api/chat/sessions/{id} - Delete session

# Features:
# - Context-aware responses
# - Citation generation
# - Session management
```

#### **routes/admin.py** - Admin Management
```python
# Endpoints:
# GET /api/admin/dashboard - System dashboard
# GET /api/admin/users - User management
# POST /api/admin/cleanup/orphaned - Cleanup orphaned data
# GET /api/admin/system/stats - System statistics

# Features:
# - System monitoring
# - User management
# - Performance metrics
# - Cleanup operations
```

### **Service Layer**

#### **services/llm_service.py** - LLM Integration
```python
# Purpose: Large Language Model integration
# Supported Models:
# - Google Gemini (gemini-pro, gemini-pro-vision)
# - OpenAI GPT (gpt-3.5-turbo, gpt-4)

# Key Functions:
# - Model initialization
# - Query processing
# - Response generation
# - Error handling
# - Rate limiting
```

#### **services/vector_service.py** - Vector Operations
```python
# Purpose: Vector storage and similarity search
# Technologies:
# - FAISS for vector indexing
# - Sentence Transformers for embeddings
# - Cosine similarity for retrieval

# Key Functions:
# - Embedding generation
# - Vector index creation
# - Similarity search
# - Index persistence
```

#### **services/monitoring_service.py** - System Monitoring
```python
# Purpose: Application performance monitoring
# Metrics Tracked:
# - CPU and memory usage
# - Request response times
# - Error rates
# - Database performance

# Features:
# - Real-time metrics
# - Alert generation
# - Performance logging
```

### **Configuration Files**

#### **.env.template** - Environment Configuration Template
```bash
# Security Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-here
SECRET_KEY=your-flask-secret-key-here

# Database Configuration
DATABASE_URL=sqlite:///ragchatbot.db

# File Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=104857600

# AI Service Configuration
GEMINI_API_KEY=your-gemini-api-key-here
OPENAI_API_KEY=your-openai-api-key-here

# Application Configuration
FRONTEND_URL=http://localhost:5173
FLASK_ENV=development
FLASK_DEBUG=false
```

---

## 🗂️ **Directory Purposes**

### **uploads/** - File Storage
```
uploads/
├── {context_id}/           # Context-specific uploads
│   ├── original/          # Original uploaded files
│   ├── processed/         # Processed text files
│   └── metadata/          # File metadata
└── temp/                  # Temporary upload files
```

### **vector_stores/** - Vector Index Storage
```
vector_stores/
├── {context_id}/          # Context-specific vector stores
│   ├── index.faiss       # FAISS vector index
│   ├── metadata.json     # Index metadata
│   └── embeddings.npy    # Raw embeddings
└── global/               # Global vector stores
```

### **instance/** - Flask Instance Data
```
instance/
├── ragchatbot.db         # SQLite database file
├── config.py             # Instance-specific configuration
└── logs/                 # Application logs
    ├── app.log
    ├── error.log
    └── access.log
```

### **tests/** - Test Suite
```
tests/
├── unit/                 # Unit tests
│   ├── test_models.py
│   ├── test_services.py
│   └── test_routes.py
├── integration/          # Integration tests
│   ├── test_api.py
│   └── test_workflows.py
└── fixtures/             # Test data
    ├── sample_documents/
    └── test_data.json
```

---

## 🔧 **Configuration Files**

### **Frontend Configuration**

#### **package.json** - Node.js Dependencies
```json
{
  "name": "ragchatbot-frontend",
  "version": "1.0.0",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "react-router-dom": "^6.8.0",
    "@types/react": "^18.2.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "typescript": "^5.0.0",
    "@vitejs/plugin-react": "^4.0.0"
  }
}
```

#### **vite.config.ts** - Build Configuration
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})
```

### **Docker Configuration**

#### **docker-compose.yml** - Multi-Service Setup
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/ragchatbot
    volumes:
      - ./uploads:/app/uploads
      - ./vector_stores:/app/vector_stores
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=ragchatbot
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 📚 **Documentation Files**

### **KNOWLEDGE_DOCUMENT.md**
- Complete application overview
- Architecture and design patterns
- Technology stack details
- Database schema documentation
- Logic flow explanations

### **API_REFERENCE.md**
- Detailed API endpoint documentation
- Request/response examples
- Error code explanations
- Authentication requirements
- Rate limiting information

### **DEPLOYMENT_GUIDE.md**
- Local development setup
- Docker deployment instructions
- Cloud platform deployment
- Production configuration
- Monitoring and maintenance

### **FIXES_APPLIED.md**
- Comprehensive list of applied fixes
- Security improvements
- Performance optimizations
- Code quality enhancements
- Test results and verification

---

## 🔍 **File Naming Conventions**

### **Python Files**
- `snake_case` for file names
- `PascalCase` for class names
- `snake_case` for function names
- `UPPER_CASE` for constants

### **Frontend Files**
- `PascalCase` for component files
- `camelCase` for utility files
- `kebab-case` for CSS files
- `lowercase` for configuration files

### **Configuration Files**
- `.env` for environment variables
- `.json` for structured configuration
- `.yml/.yaml` for Docker and CI/CD
- `.md` for documentation

---

## 🚀 **Getting Started with File Structure**

### **For Developers**
1. Start with `app_local.py` to understand the application entry point
2. Review `models.py` to understand the data structure
3. Explore `routes/` to understand API endpoints
4. Check `services/` for business logic
5. Review tests in `tests/` for usage examples

### **For Deployment**
1. Configure environment variables using `.env.template`
2. Review `DEPLOYMENT_GUIDE.md` for platform-specific instructions
3. Use `docker-compose.yml` for containerized deployment
4. Check `requirements.txt` for dependency management

### **For API Integration**
1. Start with `API_REFERENCE.md` for endpoint documentation
2. Use `clients/python_client.py` for Python integration
3. Check `frontend/src/services/api.ts` for TypeScript examples
4. Review authentication flow in `routes/auth.py`

---

**File Structure Guide Version**: 1.0  
**Last Updated**: 2024-01-01  
**Total Files**: 50+ core files, 100+ including tests and documentation
