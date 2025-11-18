"""
Application settings and configuration
"""
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # Application
    app_name: str = "CQOx"
    debug: bool = False
    api_prefix: str = "/api"
    api_url: str = "http://localhost:8000"  # For OAuth2 callbacks
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Authentication (set to True in development to skip auth)
    skip_auth: bool = True

    # Database
    database_url: str = "postgresql://cqox:cqox@localhost:5432/cqox"

    # Redis (for Celery)
    redis_url: str = "redis://localhost:6379/0"

    # Data paths
    # Base directory for data/models/config/artifacts
    # Default: project root (backend/../../)
    base_dir: Path = Path(__file__).resolve().parents[3]
    data_dir: Path = base_dir / "data"
    models_dir: Path = base_dir / "models"
    exports_dir: Path = base_dir / "data" / "exports"
    policies_dir: Path = base_dir / "policies"
    config_dir: Path = base_dir / "config"
    artifacts_dir: Path = base_dir / "artifacts"
    
    log_level: str = "INFO"
    secret_key: str = "your-secret-key-here"

    # Wolfram
    wolfram_script_path: str = "wolframscript"
    wolfram_dir: Path = base_dir / "wolfram"
    wolfram_output_dir: Path = base_dir / "wolfram" / "outputs"

    # Causal inference defaults
    default_estimators: list[str] = [
        "s_learner",
        "t_learner",
        "x_learner",
        "dr_learner",
        "causal_forest",
        "doubly_robust_forest",
        "uplift_forest"
    ]

    # Risk thresholds
    min_overlap: float = 0.6
    min_gamma: float = 1.3
    max_negative_cate_share: float = 0.05

    # Multi-objective defaults
    default_objectives: list[str] = ["incremental_profit", "risk_metric"]

    # ========== 大規模データ処理設定 ==========
    # Batch processing
    batch_chunk_size: int = 100_000  # 100K rows per chunk
    max_batch_size: int = 10_000_000  # 10M rows max
    parallel_workers: int = 4  # CPU cores for parallel processing
    
    # Database connection pool (Architecture.md: 50-200 connections)
    db_pool_size: int = 50  # Base pool size
    db_max_overflow: int = 150  # Max overflow connections
    db_pool_timeout: int = 30  # Seconds to wait for connection
    db_pool_recycle: int = 3600  # Recycle connections after 1 hour
    
    # Celery task settings
    celery_task_soft_time_limit: int = 3600  # 1 hour soft limit
    celery_task_hard_time_limit: int = 7200  # 2 hour hard limit
    celery_task_acks_late: bool = True  # Acknowledge after completion
    celery_worker_prefetch_multiplier: int = 1  # Prefetch 1 task at a time for long-running tasks
    
    # Memory management
    max_memory_per_worker_mb: int = 4096  # 4GB per worker
    enable_streaming_processing: bool = True  # Use streaming for large datasets

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()

# Create necessary directories
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.models_dir.mkdir(parents=True, exist_ok=True)
settings.exports_dir.mkdir(parents=True, exist_ok=True)
settings.wolfram_output_dir.mkdir(parents=True, exist_ok=True)
settings.config_dir.mkdir(parents=True, exist_ok=True)
settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
