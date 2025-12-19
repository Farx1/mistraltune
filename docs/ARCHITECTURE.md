# MistralTune Architecture

## Overview

MistralTune is a complete fine-tuning platform for Mistral models supporting two approaches:
1. **Mistral API Fine-tuning** - Cloud-based, managed fine-tuning via Mistral's API
2. **QLoRA Local Fine-tuning** - On-premise fine-tuning with full control

## Pipeline Components

### 1. Data Preparation
- **Format**: JSONL files with `instruction`, `input` (optional), and `output` fields
- **Location**: `data/` directory
- **Scripts**: `src/utils/data_io.py` handles loading and formatting

### 2. Training

#### QLoRA Local Training
- **Entrypoint**: `src/train_qlora.py`
- **Config**: YAML files in `configs/` (base.yaml + lora configs)
- **Output**: LoRA adapters saved to `runs/` or `outputs/`
- **Key command**:
  ```bash
  python src/train_qlora.py --config configs/base.yaml --lora configs/lora_r16a32.yaml
  ```

#### Mistral API Fine-tuning
- **Entrypoint**: `src/mistral_api_finetune.py`
- **Process**: Upload dataset → Create job → Monitor status
- **Key command**:
  ```bash
  python src/mistral_api_finetune.py --train_file data/train.jsonl --val_file data/val.jsonl
  ```

### 3. Evaluation
- **Entrypoint**: `src/eval_em_f1.py`
- **Metrics**: Exact Match (EM), F1 score, average length
- **Key command**:
  ```bash
  python src/eval_em_f1.py --model_path <path> --eval_file data/val.jsonl
  ```

### 4. Inference
- **Entrypoint**: `src/mistral_api_inference.py` (API models)
- **Comparison**: Side-by-side base vs fine-tuned model responses
- **Key command**:
  ```bash
  python src/mistral_api_inference.py --base_model <base> --fine_tuned_model <ft> --prompts "prompt1" "prompt2"
  ```

### 5. Backend API
- **Entrypoint**: `src/api/main.py`
- **Framework**: FastAPI with WebSocket support
- **Features**: Dataset upload, job management, inference endpoints
- **Key command**:
  ```bash
  python src/api/main.py
  # or: uvicorn src.api.main:app --reload
  ```

### 6. Frontend
- **Framework**: Next.js 15 with TypeScript
- **Location**: `frontend/` directory
- **Key command**:
  ```bash
  cd frontend && npm run dev
  ```

## Data Flow

```
Dataset (JSONL) 
  → Training (QLoRA or API)
    → Adapter/Model Output
      → Evaluation (EM/F1 metrics)
        → Inference/Comparison
          → Results & Reports
```

## Configuration System

- **Base config**: `configs/base.yaml` - Model, paths, training hyperparameters
- **LoRA configs**: `configs/lora_*.yaml` - LoRA-specific parameters (r, alpha, etc.)
- **Environment**: `.env` or environment variables for API keys

## Output Structure

```
outputs/
  ├── <run_id>/
  │   ├── adapter_config.json
  │   ├── adapter_model.bin
  │   ├── training_metadata.yaml
  │   └── metrics.json
```

## Key Dependencies

- **Training**: torch, transformers, peft, trl, bitsandbytes
- **API**: fastapi, mistralai, websockets
- **Frontend**: next.js, react, tailwindcss, shadcn/ui

