# Verification Guide

This document describes how to verify that MistralTune is set up correctly and working end-to-end.

## Prerequisites Check

Before starting, verify you have:

- ✅ Python 3.10+ installed (`python --version` or `python3 --version`)
- ✅ Node.js 18+ installed (`node --version`)
- ✅ Git installed (`git --version`)
- ✅ Mistral API key (optional, but required for API features)

## Initial Setup Verification

### 1. Clone and Navigate

```bash
git clone <repository-url>
cd mistraltune
```

### 2. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env  # Linux/Mac
# or
copy .env.example .env  # Windows

# Edit .env and add your MISTRAL_API_KEY
```

Verify `.env` file exists and contains at least:
```env
MISTRAL_API_KEY=your-key-here
```

## One-Command Startup Verification

### Linux/Mac

```bash
./start.sh
```

**Expected Output:**
1. Python version check (✓ Python 3.x.x found)
2. Node.js version check (✓ Node.js v18.x.x found)
3. Virtual environment creation (if needed)
4. Dependency installation messages
5. Backend startup message
6. "✓ Backend is ready" message
7. Frontend startup message
8. Final status display with URLs

**Expected URLs:**
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

### Windows (PowerShell)

```powershell
.\start.ps1
```

**Expected Output:** Same as Linux/Mac above.

**Note:** If you get execution policy errors:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Service Health Checks

### Backend Health Check

Open a new terminal and run:

```bash
# Linux/Mac
curl http://localhost:8000/api/health

# Windows PowerShell
Invoke-WebRequest -Uri http://localhost:8000/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000000",
  "version": "1.0.0",
  "mistral_api_configured": true
}
```

### Frontend Health Check

Open browser and navigate to: http://localhost:3000

**Expected:**
- Page loads without errors
- Dashboard displays (may show empty state if no jobs/datasets)
- No console errors in browser DevTools (F12)

## End-to-End Verification

### 1. Backend API Verification

**Test Root Endpoint:**
```bash
curl http://localhost:8000/
```

**Expected:** JSON with API information

**Test API Documentation:**
- Open http://localhost:8000/docs in browser
- Should see Swagger UI with all endpoints listed
- Try the `/api/health` endpoint from the UI

### 2. Frontend-Backend Integration

**Test API Connection:**
1. Open http://localhost:3000 in browser
2. Open browser DevTools (F12) → Network tab
3. Navigate to Dashboard page
4. Check for API calls to `http://localhost:8000/api/jobs` and `/api/datasets`
5. Verify no CORS errors in console

**Expected:**
- API calls return 200 status
- Data loads (may be empty arrays if no jobs/datasets)
- No CORS errors

### 3. Dataset Upload Flow

1. Navigate to http://localhost:3000/datasets
2. Click "Upload Dataset" or similar button
3. Select a JSONL file (use `data/sample_train.jsonl` as test)
4. Verify upload succeeds
5. Check dataset appears in list

**Expected:**
- Upload completes without errors
- Dataset appears in the list
- File validation works (try invalid file to test error handling)

### 4. Job Creation Flow

1. Navigate to http://localhost:3000/jobs/new
2. Select a dataset (must upload one first)
3. Fill in job parameters:
   - Model: `open-mistral-7b`
   - Learning rate: `1e-4`
   - Epochs: `3`
4. Click "Create Job"
5. Verify job is created and redirects to job detail page

**Expected:**
- Job creation succeeds
- Redirect to job detail page
- Job status displays correctly
- WebSocket connection establishes (check browser console)

### 5. WebSocket Real-time Updates

1. Navigate to a job detail page (http://localhost:3000/jobs/{job-id})
2. Open browser DevTools → Network tab → WS (WebSocket)
3. Verify WebSocket connection is established
4. Wait for status updates (if job is running)

**Expected:**
- WebSocket connection shows as "101 Switching Protocols"
- Status updates appear in real-time
- Connection remains stable

### 6. Playground Testing

1. Navigate to http://localhost:3000/playground
2. Enter a prompt (e.g., "What is AI?")
3. Select a model
4. Click "Generate" or similar
5. Verify response is generated

**Expected:**
- Response generates successfully
- No API errors
- Response displays correctly

## Command Line Verification

### Backend Tests

```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Run tests
pytest tests/ -v
```

**Expected:**
- All tests pass
- Health endpoint test passes
- Data I/O tests pass

### Frontend Build Check

```bash
cd frontend
npm run build
```

**Expected:**
- Build completes without errors
- No TypeScript errors
- Production build succeeds

### Linting Checks

**Backend:**
```bash
ruff check src/ tests/
black --check src/ tests/
```

**Frontend:**
```bash
cd frontend
npm run lint
```

**Expected:**
- No linting errors (or only acceptable warnings)
- Code formatting is correct

## Known Limitations

1. **Mistral API Key Required**: Some features require a valid Mistral API key. Without it:
   - Dataset uploads to Mistral API will fail
   - Job creation via API will fail
   - Inference features will not work
   - Local QLoRA training still works

2. **GPU Required for Local Training**: QLoRA local training requires:
   - NVIDIA GPU with 24-48 GB VRAM
   - CUDA 11.8+
   - Proper drivers installed

3. **Port Conflicts**: If ports 8000 or 3000 are in use:
   - Change `BACKEND_PORT` and `FRONTEND_PORT` in `.env`
   - Update `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` accordingly

4. **Windows PowerShell**: Some features may require:
   - Execution policy adjustment
   - Running as administrator (for port binding)

## Troubleshooting

### Backend Won't Start

1. Check Python version: `python --version` (must be 3.10+)
2. Check virtual environment is activated
3. Check dependencies installed: `pip list | grep fastapi`
4. Check port availability: `netstat -an | grep 8000` (Linux/Mac) or `netstat -an | findstr 8000` (Windows)
5. Check logs: `backend.log` file

### Frontend Won't Start

1. Check Node.js version: `node --version` (must be 18+)
2. Check dependencies: `cd frontend && npm list`
3. Check port availability: `netstat -an | grep 3000` (Linux/Mac) or `netstat -an | findstr 3000` (Windows)
4. Check logs: `frontend.log` file

### Frontend Can't Connect to Backend

1. Verify backend is running: `curl http://localhost:8000/api/health`
2. Check CORS configuration in backend (should allow all origins in dev)
3. Verify `NEXT_PUBLIC_API_URL` in `.env` matches backend URL
4. Check browser console for specific error messages

### Tests Fail

1. Ensure virtual environment is activated
2. Ensure all dependencies are installed: `pip install -r requirements.txt`
3. Check test output for specific error messages
4. Verify environment variables are set if needed

## Verification Checklist

Use this checklist to verify a complete setup:

- [ ] Prerequisites installed (Python 3.10+, Node.js 18+)
- [ ] Repository cloned
- [ ] `.env` file created and configured
- [ ] `start.sh` or `start.ps1` runs successfully
- [ ] Backend health check returns healthy status
- [ ] Frontend loads in browser
- [ ] API documentation accessible at /docs
- [ ] Frontend can call backend APIs (no CORS errors)
- [ ] Dataset upload works
- [ ] Job creation works (if API key configured)
- [ ] WebSocket connections work
- [ ] Playground generates responses
- [ ] All tests pass
- [ ] Frontend builds successfully
- [ ] Linting passes

## Next Steps

Once verification is complete:

1. Explore the web dashboard
2. Upload your own datasets
3. Create fine-tuning jobs
4. Experiment with different models and parameters
5. Review the API documentation for advanced usage
6. Check out the training scripts for local QLoRA training

For more information, see the main [README.md](../README.md).

