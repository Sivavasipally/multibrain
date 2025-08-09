# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Local Development (No Docker - Recommended for Development)
```bash
# Quick setup (Windows)
.\scripts\deploy-local.ps1

# Start development servers
.\scripts\deploy-local.ps1 deploy

# Stop services
.\scripts\deploy-local.ps1 stop

# Clean everything
.\scripts\deploy-local.ps1 clean
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev              # Start development server at http://localhost:5173
npm run build           # Build for production
npm run lint            # ESLint code checking
npm run test            # Run Jest tests
npm run test:coverage   # Run tests with coverage
```

### Backend Development
```bash
cd backend

# Local development (SQLite)
python app_local.py     # Simplified local server at http://localhost:5000

# Full development (Docker)
python app.py           # Full Flask server with PostgreSQL/Redis

# Database operations
python init_database.py # Initialize database
python check_database.py # Verify database
```

### Testing
```bash
# Frontend tests
cd frontend && npm test

# Backend tests
cd backend && python -m pytest tests/
```

### Docker (Production)
```bash
docker-compose up -d    # Full production stack
docker-compose down     # Stop all services
```

## Architecture Overview

### Two Deployment Modes
1. **Local Development** (`app_local.py`): SQLite database, no Redis, simplified dependencies
2. **Full Production** (`app.py`): PostgreSQL, Redis, Celery background tasks

### Frontend (React PWA)
- **Framework**: React 19 + TypeScript + Vite
- **UI Library**: Material-UI (MUI) v7
- **State Management**: React Context API + custom hooks
- **PWA Features**: Service worker, offline storage, installable
- **Main Components**: Located in `src/components/`
  - `Auth/` - Authentication flows
  - `Chat/` - Chat interface and message handling
  - `Context/` - Context creation wizard and management
  - `Layout/` - App layout and navigation
  - `PWA/` - Progressive Web App features

### Backend (Flask API)
- **Framework**: Flask + SQLAlchemy + Flask-JWT-Extended
- **Database Models**: `models.py` with User, Context, ChatSession, Document entities
- **Routes Structure**: `routes/` directory
  - `auth.py` - User authentication
  - `contexts.py` - Context management
  - `chat.py` - Chat functionality
  - `upload.py` - File upload handling
- **Services Layer**: `services/` directory
  - `llm_service.py` - Gemini AI integration
  - `vector_service.py` - FAISS vector search
  - `document_processor.py` - File processing
  - `repository_service.py` - GitHub/Bitbucket integration

### Data Processing Pipeline
1. **Multi-Source Ingestion**: Files, GitHub repos, databases
2. **Language-Aware Processing**: Tree-sitter for code parsing, PyMuPDF for PDFs
3. **Vector Storage**: FAISS for semantic search with Gemini embeddings
4. **RAG Chat**: Context-aware responses with source citations

### Key Technologies
- **Frontend**: React + TypeScript + MUI + Vite + PWA
- **Backend**: Flask + SQLAlchemy + JWT + Celery
- **AI/ML**: Google Gemini API + FAISS + Sentence Transformers
- **Database**: SQLite (local) / PostgreSQL (production)
- **Cache**: In-memory (local) / Redis (production)

## File Organization

### Core Application Files
- `backend/app.py` - Full production Flask server
- `backend/app_local.py` - Simplified local development server
- `backend/models.py` - Database models and relationships
- `frontend/src/App.tsx` - Main React application component
- `frontend/src/services/api.ts` - API client with authentication

### Configuration
- `backend/requirements.txt` - Python dependencies
- `frontend/package.json` - Node.js dependencies and scripts
- `docker-compose.yml` - Full production stack
- `.env` - Environment variables (created by setup script)

### Development Scripts
- `scripts/deploy-local.ps1` - Windows PowerShell setup script
- `scripts/deploy-local.bat` - Windows batch setup script
- `setup-windows.bat` - Interactive Windows setup

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### Contexts
- `GET /api/contexts` - List user contexts
- `POST /api/contexts` - Create new context
- `DELETE /api/contexts/{id}` - Delete context

### Chat
- `POST /api/chat/{context_id}` - Send chat message
- `GET /api/chat/{context_id}/history` - Get chat history

### File Upload
- `POST /api/upload` - Upload files to context

## Environment Variables

### Required for AI Features
- `GEMINI_API_KEY` - Google Gemini API key for AI responses

### Optional (have defaults)
- `DATABASE_URL` - Database connection string
- `JWT_SECRET_KEY` - JWT signing key (auto-generated)
- `REDIS_URL` - Redis connection string

## Development Workflow

1. Use local development mode for most work: `.\scripts\deploy-local.ps1`
2. Frontend runs on `http://localhost:5173` with hot reload
3. Backend runs on `http://localhost:5000` 
4. Database is SQLite file at `backend/ragchatbot.db`
5. Test with full Docker stack before production deployment

## Common Issues

### Python 3.13 Compatibility
Some dependencies have compatibility issues with Python 3.13. The requirements.txt has been modified to exclude problematic packages.

### Windows Development
The local development scripts are optimized for Windows PowerShell. Use `deploy-local.ps1` for best experience.

### Database Migrations
When modifying models, run database initialization scripts or use Flask-Migrate for schema updates.