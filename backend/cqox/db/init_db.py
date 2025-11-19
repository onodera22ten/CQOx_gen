"""
Database initialization script

Creates tables and initializes admin user
"""
from sqlalchemy.orm import Session
from cqox.db.database import engine, Base
from cqox.db.models import User
from cqox.services.auth_service import AuthService
from cqox.db.database import SessionLocal


def init_db() -> None:
    """Initialize database: create tables and admin user"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")

    # Initialize admin user
    db = SessionLocal()
    try:
        AuthService.init_admin_user(db)
    finally:
        db.close()

    print("✓ Database initialization complete")


if __name__ == "__main__":
    init_db()
