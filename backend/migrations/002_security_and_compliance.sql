-- Security and Compliance Tables
-- Migration: 002_security_and_compliance.sql

-- Users table (for authentication)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    password_hash VARCHAR(255),  -- bcrypt hash
    roles TEXT[] DEFAULT ARRAY['viewer'],  -- admin, analyst, viewer
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,  -- Soft delete for GDPR
    anonymized BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NOT NULL;


-- User sessions (for JWT token tracking)
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255),  -- SHA-256 hash
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT
);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);


-- GDPR Consent Management
CREATE TABLE IF NOT EXISTS user_consents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    consent_type VARCHAR(50) NOT NULL,  -- essential, analytics, marketing, data_sharing
    granted BOOLEAN NOT NULL,
    granted_at TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT
);

CREATE INDEX idx_user_consents_user_id ON user_consents(user_id);
CREATE INDEX idx_user_consents_type ON user_consents(consent_type);


-- GDPR Data Access Logs (Article 30)
CREATE TABLE IF NOT EXISTS data_access_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    accessed_by VARCHAR(255) NOT NULL,  -- User ID or system name
    data_category VARCHAR(50) NOT NULL,  -- user_profile, model_data, etc.
    action VARCHAR(50) NOT NULL,  -- read, write, delete, export
    timestamp TIMESTAMP DEFAULT NOW(),
    ip_address VARCHAR(45),
    reason TEXT
);

CREATE INDEX idx_data_access_logs_user_id ON data_access_logs(user_id);
CREATE INDEX idx_data_access_logs_timestamp ON data_access_logs(timestamp);
CREATE INDEX idx_data_access_logs_action ON data_access_logs(action);


-- Analytics Events (for retention policy)
CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_analytics_events_created_at ON analytics_events(created_at);
CREATE INDEX idx_analytics_events_type ON analytics_events(event_type);


-- Diagnostic Runs (with retention policy)
CREATE TABLE IF NOT EXISTS diagnostic_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_run_id UUID,
    diagnostic_type VARCHAR(100) NOT NULL,
    results JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_diagnostic_runs_created_at ON diagnostic_runs(created_at);


-- Update existing tables to support GDPR
-- Add user_id to model_runs if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'model_runs' AND column_name = 'user_id'
    ) THEN
        ALTER TABLE model_runs ADD COLUMN user_id UUID REFERENCES users(id) ON DELETE SET NULL;
        CREATE INDEX idx_model_runs_user_id ON model_runs(user_id);
    END IF;
END $$;


-- Add user_id to policies if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'policies' AND column_name = 'user_id'
    ) THEN
        ALTER TABLE policies ADD COLUMN user_id UUID REFERENCES users(id) ON DELETE SET NULL;
        CREATE INDEX idx_policies_user_id ON policies(user_id);
    END IF;
END $$;


-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Trigger for users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- Comments for documentation
COMMENT ON TABLE users IS 'User accounts with authentication credentials';
COMMENT ON TABLE user_consents IS 'GDPR consent records (Article 7)';
COMMENT ON TABLE data_access_logs IS 'Audit trail for data access (Article 30)';
COMMENT ON TABLE analytics_events IS 'Analytics events with 1-year retention';
COMMENT ON TABLE diagnostic_runs IS 'Diagnostic run results with 2-year retention';
