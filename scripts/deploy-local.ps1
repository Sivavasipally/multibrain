# RAG Chatbot PWA Local PowerShell Deployment Script (No Docker)
# This script sets up everything locally without Docker containers

param(
    [Parameter(Position=0)]
    [ValidateSet("deploy", "stop", "clean", "help")]
    [string]$Command = "deploy"
)

# Set execution policy for current session
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

# Colors for output
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Cyan"
    White = "White"
}

function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Colors.Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Colors.Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Colors.Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Colors.Red
}

function Test-CommandExists {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

function Test-Prerequisites {
    Write-Status "Checking prerequisites..."
    
    $missingDeps = @()
    
    if (-not (Test-CommandExists "node")) {
        $missingDeps += "Node.js 18+"
    }
    
    if (-not (Test-CommandExists "python")) {
        $missingDeps += "Python 3.9+"
    }
    
    if (-not (Test-CommandExists "pip")) {
        $missingDeps += "pip"
    }
    
    if (-not (Test-CommandExists "npm")) {
        $missingDeps += "npm"
    }
    
    if ($missingDeps.Count -gt 0) {
        Write-Error "Missing dependencies:"
        foreach ($dep in $missingDeps) {
            Write-Host "  - $dep" -ForegroundColor $Colors.Red
        }
        Write-Host ""
        Write-Host "Please install the missing dependencies:" -ForegroundColor $Colors.Yellow
        Write-Host "- Node.js 18+: https://nodejs.org/" -ForegroundColor $Colors.White
        Write-Host "- Python 3.9+: https://python.org/" -ForegroundColor $Colors.White
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Success "All prerequisites are installed"
}

function Initialize-Environment {
    Write-Status "Setting up environment files..."
    
    # Backend environment for local SQLite
    if (-not (Test-Path ".env")) {
        Write-Status "Creating local .env file with SQLite database..."
        
        $envContent = @"
# Local SQLite Database
DATABASE_URL=sqlite:///./ragchatbot.db

# In-memory cache (no Redis needed)
REDIS_URL=memory://

# JWT
JWT_SECRET_KEY=$((New-Guid).Guid.Replace('-', ''))

# Gemini AI (replace with your API key)
GEMINI_API_KEY=your-gemini-api-key-here

# GitHub OAuth (optional)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# File Upload
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=104857600

# CORS
FRONTEND_URL=http://localhost:5173

# Local Development
FLASK_ENV=development
FLASK_DEBUG=1
"@
        $envContent | Out-File -FilePath ".env" -Encoding UTF8
        Write-Success "Created local .env file with SQLite and generated JWT secret"
    } else {
        Write-Warning "Backend .env file already exists"
    }
    
    # Frontend environment
    if (-not (Test-Path "frontend\.env")) {
        $frontendEnvContent = @"
VITE_API_URL=http://localhost:5000
VITE_APP_NAME=RAG Chatbot PWA
"@
        $frontendEnvContent | Out-File -FilePath "frontend\.env" -Encoding UTF8
        Write-Success "Created frontend .env file"
    } else {
        Write-Warning "Frontend .env file already exists"
    }
}

function Install-Dependencies {
    Write-Status "Installing dependencies..."
    
    # Backend dependencies
    Write-Status "Setting up Python environment..."
    Set-Location "backend"
    
    if (-not (Test-Path "venv")) {
        python -m venv venv
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to create Python virtual environment"
            Read-Host "Press Enter to exit"
            exit 1
        }
        Write-Success "Created Python virtual environment"
    }
    
    # Activate virtual environment and install dependencies
    & "venv\Scripts\Activate.ps1"
    
    Write-Status "Installing Python dependencies for local development..."
    pip install --upgrade pip

    # Try local requirements first, fallback to main requirements
    if (Test-Path "requirements-local.txt") {
        pip install -r requirements-local.txt
    } else {
        pip install -r requirements.txt
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install Python dependencies"
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Success "Installed Python dependencies"
    Set-Location ".."
    
    # Frontend dependencies
    Write-Status "Installing Node.js dependencies..."
    Set-Location "frontend"
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install Node.js dependencies"
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Success "Installed Node.js dependencies"
    Set-Location ".."
}

function Initialize-Database {
    Write-Status "Setting up local SQLite database..."
    
    Set-Location "backend"
    & "venv\Scripts\Activate.ps1"
    
    # Create uploads directory
    if (-not (Test-Path "uploads")) {
        New-Item -ItemType Directory -Path "uploads" | Out-Null
    }
    
    # Initialize database
    Write-Status "Initializing SQLite database..."
    $initScript = @"
from app import app, db
with app.app_context():
    db.create_all()
    print('Database tables created successfully')
"@
    
    $initScript | python
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to initialize database"
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Success "SQLite database initialized"
    Set-Location ".."
}

function New-LocalConfig {
    Write-Status "Creating local configuration..."
    
    Set-Location "backend"
    
    if (-not (Test-Path "app_local.py")) {
        Write-Status "Creating local app configuration..."
        
        $appLocalContent = @"
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Create Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ragchatbot.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', '104857600'))

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app, origins=[os.getenv('FRONTEND_URL', 'http://localhost:5173')])

# Import models and routes
from models import *
from routes.auth import auth_bp
from routes.contexts import contexts_bp
from routes.chat import chat_bp
from routes.upload import upload_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(contexts_bp, url_prefix='/api/contexts')
app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(upload_bp, url_prefix='/api/upload')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
"@
        $appLocalContent | Out-File -FilePath "app_local.py" -Encoding UTF8
        Write-Success "Created local app configuration"
    }
    
    Set-Location ".."
}

function Start-Services {
    Write-Status "Starting services locally..."
    
    # Create vector_store directory
    if (-not (Test-Path "vector_store")) {
        New-Item -ItemType Directory -Path "vector_store" | Out-Null
    }
    
    # Start Flask backend
    Write-Status "Starting Flask backend..."
    $flaskJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        Set-Location "backend"
        & "venv\Scripts\Activate.ps1"
        python app_local.py
    }
    Write-Success "Flask backend started (Job ID: $($flaskJob.Id))"
    
    # Wait a moment for backend to start
    Start-Sleep -Seconds 3
    
    # Start React frontend
    Write-Status "Starting React frontend..."
    $reactJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        Set-Location "frontend"
        npm run dev
    }
    Write-Success "React frontend started (Job ID: $($reactJob.Id))"
    
    # Store job IDs for cleanup
    $jobIds = @($flaskJob.Id, $reactJob.Id)
    $jobIds | Out-File -FilePath ".job_ids_local.txt" -Encoding UTF8
    
    return $jobIds
}

