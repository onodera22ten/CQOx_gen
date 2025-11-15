-- =====================================================
-- Migration 004: v1 DECISIONS and Column Mapping Tables
-- =====================================================
-- Purpose: DecisionCard（Δ¥ + Go/Canary/Hold判定）とカラムマッピング
-- Author: CQOx Team
-- Date: 2025-01-15
-- =====================================================

-- =====================================================
-- 1. Column Mapping Profiles テーブル
-- =====================================================

CREATE TABLE IF NOT EXISTS column_mapping_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,                     -- 例: "KARTE Push通知 v1"
    source_system VARCHAR(100),                     -- 例: "KARTE", "Salesforce"
    mapping_json JSONB NOT NULL,                    -- マッピング定義
    version VARCHAR(20) DEFAULT '1.0',
    tenant_id UUID,                                 -- マルチテナント対応
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT fk_column_mapping_tenant FOREIGN KEY (tenant_id)
        REFERENCES tenants(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_column_mapping_profiles_tenant ON column_mapping_profiles(tenant_id);
CREATE INDEX idx_column_mapping_profiles_source ON column_mapping_profiles(source_system);
CREATE INDEX idx_column_mapping_profiles_name ON column_mapping_profiles(name);

-- Auto-update updated_at
CREATE TRIGGER update_column_mapping_profiles_updated_at
    BEFORE UPDATE ON column_mapping_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row-Level Security
ALTER TABLE column_mapping_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_column_mapping_profiles ON column_mapping_profiles
    USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID);

-- =====================================================
-- 2. DECISIONS テーブル（DecisionCard）
-- =====================================================

CREATE TABLE IF NOT EXISTS decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID NOT NULL,
    scenario_id UUID,                               -- ScenarioSpec ID（オプション）
    scenario_name VARCHAR(500) NOT NULL,            -- 例: "Push通知 最適化 #1"

    -- Δ¥関連
    delta_yen DECIMAL(15, 2) NOT NULL,              -- S1 - S0 の期待Δ¥（円）
    delta_yen_ci_low DECIMAL(15, 2),                -- 95% 信頼区間下限
    delta_yen_ci_high DECIMAL(15, 2),               -- 95% 信頼区間上限
    delta_yen_std DECIMAL(15, 2),                   -- Δ¥の標準偏差

    -- 判定
    verdict VARCHAR(20) NOT NULL,                   -- "Go" | "Canary" | "Hold"
    reason TEXT,                                    -- Hold/Canary理由

    -- メタデータ（マーケティング用）
    channel VARCHAR(100),                           -- チャネル: "アプリPush", "Email", etc.
    segment VARCHAR(200),                           -- セグメント: "RFM High-Value", etc.

    -- 品質スコア
    quality_scores JSONB,                           -- { overlap_coverage, iv_f_stat, rd_mccrary_p, balance_score }

    -- 再現性のため保存
    scenario_spec JSONB,                            -- S0/S1のポリシー定義
    estimator_results JSONB,                        -- 使用した推定器の詳細結果

    -- Audit
    tenant_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT fk_decisions_policy FOREIGN KEY (policy_id)
        REFERENCES policies(id) ON DELETE CASCADE,
    CONSTRAINT fk_decisions_tenant FOREIGN KEY (tenant_id)
        REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT chk_verdict CHECK (verdict IN ('Go', 'Canary', 'Hold'))
);

-- Indexes
CREATE INDEX idx_decisions_policy_id ON decisions(policy_id);
CREATE INDEX idx_decisions_tenant_id ON decisions(tenant_id);
CREATE INDEX idx_decisions_verdict ON decisions(verdict);
CREATE INDEX idx_decisions_delta_yen ON decisions(delta_yen DESC);  -- Δ¥ランキング用
CREATE INDEX idx_decisions_created_at ON decisions(created_at DESC);
CREATE INDEX idx_decisions_channel ON decisions(channel);
CREATE INDEX idx_decisions_segment ON decisions(segment);

-- GIN index for JSONB
CREATE INDEX idx_decisions_quality_scores ON decisions USING GIN (quality_scores);
CREATE INDEX idx_decisions_scenario_spec ON decisions USING GIN (scenario_spec);

-- Row-Level Security
ALTER TABLE decisions ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_decisions ON decisions
    USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID);

-- =====================================================
-- 3. Audit Log for Decisions
-- =====================================================

CREATE TABLE IF NOT EXISTS decision_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,                    -- 'viewed', 'exported', 'executed'
    user_id UUID NOT NULL,
    metadata JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_decision_audit_decision FOREIGN KEY (decision_id)
        REFERENCES decisions(id) ON DELETE CASCADE,
    CONSTRAINT fk_decision_audit_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_decision_audit_decision_id ON decision_audit_log(decision_id);
CREATE INDEX idx_decision_audit_user_id ON decision_audit_log(user_id);
CREATE INDEX idx_decision_audit_created_at ON decision_audit_log(created_at DESC);

-- =====================================================
-- 4. Sample Data（開発用）
-- =====================================================

-- Sample Column Mapping Profile
INSERT INTO column_mapping_profiles (name, source_system, mapping_json, version)
VALUES (
    'KARTE Push通知 v1',
    'KARTE',
    '{
        "y": "revenue",
        "treatment": "received_push",
        "unit_id": "user_id",
        "time": "event_timestamp",
        "propensity_score": "ps_model_v1",
        "features": ["age", "gender", "prefecture", "rfm_segment"]
    }'::jsonb,
    '1.0'
) ON CONFLICT DO NOTHING;

-- =====================================================
-- 5. Helper Functions
-- =====================================================

-- Function: Get Decision Summary
CREATE OR REPLACE FUNCTION get_decision_summary(
    p_tenant_id UUID,
    p_period_days INTEGER DEFAULT 7
)
RETURNS TABLE (
    total_decisions BIGINT,
    go_count BIGINT,
    canary_count BIGINT,
    hold_count BIGINT,
    avg_delta_yen DECIMAL,
    best_delta_yen DECIMAL,
    worst_delta_yen DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT AS total_decisions,
        COUNT(*) FILTER (WHERE verdict = 'Go')::BIGINT AS go_count,
        COUNT(*) FILTER (WHERE verdict = 'Canary')::BIGINT AS canary_count,
        COUNT(*) FILTER (WHERE verdict = 'Hold')::BIGINT AS hold_count,
        AVG(delta_yen)::DECIMAL AS avg_delta_yen,
        MAX(delta_yen)::DECIMAL AS best_delta_yen,
        MIN(delta_yen)::DECIMAL AS worst_delta_yen
    FROM decisions
    WHERE tenant_id = p_tenant_id
      AND created_at >= NOW() - (p_period_days || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Migration Complete
-- =====================================================
