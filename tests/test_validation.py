"""
Tests for JSONL validation functions.

Tests the validation logic for JSONL files used in fine-tuning.
"""

import pytest
import sys
import tempfile
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mistral_api_finetune import validate_jsonl


def test_validate_jsonl_valid():
    """Test validation of a valid JSONL file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('{"instruction": "What is AI?", "input": "", "output": "AI is artificial intelligence"}\n')
        f.write('{"instruction": "What is ML?", "output": "ML is machine learning"}\n')
        temp_path = f.name
    
    try:
        is_valid, error_msg, num_lines = validate_jsonl(temp_path)
        assert is_valid is True
        assert error_msg == ""
        assert num_lines == 2
    finally:
        os.unlink(temp_path)


def test_validate_jsonl_missing_fields():
    """Test validation of a file with missing required fields."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('{"instruction": "What is AI?"}\n')  # Missing "output"
        temp_path = f.name
    
    try:
        is_valid, error_msg, num_lines = validate_jsonl(temp_path)
        assert is_valid is False
        assert "champs manquants" in error_msg.lower() or "missing" in error_msg.lower()
    finally:
        os.unlink(temp_path)


def test_validate_jsonl_invalid_json():
    """Test validation of a file with invalid JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('{"instruction": "What is AI?", invalid json}\n')
        temp_path = f.name
    
    try:
        is_valid, error_msg, num_lines = validate_jsonl(temp_path)
        assert is_valid is False
        assert "json" in error_msg.lower() or "invalide" in error_msg.lower()
    finally:
        os.unlink(temp_path)


def test_validate_jsonl_empty_file():
    """Test validation of an empty file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        # File is empty
        temp_path = f.name
    
    try:
        is_valid, error_msg, num_lines = validate_jsonl(temp_path)
        assert is_valid is False
        assert "vide" in error_msg.lower() or "empty" in error_msg.lower()
    finally:
        os.unlink(temp_path)


def test_validate_jsonl_with_input_field():
    """Test validation of a file with optional input field."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('{"instruction": "Translate", "input": "Hello", "output": "Bonjour"}\n')
        temp_path = f.name
    
    try:
        is_valid, error_msg, num_lines = validate_jsonl(temp_path)
        assert is_valid is True
        assert num_lines == 1
    finally:
        os.unlink(temp_path)

