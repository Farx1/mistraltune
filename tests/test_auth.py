"""
Tests for authentication functionality.
"""

import pytest
import time
from src.auth.password import hash_password, verify_password
from src.auth.jwt import create_access_token, verify_token
from src.db.models import User


def test_password_hashing():
    """Test password hashing and verification."""
    password = "test_password_123"
    hashed = hash_password(password)
    
    # Hash should be different from original
    assert hashed != password
    assert len(hashed) > 0
    
    # Verification should work
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_jwt_token_creation():
    """Test JWT token creation."""
    data = {"sub": "user_123", "email": "test@example.com", "role": "member"}
    token = create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_jwt_token_verification():
    """Test JWT token verification."""
    data = {"sub": "user_123", "email": "test@example.com", "role": "member"}
    token = create_access_token(data)
    
    # Verify token
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == "user_123"
    assert payload["email"] == "test@example.com"
    assert payload["role"] == "member"


def test_jwt_token_invalid():
    """Test JWT token verification with invalid token."""
    invalid_token = "invalid.token.here"
    payload = verify_token(invalid_token)
    assert payload is None


def test_user_creation(test_db):
    """Test creating a user."""
    user = User(
        id="user_test_1",
        email="test@example.com",
        password_hash=hash_password("password123"),
        role="member",
        created_at=int(time.time()),
    )
    test_db.add(user)
    test_db.commit()
    
    # Retrieve and verify
    retrieved = test_db.query(User).filter(User.email == "test@example.com").first()
    assert retrieved is not None
    assert retrieved.email == "test@example.com"
    assert retrieved.role == "member"
    assert verify_password("password123", retrieved.password_hash) is True


def test_auth_endpoints_disabled(client, test_db):
    """Test auth endpoints when authentication is disabled."""
    # AUTH_REQUIRED is set to false in conftest
    response = client.post("/api/auth/login", params={"email": "test@example.com", "password": "pass"})
    assert response.status_code == 400
    assert "disabled" in response.json()["detail"].lower()

