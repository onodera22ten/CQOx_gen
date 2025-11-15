/**
 * Experiment Design v2
 * A/B testing with sample size calculation and power analysis
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface ExperimentArm {
  name: string
  treatment_value: any
  allocation: number
  description?: string
}

interface ExperimentDesign {
  id: string
  name: string
  description?: string
  treatment_variable: string
  arms: ExperimentArm[]
  primary_outcome: string
  outcome_type: string
  baseline_mean?: number
  baseline_proportion?: number
  minimum_detectable_effect: number
  alpha: number
  power: number
  required_sample_size_per_arm?: number
  total_sample_size?: number
  expected_runtime_days?: number
  status: string
  created_at: string
}

interface PowerCurvePoint {
  effect_size: number
  effect_size_standardized: number
  power: number
}

export default function ExperimentDesignV2() {
  const queryClient = useQueryClient()
  const [selectedExperiment, setSelectedExperiment] = useState<ExperimentDesign | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)

  // Fetch experiments
  const { data: experiments, isLoading } = useQuery({
    queryKey: ['v2-experiments'],
    queryFn: async () => {
      const response = await axios.get('/api/v2/experiments')
      return response.data as ExperimentDesign[]
    },
  })

  // Fetch power analysis
  const { data: powerAnalysis } = useQuery({
    queryKey: ['power-analysis', selectedExperiment?.id],
    queryFn: async () => {
      if (!selectedExperiment?.id) return null
      const response = await axios.get(
        `/api/v2/experiments/${selectedExperiment.id}/power-analysis`
      )
      return response.data as {
        experiment_id: string
        sample_size_per_arm: number
        alpha: number
        power_curve: PowerCurvePoint[]
      }
    },
    enabled: !!selectedExperiment?.id,
  })

  // Create experiment mutation
  const createExperimentMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await axios.post('/api/v2/experiments/design', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['v2-experiments'] })
      setShowCreateModal(false)
    },
  })

  // Start experiment mutation
  const startExperimentMutation = useMutation({
    mutationFn: async (experimentId: string) => {
      const response = await axios.post(`/api/v2/experiments/${experimentId}/start`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['v2-experiments'] })
    },
  })

  if (isLoading) {
    return <div className="loading-spinner">Loading experiments...</div>
  }

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Experiment Design v2</h1>
          <p className="page-subtitle">
            A/B testing with statistical power analysis and sample size calculation
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setShowCreateModal(true)}
        >
          + Design New Experiment
        </button>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {/* Experiments List */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Experiments ({experiments?.length || 0})</h2>
          </div>
          <div className="card-body">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Treatment</th>
                  <th>Outcome</th>
                  <th>Arms</th>
                  <th>Sample Size</th>
                  <th>Runtime</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {(experiments || []).map((exp) => (
                  <tr
                    key={exp.id}
                    className={selectedExperiment?.id === exp.id ? 'selected' : ''}
                  >
                    <td>
                      <div className="font-medium">{exp.name}</div>
                      {exp.description && (
                        <div className="text-sm text-gray-500">{exp.description}</div>
                      )}
                    </td>
                    <td>{exp.treatment_variable}</td>
                    <td>{exp.primary_outcome}</td>
                    <td>{exp.arms.length} arms</td>
                    <td>
                      {exp.total_sample_size?.toLocaleString() || 'N/A'}
                      <div className="text-xs text-gray-500">
                        ({exp.required_sample_size_per_arm?.toLocaleString() || 'N/A'}{' '}
                        per arm)
                      </div>
                    </td>
                    <td>
                      {exp.expected_runtime_days
                        ? `${exp.expected_runtime_days.toFixed(1)} days`
                        : 'N/A'}
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          exp.status === 'running'
                            ? 'badge-blue'
                            : exp.status === 'completed'
                            ? 'badge-green'
                            : 'badge-gray'
                        }`}
                      >
                        {exp.status}
                      </span>
                    </td>
                    <td>
                      <div className="flex gap-2">
                        <button
                          className="btn btn-sm btn-secondary"
                          onClick={() => setSelectedExperiment(exp)}
                        >
                          View
                        </button>
                        {exp.status === 'design' && (
                          <button
                            className="btn btn-sm btn-primary"
                            onClick={() => startExperimentMutation.mutate(exp.id)}
                            disabled={startExperimentMutation.isPending}
                          >
                            Start
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Experiment Details */}
        {selectedExperiment && (
          <>
            {/* Configuration */}
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">
                  Experiment Configuration: {selectedExperiment.name}
                </h2>
              </div>
              <div className="card-body">
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  <div>
                    <div className="text-sm text-gray-500">Treatment Variable</div>
                    <div className="mt-1 font-medium">
                      {selectedExperiment.treatment_variable}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Primary Outcome</div>
                    <div className="mt-1 font-medium">
                      {selectedExperiment.primary_outcome}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Outcome Type</div>
                    <div className="mt-1 font-medium">
                      {selectedExperiment.outcome_type}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">MDE</div>
                    <div className="mt-1 font-medium">
                      {selectedExperiment.minimum_detectable_effect}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Significance (α)</div>
                    <div className="mt-1 font-medium">
                      {(selectedExperiment.alpha * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Power (1-β)</div>
                    <div className="mt-1 font-medium">
                      {(selectedExperiment.power * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Baseline</div>
                    <div className="mt-1 font-medium">
                      {selectedExperiment.baseline_mean?.toFixed(2) ||
                        selectedExperiment.baseline_proportion?.toFixed(2) ||
                        'N/A'}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Status</div>
                    <div className="mt-1">
                      <span
                        className={`badge ${
                          selectedExperiment.status === 'running'
                            ? 'badge-blue'
                            : 'badge-gray'
                        }`}
                      >
                        {selectedExperiment.status}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Arms */}
                <div className="mt-6">
                  <h3 className="text-sm font-medium text-gray-700 mb-3">
                    Treatment Arms
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {selectedExperiment.arms.map((arm, idx) => (
                      <div key={idx} className="p-4 border rounded">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium">{arm.name}</span>
                          <span className="text-sm text-gray-500">
                            {(arm.allocation * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="text-sm text-gray-600">
                          Value: {JSON.stringify(arm.treatment_value)}
                        </div>
                        {arm.description && (
                          <div className="text-xs text-gray-500 mt-2">
                            {arm.description}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Sample Size & Runtime */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="card">
                <div className="card-body">
                  <div className="text-sm text-gray-500">Sample Size per Arm</div>
                  <div className="text-3xl font-bold mt-2">
                    {selectedExperiment.required_sample_size_per_arm?.toLocaleString() ||
                      'N/A'}
                  </div>
                </div>
              </div>
              <div className="card">
                <div className="card-body">
                  <div className="text-sm text-gray-500">Total Sample Size</div>
                  <div className="text-3xl font-bold mt-2">
                    {selectedExperiment.total_sample_size?.toLocaleString() || 'N/A'}
                  </div>
                </div>
              </div>
              <div className="card">
                <div className="card-body">
                  <div className="text-sm text-gray-500">Expected Runtime</div>
                  <div className="text-3xl font-bold mt-2">
                    {selectedExperiment.expected_runtime_days
                      ? `${selectedExperiment.expected_runtime_days.toFixed(1)} days`
                      : 'N/A'}
                  </div>
                </div>
              </div>
            </div>

            {/* Power Curve */}
            {powerAnalysis && powerAnalysis.power_curve && (
              <div className="card">
                <div className="card-header">
                  <h2 className="card-title">Power Curve</h2>
                  <p className="card-subtitle">
                    Statistical power for different effect sizes
                  </p>
                </div>
                <div className="card-body">
                  <ResponsiveContainer width="100%" height={400}>
                    <LineChart
                      data={powerAnalysis.power_curve}
                      margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="effect_size"
                        label={{
                          value: 'Effect Size',
                          position: 'insideBottom',
                          offset: -10,
                        }}
                      />
                      <YAxis
                        label={{
                          value: 'Statistical Power',
                          angle: -90,
                          position: 'insideLeft',
                        }}
                        domain={[0, 1]}
                        tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                      />
                      <Tooltip
                        formatter={(value: any) => `${(value * 100).toFixed(1)}%`}
                        labelFormatter={(label) => `Effect Size: ${label}`}
                      />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="power"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        name="Power"
                        dot={{ r: 4 }}
                      />
                      {/* Target power line */}
                      <Line
                        type="monotone"
                        data={[
                          { effect_size: powerAnalysis.power_curve[0].effect_size, target: selectedExperiment.power },
                          { effect_size: powerAnalysis.power_curve[powerAnalysis.power_curve.length - 1].effect_size, target: selectedExperiment.power },
                        ]}
                        dataKey="target"
                        stroke="#10b981"
                        strokeDasharray="5 5"
                        name={`Target (${(selectedExperiment.power * 100).toFixed(0)}%)`}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>

                  <div className="mt-4 p-4 bg-gray-50 rounded">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">
                      Interpretation
                    </h4>
                    <ul className="text-sm text-gray-600 space-y-1">
                      <li>
                        • At MDE = {selectedExperiment.minimum_detectable_effect}, power
                        is {(selectedExperiment.power * 100).toFixed(0)}%
                      </li>
                      <li>
                        • Larger effects can be detected with higher confidence
                      </li>
                      <li>
                        • Sample size: {powerAnalysis.sample_size_per_arm.toLocaleString()}{' '}
                        per arm
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Create Experiment Modal */}
      {showCreateModal && (
        <CreateExperimentModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={(data) => createExperimentMutation.mutate(data)}
          isSubmitting={createExperimentMutation.isPending}
        />
      )}
    </div>
  )
}

// Create Experiment Modal
function CreateExperimentModal({
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
    treatment_variable: '',
    primary_outcome: '',
    outcome_type: 'continuous',
    baseline_mean: 0,
    baseline_proportion: 0.5,
    minimum_detectable_effect: 0.1,
    alpha: 0.05,
    power: 0.80,
    arms: [
      { name: 'Control', treatment_value: 0, allocation: 0.5 },
      { name: 'Treatment', treatment_value: 1, allocation: 0.5 },
    ],
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content max-w-3xl" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">Design New Experiment</h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="space-y-4">
              {/* Basic Info */}
              <div className="form-group">
                <label className="form-label">Experiment Name</label>
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
                  rows={2}
                />
              </div>

              {/* Variables */}
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
                  <label className="form-label">Primary Outcome</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.primary_outcome}
                    onChange={(e) =>
                      setFormData({ ...formData, primary_outcome: e.target.value })
                    }
                    required
                  />
                </div>
              </div>

              {/* Outcome Type */}
              <div className="form-group">
                <label className="form-label">Outcome Type</label>
                <select
                  className="form-input"
                  value={formData.outcome_type}
                  onChange={(e) =>
                    setFormData({ ...formData, outcome_type: e.target.value })
                  }
                >
                  <option value="continuous">Continuous</option>
                  <option value="binary">Binary</option>
                </select>
              </div>

              {/* Statistical Parameters */}
              <div className="grid grid-cols-3 gap-4">
                {formData.outcome_type === 'continuous' ? (
                  <div className="form-group">
                    <label className="form-label">Baseline Mean</label>
                    <input
                      type="number"
                      step="0.01"
                      className="form-input"
                      value={formData.baseline_mean}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          baseline_mean: parseFloat(e.target.value),
                        })
                      }
                    />
                  </div>
                ) : (
                  <div className="form-group">
                    <label className="form-label">Baseline Proportion</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max="1"
                      className="form-input"
                      value={formData.baseline_proportion}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          baseline_proportion: parseFloat(e.target.value),
                        })
                      }
                    />
                  </div>
                )}

                <div className="form-group">
                  <label className="form-label">MDE</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-input"
                    value={formData.minimum_detectable_effect}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        minimum_detectable_effect: parseFloat(e.target.value),
                      })
                    }
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Significance (α)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    className="form-input"
                    value={formData.alpha}
                    onChange={(e) =>
                      setFormData({ ...formData, alpha: parseFloat(e.target.value) })
                    }
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Power (1-β)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  className="form-input"
                  value={formData.power}
                  onChange={(e) =>
                    setFormData({ ...formData, power: parseFloat(e.target.value) })
                  }
                  required
                />
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Creating...' : 'Create Experiment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
