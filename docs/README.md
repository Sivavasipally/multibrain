# 🤖 RAG Chatbot - Retrieval-Augmented Generation System

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

A sophisticated AI-powered chatbot that combines document retrieval with large language models to provide contextually accurate responses based on uploaded documents.

---

## 🎯 **Quick Start**

### **1. Clone & Setup**
```bash
git clone <repository-url>
cd myrag/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### **2. Configure Environment**
```bash
cp .env.template .env
# Edit .env with your configuration
```

### **3. Initialize Database**
```bash
python -c "from app_local import app, db; app.app_context().push(); db.create_all(); print('Database created')"
```

### **4. Start Application**
```bash
python app_local.py
```

🎉 **Application running at**: `http://localhost:5000`

---

## ✨ **Features**

### **🔐 Core Capabilities**
- **Document Processing**: Upload PDF, Word, Excel, and text files
- **Intelligent Chunking**: Multiple strategies (language-specific, semantic, fixed-size)
- **Vector Search**: FAISS-powered similarity search
- **Multi-Model Support**: Google Gemini and OpenAI integration
- **Context Management**: Organize documents into searchable contexts
- **Real-time Chat**: Interactive conversations with document-based responses
- **User Management**: Secure authentication and user isolation
- **Admin Dashboard**: System monitoring and management

### **🚀 Advanced Features**
- **Citation Generation**: Automatic source attribution
- **Performance Monitoring**: Real-time system metrics
- **Caching System**: Intelligent response caching
- **Rate Limiting**: API protection and abuse prevention
- **Security Headers**: Comprehensive security implementation
- **Health Checks**: Application monitoring and alerting

---

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React/Vue)   │◄──►│   (Flask)       │◄──►│   (SQLite/PG)   │
│   Port: 5173    │    │   Port: 5000    │    │   File/Cloud    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   AI Services   │
                    │   (Gemini/GPT)  │
                    └─────────────────┘
```

### **Technology Stack**
- **Backend**: Flask 3.0+, SQLAlchemy 2.0+, JWT Authentication
- **AI/ML**: Google Gemini, OpenAI GPT, Sentence Transformers, FAISS
- **Database**: SQLite (development), PostgreSQL (production)
- **Frontend**: React/Vue.js, TypeScript, Vite
- **Deployment**: Docker, Docker Compose, Cloud platforms

---

## 📚 **Documentation**

| Document | Description |
|----------|-------------|
| **[📖 Knowledge Document](KNOWLEDGE_DOCUMENT.md)** | Complete application guide with architecture, logic flow, and detailed explanations |
| **[🔌 API Reference](API_REFERENCE.md)** | Comprehensive API documentation with examples and error codes |
| **[🚀 Deployment Guide](DEPLOYMENT_GUIDE.md)** | Step-by-step deployment instructions for various platforms |
| **[📁 File Structure Guide](FILE_STRUCTURE_GUIDE.md)** | Detailed explanation of codebase organization and file purposes |
| **[🔧 Fixes Applied](FIXES_APPLIED.md)** | Documentation of all applied fixes and improvements |

---

## 🛠️ **Installation & Setup**

### **Prerequisites**
- Python 3.10+ (recommended 3.11)
- Node.js 16+ (for frontend)
- 4GB+ RAM
- 10GB+ free disk space

### **Development Setup**

#### **Backend Setup**
```bash
# Clone repository
git clone <repository-url>
cd myrag/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env with your settings:
# - JWT_SECRET_KEY=your-secret-key
# - GEMINI_API_KEY=your-gemini-key (optional)
# - OPENAI_API_KEY=your-openai-key (optional)

# Initialize database
python -c "from app_local import app, db; app.app_context().push(); db.create_all()"

# Run tests
python test_all_fixes.py

# Start server
python app_local.py
```

#### **Frontend Setup** (if applicable)
```bash
cd ../frontend
npm install
npm run dev
```

### **Docker Setup**
```bash
# Using Docker Compose
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

---

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Security (Required)
JWT_SECRET_KEY=your-super-secret-jwt-key-here
SECRET_KEY=your-flask-secret-key-here

# Database
DATABASE_URL=sqlite:///ragchatbot.db

# AI Services (Optional)
GEMINI_API_KEY=your-gemini-api-key-here
OPENAI_API_KEY=your-openai-api-key-here

# File Upload
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=104857600

