@echo off
echo ========================================
echo RAG Chatbot Dependency Installation
echo ========================================
echo.

REM Check if virtual environment is activated
if "%VIRTUAL_ENV%"=="" (
    echo Warning: Virtual environment not detected
    echo Please activate your virtual environment first:
    echo   venv\Scripts\activate
    echo.
    pause
    exit /b 1
)

echo Virtual environment detected: %VIRTUAL_ENV%
echo.

echo ========================================
echo Stage 1: Core Flask Dependencies
echo ========================================

uv pip install Flask>=3.0.0
uv pip install Flask-SQLAlchemy>=3.1.1
uv pip install Flask-CORS>=4.0.0
uv pip install Flask-JWT-Extended>=4.6.0
uv pip install SQLAlchemy>=2.0.25
uv pip install python-dotenv>=1.0.0
uv pip install requests>=2.31.0
uv pip install werkzeug>=3.0.0

echo.
echo ========================================
echo Stage 2: Basic Utilities
echo ========================================

uv pip install click>=8.1.0
uv pip install itsdangerous>=2.1.0
uv pip install jinja2>=3.1.0
uv pip install markupsafe>=2.1.0
uv pip install python-dateutil>=2.8.2

echo.
echo ========================================
echo Stage 3: Data Processing
echo ========================================

uv pip install numpy>=1.24.4
if errorlevel 1 (
    echo Warning: NumPy installation failed
    echo Trying alternative installation...
    pip install numpy>=1.24.4
)

uv pip install pandas>=2.1.4
if errorlevel 1 (
    echo Warning: Pandas installation failed
)

echo.
echo ========================================
echo Stage 4: Document Processing
echo ========================================

uv pip install python-docx>=1.1.0
uv pip install openpyxl>=3.1.2

echo Attempting PyMuPDF installation...
uv pip install PyMuPDF>=1.23.8
if errorlevel 1 (
    echo PyMuPDF failed, trying PyPDF2 as alternative...
    uv pip install PyPDF2>=3.0.1
)

echo.
echo ========================================
echo Stage 5: AI/ML Dependencies
echo ========================================

echo Installing Google Generative AI...
uv pip install google-generativeai>=0.3.2

echo Installing OpenAI client...
uv pip install openai>=1.6.1

echo Attempting Sentence Transformers...
uv pip install sentence-transformers>=2.2.2
if errorlevel 1 (
    echo Warning: Sentence Transformers failed
    echo You may need to install PyTorch first:
    echo   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
)

echo Attempting FAISS CPU...
uv pip install faiss-cpu>=1.7.4
if errorlevel 1 (
    echo Warning: FAISS CPU failed
    echo Alternative: conda install -c conda-forge faiss-cpu
)

echo.
echo ========================================
echo Stage 6: System Monitoring
echo ========================================

uv pip install psutil>=5.9.0
if errorlevel 1 (
    echo Warning: psutil installation failed
)

echo.
echo ========================================
echo Stage 7: Development Tools
echo ========================================

uv pip install pytest>=7.4.3
uv pip install black>=23.11.0
uv pip install flake8>=6.1.0
uv pip install gunicorn>=21.2.0

echo.
echo ========================================
echo Installation Summary
echo ========================================

echo Testing basic imports...
python -c "import flask; print('✓ Flask')" 2>nul || echo "✗ Flask"
python -c "import sqlalchemy; print('✓ SQLAlchemy')" 2>nul || echo "✗ SQLAlchemy"
python -c "import numpy; print('✓ NumPy')" 2>nul || echo "✗ NumPy"
python -c "import pandas; print('✓ Pandas')" 2>nul || echo "✗ Pandas"
python -c "import requests; print('✓ Requests')" 2>nul || echo "✗ Requests"
python -c "import google.generativeai; print('✓ Google AI')" 2>nul || echo "✗ Google AI"

echo.
echo ========================================
echo Next Steps
echo ========================================
echo 1. Check the output above for any failed packages
echo 2. Install missing packages manually if needed
echo 3. Run: python app_local.py to test the application
echo.
echo If you encounter issues:
echo - Some packages may not be available for Python 3.13 yet
echo - Try using conda for AI/ML packages
echo - Use requirements-minimal.txt for basic functionality
echo.

pause
