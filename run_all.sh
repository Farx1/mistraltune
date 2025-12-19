#!/bin/bash
# Script to launch everything: Backend + Frontend + Optional Training
# Supports local models already downloaded

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== MistralTune - Complete Launch Script ===${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: Must run from project root directory${NC}"
    exit 1
fi

# Parse arguments
BACKEND=false
FRONTEND=false
TRAIN=false
MODEL_PATH=""
USE_LOCAL_MODEL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --backend)
            BACKEND=true
            shift
            ;;
        --frontend)
            FRONTEND=true
            shift
            ;;
        --train)
            TRAIN=true
            shift
            ;;
        --model-path)
            MODEL_PATH="$2"
            USE_LOCAL_MODEL=true
            shift 2
            ;;
        --all)
            BACKEND=true
            FRONTEND=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --backend          Start backend API server"
            echo "  --frontend         Start frontend Next.js app"
            echo "  --train            Run training pipeline (demo)"
            echo "  --model-path PATH  Use local model at PATH instead of downloading"
            echo "  --all              Start both backend and frontend"
            echo "  --help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --all                           # Start backend + frontend"
            echo "  $0 --backend --frontend            # Same as --all"
            echo "  $0 --train                         # Run training demo"
            echo "  $0 --train --model-path ./models/mistral-7b  # Train with local model"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# If no options specified, show help
if [ "$BACKEND" = false ] && [ "$FRONTEND" = false ] && [ "$TRAIN" = false ]; then
    echo -e "${YELLOW}No options specified. Showing help:${NC}"
    echo ""
    $0 --help
    exit 0
fi

# Check Python environment
if [ "$BACKEND" = true ] || [ "$TRAIN" = true ]; then
    if ! command -v python &> /dev/null; then
        echo -e "${RED}Error: Python not found${NC}"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d ".venv" ]; then
        echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
        python -m venv .venv
        echo -e "${GREEN}Virtual environment created${NC}"
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Check if dependencies are installed
    if ! python -c "import torch" &> /dev/null; then
        echo -e "${YELLOW}Dependencies not installed. Installing...${NC}"
        pip install -r requirements.txt
        echo -e "${GREEN}Dependencies installed${NC}"
    fi
fi

# Check Node.js for frontend
if [ "$FRONTEND" = true ]; then
    if ! command -v node &> /dev/null; then
        echo -e "${RED}Error: Node.js not found${NC}"
        exit 1
    fi
    
    if [ ! -d "frontend/node_modules" ]; then
        echo -e "${YELLOW}Frontend dependencies not installed. Installing...${NC}"
        cd frontend
        npm install
        cd ..
        echo -e "${GREEN}Frontend dependencies installed${NC}"
    fi
fi

# Create necessary directories
mkdir -p outputs
mkdir -p reports
mkdir -p data

# Function to start backend
start_backend() {
    echo -e "${BLUE}Starting backend API server...${NC}"
    
    # Check for API key
    if [ -z "$MISTRAL_API_KEY" ]; then
        echo -e "${YELLOW}WARNING: MISTRAL_API_KEY not set${NC}"
        echo "Backend will work for local training but Mistral API features will be disabled"
    fi
    
    # Start backend in background
    python src/api/main.py &
    BACKEND_PID=$!
    echo -e "${GREEN}Backend started (PID: $BACKEND_PID)${NC}"
    echo "Backend API: http://localhost:8000"
    echo "API Docs: http://localhost:8000/docs"
    
    # Wait a bit for backend to start
    sleep 3
}

# Function to start frontend
start_frontend() {
    echo -e "${BLUE}Starting frontend...${NC}"
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    echo -e "${GREEN}Frontend started (PID: $FRONTEND_PID)${NC}"
    echo "Frontend: http://localhost:3000"
}

# Function to run training
run_training() {
    echo -e "${BLUE}Running training pipeline...${NC}"
    
    # Check if sample data exists
    if [ ! -f "data/sample_train.jsonl" ] || [ ! -f "data/sample_eval.jsonl" ]; then
        echo -e "${RED}Error: Sample data files not found${NC}"
        exit 1
    fi
    
    # Create config for local model if specified
    if [ "$USE_LOCAL_MODEL" = true ]; then
        if [ ! -d "$MODEL_PATH" ]; then
            echo -e "${RED}Error: Model path not found: $MODEL_PATH${NC}"
            exit 1
        fi
        
        echo -e "${GREEN}Using local model: $MODEL_PATH${NC}"
        
        # Create temporary config with local model
        cat > configs/local_model.yaml << EOF
base_model: "$MODEL_PATH"
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
EOF
        
        CONFIG_FILE="configs/local_model.yaml"
    else
        CONFIG_FILE="configs/sample.yaml"
    fi
    
    echo "Step 1: Training..."
    python src/train_qlora.py \
        --config "$CONFIG_FILE" \
        --lora configs/sample_lora.yaml \
        --output_dir outputs/demo_run
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Training failed${NC}"
        exit 1
    fi
    
    echo ""
    echo "Step 2: Evaluating..."
    python src/eval_em_f1.py \
        --model_path outputs/demo_run \
        --eval_file data/sample_eval.jsonl \
        --is_adapter \
        --save_results
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Evaluation failed${NC}"
        exit 1
    fi
    
    echo ""
    echo -e "${GREEN}Training pipeline completed!${NC}"
    echo "Check outputs/demo_run for the trained adapter"
    echo "Check reports/results.csv for evaluation metrics"
}

# Trap to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Cleaning up...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}Cleanup complete${NC}"
}

trap cleanup EXIT INT TERM

# Start services
if [ "$BACKEND" = true ]; then
    start_backend
fi

if [ "$FRONTEND" = true ]; then
    start_frontend
fi

if [ "$TRAIN" = true ]; then
    run_training
fi

# If both backend and frontend are running, wait
if [ "$BACKEND" = true ] && [ "$FRONTEND" = true ]; then
    echo ""
    echo -e "${GREEN}=== Services Running ===${NC}"
    echo "Backend: http://localhost:8000"
    echo "Frontend: http://localhost:3000"
    echo ""
    echo "Press Ctrl+C to stop all services"
    wait
elif [ "$TRAIN" = true ]; then
    # Training is done, exit
    exit 0
fi

