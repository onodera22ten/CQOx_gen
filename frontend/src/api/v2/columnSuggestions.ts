import { api } from '../../utils/api'

export interface ColumnSuggestion {
  role: string
  column: string
  score: number
  reason: string
}

export interface ColumnInferenceResponse {
  dataset_id: string
  suggestions: Record<string, ColumnSuggestion[]>
}

export const columnSuggestionsAPI = {
  async fetch(datasetId: string): Promise<ColumnInferenceResponse> {
    return await api.get<ColumnInferenceResponse>(`/api/v2/datasets/${datasetId}/column-suggestions`)
  }
}
