-- v2 API用テーブル

-- Offline Policy Runs
CREATE TABLE IF NOT EXISTS offline_policy_runs (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    policy_config_id UUID NOT NULL,
    objective VARCHAR(50),
    risk_metric VARCHAR(50),
    ope_method VARCHAR(50),
    risk_aversion FLOAT DEFAULT 0.5,
    dataset_id UUID,
    propensity_model_id UUID,
    outcome_model_id UUID,
    n_candidates INTEGER DEFAULT 100,
    n_bootstrap INTEGER DEFAULT 100,
    status VARCHAR(50) DEFAULT 'pending',
    frontier JSONB,
    best_policy JSONB,
    evaluation_metrics JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Experiment Designs
CREATE TABLE IF NOT EXISTS experiment_designs (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    policy_id UUID,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    outcome_type VARCHAR(50) NOT NULL,
    outcome_variable VARCHAR(255),
    baseline_mean FLOAT,
    baseline_std FLOAT,
    baseline_proportion FLOAT,
    minimum_detectable_effect FLOAT NOT NULL,
    alpha FLOAT DEFAULT 0.05,
    power FLOAT DEFAULT 0.80,
    arms JSONB NOT NULL,
    sample_size_per_arm INTEGER,
    total_sample_size INTEGER,
    estimated_runtime_days FLOAT,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_offline_policy_runs_tenant ON offline_policy_runs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_offline_policy_runs_policy ON offline_policy_runs(policy_config_id);
CREATE INDEX IF NOT EXISTS idx_experiment_designs_tenant ON experiment_designs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_experiment_designs_policy ON experiment_designs(policy_id);
