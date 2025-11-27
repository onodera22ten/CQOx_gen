"""Add Viz.pdf Global Growth Console columns

Revision ID: 003
Revises: 0d3b1a6cc5b4
Create Date: 2025-11-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '0d3b1a6cc5b4'
branch_labels = None
depends_on = None


def upgrade():
    # Add Viz.pdf columns to analysis_runs table
    op.add_column('analysis_runs', sa.Column('roi', sa.Float(), nullable=True))
    op.add_column('analysis_runs', sa.Column('cas', sa.Float(), nullable=True))
    op.add_column('analysis_runs', sa.Column('risk', sa.Float(), nullable=True))
    op.add_column('analysis_runs', sa.Column('channel', sa.String(), nullable=True))
    op.add_column('analysis_runs', sa.Column('segment_label', sa.String(), nullable=True))
    op.add_column('analysis_runs', sa.Column('budget', sa.Float(), nullable=True))
    op.add_column('analysis_runs', sa.Column('reach_users', sa.Integer(), nullable=True))
    op.add_column('analysis_runs', sa.Column('period_start', sa.DateTime(), nullable=True))
    op.add_column('analysis_runs', sa.Column('period_end', sa.DateTime(), nullable=True))

    # Create segments table
    op.create_table(
        'segments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('segment_id', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('incremental_clv', sa.Float(), nullable=True),
        sa.Column('user_count', sa.Integer(), nullable=True),
        sa.Column('rfm_r', sa.Integer(), nullable=True),
        sa.Column('rfm_f', sa.Integer(), nullable=True),
        sa.Column('rfm_m', sa.Integer(), nullable=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'))
    )


def downgrade():
    # Drop segments table
    op.drop_table('segments')

    # Remove Viz.pdf columns from analysis_runs
    op.drop_column('analysis_runs', 'period_end')
    op.drop_column('analysis_runs', 'period_start')
    op.drop_column('analysis_runs', 'reach_users')
    op.drop_column('analysis_runs', 'budget')
    op.drop_column('analysis_runs', 'segment_label')
    op.drop_column('analysis_runs', 'channel')
    op.drop_column('analysis_runs', 'risk')
    op.drop_column('analysis_runs', 'cas')
    op.drop_column('analysis_runs', 'roi')