# Application
FRONTEND_URL=http://localhost:5173
FLASK_ENV=development
FLASK_DEBUG=false
```

### **Chunking Strategies**
- **Language-Specific**: Intelligent chunking based on language structure
- **Semantic**: Embedding-based semantic chunking
- **Fixed-Size**: Simple character-based chunking

### **Supported File Types**
- **Documents**: PDF (.pdf), Word (.docx), Excel (.xlsx)
- **Text**: Plain text (.txt), Markdown (.md)
- **Size Limit**: 16MB per file (configurable)

---

## 🔌 **API Usage**

### **Authentication**
```bash
# Register user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "email": "user@example.com", "password": "password"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'
```

### **Context Management**
```bash
# Create context
curl -X POST http://localhost:5000/api/contexts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Documents", "source_type": "files", "chunk_strategy": "language-specific"}'

# Upload files
curl -X POST http://localhost:5000/api/upload/files \
  -H "Authorization: Bearer <token>" \
  -F "files=@document.pdf" \
  -F "context_id=1"
```

### **Chat Queries**
```bash
# Send query
curl -X POST http://localhost:5000/api/chat/query \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the main points?", "context_ids": [1]}'
```

---

## 🧪 **Testing**

### **Run Test Suite**
```bash
# Comprehensive tests
python test_all_fixes.py

# Specific tests
python test_context_fix.py
python test_file_upload.py

# API tests
python -m pytest tests/ -v
```

### **Health Check**
```bash
curl http://localhost:5000/api/health
```

---

## 🚀 **Deployment**

### **Local Development**
```bash
python app_local.py
```

### **Production (Docker)**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### **Cloud Platforms**

#### **Heroku**
```bash
heroku create your-app-name
heroku config:set JWT_SECRET_KEY=your-secret
git push heroku main
```

#### **AWS EC2**
```bash
# See DEPLOYMENT_GUIDE.md for detailed instructions
```

#### **Google Cloud**
```bash
gcloud app deploy app.yaml
```

---

## 📊 **Monitoring**

### **Health Endpoints**
- **Basic**: `GET /api/health`
- **Detailed**: `GET /api/health/detailed`
- **Metrics**: `GET /api/metrics` (Prometheus format)

### **Admin Dashboard**
- **URL**: `http://localhost:5000/api/admin/dashboard`
- **Features**: System stats, user management, performance metrics

### **Logging**
```bash
# View application logs
tail -f instance/logs/app.log

# Error logs
tail -f instance/logs/error.log
```

---

## 🔒 **Security**

### **Security Features**
- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: Werkzeug secure password hashing
- **Security Headers**: XSS, CSRF, clickjacking protection
- **Input Validation**: Comprehensive input sanitization
- **File Upload Security**: Type and size validation
- **Rate Limiting**: API abuse prevention

### **Security Best Practices**
- Use strong JWT secret keys
- Enable HTTPS in production
- Regular security updates
- Monitor for suspicious activity
- Implement proper backup strategies

---

## 🤝 **Contributing**

### **Development Workflow**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python test_all_fixes.py`
5. Submit a pull request

### **Code Standards**
- **Python**: Follow PEP 8, use Black for formatting
- **TypeScript**: Use ESLint and Prettier
- **Documentation**: Update relevant docs for changes
- **Testing**: Add tests for new features

---

## 📝 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 **Support**

### **Common Issues**
- **Database locked**: Restart the application
- **Import errors**: Check virtual environment activation
- **File upload fails**: Check file size and type
- **AI service errors**: Verify API keys

### **Getting Help**
- **Documentation**: Check the comprehensive docs in this repository
- **Issues**: Create an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions

---

## 🎉 **Acknowledgments**

- **Flask**: Web framework
- **SQLAlchemy**: Database ORM
- **Google Gemini**: AI language model
- **OpenAI**: GPT models
- **FAISS**: Vector similarity search
- **Sentence Transformers**: Text embeddings

---

## 📈 **Roadmap**

### **Upcoming Features**
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Plugin system for custom processors
- [ ] Real-time collaboration
- [ ] Mobile application
- [ ] Enterprise SSO integration

### **Performance Improvements**
- [ ] Async processing
- [ ] Advanced caching strategies
- [ ] Database optimization
- [ ] Load balancing support

---

**Version**: 1.0.0  
**Last Updated**: 2024-01-01  
**Status**: Production Ready  
**Maintainer**: RAG Chatbot Development Team
