# Database Migrations Applied Manually

## 2025-11-21: Add missing tables for Decision Console

Created the following tables that were missing from the initial migration:

### decisions table
```sql
CREATE TABLE IF NOT EXISTS decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    policy_id UUID,
    dataset_id UUID,
    verdict VARCHAR(50),
    delta_yen NUMERIC,
    delta_yen_ci_low NUMERIC,
    delta_yen_ci_high NUMERIC,
    confidence_score NUMERIC,
    risk_score NUMERIC,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_decisions_tenant_id ON decisions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_decisions_created_at ON decisions(created_at);
```

### analysis_runs table
```sql
CREATE TABLE IF NOT EXISTS analysis_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    policy_id UUID,
    dataset_id UUID,
    estimators TEXT[],
    treatment_col VARCHAR(255),
    outcome_col VARCHAR(255),
    feature_cols TEXT[],
    scenario_spec JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    progress NUMERIC DEFAULT 0.0,
    delta_yen NUMERIC,
    delta_yen_ci_low NUMERIC,
    delta_yen_ci_high NUMERIC,
    verdict VARCHAR(50),
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_tenant_id ON analysis_runs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_status ON analysis_runs(status);
```

These tables are required for:
- Decision Console dashboard to display analysis results
- Causal Design analysis workflow to store run results
