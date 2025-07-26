@echo off
setlocal enabledelayedexpansion

REM RAG Chatbot PWA Windows Deployment Script
REM This script sets up the complete development environment on Windows

title RAG Chatbot PWA Deployment

echo.
echo 🚀 RAG Chatbot PWA Windows Deployment Script
echo ==========================================
echo.

REM Color codes for Windows
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM Function to print colored output (simulated with echo)
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

call :command_exists docker
if errorlevel 1 set "missing_deps=!missing_deps! Docker"

call :command_exists docker-compose
if errorlevel 1 set "missing_deps=!missing_deps! Docker-Compose"

if not "!missing_deps!"=="" (
    call :print_error "Missing dependencies: !missing_deps!"
    echo.
    echo Please install the missing dependencies:
    echo - Node.js 18+: https://nodejs.org/
    echo - Python 3.9+: https://python.org/
    echo - Docker Desktop: https://docker.com/products/docker-desktop
    echo.
    echo Then run this script again.
    pause
    exit /b 1
)

call :print_success "All prerequisites are installed"
goto :eof

:setup_environment
call :print_status "Setting up environment files..."

REM Backend environment
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        call :print_success "Created backend .env file from example"
    ) else (
        call :print_warning "No .env.example found, creating basic .env file"
        (
            echo # Database
            echo DATABASE_URL=postgresql://raguser:ragpass@localhost:5432/ragchatbot
            echo.
            echo # Redis
            echo REDIS_URL=redis://localhost:6379/0
            echo.
            echo # JWT
            echo JWT_SECRET_KEY=your-secret-key-here-change-this-in-production
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
        ) > .env
        call :print_success "Created basic .env file"
    )
) else (
    call :print_warning "Backend .env file already exists"
)

REM Frontend environment
if not exist "frontend\.env" (
    if exist "frontend\.env.example" (
        copy "frontend\.env.example" "frontend\.env" >nul
        call :print_success "Created frontend .env file from example"
    ) else (
        call :print_warning "No frontend\.env.example found, creating basic .env file"
        (
            echo VITE_API_URL=http://localhost:5000
            echo VITE_APP_NAME=RAG Chatbot PWA
        ) > frontend\.env
        call :print_success "Created basic frontend .env file"
    )
) else (
    call :print_warning "Frontend .env file already exists"
)

goto :eof

:install_dependencies
call :print_status "Installing dependencies..."

REM Backend dependencies
call :print_status "Installing Python dependencies..."
cd backend

if not exist "venv" (
    python -m venv venv
    call :print_success "Created Python virtual environment"
)

REM Activate virtual environment
call venv\Scripts\activate.bat

pip install -r requirements.txt
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
call :print_status "Setting up database..."

REM Check if PostgreSQL container is running
docker ps | findstr postgres >nul 2>&1
if not errorlevel 1 (
    call :print_success "PostgreSQL container is already running"
) else (
    call :print_status "Starting PostgreSQL container..."
    docker run -d --name ragchatbot-postgres -e POSTGRES_DB=ragchatbot -e POSTGRES_USER=raguser -e POSTGRES_PASSWORD=ragpass -p 5432:5432 postgres:13
    if errorlevel 1 (
        call :print_error "Failed to start PostgreSQL container"
        pause
        exit /b 1
    )
    
    call :print_status "Waiting for PostgreSQL to be ready..."
    timeout /t 10 /nobreak >nul
    call :print_success "PostgreSQL container started"
)

REM Check if Redis container is running
docker ps | findstr redis >nul 2>&1
if not errorlevel 1 (
    call :print_success "Redis container is already running"
) else (
    call :print_status "Starting Redis container..."
    docker run -d --name ragchatbot-redis -p 6379:6379 redis:6-alpine
    if errorlevel 1 (
        call :print_error "Failed to start Redis container"
        pause
        exit /b 1
    )
    call :print_success "Redis container started"
)

goto :eof

:init_database
call :print_status "Initializing database..."

cd backend
call venv\Scripts\activate.bat

REM Initialize database
flask db upgrade
if errorlevel 1 (
    call :print_error "Failed to initialize database"
    pause
    exit /b 1
)
call :print_success "Database initialized"

cd ..
goto :eof

:start_services
call :print_status "Starting services..."

REM Create a batch file to start Celery worker
cd backend
call venv\Scripts\activate.bat

call :print_status "Starting Celery worker..."
start "Celery Worker" cmd /k "venv\Scripts\activate.bat && celery -A app.celery worker --loglevel=info"
call :print_success "Celery worker started in new window"

call :print_status "Starting Flask backend..."
start "Flask Backend" cmd /k "venv\Scripts\activate.bat && python app.py"
call :print_success "Flask backend started in new window"

cd ..

REM Start React frontend
call :print_status "Starting React frontend..."
cd frontend
start "React Frontend" cmd /k "npm run dev"
call :print_success "React frontend started in new window"

cd ..
goto :eof

:cleanup
call :print_status "Cleaning up containers..."

docker stop ragchatbot-postgres ragchatbot-redis >nul 2>&1
docker rm ragchatbot-postgres ragchatbot-redis >nul 2>&1

call :print_success "Cleanup completed"
goto :eof

:deploy
call :print_status "Starting RAG Chatbot PWA deployment..."

call :check_prerequisites
if errorlevel 1 exit /b 1

call :setup_environment
call :install_dependencies
if errorlevel 1 exit /b 1

call :setup_database
if errorlevel 1 exit /b 1

call :init_database
if errorlevel 1 exit /b 1

call :start_services

call :print_success "🎉 Deployment completed successfully!"
echo.
echo 📱 Frontend: http://localhost:5173
echo 🔧 Backend API: http://localhost:5000
echo 📊 API Docs: http://localhost:5000/api/docs
echo.
echo Services are running in separate windows.
echo Close those windows to stop the services.
echo.
echo Press any key to open the application in your browser...
pause >nul

REM Open the application in default browser
start http://localhost:5173

goto :eof

:stop_services
call :print_status "Stopping services..."

REM Kill processes by window title (this is a simplified approach)
taskkill /FI "WINDOWTITLE eq Celery Worker*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Flask Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq React Frontend*" /F >nul 2>&1

call :print_success "Services stopped"
goto :eof

:show_help
echo Usage: %~nx0 [command]
echo.
echo Commands:
echo   deploy    Start all services (default)
echo   stop      Stop all services
echo   clean     Stop and remove all containers
echo   help      Show this help message
echo.
echo Examples:
echo   %~nx0           # Start all services
echo   %~nx0 deploy    # Start all services
echo   %~nx0 stop      # Stop all services
echo   %~nx0 clean     # Clean up everything
echo.
goto :eof

:main
REM Parse command line arguments
set "command=%~1"
if "%command%"=="" set "command=deploy"

if "%command%"=="deploy" (
    call :deploy
) else if "%command%"=="stop" (
    call :stop_services
) else if "%command%"=="clean" (
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