function Test-Services {
    Write-Status "Checking if services are running..."
    
    # Wait for services to start
    Start-Sleep -Seconds 5
    
    # Check if backend is responding
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/api/auth/profile" -TimeoutSec 5 -ErrorAction SilentlyContinue
        Write-Success "Backend is responding"
    } catch {
        Write-Warning "Backend may still be starting up..."
    }
    
    # Check if frontend is responding
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 5 -ErrorAction SilentlyContinue
        Write-Success "Frontend is responding"
    } catch {
        Write-Warning "Frontend may still be starting up..."
    }
}

function Show-Info {
    Write-Success "🎉 Local deployment completed!"
    Write-Host ""
    Write-Host "📱 Frontend: http://localhost:5173" -ForegroundColor $Colors.Green
    Write-Host "🔧 Backend API: http://localhost:5000" -ForegroundColor $Colors.Green
    Write-Host "📊 API Health: http://localhost:5000/api/auth/profile" -ForegroundColor $Colors.Green
    Write-Host ""
    Write-Host "📁 Database: SQLite file in backend/ragchatbot.db" -ForegroundColor $Colors.White
    Write-Host "📁 Uploads: backend/uploads/" -ForegroundColor $Colors.White
    Write-Host "📁 Vector Store: vector_store/" -ForegroundColor $Colors.White
    Write-Host ""
    Write-Host "⚠️  Note: This is a local development setup" -ForegroundColor $Colors.Yellow
    Write-Host "   - Uses SQLite instead of PostgreSQL" -ForegroundColor $Colors.Yellow
    Write-Host "   - No Redis (in-memory caching)" -ForegroundColor $Colors.Yellow
    Write-Host "   - No background task processing" -ForegroundColor $Colors.Yellow
    Write-Host "   - File uploads stored locally" -ForegroundColor $Colors.Yellow
    Write-Host ""
    Write-Host "🔧 To stop services:" -ForegroundColor $Colors.Blue
    Write-Host "   .\scripts\deploy-local.ps1 stop" -ForegroundColor $Colors.White
    Write-Host ""
}

