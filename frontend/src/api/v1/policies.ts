/**
 * v1 Policies API Client
 */
import { api } from '../../utils/api';

export interface Policy {
  id: string;
  name: string;
  description?: string;
  status: 'draft' | 'running' | 'completed' | 'failed';
  dataset_id: string;
  target_rule?: string;
  offer_config?: Record<string, any>;
  channels?: string[];
  frequency_cap?: number;
  budget_limit?: number;
  objectives?: Record<string, number>;
  risk_constraints?: Record<string, any>;
  tenant_id?: string;
  created_at: string;
  updated_at: string;
}

export interface PolicyRunResponse {
  policy_id: string;
  status: string;
  task_id: string;
  message: string;
}

export const policiesAPI = {
  /**
   * ポリシー一覧取得
   */
  list: async (status?: string, page: number = 1, pageSize: number = 20): Promise<Policy[]> => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());
    const response = await api.get<any>(`/api/v1/policies?${params}`);
    if (Array.isArray(response)) {
      return response as Policy[];
    }
    if (response && Array.isArray(response.policies)) {
      return response.policies as Policy[];
    }
    return [];
  },

  /**
   * ポリシー詳細取得
   */
  get: async (policyId: string): Promise<Policy> => {
    return await api.get<Policy>(`/api/v1/policies/${policyId}`);
  },

  /**
   * ポリシー作成
   */
  create: async (policy: Partial<Policy>): Promise<Policy> => {
    return await api.post<Policy>('/api/v1/policies', policy);
  },

  /**
   * ポリシー分析実行
   */
  run: async (policyId: string): Promise<PolicyRunResponse> => {
    return await api.post<PolicyRunResponse>(`/api/v1/policies/${policyId}/run`);
  },

  /**
   * ポリシー削除
   */
  delete: async (policyId: string): Promise<void> => {
    await api.delete(`/api/v1/policies/${policyId}`);
  },

  /**
   * ポリシー更新
   */
  update: async (policyId: string, policy: Partial<Policy>): Promise<Policy> => {
    return await api.put<Policy>(`/api/v1/policies/${policyId}`, policy);
  },

  /**
   * Offline Policy Evaluation (OPE)
   */
  evaluateOffline: async (policyId: string) => {
    return await api.post(`/api/v1/policies/${policyId}/offline-evaluate`);
  },

  /**
   * Export target list
   */
  exportTargets: async (policyId: string, format: 'csv' | 'parquet' = 'csv') => {
    return await api.post(`/api/v1/policies/${policyId}/export-targets`, { format });
  },

  /**
   * Scenario Simulation
   */
  simulateScenario: async (scenarioName: string, policyIds: string[]) => {
    return await api.post('/api/v1/scenarios/simulate', {
      name: scenarioName,
      policy_ids: policyIds
    });
  },
};

