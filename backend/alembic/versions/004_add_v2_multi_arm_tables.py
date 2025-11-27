"""Add V2 Module A tables for Multi-Arm Causal Design

Revision ID: 004
Revises: 003
Create Date: 2025-11-26 04:00:00.000000

V2.pdf Module A: Multi-Arm Causal Design Studio
- multi_arm_experiments: 多腕実験定義
- treatment_arms: 各armの定義（Control/Light/Medium/Aggressive等）
- dose_response_configs: Dose-Response設定
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Multi-Arm Experiments テーブル
    op.create_table(
        'multi_arm_experiments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('experiment_name', sa.String(255), nullable=False),
        sa.Column('treatment_type', sa.String(50), nullable=False),  # 'binary' | 'multi_armed' | 'dose_response'
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('treatment_column', sa.String(255), nullable=False),
        sa.Column('outcome_column', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),  # draft | running | completed
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
    )
    op.create_index('ix_multi_arm_experiments_tenant_id', 'multi_arm_experiments', ['tenant_id'])
    op.create_index('ix_multi_arm_experiments_status', 'multi_arm_experiments', ['status'])

    # Treatment Arms テーブル（Multi-Armed用）
    op.create_table(
        'treatment_arms',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('experiment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('arm_id', sa.Integer, nullable=False),  # 0=control, 1,2,3...=treatment arms
        sa.Column('arm_label', sa.String(100), nullable=False),  # "Control", "Light", "Medium", "Aggressive"
        sa.Column('arm_description', sa.Text, nullable=True),
        sa.Column('delta_yen', sa.Numeric(15, 2), nullable=True),
        sa.Column('cas', sa.Numeric(5, 4), nullable=True),
        sa.Column('risk', sa.Numeric(5, 4), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['experiment_id'], ['multi_arm_experiments.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_treatment_arms_experiment_id', 'treatment_arms', ['experiment_id'])
    op.create_unique_constraint('uq_treatment_arms_experiment_arm', 'treatment_arms', ['experiment_id', 'arm_id'])

    # Dose-Response Configs テーブル
    op.create_table(
        'dose_response_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('experiment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('min_dose', sa.Numeric(10, 2), nullable=False),
        sa.Column('max_dose', sa.Numeric(10, 2), nullable=False),
        sa.Column('dose_unit', sa.String(50), nullable=True),  # "%", "times", "yen"
        sa.Column('polynomial_degree', sa.Integer, nullable=False, server_default='2'),  # 多項式次数
        sa.Column('curve_data', postgresql.JSONB, nullable=True),  # {dose: effect} のカーブデータ
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['experiment_id'], ['multi_arm_experiments.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_dose_response_configs_experiment_id', 'dose_response_configs', ['experiment_id'])


def downgrade():
    op.drop_table('dose_response_configs')
    op.drop_table('treatment_arms')
    op.drop_table('multi_arm_experiments')
