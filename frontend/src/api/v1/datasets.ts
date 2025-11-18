/**
 * v1 Datasets API Client
 */
import { api } from '../../utils/api';

export interface Dataset {
  id: string;
  name: string;
  description?: string;
  file_path?: string;
  row_count?: number;
  column_count?: number;
  schema?: Record<string, string>;
  tenant_id?: string;
  created_at: string;
  updated_at: string;
}

export interface DatasetUploadRequest {
  name: string;
  description?: string;
  column_mapping_profile_id?: string;
}

export interface DatasetUploadResponse {
  dataset_id: string;
  upload_url: string;
  expires_at: string;
  candidate_profiles: Array<Record<string, string>>;
}

export interface DatasetColumns {
  dataset_id: string;
  columns: string[];
  schema: Record<string, string>;
  suggestions: {
    treatment_col: string | null;
    outcome_col: string | null;
    feature_cols: string[];
  };
  row_count: number;
  total_rows: number;
}

export const datasetsAPI = {
  /**
   * データセット一覧取得
   */
  list: async (_page: number = 1, _pageSize: number = 20): Promise<Dataset[]> => {
    return await api.get<Dataset[]>(`/api/v1/upload/datasets`);
  },

  /**
   * データセット詳細取得
   */
  get: async (datasetId: string): Promise<Dataset> => {
    return await api.get<Dataset>(`/api/v1/datasets/${datasetId}`);
  },

  /**
   * データセットカラム情報取得
   */
  getColumns: async (datasetId: string): Promise<DatasetColumns> => {
    return await api.get<DatasetColumns>(`/api/v1/datasets/${datasetId}/columns`);
  },

  /**
   * データセットアップロード開始
   */
  createUpload: async (request: DatasetUploadRequest): Promise<DatasetUploadResponse> => {
    return await api.post<DatasetUploadResponse>('/api/v1/datasets/upload', request);
  },

  /**
   * データセットプレビュー
   */
  preview: async (datasetId: string, limit: number = 100): Promise<any> => {
    return await api.post<any>(`/api/v1/datasets/${datasetId}/preview`, { limit });
  },

  /**
   * データセット削除
   */
  delete: async (datasetId: string): Promise<void> => {
    await api.delete(`/api/v1/upload/datasets/${datasetId}`);
  },
};

