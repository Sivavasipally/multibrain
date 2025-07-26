@echo off
setlocal

title RAG Chatbot PWA - Windows Setup

echo.
echo 🚀 RAG Chatbot PWA - Windows Setup
echo ==================================
echo.
echo This script will help you set up the RAG Chatbot PWA on Windows.
echo.
echo Available deployment options:
echo.
echo 1. PowerShell Script (Recommended)
echo    - Modern PowerShell with better error handling
echo    - Colored output and progress indicators
echo    - Background job management
echo.
echo 2. Batch Script (Classic)
echo    - Traditional Windows batch file
echo    - Compatible with older Windows versions
echo    - Opens services in separate windows
echo.
echo 3. Docker Compose (Advanced)
echo    - Containerized deployment
echo    - Requires Docker Desktop
echo    - Production-like environment
echo.

:menu
echo Please choose your deployment method:
echo.
echo [1] PowerShell Script (Recommended)
echo [2] Batch Script
echo [3] Docker Compose
echo [4] Show Prerequisites
echo [5] Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto powershell
if "%choice%"=="2" goto batch
if "%choice%"=="3" goto docker
if "%choice%"=="4" goto prerequisites
if "%choice%"=="5" goto exit
echo Invalid choice. Please try again.
echo.
goto menu

:powershell
echo.
echo Starting PowerShell deployment...
echo.
echo Checking if PowerShell is available...
powershell -Command "Write-Host 'PowerShell is available'" >nul 2>&1
if errorlevel 1 (
    echo PowerShell is not available or execution policy is restricted.
    echo.
    echo To enable PowerShell scripts, run this command as Administrator:
    echo Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine
    echo.
    echo Falling back to batch script...
    timeout /t 3 /nobreak >nul
    goto batch
)

echo PowerShell is available. Starting deployment...
powershell -ExecutionPolicy Bypass -File "scripts\deploy.ps1" deploy
goto end

:batch
echo.
echo Starting batch deployment...
echo.
call scripts\deploy.bat deploy
goto end

:docker
echo.
echo Starting Docker Compose deployment...
echo.
echo Checking if Docker is available...
docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker is not installed or not running.
    echo Please install Docker Desktop from: https://docker.com/products/docker-desktop
    echo.
    pause
    goto menu
)

echo Docker is available. Starting containers...
docker-compose up -d
if errorlevel 1 (
    echo Failed to start containers. Please check Docker Desktop is running.
    echo.
    pause
    goto menu
)

echo.
echo 🎉 Docker containers started successfully!
echo.
echo 📱 Frontend: http://localhost:5173
echo 🔧 Backend API: http://localhost:5000
echo 📊 API Docs: http://localhost:5000/api/docs
echo.
echo To stop the containers, run: docker-compose down
echo.
set /p open="Open application in browser? (y/N): "
if /i "%open%"=="y" start http://localhost:5173
goto end

:prerequisites
echo.
echo 📋 Prerequisites for RAG Chatbot PWA
echo ====================================
echo.
echo Required Software:
echo.
echo 1. Node.js 18 or later
echo    Download: https://nodejs.org/
echo    Check: node --version
echo.
echo 2. Python 3.9 or later
echo    Download: https://python.org/
echo    Check: python --version
echo.
echo 3. Docker Desktop (for containerized deployment)
echo    Download: https://docker.com/products/docker-desktop
echo    Check: docker --version
echo.
echo Optional:
echo.
echo 4. Git (for version control)
echo    Download: https://git-scm.com/
echo    Check: git --version
echo.
echo 5. Visual Studio Code (recommended editor)
echo    Download: https://code.visualstudio.com/
echo.
echo Environment Setup:
echo.
echo 1. Gemini API Key (required for AI features)
echo    Get from: https://makersuite.google.com/app/apikey
echo.
echo 2. GitHub OAuth App (optional, for repository integration)
echo    Create at: https://github.com/settings/applications/new
echo.
echo Current System Check:
echo ====================
echo.

echo Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found
) else (
    for /f "tokens=*" %%i in ('node --version') do echo ✅ Node.js: %%i
)

echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found
) else (
    for /f "tokens=*" %%i in ('python --version') do echo ✅ Python: %%i
)

echo Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not found
) else (
    for /f "tokens=*" %%i in ('docker --version') do echo ✅ Docker: %%i
)

echo Checking Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git not found
) else (
    for /f "tokens=*" %%i in ('git --version') do echo ✅ Git: %%i
)

echo.
pause
goto menu

:exit
echo.
echo Thank you for using RAG Chatbot PWA!
echo.
echo For support and documentation, visit:
echo https://github.com/your-repo/rag-chatbot-pwa
echo.
goto end

:end
echo.
echo Press any key to exit...
pause >nul
