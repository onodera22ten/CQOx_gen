"""
初期デモユーザーを作成するスクリプト

Usage:
    docker compose exec api python backend/scripts/init_demo_users.py
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from sqlalchemy import text
from cqox.database.connection import get_db
from cqox.auth.jwt_manager import get_jwt_manager
import uuid
from datetime import datetime


async def create_demo_users():
    """デモユーザーを作成"""
    jwt_manager = get_jwt_manager()
    
    demo_users = [
        {
            "email": "admin@cqox.com",
            "password": "admin_password_change_me",
            "name": "Admin User",
            "roles": ["admin", "analyst", "viewer"]
        },
        {
            "email": "admin@cqox.local",
            "password": "admin123",
            "name": "Admin Demo",
            "roles": ["admin", "analyst", "viewer"]
        },
        {
            "email": "analyst@cqox.local",
            "password": "analyst123",
            "name": "Analyst Demo",
            "roles": ["analyst", "viewer"]
        },
        {
            "email": "viewer@cqox.local",
            "password": "viewer123",
            "name": "Viewer Demo",
            "roles": ["viewer"]
        }
    ]
    
    async for db in get_db():
        for user_data in demo_users:
            password_hash = jwt_manager.hash_password(user_data["password"])
            user_id = str(uuid.uuid4())
            tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
            
            # Check if user exists
            result = await db.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": user_data["email"]}
            )
            existing_user = result.fetchone()
            
            if existing_user:
                # Update existing user
                await db.execute(
                    text("""
                        UPDATE users
                        SET password_hash = :password_hash,
                            name = :name,
                            roles = :roles::jsonb,
                            updated_at = :updated_at
                        WHERE email = :email
                    """),
                    {
                        "email": user_data["email"],
                        "password_hash": password_hash,
                        "name": user_data["name"],
                        "roles": str(user_data["roles"]).replace("'", '"'),
                        "updated_at": datetime.utcnow()
                    }
                )
                print(f"✅ Updated user: {user_data['email']}")
            else:
                # Create new user
                await db.execute(
                    text("""
                        INSERT INTO users (id, email, name, password_hash, roles, tenant_id, created_at, updated_at)
                        VALUES (:id, :email, :name, :password_hash, :roles::jsonb, :tenant_id, :created_at, :updated_at)
                    """),
                    {
                        "id": uuid.UUID(user_id),
                        "email": user_data["email"],
                        "name": user_data["name"],
                        "password_hash": password_hash,
                        "roles": str(user_data["roles"]).replace("'", '"'),
                        "tenant_id": tenant_id,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                )
                print(f"✅ Created user: {user_data['email']}")
            
        await db.commit()
        print("\n✅ All demo users created/updated successfully!")
        print("\nLogin credentials:")
        print("  - admin@cqox.com / admin_password_change_me")
        print("  - admin@cqox.local / admin123")
        print("  - analyst@cqox.local / analyst123")
        print("  - viewer@cqox.local / viewer123")


if __name__ == "__main__":
    asyncio.run(create_demo_users())

