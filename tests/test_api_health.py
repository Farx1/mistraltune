"""
Tests for the FastAPI backend health endpoint.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_health_endpoint(client):
    """Test that the /api/health endpoint returns healthy status."""
    response = client.get("/api/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

