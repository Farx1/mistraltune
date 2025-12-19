#!/usr/bin/env python3
"""
Migration script to upload existing local datasets to S3/MinIO.

This script:
1. Reads existing datasets from database
2. Uploads local files to S3/MinIO
3. Updates database records with S3 keys
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import SessionLocal, get_engine
from db.models import Dataset, DatasetVersion
from storage.s3_client import get_storage_client


def migrate_to_s3():
    """Migrate existing datasets to S3."""
    db = SessionLocal()
    storage_client = get_storage_client()
    
    try:
        # Get all datasets
        datasets = db.query(Dataset).all()
        print(f"Found {len(datasets)} datasets to migrate")
        
        for dataset in datasets:
            print(f"\nProcessing dataset: {dataset.filename} (ID: {dataset.id})")
            
            # Check if already has S3 key in versions
            versions = db.query(DatasetVersion).filter(
                DatasetVersion.dataset_id == dataset.id
            ).all()
            
            if versions and versions[0].s3_key and versions[0].s3_key.startswith("s3://"):
                print(f"  Already migrated to S3: {versions[0].s3_key}")
                continue
            
            # Try to find local file
            local_paths = [
                Path(f"data/uploads/{dataset.filename}"),
                Path(f"data/storage/datasets/{dataset.id}/{dataset.filename}"),
            ]
            
            local_file = None
            for path in local_paths:
                if path.exists():
                    local_file = path
                    break
            
            if not local_file:
                print(f"  Warning: Local file not found for {dataset.filename}")
                continue
            
            # Upload to S3
            try:
                storage_key = f"{dataset.id}/{dataset.filename}"
                s3_key = storage_client.upload_file(local_file, storage_key, bucket_type="datasets")
                print(f"  Uploaded to: {s3_key}")
                
                # Update version with S3 key
                if versions:
                    version = versions[0]
                    version.s3_key = s3_key
                    if not version.file_hash:
                        version.file_hash = storage_client.compute_file_hash(local_file)
                else:
                    # Create version if doesn't exist
                    from datasets.versioning import create_dataset_version
                    create_dataset_version(db, dataset.id, local_file, s3_key=s3_key)
                
                # Update dataset hash if missing
                if not dataset.file_hash:
                    dataset.file_hash = storage_client.compute_file_hash(local_file)
                
                db.commit()
                print(f"  Successfully migrated dataset {dataset.id}")
                
            except Exception as e:
                print(f"  Error uploading {dataset.filename}: {e}")
                db.rollback()
        
        print("\nMigration completed!")
        
    except Exception as e:
        print(f"\nError during migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_to_s3()

