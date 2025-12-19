#!/usr/bin/env python3
"""
Latency Evaluation Script for Mistral-7B-Instruct Domain QA

This script measures inference latency (p50/p95) for model evaluation.
It supports both base models and fine-tuned LoRA adapters.

Usage:
    python src/eval_latency.py --model_path mistralai/Mistral-7B-Instruct-v0.3 --eval_file data/val.jsonl

Example:
    python src/eval_latency.py --model_path runs/mistral7b_qlora_domainqa_r16a32 --eval_file data/val.jsonl
"""

import argparse
import os
import csv
import time
from pathlib import Path
from typing import List, Dict, Any

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

# Import our utilities
from utils.seed import set_seed
from utils.data_io import load_eval_data
from utils.timing import measure_latency


def load_model_and_tokenizer(model_path: str, is_adapter: bool = False) -> tuple:
    """
    Load model and tokenizer, handling both base models and LoRA adapters.
    
    Args:
        model_path: Path to model or adapter
        is_adapter: Whether the path points to a LoRA adapter
        
    Returns:
        Tuple of (model, tokenizer)
    """
    print(f"Loading {'adapter' if is_adapter else 'model'} from: {model_path}")
    
    # Define Hugging Face cache on E:\
    cache_dir = 'E:/.cache/huggingface'
    os.makedirs(cache_dir, exist_ok=True)
    
    # Load tokenizer
    if is_adapter:
        # For adapters, we need to load the base model's tokenizer
        tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.3", cache_dir=cache_dir)
    else:
        tokenizer = AutoTokenizer.from_pretrained(model_path, cache_dir=cache_dir)
    
    tokenizer.pad_token = tokenizer.eos_token
    
    # Load model
    if is_adapter:
        # Load base model first
        base_model = AutoModelForCausalLM.from_pretrained(
            "mistralai/Mistral-7B-Instruct-v0.3",
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
            cache_dir=cache_dir,
        )
        
        # Load adapter
        model = PeftModel.from_pretrained(base_model, model_path)
    else:
        # Load base model with quantization for efficiency
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            cache_dir=cache_dir,
        )
    
    return model, tokenizer


def update_csv_with_latency(model_path: str, is_adapter: bool, latency_p50: float, 
                           latency_p95: float) -> None:
    """
    Update CSV file with latency measurements.
    
    Args:
        model_path: Path to the model/adapter
        is_adapter: Whether it's an adapter
        latency_p50: 50th percentile latency
        latency_p95: 95th percentile latency
    """
    csv_path = "reports/results.csv"
    
    if not os.path.exists(csv_path):
        print(f"CSV file {csv_path} not found. Run eval_em_f1.py first.")
        return
    
    # Read existing CSV
    rows = []
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    # Find matching row and update latency
    run_id = os.path.basename(model_path) if is_adapter else "baseline"
    
    updated = False
    for i, row in enumerate(rows):
        if i == 0:  # Skip header
            continue
        if len(row) > 0 and row[0] == run_id:
            # Update latency columns (indices 11 and 12)
            if len(row) > 11:
                row[11] = f"{latency_p50:.3f}"
            if len(row) > 12:
                row[12] = f"{latency_p95:.3f}"
            updated = True
            break
    
    if not updated:
        print(f"Could not find matching row for run_id: {run_id}")
        return
    
    # Write updated CSV
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    
    print(f"Updated latency measurements in {csv_path}")


def main():
    parser = argparse.ArgumentParser(description="Latency Evaluation Script")
    parser.add_argument("--model_path", required=True, help="Path to model or adapter")
    parser.add_argument("--eval_file", required=True, help="Path to evaluation JSONL file")
    parser.add_argument("--max_new_tokens", type=int, default=128, help="Maximum new tokens to generate")
    parser.add_argument("--is_adapter", action="store_true", help="Whether model_path is a LoRA adapter")
    parser.add_argument("--num_runs", type=int, default=50, help="Number of runs for latency measurement")
    parser.add_argument("--update_csv", action="store_true", help="Update CSV with latency measurements")
    
    args = parser.parse_args()
    
    # Set seed for reproducibility
    set_seed(42)
    
    # Load evaluation data
    eval_data = load_eval_data(args.eval_file)
    
    # Extract prompts for latency measurement
    prompts = []
    for item in eval_data:
        if item.get('input'):
            prompt = f"{item['instruction']}\n{item['input']}"
        else:
            prompt = item['instruction']
        prompts.append(prompt)
    
    # Load model and tokenizer
    model, tokenizer = load_model_and_tokenizer(args.model_path, args.is_adapter)
    
    # Measure latency
    print(f"Measuring latency with {args.num_runs} runs...")
    latency_p50, latency_p95 = measure_latency(
        model, tokenizer, prompts, args.max_new_tokens, args.num_runs
    )
    
    # Print results
    print("\n" + "="*50)
    print("LATENCY RESULTS")
    print("="*50)
    print(f"Latency p50: {latency_p50:.3f} seconds")
    print(f"Latency p95: {latency_p95:.3f} seconds")
    print(f"Number of runs: {args.num_runs}")
    print("="*50)
    
    # Update CSV if requested
    if args.update_csv:
        update_csv_with_latency(
            args.model_path, 
            args.is_adapter, 
            latency_p50, 
            latency_p95
        )


if __name__ == "__main__":
    main()
