#!/usr/bin/env python3
"""
Test script to verify the QLoRA Domain QA project setup.

This script performs basic tests to ensure all components are working correctly
before running the full training and evaluation pipeline.
"""

import os
import sys
import json
import yaml
from pathlib import Path


def test_project_structure():
    """Test that all required directories and files exist."""
    print("Testing project structure...")
    
    required_dirs = ['data', 'src', 'src/utils', 'configs', 'reports', 'reports/figures']
    required_files = [
        'README.md', 'MODEL_CARD.md', 'LICENSE', 'requirements.txt', 
        'Makefile', '.gitignore',
        'data/train.jsonl', 'data/val.jsonl', 'data/test.jsonl',
        'configs/base.yaml', 'configs/lora_r8a16.yaml', 
        'configs/lora_r16a32.yaml', 'configs/lora_r32a64.yaml',
        'src/train_qlora.py', 'src/eval_em_f1.py', 'src/eval_latency.py',
        'src/utils/seed.py', 'src/utils/data_io.py', 
        'src/utils/metrics.py', 'src/utils/timing.py',
        'src/generate_report.py', 'reports/results.csv'
    ]
    
    missing_dirs = []
    missing_files = []
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_dirs:
        print(f"ERROR Missing directories: {missing_dirs}")
        return False
    
    if missing_files:
        print(f"ERROR Missing files: {missing_files}")
        return False
    
    print("OK Project structure is correct")
    return True


def test_data_format():
    """Test that JSONL files have the correct format."""
    print("Testing data format...")
    
    jsonl_files = ['data/train.jsonl', 'data/val.jsonl', 'data/test.jsonl']
    required_keys = ['instruction', 'output']
    
    for file_path in jsonl_files:
        if not os.path.exists(file_path):
            print(f"ERROR File {file_path} not found")
            return False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            print(f"ERROR File {file_path} is empty")
            return False
        
        for i, line in enumerate(lines):
            try:
                data = json.loads(line.strip())
                for key in required_keys:
                    if key not in data:
                        print(f"ERROR Missing key '{key}' in {file_path} line {i+1}")
                        return False
            except json.JSONDecodeError as e:
                print(f"ERROR JSON decode error in {file_path} line {i+1}: {e}")
                return False
    
    print("OK Data format is correct")
    return True


def test_config_files():
    """Test that YAML configuration files are valid."""
    print("Testing configuration files...")
    
    config_files = [
        'configs/base.yaml', 'configs/lora_r8a16.yaml',
        'configs/lora_r16a32.yaml', 'configs/lora_r32a64.yaml'
    ]
    
    for config_path in config_files:
        if not os.path.exists(config_path):
            print(f"ERROR Config file {config_path} not found")
            return False
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if not config:
                print(f"ERROR Config file {config_path} is empty")
                return False
                
        except yaml.YAMLError as e:
            print(f"ERROR YAML error in {config_path}: {e}")
            return False
    
    print("OK Configuration files are valid")
    return True


def test_imports():
    """Test that Python modules can be imported."""
    print("Testing Python imports...")
    
    # Add src to path
    sys.path.insert(0, 'src')
    
    try:
        from utils.seed import set_seed
        from utils.data_io import load_jsonl, build_hf_dataset
        from utils.metrics import exact_match, f1_score_tokens
        from utils.timing import Timer, compute_percentiles
        print("OK Utility modules import successfully")
    except ImportError as e:
        print(f"ERROR Import error: {e}")
        return False
    
    # Test basic functionality
    try:
        set_seed(42)
        print("OK Seed setting works")
    except Exception as e:
        print(f"ERROR Seed setting error: {e}")
        return False
    
    try:
        data = load_jsonl('data/val.jsonl')
        print(f"OK Data loading works ({len(data)} samples)")
    except Exception as e:
        print(f"ERROR Data loading error: {e}")
        return False
    
    try:
        em = exact_match("test", "test")
        f1 = f1_score_tokens("test", "test")
        print(f"OK Metrics computation works (EM: {em}, F1: {f1})")
    except Exception as e:
        print(f"ERROR Metrics computation error: {e}")
        return False
    
    return True


def test_requirements():
    """Test that required packages can be imported."""
    print("Testing required packages...")
    
    required_packages = [
        'torch', 'transformers', 'peft', 'trl', 'datasets', 
        'bitsandbytes', 'numpy', 'pandas', 'matplotlib', 'yaml'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'yaml':
                import yaml
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"ERROR Missing packages: {missing_packages}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("OK All required packages are available")
    return True


def test_makefile():
    """Test that Makefile commands are valid."""
    print("Testing Makefile...")
    
    if not os.path.exists('Makefile'):
        print("ERROR Makefile not found")
        return False
    
    with open('Makefile', 'r') as f:
        content = f.read()
    
    required_targets = ['setup', 'train-r16', 'train-r8', 'train-r32', 
                       'eval-base', 'eval-r16', 'eval-r8', 'eval-r32', 
                       'plots', 'report', 'clean']
    
    missing_targets = []
    for target in required_targets:
        if f"{target}:" not in content:
            missing_targets.append(target)
    
    if missing_targets:
        print(f"ERROR Missing Makefile targets: {missing_targets}")
        return False
    
    print("OK Makefile is complete")
    return True


def main():
    """Run all tests."""
    print("Running QLoRA Domain QA Project Tests")
    print("=" * 50)
    
    tests = [
        test_project_structure,
        test_data_format,
        test_config_files,
        test_imports,
        test_requirements,
        test_makefile
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"ERROR Test {test.__name__} failed with error: {e}")
            print()
    
    print("=" * 50)
    print(f"Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("All tests passed! The project is ready to use.")
        print("\nNext steps:")
        print("1. Activate virtual environment: .venv\\Scripts\\activate")
        print("2. Run quick test: make quick-test")
        print("3. Or run full pipeline: make full-pipeline")
    else:
        print("Some tests failed. Please fix the issues before proceeding.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
