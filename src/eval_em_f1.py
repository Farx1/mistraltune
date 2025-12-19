#!/usr/bin/env python3
"""
EM/F1 Evaluation Script for Mistral-7B-Instruct Domain QA

This script evaluates model performance with EM and F1 metrics.
Handles both base models and fine-tuned LoRA adapters.

Usage:
    python src/eval_em_f1.py --model_path mistralai/Mistral-7B-Instruct-v0.3 --eval_file data/val.jsonl

Example:
    python src/eval_em_f1.py --model_path outputs/demo_run --eval_file data/val.jsonl --is_adapter
"""

import argparse
import os
import json
import csv
import time
import sys
from pathlib import Path
from typing import List, Dict, Any

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

# Import our utilities
from utils.seed import set_seed
from utils.data_io import load_eval_data
from utils.metrics import compute_metrics, print_metrics


def get_base_model_from_metadata(adapter_path: str) -> str:
    """
    Try to get base model name from training metadata.
    
    Args:
        adapter_path: Path to adapter directory
        
    Returns:
        Base model name or default
    """
    metadata_path = os.path.join(adapter_path, 'training_metadata.yaml')
    config_path = os.path.join(adapter_path, 'config_used.yaml')
    
    # Try to load from metadata
    for path in [metadata_path, config_path]:
        if os.path.exists(path):
            try:
                import yaml
                with open(path, 'r') as f:
                    data = yaml.safe_load(f)
                    # Check different possible structures
                    if isinstance(data, dict):
                        if 'base_model' in data:
                            return data['base_model']
                        if 'base' in data and isinstance(data['base'], dict):
                            if 'base_model' in data['base']:
                                return data['base']['base_model']
            except Exception:
                pass
    
    # Default fallback
    return "mistralai/Mistral-7B-Instruct-v0.3"


def load_model_and_tokenizer(model_path: str, is_adapter: bool = False, base_model: str = None) -> tuple:
    """
    Load model and tokenizer, handles both base models and LoRA adapters.
    
    Args:
        model_path: Path to model or adapter
        is_adapter: Whether the path points to a LoRA adapter
        base_model: Base model name/path (auto-detected if not provided for adapters)
        
    Returns:
        Tuple of (model, tokenizer)
    """
    print(f"Loading {'adapter' if is_adapter else 'model'} from: {model_path}")
    
    if not os.path.exists(model_path) and not is_adapter:
        raise FileNotFoundError(f"Model path not found: {model_path}")
    
    # Set Hugging Face cache directory
    cache_dir = os.path.expanduser('~/.cache/huggingface')
    os.makedirs(cache_dir, exist_ok=True)
    
    # Load tokenizer
    base_model_name = None
    if is_adapter:
        # For adapters, try to detect base model from metadata
        if base_model is None:
            base_model_name = get_base_model_from_metadata(model_path)
            print(f"Detected base model from metadata: {base_model_name}")
        else:
            base_model_name = base_model
            print(f"Using provided base model: {base_model_name}")
        
        tokenizer = AutoTokenizer.from_pretrained(base_model_name, cache_dir=cache_dir)
    else:
        tokenizer = AutoTokenizer.from_pretrained(model_path, cache_dir=cache_dir)
    
    tokenizer.pad_token = tokenizer.eos_token
    
    # Check GPU availability
    use_cuda = torch.cuda.is_available()
    if not use_cuda:
        print("WARNING: No GPU detected. Evaluation will be slow on CPU.")
    
    # Load model
    if is_adapter:
        # base_model_name already determined above
        if base_model_name is None:
            base_model_name = get_base_model_from_metadata(model_path)
        
        # Load base model first
        print(f"Loading base model: {base_model_name}")
        base_model_obj = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float16 if use_cuda else torch.float32,
            device_map="auto" if use_cuda else None,
            trust_remote_code=True,
            cache_dir=cache_dir,
        )
        
        # Load adapter
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Adapter path not found: {model_path}")
        model = PeftModel.from_pretrained(base_model_obj, model_path)
    else:
        # Load base model with quantization for efficiency
        if use_cuda:
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
        else:
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float32,
                device_map=None,
                trust_remote_code=True,
                cache_dir=cache_dir,
            )
            model = model.to('cpu')
    
    return model, tokenizer


