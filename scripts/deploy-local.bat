@echo off
setlocal enabledelayedexpansion

REM RAG Chatbot PWA Local Deployment Script (No Docker)
REM This script sets up everything locally without Docker containers

title RAG Chatbot PWA - Local Deployment

echo.
echo 🚀 RAG Chatbot PWA Local Deployment (No Docker)
echo ===============================================
echo.

REM Color codes for Windows
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

goto :main

:print_status
echo %BLUE%[INFO]%NC% %~1
goto :eof

:print_success
echo %GREEN%[SUCCESS]%NC% %~1
goto :eof

:print_warning
echo %YELLOW%[WARNING]%NC% %~1
goto :eof

:print_error
echo %RED%[ERROR]%NC% %~1
goto :eof

:command_exists
where %1 >nul 2>&1
goto :eof

:check_prerequisites
call :print_status "Checking prerequisites..."

set "missing_deps="

call :command_exists node
if errorlevel 1 set "missing_deps=!missing_deps! Node.js"

call :command_exists python
if errorlevel 1 set "missing_deps=!missing_deps! Python"

call :command_exists pip
if errorlevel 1 set "missing_deps=!missing_deps! pip"

call :command_exists npm
if errorlevel 1 set "missing_deps=!missing_deps! npm"

if not "!missing_deps!"=="" (
    call :print_error "Missing dependencies: !missing_deps!"
    echo.
    echo Please install the missing dependencies:
    echo - Node.js 18+: https://nodejs.org/
    echo - Python 3.9+: https://python.org/
    echo.
    echo Then run this script again.
    pause
    exit /b 1
)

call :print_success "All prerequisites are installed"
goto :eof

:setup_environment
call :print_status "Setting up environment files..."

REM Backend environment for local SQLite
if not exist ".env" (
    call :print_status "Creating local .env file with SQLite database..."
    (
        echo # Local SQLite Database
        echo DATABASE_URL=sqlite:///./ragchatbot.db
        echo.
        echo # In-memory cache ^(no Redis needed^)
        echo REDIS_URL=memory://
        echo.
        echo # JWT
        echo JWT_SECRET_KEY=local-development-secret-key-change-in-production
        echo.
        echo # Gemini AI ^(replace with your API key^)
        echo GEMINI_API_KEY=your-gemini-api-key-here
        echo.
        echo # GitHub OAuth ^(optional^)
        echo GITHUB_CLIENT_ID=your-github-client-id
        echo GITHUB_CLIENT_SECRET=your-github-client-secret
        echo.
        echo # File Upload
        echo UPLOAD_FOLDER=uploads
        echo MAX_CONTENT_LENGTH=104857600
        echo.
        echo # CORS
        echo FRONTEND_URL=http://localhost:5173
        echo.
        echo # Local Development
        echo FLASK_ENV=development
        echo FLASK_DEBUG=1
    ) > .env
    call :print_success "Created local .env file with SQLite"
) else (
    call :print_warning "Backend .env file already exists"
)

REM Frontend environment
if not exist "frontend\.env" (
    (
        echo VITE_API_URL=http://localhost:5000
        echo VITE_APP_NAME=RAG Chatbot PWA
    ) > frontend\.env
    call :print_success "Created frontend .env file"
) else (
    call :print_warning "Frontend .env file already exists"
)

goto :eof

:install_dependencies
call :print_status "Installing dependencies..."

REM Backend dependencies
call :print_status "Setting up Python environment..."
cd backend

if not exist "venv" (
    python -m venv venv
    if errorlevel 1 (
        call :print_error "Failed to create Python virtual environment"
        pause
        exit /b 1
    )
    call :print_success "Created Python virtual environment"
)

REM Activate virtual environment
call venv\Scripts\activate.bat

call :print_status "Installing Python dependencies for local development..."
pip install --upgrade pip

REM Try local requirements first, fallback to main requirements
if exist "requirements-local.txt" (
    pip install -r requirements-local.txt
) else (
    pip install -r requirements.txt
)

