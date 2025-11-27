import { api } from '../../utils/api'

export interface GrowthRequest {
  discount_rate?: number
  data: Array<Record<string, any>>
}

export interface ClvResponse {
  clv_treated: number
  clv_control: number
  delta_clv: number
}

export interface CohortRecord {
  cohort: string
  clv_treated: number
  clv_control: number
  delta_clv: number
}

export interface RetentionRecord {
  period: number
  retention: number
}

export const growthAPI = {
  async calculateClv(payload: GrowthRequest): Promise<ClvResponse> {
    return await api.post('/api/v2/growth/clv', payload)
  },

  async cohortAnalysis(payload: GrowthRequest, cohortColumn = 'cohort'): Promise<CohortRecord[]> {
    const query = new URLSearchParams({ cohort_column: cohortColumn })
    const response = await api.post<{ cohorts: CohortRecord[] }>(`/api/v2/growth/cohorts?${query.toString()}`, payload)
    return response.cohorts
  },

  async retentionCurve(payload: GrowthRequest, treated = true): Promise<RetentionRecord[]> {
    const query = new URLSearchParams({ treated: String(treated) })
    const response = await api.post<{ retention: RetentionRecord[] }>(`/api/v2/growth/retention?${query.toString()}`, payload)
    return response.retention
  }
}
