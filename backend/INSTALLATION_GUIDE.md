# 🚀 RAG Chatbot Installation Guide

This guide will help you install all dependencies for the RAG Chatbot application.

## 📋 Prerequisites

- **Python 3.10+** (Python 3.13 supported with some limitations)
- **Virtual Environment** (recommended)
- **Git** (for cloning the repository)

## 🔧 Quick Installation

### Option 1: Automated Installation (Recommended)

```bash
# Navigate to backend directory
cd backend

# Run the automated installer
python install_with_pip.py
```

### Option 2: Manual Installation

```bash
# Install from working requirements file
pip install -r requirements-working.txt
```

### Option 3: Windows Batch Script

```bash
# Run the batch installer (Windows only)
install_simple.bat
```

## 🐍 Virtual Environment Setup

### Create and Activate Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

## 📦 Dependency Categories

### ✅ Core Dependencies (Required)
- Flask and extensions
- SQLAlchemy
- Authentication (JWT)
- HTTP requests
- Environment variables

### ✅ Data Processing (Required)
- NumPy (version < 2.0 for compatibility)
- Pandas
- Document processing (Word, Excel)

### ✅ AI/ML Dependencies (Required for full functionality)
- Google Generative AI
- OpenAI API client
- Sentence Transformers
- FAISS vector database

### ⚠️ Optional Dependencies
- PyMuPDF (PDF processing)
- System monitoring (psutil)
- Development tools (pytest, black, flake8)

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. NumPy Compatibility Error
```
AttributeError: _ARRAY_API not found
```

**Solution:**
```bash
pip install "numpy<2.0" --force-reinstall
```

#### 2. Tree-sitter Installation Fails
```
No version of tree-sitter-kotlin==0.3.1
```

**Solution:** Tree-sitter is optional for basic functionality. Skip it or use:
```bash
pip install tree-sitter>=0.20.0  # Basic tree-sitter only
```

#### 3. FAISS Installation Fails

**Solution 1 - Use Conda:**
```bash
conda install -c conda-forge faiss-cpu
```

**Solution 2 - Skip FAISS:**
The app will work without FAISS using basic search functionality.

#### 4. Sentence Transformers Fails

**Solution:** Install PyTorch first:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install sentence-transformers
```

#### 5. PyMuPDF Installation Fails

**Solution:** Use PyPDF2 as alternative:
```bash
pip install PyPDF2>=3.0.1
```

## 🧪 Testing Installation

### Quick Test
```bash
python -c "import flask, sqlalchemy, numpy, pandas, requests; print('✅ Core dependencies working!')"
```

### Comprehensive Test
```bash
python -c "
import flask, sqlalchemy, numpy, pandas, requests
import google.generativeai, openai
import sentence_transformers, faiss
print('✅ All dependencies working!')
"
```

## 🚀 Running the Application

### 1. Set Environment Variables
Create a `.env` file in the backend directory:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here
```

### 2. Initialize Database
```bash
python -c "from app_local import app, db; app.app_context().push(); db.create_all()"
```

### 3. Start the Application
```bash
python app_local.py
```

### 4. Access the Application
Open your browser and go to: `http://localhost:5000`

## 📁 File Structure

```
backend/
├── requirements.txt              # Original requirements (may have issues)
├── requirements-working.txt      # Tested working requirements
├── requirements-python313.txt    # Python 3.13 compatible
├── requirements-minimal.txt      # Minimal requirements
├── install_with_pip.py          # Automated installer
├── install_simple.bat           # Windows batch installer
├── app_local.py                 # Main application
└── INSTALLATION_GUIDE.md        # This guide
```

## 🔍 Verification Checklist

After installation, verify these components work:

- [ ] ✅ Flask web server starts
- [ ] ✅ Database connection works
- [ ] ✅ Authentication system works
- [ ] ✅ File upload functionality
- [ ] ✅ AI/LLM integration (Gemini/OpenAI)
- [ ] ✅ Vector search (if FAISS installed)
- [ ] ✅ Document processing (PDF, Word, Excel)

## 🆘 Getting Help

If you encounter issues:

1. **Check Python Version:** Ensure you're using Python 3.10+
2. **Virtual Environment:** Make sure it's activated
3. **Dependencies:** Try installing one package at a time
4. **Logs:** Check error messages for specific package issues
5. **Alternative Packages:** Use fallback options for failed packages

## 🎯 Minimal Installation

For basic functionality, you only need:

```bash
pip install Flask Flask-SQLAlchemy Flask-CORS Flask-JWT-Extended
pip install python-dotenv requests numpy pandas
pip install google-generativeai openai
```

This will give you:
- ✅ Web interface
- ✅ User authentication
- ✅ Basic file processing
- ✅ AI chat functionality
- ❌ Advanced vector search
- ❌ Complex document processing

## 🚀 Production Deployment

For production, also install:
```bash
pip install gunicorn psutil
```

And use:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app_local:app
```

---

## 📞 Support

- **Documentation:** Check the main README.md
- **Issues:** Create GitHub issues for bugs
- **Community:** Join our Discord/Slack for help

Happy coding! 🎉
