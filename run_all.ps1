# Script PowerShell to launch everything: Backend + Frontend + Optional Training
# Supports local models already downloaded

param(
    [switch]$Backend,
    [switch]$Frontend,
    [switch]$Train,
    [string]$ModelPath = "",
    [switch]$All,
    [switch]$Help
)

# Colors
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"
$WarningColor = "Yellow"

function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Show help
if ($Help -or (-not $Backend -and -not $Frontend -and -not $Train -and -not $All)) {
    Write-ColorOutput $InfoColor "=== MistralTune - Complete Launch Script ==="
    Write-Output ""
    Write-Output "Usage: .\run_all.ps1 [OPTIONS]"
    Write-Output ""
    Write-Output "Options:"
    Write-Output "  -Backend          Start backend API server"
    Write-Output "  -Frontend         Start frontend Next.js app"
    Write-Output "  -Train            Run training pipeline (demo)"
    Write-Output "  -ModelPath PATH   Use local model at PATH instead of downloading"
    Write-Output "  -All              Start both backend and frontend"
    Write-Output "  -Help             Show this help message"
    Write-Output ""
    Write-Output "Examples:"
    Write-Output "  .\run_all.ps1 -All                           # Start backend + frontend"
    Write-Output "  .\run_all.ps1 -Backend -Frontend             # Same as -All"
    Write-Output "  .\run_all.ps1 -Train                         # Run training demo"
    Write-Output "  .\run_all.ps1 -Train -ModelPath .\models\mistral-7b  # Train with local model"
    exit 0
}

# Check if we're in the right directory
if (-not (Test-Path "requirements.txt")) {
    Write-ColorOutput $ErrorColor "Error: Must run from project root directory"
    exit 1
}

# Handle -All flag
if ($All) {
    $Backend = $true
    $Frontend = $true
}

# Check Python environment
if ($Backend -or $Train) {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-ColorOutput $ErrorColor "Error: Python not found"
        exit 1
    }
    
    # Check if virtual environment exists
    if (-not (Test-Path ".venv")) {
        Write-ColorOutput $WarningColor "Virtual environment not found. Creating..."
        python -m venv .venv
        Write-ColorOutput $SuccessColor "Virtual environment created"
    }
    
    # Activate virtual environment
    & ".venv\Scripts\Activate.ps1"
    
    # Check if dependencies are installed
    $pythonCheck = python -c "import torch" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput $WarningColor "Dependencies not installed. Installing..."
        pip install -r requirements.txt
        Write-ColorOutput $SuccessColor "Dependencies installed"
    }
}

# Check Node.js for frontend
if ($Frontend) {
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        Write-ColorOutput $ErrorColor "Error: Node.js not found"
        exit 1
    }
    
    if (-not (Test-Path "frontend\node_modules")) {
        Write-ColorOutput $WarningColor "Frontend dependencies not installed. Installing..."
        Set-Location frontend
        npm install
        Set-Location ..
        Write-ColorOutput $SuccessColor "Frontend dependencies installed"
    }
}

# Create necessary directories
@("outputs", "reports", "data") | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ | Out-Null
    }
}

# Start backend
if ($Backend) {
    Write-ColorOutput $InfoColor "Starting backend API server..."
    
    if (-not $env:MISTRAL_API_KEY) {
        Write-ColorOutput $WarningColor "WARNING: MISTRAL_API_KEY not set"
        Write-Output "Backend will work for local training but Mistral API features will be disabled"
    }
    
    # Start backend in new window
    Start-Process python -ArgumentList "src\api\main.py" -WindowStyle Normal
    Write-ColorOutput $SuccessColor "Backend started"
    Write-Output "Backend API: http://localhost:8000"
    Write-Output "API Docs: http://localhost:8000/docs"
    
    # Wait a bit for backend to start
    Start-Sleep -Seconds 3
}

# Start frontend
if ($Frontend) {
    Write-ColorOutput $InfoColor "Starting frontend..."
    Set-Location frontend
    Start-Process npm -ArgumentList "run", "dev" -WindowStyle Normal
    Set-Location ..
    Write-ColorOutput $SuccessColor "Frontend started"
    Write-Output "Frontend: http://localhost:3000"
}

# Run training
if ($Train) {
    Write-ColorOutput $InfoColor "Running training pipeline..."
    
    # Check if sample data exists
    if (-not (Test-Path "data\sample_train.jsonl") -or -not (Test-Path "data\sample_eval.jsonl")) {
        Write-ColorOutput $ErrorColor "Error: Sample data files not found"
        exit 1
    }
    
    # Create config for local model if specified
    $configFile = "configs\sample.yaml"
    if ($ModelPath) {
        if (-not (Test-Path $ModelPath)) {
            Write-ColorOutput $ErrorColor "Error: Model path not found: $ModelPath"
            exit 1
        }
        
        Write-ColorOutput $SuccessColor "Using local model: $ModelPath"
        
        # Create temporary config with local model
        $localConfig = @"
base_model: "$ModelPath"
train_file: "data/sample_train.jsonl"
eval_file: "data/sample_eval.jsonl"
output_dir: "outputs/local_model_run"
per_device_train_batch_size: 1
gradient_accumulation_steps: 2
learning_rate: 1e-4
num_train_epochs: 1
logging_steps: 1
eval_steps: 5
save_steps: 10
bnb_4bit: true
fp16: true
bf16: false
max_seq_length: 512
packing: true
report_to: "none"
seed: 42
"@
        
        $localConfig | Out-File -FilePath "configs\local_model.yaml" -Encoding UTF8
        $configFile = "configs\local_model.yaml"
    }
    
    Write-Output "Step 1: Training..."
    python src\train_qlora.py --config $configFile --lora configs\sample_lora.yaml --output_dir outputs\demo_run
    
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput $ErrorColor "Error: Training failed"
        exit 1
    }
    
    Write-Output ""
    Write-Output "Step 2: Evaluating..."
    python src\eval_em_f1.py --model_path outputs\demo_run --eval_file data\sample_eval.jsonl --is_adapter --save_results
    
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput $ErrorColor "Error: Evaluation failed"
        exit 1
    }
    
    Write-Output ""
    Write-ColorOutput $SuccessColor "Training pipeline completed!"
    Write-Output "Check outputs\demo_run for the trained adapter"
    Write-Output "Check reports\results.csv for evaluation metrics"
}

# If both backend and frontend are running, wait
if ($Backend -and $Frontend) {
    Write-Output ""
    Write-ColorOutput $SuccessColor "=== Services Running ==="
    Write-Output "Backend: http://localhost:8000"
    Write-Output "Frontend: http://localhost:3000"
    Write-Output ""
    Write-Output "Press Ctrl+C to stop all services"
    Write-Output "Note: Services are running in separate windows. Close them manually when done."
    Write-Output ""
    Write-Output "Press any key to exit this script (services will continue running)..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

