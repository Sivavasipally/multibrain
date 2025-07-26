# RAG Chatbot PWA - Project Structure

## 📁 Complete Project Structure

```
myrag/
├── 📱 frontend/                    # React PWA Frontend
│   ├── public/
│   │   ├── manifest.json          # PWA manifest
│   │   ├── sw.js                  # Service worker
│   │   └── index.html             # Main HTML file
│   ├── src/
│   │   ├── components/            # React components
│   │   │   ├── Auth/
│   │   │   │   └── ProtectedRoute.tsx
│   │   │   ├── Chat/
│   │   │   │   ├── ChatMessage.tsx
│   │   │   │   └── ContextSelector.tsx
│   │   │   ├── Context/
│   │   │   │   ├── ContextWizard.tsx
│   │   │   │   ├── ContextDetails.tsx
│   │   │   │   ├── RepositoryConfig.tsx
│   │   │   │   ├── DatabaseConfig.tsx
│   │   │   │   └── FileUploadConfig.tsx
│   │   │   ├── Layout/
│   │   │   │   └── Layout.tsx
│   │   │   └── PWA/
│   │   │       ├── InstallBanner.tsx
│   │   │       └── OfflineIndicator.tsx
│   │   ├── contexts/              # React contexts
│   │   │   ├── AuthContext.tsx
│   │   │   ├── ThemeContext.tsx
│   │   │   └── SnackbarContext.tsx
│   │   ├── hooks/                 # Custom hooks
│   │   │   ├── usePWA.ts
│   │   │   └── useOfflineStorage.ts
│   │   ├── pages/                 # Page components
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Contexts.tsx
│   │   │   ├── Chat.tsx
│   │   │   └── AuthCallback.tsx
│   │   ├── services/              # API services
│   │   │   └── api.ts
│   │   ├── App.tsx               # Main app component
│   │   └── main.tsx              # Entry point
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── 🔧 backend/                     # Flask API Backend
│   ├── routes/                    # API routes
│   │   ├── auth.py               # Authentication routes
│   │   ├── contexts.py           # Context management
│   │   ├── chat.py               # Chat functionality
│   │   └── upload.py             # File upload handling
│   ├── services/                  # Business logic services
│   │   ├── repository_service.py  # GitHub/Bitbucket integration
│   │   ├── database_service.py    # Database connections
│   │   ├── document_processor.py  # Language-aware processing
│   │   ├── vector_service.py      # FAISS vector storage
│   │   └── llm_service.py         # Gemini LLM integration
│   ├── tasks/                     # Celery background tasks
│   │   ├── context_processor.py   # Context processing tasks
│   │   └── file_processor.py      # File processing tasks
│   ├── migrations/                # Database migrations
│   ├── models.py                  # SQLAlchemy models
│   ├── app.py                     # Flask application
│   ├── config.py                  # Configuration
│   └── requirements.txt           # Python dependencies
│
├── 🐳 docker/                      # Docker configuration
│   ├── Dockerfile.frontend
│   ├── Dockerfile.backend
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
│
├── 📜 scripts/                     # Utility scripts
│   └── deploy.sh                  # Deployment script
│
├── 📚 docs/                        # Documentation
│   ├── API.md                     # API documentation
│   ├── DEPLOYMENT.md              # Deployment guide
│   └── DEVELOPMENT.md             # Development guide
│
├── .env.example                   # Environment template
├── .gitignore                     # Git ignore rules
├── README.md                      # Project overview
└── PROJECT_STRUCTURE.md           # This file
```

## 🏗️ Architecture Overview

### Frontend Architecture
- **React 18** with TypeScript for type safety
- **Material-UI (MUI)** for consistent design system
- **React Router** for client-side routing
- **Context API** for state management
- **Service Worker** for PWA functionality
- **IndexedDB** for offline data storage

### Backend Architecture
- **Flask** web framework with RESTful API design
- **SQLAlchemy** ORM for database operations
- **Celery** for background task processing
- **Redis** for task queue and caching
- **JWT** for stateless authentication
- **CORS** for cross-origin requests

### Data Processing Pipeline
1. **Multi-Source Ingestion**
   - GitHub/Bitbucket repositories via OAuth
   - Database connections (SQL/NoSQL)
   - File uploads with drag-and-drop

2. **Language-Aware Processing**
   - Tree-sitter for code parsing
   - Python AST for Python files
   - PyMuPDF for PDF documents
   - Unstructured.io for various formats

3. **Vector Storage & Retrieval**
   - FAISS for high-performance similarity search
   - Gemini embeddings for semantic understanding
   - Metadata preservation for source attribution

4. **RAG Chat Interface**
   - Context selection and management
   - Streaming responses with citations
   - Offline message queuing

## 🔄 Data Flow

```
User Input → Context Selection → Vector Search → LLM Processing → Response with Citations
     ↓              ↓                ↓              ↓                    ↓
File Upload → Document Processing → Embedding → Vector Storage → Search Index
     ↓              ↓                ↓              ↓                    ↓
Repository → Code Parsing → Chunking → FAISS Index → Similarity Search
```

## 🚀 Key Features Implemented

### ✅ Multi-Source Data Ingestion
- [x] GitHub/Bitbucket repository integration
- [x] Database connectivity (6 database types)
- [x] File upload with 50+ supported formats
- [x] ZIP archive extraction

### ✅ Advanced Document Processing
- [x] Language-aware code parsing
- [x] PDF document processing
- [x] Structured data handling (CSV, JSON, YAML)
- [x] Intelligent chunking strategies

### ✅ RAG Pipeline
- [x] FAISS vector storage
- [x] Gemini LLM integration
- [x] Semantic search with metadata
- [x] Source attribution and citations

### ✅ Progressive Web App
- [x] Service worker implementation
- [x] Offline functionality
- [x] Install prompts
- [x] Background sync
- [x] Push notifications support

### ✅ Modern UI/UX
- [x] Responsive Material-UI design
- [x] Dark/light theme support
- [x] Real-time chat interface
- [x] Context creation wizard
- [x] Mobile-optimized experience

### ✅ Security & Performance
- [x] JWT authentication
- [x] CORS protection
- [x] Input validation
- [x] Rate limiting
- [x] Efficient caching strategies

## 🛠️ Development Workflow

1. **Setup Development Environment**
   ```bash
   ./scripts/deploy.sh
   ```

2. **Frontend Development**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Backend Development**
   ```bash
   cd backend
   python app.py
   ```

4. **Background Tasks**
   ```bash
   celery -A app.celery worker --loglevel=info
   ```

## 📦 Deployment Options

### Development
- Local development with hot reload
- Docker Compose for full stack
- Separate frontend/backend servers

### Production
- Docker containers with Nginx
- Environment-specific configurations
- Horizontal scaling support
- Monitoring and logging

## 🔧 Configuration

### Environment Variables
- **Backend**: Database, Redis, API keys, OAuth credentials
- **Frontend**: API URL, app configuration
- **Docker**: Service orchestration, networking

### Feature Flags
- PWA features (install prompts, offline mode)
- Authentication methods (local, OAuth)
- Data source types (repos, databases, files)

## 📊 Performance Considerations

### Frontend Optimization
- Code splitting and lazy loading
- Service worker caching strategies
- Efficient state management
- Mobile-first responsive design

### Backend Optimization
- Database query optimization
- Vector search performance
- Background task processing
- API response caching

### Scalability
- Horizontal scaling with load balancers
- Database sharding for large datasets
- CDN for static assets
- Microservices architecture ready

---

This project structure provides a solid foundation for a production-ready RAG chatbot PWA with comprehensive features and modern development practices.
