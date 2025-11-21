/**
 * API Client
 *
 * Centralized API client with:
 * - Automatic JWT token injection
 * - Token refresh on 401
 * - Request/response interceptors
 * - Type-safe endpoints
 * - Development mock mode support
 */

import { mockPolicies, mockDatasets, delay } from '../api/mockBackend';

const API_URL = import.meta.env.VITE_API_URL || '';
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'; // モックモードを有効化

interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
}

class APIClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('access_token');

    if (!token) {
      return {};
    }

    return {
      'Authorization': `Bearer ${token}`,
    };
  }

  private async refreshToken(): Promise<boolean> {
    const refreshToken = localStorage.getItem('refresh_token');

    if (!refreshToken) {
      return false;
    }

    try {
      const response = await fetch(`${this.baseURL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        return false;
      }

      const data = await response.json();
      localStorage.setItem('access_token', data.access_token);
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    // モックモード: 開発環境でバックエンドなしで動作
    if (USE_MOCK) {
      return this.handleMockRequest<T>(endpoint, options);
    }

    const { skipAuth = false, headers = {}, ...rest } = options;

    const config: RequestInit = {
      ...rest,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
        ...(skipAuth ? {} : this.getAuthHeaders()),
      },
    };

    let response = await fetch(`${this.baseURL}${endpoint}`, config);

    // Handle 401 - try to refresh token
    if (response.status === 401 && !skipAuth) {
      const refreshed = await this.refreshToken();

      if (refreshed) {
        // Retry request with new token
        config.headers = {
          ...config.headers,
          ...this.getAuthHeaders(),
        };
        response = await fetch(`${this.baseURL}${endpoint}`, config);
      } else {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        throw new Error('Authentication required');
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`,
      }));
      throw new Error(error.detail || 'Request failed');
    }

    // Handle empty responses
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      return {} as T;
    }

    return response.json();
  }

  private async handleMockRequest<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    // モックレスポンス処理
    await delay(200); // リアルなレスポンスタイムをシミュレート

    const method = options.method || 'GET';

    // Decision Console endpoints
    if (endpoint.includes('/api/v1/console/delta-yen-summary')) {
      return {
        period_days: 7,
        total_decisions: 15,
        verdict_distribution: {
          go: 8,
          canary: 4,
          hold: 3,
          total: 15
        },
        avg_delta_yen: 2450000,
        max_delta_yen: 5200000,
        min_delta_yen: -320000,
        best_scenario: {
          id: 'dc-001',
          policy_id: 'pol-001',
          scenario_name: 'Email Campaign Q4',
          delta_yen: 5200000,
          verdict: 'Go' as const,
          created_at: new Date().toISOString()
        },
        history: []
      } as T;
    }

    if (endpoint.includes('/api/v1/console/delta-yen-history')) {
      return [
        { week: 'W45', delta_yen: 8500000, decision_count: 12 },
        { week: 'W46', delta_yen: 9200000, decision_count: 14 },
        { week: 'W47', delta_yen: 10100000, decision_count: 15 },
        { week: 'W48', delta_yen: 9800000, decision_count: 13 },
        { week: 'W49', delta_yen: 11200000, decision_count: 16 },
        { week: 'W50', delta_yen: 10500000, decision_count: 15 }
      ] as T;
    }

    if (endpoint.includes('/api/v1/console/verdict-distribution')) {
      return {
        go: 8,
        canary: 4,
        hold: 3,
        total: 15
      } as T;
    }

    if (endpoint.includes('/api/v1/results') && method === 'GET') {
      const mockDecisions = [
        {
          id: 'dc-001',
          policy_id: 'pol-001',
          scenario_name: 'Email Campaign Optimization',
          delta_yen: 5200000,
          delta_yen_ci_low: 4100000,
          delta_yen_ci_high: 6300000,
          verdict: 'Go' as const,
          reason: 'High expected profit with low risk',
          channel: 'email',
          quality_scores: { overlap_coverage: 0.92, balance_score: 0.88 },
          created_at: '2024-11-15T10:30:00Z'
        },
        {
          id: 'dc-002',
          policy_id: 'pol-002',
          scenario_name: 'Retargeting Budget Allocation',
          delta_yen: 3800000,
          delta_yen_ci_low: 2900000,
          delta_yen_ci_high: 4700000,
          verdict: 'Go' as const,
          reason: 'Strong causal evidence',
          channel: 'display',
          quality_scores: { overlap_coverage: 0.85, balance_score: 0.82 },
          created_at: '2024-11-14T15:20:00Z'
        },
        {
          id: 'dc-003',
          policy_id: 'pol-003',
          scenario_name: 'Landing Page A/B Test',
          delta_yen: 2100000,
          delta_yen_ci_low: 1200000,
          delta_yen_ci_high: 3000000,
          verdict: 'Canary' as const,
          reason: 'Moderate confidence, recommend A/B test',
          channel: 'web',
          quality_scores: { overlap_coverage: 0.75, balance_score: 0.70 },
          created_at: '2024-11-13T09:15:00Z'
        },
        {
          id: 'dc-004',
          policy_id: 'pol-004',
          scenario_name: 'Social Media Ad Mix',
          delta_yen: -450000,
          delta_yen_ci_low: -890000,
          delta_yen_ci_high: -10000,
          verdict: 'Hold' as const,
          reason: 'Negative expected profit',
          channel: 'social',
          quality_scores: { overlap_coverage: 0.65, balance_score: 0.60 },
          created_at: '2024-11-12T14:45:00Z'
        }
      ];

      return {
        total: mockDecisions.length,
        items: mockDecisions,
        page: 1,
        page_size: 10
      } as T;
    }

    // Policies endpoints
    if (endpoint.includes('/api/v1/policies') && method === 'GET') {
      return mockPolicies as T;
    }

    if (endpoint.includes('/api/v1/policies/') && endpoint.includes('/evaluate')) {
      return {
        expected_incremental_profit: 2450000,
        roi: 2.8,
        cas_score: 0.87,
        risk: {
          cvar_alpha_0_05: 1850000
        }
      } as T;
    }

    if (endpoint.includes('/api/v1/policies/simulate-scenario') || endpoint.includes('/api/v1/scenarios/simulate')) {
      return {
        total_incremental_profit: 8500000,
        total_roi: 3.2,
        total_risk: 0.18
      } as T;
    }

    if (endpoint.includes('/api/v1/policies/') && endpoint.includes('/offline-evaluate')) {
      return {
        expected_incremental_profit: 2450000,
        roi: 2.8,
        cas_score: 0.87,
        risk: {
          cvar_alpha_0_05: 1850000
        }
      } as T;
    }

    // Datasets endpoints
    if (endpoint.includes('/api/v1/upload/datasets') && method === 'GET') {
      return mockDatasets as T;
    }

    if (endpoint.includes('/api/v1/datasets/') && endpoint.includes('/columns') && method === 'GET') {
      return {
        dataset_id: endpoint.split('/')[4],
        columns: ['user_id', 'treatment', 'outcome', 'revenue', 'age', 'gender', 'region', 'category'],
        schema: {
          user_id: 'int64',
          treatment: 'int64',
          outcome: 'float64',
          revenue: 'float64',
          age: 'int64',
          gender: 'object',
          region: 'object',
          category: 'object'
        },
        suggestions: {
          treatment_col: 'treatment',
          outcome_col: 'revenue',
          feature_cols: ['age', 'gender', 'region', 'category']
        },
        row_count: 10000,
        total_rows: 10000
      } as T;
    }

    if (endpoint.includes('/api/v1/datasets/') && endpoint.includes('/preview') && method === 'POST') {
      return {
        data: [
          { user_id: 1, treatment: 1, outcome: 1.2, revenue: 5200, age: 25, gender: 'M', region: 'Tokyo', category: 'A' },
          { user_id: 2, treatment: 0, outcome: 0.8, revenue: 3800, age: 32, gender: 'F', region: 'Osaka', category: 'B' },
          { user_id: 3, treatment: 1, outcome: 1.5, revenue: 6100, age: 28, gender: 'M', region: 'Tokyo', category: 'A' },
          { user_id: 4, treatment: 0, outcome: 0.9, revenue: 4200, age: 45, gender: 'F', region: 'Nagoya', category: 'C' },
          { user_id: 5, treatment: 1, outcome: 1.3, revenue: 5800, age: 35, gender: 'M', region: 'Fukuoka', category: 'B' }
        ],
        total_rows: 10000,
        row_count: 5
      } as T;
    }

    // Analysis endpoints
    if (endpoint.includes('/api/v1/analysis/run') && method === 'POST') {
      const analysisId = `analysis-${Date.now()}`;
      return {
        analysis_id: analysisId,
        policy_id: 'pol-001',
        dataset_id: 'ds-001',
        status: 'completed',
        progress: 100,
        delta_yen: 2450000,
        delta_yen_ci_low: 1850000,
        delta_yen_ci_high: 3050000,
        verdict: 'Go',
        started_at: new Date().toISOString(),
        completed_at: new Date().toISOString()
      } as T;
    }

    if (endpoint.includes('/api/v1/analysis/') && method === 'GET') {
      return {
        analysis_id: 'analysis-001',
        policy_id: 'pol-001',
        dataset_id: 'ds-001',
        status: 'completed',
        progress: 100,
        delta_yen: 2450000,
        delta_yen_ci_low: 1850000,
        delta_yen_ci_high: 3050000,
        verdict: 'Go',
        started_at: new Date(Date.now() - 60000).toISOString(),
        completed_at: new Date().toISOString()
      } as T;
    }

    if (endpoint.includes('/api/v1/analysis') && method === 'GET') {
      return [
        {
          analysis_id: 'analysis-001',
          policy_id: 'pol-001',
          dataset_id: 'ds-001',
          status: 'completed',
          progress: 100,
          delta_yen: 2450000,
          verdict: 'Go',
          completed_at: new Date().toISOString()
        },
        {
          analysis_id: 'analysis-002',
          policy_id: 'pol-002',
          dataset_id: 'ds-002',
          status: 'running',
          progress: 65,
          started_at: new Date(Date.now() - 30000).toISOString()
        }
      ] as T;
    }

    // Visualizations endpoints
    if (endpoint.includes('/api/visualizations/pareto-frontier') && method === 'POST') {
      return {
        data: {
          efficient_frontier: [
            { name: 'Policy A', profit: 5200000, risk: 0.12 },
            { name: 'Policy B', profit: 3800000, risk: 0.08 },
            { name: 'Policy C', profit: 2100000, risk: 0.05 }
          ],
          dominated_policies: [
            { name: 'Policy D', profit: 2000000, risk: 0.15 }
          ]
        }
      } as T;
    }

    if (endpoint.includes('/api/visualizations/balance-plot') && method === 'POST') {
      return {
        data: {
          balanced_variables: ['age', 'gender', 'region'],
          imbalanced_variables: ['income'],
          max_smd: 0.15
        }
      } as T;
    }

    if (endpoint.includes('/api/visualizations/overlap-density') && method === 'POST') {
      return {
        data: {
          overlap_score: 0.87,
          common_support_range: [0.1, 0.9]
        }
      } as T;
    }

    if (endpoint.includes('/api/visualizations/cate-distribution') && method === 'POST') {
      return {
        data: {
          mean: 245000,
          std: 85000,
          median: 230000,
          q25: 180000,
          q75: 310000,
          heterogeneity_score: 0.65
        }
      } as T;
    }

    if (endpoint.includes('/api/visualizations/qini-curve') && method === 'POST') {
      return {
        data: {
          auc: 0.72,
          optimal_treatment_fraction: 0.35,
          max_uplift: 520000
        }
      } as T;
    }

    if (endpoint.includes('/api/visualizations/calibration-plot') && method === 'POST') {
      return {
        data: {
          calibration_score: 0.88,
          slope: 0.95,
          intercept: 12000
        }
      } as T;
    }

    if (endpoint.includes('/api/visualizations/sensitivity-gamma') && method === 'POST') {
      return {
        data: {
          critical_gamma: 1.8,
          robust_at_gamma_2: true
        }
      } as T;
    }

    // Demo endpoints
    if (endpoint.includes('/api/demo/generate') && method === 'POST') {
      return {
        dataset_id: `demo-${Date.now()}`,
        data_type: 'rct',
        sample_size: 1000,
        treatment_effect: 0.5,
        preview_data: [
          { user_id: 1, treatment: 1, outcome: 1.2, age: 25, gender: 'M' },
          { user_id: 2, treatment: 0, outcome: 0.8, age: 32, gender: 'F' },
          { user_id: 3, treatment: 1, outcome: 1.5, age: 28, gender: 'M' }
        ],
        columns: ['user_id', 'treatment', 'outcome', 'age', 'gender'],
        description: 'Synthetic RCT dataset with 1000 samples'
      } as T;
    }

    if (endpoint.includes('/api/demo/analyze') && method === 'POST') {
      return {
        analysis_id: `demo-analysis-${Date.now()}`,
        dataset_id: 'demo-001',
        status: 'completed',
        progress: 100,
        estimated_ate: 0.48,
        true_ate: 0.5,
        estimator_results: [
          {
            estimator: 'S-Learner',
            estimate: 0.48,
            std_error: 0.05,
            ci_lower: 0.38,
            ci_upper: 0.58,
            bias: -0.02
          },
          {
            estimator: 'T-Learner',
            estimate: 0.51,
            std_error: 0.06,
            ci_lower: 0.39,
            ci_upper: 0.63,
            bias: 0.01
          },
          {
            estimator: 'DR-Learner',
            estimate: 0.49,
            std_error: 0.04,
            ci_lower: 0.41,
            ci_upper: 0.57,
            bias: -0.01
          }
        ],
        completed_at: new Date().toISOString()
      } as T;
    }

    if (endpoint.includes('/api/demo/analysis/') && method === 'GET') {
      return {
        analysis_id: 'demo-analysis-001',
        dataset_id: 'demo-001',
        status: 'completed',
        progress: 100,
        estimated_ate: 0.48,
        true_ate: 0.5,
        estimator_results: [
          {
            estimator: 'S-Learner',
            estimate: 0.48,
            std_error: 0.05,
            ci_lower: 0.38,
            ci_upper: 0.58,
            bias: -0.02
          }
        ],
        completed_at: new Date().toISOString()
      } as T;
    }

    if (endpoint.includes('/api/demo/presets') && method === 'GET' && !endpoint.includes('/load')) {
      return [
        {
          id: 'rct-basic',
          name: 'Basic RCT',
          description: 'Simple randomized controlled trial',
          icon: 'flask',
          data_type: 'rct',
          sample_size: 1000,
          treatment_effect: 0.5,
          estimators: ['S-Learner', 'T-Learner']
        },
        {
          id: 'observational-confounding',
          name: 'Observational Study',
          description: 'Study with confounding variables',
          icon: 'eye',
          data_type: 'observational',
          sample_size: 2000,
          treatment_effect: 0.3,
          estimators: ['DR-Learner', 'IPW']
        }
      ] as T;
    }

    if (endpoint.includes('/api/demo/presets/') && endpoint.includes('/load') && method === 'POST') {
      return {
        dataset_id: 'demo-preset-001',
        data_type: 'rct',
        sample_size: 1000,
        treatment_effect: 0.5,
        preview_data: [
          { user_id: 1, treatment: 1, outcome: 1.2, age: 25, gender: 'M' },
          { user_id: 2, treatment: 0, outcome: 0.8, age: 32, gender: 'F' }
        ],
        columns: ['user_id', 'treatment', 'outcome', 'age', 'gender'],
        description: 'Basic RCT preset dataset'
      } as T;
    }

    // Default fallback
    return {} as T;
  }

  // HTTP methods
  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  async post<T>(
    endpoint: string,
    data?: any,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put<T>(
    endpoint: string,
    data?: any,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }

  async upload<T>(
    endpoint: string,
    file: File,
    options?: RequestOptions
  ): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    const { headers = {}, ...rest } = options || {};

    return this.request<T>(endpoint, {
      ...rest,
      method: 'POST',
      headers: {
        // Don't set Content-Type - browser will set it with boundary
        ...headers,
      },
      body: formData,
    });
  }
}

// Create singleton instance
export const api = new APIClient(API_URL);

// Export for testing
export { APIClient };
