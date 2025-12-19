"""
Structured logging configuration for MistralTune.

Provides JSON-formatted logs for production and human-readable logs for development.
"""

import os
import json
import logging
import sys
from typing import Optional
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add correlation ID if present
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        
        # Add job_id if present
        if hasattr(record, "job_id"):
            log_data["job_id"] = record.job_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_logging(
    level: Optional[str] = None,
    use_json: Optional[bool] = None,
    correlation_id: Optional[str] = None,
):
    """
    Setup logging configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Whether to use JSON formatting (default: based on LOG_FORMAT env)
        correlation_id: Optional correlation ID for request tracing
    """
    # Determine log level
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    log_level = getattr(logging, level, logging.INFO)
    
    # Determine format
    if use_json is None:
        log_format = os.getenv("LOG_FORMAT", "text").lower()
        use_json = log_format == "json"
    
    # Create formatter
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Set correlation ID if provided
    if correlation_id:
        # Add correlation ID to all log records
        old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.correlation_id = correlation_id
            return record
        
        logging.setLogRecordFactory(record_factory)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

