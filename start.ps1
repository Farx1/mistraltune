# MistralTune - Unified Start Script (Windows PowerShell)
# Starts backend and frontend with automatic setup

$ErrorActionPreference = "Continue"

# Colors for output
function Write-ColorOutput {
    param($ForegroundColor)
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Configuration
$BACKEND_PORT = if ($env:BACKEND_PORT) { [int]$env:BACKEND_PORT } else { 8000 }
$FRONTEND_PORT = if ($env:FRONTEND_PORT) { [int]$env:FRONTEND_PORT } else { 3000 }
$BACKEND_URL = "http://localhost:$BACKEND_PORT"
$FRONTEND_URL = "http://localhost:$FRONTEND_PORT"

# Initialize process IDs
$script:BACKEND_PID = $null
$script:FRONTEND_PID = $null

Write-ColorOutput Cyan "=== MistralTune - Starting Services ==="
Write-Output ""

# Check if we're in the right directory
if (-not (Test-Path "requirements.txt") -or -not (Test-Path "frontend")) {
    Write-ColorOutput Red "Error: Must run from project root directory"
    exit 1
}

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-ColorOutput Red "Error: Python not found. Please install Python 3.10 or higher."
    exit 1
}

$pythonVersion = python --version 2>&1 | Out-String
$pythonVersionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
if (-not $pythonVersionMatch) {
    Write-ColorOutput Red "Error: Could not determine Python version"
    exit 1
}

$pythonMajor = [int]$matches[1]
$pythonMinor = [int]$matches[2]

if ($pythonMajor -lt 3 -or ($pythonMajor -eq 3 -and $pythonMinor -lt 10)) {
    Write-ColorOutput Red "Error: Python 3.10+ required. Found: $pythonVersion"
    exit 1
}

Write-ColorOutput Green "[OK] Python $pythonVersion found"

# Check Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-ColorOutput Red "Error: Node.js not found. Please install Node.js 18 or higher."
    exit 1
}

$nodeVersion = node -v
$nodeVersionMatch = $nodeVersion -match "v(\d+)"
if (-not $nodeVersionMatch) {
    Write-ColorOutput Red "Error: Could not determine Node.js version"
    exit 1
}

$nodeMajor = [int]$matches[1]
if ($nodeMajor -lt 18) {
    Write-ColorOutput Red "Error: Node.js 18+ required. Found: $nodeVersion"
    exit 1
}

Write-ColorOutput Green "[OK] Node.js $nodeVersion found"

# Setup Python virtual environment
if (-not (Test-Path ".venv")) {
    Write-ColorOutput Yellow "Creating virtual environment..."
    python -m venv .venv
    Write-ColorOutput Green "[OK] Virtual environment created"
}

# Activate virtual environment
& ".venv\Scripts\Activate.ps1"

# Install backend dependencies
$pythonCheck = python -c "import fastapi" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Yellow "Installing backend dependencies..."
    pip install -q -r requirements.txt
    Write-ColorOutput Green "[OK] Backend dependencies installed"
} else {
    Write-ColorOutput Green "[OK] Backend dependencies already installed"
}

# Install frontend dependencies
if (-not (Test-Path "frontend\node_modules")) {
    Write-ColorOutput Yellow "Installing frontend dependencies..."
    Set-Location frontend
    npm install --silent
    Set-Location ..
    Write-ColorOutput Green "[OK] Frontend dependencies installed"
} else {
    Write-ColorOutput Green "[OK] Frontend dependencies already installed"
}

# Create necessary directories
@("data\uploads", "data") | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
    }
}

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-ColorOutput Yellow "Warning: .env file not found."
    Write-Output "Copy .env.example to .env and configure your MISTRAL_API_KEY"
    Write-Output "Backend will start but Mistral API features will be disabled."
    Write-Output ""
}

# Function to check if a port is actually in use by a real process
function Test-Port {
    param([int]$Port)
    # Check if port is listening
    $listening = netstat -ano | Select-String ":$Port.*LISTENING"
    if (-not $listening) {
        return $false
    }
    
    # Check if any listening process actually exists
    $hasRealProcess = $false
    foreach ($line in $listening) {
        if ($line -match '\s+(\d+)\s*$') {
            $processId = [int]$matches[1]
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($process) {
                $hasRealProcess = $true
                break
            }
        }
    }
    
    return $hasRealProcess
}

