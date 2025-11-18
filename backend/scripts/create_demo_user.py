#!/usr/bin/env python3
"""
デモユーザー作成スクリプト

デフォルトユーザー:
- Email: admin@cqox.local
- Password: admin123
- Role: admin

- Email: analyst@cqox.local
- Password: analyst123
- Role: analyst

- Email: viewer@cqox.local
- Password: viewer123
- Role: viewer
"""

import asyncio
import asyncpg
import os
from datetime import datetime
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# デフォルトユーザー
DEFAULT_USERS = [
    {
        "email": "admin@cqox.local",
        "password": "admin123",
        "name": "Admin User",
        "roles": ["admin", "analyst", "viewer"]
    },
    {
        "email": "analyst@cqox.local",
        "password": "analyst123",
        "name": "Analyst User",
        "roles": ["analyst", "viewer"]
    },
    {
        "email": "viewer@cqox.local",
        "password": "viewer123",
        "name": "Viewer User",
        "roles": ["viewer"]
    }
]


async def create_users_table(conn):
    """ユーザーテーブルを作成"""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            password_hash TEXT NOT NULL,
            roles TEXT[] DEFAULT ARRAY['viewer'],
            tenant_id TEXT DEFAULT 'default_tenant',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            deleted_at TIMESTAMP WITH TIME ZONE,
            anonymized BOOLEAN DEFAULT FALSE
        )
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(tenant_id)
    """)
    
    print("✓ Users table created")


async def insert_demo_users(conn):
    """デモユーザーを挿入"""
    import uuid
    
    for user_data in DEFAULT_USERS:
        # Check if user exists
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1",
            user_data["email"]
        )
        
        if existing:
            print(f"⚠ User {user_data['email']} already exists, skipping")
            continue
        
        # Hash password
        password_hash = pwd_context.hash(user_data["password"])
        
        # Insert user
        user_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        await conn.execute(
            """
            INSERT INTO users (id, email, name, password_hash, roles, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            user_id,
            user_data["email"],
            user_data["name"],
            password_hash,
            user_data["roles"],
            now,
            now
        )
        
        print(f"✓ Created user: {user_data['email']} (roles: {', '.join(user_data['roles'])})")


async def main():
    """メイン処理"""
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://cqox:cqox_dev_password@localhost:5434/cqox_dev"
    )
    
    # asyncpg は postgresql:// のみサポート
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    print("Connecting to database...")
    conn = await asyncpg.connect(database_url)
    
    try:
        await create_users_table(conn)
        await insert_demo_users(conn)
        
        print("\n" + "="*60)
        print("🎉 Demo users created successfully!")
        print("="*60)
        print("\nLogin credentials:")
        print("-" * 60)
        for user_data in DEFAULT_USERS:
            print(f"  Email: {user_data['email']}")
            print(f"  Password: {user_data['password']}")
            print(f"  Roles: {', '.join(user_data['roles'])}")
            print()
        print("="*60)
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

