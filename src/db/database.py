"""
Database configuration and connection management.

Supports PostgreSQL (production) with SQLite fallback (development).
"""

import os
from pathlib import Path
from typing import Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base


def get_database_url() -> str:
    """
    Get database URL from environment or use SQLite fallback.
    
    Returns:
        Database connection URL
    """
    postgres_url = os.getenv("POSTGRES_URL")
    
    if postgres_url:
        # PostgreSQL URL format: postgresql://user:pass@host:port/dbname
        return postgres_url
    
    # SQLite fallback for development
    db_path = Path("data/jobs.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path.absolute()}"


def create_engine_with_config() -> Engine:
    """
    Create SQLAlchemy engine with appropriate configuration.
    
    Returns:
        Configured SQLAlchemy engine
    """
    database_url = get_database_url()
    
    if database_url.startswith("sqlite"):
        # SQLite-specific configuration
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=os.getenv("SQL_DEBUG", "0").lower() in ("1", "true", "yes"),
        )
        
        # Enable foreign keys for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    else:
        # PostgreSQL configuration
        engine = create_engine(
            database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before using
            echo=os.getenv("SQL_DEBUG", "0").lower() in ("1", "true", "yes"),
        )
    
    return engine


# Global engine instance
_engine: Optional[Engine] = None


def get_engine() -> Engine:
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        _engine = create_engine_with_config()
    return _engine


# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def init_db():
    """
    Initialize database by creating all tables.
    
    This should be called once at application startup.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

