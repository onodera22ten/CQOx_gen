-- CQOx Database Initialization Script
-- This script runs automatically when the PostgreSQL container starts for the first time

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Create datasets table
CREATE TABLE IF NOT EXISTS datasets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_size BIGINT,
    row_count INTEGER,
    column_count INTEGER,
    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    status VARCHAR(50) DEFAULT 'uploaded'
);

-- Create index for datasets
CREATE INDEX IF NOT EXISTS idx_datasets_user_id ON datasets(user_id);
CREATE INDEX IF NOT EXISTS idx_datasets_status ON datasets(status);

-- Create analyses table for tracking causal analyses
CREATE TABLE IF NOT EXISTS analyses (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER REFERENCES datasets(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    estimator_type VARCHAR(50) NOT NULL,
    treatment_col VARCHAR(255),
    outcome_col VARCHAR(255),
    feature_cols TEXT[],
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    results JSONB,
    error_message TEXT
);

-- Create index for analyses
CREATE INDEX IF NOT EXISTS idx_analyses_dataset_id ON analyses(dataset_id);
CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_status ON analyses(status);

-- Create decisions table for tracking Go/Canary/Hold verdicts
CREATE TABLE IF NOT EXISTS decisions (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES analyses(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    policy_name VARCHAR(255),
    verdict VARCHAR(20) NOT NULL,  -- 'Go', 'Canary', 'Hold'
    delta_yen NUMERIC(15, 2),
    delta_yen_ci_low NUMERIC(15, 2),
    delta_yen_ci_high NUMERIC(15, 2),
    cas_score NUMERIC(3, 2),
    risk_score NUMERIC(3, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Create index for decisions
CREATE INDEX IF NOT EXISTS idx_decisions_analysis_id ON decisions(analysis_id);
CREATE INDEX IF NOT EXISTS idx_decisions_user_id ON decisions(user_id);
CREATE INDEX IF NOT EXISTS idx_decisions_verdict ON decisions(verdict);
CREATE INDEX IF NOT EXISTS idx_decisions_created_at ON decisions(created_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for users table
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default admin user (password will be hashed by backend on first run)
-- Default password: admin_password_change_me (to be hashed)
-- This is a placeholder - actual user creation should be done by the backend
INSERT INTO users (email, password_hash, role)
VALUES ('admin@cqox.local', '$2b$12$placeholder_hash_to_be_replaced_by_backend', 'admin')
ON CONFLICT (email) DO NOTHING;

-- Create view for decision summary
CREATE OR REPLACE VIEW decision_summary AS
SELECT
    d.id,
    d.policy_name,
    d.verdict,
    d.delta_yen,
    d.cas_score,
    d.created_at,
    u.email as user_email,
    a.estimator_type
FROM decisions d
JOIN users u ON d.user_id = u.id
JOIN analyses a ON d.analysis_id = a.id
ORDER BY d.created_at DESC;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cqox;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cqox;
