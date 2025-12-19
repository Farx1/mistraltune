"""
Password hashing utilities for MistralTune.
"""

import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password as string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        password: Plain text password
        hashed: Hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

