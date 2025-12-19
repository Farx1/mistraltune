"""
JWT token utilities for MistralTune.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

try:
    from jose import jwt, JWTError
    JOSE_AVAILABLE = True
except ImportError:
    JOSE_AVAILABLE = False
    jwt = None
    JWTError = Exception


# JWT configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in token
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token
    """
    if not JOSE_AVAILABLE:
        raise ImportError("python-jose is required for JWT support")
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload or None if invalid
    """
    if not JOSE_AVAILABLE:
        return None
    
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