# Function to clean up zombie connections on a port
function Clear-PortZombies {
    param([int]$Port)
    Write-ColorOutput Yellow "Checking for zombie connections on port $Port..."
    
    $listening = netstat -ano | Select-String ":$Port.*LISTENING"
    $zombieCount = 0
    
    foreach ($line in $listening) {
        if ($line -match '\s+(\d+)\s*$') {
            $processId = [int]$matches[1]
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if (-not $process) {
                $zombieCount++
            }
        }
    }
    
    if ($zombieCount -gt 0) {
        Write-ColorOutput Yellow "Found $zombieCount zombie connection(s) on port $Port"
        Write-ColorOutput Yellow "Waiting for Windows to clean up (this may take 30-60 seconds)..."
        
        $maxWait = 60
        $waited = 0
        while ($waited -lt $maxWait) {
            Start-Sleep -Seconds 2
            $waited += 2
            
            if (-not (Test-Port -Port $Port)) {
                Write-ColorOutput Green "Port $Port is now free"
                return $true
            }
        }
        
        Write-ColorOutput Red "Port $Port still appears occupied after waiting"
        return $false
    }
    
    return $true
}

# Check if ports are available
if (Test-Port -Port $BACKEND_PORT) {
    Write-ColorOutput Yellow "Port $BACKEND_PORT appears to be in use by a real process"
    Write-ColorOutput Yellow "Attempting to clear zombie connections..."
    Clear-PortZombies -Port $BACKEND_PORT | Out-Null
    
    # Check again after cleanup attempt
    if (Test-Port -Port $BACKEND_PORT) {
        Write-ColorOutput Red "Error: Port $BACKEND_PORT is still in use by a real process."
        Write-ColorOutput Yellow "Please stop the process manually or run .\stop.ps1"
        exit 1
    } else {
        Write-ColorOutput Green "Port $BACKEND_PORT is now available (zombie connections cleared)"
    }
} else {
    # Check for zombie connections but don't block if only zombies exist
    $listening = netstat -ano | Select-String ":$BACKEND_PORT.*LISTENING"
    if ($listening) {
        Write-ColorOutput Yellow "Found zombie connections on port $BACKEND_PORT (will attempt to start anyway)"
    }
}

if (Test-Port -Port $FRONTEND_PORT) {
    Write-ColorOutput Yellow "Port $FRONTEND_PORT appears to be in use by a real process"
    Write-ColorOutput Yellow "Attempting to clear zombie connections..."
    Clear-PortZombies -Port $FRONTEND_PORT | Out-Null
    
    # Check again after cleanup attempt
    if (Test-Port -Port $FRONTEND_PORT) {
        Write-ColorOutput Red "Error: Port $FRONTEND_PORT is still in use by a real process."
        Write-ColorOutput Yellow "Please stop the process manually or run .\stop.ps1"
        exit 1
    } else {
        Write-ColorOutput Green "Port $FRONTEND_PORT is now available (zombie connections cleared)"
    }
} else {
    # Check for zombie connections but don't block if only zombies exist
    $listening = netstat -ano | Select-String ":$FRONTEND_PORT.*LISTENING"
    if ($listening) {
        Write-ColorOutput Yellow "Found zombie connections on port $FRONTEND_PORT (will attempt to start anyway)"
    }
}

# Function to wait for health check
function Wait-ForBackend {
    $maxAttempts = 30
    $attempt = 0
    
    Write-ColorOutput Yellow "Waiting for backend to be ready..."
    while ($attempt -lt $maxAttempts) {
        $response = $null
        $response = Invoke-WebRequest -Uri "$BACKEND_URL/api/health" -TimeoutSec 1 -UseBasicParsing -ErrorAction SilentlyContinue
        
        if ($response) {
            if ($response.StatusCode -eq 200) {
                Write-ColorOutput Green "[OK] Backend is ready"
                return $true
            }
        }
        
        $attempt = $attempt + 1
        Start-Sleep -Seconds 1
    }
    
    Write-ColorOutput Red "Error: Backend failed to start within $maxAttempts seconds"
    return $false
}

