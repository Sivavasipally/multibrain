# Windows Deployment Guide

This guide provides comprehensive instructions for deploying the RAG Chatbot PWA on Windows systems.

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
```cmd
# Run the setup wizard
setup-windows.bat
```

### Option 2: PowerShell Deployment
```powershell
# Run PowerShell script (recommended)
.\scripts\deploy.ps1
```

### Option 3: Batch Deployment
```cmd
# Run batch script (classic)
scripts\deploy.bat
```

## 📋 Prerequisites

### Required Software

1. **Node.js 18+**
   - Download: https://nodejs.org/
   - Verify: `node --version`

2. **Python 3.9+**
   - Download: https://python.org/
   - Verify: `python --version`
   - ⚠️ Make sure to check "Add Python to PATH" during installation

3. **Docker Desktop** (for containerized deployment)
   - Download: https://docker.com/products/docker-desktop
   - Verify: `docker --version`

### Optional Software

4. **Git**
   - Download: https://git-scm.com/
   - Verify: `git --version`

5. **Visual Studio Code**
   - Download: https://code.visualstudio.com/
   - Recommended extensions: Python, TypeScript, Docker

## 🔧 Environment Setup

### 1. API Keys and Configuration

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://raguser:ragpass@localhost:5432/ragchatbot

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT Secret (generate a secure key)
JWT_SECRET_KEY=your-secret-key-here

# Gemini AI API Key (required)
GEMINI_API_KEY=your-gemini-api-key-here

# GitHub OAuth (optional)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# File Upload
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=104857600

# CORS
FRONTEND_URL=http://localhost:5173
```

### 2. Get Gemini API Key

1. Visit https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Create a new API key
4. Copy the key to your `.env` file

### 3. GitHub OAuth Setup (Optional)

1. Go to https://github.com/settings/applications/new
2. Fill in application details:
   - Application name: `RAG Chatbot PWA`
   - Homepage URL: `http://localhost:5173`
   - Authorization callback URL: `http://localhost:5000/api/auth/github/callback`
3. Copy Client ID and Client Secret to your `.env` file

## 🚀 Deployment Methods

### Method 1: PowerShell Script (Recommended)

The PowerShell script provides the best experience with colored output, error handling, and background job management.

```powershell
# Navigate to project directory
cd path\to\rag-chatbot-pwa

# Run deployment script
.\scripts\deploy.ps1

# Available commands:
.\scripts\deploy.ps1 deploy    # Start all services
.\scripts\deploy.ps1 stop      # Stop all services
.\scripts\deploy.ps1 clean     # Clean up containers
.\scripts\deploy.ps1 help      # Show help
```

**Features:**
- ✅ Automatic prerequisite checking
- ✅ Environment file creation
- ✅ Dependency installation
- ✅ Database setup with Docker
- ✅ Background service management
- ✅ Colored output and progress indicators

### Method 2: Batch Script (Classic)

The batch script provides compatibility with older Windows versions and opens services in separate windows.

```cmd
# Navigate to project directory
cd path\to\rag-chatbot-pwa

# Run deployment script
scripts\deploy.bat

# Available commands:
scripts\deploy.bat deploy    # Start all services
scripts\deploy.bat stop      # Stop all services
scripts\deploy.bat clean     # Clean up containers
```

**Features:**
- ✅ Compatible with all Windows versions
- ✅ Opens services in separate windows
- ✅ Simple and straightforward
- ✅ No PowerShell execution policy issues

### Method 3: Docker Compose

For a production-like containerized environment:

```cmd
# Start all services with Docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and start
docker-compose up -d --build
```

## 🔍 Troubleshooting

### Common Issues

#### 1. PowerShell Execution Policy Error

**Error:** `execution of scripts is disabled on this system`

**Solution:**
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine

# Or run with bypass
powershell -ExecutionPolicy Bypass -File scripts\deploy.ps1
```

#### 2. Python Not Found

**Error:** `'python' is not recognized as an internal or external command`

**Solutions:**
- Reinstall Python and check "Add Python to PATH"
- Or use `py` instead of `python`
- Add Python to PATH manually:
  1. Find Python installation (usually `C:\Users\{username}\AppData\Local\Programs\Python\Python3x\`)
  2. Add to System PATH environment variable

#### 3. Node.js Not Found

**Error:** `'node' is not recognized as an internal or external command`

**Solution:**
- Reinstall Node.js from https://nodejs.org/
- Restart command prompt/PowerShell after installation

#### 4. Docker Issues

**Error:** `docker: command not found` or connection errors

**Solutions:**
- Install Docker Desktop
- Start Docker Desktop application
- Ensure Docker is running (check system tray)

#### 5. Port Already in Use

**Error:** `Port 5000 is already in use`

**Solutions:**
```cmd
# Find process using port
netstat -ano | findstr :5000

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or use different ports in .env file
```

#### 6. Database Connection Issues

**Error:** `could not connect to server`

**Solutions:**
- Ensure PostgreSQL container is running: `docker ps`
- Check if port 5432 is available: `netstat -ano | findstr :5432`
- Restart PostgreSQL container: `docker restart ragchatbot-postgres`

### Windows-Specific Considerations

#### 1. File Paths
- Use backslashes (`\`) in Windows paths
- Or use forward slashes (`/`) which work in most contexts
- Avoid spaces in project path

#### 2. Antivirus Software
- Some antivirus software may block Node.js or Python
- Add project folder to antivirus exclusions if needed

#### 3. Windows Defender
- May block Docker or development servers
- Allow through Windows Defender Firewall when prompted

## 📱 Accessing the Application

Once deployment is complete:

- **Frontend (React PWA):** http://localhost:5173
- **Backend API:** http://localhost:5000
- **API Documentation:** http://localhost:5000/api/docs

## 🛑 Stopping Services

### PowerShell Method
```powershell
.\scripts\deploy.ps1 stop
```

### Batch Method
```cmd
scripts\deploy.bat stop
```

### Manual Method
```cmd
# Stop Docker containers
docker stop ragchatbot-postgres ragchatbot-redis

# Kill Node.js processes
taskkill /IM node.exe /F

# Kill Python processes
taskkill /IM python.exe /F
```

## 🧹 Cleanup

### Complete Cleanup
```powershell
# Using PowerShell script
.\scripts\deploy.ps1 clean

# Or using batch script
scripts\deploy.bat clean

# Manual cleanup
docker stop ragchatbot-postgres ragchatbot-redis
docker rm ragchatbot-postgres ragchatbot-redis
docker rmi postgres:13 redis:6-alpine
```

## 🔄 Development Workflow

### 1. Start Development Environment
```powershell
.\scripts\deploy.ps1 deploy
```

### 2. Make Changes
- Frontend code: `frontend/src/`
- Backend code: `backend/`
- Hot reload is enabled for both

### 3. View Logs
- PowerShell: Check background jobs with `Get-Job`
- Batch: Check separate windows
- Docker: `docker-compose logs -f`

### 4. Restart Services
```powershell
.\scripts\deploy.ps1 stop
.\scripts\deploy.ps1 deploy
```

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Ensure all prerequisites are installed
3. Verify environment variables are set correctly
4. Check Windows Event Viewer for system-level errors
5. Open an issue on GitHub with:
   - Windows version
   - Error messages
   - Steps to reproduce

## 🎯 Next Steps

After successful deployment:

1. **Create your first context** at http://localhost:5173/contexts
2. **Upload some documents** or connect a repository
3. **Start chatting** with your data at http://localhost:5173/chat
4. **Install the PWA** using the browser's install prompt

Enjoy your RAG Chatbot PWA! 🚀
