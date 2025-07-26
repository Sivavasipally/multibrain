@echo off
setlocal enabledelayedexpansion

REM RAG Chatbot PWA Test Runner Script
REM Runs comprehensive tests for both frontend and backend

title RAG Chatbot PWA - Test Runner

echo.
echo 🧪 RAG Chatbot PWA Test Runner
echo ==============================
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

:run_backend_tests
call :print_status "Running backend tests..."

cd backend

REM Check if virtual environment exists
if not exist "venv" (
    call :print_error "Python virtual environment not found. Run deploy script first."
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install test dependencies if not present
pip show pytest >nul 2>&1
if errorlevel 1 (
    call :print_status "Installing test dependencies..."
    pip install pytest pytest-flask pytest-cov pytest-mock
)

REM Run tests with coverage
call :print_status "Running Python tests with coverage..."
pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing

if errorlevel 1 (
    call :print_error "Backend tests failed"
    cd ..
    exit /b 1
)

call :print_success "Backend tests passed"
cd ..
goto :eof

:run_frontend_tests
call :print_status "Running frontend tests..."

cd frontend

REM Check if node_modules exists
if not exist "node_modules" (
    call :print_error "Node modules not found. Run deploy script first."
    exit /b 1
)

REM Install test dependencies if not present
if not exist "node_modules\jest" (
    call :print_status "Installing test dependencies..."
    npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event @types/jest jest jest-environment-jsdom msw fake-indexeddb
)

REM Run tests with coverage
call :print_status "Running React tests with coverage..."
npm run test:ci

if errorlevel 1 (
    call :print_error "Frontend tests failed"
    cd ..
    exit /b 1
)

call :print_success "Frontend tests passed"
cd ..
goto :eof

:run_integration_tests
call :print_status "Running integration tests..."

REM Start backend in test mode
cd backend
call venv\Scripts\activate.bat

set FLASK_ENV=testing
set DATABASE_URL=sqlite:///test.db

start "Test Backend" cmd /k "python app_local.py"
call :print_status "Test backend started"

REM Wait for backend to start
timeout /t 5 /nobreak >nul

cd ..

REM Run frontend integration tests
cd frontend
call :print_status "Running integration tests..."

REM This would run E2E tests with tools like Cypress or Playwright
REM For now, we'll just run a basic connectivity test
curl -s http://localhost:5000/health >nul 2>&1
if errorlevel 1 (
    call :print_warning "Backend not responding for integration tests"
) else (
    call :print_success "Backend is responding"
)

cd ..

REM Stop test backend
taskkill /FI "WINDOWTITLE eq Test Backend*" /F >nul 2>&1

goto :eof

:run_linting
call :print_status "Running code linting..."

REM Backend linting
cd backend
if exist "venv" (
    call venv\Scripts\activate.bat
    
    REM Install linting tools if not present
    pip show flake8 >nul 2>&1
    if errorlevel 1 (
        pip install flake8 black isort
    )
    
    call :print_status "Running Python linting..."
    flake8 . --max-line-length=88 --extend-ignore=E203,W503
    if errorlevel 1 (
        call :print_warning "Python linting issues found"
    ) else (
        call :print_success "Python linting passed"
    )
)
cd ..

REM Frontend linting
cd frontend
if exist "node_modules" (
    call :print_status "Running TypeScript/React linting..."
    npm run lint
    if errorlevel 1 (
        call :print_warning "TypeScript/React linting issues found"
    ) else (
        call :print_success "TypeScript/React linting passed"
    )
)
cd ..

goto :eof

:run_security_tests
call :print_status "Running security tests..."

REM Backend security
cd backend
if exist "venv" (
    call venv\Scripts\activate.bat
    
    REM Install security tools if not present
    pip show bandit >nul 2>&1
    if errorlevel 1 (
        pip install bandit safety
    )
    
    call :print_status "Running Python security scan..."
    bandit -r . -f json -o bandit-report.json
    if errorlevel 1 (
        call :print_warning "Security issues found in Python code"
    ) else (
        call :print_success "Python security scan passed"
    )
    
    call :print_status "Checking for known vulnerabilities..."
    safety check
    if errorlevel 1 (
        call :print_warning "Known vulnerabilities found in dependencies"
    ) else (
        call :print_success "No known vulnerabilities found"
    )
)
cd ..

REM Frontend security
cd frontend
if exist "node_modules" (
    call :print_status "Running npm audit..."
    npm audit --audit-level=moderate
    if errorlevel 1 (
        call :print_warning "Security vulnerabilities found in npm packages"
    ) else (
        call :print_success "npm audit passed"
    )
)
cd ..

goto :eof

:generate_reports
call :print_status "Generating test reports..."

REM Create reports directory
if not exist "test-reports" mkdir test-reports

REM Copy coverage reports
if exist "backend\htmlcov" (
    xcopy /E /I "backend\htmlcov" "test-reports\backend-coverage" >nul
    call :print_success "Backend coverage report copied"
)

if exist "frontend\coverage" (
    xcopy /E /I "frontend\coverage" "test-reports\frontend-coverage" >nul
    call :print_success "Frontend coverage report copied"
)

REM Generate summary report
(
    echo Test Summary Report
    echo ===================
    echo Generated: %date% %time%
    echo.
    echo Backend Tests: See test-reports\backend-coverage\index.html
    echo Frontend Tests: See test-reports\frontend-coverage\lcov-report\index.html
    echo.
    echo Security Reports:
    if exist "backend\bandit-report.json" echo - Backend Security: backend\bandit-report.json
    echo.
) > test-reports\summary.txt

call :print_success "Test reports generated in test-reports\ directory"

goto :eof

:show_help
echo Usage: %~nx0 [command]
echo.
echo Commands:
echo   all         Run all tests ^(default^)
echo   backend     Run backend tests only
echo   frontend    Run frontend tests only
echo   integration Run integration tests
echo   lint        Run code linting
echo   security    Run security tests
echo   reports     Generate test reports
echo   help        Show this help message
echo.
echo Examples:
echo   %~nx0           # Run all tests
echo   %~nx0 backend   # Run backend tests only
echo   %~nx0 frontend  # Run frontend tests only
echo   %~nx0 lint      # Run linting only
echo.
goto :eof

:main
REM Parse command line arguments
set "command=%~1"
if "%command%"=="" set "command=all"

if "%command%"=="all" (
    call :run_backend_tests
    if errorlevel 1 exit /b 1
    
    call :run_frontend_tests
    if errorlevel 1 exit /b 1
    
    call :run_linting
    call :run_security_tests
    call :generate_reports
    
    call :print_success "🎉 All tests completed successfully!"
    
) else if "%command%"=="backend" (
    call :run_backend_tests
) else if "%command%"=="frontend" (
    call :run_frontend_tests
) else if "%command%"=="integration" (
    call :run_integration_tests
) else if "%command%"=="lint" (
    call :run_linting
) else if "%command%"=="security" (
    call :run_security_tests
) else if "%command%"=="reports" (
    call :generate_reports
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
