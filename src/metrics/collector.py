"""
Metrics collection for MistralTune.

Tracks job durations, success/failure rates, API latency, etc.
"""

import time
from typing import Dict, Any, Optional
from collections import defaultdict
from threading import Lock

from db.models import Job


class MetricsCollector:
    """Simple in-memory metrics collector."""
    
    def __init__(self):
        self._lock = Lock()
        self._job_durations: Dict[str, float] = {}
        self._job_counts: Dict[str, int] = defaultdict(int)
        self._api_latencies: list = []
        self._active_jobs = 0
    
    def record_job_completion(self, job: Job):
        """Record a completed job."""
        with self._lock:
            if job.started_at and job.finished_at:
                duration = job.finished_at - job.started_at
                self._job_durations[job.job_type] = duration
                self._job_counts[f"{job.job_type}_{job.status}"] += 1
    
    def record_api_latency(self, latency_ms: float):
        """Record API request latency."""
        with self._lock:
            self._api_latencies.append(latency_ms)
            # Keep only last 1000 latencies
            if len(self._api_latencies) > 1000:
                self._api_latencies = self._api_latencies[-1000:]
    
    def set_active_jobs(self, count: int):
        """Set active jobs count."""
        with self._lock:
            self._active_jobs = count
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        with self._lock:
            # Calculate API latency percentiles
            latencies = sorted(self._api_latencies)
            p50 = latencies[len(latencies) // 2] if latencies else 0
            p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0
            p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0
            
            return {
                "jobs": {
                    "active": self._active_jobs,
                    "durations": dict(self._job_durations),
                    "counts": dict(self._job_counts),
                },
                "api": {
                    "latency_ms": {
                        "p50": p50,
                        "p95": p95,
                        "p99": p99,
                        "mean": sum(latencies) / len(latencies) if latencies else 0,
                    },
                    "request_count": len(self._api_latencies),
                },
            }


# Global metrics collector
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

