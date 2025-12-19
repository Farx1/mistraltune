"""
Pytest configuration and fixtures for MistralTune tests.

Provides mock fixtures for Mistral API client to enable testing without real API calls.
"""

import os
import pytest
from unittest.mock import Mock, MagicMock
from typing import Optional
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set DEMO_MODE by default for tests
if not os.getenv("DEMO_MODE"):
    os.environ["DEMO_MODE"] = "1"


def get_mock_mistral_client() -> Mock:
    """
    Create a mock Mistral client with realistic responses.
    
    Returns:
        Mock object that mimics the Mistral API client
    """
    mock_client = Mock()
    
    # Mock files.upload method
    mock_upload = Mock()
    mock_upload.id = "file_test123"
    mock_upload.filename = "test.jsonl"
    mock_upload.purpose = "fine-tuning"
    mock_client.files.upload = Mock(return_value=mock_upload)
    
    # Mock fine_tuning.jobs.create method
    mock_job = Mock()
    mock_job.id = "ftjob_test123"
    mock_job.model = "open-mistral-7b"
    mock_job.status = "validated"
    mock_job.created_at = 1234567890
    mock_job.fine_tuned_model = None
    mock_job.error = None
    mock_client.fine_tuning.jobs.create = Mock(return_value=mock_job)
    
    # Mock fine_tuning.jobs.get method
    mock_job_status = Mock()
    mock_job_status.id = "ftjob_test123"
    mock_job_status.model = "open-mistral-7b"
    mock_job_status.status = "succeeded"
    mock_job_status.created_at = 1234567890
    mock_job_status.fine_tuned_model = "ft:open-mistral-7b:test123:20240101:abc123"
    mock_job_status.error = None
    mock_client.fine_tuning.jobs.get = Mock(return_value=mock_job_status)
    
    # Mock chat.completions.create method
    mock_chat_response = Mock()
    mock_choice = Mock()
    mock_choice.message = Mock()
    mock_choice.message.content = "This is a mock response from the fine-tuned model."
    mock_choice.finish_reason = "stop"
    mock_chat_response.choices = [mock_choice]
    mock_chat_response.usage = Mock()
    mock_chat_response.usage.prompt_tokens = 10
    mock_chat_response.usage.completion_tokens = 20
    mock_chat_response.usage.total_tokens = 30
    mock_client.chat.completions.create = Mock(return_value=mock_chat_response)
    
    return mock_client


@pytest.fixture
def mock_mistral_client():
    """Fixture that provides a mock Mistral client."""
    return get_mock_mistral_client()


@pytest.fixture
def demo_mode(monkeypatch):
    """Fixture that sets DEMO_MODE=1 for tests."""
    monkeypatch.setenv("DEMO_MODE", "1")
    yield
    monkeypatch.delenv("DEMO_MODE", raising=False)


@pytest.fixture
def temp_data_dir(tmp_path):
    """Fixture that provides a temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    uploads_dir = data_dir / "uploads"
    uploads_dir.mkdir()
    return data_dir

