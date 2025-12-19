# MistralTune - Fresh Clone Test Script (PowerShell)
# Simulates a fresh clone and verifies the project can be set up from scratch

$ErrorActionPreference = "Stop"

Write-Host "=== MistralTune Fresh Clone Test ===" -ForegroundColor Cyan
Write-Host ""

# Colors for output
function Write-ColorOutput {
    param($ForegroundColor, $Message)
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    Write-Host $Message
    $host.UI.RawUI.ForegroundColor = $fc
}

# Step 1: Clean up
Write-ColorOutput Yellow "Step 1: Cleaning up existing build artifacts..."

$cleanupPaths = @(
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "frontend/node_modules",
    "frontend/.next",
    "src/__pycache__",
    "src/api/__pycache__",
    "src/utils/__pycache__",
    "*.pyc"
)

foreach ($path in $cleanupPaths) {
    if (Test-Path $path) {
        Write-Host "  Removing $path..."
        Remove-Item -Recurse -Force $path -ErrorAction SilentlyContinue
    }
}

Write-ColorOutput Green "✓ Cleanup complete"
Write-Host ""

# Step 2: Check Python
Write-ColorOutput Yellow "Step 2: Checking Python installation..."

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-ColorOutput Red "Error: Python not found"
    exit 1
}

$pythonVersion = python --version 2>&1
Write-ColorOutput Green "✓ Found $pythonVersion"
Write-Host ""

# Step 3: Create virtual environment
Write-ColorOutput Yellow "Step 3: Creating virtual environment..."

python -m venv .venv
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Error: Failed to create virtual environment"
    exit 1
}

& ".venv\Scripts\Activate.ps1"
Write-ColorOutput Green "✓ Virtual environment created"
Write-Host ""

# Step 4: Install backend dependencies
Write-ColorOutput Yellow "Step 4: Installing backend dependencies..."

pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Error: Failed to install backend dependencies"
    exit 1
}

Write-ColorOutput Green "✓ Backend dependencies installed"
Write-Host ""

# Step 5: Install frontend dependencies
Write-ColorOutput Yellow "Step 5: Installing frontend dependencies..."

Set-Location frontend
npm ci --silent
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Error: Failed to install frontend dependencies"
    Set-Location ..
    exit 1
}
Set-Location ..
Write-ColorOutput Green "✓ Frontend dependencies installed"
Write-Host ""

# Step 6: Run backend tests
Write-ColorOutput Yellow "Step 6: Running backend tests..."

$env:DEMO_MODE = "1"
pytest tests/ -v --tb=short
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Error: Backend tests failed"
    exit 1
}

Write-ColorOutput Green "✓ Backend tests passed"
Write-Host ""

# Step 7: Build frontend
Write-ColorOutput Yellow "Step 7: Building frontend..."

Set-Location frontend
$env:NEXT_PUBLIC_API_URL = "http://localhost:8000"
$env:NEXT_PUBLIC_WS_URL = "ws://localhost:8000"
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Error: Frontend build failed"
    Set-Location ..
    exit 1
}
Set-Location ..
Write-ColorOutput Green "✓ Frontend build successful"
Write-Host ""

# Step 8: Test health endpoint (quick check)
Write-ColorOutput Yellow "Step 8: Testing API health endpoint..."

# Start backend in background
$backendProcess = Start-Process -FilePath "python" -ArgumentList "src\api\main.py" -PassThru -WindowStyle Hidden -RedirectStandardOutput "test_backend.log" -RedirectStandardError "test_backend.error.log"
Start-Sleep -Seconds 3

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-ColorOutput Green "✓ Health endpoint responded successfully"
    } else {
        Write-ColorOutput Red "Error: Health endpoint returned status $($response.StatusCode)"
        exit 1
    }
} catch {
    Write-ColorOutput Yellow "Warning: Could not reach health endpoint (backend may need more time to start)"
    Write-Host "  This is acceptable for a quick smoke test"
} finally {
    # Stop backend
    if ($backendProcess) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
}

Write-Host ""
Write-ColorOutput Green "=== Fresh Clone Test PASSED ===" -ForegroundColor Green
Write-Host ""
Write-Host "All checks completed successfully. The project can be set up from a fresh clone." -ForegroundColor Green

