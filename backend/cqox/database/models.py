"""
Database models (SQLAlchemy)
"""
from datetime import datetime
import uuid as uuid_lib

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

Base = declarative_base()

DEFAULT_TENANT_ID = uuid_lib.UUID("00000000-0000-0000-0000-000000000001")


class Dataset(Base):
    """Dataset table"""
    __tablename__ = "datasets"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    file_path = Column(String)
    row_count = Column(Integer)
    column_count = Column(Integer)
    schema = Column(JSON)  # Column name -> type mapping
    tenant_id = Column(PGUUID(as_uuid=True), default=DEFAULT_TENANT_ID)  # Multi-tenancy support
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    model_runs = relationship("ModelRun", back_populates="dataset")


class Policy(Base):
    """Policy table"""
    __tablename__ = "policies"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="draft")
    dataset_id = Column(PGUUID(as_uuid=True), ForeignKey("datasets.id"))
    target_rule = Column(Text)
    offer_config = Column(JSON)
    channels = Column(JSON)
    frequency_cap = Column(Integer)
    budget_limit = Column(Float)
    objectives = Column(JSON)
    risk_constraints = Column(JSON)

    # Evaluation results
    incremental_revenue = Column(Float)
    incremental_profit = Column(Float)
    roi = Column(Float)
    risk_score = Column(Float)
    cas_score = Column(Float)

    tenant_id = Column(PGUUID(as_uuid=True), default=DEFAULT_TENANT_ID)  # Multi-tenancy support
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModelRun(Base):
    """Model training run table"""
    __tablename__ = "model_runs"

    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.id"))
    estimator = Column(String, nullable=False)
    outcome = Column(String)
    treatment = Column(String)
    features = Column(JSON)

    # Results
    ate = Column(Float)
    ate_std = Column(Float)
    cate_mean = Column(Float)
    cate_std = Column(Float)

    # Diagnostics
    overlap_score = Column(Float)
    balance_score = Column(Float)
    sensitivity_gamma = Column(Float)
    cas_score = Column(Float)

    # Status
    status = Column(String, default="pending")
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    dataset = relationship("Dataset", back_populates="model_runs")
    diagnostics = relationship("Diagnostic", back_populates="model_run")


class Diagnostic(Base):
    """Diagnostic results table"""
    __tablename__ = "diagnostics"

    id = Column(String, primary_key=True)
    model_run_id = Column(String, ForeignKey("model_runs.id"))
    diagnostic_type = Column(String, nullable=False)
    score = Column(Float)
    passed = Column(Boolean, default=False)
    warning = Column(Text)
    data = Column(JSON)
    visualization_id = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    model_run = relationship("ModelRun", back_populates="diagnostics")


class Scenario(Base):
    """Scenario table"""
    __tablename__ = "scenarios"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    policy_ids = Column(JSON)

    # Aggregated metrics
    total_incremental_profit = Column(Float)
    total_roi = Column(Float)
    total_risk = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)


class ColumnMappingProfile(Base):
    """Column mapping profile table"""
    __tablename__ = "column_mapping_profiles"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    source_system = Column(String)
    mapping_json = Column(JSON, nullable=False)  # Changed from 'mapping' to 'mapping_json'
    version = Column(String, default="1.0")
    tenant_id = Column(String)  # Multi-tenancy support

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Decision(Base):
    """Decision Card table (Δ¥ + Go/Canary/Hold判定)"""
    __tablename__ = "decisions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id"), nullable=False)
    scenario_id = Column(PGUUID(as_uuid=True))  # Optional
    scenario_name = Column(String, nullable=False)

    # Δ¥関連
    delta_yen = Column(Float, nullable=False)  # S1 - S0 の期待Δ¥（円）
    delta_yen_ci_low = Column(Float)  # 95% 信頼区間下限
    delta_yen_ci_high = Column(Float)  # 95% 信頼区間上限
    delta_yen_std = Column(Float)  # Δ¥の標準偏差

    # 判定
    verdict = Column(String, nullable=False)  # "Go" | "Canary" | "Hold"
    reason = Column(Text)  # Hold/Canary理由

    # メタデータ（マーケティング用）
    channel = Column(String)  # チャネル: "アプリPush", "Email", etc.
    segment = Column(String)  # セグメント: "RFM High-Value", etc.

    # 品質スコア & 再現性
    quality_scores = Column(JSON)  # { overlap_coverage, iv_f_stat, ... }
    scenario_spec = Column(JSON)  # S0/S1のポリシー定義
    estimator_results = Column(JSON)  # 使用した推定器の詳細結果

    # Audit
    tenant_id = Column(PGUUID(as_uuid=True), default=DEFAULT_TENANT_ID)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    policy = relationship("Policy")


class AnalysisRun(Base):
    """Analysis Run table (因果推論分析実行)"""
    __tablename__ = "analysis_runs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id"), nullable=False)
    dataset_id = Column(PGUUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    
    # Analysis configuration
    estimators = Column(JSON)  # List of estimators: ["DR", "IPW", etc.]
    treatment_col = Column(String)
    outcome_col = Column(String)
    feature_cols = Column(JSON)
    scenario_spec = Column(JSON)
    
    # Status
    status = Column(String, default="pending")  # pending, running, completed, failed
    progress = Column(Float, default=0.0)  # 0.0-1.0
    
    # Results (if completed)
    delta_yen = Column(Float)
    delta_yen_ci_low = Column(Float)
    delta_yen_ci_high = Column(Float)
    verdict = Column(String)  # Go, Canary, Hold
    
    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Error (if failed)
    error_message = Column(Text)
    
    # Multi-tenancy
    tenant_id = Column(PGUUID(as_uuid=True), default=DEFAULT_TENANT_ID)
    
    # Relationships
    policy = relationship("Policy")
    dataset = relationship("Dataset")
