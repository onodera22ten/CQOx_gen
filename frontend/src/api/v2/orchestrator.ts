import { api } from '../../utils/api'

export interface OrchestratorExperiment {
  id: string
  experiment_name: string
  target_metric: string
  status: string
  created_at?: string | null
}

export interface CreateOrchestratorPayload {
  experiment_name: string
  target_metric: string
  arms: string[]
}

export interface AllocationResponse {
  experiment_id: string
  allocations: Record<string, number>
}

export interface OutcomePayload {
  arm_id: string
  reward: number
}

export const orchestratorAPI = {
  async createExperiment(payload: CreateOrchestratorPayload): Promise<OrchestratorExperiment> {
    return await api.post('/api/v2/experiments', payload)
  },

  async listExperiments(): Promise<OrchestratorExperiment[]> {
    return await api.get('/api/v2/experiments')
  },

  async getAllocation(experimentId: string): Promise<AllocationResponse> {
    return await api.get(`/api/v2/experiments/${experimentId}/allocation`)
  },

  async updateExperiment(experimentId: string, outcomes: OutcomePayload[]): Promise<AllocationResponse> {
    return await api.post(`/api/v2/experiments/${experimentId}/update`, { outcomes })
  }
}
