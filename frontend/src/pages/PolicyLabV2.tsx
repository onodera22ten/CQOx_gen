/**
 * Policy Lab v2
 * Offline policy learning with Pareto frontier visualization
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import {
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface PolicyConfig {
  id: string
  tenant_id: string
  name: string
  description?: string
  policy_type: string
  treatment_variable: string
  outcome_variable: string
  features: string[]
  threshold?: number
  budget_constraint?: number
  coverage_constraint?: number
  dataset_id: string
  model_id?: string
  status: string
  created_at: string
}

interface FrontierPoint {
  expected_value: number
  risk: number
  policy_params: any
  metrics: any
}

interface OfflinePolicyRun {
  id: string
  policy_config_id: string
  status: string
  frontier?: FrontierPoint[]
  best_policy?: PolicyConfig
  selected_point?: FrontierPoint
  estimated_value?: number
  estimated_risk?: number
  confidence_interval?: [number, number]
  created_at: string
  completed_at?: string
  error_message?: string
}

export default function PolicyLabV2() {
  const queryClient = useQueryClient()
  const [selectedPolicy, setSelectedPolicy] = useState<PolicyConfig | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedRun, setSelectedRun] = useState<OfflinePolicyRun | null>(null)

  // Fetch policies
  const { data: policies, isLoading: policiesLoading } = useQuery({
    queryKey: ['v2-policies'],
    queryFn: async () => {
      const response = await axios.get('/api/v2/policies')
      return response.data as PolicyConfig[]
    },
  })

  // Create policy mutation
  const createPolicyMutation = useMutation({
    mutationFn: async (policyData: any) => {
      const response = await axios.post('/api/v2/policies', policyData)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['v2-policies'] })
      setShowCreateModal(false)
    },
  })

  // Run offline learning mutation
  const runOfflineLearningMutation = useMutation({
    mutationFn: async ({
      policyId,
      config,
    }: {
      policyId: string
      config: any
    }) => {
      const response = await axios.post(
        `/api/v2/policies/${policyId}/offline-learn`,
        config
      )
      return response.data
    },
    onSuccess: (data) => {
      setSelectedRun(data)
      // Start polling for results
      queryClient.invalidateQueries({ queryKey: ['policy-run', data.id] })
    },
  })

  // Fetch policy run results
  const { data: runData } = useQuery({
    queryKey: ['policy-run', selectedRun?.id],
    queryFn: async () => {
      if (!selectedRun?.id) return null
      const response = await axios.get(`/api/v2/policies/runs/${selectedRun.id}`)
      return response.data as OfflinePolicyRun
    },
    enabled: !!selectedRun?.id,
    refetchInterval: (data) => {
      // Poll every 2 seconds if status is pending or running
      if (data && (data.status === 'pending' || data.status === 'running')) {
        return 2000
      }
      return false
    },
  })

  if (policiesLoading) {
    return <div className="loading-spinner">Loading policies...</div>
  }

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Policy Lab v2</h1>
          <p className="page-subtitle">
            Offline policy learning with off-policy evaluation
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setShowCreateModal(true)}
        >
          + Create Policy
        </button>
      </div>

      {/* Policies Grid */}
      <div className="grid grid-cols-1 gap-6">
        {/* Policies List */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Policies ({policies?.length || 0})</h2>
          </div>
          <div className="card-body">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Treatment</th>
                  <th>Outcome</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {(policies || []).map((policy) => (
                  <tr
                    key={policy.id}
                    className={
                      selectedPolicy?.id === policy.id ? 'selected' : ''
                    }
                  >
                    <td>
                      <div className="font-medium">{policy.name}</div>
                      {policy.description && (
                        <div className="text-sm text-gray-500">
                          {policy.description}
                        </div>
                      )}
                    </td>
                    <td>
                      <span className="badge badge-blue">
                        {policy.policy_type}
                      </span>
                    </td>
                    <td>{policy.treatment_variable}</td>
                    <td>{policy.outcome_variable}</td>
                    <td>
                      <span
                        className={`badge ${
                          policy.status === 'active'
                            ? 'badge-green'
                            : policy.status === 'optimized'
                            ? 'badge-purple'
                            : 'badge-gray'
                        }`}
                      >
                        {policy.status}
                      </span>
                    </td>
                    <td>
                      <div className="flex gap-2">
                        <button
                          className="btn btn-sm btn-secondary"
                          onClick={() => setSelectedPolicy(policy)}
                        >
                          View
                        </button>
                        <button
                          className="btn btn-sm btn-primary"
                          onClick={() => {
                            setSelectedPolicy(policy)
                            runOfflineLearningMutation.mutate({
                              policyId: policy.id,
                              config: {
                                objective: 'uplift',
                                risk_metric: 'std',
                                ope_method: 'DR',
                                risk_aversion: 0.5,
                                n_candidates: 100,
                                n_bootstrap: 1000,
                              },
                            })
                          }}
                          disabled={runOfflineLearningMutation.isPending}
                        >
                          {runOfflineLearningMutation.isPending
                            ? 'Running...'
                            : 'Optimize'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Policy Details & Results */}
        {selectedPolicy && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Policy Details: {selectedPolicy.name}</h2>
            </div>
            <div className="card-body">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-500">
                    Policy Type
                  </h3>
                  <p className="mt-1">{selectedPolicy.policy_type}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500">
                    Treatment Variable
                  </h3>
                  <p className="mt-1">{selectedPolicy.treatment_variable}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500">
                    Outcome Variable
                  </h3>
                  <p className="mt-1">{selectedPolicy.outcome_variable}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Features</h3>
                  <p className="mt-1">{selectedPolicy.features.join(', ')}</p>
                </div>
                {selectedPolicy.threshold !== undefined && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">
                      Threshold
                    </h3>
                    <p className="mt-1">{selectedPolicy.threshold.toFixed(3)}</p>
                  </div>
                )}
                {selectedPolicy.budget_constraint !== undefined && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">
                      Budget Constraint
                    </h3>
                    <p className="mt-1">
                      ${selectedPolicy.budget_constraint.toLocaleString()}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Offline Learning Results */}
        {runData && (
          <>
            {/* Status */}
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Offline Learning Status</h2>
              </div>
              <div className="card-body">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-lg font-medium">
                      Status:{' '}
                      <span
                        className={`badge ${
                          runData.status === 'completed'
                            ? 'badge-green'
                            : runData.status === 'failed'
                            ? 'badge-red'
                            : 'badge-yellow'
                        }`}
                      >
                        {runData.status}
                      </span>
                    </div>
                    {runData.error_message && (
                      <div className="mt-2 text-red-600">
                        Error: {runData.error_message}
                      </div>
                    )}
                  </div>
                  {runData.status === 'running' && (
                    <div className="loading-spinner">Optimizing...</div>
                  )}
                </div>
              </div>
            </div>

            {/* Results */}
            {runData.status === 'completed' && runData.frontier && (
              <>
                {/* Metrics */}
                <div className="grid grid-cols-3 gap-6">
                  <div className="card">
                    <div className="card-body">
                      <h3 className="text-sm font-medium text-gray-500">
                        Estimated Value
                      </h3>
                      <p className="mt-2 text-3xl font-bold">
                        {runData.estimated_value?.toFixed(2) || 'N/A'}
                      </p>
                      {runData.confidence_interval && (
                        <p className="mt-1 text-sm text-gray-500">
                          95% CI: [{runData.confidence_interval[0].toFixed(2)},
                          {runData.confidence_interval[1].toFixed(2)}]
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="card">
                    <div className="card-body">
                      <h3 className="text-sm font-medium text-gray-500">
                        Estimated Risk
                      </h3>
                      <p className="mt-2 text-3xl font-bold">
                        {runData.estimated_risk?.toFixed(2) || 'N/A'}
                      </p>
                    </div>
                  </div>

                  <div className="card">
                    <div className="card-body">
                      <h3 className="text-sm font-medium text-gray-500">
                        Frontier Points
                      </h3>
                      <p className="mt-2 text-3xl font-bold">
                        {runData.frontier.length}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Pareto Frontier Visualization */}
                <div className="card">
                  <div className="card-header">
                    <h2 className="card-title">Pareto Frontier</h2>
                    <p className="card-subtitle">
                      Trade-off between expected value and risk
                    </p>
                  </div>
                  <div className="card-body">
                    <ResponsiveContainer width="100%" height={400}>
                      <ScatterChart
                        margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          type="number"
                          dataKey="risk"
                          name="Risk"
                          label={{
                            value: 'Risk (Standard Deviation)',
                            position: 'insideBottom',
                            offset: -10,
                          }}
                        />
                        <YAxis
                          type="number"
                          dataKey="expected_value"
                          name="Expected Value"
                          label={{
                            value: 'Expected Value',
                            angle: -90,
                            position: 'insideLeft',
                          }}
                        />
                        <Tooltip
                          cursor={{ strokeDasharray: '3 3' }}
                          content={({ active, payload }) => {
                            if (active && payload && payload.length) {
                              const data = payload[0].payload as FrontierPoint
                              return (
                                <div className="bg-white p-4 border border-gray-200 rounded shadow-lg">
                                  <p className="font-medium">Frontier Point</p>
                                  <p className="text-sm">
                                    Expected Value:{' '}
                                    {data.expected_value.toFixed(3)}
                                  </p>
                                  <p className="text-sm">
                                    Risk: {data.risk.toFixed(3)}
                                  </p>
                                  {data.policy_params.threshold && (
                                    <p className="text-sm">
                                      Threshold:{' '}
                                      {data.policy_params.threshold.toFixed(3)}
                                    </p>
                                  )}
                                  {data.metrics.utility && (
                                    <p className="text-sm">
                                      Utility: {data.metrics.utility.toFixed(3)}
                                    </p>
                                  )}
                                </div>
                              )
                            }
                            return null
                          }}
                        />
                        <Scatter
                          name="Frontier Points"
                          data={runData.frontier}
                          fill="#3b82f6"
                        />
                        {runData.selected_point && (
                          <Scatter
                            name="Selected Policy"
                            data={[runData.selected_point]}
                            fill="#10b981"
                            shape="star"
                          />
                        )}
                      </ScatterChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Best Policy */}
                {runData.best_policy && (
                  <div className="card">
                    <div className="card-header">
                      <h2 className="card-title">Recommended Policy</h2>
                    </div>
                    <div className="card-body">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <h3 className="text-sm font-medium text-gray-500">
                            Policy Type
                          </h3>
                          <p className="mt-1">{runData.best_policy.policy_type}</p>
                        </div>
                        {runData.best_policy.threshold !== undefined && (
                          <div>
                            <h3 className="text-sm font-medium text-gray-500">
                              Optimal Threshold
                            </h3>
                            <p className="mt-1 text-lg font-medium">
                              {runData.best_policy.threshold.toFixed(3)}
                            </p>
                          </div>
                        )}
                      </div>
                      <div className="mt-4">
                        <button className="btn btn-primary">
                          Deploy Policy
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>

      {/* Create Policy Modal */}
      {showCreateModal && (
        <CreatePolicyModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={(data) => createPolicyMutation.mutate(data)}
          isSubmitting={createPolicyMutation.isPending}
        />
      )}
    </div>
  )
}

// Create Policy Modal Component
function CreatePolicyModal({
  onClose,
  onSubmit,
  isSubmitting,
}: {
  onClose: () => void
  onSubmit: (data: any) => void
  isSubmitting: boolean
}) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    policy_type: 'threshold',
    treatment_variable: '',
    outcome_variable: '',
    features: '',
    threshold: 0.5,
    dataset_id: '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      ...formData,
      features: formData.features.split(',').map((f) => f.trim()),
    })
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">Create New Policy</h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-group">
              <label className="form-label">Policy Name</label>
              <input
                type="text"
                className="form-input"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Description</label>
              <textarea
                className="form-input"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                rows={3}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Policy Type</label>
              <select
                className="form-input"
                value={formData.policy_type}
                onChange={(e) =>
                  setFormData({ ...formData, policy_type: e.target.value })
                }
              >
                <option value="threshold">Threshold</option>
                <option value="linear">Linear</option>
                <option value="multi_arm">Multi-Arm</option>
                <option value="custom">Custom</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="form-group">
                <label className="form-label">Treatment Variable</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.treatment_variable}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      treatment_variable: e.target.value,
                    })
                  }
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Outcome Variable</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.outcome_variable}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      outcome_variable: e.target.value,
                    })
                  }
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">
                Features (comma-separated)
              </label>
              <input
                type="text"
                className="form-input"
                value={formData.features}
                onChange={(e) =>
                  setFormData({ ...formData, features: e.target.value })
                }
                placeholder="feature1, feature2, feature3"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Dataset ID</label>
              <input
                type="text"
                className="form-input"
                value={formData.dataset_id}
                onChange={(e) =>
                  setFormData({ ...formData, dataset_id: e.target.value })
                }
                required
              />
            </div>
          </div>

          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Creating...' : 'Create Policy'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
