"""
Authentication Service - Business logic for user authentication
"""
import os
import hashlib
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from cqox.db.models import User
from cqox.models.auth import UserCreate, TokenPayload

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class AuthService:
    """Authentication service for user management and JWT token generation"""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        # Use SHA256 for passwords > 72 bytes
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = hashlib.sha256(password_bytes).digest()
        return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        # Use SHA256 for passwords > 72 bytes
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = hashlib.sha256(password_bytes).digest()
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow()
        })
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[TokenPayload]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return TokenPayload(**payload)
        except JWTError:
            return None

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        """Create a new user"""
        hashed_password = AuthService.get_password_hash(user.password)
        db_user = User(
            email=user.email,
            hashed_password=hashed_password,
            role=user.role,
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = AuthService.get_user_by_email(db, email)
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    @staticmethod
    def init_admin_user(db: Session):
        """Initialize admin user if not exists"""
        admin_email = os.getenv("ADMIN_EMAIL", "admin@cqox.local")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin_password_change_me")

        # Check if admin exists
        existing_admin = AuthService.get_user_by_email(db, admin_email)
        if existing_admin:
            print(f"Admin user already exists: {admin_email}")
            return existing_admin

        # Create admin user
        admin_user = UserCreate(
            email=admin_email,
            password=admin_password,
            role="admin"
        )
        db_admin = AuthService.create_user(db, admin_user)
        print(f"Created admin user: {admin_email}")
        return db_admin
