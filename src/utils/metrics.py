"""
Metrics utilities for evaluating model performance.

This module provides functions to compute Exact Match (EM) and F1 scores
for question-answering tasks.
"""

import re
from typing import List, Tuple
from sklearn.metrics import f1_score
import numpy as np


def normalize_text(text: str) -> str:
    """
    Normalize text for evaluation by removing punctuation and extra whitespace.
    
    Args:
        text: Input text to normalize
        
    Returns:
        Normalized text string
        
    Example:
        >>> normalized = normalize_text("Hello, world!  How are you?")
        >>> print(normalized)  # "hello world how are you"
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove punctuation (keep alphanumeric and spaces)
    text = re.sub(r'[^\w\s]', '', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def exact_match(prediction: str, ground_truth: str) -> int:
    """
    Compute exact match score (1 if exact match, 0 otherwise).
    
    Args:
        prediction: Model prediction
        ground_truth: Ground truth answer
        
    Returns:
        1 if exact match, 0 otherwise
        
    Example:
        >>> em_score = exact_match("AI is artificial intelligence", "AI is artificial intelligence")
        >>> print(em_score)  # 1
    """
    pred_norm = normalize_text(prediction)
    gt_norm = normalize_text(ground_truth)
    
    return 1 if pred_norm == gt_norm else 0


def f1_score_tokens(prediction: str, ground_truth: str) -> float:
    """
    Compute F1 score based on token overlap.
    
    Args:
        prediction: Model prediction
        ground_truth: Ground truth answer
        
    Returns:
        F1 score between 0 and 1
        
    Example:
        >>> f1 = f1_score_tokens("AI is artificial intelligence", "AI is machine learning")
        >>> print(f1)  # 0.5 (50% overlap)
    """
    pred_tokens = set(normalize_text(prediction).split())
    gt_tokens = set(normalize_text(ground_truth).split())
    
    if len(pred_tokens) == 0 and len(gt_tokens) == 0:
        return 1.0
    
    if len(pred_tokens) == 0 or len(gt_tokens) == 0:
        return 0.0
    
    # Calculate precision and recall
    intersection = pred_tokens.intersection(gt_tokens)
    
    precision = len(intersection) / len(pred_tokens)
    recall = len(intersection) / len(gt_tokens)
    
    # Calculate F1 score
    if precision + recall == 0:
        return 0.0
    
    f1 = 2 * (precision * recall) / (precision + recall)
    return f1


def compute_metrics(predictions: List[str], ground_truths: List[str]) -> Tuple[float, float]:
    """
    Compute EM and F1 scores for a list of predictions.
    
    Args:
        predictions: List of model predictions
        ground_truths: List of ground truth answers
        
    Returns:
        Tuple of (EM_score, F1_score)
        
    Example:
        >>> preds = ["AI is artificial intelligence", "ML is machine learning"]
        >>> truths = ["AI is artificial intelligence", "ML is machine learning"]
        >>> em, f1 = compute_metrics(preds, truths)
        >>> print(f"EM: {em}, F1: {f1}")
    """
    if len(predictions) != len(ground_truths):
        raise ValueError("Predictions and ground truths must have the same length")
    
    em_scores = []
    f1_scores = []
    
    for pred, gt in zip(predictions, ground_truths):
        em_scores.append(exact_match(pred, gt))
        f1_scores.append(f1_score_tokens(pred, gt))
    
    avg_em = np.mean(em_scores)
    avg_f1 = np.mean(f1_scores)
    
    return avg_em, avg_f1


def print_metrics(em_score: float, f1_score: float, num_samples: int) -> None:
    """
    Print formatted metrics.
    
    Args:
        em_score: Exact Match score
        f1_score: F1 score
        num_samples: Number of samples evaluated
        
    Example:
        >>> print_metrics(0.8, 0.85, 100)
        # Output: Samples: 100, EM: 0.800, F1: 0.850
    """
    print(f"Samples: {num_samples}, EM: {em_score:.3f}, F1: {f1_score:.3f}")
