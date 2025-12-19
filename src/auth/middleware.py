"""
FastAPI authentication middleware and dependencies.
"""

import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import User
from auth.jwt import verify_token

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Check if auth is required
    auth_required = os.getenv("AUTH_REQUIRED", "false").lower() in ("true", "1", "yes")
    if not auth_required:
        # Return a default anonymous user or None
        # For now, raise error if auth is disabled but token provided
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is disabled",
        )
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


def require_auth(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to require authentication.
    
    Returns:
        Current user
    """
    return current_user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to require admin role.
    
    Returns:
        Current user (admin)
        
    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user

