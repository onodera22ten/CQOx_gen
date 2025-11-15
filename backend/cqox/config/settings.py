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

    # Database
    database_url: str = "postgresql://cqox:cqox@localhost:5432/cqox"

    # Redis (for Celery)
    redis_url: str = "redis://localhost:6379/0"

    # Data paths
    base_dir: Path = Path("/home/hirokionodeara/CQOx_gen")
    data_dir: Path = base_dir / "data"
    models_dir: Path = base_dir / "models"
    exports_dir: Path = base_dir / "data" / "exports"
    policies_dir: Path = base_dir / "policies"
    config_dir: Path = base_dir / "config"
    artifacts_dir: Path = base_dir / "artifacts"

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
