-- Migration 001: Base Schema
-- Core tables for multi-tenant CQOx application

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_crypto";

-- ============================================================================
-- MULTI-TENANCY TABLES
-- ============================================================================

-- Tenants table
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,

    -- Plan and limits
    plan VARCHAR(50) NOT NULL DEFAULT 'free', -- free, pro, enterprise
    max_datasets INTEGER NOT NULL DEFAULT 10,
    max_models INTEGER NOT NULL DEFAULT 50,
    max_storage_gb INTEGER NOT NULL DEFAULT 10,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, suspended, deleted

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_status ON tenants(status);


-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,

    -- Authentication
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255), -- NULL for OAuth-only users
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,

    -- Profile
    full_name VARCHAR(255),
    avatar_url TEXT,

    -- Authorization
    roles VARCHAR(50)[] NOT NULL DEFAULT ARRAY['viewer'], -- admin, analyst, viewer

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, suspended, deleted

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,

    CONSTRAINT users_tenant_id_fk FOREIGN KEY (tenant_id)
        REFERENCES tenants(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);


-- ============================================================================
-- DATA MANAGEMENT TABLES
-- ============================================================================

-- Datasets table
CREATE TABLE IF NOT EXISTS datasets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,

    -- Metadata
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Schema
    schema JSONB NOT NULL, -- column definitions
    schema_version VARCHAR(20) NOT NULL DEFAULT '1.0.0',

    -- Storage
    storage_location TEXT, -- S3 path or file path
    file_format VARCHAR(50) NOT NULL DEFAULT 'csv', -- csv, parquet, json
    size_bytes BIGINT NOT NULL DEFAULT 0,
    row_count INTEGER NOT NULL DEFAULT 0,

    -- Column mapping
    treatment_column VARCHAR(100),
    outcome_column VARCHAR(100),
    feature_columns JSONB, -- array of column names

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'uploading', -- uploading, ready, processing, failed

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,

    CONSTRAINT datasets_tenant_id_fk FOREIGN KEY (tenant_id)
        REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT datasets_created_by_fk FOREIGN KEY (created_by)
        REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_datasets_tenant_id ON datasets(tenant_id);
CREATE INDEX idx_datasets_status ON datasets(status);
CREATE INDEX idx_datasets_created_at ON datasets(created_at DESC);

-- Row-level security
ALTER TABLE datasets ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_datasets ON datasets
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- Models table (causal models)
CREATE TABLE IF NOT EXISTS models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    dataset_id UUID NOT NULL,

    -- Model metadata
    name VARCHAR(255) NOT NULL,
    description TEXT,
    estimator_type VARCHAR(50) NOT NULL, -- s_learner, t_learner, x_learner, dr_learner, causal_forest

    -- Configuration
    hyperparameters JSONB,
    features JSONB, -- array of feature names used

    -- Training
    training_status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, training, completed, failed
    training_metrics JSONB,

    -- Storage
    artifact_location TEXT, -- S3 path to saved model

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    trained_at TIMESTAMPTZ,
    created_by UUID,

    CONSTRAINT models_tenant_id_fk FOREIGN KEY (tenant_id)
        REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT models_dataset_id_fk FOREIGN KEY (dataset_id)
        REFERENCES datasets(id) ON DELETE RESTRICT,
    CONSTRAINT models_created_by_fk FOREIGN KEY (created_by)
        REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_models_tenant_id ON models(tenant_id);
CREATE INDEX idx_models_dataset_id ON models(dataset_id);
CREATE INDEX idx_models_status ON models(training_status);
CREATE INDEX idx_models_created_at ON models(created_at DESC);

-- Row-level security
ALTER TABLE models ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_models ON models
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ============================================================================
-- JOB TRACKING TABLES
-- ============================================================================

-- Jobs table (for async operations)
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    user_id UUID,

    -- Job identification
    job_type VARCHAR(50) NOT NULL, -- train_model, run_diagnostic, generate_visualization, etc.
    idempotency_key VARCHAR(255) UNIQUE, -- for deduplication

    -- References
    resource_type VARCHAR(50), -- dataset, model, policy
    resource_id UUID,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, running, completed, failed, cancelled
    progress FLOAT DEFAULT 0.0 CHECK (progress >= 0 AND progress <= 100),

    -- Execution
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Results
    result JSONB,
    error_message TEXT,
    error_traceback TEXT,

    -- Metadata
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT jobs_tenant_id_fk FOREIGN KEY (tenant_id)
        REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT jobs_user_id_fk FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_jobs_tenant_id ON jobs(tenant_id);
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_job_type ON jobs(job_type);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_jobs_idempotency_key ON jobs(idempotency_key) WHERE idempotency_key IS NOT NULL;

-- Row-level security
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_jobs ON jobs
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);


-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER update_tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_datasets_updated_at
    BEFORE UPDATE ON datasets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_models_updated_at
    BEFORE UPDATE ON models
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- SEED DATA
-- ============================================================================

-- Create default tenant
INSERT INTO tenants (id, name, slug, plan, status)
VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    'Default Tenant',
    'default',
    'enterprise',
    'active'
) ON CONFLICT (id) DO NOTHING;

-- Create demo user
INSERT INTO users (id, tenant_id, email, full_name, roles, status)
VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    '00000000-0000-0000-0000-000000000001'::UUID,
    'demo@cqox.com',
    'Demo User',
    ARRAY['admin'],
    'active'
) ON CONFLICT (id) DO NOTHING;


-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE tenants IS 'Multi-tenant organizations';
COMMENT ON TABLE users IS 'Application users with RBAC';
COMMENT ON TABLE datasets IS 'Uploaded datasets for causal analysis';
COMMENT ON TABLE models IS 'Trained causal inference models';
COMMENT ON TABLE jobs IS 'Async job tracking with idempotency';