if errorlevel 1 (
    call :print_error "Failed to install Python dependencies"
    pause
    exit /b 1
)

call :print_success "Installed Python dependencies"

cd ..

REM Frontend dependencies
call :print_status "Installing Node.js dependencies..."
cd frontend
call npm install
if errorlevel 1 (
    call :print_error "Failed to install Node.js dependencies"
    pause
    exit /b 1
)
call :print_success "Installed Node.js dependencies"
cd ..

goto :eof

:setup_database
call :print_status "Setting up local SQLite database..."

cd backend
call venv\Scripts\activate.bat

REM Create uploads directory
if not exist "uploads" mkdir uploads

REM Initialize database
call :print_status "Initializing SQLite database..."
python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database tables created successfully')
"

if errorlevel 1 (
    call :print_error "Failed to initialize database"
    pause
    exit /b 1
)

call :print_success "SQLite database initialized"
cd ..
goto :eof

:create_local_config
call :print_status "Creating local configuration..."

REM Create a simplified app.py for local development
cd backend

if not exist "app_local.py" (
    call :print_status "Creating local app configuration..."
    (
        echo import os
        echo from flask import Flask
        echo from flask_sqlalchemy import SQLAlchemy
        echo from flask_cors import CORS
        echo from flask_jwt_extended import JWTManager
        echo.
        echo # Create Flask app
        echo app = Flask^(__name__^)
        echo.
        echo # Configuration
        echo app.config['SECRET_KEY'] = os.getenv^('JWT_SECRET_KEY', 'dev-secret'^)
        echo app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv^('DATABASE_URL', 'sqlite:///ragchatbot.db'^)
        echo app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        echo app.config['JWT_SECRET_KEY'] = os.getenv^('JWT_SECRET_KEY', 'dev-secret'^)
        echo app.config['UPLOAD_FOLDER'] = os.getenv^('UPLOAD_FOLDER', 'uploads'^)
        echo app.config['MAX_CONTENT_LENGTH'] = int^(os.getenv^('MAX_CONTENT_LENGTH', '104857600'^)^)
        echo.
        echo # Initialize extensions
        echo db = SQLAlchemy^(app^)
        echo jwt = JWTManager^(app^)
        echo CORS^(app, origins=[os.getenv^('FRONTEND_URL', 'http://localhost:5173'^)]^)
        echo.
        echo # Import models and routes
        echo from models import *
        echo from routes.auth import auth_bp
        echo from routes.contexts import contexts_bp
        echo from routes.chat import chat_bp
        echo from routes.upload import upload_bp
        echo.
        echo # Register blueprints
        echo app.register_blueprint^(auth_bp, url_prefix='/api/auth'^)
        echo app.register_blueprint^(contexts_bp, url_prefix='/api/contexts'^)
        echo app.register_blueprint^(chat_bp, url_prefix='/api/chat'^)
        echo app.register_blueprint^(upload_bp, url_prefix='/api/upload'^)
        echo.
        echo if __name__ == '__main__':
        echo     with app.app_context^(^):
        echo         db.create_all^(^)
        echo     app.run^(debug=True, host='0.0.0.0', port=5000^)
    ) > app_local.py
    call :print_success "Created local app configuration"
)

cd ..
goto :eof

:start_services
call :print_status "Starting services locally..."

REM Create vector_store directory
if not exist "vector_store" mkdir vector_store

REM Start Flask backend
call :print_status "Starting Flask backend..."
cd backend
start "Flask Backend" cmd /k "venv\Scripts\activate.bat && python app_local.py"
call :print_success "Flask backend started in new window"
cd ..

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start React frontend
call :print_status "Starting React frontend..."
cd frontend
start "React Frontend" cmd /k "npm run dev"
call :print_success "React frontend started in new window"
cd ..

goto :eof

:check_services
call :print_status "Checking if services are running..."

REM Check if backend is responding
timeout /t 5 /nobreak >nul
curl -s http://localhost:5000/api/auth/profile >nul 2>&1
if errorlevel 1 (
    call :print_warning "Backend may still be starting up..."
) else (
    call :print_success "Backend is responding"
)

