import { api } from '../../utils/api'

export type Verdict = 'go' | 'canary' | 'hold'

// ==================== 修正.pdf仕様準拠 ====================

export interface ConsoleSummaryKPIs {
  total_delta_yen: number
  avg_delta_yen: number
  mean_cas: number | null
  portfolio_cvar_10: number
}

export interface ConsoleTrendPoint {
  week: string  // ISO week format: "2025-W48"
  delta_yen: number
}

export interface ConsoleSegmentPortfolio {
  segment_label: string
  population: number
  total_delta_yen: number
  policy_count: number
  mean_cas: number | null
}

export interface ConsoleChannelPerformance {
  channel: string
  total_delta_yen: number
  roi: number | null
}

export interface ConsoleDecisionCard {
  id: string
  policy_name: string
  dataset_name: string
  channel: string | null
  segment: string | null
  delta_yen: number
  roi: number | null
  cas: number | null
  risk: number | null
  verdict: string
  decided_at: string
}

export interface DecisionConsoleSummaryV2 {
  window: {
    start: string
    end: string
  }
  kpis: ConsoleSummaryKPIs
  trend: ConsoleTrendPoint[]
  segment_portfolio: ConsoleSegmentPortfolio[]
  channel_performance: ConsoleChannelPerformance[]
  decision_cards: ConsoleDecisionCard[]
}

// ==================== 既存API（後方互換性） ====================

export interface TrendPoint {
  bucket: string
  delta_yen: number
  target_yen?: number | null
}

export interface SegmentPortfolioPoint {
  segment_id: string
  segment_label: string
  population: number
  total_delta_yen: number
  policy_count: number
  mean_cas: number | null
}

export interface ChannelPerformancePoint {
  channel: string
  total_delta_yen: number
  roi: number | null
}

export interface DecisionPolicyRow {
  id: string
  dataset_label: string
  policy_name: string
  channel: string | null
  segment_label: string | null
  delta_yen: number
  roi: number | null
  cas_score: number | null
  risk_score: number | null
  verdict: Verdict | string
  start_date: string
  end_date: string
  decided_at: string
}

export interface DecisionConsoleSummary {
  total_delta_yen: number
  avg_delta_yen_per_policy: number
  mean_cas: number | null
  cvar_yen_p10: number | null
  trend: TrendPoint[]
  segment_portfolio: SegmentPortfolioPoint[]
  channel_performance: ChannelPerformancePoint[]
  decisions: DecisionPolicyRow[]
}

export const decisionConsoleAPI = {
  // 修正.pdf仕様準拠エンドポイント
  summary: async (params: { window?: '14d' | '28d' | '56d' }): Promise<DecisionConsoleSummaryV2> => {
    const window = params.window || '28d'
    return await api.get<DecisionConsoleSummaryV2>(`/api/v1/console/summary?window=${window}`)
  },

  // 既存エンドポイント（後方互換性）
  overview: async (params: { from: string; to: string; locale?: string }): Promise<DecisionConsoleSummary> => {
    const query = new URLSearchParams()
    query.append('from', params.from)
    query.append('to', params.to)
    if (params.locale) query.append('locale', params.locale)
    return await api.get<DecisionConsoleSummary>(`/api/v1/decision-console/overview?${query.toString()}`)
  }
}
