/**
 * v1 API Client for DecisionCard
 *
 * Δ¥ + Go/Canary/Hold判定のAPI
 */
import { api } from '../../utils/api';

export interface QualityScores {
  overlap_coverage?: number;
  iv_f_stat?: number;
  rd_mccrary_p?: number;
  balance_score?: number;
}

export interface DecisionCard {
  id: string;
  policy_id: string;
  scenario_id?: string;
  scenario_name: string;
  delta_yen: number;
  delta_yen_ci_low?: number;
  delta_yen_ci_high?: number;
  delta_yen_std?: number;
  verdict: 'Go' | 'Canary' | 'Hold';
  reason?: string;
  channel?: string;
  segment?: string;
  quality_scores?: QualityScores;
  scenario_spec?: any;
  estimator_results?: any;
  created_at: string;
}

export interface DecisionCardList {
  total: number;
  items: DecisionCard[];
  page: number;
  page_size: number;
}

export interface DeltaYenSummary {
  period_days: number;
  total_decisions: number;
  verdict_distribution: VerdictDistribution;
  avg_delta_yen: number;
  max_delta_yen: number;
  min_delta_yen: number;
  best_scenario?: DecisionCard;
  history: DeltaYenHistoryItem[];
}

export interface DeltaYenHistoryItem {
  week: string;
  delta_yen: number;
  decision_count: number;
}

export interface VerdictDistribution {
  go: number;
  canary: number;
  hold: number;
  total: number;
}

export const decisionsApi = {
  /**
   * DecisionCard一覧取得（Δ¥ランキング順）
   */
  async list(params?: {
    sort_by?: 'delta_yen' | 'created_at';
    order?: 'asc' | 'desc';
    verdict?: 'Go' | 'Canary' | 'Hold';
    channel?: string;
    segment?: string;
    page?: number;
    page_size?: number;
  }): Promise<DecisionCardList> {
    // paramsをURLクエリ文字列に変換
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, String(value));
        }
      });
    }
    const queryString = queryParams.toString();
    const url = `/api/v1/results${queryString ? `?${queryString}` : ''}`;
    return await api.get<DecisionCardList>(url);
  },

  /**
   * DecisionCard詳細取得
   */
  async get(id: string): Promise<DecisionCard> {
    return await api.get<DecisionCard>(`/api/v1/results/${id}`);
  },

  /**
   * Δ¥サマリー取得（Decision Console用）
   */
  async getSummary(period_days: number = 7): Promise<DeltaYenSummary> {
    return await api.get<DeltaYenSummary>(`/api/v1/console/delta-yen-summary?period_days=${period_days}`);
  },

  /**
   * Δ¥履歴取得（週次）
   */
  async getHistory(params?: {
    period?: 'week' | 'month';
    weeks?: number;
  }): Promise<DeltaYenHistoryItem[]> {
    const queryParams = new URLSearchParams();
    if (params) {
      if (params.period) queryParams.append('period', params.period);
      if (params.weeks) queryParams.append('weeks', String(params.weeks));
    }
    const queryString = queryParams.toString();
    const url = `/api/v1/console/delta-yen-history${queryString ? `?${queryString}` : ''}`;
    return await api.get<DeltaYenHistoryItem[]>(url);
  },

  /**
   * 判定内訳取得（Go/Canary/Hold）
   */
  async getVerdictDistribution(period_days: number = 7): Promise<VerdictDistribution> {
    return await api.get<VerdictDistribution>(`/api/v1/console/verdict-distribution?period_days=${period_days}`);
  }
};
