"""Add diagnostics and impact metrics to analysis_runs

Revision ID: 0d3b1a6cc5b4
Revises: f61dd8c176f6
Create Date: 2025-11-23 20:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0d3b1a6cc5b4'
down_revision = 'f61dd8c176f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('analysis_runs', sa.Column('diagnostics_snapshot', sa.JSON(), nullable=True))
    op.add_column('analysis_runs', sa.Column('impact_metrics', sa.JSON(), nullable=True))
    op.add_column('analysis_runs', sa.Column('estimator_results', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('analysis_runs', 'estimator_results')
    op.drop_column('analysis_runs', 'impact_metrics')
    op.drop_column('analysis_runs', 'diagnostics_snapshot')