# Cleanup function
function Cleanup {
    Write-Output ""
    Write-ColorOutput Yellow "Shutting down services..."
    
    if ($script:BACKEND_PID) {
        $process = Get-Process -Id $script:BACKEND_PID -ErrorAction SilentlyContinue
        if ($process) {
            Stop-Process -Id $script:BACKEND_PID -Force -ErrorAction SilentlyContinue
                Write-ColorOutput Green "[OK] Backend stopped"
        }
    }
    
    if ($script:FRONTEND_PID) {
        $process = Get-Process -Id $script:FRONTEND_PID -ErrorAction SilentlyContinue
        if ($process) {
            Stop-Process -Id $script:FRONTEND_PID -Force -ErrorAction SilentlyContinue
                Write-ColorOutput Green "[OK] Frontend stopped"
        }
    }
    
    Write-ColorOutput Green "Cleanup complete"
}

# Register cleanup on exit
Register-EngineEvent PowerShell.Exiting -Action { Cleanup } | Out-Null

# Start backend
Write-ColorOutput Cyan "Starting backend on port $BACKEND_PORT..."
$backendProcess = Start-Process -FilePath "python" -ArgumentList "src\api\main.py" -PassThru -WindowStyle Hidden -RedirectStandardOutput "backend.log" -RedirectStandardError "backend.error.log"
if (-not $backendProcess) {
    Write-ColorOutput Red "Failed to start backend process"
    exit 1
}
$script:BACKEND_PID = $backendProcess.Id
Write-ColorOutput Green "Backend started (PID: $script:BACKEND_PID)"

# Wait for backend to be ready
if (-not (Wait-ForBackend)) {
    Write-ColorOutput Red "Backend startup failed. Check backend.log and backend.error.log for details."
    Cleanup
    exit 1
}

# Start frontend
Write-ColorOutput Cyan "Starting frontend on port $FRONTEND_PORT..."
Set-Location frontend
$frontendProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -PassThru -WindowStyle Hidden -RedirectStandardOutput "..\frontend.log" -RedirectStandardError "..\frontend.error.log"
Set-Location ..
if (-not $frontendProcess) {
    Write-ColorOutput Red "Failed to start frontend process"
    Cleanup
    exit 1
}
$script:FRONTEND_PID = $frontendProcess.Id
Write-ColorOutput Green "Frontend started (PID: $script:FRONTEND_PID)"

# Wait a bit for frontend to start
Start-Sleep -Seconds 3

# Display status
Write-Output ""
Write-ColorOutput Green "=== Services Running ==="
Write-Output ""
Write-ColorOutput Cyan "Backend API:  $BACKEND_URL"
$apiDocsMsg = "API Docs:    $BACKEND_URL/docs"
Write-ColorOutput Cyan $apiDocsMsg
$frontendMsg = "Frontend:    $FRONTEND_URL"
Write-ColorOutput Cyan $frontendMsg
Write-Output ""
Write-ColorOutput Yellow "Press Ctrl+C to stop all services"
Write-Output ""

# Wait for user interrupt
$running = $true
while ($running) {
    Start-Sleep -Seconds 1
    
    # Check if processes are still running
    $backendRunning = $null
    $frontendRunning = $null
    
    if ($script:BACKEND_PID) {
        $backendRunning = Get-Process -Id $script:BACKEND_PID -ErrorAction SilentlyContinue
    }
    
    if ($script:FRONTEND_PID) {
        $frontendRunning = Get-Process -Id $script:FRONTEND_PID -ErrorAction SilentlyContinue
    }
    
    if ($script:BACKEND_PID -and -not $backendRunning) {
        Write-ColorOutput Yellow "Backend stopped unexpectedly"
        $running = $false
    }
    
    if ($script:FRONTEND_PID -and -not $frontendRunning) {
        Write-ColorOutput Yellow "Frontend stopped unexpectedly"
        $running = $false
    }
}

Cleanup
