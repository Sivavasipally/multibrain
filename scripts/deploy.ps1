# RAG Chatbot PWA PowerShell Deployment Script
# This script sets up the complete development environment on Windows

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
    
    if (-not (Test-CommandExists "docker")) {
        $missingDeps += "Docker Desktop"
    }
    
    if (-not (Test-CommandExists "docker-compose")) {
        $missingDeps += "Docker Compose"
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
        Write-Host "- Docker Desktop: https://docker.com/products/docker-desktop" -ForegroundColor $Colors.White
        Write-Host ""
        Write-Host "Then run this script again." -ForegroundColor $Colors.Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Success "All prerequisites are installed"
}

function Initialize-Environment {
    Write-Status "Setting up environment files..."
    
    # Backend environment
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env"
            Write-Success "Created backend .env file from example"
        } else {
            Write-Warning "No .env.example found, creating basic .env file"
            
            $envContent = @"
# Database
DATABASE_URL=postgresql://raguser:ragpass@localhost:5432/ragchatbot

# Redis
REDIS_URL=redis://localhost:6379/0

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
"@
            $envContent | Out-File -FilePath ".env" -Encoding UTF8
            Write-Success "Created basic .env file with generated JWT secret"
        }
    } else {
        Write-Warning "Backend .env file already exists"
    }
    
    # Frontend environment
    if (-not (Test-Path "frontend\.env")) {
        if (Test-Path "frontend\.env.example") {
            Copy-Item "frontend\.env.example" "frontend\.env"
            Write-Success "Created frontend .env file from example"
        } else {
            Write-Warning "No frontend\.env.example found, creating basic .env file"
            
            $frontendEnvContent = @"
VITE_API_URL=http://localhost:5000
VITE_APP_NAME=RAG Chatbot PWA
"@
            $frontendEnvContent | Out-File -FilePath "frontend\.env" -Encoding UTF8
            Write-Success "Created basic frontend .env file"
        }
    } else {
        Write-Warning "Frontend .env file already exists"
    }
}

function Install-Dependencies {
    Write-Status "Installing dependencies..."
    
    # Backend dependencies
    Write-Status "Installing Python dependencies..."
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
    pip install -r requirements.txt
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
    Write-Status "Setting up database containers..."
    
    # Check if PostgreSQL container is running
    $postgresRunning = docker ps --format "table {{.Names}}" | Select-String "ragchatbot-postgres"
    if ($postgresRunning) {
        Write-Success "PostgreSQL container is already running"
    } else {
        Write-Status "Starting PostgreSQL container..."
        docker run -d --name ragchatbot-postgres -e POSTGRES_DB=ragchatbot -e POSTGRES_USER=raguser -e POSTGRES_PASSWORD=ragpass -p 5432:5432 postgres:13
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to start PostgreSQL container"
            Read-Host "Press Enter to exit"
            exit 1
        }
        
        Write-Status "Waiting for PostgreSQL to be ready..."
        Start-Sleep -Seconds 10
        Write-Success "PostgreSQL container started"
    }
    
    # Check if Redis container is running
    $redisRunning = docker ps --format "table {{.Names}}" | Select-String "ragchatbot-redis"
    if ($redisRunning) {
        Write-Success "Redis container is already running"
    } else {
        Write-Status "Starting Redis container..."
        docker run -d --name ragchatbot-redis -p 6379:6379 redis:6-alpine
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to start Redis container"
            Read-Host "Press Enter to exit"
            exit 1
        }
        Write-Success "Redis container started"
    }
    
    # Initialize database schema
    Write-Status "Initializing database schema..."
    Set-Location "backend"
    & "venv\Scripts\Activate.ps1"
    flask db upgrade
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to initialize database"
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Success "Database initialized"
    Set-Location ".."
}

