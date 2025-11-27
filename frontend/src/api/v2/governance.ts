import { api } from '../../utils/api'

export interface FairnessRequest {
  data: Array<Record<string, any>>
  sensitive_attributes: Record<string, string[]>
  threshold?: number
}

export interface Violation {
  rule_id: string
  type: string
  severity: string
  details: Record<string, any> | string
  affected_groups?: string[]
}

export interface ViolationResponse {
  violations: Violation[]
}

export interface DataQualityRequest {
  data: Array<Record<string, any>>
  min_samples?: number
}

export interface ComplianceRequest {
  user_exposures: Record<string, number>
  max_frequency?: number
}

export interface GovernanceViolationRecord {
  id: string
  rule_id: string | null
  type: string
  severity: string
  details: Record<string, any> | string
  created_at: string
}

export interface GovernanceRule {
  id: string
  name: string
  description?: string | null
  rule_type: string
  severity: string
  action: string
  threshold_value?: number | null
  config?: Record<string, any> | null
  is_active: boolean
}

export interface GovernanceRuleResponse {
  rules: GovernanceRule[]
}

export const governanceAPI = {
  async checkFairness(payload: FairnessRequest): Promise<ViolationResponse> {
    return await api.post('/api/v2/governance/check/fairness', payload)
  },
  async checkDataQuality(payload: DataQualityRequest): Promise<ViolationResponse> {
    return await api.post('/api/v2/governance/check/data-quality', payload)
  },
  async checkCompliance(payload: ComplianceRequest): Promise<ViolationResponse> {
    return await api.post('/api/v2/governance/check/compliance', payload)
  },
  async listViolations(): Promise<{ violations: GovernanceViolationRecord[] }> {
    return await api.get('/api/v2/governance/violations')
  },
  async listRules(): Promise<GovernanceRuleResponse> {
    return await api.get('/api/v2/governance/rules')
  }
}
