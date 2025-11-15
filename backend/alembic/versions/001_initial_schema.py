"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-11-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create datasets table
    op.create_table(
        'datasets',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('column_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create policies table
    op.create_table(
        'policies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('dataset_id', sa.String(), nullable=True),
        sa.Column('target_rule', sa.Text(), nullable=True),
        sa.Column('offer_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('channels', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('frequency_cap', sa.Integer(), nullable=True),
        sa.Column('budget_limit', sa.Float(), nullable=True),
        sa.Column('objectives', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('risk_constraints', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('incremental_revenue', sa.Float(), nullable=True),
        sa.Column('incremental_profit', sa.Float(), nullable=True),
        sa.Column('roi', sa.Float(), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('cas_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'])
    )

    # Create model_runs table
    op.create_table(
        'model_runs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('dataset_id', sa.String(), nullable=True),
        sa.Column('estimator', sa.String(), nullable=False),
        sa.Column('outcome', sa.String(), nullable=True),
        sa.Column('treatment', sa.String(), nullable=True),
        sa.Column('features', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ate', sa.Float(), nullable=True),
        sa.Column('ate_std', sa.Float(), nullable=True),
        sa.Column('cate_mean', sa.Float(), nullable=True),
        sa.Column('cate_std', sa.Float(), nullable=True),
        sa.Column('overlap_score', sa.Float(), nullable=True),
        sa.Column('balance_score', sa.Float(), nullable=True),
        sa.Column('sensitivity_gamma', sa.Float(), nullable=True),
        sa.Column('cas_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'])
    )

    # Create diagnostics table
    op.create_table(
        'diagnostics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('model_run_id', sa.String(), nullable=True),
        sa.Column('diagnostic_type', sa.String(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('passed', sa.Boolean(), nullable=True),
        sa.Column('warning', sa.Text(), nullable=True),
        sa.Column('data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('visualization_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['model_run_id'], ['model_runs.id'])
    )

    # Create scenarios table
    op.create_table(
        'scenarios',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('policy_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('total_incremental_profit', sa.Float(), nullable=True),
        sa.Column('total_roi', sa.Float(), nullable=True),
        sa.Column('total_risk', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create column_mapping_profiles table
    op.create_table(
        'column_mapping_profiles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('mapping', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create indexes
    op.create_index('ix_datasets_created_at', 'datasets', ['created_at'])
    op.create_index('ix_policies_status', 'policies', ['status'])
    op.create_index('ix_model_runs_status', 'model_runs', ['status'])
    op.create_index('ix_diagnostics_type', 'diagnostics', ['diagnostic_type'])


def downgrade() -> None:
    op.drop_index('ix_diagnostics_type')
    op.drop_index('ix_model_runs_status')
    op.drop_index('ix_policies_status')
    op.drop_index('ix_datasets_created_at')

    op.drop_table('column_mapping_profiles')
    op.drop_table('scenarios')
    op.drop_table('diagnostics')
    op.drop_table('model_runs')
    op.drop_table('policies')
    op.drop_table('datasets')
