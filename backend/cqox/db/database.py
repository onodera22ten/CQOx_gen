"""
Database configuration and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://cqox:cqox_dev_password@localhost:5434/cqox_dev"
)

# Create engine
# For asyncpg, we would use create_async_engine
# For now, using synchronous psycopg2
engine = create_engine(
    DATABASE_URL.replace("+asyncpg", "+psycopg2"),  # Use psycopg2 for now
    poolclass=NullPool,  # Disable connection pooling for development
    echo=False,  # Set to True to see SQL queries
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()


def get_db():
    """
    Dependency to get database session

    Usage in FastAPI:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables
    Should be called once at application startup
    """
    from . import models  # Import to register models
    Base.metadata.create_all(bind=engine)


__all__ = ["Base", "engine", "SessionLocal", "get_db", "init_db"]
