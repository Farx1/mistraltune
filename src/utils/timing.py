"""
Timing utilities for measuring latency and performance metrics.

This module provides context managers and functions for timing operations
and computing percentile statistics.
"""

import time
import statistics
from contextlib import contextmanager
from typing import List, Tuple, Optional, Dict
import subprocess
import os
import torch


@contextmanager
def Timer():
    """
    Context manager for timing operations.
    
    Yields:
        Timer object with start_time and end_time attributes
        
    Example:
        >>> with Timer() as timer:
        ...     # Some operation
        ...     time.sleep(1)
        >>> print(f"Operation took {timer.elapsed:.2f} seconds")
    """
    timer = type('Timer', (), {})()
    timer.start_time = time.time()
    yield timer
    timer.end_time = time.time()
    timer.elapsed = timer.end_time - timer.start_time


def compute_percentiles(times: List[float], percentiles: List[int] = [50, 95]) -> Dict[int, float]:
    """
    Compute percentile statistics from a list of times.
    
    Args:
        times: List of timing measurements
        percentiles: List of percentiles to compute (default: [50, 95])
        
    Returns:
        Dictionary mapping percentile to value
        
    Example:
        >>> times = [0.1, 0.2, 0.3, 0.4, 0.5]
        >>> stats = compute_percentiles(times, [50, 95])
        >>> print(f"p50: {stats[50]:.3f}s, p95: {stats[95]:.3f}s")
    """
    if not times:
        return {p: 0.0 for p in percentiles}
    
    sorted_times = sorted(times)
    result = {}
    
    for p in percentiles:
        if p == 100:
            result[p] = max(sorted_times)
        else:
            index = (p / 100) * (len(sorted_times) - 1)
            if index.is_integer():
                result[p] = sorted_times[int(index)]
            else:
                # Linear interpolation
                lower = int(index)
                upper = lower + 1
                weight = index - lower
                result[p] = sorted_times[lower] * (1 - weight) + sorted_times[upper] * weight
    
    return result


def measure_latency(model, tokenizer, prompts: List[str], max_new_tokens: int = 128, 
                   num_runs: int = 50) -> Tuple[float, float]:
    """
    Measure latency for model inference.
    
    Args:
        model: The model to evaluate
        tokenizer: The tokenizer
        prompts: List of prompts to evaluate
        max_new_tokens: Maximum number of new tokens to generate
        num_runs: Number of runs for latency measurement
        
    Returns:
        Tuple of (p50_latency, p95_latency) in seconds
        
    Example:
        >>> p50, p95 = measure_latency(model, tokenizer, prompts, num_runs=50)
        >>> print(f"Latency p50: {p50:.3f}s, p95: {p95:.3f}s")
    """
    latencies = []
    
    # Ensure we have enough prompts
    if len(prompts) < num_runs:
        prompts = prompts * ((num_runs // len(prompts)) + 1)
    
    prompts = prompts[:num_runs]
    
    for prompt in prompts:
        # Format prompt for Mistral
        formatted_prompt = f"<s>[INST] {prompt} [/INST]"
        
        # Tokenize
        inputs = tokenizer(formatted_prompt, return_tensors="pt")
        if hasattr(model, 'device'):
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        # Time the generation
        with Timer() as timer:
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,  # Greedy decoding for consistent timing
                    pad_token_id=tokenizer.eos_token_id
                )
        
        latencies.append(timer.elapsed)
    
    # Compute percentiles
    percentiles = compute_percentiles(latencies, [50, 95])
    
    return percentiles[50], percentiles[95]


def get_gpu_memory_usage() -> Optional[float]:
    """
    Get current GPU memory usage in GB.
    
    Returns:
        GPU memory usage in GB, or None if nvidia-smi is not available
        
    Example:
        >>> memory_gb = get_gpu_memory_usage()
        >>> if memory_gb:
        ...     print(f"GPU memory usage: {memory_gb:.2f} GB")
    """
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True, check=True)
        memory_mb = float(result.stdout.strip())
        return memory_mb / 1024  # Convert to GB
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return None


def get_max_gpu_memory() -> Optional[float]:
    """
    Get maximum GPU memory usage during training.
    
    Returns:
        Maximum GPU memory usage in GB, or None if not available
        
    Example:
        >>> max_memory = get_max_gpu_memory()
        >>> if max_memory:
        ...     print(f"Peak GPU memory: {max_memory:.2f} GB")
    """
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=memory.max_used', '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True, check=True)
        memory_mb = float(result.stdout.strip())
        return memory_mb / 1024  # Convert to GB
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return None