function Stop-Services {
    Write-Status "Stopping local services..."
    
    if (Test-Path ".job_ids_local.txt") {
        $jobIds = Get-Content ".job_ids_local.txt"
        foreach ($jobId in $jobIds) {
            try {
                Stop-Job -Id $jobId -ErrorAction SilentlyContinue
                Remove-Job -Id $jobId -ErrorAction SilentlyContinue
            } catch {
                # Job might already be stopped
            }
        }
        Remove-Item ".job_ids_local.txt" -ErrorAction SilentlyContinue
    }
    
    # Also kill any processes that might be running
    Get-Process | Where-Object { $_.ProcessName -like "*python*" -or $_.ProcessName -like "*node*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Success "Local services stopped"
}

function Remove-LocalFiles {
    Write-Status "Cleaning up local files..."
    
    # Remove database
    if (Test-Path "backend\ragchatbot.db") {
        Remove-Item "backend\ragchatbot.db" -Force
        Write-Success "Removed SQLite database"
    }
    
    # Remove uploads
    if (Test-Path "backend\uploads") {
        Remove-Item "backend\uploads" -Recurse -Force
        Write-Success "Removed uploads directory"
    }
    
    # Remove vector store
    if (Test-Path "vector_store") {
        Remove-Item "vector_store" -Recurse -Force
        Write-Success "Removed vector store"
    }
    
    # Ask about removing dependencies
    $removeDeps = Read-Host "Remove node_modules and Python venv? (y/N)"
    if ($removeDeps -eq "y" -or $removeDeps -eq "Y") {
        if (Test-Path "frontend\node_modules") {
            Remove-Item "frontend\node_modules" -Recurse -Force
            Write-Success "Removed frontend node_modules"
        }
        if (Test-Path "backend\venv") {
            Remove-Item "backend\venv" -Recurse -Force
            Write-Success "Removed Python virtual environment"
        }
    }
    
    Write-Success "Cleanup completed"
}

function Start-Deployment {
    Write-Host ""
    Write-Host "🚀 RAG Chatbot PWA Local PowerShell Deployment (No Docker)" -ForegroundColor $Colors.Blue
    Write-Host "=========================================================" -ForegroundColor $Colors.Blue
    Write-Host ""
    
    Write-Status "Starting local RAG Chatbot PWA deployment..."
    
    Test-Prerequisites
    Initialize-Environment
    Install-Dependencies
    Initialize-Database
    New-LocalConfig
    $jobIds = Start-Services
    Test-Services
    Show-Info
    
    $openBrowser = Read-Host "Open application in browser? (y/N)"
    if ($openBrowser -eq "y" -or $openBrowser -eq "Y") {
        Start-Process "http://localhost:5173"
    }
    
    Write-Host ""
    Write-Host "Monitoring services... Press Ctrl+C to stop monitoring (services will continue running)" -ForegroundColor $Colors.Yellow
    
    try {
        while ($true) {
            Start-Sleep -Seconds 5
            $runningJobs = Get-Job | Where-Object { $_.Id -in $jobIds -and $_.State -eq "Running" }
            if ($runningJobs.Count -eq 0) {
                Write-Warning "All services have stopped"
                break
            }
        }
    } catch {
        Write-Host ""
        Write-Host "Monitoring stopped. Services are still running in background." -ForegroundColor $Colors.Yellow
    }
}

function Show-Help {
    Write-Host ""
    Write-Host "RAG Chatbot PWA Local PowerShell Deployment Script (No Docker)" -ForegroundColor $Colors.Blue
    Write-Host ""
    Write-Host "Usage: .\deploy-local.ps1 [command]" -ForegroundColor $Colors.White
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor $Colors.Yellow
    Write-Host "  deploy    Start all services locally (default)" -ForegroundColor $Colors.White
    Write-Host "  stop      Stop all services" -ForegroundColor $Colors.White
    Write-Host "  clean     Clean up local files" -ForegroundColor $Colors.White
    Write-Host "  help      Show this help message" -ForegroundColor $Colors.White
    Write-Host ""
    Write-Host "This script runs everything locally without Docker:" -ForegroundColor $Colors.Yellow
    Write-Host "- SQLite database instead of PostgreSQL" -ForegroundColor $Colors.White
    Write-Host "- In-memory caching instead of Redis" -ForegroundColor $Colors.White
    Write-Host "- Local file storage" -ForegroundColor $Colors.White
    Write-Host "- No background task processing" -ForegroundColor $Colors.White
    Write-Host ""
}

# Main execution
switch ($Command) {
    "deploy" {
        Start-Deployment
    }
    "stop" {
        Stop-Services
    }
    "clean" {
        Stop-Services
        Remove-LocalFiles
    }
    "help" {
        Show-Help
    }
    default {
        Write-Error "Unknown command: $Command"
        Show-Help
        exit 1
    }
}
