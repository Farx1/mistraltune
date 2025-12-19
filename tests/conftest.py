"""
Pytest configuration and fixtures for MistralTune tests.
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Set test environment variables
os.environ["DEMO_MODE"] = "1"
os.environ["AUTH_REQUIRED"] = "false"
os.environ["SQL_DEBUG"] = "0"

# Import after setting env vars
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.models import Base
from src.db.database import get_db
from src.api.main import app
from fastapi.testclient import TestClient


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """Create a temporary SQLite database for testing."""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    
    # Create engine and session
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create a shared session that will be reused
    shared_db = TestingSessionLocal()
    
    # Override get_db dependency to return the shared session
    def override_get_db():
        yield shared_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        yield shared_db
    finally:
        shared_db.close()
        # Close all connections
        engine.dispose()
        app.dependency_overrides.clear()
        # Clean up - retry on Windows
        import time
        for _ in range(5):
            try:
                if os.path.exists(db_path):
                    os.unlink(db_path)
                break
            except (PermissionError, OSError):
                time.sleep(0.1)


@pytest.fixture(scope="function")
def client(test_db: Session) -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(scope="function")
def temp_data_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def sample_jsonl_file(temp_data_dir: Path) -> Path:
    """Create a sample JSONL file for testing."""
    file_path = temp_data_dir / "test_dataset.jsonl"
    sample_data = [
        '{"messages": [{"role": "user", "content": "What is AI?"}, {"role": "assistant", "content": "AI is artificial intelligence."}]}\n',
        '{"messages": [{"role": "user", "content": "What is ML?"}, {"role": "assistant", "content": "ML is machine learning."}]}\n',
        '{"messages": [{"role": "user", "content": "What is NLP?"}, {"role": "assistant", "content": "NLP is natural language processing."}]}\n',
    ]
    with open(file_path, "w") as f:
        f.writelines(sample_data)
    return file_path
