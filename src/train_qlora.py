#!/usr/bin/env python3
"""
QLoRA Training Script for Mistral-7B-Instruct

This script performs QLoRA fine-tuning on Mistral-7B-Instruct for QA tasks.
Uses TRL and PEFT to simplify the process.

Usage:
    python src/train_qlora.py --config configs/base.yaml --lora configs/lora_r16a32.yaml

Example:
    python src/train_qlora.py --config configs/base.yaml --lora configs/lora_r16a32.yaml
"""

import argparse
import yaml
import os
import time
import sys
from pathlib import Path
from typing import Dict, Any

import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    BitsAndBytesConfig,
    TrainingArguments
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer
from datasets import DatasetDict

# Import our utilities
from utils.seed import set_seed
from utils.data_io import build_hf_dataset
from utils.timing import Timer, get_max_gpu_memory


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def create_bnb_config(config: Dict[str, Any]) -> BitsAndBytesConfig:
    """Create BitsAndBytes configuration for 4-bit quantization."""
    return BitsAndBytesConfig(
        load_in_4bit=config.get('bnb_4bit', True),
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16 if config.get('fp16', True) else torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )


def create_lora_config(lora_config: Dict[str, Any]) -> LoraConfig:
    """Create LoRA configuration."""
    return LoraConfig(
        r=lora_config['lora_r'],
        lora_alpha=lora_config['lora_alpha'],
        target_modules=lora_config.get('lora_target_modules', 
            ["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]),
        lora_dropout=lora_config.get('lora_dropout', 0.05),
        bias="none",
        task_type="CAUSAL_LM",
    )


def validate_dataset_files(train_file: str, eval_file: str) -> None:
    """Validate that dataset files exist and are readable."""
    if not os.path.exists(train_file):
        raise FileNotFoundError(f"Training file not found: {train_file}")
    if not os.path.exists(eval_file):
        raise FileNotFoundError(f"Evaluation file not found: {eval_file}")
    
    # Try to load a sample to check format
    try:
        from utils.data_io import load_jsonl
        train_data = load_jsonl(train_file)
        if len(train_data) == 0:
            raise ValueError(f"Training file is empty: {train_file}")
        # Check required fields
        required_fields = {'instruction', 'output'}
        missing = required_fields - set(train_data[0].keys())
        if missing:
            raise ValueError(f"Missing required fields in dataset: {missing}")
    except Exception as e:
        raise ValueError(f"Error validating training file: {e}")


def main():
    parser = argparse.ArgumentParser(description="QLoRA Training Script")
    parser.add_argument("--config", required=True, help="Path to base config YAML file")
    parser.add_argument("--lora", required=True, help="Path to LoRA config YAML file")
    parser.add_argument("--output_dir", help="Override output directory")
    parser.add_argument("--run_id", help="Run ID for tracking")
    
    args = parser.parse_args()
    
    try:
        # Load configurations
        base_config = load_config(args.config)
        lora_config = load_config(args.lora)
        
        # Validate dataset files
        validate_dataset_files(base_config['train_file'], base_config['eval_file'])
        
        # Set seed for reproducibility
        seed = base_config.get('seed', 42)
        set_seed(seed)
        
        # Override output directory if provided
        if args.output_dir:
            base_config['output_dir'] = args.output_dir
        elif args.run_id:
            # Create a specific folder for this run
            base_config['output_dir'] = f"outputs/mistral7b_qlora_{args.run_id}"
        else:
            # Default to outputs directory
            base_config['output_dir'] = base_config.get('output_dir', 'outputs/default_run')
        
        # Create output directory
        os.makedirs(base_config['output_dir'], exist_ok=True)
        
        # Save used configs for reproducibility
        config_save_path = os.path.join(base_config['output_dir'], 'config_used.yaml')
        with open(config_save_path, 'w') as f:
            yaml.dump({'base': base_config, 'lora': lora_config}, f, default_flow_style=False)
        
        # Set cache directory (use default if not specified)
        cache_dir = base_config.get('cache_dir', os.path.expanduser('~/.cache/huggingface'))
        os.makedirs(cache_dir, exist_ok=True)
        
        print("="*60)
        print("QLoRA Training Starting...")
        print("="*60)
        print(f"Base model: {base_config['base_model']}")
        print(f"Output directory: {base_config['output_dir']}")
        print(f"Hugging Face cache: {cache_dir}")
        print(f"LoRA r={lora_config['lora_r']}, alpha={lora_config['lora_alpha']}")
        print(f"Seed: {seed}")
        print("="*60)
        
        # Check GPU availability
        use_cuda = torch.cuda.is_available()
        if not use_cuda:
            print("WARNING: No GPU detected. Training will be very slow on CPU.")
            print("Consider using a GPU-enabled environment for training.")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                print("Training cancelled.")
                sys.exit(1)
        else:
            print(f"GPU detected: {torch.cuda.get_device_name(0)}")
            print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        
        # Load tokenizer
        print("\nLoading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            base_config['base_model'],
            cache_dir=cache_dir
        )
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"
        
        # Load model with or without quantization based on GPU availability
        if use_cuda and base_config.get('bnb_4bit', True):
            print("Loading model with 4-bit quantization (GPU detected)...")
            bnb_config = create_bnb_config(base_config)
            
            model = AutoModelForCausalLM.from_pretrained(
                base_config['base_model'],
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
                cache_dir=cache_dir,
            )
            
            # Prepare model for k-bit training
            model = prepare_model_for_kbit_training(model)
        else:
            if not use_cuda:
                print("WARNING: Loading model without quantization (CPU only).")
                print("This will require significant RAM (~14GB for the model alone).")
            else:
                print("Loading model without quantization (quantization disabled in config)...")
            
            # Load model without quantization
            model = AutoModelForCausalLM.from_pretrained(
                base_config['base_model'],
                torch_dtype=torch.float16 if base_config.get('fp16', True) else torch.float32,
                device_map="auto" if use_cuda else None,
                trust_remote_code=True,
                cache_dir=cache_dir,
            )
            
            if not use_cuda:
                model = model.to('cpu')
        
        # Apply LoRA
        print("Applying LoRA configuration...")
        peft_config = create_lora_config(lora_config)
        model = get_peft_model(model, peft_config)
        
        # Display trainable parameters
        model.print_trainable_parameters()
        
        # Load dataset
        print("\nLoading dataset...")
        dataset = build_hf_dataset(
            base_config['train_file'], 
            base_config['eval_file']
        )
        
        print(f"Training samples: {len(dataset['train'])}")
        print(f"Validation samples: {len(dataset['validation'])}")
        
        if len(dataset['train']) == 0:
            raise ValueError("Training dataset is empty!")
        if len(dataset['validation']) == 0:
            print("WARNING: Validation dataset is empty!")
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=base_config['output_dir'],
            per_device_train_batch_size=base_config['per_device_train_batch_size'],
            gradient_accumulation_steps=base_config['gradient_accumulation_steps'],
            learning_rate=base_config['learning_rate'],
            num_train_epochs=base_config['num_train_epochs'],
            logging_steps=base_config['logging_steps'],
            eval_steps=base_config['eval_steps'],
            save_steps=base_config['save_steps'],
            evaluation_strategy="steps",
            save_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            fp16=base_config.get('fp16', True),
            bf16=base_config.get('bf16', False),
            report_to=base_config.get('report_to', 'none'),
            remove_unused_columns=False,
            dataloader_pin_memory=False,
        )
        
        # Create trainer
        trainer = SFTTrainer(
            model=model,
            args=training_args,
            train_dataset=dataset['train'],
            eval_dataset=dataset['validation'],
            tokenizer=tokenizer,
            dataset_text_field="text",
            max_seq_length=base_config['max_seq_length'],
            packing=base_config.get('packing', True),
        )
        
        # Start training
        print("\n" + "="*60)
        print("Starting training...")
        print("="*60)
        start_time = time.time()
        
        with Timer() as timer:
            trainer.train()
        
        training_time = timer.elapsed
        
        # Save model
        print("\nSaving model...")
        trainer.save_model()
        tokenizer.save_pretrained(base_config['output_dir'])
        
        # Get max GPU memory usage
        peak_memory = get_max_gpu_memory()
        
        # Display training summary
        print("\n" + "="*60)
        print("TRAINING SUMMARY")
        print("="*60)
        print(f"Training time: {training_time:.2f} seconds ({training_time/60:.2f} minutes)")
        print(f"Peak GPU memory: {peak_memory:.2f} GB" if peak_memory else "Peak GPU memory: N/A")
        print(f"Model saved to: {base_config['output_dir']}")
        print(f"LoRA config: r={lora_config['lora_r']}, alpha={lora_config['lora_alpha']}")
        print("="*60)
        
        # Save training metadata
        metadata = {
            'base_model': base_config['base_model'],
            'lora_r': lora_config['lora_r'],
            'lora_alpha': lora_config['lora_alpha'],
            'lora_dropout': lora_config.get('lora_dropout', 0.05),
            'learning_rate': base_config['learning_rate'],
            'num_epochs': base_config['num_train_epochs'],
            'batch_size': base_config['per_device_train_batch_size'],
            'gradient_accumulation_steps': base_config['gradient_accumulation_steps'],
            'max_seq_length': base_config['max_seq_length'],
            'training_time_seconds': training_time,
            'peak_gpu_memory_gb': peak_memory,
            'train_samples': len(dataset['train']),
            'eval_samples': len(dataset['validation']),
            'seed': seed,
        }
        
        metadata_path = os.path.join(base_config['output_dir'], 'training_metadata.yaml')
        with open(metadata_path, 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False)
        
        print(f"\nTraining metadata saved to: {metadata_path}")
        print(f"Configuration saved to: {config_save_path}")
        print("\nTraining completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: Training failed with error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
