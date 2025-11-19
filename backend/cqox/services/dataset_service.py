"""
Dataset Service - Business logic for dataset management
"""
import os
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import pandas as pd

from cqox.db.models import Dataset, User


class DatasetService:
    """Service for dataset management operations"""

    @staticmethod
    def get_datasets_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Dataset]:
        """Get all datasets for a user"""
        return db.query(Dataset).filter(
            Dataset.user_id == user_id
        ).offset(skip).limit(limit).all()

    @staticmethod
    def get_dataset_by_id(db: Session, dataset_id: int, user_id: int) -> Optional[Dataset]:
        """Get a specific dataset by ID (with user ownership check)"""
        return db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.user_id == user_id
        ).first()

    @staticmethod
    def create_dataset(
        db: Session,
        user_id: int,
        name: str,
        file_path: str,
        description: Optional[str] = None
    ) -> Dataset:
        """Create a new dataset record"""
        dataset = Dataset(
            user_id=user_id,
            name=name,
            description=description,
            file_path=file_path,
            status='uploaded'
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        return dataset

    @staticmethod
    def update_dataset_stats(
        db: Session,
        dataset_id: int,
        row_count: int,
        column_count: int,
        columns_info: Optional[dict] = None
    ) -> Dataset:
        """Update dataset statistics after file processing"""
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if dataset:
            dataset.row_count = row_count
            dataset.column_count = column_count
            if columns_info:
                dataset.columns_info = columns_info
            dataset.status = 'ready'
            db.commit()
            db.refresh(dataset)
        return dataset

    @staticmethod
    def delete_dataset(db: Session, dataset_id: int, user_id: int) -> bool:
        """Delete a dataset (with ownership check)"""
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.user_id == user_id
        ).first()

        if not dataset:
            return False

        # Delete associated file if exists
        if dataset.file_path and os.path.exists(dataset.file_path):
            try:
                os.remove(dataset.file_path)
            except Exception as e:
                print(f"Failed to delete file: {e}")

        db.delete(dataset)
        db.commit()
        return True

    @staticmethod
    def process_uploaded_file(file_path: str) -> dict:
        """Process uploaded file and extract metadata"""
        try:
            # Read file based on extension
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.parquet'):
                df = pd.read_parquet(file_path)
            else:
                raise ValueError("Unsupported file format. Use CSV or Parquet.")

            # Extract metadata
            row_count = len(df)
            column_count = len(df.columns)

            columns_info = {
                col: str(df[col].dtype) for col in df.columns
            }

            # Suggest columns for causal analysis
            suggestions = {
                'treatment_col': None,
                'outcome_col': None,
                'feature_cols': []
            }

            # Simple heuristics for suggestions
            for col in df.columns:
                col_lower = col.lower()
                if 'treatment' in col_lower or 'treat' in col_lower:
                    suggestions['treatment_col'] = col
                elif 'outcome' in col_lower or 'revenue' in col_lower or 'conversion' in col_lower:
                    suggestions['outcome_col'] = col
                else:
                    suggestions['feature_cols'].append(col)

            return {
                'row_count': row_count,
                'column_count': column_count,
                'columns_info': columns_info,
                'suggestions': suggestions
            }

        except Exception as e:
            raise ValueError(f"Failed to process file: {str(e)}")

    @staticmethod
    def get_dataset_preview(file_path: str, limit: int = 100) -> dict:
        """Get preview of dataset"""
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, nrows=limit)
            elif file_path.endswith('.parquet'):
                df = pd.read_parquet(file_path)
                df = df.head(limit)
            else:
                raise ValueError("Unsupported file format")

            return {
                'columns': df.columns.tolist(),
                'data': df.to_dict('records'),
                'row_count': len(df)
            }

        except Exception as e:
            raise ValueError(f"Failed to preview file: {str(e)}")
