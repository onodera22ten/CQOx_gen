import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { policiesAPI, Policy } from '../api/v1/policies'
import { formatYenShort, formatYenMan } from '../utils/format'

interface CustomScenario {
  name: string
  targetSegment: string
  channel: string[]
  frequency: string
  discountRate: number
  budgetCap: number
  evaluationMetric: string
  duration: number
}

export default function PolicyLab() {
  const queryClient = useQueryClient()
  const [selectedPolicy, setSelectedPolicy] = useState<Policy | null>(null)
  const [editMode, setEditMode] = useState(false)
  const [yamlContent, setYamlContent] = useState('')
  const [activeTab, setActiveTab] = useState<'predefined' | 'custom'>('predefined')
  const [showScenarioSimulator, setShowScenarioSimulator] = useState(false)
  const [scenarioName, setScenarioName] = useState('')
  const [selectedPolicyIds, setSelectedPolicyIds] = useState<string[]>([])

  // Custom Scenario State
  const [customScenario, setCustomScenario] = useState<CustomScenario>({
    name: '',
    targetSegment: '',
    channel: [],
    frequency: 'weekly',
    discountRate: 0,
    budgetCap: 1000000,
    evaluationMetric: 'revenue',
    duration: 28
  })

  const { data, isLoading, error } = useQuery<Policy[]>({
    queryKey: ['policies'],
    queryFn: async () => {
      const response = await policiesAPI.list()
      return response
    },
  })

  const evaluateMutation = useMutation({
    mutationFn: (policyId: string) => policiesAPI.evaluateOffline(policyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policies'] })
    }
  })

  const scenarioMutation = useMutation({
    mutationFn: () => policiesAPI.simulateScenario(scenarioName, selectedPolicyIds),
  })

  if (isLoading) {
    return (
      <div style={{ padding: '32px', color: '#cbd5e0' }}>
        Loading policies...
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: '32px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '24px' }}>
          Policy Lab
        </h1>
        <div style={{ 
          background: 'rgba(245, 87, 108, 0.1)', 
          border: '1px solid rgba(245, 87, 108, 0.3)',
          borderRadius: '8px',
          padding: '16px',
          color: '#f5576c'
        }}>
          <div style={{ fontWeight: '600', marginBottom: '8px' }}>データ取得エラー</div>
          <div style={{ fontSize: '14px', opacity: 0.7 }}>
            バックエンドAPIに接続できません。Docker Composeが起動していることを確認してください。
          </div>
        </div>
      </div>
    )
  }

  const policies = data || []

  const handlePolicySelect = (policy: Policy) => {
    setSelectedPolicy(policy)
    setEditMode(false)
    // Convert policy to YAML-like format
    setYamlContent(`id: "${policy.id}"
name: "${policy.name}"
description: "${policy.description || ''}"
dataset_id: "${policy.dataset_id}"
target_rule: "${policy.target_rule || ''}"
channels: ${JSON.stringify(policy.channels || [])}
budget_limit: ${policy.budget_limit || 0}
status: "${policy.status}"`)
  }

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '8px' }}>Policy Lab</h1>
        <p style={{ color: '#94a3b8', fontSize: '16px', marginBottom: '24px' }}>
          Design, evaluate, and simulate marketing policies
        </p>

        {/* Tab Navigation */}
        <div style={{ display: 'flex', gap: '12px', borderBottom: '2px solid #334155', marginBottom: '24px' }}>
          <button
            onClick={() => setActiveTab('predefined')}
            style={{
              padding: '12px 24px',
              background: activeTab === 'predefined' ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' : 'transparent',
              border: 'none',
              borderBottom: activeTab === 'predefined' ? '3px solid #3b82f6' : '3px solid transparent',
              borderRadius: '8px 8px 0 0',
              color: activeTab === 'predefined' ? '#fff' : '#94a3b8',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            📋 Predefined Scenarios
          </button>
          <button
            onClick={() => setActiveTab('custom')}
            style={{
              padding: '12px 24px',
              background: activeTab === 'custom' ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' : 'transparent',
              border: 'none',
              borderBottom: activeTab === 'custom' ? '3px solid #3b82f6' : '3px solid transparent',
              borderRadius: '8px 8px 0 0',
              color: activeTab === 'custom' ? '#fff' : '#94a3b8',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            ⚡ Custom Scenario Builder
          </button>
        </div>
      </div>

      {/* Predefined Scenarios Tab */}
      {activeTab === 'predefined' && (
        <div style={{ marginBottom: '24px', display: 'flex', gap: '12px' }}>
          <button
            onClick={() => setShowScenarioSimulator(false)}
            style={{
              padding: '10px 20px',
              background: !showScenarioSimulator ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' : 'transparent',
              border: `1px solid ${!showScenarioSimulator ? '#3b82f6' : '#334155'}`,
              borderRadius: '8px',
              color: !showScenarioSimulator ? '#fff' : '#94a3b8',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            📋 Policy List
          </button>
          <button
            onClick={() => setShowScenarioSimulator(true)}
            style={{
              padding: '10px 20px',
              background: showScenarioSimulator ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' : 'transparent',
              border: `1px solid ${showScenarioSimulator ? '#3b82f6' : '#334155'}`,
              borderRadius: '8px',
              color: showScenarioSimulator ? '#fff' : '#94a3b8',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            🎯 Scenario Simulator
          </button>
        </div>
      )}

      {activeTab === 'predefined' && showScenarioSimulator && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%)',
          border: '1px solid rgba(139, 92, 246, 0.3)',
          borderRadius: '16px',
          padding: '32px',
          marginBottom: '32px'
        }}>
          <h2 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '16px', color: '#fff' }}>
            🎯 Scenario Simulator
          </h2>
          <p style={{ color: '#cbd5e1', marginBottom: '24px' }}>
            Compare multiple policies and optimize your portfolio
          </p>

          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#f1f5f9' }}>
              Scenario Name
            </label>
            <input
              type="text"
              value={scenarioName}
              onChange={(e) => setScenarioName(e.target.value)}
              placeholder="e.g., Q1 Campaign Portfolio"
              style={{
                width: '100%',
                padding: '12px',
                background: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#f1f5f9',
                fontSize: '14px'
              }}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', marginBottom: '12px', fontWeight: '500', color: '#f1f5f9' }}>
              Select Policies to Include
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '12px' }}>
              {policies.map((policy: Policy) => (
                <label
                  key={policy.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '12px',
                    background: selectedPolicyIds.includes(policy.id) ? 'rgba(139, 92, 246, 0.2)' : '#1e293b',
                    border: `1px solid ${selectedPolicyIds.includes(policy.id) ? 'rgba(139, 92, 246, 0.5)' : '#334155'}`,
                    borderRadius: '8px',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedPolicyIds.includes(policy.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedPolicyIds([...selectedPolicyIds, policy.id])
                      } else {
                        setSelectedPolicyIds(selectedPolicyIds.filter(id => id !== policy.id))
                      }
                    }}
                    style={{ marginRight: '12px' }}
                  />
                  <div>
                    <div style={{ fontWeight: '600', color: '#f1f5f9', fontSize: '14px' }}>
                      {policy.name}
                    </div>
                    <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>
                      {policy.status}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <button
            onClick={() => scenarioMutation.mutate()}
            disabled={!scenarioName || selectedPolicyIds.length === 0 || scenarioMutation.isPending}
            className="btn btn-primary"
            style={{ width: '100%' }}
          >
            {scenarioMutation.isPending ? 'Simulating...' : '▶ Run Scenario Simulation'}
          </button>

          {scenarioMutation.data ? (
            <div style={{
              marginTop: '24px',
              padding: '24px',
              background: '#1e293b',
              borderRadius: '12px',
              border: '1px solid #334155'
            }}>
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', color: '#fff' }}>
                Simulation Results
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
                <div>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Total Incremental Profit</div>
                  <div style={{ fontSize: '24px', fontWeight: '700', color: '#10b981' }}>
                    {formatYenShort((scenarioMutation.data as Record<string, any>).total_incremental_profit || 0)}
                  </div>
                  <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
                    {formatYenMan((scenarioMutation.data as Record<string, any>).total_incremental_profit || 0)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Portfolio ROI</div>
                  <div style={{ fontSize: '24px', fontWeight: '700', color: '#3b82f6' }}>
                    {(((scenarioMutation.data as Record<string, any>).total_roi || 0) * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Risk Score</div>
                  <div style={{ fontSize: '24px', fontWeight: '700', color: '#f59e0b' }}>
                    {((scenarioMutation.data as Record<string, any>).total_risk || 0).toFixed(2)}
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      )}

      {/* Policy List and Details */}
      {activeTab === 'predefined' && !showScenarioSimulator && (
        <div style={{ display: 'grid', gridTemplateColumns: selectedPolicy ? '1fr 1fr' : '1fr', gap: '24px' }}>

          {/* Policy List */}
          <div style={{ background: '#1e293b', borderRadius: '16px', padding: '24px', border: '1px solid #334155' }}>
            <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '20px', color: '#fff' }}>
              Policies ({policies.length})
            </h2>
            <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
              {policies.length === 0 ? (
                <div style={{ padding: '48px', textAlign: 'center', color: '#64748b' }}>
                  <div style={{ fontSize: '16px', marginBottom: '8px' }}>No policies yet</div>
                  <div style={{ fontSize: '14px' }}>Create your first policy to get started</div>
                </div>
              ) : (
                policies.map((policy: Policy) => (
                  <div
                    key={policy.id}
                    onClick={() => handlePolicySelect(policy)}
                    style={{
                      padding: '16px',
                      marginBottom: '12px',
                      background: selectedPolicy?.id === policy.id ? 'rgba(59, 130, 246, 0.1)' : '#0f172a',
                      border: `1px solid ${selectedPolicy?.id === policy.id ? 'rgba(59, 130, 246, 0.5)' : '#1e293b'}`,
                      borderRadius: '12px',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '8px' }}>
                      <div style={{ fontWeight: '600', color: '#f1f5f9', fontSize: '15px' }}>
                        {policy.name}
                      </div>
                      <span style={{
                        padding: '4px 10px',
                        borderRadius: '12px',
                        fontSize: '11px',
                        fontWeight: '600',
                        background: policy.status === 'completed' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(100, 116, 139, 0.2)',
                        color: policy.status === 'completed' ? '#10b981' : '#94a3b8',
                        textTransform: 'uppercase'
                      }}>
                        {policy.status || 'draft'}
                      </span>
                    </div>
                    <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '8px' }}>
                      {policy.description || 'No description'}
                    </div>
                    <div style={{ display: 'flex', gap: '12px', fontSize: '12px', color: '#64748b' }}>
                      <span>Dataset: {policy.dataset_id?.substring(0, 8)}...</span>
                      <span>•</span>
                      <span>Channels: {policy.channels?.length || 0}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Policy Details */}
          {selectedPolicy && (
            <div style={{ background: '#1e293b', borderRadius: '16px', padding: '24px', border: '1px solid #334155' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#fff' }}>
                  Policy Details
                </h2>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => setEditMode(!editMode)}
                    style={{
                      padding: '8px 16px',
                      background: editMode ? 'rgba(239, 68, 68, 0.2)' : 'rgba(59, 130, 246, 0.2)',
                      border: `1px solid ${editMode ? 'rgba(239, 68, 68, 0.5)' : 'rgba(59, 130, 246, 0.5)'}`,
                      borderRadius: '8px',
                      color: editMode ? '#ef4444' : '#3b82f6',
                      fontSize: '14px',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                  >
                    {editMode ? 'Cancel' : '✏ Edit YAML'}
                  </button>
                  <button
                    onClick={() => evaluateMutation.mutate(selectedPolicy.id)}
                    disabled={evaluateMutation.isPending}
                    style={{
                      padding: '8px 16px',
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      border: 'none',
                      borderRadius: '8px',
                      color: 'white',
                      fontSize: '14px',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                  >
                    {evaluateMutation.isPending ? '⏳ Evaluating...' : '▶ Evaluate (OPE)'}
                  </button>
                </div>
              </div>

              {editMode ? (
                <div>
                  <textarea
                    value={yamlContent}
                    onChange={(e) => setYamlContent(e.target.value)}
                    style={{
                      width: '100%',
                      minHeight: '400px',
                      padding: '16px',
                      background: '#0f172a',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#f1f5f9',
                      fontSize: '13px',
                      fontFamily: 'monospace',
                      resize: 'vertical'
                    }}
                  />
                  <button
                    style={{
                      marginTop: '16px',
                      padding: '10px 20px',
                      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      border: 'none',
                      borderRadius: '8px',
                      color: 'white',
                      fontSize: '14px',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                  >
                    💾 Save Changes
                  </button>
                </div>
              ) : (
                <div>
                  <div style={{ marginBottom: '24px' }}>
                    <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '1px' }}>
                      Policy Configuration
                    </div>
                    <pre style={{
                      padding: '16px',
                      background: '#0f172a',
                      border: '1px solid #1e293b',
                      borderRadius: '8px',
                      color: '#cbd5e1',
                      fontSize: '13px',
                      fontFamily: 'monospace',
                      overflow: 'auto',
                      whiteSpace: 'pre-wrap'
                    }}>
                      {yamlContent}
                    </pre>
                  </div>

                  {evaluateMutation.data ? (
                    <div style={{
                      padding: '20px',
                      background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%)',
                      border: '1px solid rgba(16, 185, 129, 0.3)',
                      borderRadius: '12px'
                    }}>
                      <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#10b981' }}>
                        📊 Offline Policy Evaluation Results
                      </h3>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
                        <div>
                          <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Expected Incremental Profit</div>
                          <div style={{ fontSize: '20px', fontWeight: '700', color: '#10b981' }}>
                            {formatYenShort((evaluateMutation.data as Record<string, any>).expected_incremental_profit || 0)}
                          </div>
                          <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
                            {formatYenMan((evaluateMutation.data as Record<string, any>).expected_incremental_profit || 0)}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>ROI</div>
                          <div style={{ fontSize: '20px', fontWeight: '700', color: '#3b82f6' }}>
                            {(((evaluateMutation.data as Record<string, any>).roi || 0) * 100).toFixed(1)}%
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>CAS Score</div>
                          <div style={{ fontSize: '20px', fontWeight: '700', color: '#f59e0b' }}>
                            {(((evaluateMutation.data as Record<string, any>).cas_score || 0) * 100).toFixed(0)}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>CVaR (α=0.05)</div>
                          <div style={{ fontSize: '20px', fontWeight: '700', color: '#ef4444' }}>
                            {formatYenShort(((evaluateMutation.data as Record<string, any>).risk as Record<string, any>)?.cvar_alpha_0_05 || 0)}
                          </div>
                          <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
                            {formatYenMan(((evaluateMutation.data as Record<string, any>).risk as Record<string, any>)?.cvar_alpha_0_05 || 0)}
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : null}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Custom Scenario Builder Tab */}
      {activeTab === 'custom' && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          borderRadius: '16px',
          padding: '32px'
        }}>
          <h2 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '16px', color: '#fff' }}>
            ⚡ Custom Scenario Builder
          </h2>
          <p style={{ color: '#cbd5e1', marginBottom: '32px' }}>
            Define your own scenario without being constrained by predefined templates. Build scenarios from SQL conditions, specify channels, budget caps, and evaluation metrics.
          </p>

          <div style={{ display: 'grid', gap: '24px' }}>
            {/* Scenario Name */}
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#f1f5f9', fontSize: '14px' }}>
                📝 Scenario Name *
              </label>
              <input
                type="text"
                value={customScenario.name}
                onChange={(e) => setCustomScenario({ ...customScenario, name: e.target.value })}
                placeholder="e.g., High-Value Weekend Campaign"
                style={{
                  width: '100%',
                  padding: '12px',
                  background: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#f1f5f9',
                  fontSize: '14px'
                }}
              />
            </div>

            {/* Target Segment */}
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#f1f5f9', fontSize: '14px' }}>
                🎯 Target Segment (SQL WHERE Clause) *
              </label>
              <textarea
                value={customScenario.targetSegment}
                onChange={(e) => setCustomScenario({ ...customScenario, targetSegment: e.target.value })}
                placeholder="e.g., customer_value >= 10000 AND last_purchase_days <= 30 AND city IN ('Tokyo', 'Osaka')"
                rows={3}
                style={{
                  width: '100%',
                  padding: '12px',
                  background: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#f1f5f9',
                  fontSize: '13px',
                  fontFamily: 'monospace',
                  resize: 'vertical'
                }}
              />
              <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '6px' }}>
                💡 Define your target audience using SQL WHERE clause syntax
              </div>
            </div>

            {/* Channels */}
            <div>
              <label style={{ display: 'block', marginBottom: '12px', fontWeight: '600', color: '#f1f5f9', fontSize: '14px' }}>
                📡 Communication Channels
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px' }}>
                {['Email', 'SMS', 'Push', 'LINE', 'In-App', 'Direct Mail'].map(ch => (
                  <label
                    key={ch}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '12px',
                      background: customScenario.channel.includes(ch) ? 'rgba(59, 130, 246, 0.2)' : '#1e293b',
                      border: `1px solid ${customScenario.channel.includes(ch) ? 'rgba(59, 130, 246, 0.5)' : '#334155'}`,
                      borderRadius: '8px',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={customScenario.channel.includes(ch)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setCustomScenario({ ...customScenario, channel: [...customScenario.channel, ch] })
                        } else {
                          setCustomScenario({ ...customScenario, channel: customScenario.channel.filter(c => c !== ch) })
                        }
                      }}
                      style={{ marginRight: '8px' }}
                    />
                    <span style={{ color: '#f1f5f9', fontSize: '13px', fontWeight: '500' }}>{ch}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Frequency & Duration */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#f1f5f9', fontSize: '14px' }}>
                  🔄 Contact Frequency
                </label>
                <select
                  value={customScenario.frequency}
                  onChange={(e) => setCustomScenario({ ...customScenario, frequency: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '12px',
                    background: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    color: '#f1f5f9',
                    fontSize: '14px'
                  }}
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="biweekly">Bi-weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="one-time">One-time</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#f1f5f9', fontSize: '14px' }}>
                  ⏱ Campaign Duration (days)
                </label>
                <input
                  type="number"
                  value={customScenario.duration}
                  onChange={(e) => setCustomScenario({ ...customScenario, duration: parseInt(e.target.value) || 0 })}
                  min="1"
                  max="365"
                  style={{
                    width: '100%',
                    padding: '12px',
                    background: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    color: '#f1f5f9',
                    fontSize: '14px'
                  }}
                />
              </div>
            </div>

            {/* Discount Rate & Budget Cap */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#f1f5f9', fontSize: '14px' }}>
                  💰 Discount Rate (%)
                </label>
                <input
                  type="range"
                  min="0"
                  max="50"
                  step="1"
                  value={customScenario.discountRate}
                  onChange={(e) => setCustomScenario({ ...customScenario, discountRate: parseInt(e.target.value) })}
                  style={{ width: '100%', marginBottom: '8px' }}
                />
                <div style={{ textAlign: 'center', fontSize: '20px', fontWeight: '700', color: '#3b82f6' }}>
                  {customScenario.discountRate}%
                </div>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#f1f5f9', fontSize: '14px' }}>
                  💵 Budget Cap (¥)
                </label>
                <input
                  type="number"
                  value={customScenario.budgetCap}
                  onChange={(e) => setCustomScenario({ ...customScenario, budgetCap: parseInt(e.target.value) || 0 })}
                  min="0"
                  step="100000"
                  style={{
                    width: '100%',
                    padding: '12px',
                    background: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    color: '#f1f5f9',
                    fontSize: '14px'
                  }}
                />
                <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '6px' }}>
                  約{(customScenario.budgetCap / 10000).toFixed(0)}万円
                </div>
              </div>
            </div>

            {/* Evaluation Metric */}
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#f1f5f9', fontSize: '14px' }}>
                📊 Primary Evaluation Metric
              </label>
              <select
                value={customScenario.evaluationMetric}
                onChange={(e) => setCustomScenario({ ...customScenario, evaluationMetric: e.target.value })}
                style={{
                  width: '100%',
                  padding: '12px',
                  background: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#f1f5f9',
                  fontSize: '14px'
                }}
              >
                <option value="revenue">Incremental Revenue (Δ¥)</option>
                <option value="profit">Incremental Profit (Δ¥)</option>
                <option value="roi">ROI</option>
                <option value="conversion">Conversion Rate</option>
                <option value="ltv">Customer Lifetime Value</option>
                <option value="engagement">Engagement Rate</option>
              </select>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
              <button
                onClick={() => {
                  // Validation
                  if (!customScenario.name || !customScenario.targetSegment || customScenario.channel.length === 0) {
                    alert('Please fill in all required fields (Name, Target Segment, at least one Channel)')
                    return
                  }

                  // Generate ScenarioSpec
                  const scenarioSpec = {
                    apiVersion: 'cqox.ai/v1',
                    kind: 'Scenario',
                    metadata: {
                      name: customScenario.name,
                      createdAt: new Date().toISOString(),
                      type: 'custom'
                    },
                    spec: {
                      target_segment: {
                        type: 'sql',
                        condition: customScenario.targetSegment
                      },
                      channels: customScenario.channel,
                      frequency: customScenario.frequency,
                      discount_rate: customScenario.discountRate / 100,
                      budget_cap: customScenario.budgetCap,
                      evaluation_metric: customScenario.evaluationMetric,
                      duration_days: customScenario.duration
                    }
                  }

                  // Show YAML output
                  const yamlOutput = `# CQOx Scenario Specification
apiVersion: cqox.ai/v1
kind: Scenario
metadata:
  name: ${scenarioSpec.metadata.name}
  createdAt: ${scenarioSpec.metadata.createdAt}
  type: ${scenarioSpec.metadata.type}
spec:
  target_segment:
    type: ${scenarioSpec.spec.target_segment.type}
    condition: "${scenarioSpec.spec.target_segment.condition}"
  channels: [${scenarioSpec.spec.channels.map(c => `"${c}"`).join(', ')}]
  frequency: ${scenarioSpec.spec.frequency}
  discount_rate: ${scenarioSpec.spec.discount_rate}
  budget_cap: ${scenarioSpec.spec.budget_cap}
  evaluation_metric: ${scenarioSpec.spec.evaluation_metric}
  duration_days: ${scenarioSpec.spec.duration_days}
`

                  // Create blob and download
                  const blob = new Blob([yamlOutput], { type: 'text/yaml' })
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement('a')
                  a.href = url
                  a.download = `scenario_${customScenario.name.toLowerCase().replace(/\s+/g, '_')}.yaml`
                  a.click()
                  URL.revokeObjectURL(url)

                  alert('✅ Scenario specification exported as YAML!')
                }}
                disabled={!customScenario.name || !customScenario.targetSegment || customScenario.channel.length === 0}
                style={{
                  flex: 1,
                  padding: '14px 24px',
                  background: customScenario.name && customScenario.targetSegment && customScenario.channel.length > 0
                    ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)'
                    : '#334155',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                  fontSize: '15px',
                  fontWeight: '600',
                  cursor: customScenario.name && customScenario.targetSegment && customScenario.channel.length > 0 ? 'pointer' : 'not-allowed',
                  transition: 'all 0.2s'
                }}
              >
                💾 Save as ScenarioSpec YAML
              </button>

              <button
                onClick={() => {
                  setCustomScenario({
                    name: '',
                    targetSegment: '',
                    channel: [],
                    frequency: 'weekly',
                    discountRate: 0,
                    budgetCap: 1000000,
                    evaluationMetric: 'revenue',
                    duration: 28
                  })
                }}
                style={{
                  padding: '14px 24px',
                  background: 'transparent',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#94a3b8',
                  fontSize: '15px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                🔄 Reset Form
              </button>
            </div>

            {/* Example Scenarios */}
            <div style={{ marginTop: '24px', padding: '20px', background: 'rgba(59, 130, 246, 0.05)', border: '1px solid rgba(59, 130, 246, 0.2)', borderRadius: '12px' }}>
              <div style={{ fontSize: '14px', fontWeight: '600', color: '#3b82f6', marginBottom: '12px' }}>
                💡 Example Use Cases
              </div>
              <div style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: '1.8' }}>
                <ul style={{ margin: 0, paddingLeft: '20px' }}>
                  <li><strong>High-Value Dormant Users:</strong> <code style={{ background: '#1e293b', padding: '2px 6px', borderRadius: '4px', fontSize: '12px' }}>customer_value &gt;= 50000 AND last_purchase_days &gt; 90</code></li>
                  <li><strong>Weekend Shoppers in Major Cities:</strong> <code style={{ background: '#1e293b', padding: '2px 6px', borderRadius: '4px', fontSize: '12px' }}>purchase_dow IN (0, 6) AND city IN ('Tokyo', 'Osaka', 'Nagoya')</code></li>
                  <li><strong>Mobile App Power Users:</strong> <code style={{ background: '#1e293b', padding: '2px 6px', borderRadius: '4px', fontSize: '12px' }}>app_sessions_30d &gt;= 20 AND mobile_order_ratio &gt; 0.8</code></li>
                  <li><strong>Cart Abandoners with High Intent:</strong> <code style={{ background: '#1e293b', padding: '2px 6px', borderRadius: '4px', fontSize: '12px' }}>cart_value &gt; 10000 AND abandoned_hours &lt; 24 AND view_count &gt;= 3</code></li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
