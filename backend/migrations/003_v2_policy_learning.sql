-- Migration 003: v2 Policy Learning Tables
-- Policy Lab, Recourse, and Experiment Design

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- POLICY LAB TABLES
-- ============================================================================

-- Policy configurations
CREATE TABLE IF NOT EXISTS policy_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Policy definition
    policy_type VARCHAR(50) NOT NULL, -- threshold, multi_arm, linear, tree, custom
    treatment_variable VARCHAR(100) NOT NULL,
    outcome_variable VARCHAR(100) NOT NULL,
    features JSONB NOT NULL, -- array of feature names

    -- Policy parameters
    threshold FLOAT,
    coefficients JSONB, -- dict of feature -> coefficient
    treatment_mapping JSONB, -- dict of conditions -> treatment values

    -- Constraints
    budget_constraint FLOAT,
    coverage_constraint FLOAT, -- fraction of population to treat
    fairness_constraint JSONB,

    -- References
    dataset_id UUID NOT NULL,
    model_id UUID,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,
    status VARCHAR(20) NOT NULL DEFAULT 'draft', -- draft, active, archived

    CONSTRAINT policy_configs_tenant_id_fk FOREIGN KEY (tenant_id)
        REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT policy_configs_dataset_id_fk FOREIGN KEY (dataset_id)
        REFERENCES datasets(id) ON DELETE RESTRICT
);

-- Indexes for policy_configs
CREATE INDEX idx_policy_configs_tenant_id ON policy_configs(tenant_id);
CREATE INDEX idx_policy_configs_dataset_id ON policy_configs(dataset_id);
CREATE INDEX idx_policy_configs_status ON policy_configs(status);
CREATE INDEX idx_policy_configs_created_at ON policy_configs(created_at DESC);

-- Row-level security for policy_configs
ALTER TABLE policy_configs ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_policy_configs ON policy_configs
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);


-- Offline policy learning runs
CREATE TABLE IF NOT EXISTS offline_policy_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    policy_config_id UUID NOT NULL,

    -- Learning configuration
    objective VARCHAR(50) NOT NULL, -- uplift, delta_revenue, roi, ate, att
    risk_metric VARCHAR(50) NOT NULL, -- std, var, cvar, worst_case
    ope_method VARCHAR(20) NOT NULL, -- DR, IPW, DM, SWITCH, DR_OS
    risk_aversion FLOAT NOT NULL DEFAULT 0.0 CHECK (risk_aversion >= 0 AND risk_aversion <= 1),

    -- Results
    frontier JSONB, -- array of FrontierPoint objects
    best_policy JSONB, -- PolicyConfig object
    selected_point JSONB, -- FrontierPoint object

    -- Evaluation metrics
    estimated_value FLOAT,
    estimated_risk FLOAT,
    confidence_interval JSONB, -- [lower, upper]
    bias_estimate FLOAT,
    variance_estimate FLOAT,

    -- Execution configuration
    dataset_id UUID NOT NULL,
    propensity_model_id UUID,
    outcome_model_id UUID,
    n_candidates INTEGER NOT NULL DEFAULT 100,
    n_bootstrap INTEGER NOT NULL DEFAULT 1000,

    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, running, completed, failed
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    CONSTRAINT offline_runs_tenant_id_fk FOREIGN KEY (tenant_id)
        REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT offline_runs_policy_config_id_fk FOREIGN KEY (policy_config_id)
        REFERENCES policy_configs(id) ON DELETE CASCADE,
    CONSTRAINT offline_runs_dataset_id_fk FOREIGN KEY (dataset_id)
        REFERENCES datasets(id) ON DELETE RESTRICT
);

-- Indexes for offline_policy_runs
CREATE INDEX idx_offline_runs_tenant_id ON offline_policy_runs(tenant_id);
CREATE INDEX idx_offline_runs_policy_config_id ON offline_policy_runs(policy_config_id);
CREATE INDEX idx_offline_runs_status ON offline_policy_runs(status);
CREATE INDEX idx_offline_runs_created_at ON offline_policy_runs(created_at DESC);

-- Row-level security
ALTER TABLE offline_policy_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_offline_runs ON offline_policy_runs
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);


-- ============================================================================
-- EXPERIMENT DESIGN TABLES
-- ============================================================================

-- Experiment designs (A/B tests)
CREATE TABLE IF NOT EXISTS experiment_designs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Treatment configuration
    treatment_variable VARCHAR(100) NOT NULL,
    arms JSONB NOT NULL, -- array of ExperimentArm objects

    -- Primary metric
    primary_outcome VARCHAR(100) NOT NULL,
    outcome_type VARCHAR(20) NOT NULL DEFAULT 'continuous', -- continuous, binary, count

    -- Sample size calculation inputs
    baseline_mean FLOAT,
    baseline_proportion FLOAT, -- for binary outcomes
    minimum_detectable_effect FLOAT NOT NULL,
    alpha FLOAT NOT NULL DEFAULT 0.05,
    power FLOAT NOT NULL DEFAULT 0.80,

    -- Calculated sample sizes
    required_sample_size_per_arm INTEGER,
    total_sample_size INTEGER,
    expected_runtime_days FLOAT,

    -- Stratification
    stratify_by JSONB, -- array of feature names

    -- Stopping rules
    early_stopping BOOLEAN NOT NULL DEFAULT FALSE,
    sequential_testing BOOLEAN NOT NULL DEFAULT FALSE,

    -- References
    dataset_id UUID, -- for power analysis from historical data
    policy_config_id UUID, -- which policy to test

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'design', -- design, running, completed, stopped

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    CONSTRAINT exp_designs_tenant_id_fk FOREIGN KEY (tenant_id)
        REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT exp_designs_dataset_id_fk FOREIGN KEY (dataset_id)
        REFERENCES datasets(id) ON DELETE SET NULL,
    CONSTRAINT exp_designs_policy_config_id_fk FOREIGN KEY (policy_config_id)
        REFERENCES policy_configs(id) ON DELETE SET NULL
);

