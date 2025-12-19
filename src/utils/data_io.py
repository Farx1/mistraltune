"""
Utilities for loading and processing JSONL datasets.

This module provides functions to load JSONL files
and convert them to HuggingFace datasets in the correct format for training.
"""

import json
from typing import List, Dict, Any
from datasets import Dataset as HFDataset, DatasetDict


def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """
    Load data from a JSONL file.
    
    Args:
        file_path: Path to the JSONL file
        
    Returns:
        List of dictionaries containing the data
        
    Example:
        >>> data = load_jsonl("data/train.jsonl")
        >>> print(f"Loaded {len(data)} examples")
    """
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def format_instruction(instruction: str, input_text: str = "", output: str = "") -> str:
    """
    Format instruction data in Mistral format.
    
    Args:
        instruction: The instruction/question
        input_text: Additional input context (optional)
        output: The expected response
        
    Returns:
        Formatted string in Mistral instruction format
        
    Example:
        >>> formatted = format_instruction("What is AI?", "", "AI is artificial intelligence")
        >>> print(formatted)
    """
    if input_text:
        prompt = f"{instruction}\n{input_text}"
    else:
        prompt = instruction
    
    formatted_text = f"<s>[INST] {prompt} [/INST] {output} </s>"
    return formatted_text


def build_hf_dataset(train_file: str, eval_file: str) -> DatasetDict:
    """
    Build a HuggingFace dataset from JSONL files.
    
    Args:
        train_file: Path to training JSONL file
        eval_file: Path to validation JSONL file
        
    Returns:
        DatasetDict containing training and validation datasets
        
    Example:
        >>> dataset = build_hf_dataset("data/train.jsonl", "data/val.jsonl")
        >>> print(f"Training: {len(dataset['train'])} examples")
        >>> print(f"Validation: {len(dataset['validation'])} examples")
    """
    # Load training data
    train_data = load_jsonl(train_file)
    train_texts = []
    
    for item in train_data:
        formatted_text = format_instruction(
            item['instruction'],
            item.get('input', ''),
            item['output']
        )
        train_texts.append({'text': formatted_text})
    
    # Load validation data
    eval_data = load_jsonl(eval_file)
    eval_texts = []
    
    for item in eval_data:
        formatted_text = format_instruction(
            item['instruction'],
            item.get('input', ''),
            item['output']
        )
        eval_texts.append({'text': formatted_text})
    
    # Create datasets
    train_dataset = Dataset.from_list(train_texts)
    eval_dataset = Dataset.from_list(eval_texts)
    
    return DatasetDict({
        'train': train_dataset,
        'validation': eval_dataset
    })


def load_eval_data(eval_file: str) -> List[Dict[str, Any]]:
    """
    Load evaluation data for inference.
    
    Args:
        eval_file: Path to evaluation JSONL file
        
    Returns:
        List of dictionaries with instruction, input, and output fields
        
    Example:
        >>> eval_data = load_eval_data("data/val.jsonl")
        >>> print(f"Loaded {len(eval_data)} evaluation examples")
    """
    return load_jsonl(eval_file)
