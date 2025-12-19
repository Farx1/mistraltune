#!/bin/bash
# Demo script: Prepare data → Train (tiny) → Eval → Inference

set -e  # Exit on error

echo "=== MistralTune Demo Script ==="
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: Must run from project root directory"
    exit 1
fi

# Check Python environment
if ! command -v python &> /dev/null; then
    echo "Error: Python not found"
    exit 1
fi

# Check if sample data exists
if [ ! -f "data/sample_train.jsonl" ] || [ ! -f "data/sample_eval.jsonl" ]; then
    echo "Error: Sample data files not found"
    echo "Expected: data/sample_train.jsonl and data/sample_eval.jsonl"
    exit 1
fi

# Create outputs directory
mkdir -p outputs

echo "Step 1: Training on sample data..."
python src/train_qlora.py \
    --config configs/sample.yaml \
    --lora configs/sample_lora.yaml \
    --output_dir outputs/demo_run

if [ $? -ne 0 ]; then
    echo "Error: Training failed"
    exit 1
fi

echo ""
echo "Step 2: Evaluating the model..."
python src/eval_em_f1.py \
    --model_path outputs/demo_run \
    --eval_file data/sample_eval.jsonl \
    --is_adapter \
    --save_results

if [ $? -ne 0 ]; then
    echo "Error: Evaluation failed"
    exit 1
fi

echo ""
echo "Step 3: Running inference comparison..."
echo "Note: Inference comparison requires API access. Skipping for demo."
echo "To test inference, run:"
echo "  python src/mistral_api_inference.py --base_model <base> --fine_tuned_model <ft> --prompts 'What is AI?'"

echo ""
echo "=== Demo completed successfully! ==="
echo "Check outputs/demo_run for the trained adapter"
echo "Check reports/results.csv for evaluation metrics"

