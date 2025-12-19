"""
Tests for FastAPI endpoints.

Tests all API endpoints with mocked Mistral API to avoid real API calls.
"""

import pytest
import sys
import tempfile
import os
from pathlib import Path
from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from api.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    # Set DEMO_MODE for all tests
    os.environ["DEMO_MODE"] = "1"
    return TestClient(app)


def test_health_endpoint(client):
    """Test that the /api/health endpoint returns healthy status."""
    response = client.get("/api/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "mistral_api_configured" in data
    assert isinstance(data["mistral_api_configured"], bool)


def test_root_endpoint(client):
    """Test that the root endpoint returns API information."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "message" in data
    assert "version" in data
    assert "endpoints" in data


def test_upload_dataset_endpoint(client):
    """Test uploading a valid JSONL file."""
    # Create a temporary valid JSONL file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('{"instruction": "What is AI?", "input": "", "output": "AI is artificial intelligence"}\n')
        f.write('{"instruction": "What is ML?", "input": "", "output": "ML is machine learning"}\n')
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as file:
            response = client.post(
                "/api/datasets/upload",
                files={"file": ("test.jsonl", file, "application/jsonl")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "file_id" in data
        assert "filename" in data
        assert "num_samples" in data
        assert data["num_samples"] == 2
    finally:
        os.unlink(temp_path)


def test_upload_dataset_invalid_format(client):
    """Test that uploading a non-JSONL file is rejected."""
    # Create a temporary non-JSONL file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is not JSONL")
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as file:
            response = client.post(
                "/api/datasets/upload",
                files={"file": ("test.txt", file, "text/plain")}
            )
        
        assert response.status_code == 400
        assert "jsonl" in response.json()["detail"].lower()
    finally:
        os.unlink(temp_path)


def test_list_datasets(client):
    """Test listing datasets."""
    response = client.get("/api/datasets")
    
    assert response.status_code == 200
    data = response.json()
    assert "datasets" in data
    assert isinstance(data["datasets"], list)


def test_create_job_mistral_api(client):
    """Test creating a fine-tuning job (mock mode)."""
    # First upload a dataset
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('{"instruction": "Test?", "input": "", "output": "Answer"}\n')
        temp_path = f.name
    
    try:
        # Upload dataset
        with open(temp_path, 'rb') as file:
            upload_response = client.post(
                "/api/datasets/upload",
                files={"file": ("test.jsonl", file, "application/jsonl")}
            )
        file_id = upload_response.json()["file_id"]
        
        # Create job
        job_data = {
            "model": "open-mistral-7b",
            "training_file_id": file_id,
            "learning_rate": 1e-4,
            "epochs": 3,
            "job_type": "mistral_api"
        }
        response = client.post("/api/jobs/create", json=job_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "status" in data
    finally:
        os.unlink(temp_path)


def test_get_job_status(client):
    """Test getting job status."""
    # First create a job
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('{"instruction": "Test?", "input": "", "output": "Answer"}\n')
        temp_path = f.name
    
    try:
        # Upload dataset
        with open(temp_path, 'rb') as file:
            upload_response = client.post(
                "/api/datasets/upload",
                files={"file": ("test.jsonl", file, "application/jsonl")}
            )
        file_id = upload_response.json()["file_id"]
        
        # Create job
        job_data = {
            "model": "open-mistral-7b",
            "training_file_id": file_id,
            "job_type": "mistral_api"
        }
        create_response = client.post("/api/jobs/create", json=job_data)
        job_id = create_response.json()["job_id"]
        
        # Get job status
        response = client.get(f"/api/jobs/{job_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "status" in data
        assert "model" in data
    finally:
        os.unlink(temp_path)


def test_inference_generate(client):
    """Test the inference generation endpoint (mock mode)."""
    response = client.post(
        "/api/inference/generate",
        params={
            "model": "open-mistral-7b",
            "prompt": "What is AI?",
            "temperature": 0.7,
            "max_tokens": 100
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data or "content" in data


def test_inference_compare(client):
    """Test the model comparison endpoint (mock mode)."""
    request_data = {
        "base_model": "open-mistral-7b",
        "fine_tuned_model": "ft:open-mistral-7b:test123:20240101:abc123",
        "prompts": ["What is AI?", "What is machine learning?"],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    response = client.post("/api/inference/compare", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)