def generate_response(model, tokenizer, instruction: str, input_text: str = "", 
                     max_new_tokens: int = 128) -> str:
    """
    Generate response for a given instruction.
    
    Args:
        model: The model to use for generation
        tokenizer: The tokenizer
        instruction: The instruction/question
        input_text: Additional input context
        max_new_tokens: Maximum number of new tokens to generate
        
    Returns:
        Generated response text
    """
    # Format prompt
    if input_text:
        prompt = f"{instruction}\n{input_text}"
    else:
        prompt = instruction
    
    formatted_prompt = f"<s>[INST] {prompt} [/INST]"
    
    # Tokenize
    inputs = tokenizer(formatted_prompt, return_tensors="pt")
    if hasattr(model, 'device'):
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
    elif use_cuda := torch.cuda.is_available():
        inputs = {k: v.cuda() for k, v in inputs.items()}
    
    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,  # Greedy decoding for consistent results
            temperature=0.7,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    
    # Decode response
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract only the generated part (after [/INST])
    if "[/INST]" in response:
        response = response.split("[/INST]")[1].strip()
    
    return response


def evaluate_model(model, tokenizer, eval_data: List[Dict[str, Any]], 
                  max_new_tokens: int = 128) -> tuple:
    """
    Evaluate model on the evaluation dataset.
    
    Args:
        model: The model to evaluate
        tokenizer: The tokenizer
        eval_data: List of evaluation examples
        max_new_tokens: Maximum number of new tokens to generate
        
    Returns:
        Tuple of (predictions, ground_truths, em_score, f1_score, avg_length)
    """
    predictions = []
    ground_truths = []
    lengths = []
    
    print(f"Evaluating on {len(eval_data)} examples...")
    
    for i, item in enumerate(eval_data):
        print(f"Processing example {i+1}/{len(eval_data)}", end="\r")
        
        # Generate prediction
        try:
        prediction = generate_response(
            model, tokenizer, 
            item['instruction'], 
            item.get('input', ''),
            max_new_tokens
        )
        predictions.append(prediction)
        ground_truths.append(item['output'])
            lengths.append(len(prediction))
        except Exception as e:
            print(f"\nError generating response for example {i+1}: {e}")
            predictions.append("")
            ground_truths.append(item['output'])
            lengths.append(0)
    
    print()  # New line after progress
    
    # Compute metrics
    em_score, f1_score = compute_metrics(predictions, ground_truths)
    avg_length = sum(lengths) / len(lengths) if lengths else 0
    
    return predictions, ground_truths, em_score, f1_score, avg_length


def save_results_to_csv(model_path: str, is_adapter: bool, em_score: float, 
                       f1_score: float, avg_length: float, num_samples: int,
                       notes: str = "") -> None:
    """
    Save evaluation results to CSV file.
    
    Args:
        model_path: Path to the model/adapter
        is_adapter: Whether it's an adapter
        em_score: Exact Match score
        f1_score: F1 score
        avg_length: Average response length
        num_samples: Number of samples evaluated
        notes: Additional notes (optional)
    """
    csv_path = "reports/results.csv"
    
    # Create reports directory if it doesn't exist
    os.makedirs("reports", exist_ok=True)
    
    # Check if CSV exists to determine if we need headers
    file_exists = os.path.exists(csv_path)
    
    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f)
        
        # Write headers if file is new
        if not file_exists:
            writer.writerow([
                'run_id', 'base_model', 'adapter', 'timestamp', 'epochs', 'lr',
                'lora_r', 'lora_alpha', 'seq_len', 'em', 'f1', 'avg_length',
                'num_samples', 'notes'
            ])
        
        # Extract run info from model path
        run_id = os.path.basename(model_path) if is_adapter else "baseline"
        base_model = "mistralai/Mistral-7B-Instruct-v0.3"
        adapter = model_path if is_adapter else ""
        
        # Extract LoRA parameters if it's an adapter
        lora_r = ""
        lora_alpha = ""
        if is_adapter:
            if "r16a32" in model_path or "r16" in model_path:
            lora_r = "16"
            lora_alpha = "32"
            elif "r8a16" in model_path or "r8" in model_path:
            lora_r = "8"
            lora_alpha = "16"
            elif "r32a64" in model_path or "r32" in model_path:
            lora_r = "32"
            lora_alpha = "64"
        
        writer.writerow([
            run_id,
            base_model,
            adapter,
            time.strftime("%Y-%m-%d %H:%M:%S"),
            "",  # epochs
            "",  # lr
            lora_r,
            lora_alpha,
            "",  # seq_len
            f"{em_score:.4f}",
            f"{f1_score:.4f}",
            f"{avg_length:.2f}",
            num_samples,
            notes
        ])


