@echo off
REM Demo script for Windows: Prepare data → Train (tiny) → Eval → Inference

setlocal enabledelayedexpansion

echo === MistralTune Demo Script ===
echo.

REM Check if we're in the right directory
if not exist "requirements.txt" (
    echo Error: Must run from project root directory
    exit /b 1
)

REM Check if sample data exists
if not exist "data\sample_train.jsonl" (
    echo Error: Sample data files not found
    echo Expected: data\sample_train.jsonl and data\sample_eval.jsonl
    exit /b 1
)

if not exist "data\sample_eval.jsonl" (
    echo Error: Sample eval file not found
    exit /b 1
)

REM Create outputs directory
if not exist "outputs" mkdir outputs

echo Step 1: Training on sample data...
python src\train_qlora.py --config configs\sample.yaml --lora configs\sample_lora.yaml --output_dir outputs\demo_run

if errorlevel 1 (
    echo Error: Training failed
    exit /b 1
)

echo.
echo Step 2: Evaluating the model...
python src\eval_em_f1.py --model_path outputs\demo_run --eval_file data\sample_eval.jsonl --is_adapter --save_results

if errorlevel 1 (
    echo Error: Evaluation failed
    exit /b 1
)

echo.
echo Step 3: Running inference comparison...
echo Note: Inference comparison requires API access. Skipping for demo.
echo To test inference, run:
echo   python src\mistral_api_inference.py --base_model ^<base^> --fine_tuned_model ^<ft^> --prompts "What is AI?"

echo.
echo === Demo completed successfully! ===
echo Check outputs\demo_run for the trained adapter
echo Check reports\results.csv for evaluation metrics

