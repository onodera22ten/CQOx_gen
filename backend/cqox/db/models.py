"""
SQLAlchemy ORM Models for CQOx database tables
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, ARRAY, BigInteger, Numeric, JSON
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    """User table for authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="viewer", index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    datasets = relationship("Dataset", back_populates="user", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="user", cascade="all, delete-orphan")


class Dataset(Base):
    """Dataset table for uploaded data files"""
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(Text, nullable=False)
    file_size = Column(BigInteger)
    row_count = Column(Integer)
    column_count = Column(Integer)
    columns_info = Column(JSON)  # Column names and types
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_metadata = Column(JSON)  # Renamed from 'metadata' to avoid SQLAlchemy reserved word
    status = Column(String(50), default="uploaded", index=True)

    # Relationships
    user = relationship("User", back_populates="datasets")
    analyses = relationship("Analysis", back_populates="dataset", cascade="all, delete-orphan")


class Analysis(Base):
    """Analysis table for tracking causal analyses"""
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    estimator_type = Column(String(50), nullable=False)
    treatment_col = Column(String(255))
    outcome_col = Column(String(255))
    feature_cols = Column(ARRAY(Text))
    status = Column(String(50), default="pending", index=True)
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime)
    results = Column(JSON)
    error_message = Column(Text)

    # Relationships
    user = relationship("User", back_populates="analyses")
    dataset = relationship("Dataset", back_populates="analyses")
    decisions = relationship("Decision", back_populates="analysis", cascade="all, delete-orphan")


class Decision(Base):
    """Decision table for Go/Canary/Hold verdicts"""
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    policy_name = Column(String(255))
    verdict = Column(String(20), nullable=False, index=True)  # 'Go', 'Canary', 'Hold'
    delta_yen = Column(Numeric(15, 2))
    confidence_interval_low = Column(Numeric(15, 2))
    confidence_interval_high = Column(Numeric(15, 2))
    cas_score = Column(Numeric(3, 2))
    risk_score = Column(Numeric(3, 2))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_metadata = Column(JSON)  # Renamed from 'metadata' to avoid SQLAlchemy reserved word

    # Relationships
    user = relationship("User", back_populates="decisions")
    analysis = relationship("Analysis", back_populates="decisions")
