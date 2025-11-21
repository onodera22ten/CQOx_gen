"""Add users table

Revision ID: 002
Revises: 001
Create Date: 2025-11-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime
import uuid

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, default='viewer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, default=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column('last_login', sa.DateTime(), nullable=True),
    )

    # Insert default admin user
    # Password: admin_password_change_me (hashed with bcrypt)
    # Hash generated with: passlib.hash.bcrypt.hash("admin_password_change_me")
    op.execute("""
        INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_superuser, tenant_id, created_at, updated_at)
        VALUES (
            '00000000-0000-0000-0000-000000000001'::uuid,
            'admin@cqox.local',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU2hPKIB7dVe',
            'System Administrator',
            'admin',
            true,
            true,
            '00000000-0000-0000-0000-000000000001'::uuid,
            NOW(),
            NOW()
        )
    """)


def downgrade() -> None:
    op.drop_table('users')
