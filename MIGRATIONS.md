# Database Migrations Applied

## 2025-11-21: Complete Schema Unification

### Problem
- Multiple ORM definitions existed: `cqox/db/models.py` (old v1) and `cqox/database/models.py` (new v2)
- Database schema didn't match ORM models, causing "column does not exist" errors
- Alembic migrations incomplete

### Solution
1. **Unified ORM models** in `cqox/database/models.py`:
   - Added `User` model from `cqox/db/models.py`
   - All models now use UUID primary keys
   - Consistent JSON column types (not JSONB)

2. **Rebuilt database** from clean state:
   - Applied Alembic migrations: `001` (initial schema) + `002` (users table)
   - Created remaining tables via `cqox/database/connection.py::init_db()`
   - Final schema matches ORM perfectly

3. **Tables created**:
   - `users` - Authentication (UUID id, email, hashed_password, role, tenant_id)
   - `datasets` - Data uploads
   - `policies` - Marketing policies
   - `decisions` - Go/Canary/Hold decisions with Δ¥
   - `analysis_runs` - Causal inference execution tracking
   - `model_runs` - Model training runs
   - `diagnostics` - Quality diagnostics
   - `scenarios` - Portfolio scenarios
   - `column_mapping_profiles` - Column mapping configs

## 2025-11-21 (OLD): Add missing tables for Decision Console

**NOTE: This approach was replaced by complete schema unification above**

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
