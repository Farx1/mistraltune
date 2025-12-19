"""
FastAPI middleware for correlation IDs and request logging.
"""

import uuid
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

import logging

logger = logging.getLogger(__name__)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation IDs to requests."""
    
    async def dispatch(self, request: Request, call_next):
        # Generate or get correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        
        # Add to request state
        request.state.correlation_id = correlation_id
        
        # Add correlation ID to logger context
        import logging
        old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.correlation_id = correlation_id
            return record
        
        logging.setLogRecordFactory(record_factory)
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": process_time,
            }
        )
        
        return response