function Start-Services {
    Write-Status "Starting services..."
    
    # Start Celery worker
    Write-Status "Starting Celery worker..."
    $celeryJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        Set-Location "backend"
        & "venv\Scripts\Activate.ps1"
        celery -A app.celery worker --loglevel=info
    }
    Write-Success "Celery worker started (Job ID: $($celeryJob.Id))"
    
    # Start Flask backend
    Write-Status "Starting Flask backend..."
    $flaskJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        Set-Location "backend"
        & "venv\Scripts\Activate.ps1"
        python app.py
    }
    Write-Success "Flask backend started (Job ID: $($flaskJob.Id))"
    
    # Start React frontend
    Write-Status "Starting React frontend..."
    $reactJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        Set-Location "frontend"
        npm run dev
    }
    Write-Success "React frontend started (Job ID: $($reactJob.Id))"
    
    # Store job IDs for cleanup
    $jobIds = @($celeryJob.Id, $flaskJob.Id, $reactJob.Id)
    $jobIds | Out-File -FilePath ".job_ids.txt" -Encoding UTF8
    
    return $jobIds
}

function Stop-Services {
    Write-Status "Stopping services..."
    
    if (Test-Path ".job_ids.txt") {
        $jobIds = Get-Content ".job_ids.txt"
        foreach ($jobId in $jobIds) {
            try {
                Stop-Job -Id $jobId -ErrorAction SilentlyContinue
                Remove-Job -Id $jobId -ErrorAction SilentlyContinue
            } catch {
                # Job might already be stopped
            }
        }
        Remove-Item ".job_ids.txt" -ErrorAction SilentlyContinue
    }
    
    # Also kill any processes that might be running
    Get-Process | Where-Object { $_.ProcessName -like "*celery*" -or $_.ProcessName -like "*flask*" -or $_.ProcessName -like "*node*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Success "Services stopped"
}

function Remove-Containers {
    Write-Status "Cleaning up containers..."
    
    docker stop ragchatbot-postgres ragchatbot-redis 2>$null
    docker rm ragchatbot-postgres ragchatbot-redis 2>$null
    
    Write-Success "Containers removed"
}

function Start-Deployment {
    Write-Host ""
    Write-Host "🚀 RAG Chatbot PWA PowerShell Deployment Script" -ForegroundColor $Colors.Blue
    Write-Host "=============================================" -ForegroundColor $Colors.Blue
    Write-Host ""
    
    Write-Status "Starting RAG Chatbot PWA deployment..."
    
    Test-Prerequisites
    Initialize-Environment
    Install-Dependencies
    Initialize-Database
    $jobIds = Start-Services
    
    Write-Success "🎉 Deployment completed successfully!"
    Write-Host ""
    Write-Host "📱 Frontend: http://localhost:5173" -ForegroundColor $Colors.Green
    Write-Host "🔧 Backend API: http://localhost:5000" -ForegroundColor $Colors.Green
    Write-Host "📊 API Docs: http://localhost:5000/api/docs" -ForegroundColor $Colors.Green
    Write-Host ""
    Write-Host "Services are running in background jobs." -ForegroundColor $Colors.Yellow
    Write-Host "Run 'deploy.ps1 stop' to stop all services." -ForegroundColor $Colors.Yellow
    Write-Host ""
    
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
    Write-Host "RAG Chatbot PWA PowerShell Deployment Script" -ForegroundColor $Colors.Blue
    Write-Host ""
    Write-Host "Usage: .\deploy.ps1 [command]" -ForegroundColor $Colors.White
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor $Colors.Yellow
    Write-Host "  deploy    Start all services (default)" -ForegroundColor $Colors.White
    Write-Host "  stop      Stop all services" -ForegroundColor $Colors.White
    Write-Host "  clean     Stop and remove all containers" -ForegroundColor $Colors.White
    Write-Host "  help      Show this help message" -ForegroundColor $Colors.White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor $Colors.Yellow
    Write-Host "  .\deploy.ps1           # Start all services" -ForegroundColor $Colors.White
    Write-Host "  .\deploy.ps1 deploy    # Start all services" -ForegroundColor $Colors.White
    Write-Host "  .\deploy.ps1 stop      # Stop all services" -ForegroundColor $Colors.White
    Write-Host "  .\deploy.ps1 clean     # Clean up everything" -ForegroundColor $Colors.White
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
        Remove-Containers
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
