"""
Smoke tests for data loading and tokenization.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.data_io import load_jsonl, format_instruction, build_hf_dataset
from utils.metrics import normalize_text, exact_match, f1_score_tokens


def test_load_jsonl():
    """Test loading JSONL file."""
    # Create temporary JSONL file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('{"instruction": "Test?", "input": "", "output": "Answer"}\n')
        f.write('{"instruction": "Another?", "output": "Another answer"}\n')
        temp_path = f.name
    
    try:
        data = load_jsonl(temp_path)
        assert len(data) == 2
        assert data[0]['instruction'] == "Test?"
        assert data[0]['output'] == "Answer"
    finally:
        os.unlink(temp_path)


def test_format_instruction():
    """Test instruction formatting."""
    formatted = format_instruction("What is AI?", "", "AI is artificial intelligence")
    assert "[INST]" in formatted
    assert "[/INST]" in formatted
    assert "AI is artificial intelligence" in formatted


def test_build_hf_dataset():
    """Test building HuggingFace dataset."""
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as train_f:
        train_f.write('{"instruction": "Test?", "output": "Answer"}\n')
        train_path = train_f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as eval_f:
        eval_f.write('{"instruction": "Eval?", "output": "Eval answer"}\n')
        eval_path = eval_f.name
    
    try:
        dataset = build_hf_dataset(train_path, eval_path)
        assert 'train' in dataset
        assert 'validation' in dataset
        assert len(dataset['train']) == 1
        assert len(dataset['validation']) == 1
    finally:
        os.unlink(train_path)
        os.unlink(eval_path)


def test_normalize_text():
    """Test text normalization."""
    assert normalize_text("Hello, World!") == "hello world"
    assert normalize_text("  Test   Text  ") == "test text"


def test_exact_match():
    """Test exact match metric."""
    assert exact_match("AI is artificial intelligence", "AI is artificial intelligence") == 1
    assert exact_match("AI is AI", "AI is artificial intelligence") == 0
    # Should be case-insensitive
    assert exact_match("AI IS ARTIFICIAL INTELLIGENCE", "ai is artificial intelligence") == 1


def test_f1_score_tokens():
    """Test F1 score calculation."""
    # Perfect match
    assert f1_score_tokens("AI is artificial intelligence", "AI is artificial intelligence") == 1.0
    # Partial match
    f1 = f1_score_tokens("AI is machine learning", "AI is artificial intelligence")
    assert 0 < f1 < 1
    # No match
    assert f1_score_tokens("completely different", "AI is artificial intelligence") == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