-- Indexes for experiment_designs
CREATE INDEX idx_exp_designs_tenant_id ON experiment_designs(tenant_id);
CREATE INDEX idx_exp_designs_status ON experiment_designs(status);
CREATE INDEX idx_exp_designs_created_at ON experiment_designs(created_at DESC);

-- Row-level security
ALTER TABLE experiment_designs ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_exp_designs ON experiment_designs
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);


-- Experiment results (time-series)
CREATE TABLE IF NOT EXISTS experiment_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL,
    tenant_id UUID NOT NULL,

    -- Results by arm
    arm_results JSONB NOT NULL, -- dict of arm_name -> metrics
    primary_metric_values JSONB NOT NULL, -- dict of arm_name -> value

    -- Statistical significance
    statistical_significance BOOLEAN,
    p_value FLOAT,
    confidence_intervals JSONB, -- dict of arm_name -> [lower, upper]

    -- Sequential testing
    current_sample_size INTEGER NOT NULL,
    stop_early BOOLEAN NOT NULL DEFAULT FALSE,
    stop_reason TEXT,

    -- Timestamp
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT exp_results_experiment_id_fk FOREIGN KEY (experiment_id)
        REFERENCES experiment_designs(id) ON DELETE CASCADE,
    CONSTRAINT exp_results_tenant_id_fk FOREIGN KEY (tenant_id)
        REFERENCES tenants(id) ON DELETE CASCADE
);

-- Indexes for experiment_results
CREATE INDEX idx_exp_results_experiment_id ON experiment_results(experiment_id);
CREATE INDEX idx_exp_results_tenant_id ON experiment_results(tenant_id);
CREATE INDEX idx_exp_results_updated_at ON experiment_results(updated_at DESC);

-- Row-level security
ALTER TABLE experiment_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_exp_results ON experiment_results
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);


-- ============================================================================
-- AUDIT LOG FOR V2 OPERATIONS
-- ============================================================================

-- Audit log for policy operations (GDPR compliance)
CREATE TABLE IF NOT EXISTS policy_audit_log (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL,
    user_id UUID,

    -- Operation details
    operation VARCHAR(50) NOT NULL, -- create_policy, run_learning, generate_recourse, etc.
    resource_type VARCHAR(50) NOT NULL, -- policy_config, offline_run, recourse, experiment
    resource_id UUID,

    -- Request details
    request_method VARCHAR(10),
    request_path TEXT,
    request_body JSONB,

    -- Response details
    response_status INTEGER,
    response_body JSONB,

    -- Metadata
    ip_address INET,
    user_agent TEXT,
    correlation_id UUID,

    -- Timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT policy_audit_tenant_id_fk FOREIGN KEY (tenant_id)
        REFERENCES tenants(id) ON DELETE CASCADE
);

-- Indexes for audit log
CREATE INDEX idx_policy_audit_tenant_id ON policy_audit_log(tenant_id);
CREATE INDEX idx_policy_audit_user_id ON policy_audit_log(user_id);
CREATE INDEX idx_policy_audit_operation ON policy_audit_log(operation);
CREATE INDEX idx_policy_audit_created_at ON policy_audit_log(created_at DESC);

-- Partition by month for scalability (TimescaleDB hypertable)
-- SELECT create_hypertable('policy_audit_log', 'created_at', if_not_exists => TRUE);


-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_policy_configs_updated_at
    BEFORE UPDATE ON policy_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- SEED DATA (Optional, for development)
-- ============================================================================

-- Insert default tenant (if not exists)
INSERT INTO tenants (id, name, status, created_at)
VALUES ('00000000-0000-0000-0000-000000000001'::UUID, 'Default Tenant', 'active', NOW())
ON CONFLICT (id) DO NOTHING;


-- ============================================================================
-- GRANTS (Adjust based on your user roles)
-- ============================================================================

-- Grant permissions to application user
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO cqox_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO cqox_app_user;


-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE policy_configs IS 'v2 Policy configurations for treatment assignment';
COMMENT ON TABLE offline_policy_runs IS 'v2 Offline policy learning execution results';
COMMENT ON TABLE experiment_designs IS 'v2 A/B test experiment designs';
COMMENT ON TABLE experiment_results IS 'v2 Time-series experiment results';
COMMENT ON TABLE policy_audit_log IS 'v2 Audit log for GDPR compliance and security';
