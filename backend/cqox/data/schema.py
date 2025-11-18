"""
Data models and schemas for CQOx
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


# ========== Enums ==========

class EventType(str, Enum):
    """Event types"""
    VIEW = "view"
    CLICK = "click"
    PURCHASE = "purchase"
    CAMPAIGN_SEND = "campaign_send"
    OPEN = "open"
    CONVERSION = "conversion"
    CHURN = "churn"


class Channel(str, Enum):
    """Marketing channels"""
    PUSH = "push"
    EMAIL = "email"
    WEB = "web"
    APP = "app"
    ADS = "ads"
    SMS = "sms"


class OfferType(str, Enum):
    """Offer types"""
    COUPON = "coupon"
    DISCOUNT = "discount"
    FREE_SHIPPING = "free_shipping"
    CASHBACK = "cashback"
    BUNDLE = "bundle"


class PolicyStatus(str, Enum):
    """Policy status"""
    DRAFT = "draft"
    EVALUATED = "evaluated"
    RECOMMENDED = "recommended"
    DEPRECATED = "deprecated"
    ACTIVE = "active"


# ========== Core Data Models ==========

class User(BaseModel):
    """User/Customer model"""
    user_id: str
    # Static attributes
    gender: Optional[str] = None
    age: Optional[int] = None
    region: Optional[str] = None
    member_rank: Optional[str] = None
    registration_channel: Optional[str] = None
    registration_date: Optional[datetime] = None

    # Dynamic attributes
    rfm_recency: Optional[float] = None
    rfm_frequency: Optional[float] = None
    rfm_monetary: Optional[float] = None
    session_count: Optional[int] = None
    app_installed: bool = False

    # Preferences
    category_preference: Optional[dict[str, float]] = None
    price_sensitivity: Optional[float] = None

    # Additional features
    features: Optional[dict[str, Any]] = None


class Event(BaseModel):
    """Event/Log model"""
    event_id: str
    user_id: str
    timestamp: datetime
    event_type: EventType

    # Campaign related
    campaign_id: Optional[str] = None
    treatment: Optional[str] = None
    channel: Optional[Channel] = None

    # Business metrics
    revenue: float = 0.0
    margin: float = 0.0
    cost_marketing: float = 0.0
    cost_goods: float = 0.0
    nps_change: Optional[float] = None
    churn_flag: bool = False

    # Additional data
    metadata: Optional[dict[str, Any]] = None


class Campaign(BaseModel):
    """Campaign/Scenario definition"""
    campaign_id: str
    name: str
    description: Optional[str] = None
    channel: Channel
    start_at: datetime
    end_at: datetime
    treatment_arms: list[str] = Field(default_factory=list)
    experiment_flag: bool = False

    # Metrics
    total_users: Optional[int] = None
    total_cost: Optional[float] = None
    total_revenue: Optional[float] = None


# ========== Policy Models ==========

class PolicyObjective(BaseModel):
    """Policy objective"""
    name: str
    weight: float = 1.0


class RiskConstraints(BaseModel):
    """Risk constraints for policy"""
    min_overlap: float = 0.6
    min_gamma: float = 1.3
    max_negative_cate_share: float = 0.05
    max_risk_cvar_alpha_0_05: Optional[float] = None


class PolicyOffer(BaseModel):
    """Offer definition"""
    type: OfferType
    template_id: str
    discount_percentage: Optional[float] = None
    amount: Optional[float] = None


class Policy(BaseModel):
    """Policy definition (YAML/JSON representation)"""
    id: str
    name: str
    description: Optional[str] = None
    status: PolicyStatus = PolicyStatus.DRAFT

    # Data
    dataset_id: str
    target_rule: str  # SQL-like or DSL expression

    # Offer
    offer: PolicyOffer

    # Channels
    channels: list[Channel]
    frequency_cap: Optional[int] = None
    budget_limit: Optional[float] = None

    # Objectives
    objectives: list[PolicyObjective] = Field(default_factory=list)

    # Risk constraints
    risk_constraints: RiskConstraints = Field(default_factory=RiskConstraints)

    # Evaluation results (populated after offline evaluation)
    incremental_revenue: Optional[float] = None
    incremental_profit: Optional[float] = None
    roi: Optional[float] = None
    risk_score: Optional[float] = None
    cas_score: Optional[float] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Scenario(BaseModel):
    """Scenario: collection of policies"""
    scenario_id: str
    name: str
    description: Optional[str] = None
    policies: list[str] = Field(default_factory=list)  # policy IDs

    # Aggregated metrics
    total_incremental_profit: Optional[float] = None
    total_roi: Optional[float] = None
    total_risk: Optional[float] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)


# ========== Estimation Results ==========

class EstimationResult(BaseModel):
    """Causal estimation result"""
    model_config = {"protected_namespaces": ()}  # Allow model_ prefix
    
    model_run_id: str
    dataset_id: str
    estimator: str
    outcome: str
    treatment: str
    features: list[str]

    # Results
    ate: Optional[float] = None
    ate_std: Optional[float] = None
    cate_mean: Optional[float] = None
    cate_std: Optional[float] = None

    # Diagnostics
    overlap_score: Optional[float] = None
    balance_score: Optional[float] = None
    sensitivity_gamma: Optional[float] = None

    # Status
    status: str = "pending"  # pending, running, completed, failed
    error_message: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class DiagnosticResult(BaseModel):
    """Diagnostic result"""
    model_config = {"protected_namespaces": ()}  # Allow model_ prefix
    
    diagnostic_id: str
    model_run_id: str
    diagnostic_type: str
    score: Optional[float] = None
    passed: bool = False
    warning: Optional[str] = None
    data: Optional[dict[str, Any]] = None
    visualization_id: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
