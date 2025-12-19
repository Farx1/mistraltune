#!/usr/bin/env python3
"""
Migration script to copy data from existing SQLite database to new schema.

This script:
1. Reads existing jobs and datasets from old SQLite schema
2. Migrates them to the new SQLAlchemy models
3. Creates initial dataset versions for existing datasets
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.database import get_engine, init_db, SessionLocal
from src.db.models import Job, Dataset, DatasetVersion
from sqlalchemy.orm import Session


def migrate_sqlite_data():
    """Migrate data from old SQLite schema to new models."""
    
    # Initialize new database
    init_db()
    
    # Connect to old SQLite database
    old_db_path = Path("data/jobs.db")
    if not old_db_path.exists():
        print("No existing SQLite database found. Skipping migration.")
        return
    
    print(f"Found existing database at {old_db_path}")
    old_conn = sqlite3.connect(old_db_path)
    old_cursor = old_conn.cursor()
    
    # Get new database session
    db: Session = SessionLocal()
    
    try:
        # Migrate datasets
        print("Migrating datasets...")
        old_cursor.execute("SELECT * FROM datasets")
        old_datasets = old_cursor.fetchall()
        old_columns = [desc[0] for desc in old_cursor.description]
        
        for row in old_datasets:
            dataset_dict = dict(zip(old_columns, row))
            
            # Check if already migrated
            existing = db.query(Dataset).filter(Dataset.id == dataset_dict["id"]).first()
            if existing:
                print(f"  Dataset {dataset_dict['id']} already exists, skipping")
                continue
            
            # Parse metadata
            metadata = {}
            if dataset_dict.get("metadata"):
                try:
                    metadata = json.loads(dataset_dict["metadata"])
                except:
                    pass
            
            # Create new dataset
            new_dataset = Dataset(
                id=dataset_dict["id"],
                filename=dataset_dict["filename"],
                file_hash=None,  # Will be computed on next upload
                size_bytes=metadata.get("size") if metadata else None,
                uploaded_at=dataset_dict["uploaded_at"],
                metadata_json=metadata,
            )
            
            db.add(new_dataset)
            
            # Create initial version
            version = DatasetVersion(
                id=f"{dataset_dict['id']}_v1",
                dataset_id=dataset_dict["id"],
                version=1,
                file_hash=None,  # Will be computed if file still exists
                created_at=dataset_dict["uploaded_at"],
            )
            db.add(version)
            
            print(f"  Migrated dataset: {dataset_dict['filename']}")
        
        # Migrate jobs
        print("Migrating jobs...")
        old_cursor.execute("SELECT * FROM jobs")
        old_jobs = old_cursor.fetchall()
        old_columns = [desc[0] for desc in old_cursor.description]
        
        for row in old_jobs:
            job_dict = dict(zip(old_columns, row))
            
            # Check if already migrated
            existing = db.query(Job).filter(Job.id == job_dict["id"]).first()
            if existing:
                print(f"  Job {job_dict['id']} already exists, skipping")
                continue
            
            # Parse config and metadata
            config = {}
            metadata = {}
            if job_dict.get("config"):
                try:
                    config = json.loads(job_dict["config"])
                except:
                    pass
            if job_dict.get("metadata"):
                try:
                    metadata = json.loads(job_dict["metadata"])
                except:
                    pass
            
            # Parse error
            error_msg = None
            if job_dict.get("error"):
                try:
                    error_data = json.loads(job_dict["error"])
                    if isinstance(error_data, dict):
                        error_msg = error_data.get("message") or str(error_data)
                    else:
                        error_msg = str(error_data)
                except:
                    error_msg = str(job_dict["error"])
            
            # Create new job
            new_job = Job(
                id=job_dict["id"],
                job_type=job_dict["job_type"],
                model=job_dict["model"],
                status=job_dict["status"],
                created_at=job_dict["created_at"],
                started_at=None,  # Not in old schema
                finished_at=None,  # Not in old schema
                progress=None,  # Not in old schema
                error_message=error_msg,
                config_json=config,
                dataset_version_id=None,  # Will need to be linked manually if needed
                model_output_ref=job_dict.get("fine_tuned_model"),
                metrics_json=metadata,
            )
            
            db.add(new_job)
            print(f"  Migrated job: {job_dict['id']} ({job_dict['status']})")
        
        # Commit all changes
        db.commit()
        print("\nMigration completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"\nError during migration: {e}")
        raise
    finally:
        db.close()
        old_conn.close()


if __name__ == "__main__":
    migrate_sqlite_data()

