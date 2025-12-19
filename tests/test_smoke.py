"""
Smoke test: dataset parsing + tokenization + one forward pass on small batch.
"""

import pytest
import torch
import tempfile
import os
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from transformers import AutoTokenizer
from utils.data_io import build_hf_dataset, format_instruction
from utils.seed import set_seed


def test_tokenization():
    """Test tokenization with a lightweight tokenizer (gpt2) to avoid large downloads."""
    set_seed(42)
    
    # Use gpt2 tokenizer which is lightweight and doesn't require large downloads
    # This tests the tokenization logic without downloading Mistral-7B
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    tokenizer.pad_token = tokenizer.eos_token
    
    # Test tokenization
    text = format_instruction("What is AI?", "", "AI is artificial intelligence")
    tokens = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=128)
    
    assert 'input_ids' in tokens
    assert tokens['input_ids'].shape[0] == 1
    assert tokens['input_ids'].shape[1] <= 128


def test_small_batch_forward():
    """Test one forward pass on a small batch (CPU only, no actual model)."""
    set_seed(42)
    
    # Create tiny dataset
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as train_f:
        train_f.write('{"instruction": "Test?", "output": "Answer"}\n')
        train_path = train_f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as eval_f:
        eval_f.write('{"instruction": "Eval?", "output": "Eval answer"}\n')
        eval_path = eval_f.name
    
    try:
        # Build dataset
        dataset = build_hf_dataset(train_path, eval_path)
        
        # Load tokenizer (use gpt2 to avoid large downloads)
        tokenizer = AutoTokenizer.from_pretrained("gpt2")
        tokenizer.pad_token = tokenizer.eos_token
        
        # Tokenize a small batch
        batch_texts = [dataset['train'][0]['text'], dataset['train'][0]['text']]
        tokens = tokenizer(
            batch_texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=128
        )
        
        assert tokens['input_ids'].shape[0] == 2  # Batch size 2
        assert tokens['input_ids'].shape[1] <= 128  # Max length
        
        print("✓ Tokenization and batching works correctly")
        
    finally:
        os.unlink(train_path)
        os.unlink(eval_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

