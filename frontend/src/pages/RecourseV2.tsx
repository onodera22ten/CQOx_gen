/**
 * Recourse Panel - Individual Counterfactual Interventions
 * Generates actionable recommendations for individuals to achieve desired outcomes
 */

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import axios from 'axios'

interface RecourseCandidate {
  intervention: Record<string, number>
  predicted_outcome: number
  cost: number
  feasibility: number
  actionability: number
  diversity?: number
}

interface RecoursePlan {
  id: string
  unit_id: string
  current_features: Record<string, number>
  current_predicted_outcome: number
  target_outcome: number
  candidates: RecourseCandidate[]
  actionable_features: string[]
  immutable_features: string[]
}

export default function RecoursePanelV2() {
  const [unitId, setUnitId] = useState('')
  const [policyId, setPolicyId] = useState('')
  const [currentFeatures, setCurrentFeatures] = useState<Record<string, number>>({})
  const [targetOutcome, setTargetOutcome] = useState<number>(0)
  const [actionableFeatures, setActionableFeatures] = useState<string[]>([])
  const [recoursePlan, setRecoursePlan] = useState<RecoursePlan | null>(null)
  const [selectedCandidate, setSelectedCandidate] = useState<number>(0)

  // Generate recourse mutation
  const generateRecourseMutation = useMutation({
    mutationFn: async (data: {
      unit_id: string
      policy_id: string
      current_features: Record<string, number>
      target_outcome: number
      actionable_features: string[]
      n_candidates: number
    }) => {
      const response = await axios.post(`/api/v2/recourse/${data.unit_id}`, {
        policy_id: data.policy_id,
        current_features: data.current_features,
        target_outcome: data.target_outcome,
        actionable_features: data.actionable_features,
        immutable_features: [],
        n_candidates: data.n_candidates,
        cost_type: 'L1',
      })
      return response.data as RecoursePlan
    },
    onSuccess: (data) => {
      setRecoursePlan(data)
      setSelectedCandidate(0)
    },
  })

  const handleGenerateRecourse = () => {
    if (!unitId || !policyId || actionableFeatures.length === 0) {
      alert('Please fill in all required fields')
      return
    }

    generateRecourseMutation.mutate({
      unit_id: unitId,
      policy_id: policyId,
      current_features: currentFeatures,
      target_outcome: targetOutcome,
      actionable_features: actionableFeatures,
      n_candidates: 5,
    })
  }

  const selectedCandidateData = recoursePlan?.candidates[selectedCandidate]

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Recourse v2</h1>
          <p className="page-subtitle">
            Individual-level counterfactual interventions and actionable recommendations
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Form */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Generate Recourse Plan</h2>
          </div>
          <div className="card-body">
            <div className="space-y-4">
              {/* Unit ID */}
              <div className="form-group">
                <label className="form-label">Individual ID</label>
                <input
                  type="text"
                  className="form-input"
                  value={unitId}
                  onChange={(e) => setUnitId(e.target.value)}
                  placeholder="user_12345"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Unique identifier for the individual
                </p>
              </div>

              {/* Policy ID */}
              <div className="form-group">
                <label className="form-label">Policy ID</label>
                <input
                  type="text"
                  className="form-input"
                  value={policyId}
                  onChange={(e) => setPolicyId(e.target.value)}
                  placeholder="policy_xyz"
                />
              </div>

              {/* Current Features */}
              <div className="form-group">
                <label className="form-label">Current Features (JSON)</label>
                <textarea
                  className="form-input font-mono text-sm"
                  rows={4}
                  value={JSON.stringify(currentFeatures, null, 2)}
                  onChange={(e) => {
                    try {
                      setCurrentFeatures(JSON.parse(e.target.value))
                    } catch {}
                  }}
                  placeholder='{"age": 35, "income": 50000, "score": 0.6}'
                />
              </div>

              {/* Target Outcome */}
              <div className="form-group">
                <label className="form-label">Target Outcome</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input"
                  value={targetOutcome}
                  onChange={(e) => setTargetOutcome(parseFloat(e.target.value))}
                  placeholder="0.8"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Desired outcome value to achieve
                </p>
              </div>

              {/* Actionable Features */}
              <div className="form-group">
                <label className="form-label">Actionable Features (comma-separated)</label>
                <input
                  type="text"
                  className="form-input"
                  value={actionableFeatures.join(', ')}
                  onChange={(e) =>
                    setActionableFeatures(
                      e.target.value.split(',').map((f) => f.trim()).filter(Boolean)
                    )
                  }
                  placeholder="income, score, engagement"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Features that can be changed (age, gender are immutable)
                </p>
              </div>

              {/* Generate Button */}
              <button
                className="btn btn-primary w-full"
                onClick={handleGenerateRecourse}
                disabled={generateRecourseMutation.isPending}
              >
                {generateRecourseMutation.isPending
                  ? 'Generating...'
                  : 'Generate Recourse Plan'}
              </button>

              {generateRecourseMutation.isError && (
                <div className="alert alert-error">
                  Error: {(generateRecourseMutation.error as any)?.message}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Results */}
        {recoursePlan && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Recourse Plan</h2>
              <span className="text-sm text-gray-500">
                {recoursePlan.candidates.length} options found
              </span>
            </div>
            <div className="card-body">
              {/* Current State */}
              <div className="mb-6 p-4 bg-gray-50 rounded">
                <h3 className="text-sm font-medium text-gray-700 mb-2">
                  Current State
                </h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-gray-500">Predicted Outcome:</span>
                    <span className="ml-2 font-medium">
                      {recoursePlan.current_predicted_outcome.toFixed(3)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Target:</span>
                    <span className="ml-2 font-medium">
                      {recoursePlan.target_outcome.toFixed(3)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Candidate Selector */}
              <div className="mb-4">
                <label className="form-label">Select Intervention Option</label>
                <select
                  className="form-input"
                  value={selectedCandidate}
                  onChange={(e) => setSelectedCandidate(parseInt(e.target.value))}
                >
                  {recoursePlan.candidates.map((candidate, idx) => (
                    <option key={idx} value={idx}>
                      Option {idx + 1} - Cost: {candidate.cost.toFixed(2)},
                      Outcome: {candidate.predicted_outcome.toFixed(3)}
                    </option>
                  ))}
                </select>
              </div>

              {/* Selected Candidate Details */}
              {selectedCandidateData && (
                <div className="space-y-4">
                  {/* Metrics */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-blue-50 rounded">
                      <div className="text-sm text-gray-500">Predicted Outcome</div>
                      <div className="text-2xl font-bold text-blue-600">
                        {selectedCandidateData.predicted_outcome.toFixed(3)}
                      </div>
                    </div>
                    <div className="p-3 bg-green-50 rounded">
                      <div className="text-sm text-gray-500">Cost</div>
                      <div className="text-2xl font-bold text-green-600">
                        {selectedCandidateData.cost.toFixed(2)}
                      </div>
                    </div>
                    <div className="p-3 bg-purple-50 rounded">
                      <div className="text-sm text-gray-500">Feasibility</div>
                      <div className="text-2xl font-bold text-purple-600">
                        {(selectedCandidateData.feasibility * 100).toFixed(0)}%
                      </div>
                    </div>
                    <div className="p-3 bg-orange-50 rounded">
                      <div className="text-sm text-gray-500">Actionability</div>
                      <div className="text-2xl font-bold text-orange-600">
                        {(selectedCandidateData.actionability * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>

                  {/* Interventions */}
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-3">
                      Required Actions
                    </h3>
                    <div className="space-y-2">
                      {Object.entries(selectedCandidateData.intervention).map(
                        ([feature, newValue]) => {
                          const currentValue = recoursePlan.current_features[feature]
                          const change = newValue - currentValue
                          const changePercent = currentValue !== 0
                            ? (change / currentValue) * 100
                            : 0

                          return (
                            <div
                              key={feature}
                              className="flex items-center justify-between p-3 bg-white border rounded"
                            >
                              <div>
                                <div className="font-medium">{feature}</div>
                                <div className="text-sm text-gray-500">
                                  {currentValue.toFixed(2)} → {newValue.toFixed(2)}
                                </div>
                              </div>
                              <div className="text-right">
                                <div
                                  className={`text-sm font-medium ${
                                    change > 0 ? 'text-green-600' : 'text-red-600'
                                  }`}
                                >
                                  {change > 0 ? '+' : ''}
                                  {change.toFixed(2)}
                                </div>
                                <div className="text-xs text-gray-500">
                                  {change > 0 ? '+' : ''}
                                  {changePercent.toFixed(1)}%
                                </div>
                              </div>
                            </div>
                          )
                        }
                      )}
                    </div>
                  </div>

                  {/* Action Button */}
                  <button className="btn btn-primary w-full">
                    Apply This Intervention
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!recoursePlan && !generateRecourseMutation.isPending && (
          <div className="card">
            <div className="card-body text-center py-12">
              <div className="text-gray-400 mb-4">
                <svg
                  className="w-16 h-16 mx-auto"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No Recourse Plan Yet
              </h3>
              <p className="text-gray-500">
                Fill in the form and click "Generate Recourse Plan" to get started
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Privacy Notice */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded">
        <div className="flex items-start">
          <svg
            className="w-5 h-5 text-blue-600 mt-0.5 mr-3"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
          <div>
            <h4 className="text-sm font-medium text-blue-900">Privacy Notice</h4>
            <p className="text-sm text-blue-700 mt-1">
              Individual-level recourse plans are computed on-the-fly and NOT stored in
              the database. This ensures GDPR compliance and protects user privacy.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