REM Check if frontend is responding
curl -s http://localhost:5173 >nul 2>&1
if errorlevel 1 (
    call :print_warning "Frontend may still be starting up..."
) else (
    call :print_success "Frontend is responding"
)

goto :eof

:show_info
call :print_success "🎉 Local deployment completed!"
echo.
echo 📱 Frontend: http://localhost:5173
echo 🔧 Backend API: http://localhost:5000
echo 📊 API Health: http://localhost:5000/api/auth/profile
echo.
echo 📁 Database: SQLite file in backend/ragchatbot.db
echo 📁 Uploads: backend/uploads/
echo 📁 Vector Store: vector_store/
echo.
echo ⚠️  Note: This is a local development setup
echo    - Uses SQLite instead of PostgreSQL
echo    - No Redis ^(in-memory caching^)
echo    - No background task processing
echo    - File uploads stored locally
echo.
echo 🔧 To stop services:
echo    - Close the Flask Backend window
echo    - Close the React Frontend window
echo    - Or run: scripts\deploy-local.bat stop
echo.
goto :eof

:stop_services
call :print_status "Stopping local services..."

REM Kill processes by window title
taskkill /FI "WINDOWTITLE eq Flask Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq React Frontend*" /F >nul 2>&1

REM Also try to kill by process name
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM node.exe /F >nul 2>&1

call :print_success "Local services stopped"
goto :eof

:cleanup
call :print_status "Cleaning up local files..."

REM Remove database
if exist "backend\ragchatbot.db" (
    del "backend\ragchatbot.db"
    call :print_success "Removed SQLite database"
)

REM Remove uploads
if exist "backend\uploads" (
    rmdir /s /q "backend\uploads"
    call :print_success "Removed uploads directory"
)

REM Remove vector store
if exist "vector_store" (
    rmdir /s /q "vector_store"
    call :print_success "Removed vector store"
)

REM Remove node_modules (optional)
set /p remove_deps="Remove node_modules and Python venv? (y/N): "
if /i "%remove_deps%"=="y" (
    if exist "frontend\node_modules" (
        rmdir /s /q "frontend\node_modules"
        call :print_success "Removed frontend node_modules"
    )
    if exist "backend\venv" (
        rmdir /s /q "backend\venv"
        call :print_success "Removed Python virtual environment"
    )
)

call :print_success "Cleanup completed"
goto :eof

:show_help
echo Usage: %~nx0 [command]
echo.
echo Commands:
echo   deploy    Start all services locally ^(default^)
echo   stop      Stop all services
echo   clean     Clean up local files
echo   help      Show this help message
echo.
echo Examples:
echo   %~nx0           # Start all services locally
echo   %~nx0 deploy    # Start all services locally
echo   %~nx0 stop      # Stop all services
echo   %~nx0 clean     # Clean up everything
echo.
echo This script runs everything locally without Docker:
echo - SQLite database instead of PostgreSQL
echo - In-memory caching instead of Redis
echo - Local file storage
echo - No background task processing
echo.
goto :eof

:main
REM Parse command line arguments
set "command=%~1"
if "%command%"=="" set "command=deploy"

if "%command%"=="deploy" (
    call :check_prerequisites
    if errorlevel 1 exit /b 1
    
    call :setup_environment
    call :install_dependencies
    if errorlevel 1 exit /b 1
    
    call :setup_database
    if errorlevel 1 exit /b 1
    
    call :create_local_config
    call :start_services
    call :check_services
    call :show_info
    
    set /p open="Open application in browser? (y/N): "
    if /i "!open!"=="y" start http://localhost:5173
    
) else if "%command%"=="stop" (
    call :stop_services
) else if "%command%"=="clean" (
    call :stop_services
    call :cleanup
) else if "%command%"=="help" (
    call :show_help
) else (
    call :print_error "Unknown command: %command%"
    echo.
    call :show_help
    exit /b 1
)

echo.
echo Press any key to exit...
pause >nul
