# Reproduction Instructions

Exact commands to reproduce the project locally.

## Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- GPU with 24+ GB VRAM (recommended for training)
- CUDA 11.8+ (for bitsandbytes)

## Setup

### 1. Clone and Setup Environment

```bash
# Clone repository
git clone <repo-url>
cd mistraltune

# Create virtual environment
python -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Verify Setup (CPU - No GPU Required)

```bash
# Run tests
pytest tests/ -v

# Expected output: All tests pass
```

### 3. Format and Lint Code

```bash
# Check code style
ruff check src/ tests/

# Format code
black src/ tests/
```

## CPU Smoke Test (No GPU Required)

This tests the pipeline without actual training:

```bash
# Run demo script (will validate setup, but training will be slow on CPU)
make demo

# Or manually:
bash scripts/demo.sh
# Windows: scripts\demo.bat
```

**Expected**: Script validates files, attempts training (will be slow on CPU), runs evaluation.

## GPU Training (Full Pipeline)

### Quick Test (Sample Data, 1 Epoch)

```bash
# Train on sample data
python src/train_qlora.py \
    --config configs/sample.yaml \
    --lora configs/sample_lora.yaml \
    --output_dir outputs/demo_run

# Evaluate
python src/eval_em_f1.py \
    --model_path outputs/demo_run \
    --eval_file data/sample_eval.jsonl \
    --is_adapter \
    --save_results

# Check results
cat outputs/demo_run/metrics.json
cat reports/results.csv
```

### Full Training (Production Config)

```bash
# Train with full config
python src/train_qlora.py \
    --config configs/base.yaml \
    --lora configs/lora_r16a32.yaml \
    --output_dir outputs/full_run

# Evaluate
python src/eval_em_f1.py \
    --model_path outputs/full_run \
    --eval_file data/val.jsonl \
    --is_adapter \
    --save_results
```

## Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create .env.local from example
cp .env.example .env.local

# Edit .env.local if needed (defaults should work for local dev)
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Start frontend
npm run dev
```

Frontend will be available at `http://localhost:3000`

## Backend API Setup

```bash
# From project root, with venv activated

# Set API key (if using Mistral API)
export MISTRAL_API_KEY="your-key-here"  # Linux/Mac
set MISTRAL_API_KEY=your-key-here       # Windows

# Start backend
python src/api/main.py

# Or with uvicorn
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

## Complete End-to-End Test

1. **Start Backend**:
   ```bash
   python src/api/main.py
   ```

2. **Start Frontend** (new terminal):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Train Model** (new terminal):
   ```bash
   python src/train_qlora.py --config configs/sample.yaml --lora configs/sample_lora.yaml
   ```

4. **Test in Frontend**:
   - Open `http://localhost:3000`
   - Upload a dataset
   - Create a job
   - Monitor progress
   - Test inference

## Verification

After running, verify:

1. **Training Output**:
   ```bash
   ls outputs/demo_run/
   # Should contain: adapter_model.bin, adapter_config.json, training_metadata.yaml, config_used.yaml, metrics.json
   ```

2. **Evaluation Results**:
   ```bash
   cat reports/results.csv
   # Should contain evaluation metrics
   ```

3. **Metrics JSON**:
   ```bash
   cat outputs/demo_run/metrics.json
   # Should contain EM, F1, avg_length, and examples
   ```

## Troubleshooting

### "No GPU detected"
- Training will be very slow on CPU
- Script will warn and ask to continue
- For actual training, use a GPU-enabled environment

### "File not found" errors
- Ensure you're running from project root
- Check that sample data files exist: `data/sample_train.jsonl`, `data/sample_eval.jsonl`

### "Module not found" errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

### Frontend connection errors
- Ensure backend is running on `http://localhost:8000`
- Check `.env.local` has correct API URL
- Check CORS settings in backend

## Expected Outputs

### Training
- Model adapter saved to `outputs/<run_id>/`
- Training metadata in `outputs/<run_id>/training_metadata.yaml`
- Used config in `outputs/<run_id>/config_used.yaml`

### Evaluation
- Metrics in `outputs/<run_id>/metrics.json`
- Results in `reports/results.csv`
- Console output with EM, F1, avg_length

### Tests
- All tests pass
- No errors or warnings

