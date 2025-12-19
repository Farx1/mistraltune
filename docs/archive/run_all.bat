@echo off
REM Script to launch everything: Backend + Frontend + Optional Training
REM Supports local models already downloaded

setlocal enabledelayedexpansion

echo === MistralTune - Complete Launch Script ===
echo.

REM Check if we're in the right directory
if not exist "requirements.txt" (
    echo Error: Must run from project root directory
    exit /b 1
)

REM Parse arguments
set BACKEND=false
set FRONTEND=false
set TRAIN=false
set MODEL_PATH=
set USE_LOCAL_MODEL=false
set SHOW_HELP=false

:parse_args
if "%~1"=="" goto end_parse
if "%~1"=="--backend" (
    set BACKEND=true
    shift
    goto parse_args
)
if "%~1"=="--frontend" (
    set FRONTEND=true
    shift
    goto parse_args
)
if "%~1"=="--train" (
    set TRAIN=true
    shift
    goto parse_args
)
if "%~1"=="--model-path" (
    set MODEL_PATH=%~2
    set USE_LOCAL_MODEL=true
    shift
    shift
    goto parse_args
)
if "%~1"=="--all" (
    set BACKEND=true
    set FRONTEND=true
    shift
    goto parse_args
)
if "%~1"=="--help" (
    set SHOW_HELP=true
    goto show_help
)
echo Unknown option: %~1
echo Use --help for usage information
exit /b 1

:show_help
echo Usage: %~nx0 [OPTIONS]
echo.
echo Options:
echo   --backend          Start backend API server
echo   --frontend         Start frontend Next.js app
echo   --train            Run training pipeline (demo)
echo   --model-path PATH  Use local model at PATH instead of downloading
echo   --all              Start both backend and frontend
echo   --help             Show this help message
echo.
echo Examples:
echo   %~nx0 --all                           # Start backend + frontend
echo   %~nx0 --backend --frontend            # Same as --all
echo   %~nx0 --train                         # Run training demo
echo   %~nx0 --train --model-path .\models\mistral-7b  # Train with local model
exit /b 0

:end_parse

REM If no options specified, show help
if "%BACKEND%"=="false" if "%FRONTEND%"=="false" if "%TRAIN%"=="false" (
    echo No options specified. Showing help:
    echo.
    call %~nx0 --help
    exit /b 0
)

REM Check Python environment
if "%BACKEND%"=="true" goto check_python
if "%TRAIN%"=="true" goto check_python
goto check_node

:check_python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    exit /b 1
)

REM Check if virtual environment exists
if not exist ".venv" (
    echo Virtual environment not found. Creating...
    python -m venv .venv
    echo Virtual environment created
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import torch" >nul 2>&1
if errorlevel 1 (
    echo Dependencies not installed. Installing...
    pip install -r requirements.txt
    echo Dependencies installed
)

:check_node
if "%FRONTEND%"=="false" goto create_dirs

node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js not found
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo Frontend dependencies not installed. Installing...
    cd frontend
    call npm install
    cd ..
    echo Frontend dependencies installed
)

:create_dirs
if not exist "outputs" mkdir outputs
if not exist "reports" mkdir reports
if not exist "data" mkdir data

REM Start services
if "%BACKEND%"=="true" (
    echo Starting backend API server...
    if "%MISTRAL_API_KEY%"=="" (
        echo WARNING: MISTRAL_API_KEY not set
        echo Backend will work for local training but Mistral API features will be disabled
    )
    start "MistralTune Backend" python src\api\main.py
    echo Backend started
    echo Backend API: http://localhost:8000
    echo API Docs: http://localhost:8000/docs
    timeout /t 3 /nobreak >nul
)

if "%FRONTEND%"=="true" (
    echo Starting frontend...
    cd frontend
    start "MistralTune Frontend" npm run dev
    cd ..
    echo Frontend started
    echo Frontend: http://localhost:3000
)

if "%TRAIN%"=="true" (
    echo Running training pipeline...
    
    if not exist "data\sample_train.jsonl" (
        echo Error: Sample data files not found
        exit /b 1
    )
    
    if not exist "data\sample_eval.jsonl" (
        echo Error: Sample eval file not found
        exit /b 1
    )
    
    REM Create config for local model if specified
    if "%USE_LOCAL_MODEL%"=="true" (
        if not exist "%MODEL_PATH%" (
            echo Error: Model path not found: %MODEL_PATH%
            exit /b 1
        )
        
        echo Using local model: %MODEL_PATH%
        
        (
            echo base_model: "%MODEL_PATH%"
            echo train_file: "data/sample_train.jsonl"
            echo eval_file: "data/sample_eval.jsonl"
            echo output_dir: "outputs/local_model_run"
            echo per_device_train_batch_size: 1
            echo gradient_accumulation_steps: 2
            echo learning_rate: 1e-4
            echo num_train_epochs: 1
            echo logging_steps: 1
            echo eval_steps: 5
            echo save_steps: 10
            echo bnb_4bit: true
            echo fp16: true
            echo bf16: false
            echo max_seq_length: 512
            echo packing: true
            echo report_to: "none"
            echo seed: 42
        ) > configs\local_model.yaml
        
        set CONFIG_FILE=configs\local_model.yaml
    ) else (
        set CONFIG_FILE=configs\sample.yaml
    )
    
    echo Step 1: Training...
    python src\train_qlora.py --config %CONFIG_FILE% --lora configs\sample_lora.yaml --output_dir outputs\demo_run
    
    if errorlevel 1 (
        echo Error: Training failed
        exit /b 1
    )
    
    echo.
    echo Step 2: Evaluating...
    python src\eval_em_f1.py --model_path outputs\demo_run --eval_file data\sample_eval.jsonl --is_adapter --save_results
    
    if errorlevel 1 (
        echo Error: Evaluation failed
        exit /b 1
    )
    
    echo.
    echo Training pipeline completed!
    echo Check outputs\demo_run for the trained adapter
    echo Check reports\results.csv for evaluation metrics
)

if "%BACKEND%"=="true" if "%FRONTEND%"=="true" (
    echo.
    echo === Services Running ===
    echo Backend: http://localhost:8000
    echo Frontend: http://localhost:3000
    echo.
    echo Press Ctrl+C to stop all services
    pause
)

