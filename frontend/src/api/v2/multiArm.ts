import { api } from '../../utils/api'

export type TreatmentType = 'binary' | 'multi_armed' | 'dose_response'

export interface TreatmentArmRequest {
  arm_id: number
  label: string
  description?: string
}

export interface TreatmentArm extends TreatmentArmRequest {
  delta_yen?: number | null
  cas?: number | null
  risk?: number | null
}

export interface MultiArmExperiment {
  id: string
  experiment_name: string
  treatment_type: TreatmentType
  status: string
  dataset_id?: string | null
  created_at?: string | null
  treatment_column?: string | null
  outcome_column?: string | null
  arms: TreatmentArm[]
}

export interface CreateExperimentPayload {
  experiment_name: string
  treatment_type: TreatmentType
  dataset_id: string
  treatment_column: string
  outcome_column: string
  arms: TreatmentArmRequest[]
}

export interface AutoPayloadResponse {
  dataset_id: string
  treatment_column: string
  outcome_column: string
  feature_columns: string[]
  row_count: number
  X: number[][]
  T: number[]
  Y: number[]
}

export const multiArmAPI = {
  async createExperiment(payload: CreateExperimentPayload): Promise<MultiArmExperiment> {
    return await api.post('/api/v2/multi-arm/experiments', payload)
  },

  async listExperiments(): Promise<MultiArmExperiment[]> {
    return await api.get('/api/v2/multi-arm/experiments')
  },

  async analyzeExperiment(
    experimentId: string,
    data: { X: number[][]; T: number[]; Y: number[] }
  ): Promise<{ ate_by_arm: Record<string, number> }> {
    return await api.post(`/api/v2/multi-arm/experiments/${experimentId}/analyze`, data)
  },

  async generatePayload(experimentId: string): Promise<AutoPayloadResponse> {
    return await api.get(`/api/v2/multi-arm/experiments/${experimentId}/auto-payload`)
  }
}
