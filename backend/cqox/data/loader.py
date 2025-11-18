"""
Data loading and preprocessing
"""
from pathlib import Path
from typing import Optional, Union, Dict, Any
import pandas as pd
import polars as pl
from loguru import logger

from cqox.config import settings


class DataLoader:
    """Load data from various sources"""

    @staticmethod
    def load_csv(
        file_path: Union[str, Path],
        **kwargs
    ) -> pd.DataFrame:
        """Load CSV file"""
        logger.info(f"Loading CSV from {file_path}")
        df = pd.read_csv(file_path, **kwargs)
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        return df

    @staticmethod
    def load_parquet(
        file_path: Union[str, Path],
        engine: str = 'pyarrow',
        **kwargs
    ) -> pd.DataFrame:
        """Load Parquet file"""
        logger.info(f"Loading Parquet from {file_path}")
        df = pd.read_parquet(file_path, engine=engine, **kwargs)
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        return df

    @staticmethod
    def load_auto(
        file_path: Union[str, Path],
        **kwargs
    ) -> pd.DataFrame:
        """Auto-detect format and load"""
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()

        if suffix == '.csv':
            return DataLoader.load_csv(file_path, **kwargs)
        elif suffix in ['.parquet', '.pq']:
            return DataLoader.load_parquet(file_path, **kwargs)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    @staticmethod
    def save_parquet(
        df: pd.DataFrame,
        file_path: Union[str, Path],
        compression: str = 'snappy'
    ):
        """Save DataFrame as Parquet"""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving Parquet to {file_path}")
        df.to_parquet(file_path, compression=compression, index=False)
        logger.info(f"Saved {len(df)} rows to {file_path}")

    @staticmethod
    def get_column_info(df: pd.DataFrame) -> Dict[str, Any]:
        """Get column information"""
        return {
            'columns': list(df.columns),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'row_count': len(df),
            'column_count': len(df.columns),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
        }


class DatasetRegistry:
    """Registry for managing datasets"""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.data_dir
        self.registry_file = self.data_dir / "registry.yaml"

    def register_dataset(
        self,
        dataset_id: str,
        metadata: Dict[str, Any]
    ):
        """Register a dataset"""
        import yaml

        # Load existing registry
        if self.registry_file.exists():
            with open(self.registry_file, 'r') as f:
                registry = yaml.safe_load(f) or {}
        else:
            registry = {}

        # Add dataset
        registry[dataset_id] = metadata

        # Save registry
        with open(self.registry_file, 'w') as f:
            yaml.dump(registry, f, default_flow_style=False)

        logger.info(f"Registered dataset: {dataset_id}")

    def get_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """Get dataset metadata"""
        import yaml

        if not self.registry_file.exists():
            raise ValueError("Dataset registry not found")

        with open(self.registry_file, 'r') as f:
            registry = yaml.safe_load(f) or {}

        if dataset_id not in registry:
            raise ValueError(f"Dataset '{dataset_id}' not found in registry")

        return registry[dataset_id]

    def list_datasets(self) -> Dict[str, Any]:
        """List all registered datasets"""
        import yaml

        if not self.registry_file.exists():
            return {}

        with open(self.registry_file, 'r') as f:
            registry = yaml.safe_load(f) or {}

        return registry

    def delete_dataset(self, dataset_id: str):
        """Delete a dataset from registry and optionally remove files"""
        import yaml
        import os

        if not self.registry_file.exists():
            raise ValueError("Dataset registry not found")

        # Load existing registry
        with open(self.registry_file, 'r') as f:
            registry = yaml.safe_load(f) or {}

        if dataset_id not in registry:
            raise ValueError(f"Dataset '{dataset_id}' not found in registry")

        # Get dataset info before deletion
        dataset_info = registry[dataset_id]

        # Remove from registry
        del registry[dataset_id]

        # Save updated registry
        with open(self.registry_file, 'w') as f:
            yaml.dump(registry, f, default_flow_style=False)

        # Optionally delete physical file
        if 'file_path' in dataset_info:
            file_path = Path(dataset_info['file_path'])
            if file_path.exists():
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted dataset file: {file_path}")
                except Exception as e:
                    logger.warning(f"Could not delete file {file_path}: {e}")

        logger.info(f"Deleted dataset from registry: {dataset_id}")
