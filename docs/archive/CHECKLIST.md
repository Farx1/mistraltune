# Verification Checklist

This document tracks what has been verified and tested.

## Setup & Installation

- [x] **Dependencies**: `requirements.txt` includes all necessary packages
- [x] **Sample Data**: `data/sample_train.jsonl` and `data/sample_eval.jsonl` created
- [x] **Configs**: Sample configs (`configs/sample.yaml`, `configs/sample_lora.yaml`) created
- [x] **Demo Scripts**: `scripts/demo.sh` and `scripts/demo.bat` created
- [x] **Makefile**: `make demo` target added

## Code Quality

- [x] **Translation**: All French comments translated to English
  - `src/train_qlora.py`
  - `src/eval_em_f1.py`
  - `src/utils/seed.py`
  - `src/utils/data_io.py`
  - `Makefile`
- [x] **Formatting**: `pyproject.toml` configured for ruff and black
- [x] **Linting**: Ruff configuration added
- [x] **Tests**: Pytest tests created
  - `tests/test_data_io.py`: Data loading and metrics tests
  - `tests/test_smoke.py`: Tokenization and batch tests

## Error Handling

- [x] **Dataset Validation**: `validate_dataset_files()` checks file existence and format
- [x] **GPU Detection**: Clear warnings when no GPU available
- [x] **File Checks**: All scripts validate input files exist
- [x] **Clear Messages**: Error messages indicate what went wrong and how to fix

## Reproducibility

- [x] **Seeds**: Deterministic seeds set (default: 42)
- [x] **Config Saving**: Used configs saved to `outputs/<run>/config_used.yaml`
- [x] **Metadata**: Training metadata saved with seed, timestamps, hyperparameters
- [x] **Output Organization**: Default output directory changed to `outputs/`

## Evaluation

- [x] **Metrics**: EM, F1, and average length calculated
- [x] **CSV Export**: Results saved to `reports/results.csv`
- [x] **JSON Export**: Detailed metrics saved to `outputs/<run>/metrics.json`
- [x] **Examples**: First 3 examples printed, first 5 saved to JSON

## Documentation

- [x] **Architecture**: `docs/ARCHITECTURE.md` created
- [x] **Improvements**: `IMPROVEMENTS.md` created
- [x] **Checklist**: This file created
- [x] **Frontend Env**: `.env.example` created in frontend directory

## Commands Verified

### Test Commands (Ready to Run)

1. **Run Tests** (no GPU required):
   ```bash
   pytest tests/ -v
   ```
   Status: Tests created, ready to run

2. **Format Code**:
   ```bash
   ruff check src/ tests/
   black src/ tests/
   ```
   Status: Tools configured, ready to use

3. **Demo Script** (requires GPU for training, but validates setup):
   ```bash
   make demo
   # or
   bash scripts/demo.sh
   # or (Windows)
   scripts\demo.bat
   ```
   Status: Scripts created, ready to run

### Training Commands (Require GPU)

4. **Quick Training** (sample data, 1 epoch):
   ```bash
   python src/train_qlora.py --config configs/sample.yaml --lora configs/sample_lora.yaml
   ```
   Status: Ready to run (will be slow on CPU)

5. **Full Training**:
   ```bash
   python src/train_qlora.py --config configs/base.yaml --lora configs/lora_r16a32.yaml
   ```
   Status: Ready to run (requires GPU)

6. **Evaluation**:
   ```bash
   python src/eval_em_f1.py --model_path outputs/demo_run --eval_file data/sample_eval.jsonl --is_adapter --save_results
   ```
   Status: Ready to run

## Notes

- **CPU Testing**: Tests can run without GPU (they only test data loading and tokenization)
- **Training**: Full training requires GPU for reasonable performance
- **Demo Script**: Uses minimal configs for quick testing (1 epoch, small batch)
- **Error Handling**: All scripts now have proper error handling and clear messages

## What Still Needs Manual Testing

1. **Actual Training Run**: Run `make demo` or training script with GPU to verify end-to-end
2. **Frontend**: Start frontend and verify API calls work
3. **Full Pipeline**: Run complete pipeline from training → eval → inference

## Known Limitations

- Demo script assumes GPU availability (will warn and ask to continue on CPU)
- Some tests require downloading models (first run will be slow)
- Frontend requires backend to be running for full functionality