def save_metrics_json(model_path: str, em_score: float, f1_score: float, 
                     avg_length: float, num_samples: int, predictions: List[str],
                     ground_truths: List[str], output_dir: str = None) -> None:
    """Save detailed metrics to JSON file."""
    if output_dir is None:
        output_dir = os.path.dirname(model_path) if os.path.isdir(model_path) else "reports"
    
    os.makedirs(output_dir, exist_ok=True)
    
    metrics = {
        'em_score': em_score,
        'f1_score': f1_score,
        'avg_length': avg_length,
        'num_samples': num_samples,
        'examples': [
            {
                'prediction': pred,
                'ground_truth': gt
            }
            for pred, gt in zip(predictions[:5], ground_truths[:5])  # Save first 5 examples
        ]
    }
    
    metrics_path = os.path.join(output_dir, 'metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    
    print(f"Detailed metrics saved to: {metrics_path}")


def main():
    parser = argparse.ArgumentParser(description="EM/F1 Evaluation Script")
    parser.add_argument("--model_path", required=True, help="Path to model or adapter")
    parser.add_argument("--eval_file", required=True, help="Path to evaluation JSONL file")
    parser.add_argument("--max_new_tokens", type=int, default=128, help="Maximum new tokens to generate")
    parser.add_argument("--is_adapter", action="store_true", help="Whether model_path is a LoRA adapter")
    parser.add_argument("--base_model", help="Base model name/path (auto-detected from metadata if not provided)")
    parser.add_argument("--save_results", action="store_true", help="Save results to CSV")
    parser.add_argument("--output_dir", help="Directory to save metrics JSON")
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.eval_file):
        print(f"ERROR: Evaluation file not found: {args.eval_file}", file=sys.stderr)
        sys.exit(1)
    
    # Set seed for reproducibility
    set_seed(42)
    
    # Load evaluation data
    try:
    eval_data = load_eval_data(args.eval_file)
        if len(eval_data) == 0:
            print(f"ERROR: Evaluation file is empty: {args.eval_file}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to load evaluation data: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Load model and tokenizer
    try:
        model, tokenizer = load_model_and_tokenizer(
            args.model_path, 
            args.is_adapter,
            base_model=args.base_model
        )
    except Exception as e:
        print(f"ERROR: Failed to load model: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Evaluate model
    try:
        predictions, ground_truths, em_score, f1_score, avg_length = evaluate_model(
        model, tokenizer, eval_data, args.max_new_tokens
    )
    except Exception as e:
        print(f"ERROR: Evaluation failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Print results
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    print_metrics(em_score, f1_score, len(eval_data))
    print(f"Average response length: {avg_length:.2f} characters")
    print("="*60)
    
    # Print some examples
    print("\nSample predictions (first 3):")
    for i in range(min(3, len(eval_data))):
        print(f"\nExample {i+1}:")
        print(f"Instruction: {eval_data[i]['instruction']}")
        print(f"Ground Truth: {ground_truths[i]}")
        print(f"Prediction: {predictions[i]}")
    
    # Save results to CSV if requested
    if args.save_results:
        save_results_to_csv(
            args.model_path, 
            args.is_adapter, 
            em_score, 
            f1_score, 
            avg_length,
            len(eval_data)
        )
        print(f"\nResults saved to reports/results.csv")
    
    # Save detailed metrics JSON
    output_dir = args.output_dir or (args.model_path if os.path.isdir(args.model_path) else "reports")
    save_metrics_json(
        args.model_path,
        em_score,
        f1_score,
        avg_length,
        len(eval_data),
        predictions,
        ground_truths,
        output_dir
    )


if __name__ == "__main__":
    main()
