@echo off
echo ========================================
echo RAG Chatbot Simple Installation
echo ========================================
echo.

REM Check if virtual environment is activated
if "%VIRTUAL_ENV%"=="" (
    echo Warning: Virtual environment not detected
    echo Please activate your virtual environment first:
    echo   venv\Scripts\activate
    echo.
    set /p continue="Continue anyway? (y/N): "
    if /i not "%continue%"=="y" (
        echo Exiting...
        pause
        exit /b 1
    )
)

echo Installing core dependencies...
echo.

REM Core Flask dependencies
pip install Flask>=3.0.0
pip install Flask-SQLAlchemy>=3.1.1
pip install Flask-CORS>=4.0.0
pip install Flask-JWT-Extended>=4.6.0
pip install SQLAlchemy>=2.0.25

REM Basic utilities
pip install python-dotenv>=1.0.0
pip install requests>=2.31.0
pip install werkzeug>=3.0.0
pip install click>=8.1.0
pip install itsdangerous>=2.1.0
pip install jinja2>=3.1.0
pip install markupsafe>=2.1.0

echo.
echo Installing data processing dependencies...
pip install numpy>=1.24.4
pip install pandas>=2.1.4
pip install python-docx>=1.1.0
pip install openpyxl>=3.1.2

echo.
echo Installing AI dependencies...
pip install google-generativeai>=0.3.2
pip install openai>=1.6.1

echo.
echo Installing optional dependencies...
pip install psutil>=5.9.0
pip install pytest>=7.4.3

echo.
echo Attempting document processing...
pip install PyMuPDF>=1.23.8
if errorlevel 1 (
    echo PyMuPDF failed, trying PyPDF2...
    pip install PyPDF2>=3.0.1
)

echo.
echo Attempting advanced AI packages (may fail)...
pip install sentence-transformers>=2.2.2
if errorlevel 1 (
    echo Sentence Transformers failed - this is optional
)

pip install faiss-cpu>=1.7.4
if errorlevel 1 (
    echo FAISS failed - this is optional
)

echo.
echo ========================================
echo Testing installation...
echo ========================================

python -c "import flask; print('✓ Flask')" 2>nul || echo "✗ Flask"
python -c "import sqlalchemy; print('✓ SQLAlchemy')" 2>nul || echo "✗ SQLAlchemy"
python -c "import numpy; print('✓ NumPy')" 2>nul || echo "✗ NumPy"
python -c "import pandas; print('✓ Pandas')" 2>nul || echo "✗ Pandas"
python -c "import requests; print('✓ Requests')" 2>nul || echo "✗ Requests"
python -c "import google.generativeai; print('✓ Google AI')" 2>nul || echo "✗ Google AI"

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Make sure your virtual environment is activated
echo 2. Run: python app_local.py
echo 3. Open http://localhost:5000 in your browser
echo.
echo If some packages failed, that's OK - the app will still work
echo with basic functionality.
echo.

pause
