-- デモユーザー作成スクリプト
-- 
-- 実行方法:
-- psql -h localhost -p 5434 -U cqox -d cqox_dev -f scripts/create_demo_user.sql
--
-- または:
-- docker exec -i cqox-postgres psql -U cqox -d cqox_dev < scripts/create_demo_user.sql

-- ユーザーテーブル作成
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
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(tenant_id);

-- デモユーザー挿入（パスワードは bcrypt でハッシュ化済み）
-- admin@cqox.local / admin123
-- $2b$12$ は bcrypt のプレフィックス

-- admin@cqox.local / admin123 (roles: admin, analyst, viewer)
INSERT INTO users (id, email, name, password_hash, roles, created_at, updated_at)
VALUES (
    'admin-001',
    'admin@cqox.local',
    'Admin User',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYuYLaOQdGq', -- admin123
    ARRAY['admin', 'analyst', 'viewer'],
    NOW(),
    NOW()
)
ON CONFLICT (email) DO NOTHING;

-- analyst@cqox.local / analyst123 (roles: analyst, viewer)
INSERT INTO users (id, email, name, password_hash, roles, created_at, updated_at)
VALUES (
    'analyst-001',
    'analyst@cqox.local',
    'Analyst User',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYuYLaOQdGq', -- analyst123
    ARRAY['analyst', 'viewer'],
    NOW(),
    NOW()
)
ON CONFLICT (email) DO NOTHING;

-- viewer@cqox.local / viewer123 (roles: viewer)
INSERT INTO users (id, email, name, password_hash, roles, created_at, updated_at)
VALUES (
    'viewer-001',
    'viewer@cqox.local',
    'Viewer User',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYuYLaOQdGq', -- viewer123
    ARRAY['viewer'],
    NOW(),
    NOW()
)
ON CONFLICT (email) DO NOTHING;

-- 確認
SELECT id, email, name, roles, created_at FROM users ORDER BY created_at DESC;

-- 成功メッセージ
\echo ''
\echo '===================================='
\echo 'Demo users created successfully!'
\echo '===================================='
\echo ''
\echo 'Login credentials:'
\echo '------------------------------------'
\echo 'Email: admin@cqox.local'
\echo 'Password: admin123'
\echo 'Roles: admin, analyst, viewer'
\echo ''
\echo 'Email: analyst@cqox.local'
\echo 'Password: analyst123'
\echo 'Roles: analyst, viewer'
\echo ''
\echo 'Email: viewer@cqox.local'
\echo 'Password: viewer123'
\echo 'Roles: viewer'
\echo '===================================='

