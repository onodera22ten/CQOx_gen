/**
 * Demo API Client
 * Provides simplified causal inference demonstrations
 */
import { api } from '../../utils/api';

export interface DemoDatasetRequest {
  data_type: 'rct' | 'observational' | 'panel';
  sample_size: number;
  treatment_effect: number;
  noise_level?: number;
}

export interface DemoDataset {
  dataset_id: string;
  data_type: string;
  sample_size: number;
  treatment_effect: number;
  preview_data: Array<Record<string, any>>;
  columns: string[];
  description: string;
}

export interface DemoAnalysisRequest {
  dataset_id: string;
  estimators?: string[];
}

export interface DemoAnalysisResult {
  analysis_id: string;
  dataset_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  estimated_ate: number;
  true_ate: number;
  estimator_results: Array<{
    estimator: string;
    estimate: number;
    std_error: number;
    ci_lower: number;
    ci_upper: number;
    bias: number;
  }>;
  visualization_data?: any;
  completed_at?: string;
  error_message?: string;
}

export interface DemoPreset {
  id: string;
  name: string;
  description: string;
  icon: string;
  data_type: 'rct' | 'observational' | 'panel';
  sample_size: number;
  treatment_effect: number;
  estimators: string[];
}

export const demoAPI = {
  /**
   * Generate synthetic dataset for demonstration
   */
  generateDataset: async (request: DemoDatasetRequest): Promise<DemoDataset> => {
    return await api.post<DemoDataset>('/api/demo/generate', request);
  },

  /**
   * Run causal analysis on demo dataset
   */
  runAnalysis: async (request: DemoAnalysisRequest): Promise<DemoAnalysisResult> => {
    return await api.post<DemoAnalysisResult>('/api/demo/analyze', request);
  },

  /**
   * Get analysis status and results
   */
  getAnalysis: async (analysisId: string): Promise<DemoAnalysisResult> => {
    return await api.get<DemoAnalysisResult>(`/api/demo/analysis/${analysisId}`);
  },

  /**
   * Get available presets
   */
  getPresets: async (): Promise<DemoPreset[]> => {
    return await api.get<DemoPreset[]>('/api/demo/presets');
  },

  /**
   * Load a preset scenario
   */
  loadPreset: async (presetId: string): Promise<DemoDataset> => {
    return await api.post<DemoDataset>(`/api/demo/presets/${presetId}/load`, {});
  },
};
