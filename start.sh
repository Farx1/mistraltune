#!/bin/bash
# MistralTune - Unified Start Script (Linux/Mac)
# Starts backend and frontend with automatic setup

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}
BACKEND_URL="http://localhost:${BACKEND_PORT}"
FRONTEND_URL="http://localhost:${FRONTEND_PORT}"

echo -e "${BLUE}=== MistralTune - Starting Services ===${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}Error: Must run from project root directory${NC}"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 not found. Please install Python 3.10 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "${RED}Error: Python 3.10+ required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js not found. Please install Node.js 18 or higher.${NC}"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo -e "${RED}Error: Node.js 18+ required. Found: $(node -v)${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Node.js $(node -v) found${NC}"

# Setup Python virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
source .venv/bin/activate

# Install backend dependencies
if ! python -c "import fastapi" &> /dev/null; then
    echo -e "${YELLOW}Installing backend dependencies...${NC}"
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓ Backend dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Backend dependencies already installed${NC}"
fi

# Install frontend dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    cd frontend
    npm install --silent
    cd ..
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Frontend dependencies already installed${NC}"
fi

# Create necessary directories
mkdir -p data/uploads
mkdir -p data

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found.${NC}"
    echo "Copy .env.example to .env and configure your MISTRAL_API_KEY"
    echo "Backend will start but Mistral API features will be disabled."
    echo ""
fi

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 || nc -z localhost $port 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Check if ports are available
if check_port $BACKEND_PORT; then
    echo -e "${RED}Error: Port $BACKEND_PORT is already in use${NC}"
    exit 1
fi

if check_port $FRONTEND_PORT; then
    echo -e "${RED}Error: Port $FRONTEND_PORT is already in use${NC}"
    exit 1
fi

# Function to wait for health check
wait_for_backend() {
    local max_attempts=30
    local attempt=0
    
    echo -e "${YELLOW}Waiting for backend to be ready...${NC}"
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "${BACKEND_URL}/api/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Backend is ready${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    echo -e "${RED}Error: Backend failed to start within ${max_attempts} seconds${NC}"
    return 1
}

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✓ Backend stopped${NC}"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}✓ Frontend stopped${NC}"
    fi
    
    echo -e "${GREEN}Cleanup complete${NC}"
    exit 0
}

# Trap signals for cleanup
trap cleanup EXIT INT TERM

# Start backend
echo -e "${BLUE}Starting backend on port ${BACKEND_PORT}...${NC}"
cd src/api
python main.py > ../../backend.log 2>&1 &
BACKEND_PID=$!
cd ../..
echo -e "${GREEN}Backend started (PID: $BACKEND_PID)${NC}"

# Wait for backend to be ready
if ! wait_for_backend; then
    echo -e "${RED}Backend startup failed. Check backend.log for details.${NC}"
    exit 1
fi

# Start frontend
echo -e "${BLUE}Starting frontend on port ${FRONTEND_PORT}...${NC}"
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo -e "${GREEN}Frontend started (PID: $FRONTEND_PID)${NC}"

# Wait a bit for frontend to start
sleep 3

# Display status
echo ""
echo -e "${GREEN}=== Services Running ===${NC}"
echo ""
echo -e "Backend API:  ${BLUE}${BACKEND_URL}${NC}"
echo -e "API Docs:    ${BLUE}${BACKEND_URL}/docs${NC}"
echo -e "Frontend:    ${BLUE}${FRONTEND_URL}${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for user interrupt
wait

