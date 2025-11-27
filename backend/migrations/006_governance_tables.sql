-- Module D: Governance tables

CREATE TABLE IF NOT EXISTS governance_rules (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rule_type VARCHAR(50) NOT NULL,
    severity VARCHAR(32) DEFAULT 'medium',
    action VARCHAR(32) DEFAULT 'warn',
    threshold_value FLOAT,
    config JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS governance_violations (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    rule_id UUID REFERENCES governance_rules(id),
    violation_type VARCHAR(50) NOT NULL,
    severity VARCHAR(32) NOT NULL,
    details JSONB,
    status VARCHAR(32) DEFAULT 'open',
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_governance_rules_tenant ON governance_rules(tenant_id);
CREATE INDEX IF NOT EXISTS idx_governance_violations_tenant ON governance_violations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_governance_violations_rule ON governance_violations(rule_id);
