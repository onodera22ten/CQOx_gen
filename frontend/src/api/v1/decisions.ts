/**
 * v1 API Client for DecisionCard
 *
 * Δ¥ + Go/Canary/Hold判定のAPI
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
  total_decisions: number;
  go_count: number;
  canary_count: number;
  hold_count: number;
  avg_delta_yen: number;
  best_delta_yen: number;
  worst_delta_yen: number;
  best_scenario?: DecisionCard;
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
    const response = await axios.get(`${API_BASE_URL}/api/v1/results`, { params });
    return response.data;
  },

  /**
   * DecisionCard詳細取得
   */
  async get(id: string): Promise<DecisionCard> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/results/${id}`);
    return response.data;
  },

  /**
   * Δ¥サマリー取得（Decision Console用）
   */
  async getSummary(period_days: number = 7): Promise<DeltaYenSummary> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/console/delta-yen-summary`, {
      params: { period_days }
    });
    return response.data;
  },

  /**
   * Δ¥履歴取得（週次）
   */
  async getHistory(params?: {
    period?: 'week' | 'month';
    weeks?: number;
  }): Promise<DeltaYenHistoryItem[]> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/console/delta-yen-history`, { params });
    return response.data;
  },

  /**
   * 判定内訳取得（Go/Canary/Hold）
   */
  async getVerdictDistribution(period_days: number = 7): Promise<VerdictDistribution> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/console/verdict-distribution`, {
      params: { period_days }
    });
    return response.data;
  }
};
