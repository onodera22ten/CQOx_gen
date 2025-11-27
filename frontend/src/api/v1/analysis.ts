import { api } from '../../utils/api';

export interface AnalysisRequest {
  dataset_id: string;
  policy_id: string;
  estimators: string[];
  treatment_col: string;
  outcome_col: string;
  feature_cols: string[];
  scenario_spec: any;
  bootstrap_iterations?: number;
  confidence_level?: number;
}

export interface AnalysisStatus {
  analysis_id: string;
  policy_id: string;
  dataset_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  delta_yen?: number;
  delta_yen_ci_low?: number;
  delta_yen_ci_high?: number;
  verdict?: 'Go' | 'Canary' | 'Hold';
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  error_code?: string;
  error_details?: Record<string, any> | null;
}

export interface DiagnosticCheck {
  type: string;
  name: string;
  passed: boolean;
  score?: number;
  threshold?: number;
  data?: any;
}

export interface DiagnosticsData {
  status: string;
  cas_score: number;
  quality_level: string;
  diagnostics: DiagnosticCheck[];
  recommendations?: string[];
  total_checks: number;
}

export interface AnalysisImpactMetrics {
  estimated_cost: number;
  baseline_conversion_rate: number;
  projected_conversion_rate: number;
  conversion_uplift: number;
  users_affected: number;
  total_users: number;
  estimated_roi?: number | null;
}

export interface AnalysisDetails {
  analysis: AnalysisStatus;
  diagnostics?: DiagnosticsData | null;
  impact_metrics?: AnalysisImpactMetrics | null;
  estimator_results?: Record<string, any> | null;
}

export const analysisAPI = {
  /**
   * 因果推論分析を開始
   */
  start: async (request: AnalysisRequest): Promise<AnalysisStatus> => {
    return await api.post<AnalysisStatus>('/api/v1/analysis/run', request);
  },

  /**
   * 分析ステータス取得
   */
  getStatus: async (analysisId: string): Promise<AnalysisStatus> => {
    return await api.get<AnalysisStatus>(`/api/v1/analysis/${analysisId}`);
  },

  /**
   * 分析一覧取得
   */
  list: async (params?: {
    status?: string;
    policy_id?: string;
    page?: number;
    page_size?: number;
  }): Promise<AnalysisStatus[]> => {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status', params.status);
    if (params?.policy_id) queryParams.append('policy_id', params.policy_id);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.page_size) queryParams.append('page_size', params.page_size.toString());
    
    const url = `/api/v1/analysis${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await api.get<AnalysisStatus[]>(url);
  },

  /**
   * 分析キャンセル
   */
  cancel: async (analysisId: string): Promise<void> => {
    await api.delete(`/api/v1/analysis/${analysisId}`);
  },

  /**
   * 分析の詳細（診断結果・影響指標）取得
   */
  getDetails: async (analysisId: string): Promise<AnalysisDetails> => {
    return await api.get<AnalysisDetails>(`/api/v1/analysis/${analysisId}/details`);
  },
};
